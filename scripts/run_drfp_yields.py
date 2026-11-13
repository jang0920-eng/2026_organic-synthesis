"""DRFP 지문 + XGBoost로 단계별 수율을 예측한다 (Yield-BERT 비교용).

DRFP: https://github.com/reymond-group/drfp — Probst et al.,
Digital Discovery 2022, 1, 91. 반응 지문만 만들고 수율 모델은 포함하지 않으므로,
회귀 모델을 직접 학습해야 한다.

비교의 공정성
    Yield-BERT(run_rxn_yields.py)와 **같은 Suzuki-Miyaura HTE 데이터, 같은 split**으로
    학습한다. 달라지는 것은 반응 표현 방식뿐이다 (BERT 토큰 임베딩 vs DRFP 이진 지문).
    홀드아웃 구간으로 R²·RMSE를 측정해 모델이 제대로 학습되었는지 먼저 확인한다.

사용법
    python scripts/run_drfp_yields.py --route 1 6 --splits 10
"""

import argparse
import csv
import gc
import json
import os
import pathlib
import sys
import warnings
from hashlib import blake2b

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
TRAIN_ROWS = 4032  # Yield-BERT와 동일한 학습 구간


def patch_drfp_hash():
    """Windows 패치.

    drfp 0.3.6은 blake2b(digest_size=4) 결과를 np.int32에 담는데, 이 값은 부호 없는
    32비트라 2^31을 넘으면 Windows에서 OverflowError가 난다 (C long이 32비트).
    부호 없는 타입으로 담는 것이 digest의 원래 의미에도 맞다.
    """
    import numpy as np
    from drfp import DrfpEncoder

    def _hash(shingling):
        return np.array(
            [int(blake2b(t, digest_size=4).hexdigest(), 16) for t in shingling],
            dtype=np.uint32,
        )

    DrfpEncoder.hash = staticmethod(_hash)
    return DrfpEncoder


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--route", type=int, nargs="+", default=[1, 6])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--splits", type=int, default=10)
    ap.add_argument("--outdir", default="results/yields")
    args = ap.parse_args()

    import numpy as np
    import pandas as pd
    from sklearn.metrics import mean_squared_error, r2_score
    from xgboost import XGBRegressor

    DrfpEncoder = patch_drfp_hash()

    # --- 예측 대상 반응 ---
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

    print(f"대상 반응 {len(texts)}개 인코딩 중...")
    target_fps = np.array(DrfpEncoder.encode(texts), dtype=np.float32)

    # --- split마다 학습 → 검증 → 예측 ---
    all_preds, r2s, rmses = [], [], []
    for i in range(args.splits):
        tsv = os.path.join(
            args.repo, "data", "Suzuki-Miyaura", "random_splits", f"random_split_{i}.tsv"
        )
        if not os.path.exists(tsv):
            continue
        df = pd.read_csv(tsv, sep="\t")
        fps = np.array(DrfpEncoder.encode(df.rxn.tolist()), dtype=np.float32)

        X_tr, y_tr = fps[:TRAIN_ROWS], df.y.values[:TRAIN_ROWS]
        X_te, y_te = fps[TRAIN_ROWS:], df.y.values[TRAIN_ROWS:]

        model = XGBRegressor(
            n_estimators=600, max_depth=12, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, n_jobs=4, random_state=42,
        )
        model.fit(X_tr, y_tr)

        r2 = r2_score(y_te, model.predict(X_te))
        rmse = mean_squared_error(y_te, model.predict(X_te)) ** 0.5 * 100
        r2s.append(r2)
        rmses.append(rmse)

        all_preds.append(np.clip(model.predict(target_fps), 0, 1) * 100)
        print(f"  split {i}: 홀드아웃 R²={r2:.3f}, RMSE={rmse:.1f}%p", flush=True)

        # 메모리가 적은 노트북에서는 split마다 바로 반납해야 한다.
        # 지문 배열(4032 x 2048 float32)과 학습된 트리가 쌓이면 수 GB가 된다.
        del model, fps, X_tr, X_te, y_tr, y_te, df
        gc.collect()

    if not all_preds:
        sys.exit("학습 데이터를 찾지 못했다.")

    arr = np.vstack(all_preds)
    pred_mean, pred_std = arr.mean(axis=0), arr.std(axis=0)
    print(f"\n홀드아웃 평균: R²={np.mean(r2s):.3f}, RMSE={np.mean(rmses):.1f}%p")

    # --- 저장 ---
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for n in args.route:
        rows = [(i, s) for i, (rn, s) in enumerate(keys) if rn == n]

        with open(outdir / f"route_{n}_yields_drfp.csv", "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["step", "policy_probability", "yield_mean_pct",
                        "yield_std_pct", "reaction_smiles"])
            for i, s in rows:
                w.writerow([s["step"], s["policy_probability"],
                            round(float(pred_mean[i]), 1),
                            round(float(pred_std[i]), 1), s["reaction_smiles"]])

        lines = [
            f"# v4 route {n} — DRFP + XGBoost 수율 예측",
            "",
            f"Suzuki-Miyaura HTE 데이터 random split {len(all_preds)}개 앙상블.",
            "Yield-BERT와 같은 데이터·같은 split으로 학습했고, 반응 표현만 다르다.",
            "",
            f"홀드아웃 성능: R² = {np.mean(r2s):.3f}, RMSE = {np.mean(rmses):.1f}%p "
            "(HTE 테스트 구간 기준)",
            "",
            "| 단계 | 경로 p | DRFP 예측 수율 (%) | 앙상블 편차 (%) |",
            "| --- | --- | --- | --- |",
        ]
        for i, s in rows:
            lines.append(
                f"| {s['step']} | {s['policy_probability']:.3f} | "
                f"{pred_mean[i]:.1f} | ±{pred_std[i]:.1f} |"
            )
        (outdir / f"route_{n}_yields_drfp.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        print(f"route {n}: {len(rows)}단계 저장")


if __name__ == "__main__":
    main()
