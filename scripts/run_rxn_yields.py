"""rxn_yields (Yield-BERT)로 단계별 수율을 예측한다.

모델: https://github.com/rxn4chemistry/rxn_yields — Schwaller et al.,
Mach. Learn.: Sci. Technol. 2021, 2, 015016.

보정에 관한 중요한 주의
    모델 출력은 **표준화된 값**이다. 학습 세트의 mean·std로 되돌리고 ×100 한 뒤
    0–100으로 클립해야 수율(%)이 된다. 이 보정을 하지 않으면 숫자가 의미가 없다.

    repo에 동봉된 학습 모델은 세 종류다.
      - suzuki_miyaura : HTE 데이터가 repo에 있어 mean·std를 계산할 수 있다 → 사용
      - buchwald_hartwig: HTE 데이터가 repo에 있지만 이 경로에 Pd 촉매 C–N 커플링이 없다
      - uspto          : 범용이지만 학습 데이터가 IBM Box(로그인 필요)에 있어
                         mean·std를 알 수 없다 → 절대 수율로 환산 불가

불확실성
    10개 random split 모델로 앙상블하고 평균과 표준편차를 함께 낸다.

사용법
    python scripts/run_rxn_yields.py --route 1 6
"""

import argparse
import csv
import glob
import json
import os
import pathlib
import sys
import warnings

warnings.filterwarnings("ignore")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

#  기본값은 이 repo와 같은 폴더에 나란히 받은 rxn-yields-src다.
#  다른 곳에 받았으면 환경변수 RXN_YIELDS_REPO 또는 --repo로 알려준다.
DEFAULT_REPO = os.environ.get(
    "RXN_YIELDS_REPO",
    str(pathlib.Path(__file__).resolve().parent.parent.parent / "rxn-yields-src"),
)
SUZUKI_TRAIN_ROWS = 4032  # 논문의 random split 학습 구간


def find_checkpoints(repo, n_splits):
    """split별 epoch-15 체크포인트 경로를 찾는다."""
    found = []
    for i in range(n_splits):
        folder = os.path.join(
            repo, "trained_models", "suzuki_miyaura", f"random_split_{i}_split_4032"
        )
        hits = glob.glob(os.path.join(folder, "*epoch-15"))
        if hits:
            found.append((i, hits[0]))
    return found


def is_suzuki(reactants):
    """반응물에 붕소 시약이 있으면 Suzuki 커플링으로 본다."""
    for r in reactants:
        if "B(" in r or "B1" in r or "[B-]" in r:
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--route", type=int, nargs="+", default=[1, 6])
    ap.add_argument("--repo", default=DEFAULT_REPO, help="rxn_yields 클론 경로")
    ap.add_argument("--splits", type=int, default=10, help="앙상블에 쓸 split 수")
    ap.add_argument("--outdir", default="results/yields")
    args = ap.parse_args()

    import numpy as np
    import pandas as pd
    from rxnfp.models import SmilesClassificationModel

    # --- 보정 상수: 학습 세트의 mean/std ---
    tsv = os.path.join(
        args.repo, "data", "Suzuki-Miyaura", "random_splits", "random_split_0.tsv"
    )
    train = pd.read_csv(tsv, sep="\t").iloc[:SUZUKI_TRAIN_ROWS]
    mean, std = train.y.mean(), train.y.std()
    print(f"보정 상수 (Suzuki-Miyaura 학습 세트): mean={mean:.4f}, std={std:.4f}")

    ckpts = find_checkpoints(args.repo, args.splits)
    if not ckpts:
        sys.exit(f"체크포인트를 찾지 못했다: {args.repo}")
    print(f"앙상블 모델 {len(ckpts)}개")

    # --- 입력 모으기 ---
    routes = {}
    for n in args.route:
        payload = json.loads(
            pathlib.Path(f"results/steps/route_{n}.json").read_text(encoding="utf-8")
        )
        routes[n] = payload["steps"]

    texts, keys = [], []
    for n, steps in routes.items():
        for s in steps:
            texts.append(s["reaction_smiles"])
            keys.append((n, s))

    # --- 앙상블 예측 ---
    # Windows에서는 피처 변환의 멀티프로세싱이 spawn 때문에 극단적으로 느리다
    # (배치당 30초 이상). 22개 반응 규모에서는 끄는 쪽이 훨씬 빠르다.
    model_args = {
        "regression": True,
        "use_multiprocessing": False,
        "use_multiprocessing_for_evaluation": False,
        "process_count": 1,
        "silent": True,
    }

    all_preds = []
    for split_no, path in ckpts:
        model = SmilesClassificationModel(
            "bert", path, num_labels=1, args=model_args, use_cuda=False
        )
        # rxnfp 0.1.0의 SmilesClassificationModel은 옛 simpletransformers 기준으로
        # 작성되어 loss_fct를 설정하지 않는다. 0.63.6의 predict는 이 속성을 요구하므로
        # None을 넣어 기본 손실함수를 쓰게 한다 (회귀 예측값에는 영향이 없다).
        if not hasattr(model, "loss_fct"):
            model.loss_fct = None
        raw = model.predict(texts)[0]
        pct = np.clip(np.asarray(raw) * std + mean, 0, 1) * 100
        all_preds.append(pct)
        print(f"  split {split_no}: 완료")
        del model

    arr = np.vstack(all_preds)            # (splits, reactions)
    pred_mean = arr.mean(axis=0)
    pred_std = arr.std(axis=0)

    # --- 저장 ---
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for n in args.route:
        rows = [(i, s) for i, (rn, s) in enumerate(keys) if rn == n]

        csv_path = outdir / f"route_{n}_yields.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(
                ["step", "policy_name", "policy_probability", "is_suzuki",
                 "yield_mean_pct", "yield_std_pct", "reaction_smiles"]
            )
            for i, s in rows:
                w.writerow([
                    s["step"], s["policy_name"], s["policy_probability"],
                    is_suzuki(s["reactants"]),
                    round(float(pred_mean[i]), 1), round(float(pred_std[i]), 1),
                    s["reaction_smiles"],
                ])

        lines = [
            f"# v4 route {n} — Yield-BERT 수율 예측",
            "",
            "모델: rxn_yields, **Suzuki-Miyaura HTE 데이터로 학습한 가중치**. "
            f"random split {len(ckpts)}개 앙상블, CPU 추론.",
            "",
            f"보정: 학습 세트 mean={mean:.4f}, std={std:.4f}로 역표준화한 뒤 ×100, 0–100 클립.",
            "",
            "> **도메인 경고.** 이 모델은 단일 Suzuki 커플링 HTE 실험(기질이 고정되고 "
            "리간드·염기만 바뀌는 조합)으로 학습되었다. 아래 표에서 `Suzuki` 열이 "
            "아니오인 단계는 **학습 도메인 밖**이고, 모델이 내는 숫자는 "
            "그 반응의 수율 추정값으로 쓸 수 없다. 그럼에도 모델은 아무 경고 없이 "
            "값을 낸다 — 그 자체가 한계점이다.",
            "",
            "| 단계 | Suzuki | 경로 p | 예측 수율 (%) | 앙상블 편차 (%) |",
            "| --- | --- | --- | --- | --- |",
        ]
        for i, s in rows:
            lines.append(
                f"| {s['step']} | {'예' if is_suzuki(s['reactants']) else '아니오'} | "
                f"{s['policy_probability']:.3f} | {pred_mean[i]:.1f} | ±{pred_std[i]:.1f} |"
            )
        lines.append("")
        (outdir / f"route_{n}_yields.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        print(f"route {n}: {len(rows)}단계 -> {csv_path}")


if __name__ == "__main__":
    main()
