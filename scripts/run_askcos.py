"""ASKCOS v1 context recommender로 단계별 반응 조건을 예측한다 (온도 포함).

모델: https://gitlab.com/mlpds_mit/askcosv2/context_recommender
Gao et al., ACS Cent. Sci. 2018, 4, 1465 의 신경망 조건 추천 모델.

Docker 없이 실행한다
    repo의 Docker/Singularity는 FastAPI 서비스를 띄우는 포장일 뿐이다.
    예측기 클래스를 직접 import해서 recommend()를 부르면 서비스가 필요 없다.
    모델 가중치는 Dropbox 직링크로 받을 수 있다 (scripts/download_trained_models.sh).

출력 형식
    recommend()는 조건마다 [온도(°C), 용매, 시약, 촉매, EHS점수, 최고EHS여부]를 돌려준다.
    EHS는 용매의 환경·건강·안전 점수로, 낮을수록 좋다.

Parrot과의 차이
    Parrot(USPTO 학습 공개본)은 온도를 내지 않는다. 온도를 내는 모델은 이쪽뿐이다.

검증
    SKILL.md 7.1절 규칙을 적용한다 — 예측 온도가 용매 끓는점보다 높으면 그 조건은
    열린 플라스크에서 재현할 수 없다. 해당하는 조건에 경고를 붙인다.

사용법
    conda activate askcos-env
    python scripts/run_askcos.py --route 1 6
"""

import argparse
import csv
import json
import os
import pathlib
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

#  기본값은 이 repo와 같은 폴더에 나란히 받은 askcos-context-src다.
#  다른 곳에 받았으면 환경변수 ASKCOS_REPO 또는 --repo로 알려준다.
DEFAULT_REPO = os.environ.get(
    "ASKCOS_REPO",
    str(pathlib.Path(__file__).resolve().parent.parent.parent / "askcos-context-src"),
)

# 용매 SMILES → (이름, 1기압 끓는점 °C). 끓는점은 보고서의 조건 검증에 쓴다.
SOLVENTS = {
    "ClCCl": ("DCM", 39.6),
    "C1CCOC1": ("THF", 66.0),
    "CC#N": ("아세토나이트릴", 81.6),
    "Cc1ccccc1": ("톨루엔", 110.6),
    "CO": ("메탄올", 64.7),
    "CCO": ("에탄올", 78.4),
    "CN(C)C=O": ("DMF", 153.0),
    "CS(C)=O": ("DMSO", 189.0),
    "C1COCCO1": ("1,4-다이옥세인", 101.0),
    "O": ("물", 100.0),
    "CCOC(C)=O": ("에틸 아세테이트", 77.1),
    "ClC(Cl)Cl": ("클로로폼", 61.2),
    "CCOCC": ("다이에틸 에터", 34.6),
    "CC(C)O": ("아이소프로판올", 82.6),
    "c1ccccc1": ("벤젠", 80.1),
    "CC(=O)O": ("아세트산", 118.1),
    "ClCCCl": ("1,2-다이클로로에탄", 83.5),
    "CC(C)=O": ("아세톤", 56.0),
    "CCCCCC": ("헥세인", 68.7),
    "CN1CCCC1=O": ("NMP", 202.0),
    "CCN(CC)CC": ("트라이에틸아민", 89.0),
    "CC(C)(C)O": ("tert-뷰탄올", 82.4),
    "CCCCO": ("뷰탄올", 117.7),
    "CC(C)OC(C)C": ("다이아이소프로필 에터", 68.5),
}

REAGENTS = {
    "CCN(CC)CC": "트라이에틸아민",
    "CCN(C(C)C)C(C)C": "DIPEA",
    "O=C([O-])[O-].[Na+].[Na+]": "Na2CO3",
    "O=C([O-])[O-].[K+].[K+]": "K2CO3",
    "O=C([O-])[O-].[Cs+].[Cs+]": "Cs2CO3",
    "[OH-].[Na+]": "NaOH",
    "[OH-].[K+]": "KOH",
    "Cl": "HCl",
    "CC(C)(C)[O-].[K+]": "t-BuOK",
    "[Na+].[H-]": "NaH",
    "c1ccncc1": "피리딘",
    "CN(C)c1ccncc1": "DMAP",
}


def name_solvent(smi):
    if not smi:
        return "—", None
    parts = smi.split(".")
    names, bps = [], []
    for p in parts:
        n, bp = SOLVENTS.get(p, (p, None))
        names.append(n)
        if bp is not None:
            bps.append(bp)
    # 혼합 용매는 가장 낮은 끓는점이 상한을 정한다
    return " / ".join(names), (min(bps) if bps else None)


def name_reagent(smi):
    if not smi:
        return "—"
    return " / ".join(REAGENTS.get(p, p) for p in smi.split("."))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--route", type=int, nargs="+", default=[1, 6])
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--outdir", default="results/askcos")
    args = ap.parse_args()

    project = os.getcwd()

    repo = pathlib.Path(args.repo)
    if not (repo / "app" / "v1" / "services" / "predictor.py").exists():
        sys.exit(
            f"ASKCOS 소스를 찾지 못했다: {repo}\n"
            "  git clone https://gitlab.com/mlpds_mit/askcosv2/context_recommender.git "
            "askcos-context-src\n"
            "  로 받은 뒤, 다른 위치라면 --repo 또는 환경변수 ASKCOS_REPO로 알려준다.\n"
            "  자세한 절차는 SKILL.md 3절을 본다."
        )
    weights = repo / "app/resources/models/context/v1/weights.h5"
    if not weights.exists():
        sys.exit(
            f"모델 가중치가 없다: {weights}\n"
            "  SKILL.md 3절의 gdown/curl 명령으로 v1.tar.gz를 받아 푼다."
        )

    # 설정이 app/resources 상대경로를 쓰므로 repo 안에서 실행해야 한다
    sys.path.insert(0, str(repo))
    os.chdir(repo)
    from app.v1.services.predictor import NeuralNetContextRecommender

    print("모델 로드 중...")
    rec = NeuralNetContextRecommender().load()
    print("로드 완료")

    os.chdir(project)
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for n in args.route:
        payload = json.loads(
            pathlib.Path(f"results/steps/route_{n}.json").read_text(encoding="utf-8")
        )
        steps = payload["steps"]

        csv_rows, md = [], []
        md += [
            f"# v4 route {n} — ASKCOS 반응 조건 예측 (온도 포함)",
            "",
            "모델: ASKCOS v1 neural network context recommender. Docker 없이 예측기를 "
            "직접 호출했다.",
            "",
            "Parrot과 달리 **온도를 예측한다.** EHS는 용매의 환경·건강·안전 점수로 낮을수록 좋다.",
            "",
            "> **검증 규칙 (SKILL.md 7.1).** 열린 플라스크는 용매 끓는점보다 뜨거워지지 않는다. "
            "예측 온도가 용매 끓는점을 넘으면 가압 조건이거나 재현할 수 없는 조건이다. "
            "해당 행에 `끓는점 초과` 표시를 달았다.",
            "",
        ]

        n_over = 0
        for s in steps:
            try:
                combos, scores = rec.recommend(
                    s["reaction_smiles"], None, args.topk, return_scores=True
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  단계 {s['step']}: 실패 — {exc}")
                continue

            md += [
                f"## 단계 {s['step']}",
                "",
                f"- 경로 모델 정책: {s['policy_name']} (p={s['policy_probability']:.3f})",
                f"- 반응 SMILES: `{s['reaction_smiles']}`",
                "",
                "| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
            for rank, (combo, score) in enumerate(zip(combos, scores), start=1):
                temp, solv, rgt, cat = combo[0], combo[1], combo[2], combo[3]
                ehs = combo[4] if len(combo) > 4 else ""
                sname, bp = name_solvent(solv)
                flag = ""
                if bp is not None and temp > bp:
                    flag = f"**끓는점 초과** ({bp:.0f} °C)"
                    n_over += 1
                md.append(
                    f"| top-{rank} | {temp:.1f} | {sname} | {name_reagent(rgt)} | "
                    f"{name_reagent(cat)} | {ehs} | {score:.3f} | {flag or '—'} |"
                )
                csv_rows.append([
                    s["step"], rank, round(float(temp), 1), solv, sname,
                    bp if bp is not None else "", rgt, cat, ehs,
                    round(float(score), 4), bool(flag), s["reaction_smiles"],
                ])
            md.append("")

        with open(outdir / f"route_{n}_askcos.csv", "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["step", "rank", "temperature_c", "solvent_smiles",
                        "solvent_name", "solvent_bp_c", "reagent_smiles",
                        "catalyst_smiles", "ehs_score", "score",
                        "above_boiling_point", "reaction_smiles"])
            w.writerows(csv_rows)

        (outdir / f"route_{n}_askcos.md").write_text(
            "\n".join(md) + "\n", encoding="utf-8"
        )
        print(f"route {n}: {len(steps)}단계, 끓는점 초과 조건 {n_over}건 -> {outdir}")


if __name__ == "__main__":
    main()
