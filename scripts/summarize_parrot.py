"""Parrot 조건 예측 결과(csv)를 단계 번호와 합쳐 읽을 수 있는 표로 만든다.

Parrot의 출력 csv는 입력 txt의 줄 순서를 따르고 단계 번호가 없다.
make_parrot_input.py가 만든 index.csv와 합쳐 단계 번호를 붙인다.

사용법
    python scripts/summarize_parrot.py --route 1 6

출력
    results/parrot/route_<n>_summary.md

주의
    USPTO로 학습한 공개 모델은 촉매·용매·시약만 내고 온도는 내지 않는다.
    온도까지 내는 모델은 Reaxys-TotalSyn-Condition으로 학습한 쪽인데
    Reaxys 라이선스가 필요해 배포되지 않는다.
"""

import argparse
import csv
import pathlib
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# 결과에 자주 나오는 SMILES를 보고서에 쓸 이름으로 바꾼다.
NAMES = {
    "C1CCOC1": "THF",
    "C1COCCO1": "1,4-다이옥세인",
    "O": "물",
    "ClCCl": "DCM",
    "ClC(Cl)Cl": "클로로폼",
    "CC#N": "아세토나이트릴",
    "Cc1ccccc1": "톨루엔",
    "c1ccccc1": "벤젠",
    "CCOC(C)=O": "에틸 아세테이트",
    "CO": "메탄올",
    "CCO": "에탄올",
    "CN(C)C=O": "DMF",
    "CS(C)=O": "DMSO",
    "CC(C)O": "아이소프로판올",
    "CCN(CC)CC": "트라이에틸아민",
    "CCN(C(C)C)C(C)C": "DIPEA",
    "O=C([O-])[O-].[Na+].[Na+]": "Na2CO3",
    "O=C([O-])[O-].[K+].[K+]": "K2CO3",
    "O=C([O-])[O-].[Cs+].[Cs+]": "Cs2CO3",
    "O=C([O-])O.[Na+]": "NaHCO3",
    "[OH-].[Na+]": "NaOH",
    "[OH-].[K+]": "KOH",
    "[Li]CCCC": "n-BuLi",
    "[I-].[Na+]": "NaI",
    "Cl": "HCl",
    "O=S(=O)(O)O": "황산",
    "CC(=O)O": "아세트산",
    "O=C(O)C(F)(F)F": "TFA",
    "[Pd]": "Pd",
    "[H][H]": "수소",
    "CC(C)(C)[O-].[K+]": "t-BuOK",
    "[Na+].[H-]": "NaH",
    "N": "암모니아",
    "CCOCC": "다이에틸 에터",
}

PD_PPH3 = "[Pd]"  # 긴 포스핀 착물 SMILES를 줄여 표기할 때 쓴다


def pretty(smiles):
    """SMILES를 읽을 수 있는 이름으로. 모르면 SMILES 그대로 돌려준다."""
    if not smiles:
        return "—"
    if smiles in NAMES:
        return NAMES[smiles]
    # Pd 포스핀 착물은 길어서 표에 그대로 쓰면 읽기 어렵다
    if "[Pd]" in smiles and "P" in smiles:
        n_ph3 = smiles.count("[P](c2ccccc2)(c2ccccc2)")
        if n_ph3:
            return f"Pd(PPh3){n_ph3 + 1 if n_ph3 < 4 else 4}"
        return "Pd 포스핀 착물"
    return smiles


def load_conditions(path):
    """Parrot csv를 반응별 top-k 리스트로 묶는다.

    rxn_smiles 열은 각 반응의 첫 행에만 채워져 있고 나머지는 빈 칸이다.
    """
    groups = []
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["rxn_smiles"]:
                groups.append({"rxn_smiles": row["rxn_smiles"], "preds": []})
            if not groups:
                continue
            groups[-1]["preds"].append(row)
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--route", type=int, nargs="+", default=[1, 6])
    ap.add_argument("--topk", type=int, default=3, help="단계마다 보여줄 후보 수")
    ap.add_argument("--dir", default="results/parrot")
    args = ap.parse_args()

    base = pathlib.Path(args.dir)

    for n in args.route:
        cond_path = base / f"route_{n}_conditions.csv"
        idx_path = base / f"route_{n}_index.csv"
        if not cond_path.exists():
            print(f"건너뜀: {cond_path} 없음")
            continue

        groups = load_conditions(cond_path)
        index = list(csv.DictReader(open(idx_path, encoding="utf-8")))

        if len(groups) != len(index):
            print(
                f"경고: route {n} — 예측 {len(groups)}개, 입력 {len(index)}개. "
                "정규화 단계에서 반응이 빠졌을 수 있다."
            )

        lines = [
            f"# v4 route {n} — Parrot 반응 조건 예측",
            "",
            "모델: Parrot, USPTO-Condition으로 학습한 공개 가중치",
            "(`Parrot_train_in_USPTO_Condition_enhance`), CPU 추론.",
            "",
            "**이 모델은 온도를 예측하지 않는다.** 출력 항목은 촉매·용매 2개·시약 2개뿐이다. "
            "온도까지 내는 모델은 Reaxys-TotalSyn-Condition으로 학습한 쪽인데, "
            "Reaxys 라이선스가 필요해 배포되지 않는다.",
            "",
            "`score`는 빔 서치의 로그 확률이라 값이 클수록(0에 가까울수록) 모델이 확신한다는 뜻이다.",
            "",
        ]

        for g, i in zip(groups, index):
            preds = [p for p in g["preds"] if p["top-k"].startswith("top-")]
            lines += [
                f"## 단계 {i['step']}",
                "",
                f"- 경로 모델 정책: {i['policy_name']} (p={float(i['policy_probability']):.3f})",
                f"- 반응 SMILES: `{g['rxn_smiles']}`",
                "",
                "| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
            for p in preds[: args.topk]:
                lines.append(
                    "| {} | {} | {} | {} | {} | {} | {} |".format(
                        p["top-k"],
                        pretty(p["catalyst1"]),
                        pretty(p["solvent1"]),
                        pretty(p["solvent2"]),
                        pretty(p["reagent1"]),
                        pretty(p["reagent2"]),
                        p["scores"],
                    )
                )
            lines.append("")

        out = base / f"route_{n}_summary.md"
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"route {n}: {len(groups)}단계 -> {out}")


if __name__ == "__main__":
    main()
