"""extract_steps.py가 만든 경로 json에서 반응식·구조식 이미지를 생성한다.

보고서 가독성 항목에 쓴다.

사용법
    python scripts/draw_route.py results/steps/route_1.json
    python scripts/draw_route.py results/steps/route_1.json --format svg

출력 (results/images/route_<n>/)
    target.png          목표 분자
    step_01.png …       단계별 반응식 (반응물 >> 생성물)
    precursors.png      전구체 모음 (재고 미보유 전구체 표시)
    route_overview.png  전체 단계를 한 장에 세로로 이어붙인 그림
"""

import argparse
import json
import pathlib
import sys

from rdkit import Chem, RDLogger
from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Chem import rdChemReactions

RDLogger.DisableLog("rdApp.*")

# Windows 기본 콘솔 코드페이지(cp949)에서 한국어·기호 출력이 깨지지 않게 한다.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def parse_mol(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        print(f"  경고: SMILES 파싱 실패 — {smiles}", file=sys.stderr)
    return mol


def draw_reaction(rxn_smiles, out_path, fmt, width=1600, height=450):
    """반응식 하나를 그린다. 실패하면 False."""
    try:
        rxn = rdChemReactions.ReactionFromSmarts(rxn_smiles, useSmiles=True)
    except Exception as exc:  # noqa: BLE001
        print(f"  경고: 반응 파싱 실패 — {exc}", file=sys.stderr)
        return False
    if rxn is None:
        return False

    drawer = (
        rdMolDraw2D.MolDraw2DSVG(width, height)
        if fmt == "svg"
        else rdMolDraw2D.MolDraw2DCairo(width, height)
    )
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = True
    drawer.DrawReaction(rxn)
    drawer.FinishDrawing()
    data = drawer.GetDrawingText()
    mode = "w" if fmt == "svg" else "wb"
    kwargs = {"encoding": "utf-8"} if fmt == "svg" else {}
    with open(out_path, mode, **kwargs) as fh:
        fh.write(data)
    return True


def draw_molecule(smiles, out_path, fmt, legend="", width=900, height=700):
    mol = parse_mol(smiles)
    if mol is None:
        return False
    drawer = (
        rdMolDraw2D.MolDraw2DSVG(width, height)
        if fmt == "svg"
        else rdMolDraw2D.MolDraw2DCairo(width, height)
    )
    drawer.drawOptions().addStereoAnnotation = True
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend=legend)
    drawer.FinishDrawing()
    data = drawer.GetDrawingText()
    mode = "w" if fmt == "svg" else "wb"
    kwargs = {"encoding": "utf-8"} if fmt == "svg" else {}
    with open(out_path, mode, **kwargs) as fh:
        fh.write(data)
    return True


def draw_precursor_grid(precursors, out_path, fmt):
    mols, legends = [], []
    for p in precursors:
        mol = parse_mol(p["smiles"])
        if mol is None:
            continue
        mols.append(mol)
        legends.append("재고 보유" if p.get("in_stock") else "재고 미보유")
    if not mols:
        return False
    img = Draw.MolsToGridImage(
        mols,
        molsPerRow=3,
        subImgSize=(420, 340),
        legends=legends,
        useSVG=(fmt == "svg"),
    )
    if fmt == "svg":
        text = img.data if hasattr(img, "data") else str(img)
        pathlib.Path(out_path).write_text(text, encoding="utf-8")
    else:
        data = img.data if hasattr(img, "data") else img
        if isinstance(data, bytes):
            pathlib.Path(out_path).write_bytes(data)
        else:
            img.save(out_path)
    return True


def stack_pngs(paths, out_path):
    """단계 이미지를 세로로 이어 한 장으로 만든다. Pillow가 없으면 건너뛴다."""
    try:
        from PIL import Image
    except ImportError:
        print("  Pillow가 없어 route_overview는 건너뛴다.", file=sys.stderr)
        return False
    imgs = [Image.open(p) for p in paths if pathlib.Path(p).exists()]
    if not imgs:
        return False
    width = max(im.width for im in imgs)
    total = sum(im.height for im in imgs)
    canvas = Image.new("RGB", (width, total), "white")
    y = 0
    for im in imgs:
        canvas.paste(im, (0, y))
        y += im.height
    canvas.save(out_path)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("route_json", help="extract_steps.py가 만든 route_<n>.json")
    ap.add_argument("--format", choices=["png", "svg"], default="png")
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    src = pathlib.Path(args.route_json)
    payload = json.loads(src.read_text(encoding="utf-8"))
    route_no = payload["route_number"]
    steps = payload["steps"]
    summary = payload["summary"]
    fmt = args.format
    ext = f".{fmt}"

    outdir = (
        pathlib.Path(args.outdir)
        if args.outdir
        else src.parent.parent / "images" / f"route_{route_no}"
    )
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"route {route_no} — {len(steps)}단계, 출력 {outdir}")

    draw_molecule(
        summary["target"],
        outdir / f"target{ext}",
        fmt,
        legend=f"목표 분자 (route {route_no})",
    )

    step_paths = []
    for s in steps:
        name = f"step_{s['step']:02d}{ext}"
        path = outdir / name
        ok = draw_reaction(s["reaction_smiles"], path, fmt)
        prob = s["policy_probability"]
        prob_txt = f"p={prob:.3f}" if isinstance(prob, (int, float)) else "p=—"
        print(
            f"  step {s['step']:>2}: {'ok ' if ok else '실패'} "
            f"{s['policy_name']}, {prob_txt} -> {name}"
        )
        if ok:
            step_paths.append(path)

    draw_precursor_grid(summary["precursors"], outdir / f"precursors{ext}", fmt)

    if fmt == "png":
        stack_pngs(step_paths, outdir / "route_overview.png")

    print(f"완료: {len(step_paths)}/{len(steps)} 단계 이미지 생성")


if __name__ == "__main__":
    main()
