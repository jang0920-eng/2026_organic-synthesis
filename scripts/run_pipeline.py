"""경로 → 조건 → 수율 전체 파이프라인을 한 번에 돌리고 결과를 json 하나로 모은다.

왜 단계마다 다른 파이썬을 부르는가
    모델들이 서로 충돌하는 의존성을 요구해서 conda 환경을 나눠 쓴다.
    (AiZynthFinder는 onnxruntime, Parrot은 transformers 4.18, ASKCOS는 TF 2.7)
    따라서 이 스크립트는 단계마다 해당 환경의 python.exe를 subprocess로 부른다.
    이것이 한 환경에 다 몰아넣는 것보다 재현하기 쉽다.

단계
    steps        trees.json → 단계별 반응 SMILES          (표준 라이브러리만)
    parrot-in    Parrot 입력 txt + 줄↔단계 대응표          (표준 라이브러리만)
    parrot       조건 예측 (촉매·용매·시약)                 parrot-env
    askcos       조건 예측 (온도 포함) + 끓는점 검증         askcos-env
    yields       Yield-BERT 수율 예측                      parrot-env
    drfp         DRFP + XGBoost 수율 예측                  parrot-env
    images       RDKit 반응식 이미지                       aizynth-env
    merge        위 결과를 json 하나로 통합                 (표준 라이브러리만)

메모리 주의
    drfp 단계는 XGBoost를 10번 학습해서 수 GB를 쓴다. RAM이 8GB 이하인 기기에서는
    --splits를 줄이거나 이 단계를 빼고 돌린다.

사용법
    python scripts/run_pipeline.py                      # 전체
    python scripts/run_pipeline.py --only merge         # 통합만 다시
    python scripts/run_pipeline.py --skip drfp images   # 무거운 단계 빼고
"""

import argparse
import csv
import json
import os
import pathlib
import subprocess
import sys
import time

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from summarize_parrot import pretty  # noqa: E402  SMILES → 읽을 수 있는 이름

HOME = pathlib.Path(os.path.expanduser("~"))
ENVS = {
    "aizynth": HOME / "miniconda3/envs/aizynth-env/python.exe",
    "parrot": HOME / "miniconda3/envs/parrot-env/python.exe",
    "askcos": HOME / "miniconda3/envs/askcos-env/python.exe",
}
#  기본값은 이 repo와 같은 폴더에 나란히 받은 parrot-src다.
PARROT_SRC = pathlib.Path(os.environ.get(
    "PARROT_REPO",
    str(pathlib.Path(__file__).resolve().parent.parent.parent / "parrot-src"),
))

TREES = "results/sotorasib_trees_v4.json"
ROUTES = [1, 6]
STAGE_ORDER = ["steps", "parrot-in", "parrot", "askcos", "yields", "drfp",
               "images", "merge"]


def run(cmd, cwd=None, label=""):
    """하위 프로세스를 돌리고 실패하면 멈춘다."""
    print(f"\n  $ {' '.join(str(c) for c in cmd)}")
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=cwd)
    dt = time.time() - t0
    if proc.returncode != 0:
        sys.exit(f"[중단] {label} 실패 (exit {proc.returncode})")
    print(f"  ({dt:.0f}초)")


# --------------------------------------------------------------------------
# 통합
# --------------------------------------------------------------------------

def load_parrot(route):
    """Parrot csv를 단계 번호별 top-3로 묶는다.

    Parrot 출력에는 단계 번호가 없고 rxn_smiles도 각 반응의 첫 행에만 있다.
    make_parrot_input.py가 만든 index.csv로 줄 번호와 단계 번호를 맞춘다.
    """
    cond = pathlib.Path(f"results/parrot/route_{route}_conditions.csv")
    idx = pathlib.Path(f"results/parrot/route_{route}_index.csv")
    if not cond.exists() or not idx.exists():
        return {}

    index = list(csv.DictReader(open(idx, encoding="utf-8")))
    groups, out = [], {}
    for row in csv.DictReader(open(cond, encoding="utf-8")):
        if row["rxn_smiles"]:
            groups.append([])
        if groups:
            groups[-1].append(row)

    for g, i in zip(groups, index):
        out[int(i["step"])] = [
            {
                "rank": r["top-k"],
                "catalyst": r["catalyst1"] or None,
                "solvent1": r["solvent1"] or None,
                "solvent2": r["solvent2"] or None,
                "reagent1": r["reagent1"] or None,
                "reagent2": r["reagent2"] or None,
                "score": float(r["scores"]),
            }
            for r in g[:3]
        ]
    return out


def load_askcos(route):
    path = pathlib.Path(f"results/askcos/route_{route}_askcos.csv")
    if not path.exists():
        return {}
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        out.setdefault(int(r["step"]), []).append({
            "rank": int(r["rank"]),
            "temperature_c": float(r["temperature_c"]),
            "solvent": r["solvent_name"],
            "solvent_smiles": r["solvent_smiles"] or None,
            "solvent_bp_c": float(r["solvent_bp_c"]) if r["solvent_bp_c"] else None,
            "reagent": r["reagent_smiles"] or None,
            "catalyst": r["catalyst_smiles"] or None,
            "ehs_score": r["ehs_score"] or None,
            "score": float(r["score"]),
            "above_boiling_point": r["above_boiling_point"] == "True",
        })
    return out


def load_yield(path, key):
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    return {
        int(r["step"]): {
            f"{key}_mean_pct": float(r["yield_mean_pct"]),
            f"{key}_std_pct": float(r["yield_std_pct"]),
        }
        for r in csv.DictReader(open(p, encoding="utf-8"))
    }


def merge():
    """모든 결과를 json 하나로 모으고 요약 표를 만든다."""
    outdir = pathlib.Path("results/pipeline")
    outdir.mkdir(parents=True, exist_ok=True)

    bundle = {
        "target": "Sotorasib (AMG 510)",
        "target_smiles": (
            "C[C@H]1CN(CCN1C2=NC(=O)N(C3=NC(=C(C=C32)F)C4=C(C=CC=C4F)O)"
            "C5=C(C=CN=C5C(C)C)C)C(=O)C=C"
        ),
        "pubchem_cid": 137278711,
        "route_source": TREES,
        "models": {
            "route": "AiZynthFinder 4.4.1 (uspto + ringbreaker)",
            "conditions": [
                "Parrot (USPTO-Condition) — 온도 없음",
                "ASKCOS v1 context recommender — 온도 있음",
            ],
            "yield": [
                "Yield-BERT (rxn_yields, Suzuki HTE, 10 split 앙상블)",
                "DRFP + XGBoost (같은 Suzuki HTE, 10 split 앙상블)",
            ],
        },
        "notes": [
            "Parrot 공개본은 온도를 예측하지 않는다 (Reaxys 라이선스).",
            "수율 모델은 Suzuki HTE 데이터 전용이다. USPTO 범용 모델은 보정 상수를 "
            "구할 수 없어 쓸 수 없다.",
            "above_boiling_point가 true인 조건은 열린 플라스크에서 재현할 수 없다 "
            "(SKILL.md 7.1절).",
        ],
        "routes": {},
    }

    n_bp = n_steps = 0
    for route in ROUTES:
        step_path = pathlib.Path(f"results/steps/route_{route}.json")
        if not step_path.exists():
            continue
        payload = json.loads(step_path.read_text(encoding="utf-8"))
        parrot = load_parrot(route)
        askcos = load_askcos(route)
        ybert = load_yield(f"results/yields/route_{route}_yields.csv", "yield_bert")
        drfp = load_yield(f"results/yields/route_{route}_yields_drfp.csv", "drfp")

        steps = []
        for s in payload["steps"]:
            n = s["step"]
            ask = askcos.get(n, [])
            bp_hits = [a for a in ask if a["above_boiling_point"]]
            n_bp += len(bp_hits)
            n_steps += 1
            steps.append({
                "step": n,
                "reaction_smiles": s["reaction_smiles"],
                "reactants": s["reactants"],
                "product": s["product"],
                "route_model": {
                    "policy_name": s["policy_name"],
                    "policy_probability": s["policy_probability"],
                    "classification": s["classification"],
                },
                "conditions": {"parrot": parrot.get(n, []), "askcos": ask},
                "yield": {**ybert.get(n, {}), **drfp.get(n, {})},
                "validation": {
                    "askcos_conditions_above_boiling_point": len(bp_hits),
                    "image": f"results/images/route_{route}/step_{n:02d}.png",
                },
            })

        bundle["routes"][f"route_{route}"] = {
            "n_steps": payload["summary"]["n_steps"],
            "scores": payload["summary"]["scores"],
            "precursors": payload["summary"]["precursors"],
            "steps": steps,
        }

    json_path = outdir / "sotorasib_pipeline.json"
    json_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 요약 표
    md = [
        "# 소토라십 — 경로·조건·수율 통합 결과",
        "",
        f"대상: {bundle['target']} (PubChem CID {bundle['pubchem_cid']})",
        "",
        "경로는 AiZynthFinder v4, 조건은 Parrot과 ASKCOS, 수율은 Yield-BERT와 DRFP다.",
        "**온도는 ASKCOS만 낸다.** `!` 표시는 예측 온도가 용매 끓는점을 넘어",
        "열린 플라스크에서 재현할 수 없는 조건이라는 뜻이다 (SKILL.md 7.1절).",
        "",
        "전체 데이터: `sotorasib_pipeline.json`",
        "",
    ]
    for route in ROUTES:
        key = f"route_{route}"
        if key not in bundle["routes"]:
            continue
        r = bundle["routes"][key]
        md += [
            f"## route {route} ({r['n_steps']}단계)",
            "",
            "| 단계 | 경로 p | Parrot 용매/시약 | ASKCOS 온도 | ASKCOS 용매 | Yield-BERT | DRFP |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for s in r["steps"]:
            p = s["conditions"]["parrot"]
            a = s["conditions"]["askcos"]
            p1 = p[0] if p else {}
            a1 = a[0] if a else {}
            pstr = " / ".join(
                pretty(x) for x in [p1.get("solvent1"), p1.get("reagent1")] if x
            ) or "—"
            tstr = (
                f"{a1['temperature_c']:.0f} °C"
                + (" **!**" if a1.get("above_boiling_point") else "")
                if a1 else "—"
            )
            y = s["yield"]
            md.append(
                f"| {s['step']} | {s['route_model']['policy_probability']:.3f} | "
                f"`{pstr}` | {tstr} | {a1.get('solvent', '—')} | "
                f"{y.get('yield_bert_mean_pct', float('nan')):.1f}% | "
                f"{y.get('drfp_mean_pct', float('nan')):.1f}% |"
            )
        md.append("")

    md += [
        "## 검증 요약",
        "",
        f"- 단계 수: {n_steps}",
        f"- 끓는점을 넘는 ASKCOS 조건: **{n_bp}건**",
        "",
        "끓는점을 넘는 조건은 전부 Suzuki 커플링 단계에 몰려 있다. 자세한 내용은",
        "`results/askcos/README.md` 3절을 참조한다.",
        "",
    ]
    md_path = outdir / "sotorasib_pipeline.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"\n통합 완료: {n_steps}단계, 끓는점 초과 조건 {n_bp}건")
    print(f"  {json_path}")
    print(f"  {md_path}")


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="+", choices=STAGE_ORDER)
    ap.add_argument("--skip", nargs="+", choices=STAGE_ORDER, default=[])
    ap.add_argument("--splits", type=int, default=10, help="수율 앙상블 split 수")
    args = ap.parse_args()

    stages = args.only or [s for s in STAGE_ORDER if s not in args.skip]
    print("실행할 단계:", " → ".join(stages))

    for stage in stages:
        print(f"\n{'=' * 60}\n[{stage}]")

        if stage == "steps":
            run([sys.executable, "scripts/extract_steps.py", TREES,
                 "--route", *map(str, ROUTES)], label=stage)

        elif stage == "parrot-in":
            run([sys.executable, "scripts/make_parrot_input.py",
                 *[f"results/steps/route_{n}.json" for n in ROUTES]], label=stage)

        elif stage == "parrot":
            project = pathlib.Path.cwd()
            for n in ROUTES:
                run([str(ENVS["parrot"]), "inference.py",
                     "--config_path", "configs/config_inference_use_uspto.yaml",
                     "--input_path", str(project / f"results/parrot/route_{n}_input.txt"),
                     "--output_path", str(project / f"results/parrot/route_{n}_conditions.csv"),
                     "--num_workers", "2", "--inference_batch_size", "8",
                     "--gpu", "-1"],
                    cwd=PARROT_SRC, label=f"{stage} route {n}")
            run([sys.executable, "scripts/summarize_parrot.py",
                 "--route", *map(str, ROUTES)], label="summarize_parrot")

        elif stage == "askcos":
            run([str(ENVS["askcos"]), "scripts/run_askcos.py",
                 "--route", *map(str, ROUTES)], label=stage)

        elif stage == "yields":
            run([str(ENVS["parrot"]), "-u", "scripts/run_rxn_yields.py",
                 "--route", *map(str, ROUTES), "--splits", str(args.splits)],
                label=stage)

        elif stage == "drfp":
            run([str(ENVS["parrot"]), "-u", "scripts/run_drfp_yields.py",
                 "--route", *map(str, ROUTES), "--splits", str(args.splits)],
                label=stage)

        elif stage == "images":
            for n in ROUTES:
                run([str(ENVS["aizynth"]), "scripts/draw_route.py",
                     f"results/steps/route_{n}.json"], label=f"{stage} route {n}")

        elif stage == "merge":
            merge()

    print("\n파이프라인 완료.")


if __name__ == "__main__":
    main()
