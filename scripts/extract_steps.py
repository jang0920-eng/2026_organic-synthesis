"""AiZynthFinder trees.json에서 단계별 반응 SMILES를 추출한다.

조건 예측(Parrot, ASKCOS)과 수율 예측(rxn_yields, DRFP) 모델의 입력으로 쓴다.

사용법
    python scripts/extract_steps.py results/sotorasib_trees_v4.json --route 1 6

출력
    results/steps/route_<n>.json   단계별 반응 SMILES와 메타데이터
    results/steps/route_<n>.md     사람이 읽는 표

트리 구조
    최상위는 경로 리스트. 각 경로는 mol 노드와 reaction 노드가 번갈아 나오는 트리.
    reaction 노드의 smiles 필드는 역합성 '템플릿'이고 실제 반응식이 아니다.
    실제 반응은 (reaction 노드의 자식 mol들) >> (reaction 노드의 부모 mol) 이다.

단계 번호
    역합성 트리에서 깊은 reaction 노드가 먼저 일어나는 반응이다.
    깊이 내림차순으로 정렬하면 정반응 순서가 된다 (위상 정렬).

    같은 깊이에 여러 반응이 있으면 (= 서로 독립인 가지) 서브트리가 깊은 쪽을 먼저 쓴다.
    긴 쪽이 주 사슬이고 짧은 쪽이 분기이므로, 주 사슬이 연속 번호로 이어지고
    분기가 그 뒤에 와서 보고서에서 읽기 좋다. 독립인 가지의 순서는 어느 쪽이든
    위상 정렬상 유효하고 화학적으로도 같다.
"""

import argparse
import json
import pathlib
import sys

# Windows 기본 콘솔 코드페이지(cp949)에서 한국어·기호 출력이 깨지지 않게 한다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def collect_reactions(route):
    """경로 트리에서 reaction 노드를 DFS 순서로 모은다.

    각 항목: [깊이, 그 반응 아래 서브트리의 최대 깊이, DFS 순번, 생성물 SMILES, reaction 노드]
    서브트리 최대 깊이는 같은 깊이의 가지 중 어느 쪽이 주 사슬인지 가리는 데 쓴다.
    """
    found = []

    def walk(mol_node, depth):
        """이 mol 노드 아래에 있는 반응 중 가장 깊은 것의 깊이를 돌려준다."""
        deepest = depth - 1  # 잎이면 (반응이 없으면) 자기보다 얕은 값
        for rxn in mol_node.get("children") or []:
            if rxn.get("type") != "reaction":
                continue
            idx = len(found)
            found.append([depth, depth, idx, mol_node["smiles"], rxn])
            subtree_deepest = depth
            for child_mol in rxn.get("children") or []:
                subtree_deepest = max(subtree_deepest, walk(child_mol, depth + 1))
            found[idx][1] = subtree_deepest
            deepest = max(deepest, subtree_deepest)
        return deepest

    walk(route, 0)
    return found


def build_steps(route):
    """정반응 순서의 단계 리스트를 만든다."""
    found = collect_reactions(route)
    # 깊이 내림차순 (깊은 반응이 먼저) → 같은 깊이면 서브트리가 깊은 쪽(주 사슬) 먼저
    # → 그래도 같으면 DFS 순서.
    found.sort(key=lambda t: (-t[0], -t[1], t[2]))

    steps = []
    for i, (depth, _subtree_deepest, _idx, product, rxn) in enumerate(found, start=1):
        reactants = [c["smiles"] for c in (rxn.get("children") or [])]
        meta = rxn.get("metadata") or {}
        steps.append(
            {
                "step": i,
                "retro_depth": depth,
                "reaction_smiles": ".".join(reactants) + ">>" + product,
                "reactants": reactants,
                "product": product,
                "policy_name": meta.get("policy_name"),
                "policy_probability": meta.get("policy_probability"),
                "policy_probability_rank": meta.get("policy_probability_rank"),
                "classification": meta.get("classification"),
                "template_hash": meta.get("template_hash"),
                "library_occurence": meta.get("library_occurence"),
                "mapped_reaction_smiles": meta.get("mapped_reaction_smiles"),
                "retro_template": rxn.get("smiles"),
            }
        )
    return steps


def route_summary(route, steps):
    scores = route.get("scores") or {}
    leaves = []

    def walk(mol_node):
        kids = mol_node.get("children") or []
        if not kids:
            leaves.append(mol_node)
            return
        for rxn in kids:
            for child_mol in rxn.get("children") or []:
                walk(child_mol)

    walk(route)
    return {
        "target": route.get("smiles"),
        "n_steps": len(steps),
        "scores": scores,
        "precursors": [
            {"smiles": m["smiles"], "in_stock": m.get("in_stock")} for m in leaves
        ],
        "n_precursors": len(leaves),
        "n_precursors_in_stock": sum(1 for m in leaves if m.get("in_stock")),
    }


def write_markdown(path, route_no, summary, steps):
    lines = [
        f"# v4 route {route_no} — 단계별 반응 SMILES",
        "",
        f"- 목표 분자: `{summary['target']}`",
        f"- 단계 수: {summary['n_steps']}",
        f"- 전구체: {summary['n_precursors_in_stock']} / {summary['n_precursors']} 재고 보유",
    ]
    for key, val in (summary["scores"] or {}).items():
        lines.append(f"- {key}: {val}")
    lines += [
        "",
        "단계 번호는 정반응 순서다 (역합성 트리의 깊은 노드가 먼저 일어나는 반응).",
        "",
        "| # | 정책 | p | 분류 | 반응 SMILES |",
        "| --- | --- | --- | --- | --- |",
    ]
    for s in steps:
        prob = s["policy_probability"]
        prob_txt = f"{prob:.3f}" if isinstance(prob, (int, float)) else "—"
        lines.append(
            f"| {s['step']} | {s['policy_name']} | {prob_txt} | "
            f"{s['classification']} | `{s['reaction_smiles']}` |"
        )

    lines += ["", "## 전구체", ""]
    for p in summary["precursors"]:
        mark = "재고 보유" if p["in_stock"] else "**재고 미보유**"
        lines.append(f"- `{p['smiles']}` — {mark}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trees_json", help="AiZynthFinder 출력 json")
    ap.add_argument(
        "--route",
        type=int,
        nargs="+",
        default=[1],
        help="추출할 경로 번호 (1부터). 보고서 기준: 1=최고점수, 6=화학적으로 정합적",
    )
    ap.add_argument(
        "--outdir",
        default=None,
        help="출력 폴더 (기본: <trees_json의 폴더>/steps)",
    )
    args = ap.parse_args()

    src = pathlib.Path(args.trees_json)
    routes = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(routes, list):
        sys.exit(f"예상과 다른 형식이다: {type(routes)}. 경로 리스트여야 한다.")

    outdir = pathlib.Path(args.outdir) if args.outdir else src.parent / "steps"
    outdir.mkdir(parents=True, exist_ok=True)

    for route_no in args.route:
        if not 1 <= route_no <= len(routes):
            sys.exit(f"경로 {route_no}가 없다. 이 파일의 경로 수는 {len(routes)}개다.")
        route = routes[route_no - 1]
        steps = build_steps(route)
        summary = route_summary(route, steps)

        payload = {
            "source": src.name,
            "route_number": route_no,
            "summary": summary,
            "steps": steps,
        }
        json_path = outdir / f"route_{route_no}.json"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        md_path = outdir / f"route_{route_no}.md"
        write_markdown(md_path, route_no, summary, steps)

        print(
            f"route {route_no}: {len(steps)}단계, "
            f"전구체 {summary['n_precursors_in_stock']}/{summary['n_precursors']} 재고 보유"
        )
        print(f"  {json_path}")
        print(f"  {md_path}")


if __name__ == "__main__":
    main()
