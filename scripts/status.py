"""프로젝트 진행 상황을 실제 파일 상태에서 계산해 보여준다.

문서에 적힌 체크박스는 갱신을 잊으면 낡는다. 이 스크립트는 산출물이 실제로
있는지를 직접 확인하므로 항상 지금 상태를 보여준다. 체크박스와 어긋나면
그 사실도 알려준다.

사용법
    python scripts/status.py
"""

import datetime
import json
import pathlib
import re
import subprocess
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

REPO = pathlib.Path(__file__).resolve().parent.parent
DEADLINE = datetime.date(2026, 12, 12)

# (일정, 항목, 있어야 할 산출물들)
TASKS = [
    ("1주차 11/1-11/7", "물질 선정 + AiZynthFinder 경로", [
        "results/sotorasib_trees_v4.json"]),
    ("2주차 11/8", "단계별 반응 SMILES 추출", [
        "scripts/extract_steps.py", "results/steps/route_1.json",
        "results/steps/route_6.json"]),
    ("2주차 11/9", "Parrot 조건 예측", [
        "results/parrot/route_1_conditions.csv",
        "results/parrot/route_6_conditions.csv"]),
    ("2주차 11/10", "ASKCOS 조건 예측 (온도)", [
        "results/askcos/route_1_askcos.csv",
        "results/askcos/route_6_askcos.csv"]),
    ("2주차 11/11", "Yield-BERT 수율 예측", [
        "results/yields/route_1_yields.csv",
        "results/yields/route_6_yields.csv"]),
    ("2주차 11/12", "DRFP 수율 예측", [
        "results/yields/route_1_yields_drfp.csv",
        "results/yields/route_6_yields_drfp.csv"]),
    ("2주차 11/13", "run_pipeline.py 통합", [
        "scripts/run_pipeline.py", "results/pipeline/sotorasib_pipeline.json"]),
    ("3주차 11/15", "RDKit 구조·반응식 이미지", [
        "results/images/route_1/step_01.png",
        "results/images/route_6/step_01.png"]),
    ("3주차 11/16", "SKILL.md 완성", ["SKILL.md"]),
    ("3주차 11/17", "Solar Pro 4 보고서 생성", [
        "results/report/report_v1.md"]),
    ("3주차 11/19", "보고서 v1 확정 + push", [
        "results/report/report_v1.md"]),
    ("여유기 11/20-11/26", "SynthEx 추가 (모델 다양성)", [
        "results/synthex"]),
    ("여유기 11/27-12/3", "추가점수: 하네스 비교 또는 EPI Suite", [
        "results/extra"]),
]


def exists(rel):
    return (REPO / rel).exists()


def git(*args):
    try:
        out = subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                             text=True, encoding="utf-8", errors="replace")
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def skill_todos():
    text = (REPO / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(r"<!-- TODO:?(.*?)-->", text)


def pipeline_summary():
    p = REPO / "results/pipeline/sotorasib_pipeline.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    steps = sum(len(r["steps"]) for r in d["routes"].values())
    bp = sum(
        s["validation"]["askcos_conditions_above_boiling_point"]
        for r in d["routes"].values() for s in r["steps"]
    )
    return steps, bp, list(d["routes"])


def main():
    today = datetime.date.today()
    left = (DEADLINE - today).days

    print("=" * 66)
    print("  유기합성학 기말 프로젝트 — 소토라십 AI 합성 예측")
    print(f"  오늘 {today}  ·  제출 {DEADLINE} (D-{left})")
    print("=" * 66)

    done, todo = [], []
    for sched, name, arts in TASKS:
        ok = all(exists(a) for a in arts)
        (done if ok else todo).append((sched, name, arts))
        print(f"  {'[완료]' if ok else '[  . ]'}  {sched:<20} {name}")

    print(f"\n  진행: {len(done)}/{len(TASKS)}")

    ps = pipeline_summary()
    if ps:
        steps, bp, routes = ps
        print(f"\n  파이프라인 통합: {', '.join(routes)} — {steps}단계, "
              f"끓는점 초과 조건 {bp}건")

    todos = skill_todos()
    if todos:
        print(f"\n  SKILL.md 남은 TODO {len(todos)}개:")
        for t in todos:
            print(f"    - {t.strip() or '(내용 없음)'}")

    print("\n  최근 커밋:")
    for line in (git("log", "--oneline", "-5") or "(없음)").splitlines():
        print(f"    {line}")

    dirty = git("status", "--short")
    if dirty:
        print("\n  커밋 안 된 변경:")
        for line in dirty.splitlines()[:10]:
            print(f"    {line}")
    else:
        print("\n  작업 트리 깨끗함 (원격과 동기화됨)")

    if todo:
        sched, name, arts = todo[0]
        print(f"\n  >> 다음 할 일: {sched} — {name}")
        print(f"     만들어야 할 것: {', '.join(arts)}")
    else:
        print("\n  >> 일정표 항목을 모두 끝냈다.")

    print("\n  자세한 맥락은 HANDOFF.md, 작업 절차는 SKILL.md를 읽는다.")
    print("=" * 66)


if __name__ == "__main__":
    main()
