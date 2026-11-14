"""Solar Pro 4로 합성 보고서를 생성한다.

설계 원칙
    **생성된 보고서를 직접 고치지 않는다.** 어색한 부분이 있으면 이 파일의 프롬프트를
    고치고 해당 장만 다시 생성한다. 그래야 스킬이 다른 분자에도
    그대로 동작한다.

    장을 따로 생성하는 이유는 두 가지다.
    1. 20쪽 분량을 한 번에 요청하면 토큰 한도에 걸린다.
    2. 한 장만 마음에 안 들 때 그 장만 다시 생성할 수 있다.

인코딩 주의 (Windows)
    한글이 든 JSON을 셸 인자로 curl에 직접 넘기면 인코딩이 깨져 400
    invalid_request_body가 난다. 반드시 UTF-8로 직렬화해서 바이트로 보낸다.
    이 스크립트는 urllib로 직접 보내므로 문제가 없다.

사용법
    python scripts/generate_report.py                 # 전체 10장
    python scripts/generate_report.py --chapter 5 6   # 5·6장만 다시
    python scripts/generate_report.py --assemble      # 생성 없이 합치기만
"""

import argparse
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

API_URL = "https://api.upstage.ai/v1/chat/completions"
MODEL = "solar-pro4"
OUTDIR = pathlib.Path("results/report")
CHAPTER_DIR = OUTDIR / "chapters"


# --------------------------------------------------------------------------
# 자료 준비
# --------------------------------------------------------------------------

def read(path):
    p = pathlib.Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def analysis_section(num):
    """docs/analysis.md에서 `## <num>. ...` 장을 통째로 꺼낸다.

    1 선정 근거 / 2 실행 결과 / 3 경로 상세 / 4 문헌 비교 / 5 한계점
    """
    text = read("docs/analysis.md")
    m = re.search(rf"^## {num}\. .*?(?=^## \d+\. |\Z)", text, re.M | re.S)
    return m.group(0).strip() if m else ""


def skill_section(num):
    text = read("SKILL.md")
    m = re.search(rf"^## {num}\. .*?(?=^## \d+\. |\Z)", text, re.M | re.S)
    return m.group(0).strip() if m else ""


def load_pipeline():
    p = pathlib.Path("results/pipeline/sotorasib_pipeline.json")
    if not p.exists():
        sys.exit("results/pipeline/sotorasib_pipeline.json 이 없다. "
                 "먼저 run_pipeline.py --only merge 를 돌린다.")
    return json.loads(p.read_text(encoding="utf-8"))


def digest_route(bundle, route_key):
    """경로 한 개를 표 형태 텍스트로 압축한다 (토큰 절약 + 출력 품질)."""
    r = bundle["routes"][route_key]
    lines = [f"[{route_key}] {r['n_steps']}단계, "
             f"state score {r['scores'].get('state score')}"]
    for s in r["steps"]:
        rm = s["route_model"]
        lines.append(
            f"  단계 {s['step']}: {s['reaction_smiles']}\n"
            f"      정책={rm['policy_name']} p={rm['policy_probability']:.3f} "
            f"분류={rm['classification']}"
        )
    lines.append("  전구체: " + ", ".join(
        f"{p['smiles']}{'' if p['in_stock'] else ' (재고 미보유)'}"
        for p in r["precursors"]
    ))
    return "\n".join(lines)


def digest_conditions(bundle, route_key):
    r = bundle["routes"][route_key]
    lines = [f"[{route_key}] 단계별 조건 — Parrot(온도 없음) / ASKCOS(온도 있음)"]
    for s in r["steps"]:
        p = s["conditions"]["parrot"][:1]
        a = s["conditions"]["askcos"][:1]
        p1 = p[0] if p else {}
        a1 = a[0] if a else {}
        bp = ""
        if a1.get("above_boiling_point"):
            bp = f"  ** 끓는점({a1['solvent_bp_c']}°C) 초과 — 열린 플라스크 불가 **"
        lines.append(
            f"  단계 {s['step']}:\n"
            # 구분자로 /를 쓰면 안 된다. /는 SMILES의 결합 기호여서 두 시약이
            # 하나의 엉뚱한 분자로 이어져 보고서에 그대로 실린다.
            f"      Parrot  촉매={p1.get('catalyst') or '없음'} "
            f"용매1={p1.get('solvent1') or '없음'} "
            f"용매2={p1.get('solvent2') or '없음'} "
            f"시약1={p1.get('reagent1') or '없음'} "
            f"시약2={p1.get('reagent2') or '없음'} "
            f"score={p1.get('score')}\n"
            f"      ASKCOS  온도={a1.get('temperature_c')}°C "
            f"용매={a1.get('solvent')} 시약={a1.get('reagent') or '없음'} "
            f"촉매={a1.get('catalyst') or '없음'} score={a1.get('score')}{bp}"
        )
    return "\n".join(lines)


def digest_yields(bundle, route_key):
    r = bundle["routes"][route_key]
    lines = [f"[{route_key}] 단계별 수율 — Yield-BERT / DRFP+XGBoost "
             f"(둘 다 Suzuki HTE 학습, 10 split 앙상블, 단위 %)"]
    prod = {"yield_bert_mean_pct": 1.0, "drfp_mean_pct": 1.0}
    for s in r["steps"]:
        y = s["yield"]
        lines.append(
            f"  단계 {s['step']}: Yield-BERT {y.get('yield_bert_mean_pct')}"
            f"±{y.get('yield_bert_std_pct')}  /  "
            f"DRFP {y.get('drfp_mean_pct')}±{y.get('drfp_std_pct')}"
        )
        for key in prod:
            v = y.get(key)
            if v is not None:
                prod[key] *= v / 100.0

    # 총수율은 여기서 계산해 넘긴다. 22단계 곱셈을 모델에 맡기면 틀리고,
    # 값이 1e-8 수준이라 소수로 전개하다 토큰 한도에 걸린다.
    lines.append(
        f"  [총수율 — 계산된 추정값, 지수 표기로 그대로 옮긴다]\n"
        f"      Yield-BERT 단계 곱: {prod['yield_bert_mean_pct'] * 100:.2e} %\n"
        f"      DRFP 단계 곱:      {prod['drfp_mean_pct'] * 100:.2e} %"
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 장 정의
# --------------------------------------------------------------------------

def build_chapters(bundle):
    route_digest = "\n\n".join(
        digest_route(bundle, k) for k in bundle["routes"]
    )
    cond_digest = "\n\n".join(
        digest_conditions(bundle, k) for k in bundle["routes"]
    )
    yield_digest = "\n\n".join(
        digest_yields(bundle, k) for k in bundle["routes"]
    )
    literature = analysis_section(4)
    limits = analysis_section(5)
    selection = analysis_section(1)
    run_results = analysis_section(2)
    # 대상 물질의 식별 정보. analysis.md에는 SMILES가 없어 모델이 지어냈던 자리다.
    # 번들에서 읽으므로 다른 분자에도 그대로 동작한다.
    identity = (
        f"[대상 물질 식별 정보 — 이 값을 그대로 옮겨 적는다]\n"
        f"  이름: {bundle['target']}\n"
        f"  SMILES: {bundle['target_smiles']}\n"
        f"  PubChem CID: {bundle['pubchem_cid']}"
    )

    return [
        {
            "no": 2, "title": "대상 물질과 선정 이유", "tokens": 1200,
            "context": identity + "\n\n" + selection,
            "task": "대상 물질 소토라십의 구조·용도·작용 기전을 쓰고, 이 물질을 고른 "
                    "이유를 자료에 있는 근거로 설명한다. "
                    "SMILES와 PubChem CID는 자료의 식별 정보에 있는 문자열을 한 글자도 "
                    "바꾸지 않고 그대로 옮긴다. SMILES를 직접 작성하거나 기억으로 "
                    "채우지 않는다. "
                    "KRAS G12C 억제제라는 점과 축 비대칭(atropisomerism)을 갖는다는 점을 포함한다.",
        },
        {
            "no": 3, "title": "사용한 AI 모델과 방법", "tokens": 1800,
            "context": skill_section(2) + "\n\n" + skill_section(4),
            "task": "사용한 모델을 표로 정리하고, 각 모델이 무엇을 입력받아 무엇을 "
                    "출력하는지 쓴다. 조건 예측 모델이 둘인 이유(Parrot은 온도를 "
                    "예측하지 않아 ASKCOS로 온도를 채웠다)와 수율 모델이 둘인 이유"
                    "(표현 방식 비교)를 반드시 설명한다. 실행 환경과 재현 방법도 간단히 쓴다.",
        },
        {
            "no": 4, "title": "예측 합성 경로", "tokens": 3000,
            "context": route_digest,
            "task": "두 경로를 각각 단계별로 설명한다. 단계마다 반응 유형과 메커니즘을 "
                    "친핵체·친전자체·이탈기 용어로 설명한다. "
                    "각 단계 그림은 마크다운 이미지 문법으로 넣어 실제로 보이게 한다. "
                    "형식은 정확히 다음과 같다 — "
                    "![그림 4.N. 단계 N 반응 모식도](../images/route_<n>/step_NN.png) "
                    "경로는 `../images/`로 시작해야 한다. 경로를 글자로만 적지 않는다. "
                    "route 1은 점수 최고, route 6은 보호기를 모두 명시한 "
                    "가장 정합적인 경로임을 밝힌다. "
                    "주의: 피리미딘 C4의 염소를 피페라진 질소가 치환하는 단계는 sp2 "
                    "탄소에서 일어나므로 SN2가 아니라 SNAr(addition-elimination)이다.",
        },
        {
            "no": 5, "title": "단계별 합성 조건", "tokens": 2600,
            "context": cond_digest + "\n\n[실제 공정 조건]\n" + literature,
            "task": "단계별 조건을 표로 정리하고 두 모델의 예측을 비교한다. "
                    "온도는 ASKCOS만 예측한다는 점을 명시한다. "
                    "끓는점을 넘는 조건은 반드시 표시하고, 열린 플라스크에서 재현할 수 "
                    "없다는 것과 실제 공정이 2-MeTHF(끓는점 80도)에서 78도로 돌려 이 "
                    "문제를 피한 것을 대조한다. 실제 공정 조건과도 비교한다. "
                    "시약1·시약2처럼 자료에 따로 적힌 성분은 표에서도 따로 적는다. "
                    "두 SMILES를 이어 붙여 하나처럼 쓰지 않는다.",
        },
        {
            "no": 6, "title": "단계별 예측 수율", "tokens": 3000,
            "context": yield_digest + "\n\n[실제 공정 수율]\n" + literature
                       + "\n\n[수율 모델 상세]\n" + read("results/yields/README.md"),
            "task": "단계별 수율과 총수율을 표로 정리하고 두 모델을 비교한다. "
                    "두 모델 모두 Suzuki HTE 데이터로 학습해 다른 반응은 학습 도메인 "
                    "밖이라는 점을 반드시 밝힌다. 실제 공정 수율(Suzuki 80%, 염소화+SNAr "
                    "66%, 전체 65%)과 비교해 과소평가 정도를 수치로 쓴다. "
                    "총수율은 자료에 이미 계산되어 있다. 직접 곱하지 말고 자료의 값을 "
                    "지수 표기(예: 1.2e-08 %)로 그대로 옮기고 '추정값'임을 표시한다. "
                    "0.0000... 같은 소수 전개를 절대 쓰지 않는다. "
                    "두 경로를 모두 다룬다. "
                    "총수율이 사실상 0이 되는 이유가 "
                    "학습 도메인 밖 단계에 낮은 수율이 반복 곱해진 탓임을 설명한다.",
        },
        {
            "no": 7, "title": "종합 결론", "tokens": 1800,
            "context": cond_digest + "\n\n" + literature,
            "task": "모든 모델 결과를 취합해 실제로 시도할 경로와 조건을 제안한다. "
                    "모델 출력을 그대로 쓰지 말고, 끓는점 규칙에 걸린 조건은 대안을 "
                    "제시한다(예: 더 높은 끓는점의 용매로 교체). "
                    "AI 예측 중 신뢰할 수 있는 부분과 사람이 보정해야 하는 부분을 구분한다.",
        },
        {
            "no": 8, "title": "AI 모델의 성능과 한계점", "tokens": 3200,
            "context": limits + "\n\n[조건 모델]\n" + read("results/parrot/README.md")
                       + "\n\n[온도 모델]\n" + read("results/askcos/README.md"),
            "task": "AI가 맞힌 것과 틀린 것을 모두 구체적으로 정리한다. "
                    "맞힌 것: 역합성 후반부 전략, POCl3 염소화의 톨루엔+DIPEA 등. "
                    "틀린 것: 자료의 한계점 항목을 수치와 함께 쓴다. "
                    "가장 중요한 결론은 '경로·조건·온도·수율 네 모델이 모두 통과시킨 "
                    "불가능한 반응이 있었다'는 것과 '사람이 검증 규칙을 적용하니 "
                    "끓는점 초과 조건 12건이 한 번에 걸러졌다'는 것이다. 이 둘을 강조한다.",
        },
        {
            "no": 10, "title": "참고문헌", "tokens": 900,
            "context": literature + "\n\n" + skill_section(2),
            "task": "참고문헌을 번호를 붙여 정리한다. 합성 논문, 사용한 AI 모델의 "
                    "원 논문과 저장소 주소를 포함한다. 강의자료는 출처에 적지 않는다.",
        },
        {
            "no": 1, "title": "요약", "tokens": 900,
            "context": "",  # 다른 장을 모두 쓴 뒤 생성한다
            "task": "보고서 전체의 요약을 반 쪽 이내로 쓴다. 대상 물질, 예측된 경로, "
                    "예상 총수율, 핵심 결론을 담는다. 아래에 다른 장의 내용이 주어진다.",
            "needs_others": True,
        },
    ]


SYSTEM_PROMPT = """너는 유기합성 전공자가 제출할 한국어 보고서를 쓰는 조수다.

작성 규칙
- 한국어 문어체(~이다, ~한다)로 쓴다. 구어체·높임말을 쓰지 않는다.
- 수치는 주어진 자료의 값을 그대로 쓴다. 자료에 없는 수치를 지어내지 않는다.
- SMILES는 자료에 있는 문자열만 복사해서 쓴다. 기억으로 쓰거나 직접 조립하지 않는다.
  자료에 없으면 그 자리에 SMILES를 적지 않는다.
- 계산으로 얻은 값은 반드시 "추정값"이라고 표시한다.
- 자료에 없는 내용은 쓰지 않는다. 결과가 없으면 "예측 실패"로 적는다.
- 표와 그림에는 번호와 제목을 붙인다.
- 전문용어는 강의 표기를 따른다: 친핵체, 친전자체, 이탈기, 사면체 중간체,
  addition-elimination, SNAr, Buchwald-Hartwig.

화학적 검증 규칙 (어기면 감점이다)
- sp2 탄소(방향족·비닐)에는 SN2가 일어나지 않는다. 방향족 C-N 결합은 SNAr이거나
  Pd 촉매 반응이다.
- 1차 탄소에서 SN1은 일어나지 않는다.
- 카복실산 유도체는 반응성이 높은 쪽에서 낮은 쪽으로만 변환된다.
- 열린 플라스크는 용매 끓는점보다 뜨거워지지 않는다. 예측 온도가 용매 끓는점보다
  높으면 그 조건은 그대로 쓸 수 없고, 반드시 그 사실을 지적한다.
- 원자 수지가 맞는다고 메커니즘이 성립하는 것은 아니다. 이탈기가 생성물에
  치환기로 남아 있는 단계는 틀린 단계다.
- 조건 모델이 조건을 냈다고 그 반응이 일어나는 것은 아니다.
- 계산값은 추정이지 실험적 진실이 아니다.

출력 형식
- 마크다운으로 쓴다. 장 제목은 `## N. 제목` 형식의 헤딩 하나로 시작한다.
- 서론·맺음말 같은 군더더기를 붙이지 않는다. 요청받은 장의 내용만 쓴다.
"""


# --------------------------------------------------------------------------
# API 호출
# --------------------------------------------------------------------------

def call_solar(system, user, max_tokens, retries=3):
    key = os.environ.get("UPSTAGE_API_KEY")
    if not key:
        sys.exit("UPSTAGE_API_KEY 환경변수가 없다.")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    # 한글이 깨지지 않도록 UTF-8 바이트로 직접 보낸다
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            API_URL, data=data,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return (
                body["choices"][0]["message"]["content"],
                body.get("usage", {}),
            )
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if attempt == retries:
                sys.exit(f"API 오류 {e.code}: {detail}")
            print(f"    재시도 {attempt}/{retries} (HTTP {e.code})")
            time.sleep(5 * attempt)
        except Exception as e:  # noqa: BLE001
            if attempt == retries:
                sys.exit(f"API 호출 실패: {e}")
            print(f"    재시도 {attempt}/{retries} ({e})")
            time.sleep(5 * attempt)


# --------------------------------------------------------------------------

# 보고서는 results/report/에 놓이고 그림은 results/images/에 있으므로
# 보고서 기준 상대 경로는 ../images/ 다.
IMG_RE = re.compile(r"(?:\.\./images|results/images)/(route_\d+/[A-Za-z0-9_]+\.png)")


def normalize_images(text):
    """그림 참조를 깃허브에서 보이는 마크다운 이미지로 바꾼다.

    모델이 경로를 글자로만 적거나 경로 깊이를 틀리는 일이 있어, 생성물에
    기대지 않고 여기서 한 번 더 맞춘다. 보고서를 직접 고치는 것이 아니라
    조립 규칙이므로 다른 분자에도 그대로 동작한다.
    """
    # 1) 이미 이미지 문법인 것은 경로만 ../images/로 맞춘다
    text = re.sub(
        r"!\[([^\]]*)\]\(\s*(?:\.\./images|results/images)/(route_\d+/[A-Za-z0-9_]+\.png)\s*\)",
        r"![\1](../images/\2)",
        text,
    )

    # 2) 글자로만 적힌 그림 줄을 이미지로 바꾼다
    #    예: "그림: 그림 4.1. `results/images/route_1/step_01.png` — 단계 1 반응 모식도."
    def line_to_image(m):
        caption = (m.group("cap") or "").strip(" .—-")
        label = (m.group("label") or "").strip(" .")
        alt = f"{label}. {caption}" if label and caption else (label or caption or "반응 모식도")
        return f"![{alt}](../images/{m.group('path')})"

    text = re.sub(
        r"^\s*(?:그림[:：]\s*)?(?P<label>그림\s*[\d.]+)?\s*\.?\s*`?"
        r"(?:\.\./images|results/images)/(?P<path>route_\d+/[A-Za-z0-9_]+\.png)`?"
        r"\s*(?:[—–-]\s*(?P<cap>[^\n]*))?$",
        line_to_image,
        text,
        flags=re.M,
    )
    return text


def assemble():
    """장 파일을 번호 순으로 합쳐 보고서 하나로 만든다."""
    OUTDIR.mkdir(parents=True, exist_ok=True)
    parts = ["# 소토라십(Sotorasib, AMG 510) AI 합성 예측 보고서", ""]
    missing = []
    for no in range(1, 11):
        f = CHAPTER_DIR / f"ch{no:02d}.md"
        if f.exists():
            parts += [normalize_images(f.read_text(encoding="utf-8").strip()), ""]
        elif no == 9:
            continue  # 선택 항목
        else:
            missing.append(no)
    out = OUTDIR / "report_v1.md"
    out.write_text("\n".join(parts), encoding="utf-8")
    words = len(out.read_text(encoding="utf-8"))
    print(f"\n보고서 조립 완료: {out} ({words:,}자)")
    if missing:
        print(f"  빠진 장: {missing}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chapter", type=int, nargs="+",
                    help="다시 생성할 장 번호. 생략하면 전체")
    ap.add_argument("--assemble", action="store_true",
                    help="생성 없이 기존 장 파일을 합치기만")
    args = ap.parse_args()

    if args.assemble:
        assemble()
        return

    CHAPTER_DIR.mkdir(parents=True, exist_ok=True)
    bundle = load_pipeline()
    chapters = build_chapters(bundle)
    if args.chapter:
        chapters = [c for c in chapters if c["no"] in args.chapter]
        if not chapters:
            sys.exit("해당 번호의 장이 없다.")

    total_tokens = 0
    for c in chapters:
        print(f"\n[{c['no']}장] {c['title']} 생성 중...")

        context = c["context"]
        if c.get("needs_others"):
            others = []
            for no in (2, 4, 5, 6, 7, 8):
                f = CHAPTER_DIR / f"ch{no:02d}.md"
                if f.exists():
                    others.append(f.read_text(encoding="utf-8")[:2500])
            context = "\n\n".join(others)

        user = (
            f"다음 자료를 바탕으로 보고서의 {c['no']}장 「{c['title']}」을 쓴다.\n\n"
            f"[지시]\n{c['task']}\n\n"
            f"[자료]\n{context}"
        )
        text, usage = call_solar(SYSTEM_PROMPT, user, c["tokens"])
        (CHAPTER_DIR / f"ch{c['no']:02d}.md").write_text(text, encoding="utf-8")
        used = usage.get("total_tokens", 0)
        total_tokens += used
        print(f"  완료 — {len(text):,}자, {used:,} 토큰")

    print(f"\n총 {total_tokens:,} 토큰 사용")
    assemble()


if __name__ == "__main__":
    main()
