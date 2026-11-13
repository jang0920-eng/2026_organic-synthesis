"""Parrot의 inference.py를 Windows에서 돌아가도록 고친다.

문제
    Windows에는 fork가 없어 pandarallel의 워커가 spawn으로 뜨고, 자식 프로세스가
    모듈 전역 함수 caonicalize_rxn_smiles를 찾지 못해 NameError로 죽는다.

해결
    Windows에서만 단일 프로세스 apply를 쓴다. 결과는 같고, 22개 반응 규모에서는
    속도 차이도 없다. Linux/macOS에서는 원래대로 parallel_apply를 쓴다.

여러 번 실행해도 안전하다 (이미 고쳐져 있으면 아무것도 하지 않는다).

사용법
    python scripts/patch_parrot.py
    python scripts/patch_parrot.py --repo <Parrot 클론 경로>
"""

import argparse
import os
import pathlib
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

DEFAULT_REPO = os.environ.get(
    "PARROT_REPO",
    str(pathlib.Path(__file__).resolve().parent.parent.parent / "parrot-src"),
)

OLD = """    print('Caonicalize reaction smiles and remove invalid reaction...')
    test_df['text'] = test_df.text.parallel_apply(
        lambda x: caonicalize_rxn_smiles(x))"""

NEW = """    print('Caonicalize reaction smiles and remove invalid reaction...')
    if os.name == 'nt':
        # Windows 패치: Windows에는 fork가 없어 pandarallel 워커가 spawn으로 뜨고,
        # 자식 프로세스에서 모듈 전역 함수(caonicalize_rxn_smiles)를 찾지 못해
        # NameError로 죽는다. 단일 프로세스 apply로 대체한다 (결과는 동일).
        test_df['text'] = test_df.text.apply(
            lambda x: caonicalize_rxn_smiles(x))
    else:
        test_df['text'] = test_df.text.parallel_apply(
            lambda x: caonicalize_rxn_smiles(x))"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    args = ap.parse_args()

    target = pathlib.Path(args.repo) / "inference.py"
    if not target.exists():
        sys.exit(
            f"Parrot의 inference.py를 찾지 못했다: {target}\n"
            "  git clone https://github.com/wangxr0526/Parrot.git parrot-src\n"
            "  로 받은 뒤, 다른 위치라면 --repo 또는 환경변수 PARROT_REPO로 알려준다."
        )

    text = target.read_text(encoding="utf-8")

    if "Windows 패치" in text:
        print(f"이미 적용되어 있다: {target}")
        return

    if OLD not in text:
        sys.exit(
            f"고칠 부분을 찾지 못했다: {target}\n"
            "  Parrot의 버전이 달라졌을 수 있다. inference.py의 parallel_apply 호출을\n"
            "  Windows에서 apply로 바꾸는 수정을 직접 적용한다 (SKILL.md 3절 참조)."
        )

    text = text.replace(OLD, NEW)

    # os 모듈이 import되어 있지 않으면 추가한다
    if "\nimport os\n" not in text:
        text = text.replace("import json\n", "import json\nimport os\n", 1)

    backup = target.with_suffix(".py.orig")
    if not backup.exists():
        backup.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"원본 백업: {backup}")

    target.write_text(text, encoding="utf-8")
    print(f"패치 적용: {target}")


if __name__ == "__main__":
    main()
