"""extract_steps.py가 만든 경로 json에서 Parrot 입력 txt를 만든다.

Parrot의 inference.py는 반응 SMILES가 한 줄에 하나씩 들어간 txt를 입력으로 받는다.
출력 csv는 입력 줄 순서와 같으므로, 단계 번호를 따로 적어 두어야 나중에 맞출 수 있다.

사용법
    python scripts/make_parrot_input.py results/steps/route_1.json results/steps/route_6.json

출력
    results/parrot/route_<n>_input.txt   반응 SMILES (Parrot 입력)
    results/parrot/route_<n>_index.csv   줄 번호 ↔ 단계 번호 대응표
"""

import argparse
import csv
import json
import pathlib
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("route_json", nargs="+", help="route_<n>.json 파일들")
    ap.add_argument("--outdir", default="results/parrot")
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for path in args.route_json:
        src = pathlib.Path(path)
        payload = json.loads(src.read_text(encoding="utf-8"))
        route_no = payload["route_number"]
        steps = payload["steps"]

        txt_path = outdir / f"route_{route_no}_input.txt"
        txt_path.write_text(
            "\n".join(s["reaction_smiles"] for s in steps) + "\n", encoding="utf-8"
        )

        idx_path = outdir / f"route_{route_no}_index.csv"
        with open(idx_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(
                ["line", "step", "policy_name", "policy_probability", "reaction_smiles"]
            )
            for line_no, s in enumerate(steps, start=1):
                w.writerow(
                    [
                        line_no,
                        s["step"],
                        s["policy_name"],
                        s["policy_probability"],
                        s["reaction_smiles"],
                    ]
                )

        print(f"route {route_no}: {len(steps)}단계")
        print(f"  {txt_path}")
        print(f"  {idx_path}")


if __name__ == "__main__":
    main()
