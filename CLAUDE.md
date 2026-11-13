# 유기합성학 기말 프로젝트 (소토라십 AI 합성 예측)

## 세션을 시작할 때

사용자가 "진행상황 알려줘", "어디까지 했어", "할 일 뭐야" 같은 말을 하면
**먼저 이것부터 실행한다.** 문서의 체크박스는 갱신을 잊으면 낡지만, 이 스크립트는
산출물이 실제로 있는지 확인해서 진행률을 계산한다.

```bash
C:\Users\happi\miniconda3\envs\aizynth-env\python.exe scripts/status.py
```

완료/미완료 항목, 다음 할 일, 남은 TODO, 최근 커밋, 커밋 안 된 변경이 한 번에 나온다.
그다음 필요하면 아래를 읽는다.

| 파일 | 내용 |
|---|---|
| `HANDOFF.md` | 전체 맥락 — 물질 선정 이유, 일정표, 실행 결과, 문헌 비교, 한계점, 보고서 금지사항 |
| `SKILL.md` | 작업 절차 — 모델 설치·실행, 보고서 목차, **7절 화학적 검증 규칙** |
| `results/*/README.md` | 모델별 결과 분석과 문헌 비교 |

**특히 중요한 것은 `HANDOFF.md` 8장(보고서 금지·주의 사항)과 7장(한계점 목록)이다.**

## 과제 개요

- 대상: **소토라십 (Sotorasib, AMG 510)**, PubChem CID 137278711
- 제출: **2026-12-12** (12/13 예비일)
- 결과물: 한국어 합성 보고서 20쪽 이하 (docx 또는 pdf)
- 평가: 재현성 20점, 가독성 30점, "AI 모델의 성능과 한계점" 포함

**모델이 틀린 것도 성과다.** 상용 공정 논문(OPRD 2022)에 단계별 수율·조건이 숫자로
공개되어 있어 정량 비교가 가능하다는 이유로 이 물질을 골랐다. 한계점이 보고서의
핵심 내용이다.

## 디렉터리

```
scripts/      실행 스크립트 (아래 표 참조)
results/
  steps/      단계별 반응 SMILES (조건·수율 모델의 입력)
  parrot/     Parrot 조건 예측 (온도 없음)
  askcos/     ASKCOS 조건 예측 (온도 있음) + 끓는점 검증
  yields/     Yield-BERT와 DRFP 수율 예측
  images/     RDKit 반응식·구조식
  pipeline/   통합 결과 json
  report/     Solar Pro 4 생성 보고서
```

repo 밖에 있는 것 (용량이 커서 `.gitignore` 처리):
`../aizynth-data`(모델·재고), `../parrot-src`, `../askcos-context-src`, `../rxn-yields-src`

## 스크립트

| 스크립트 | 환경 | 하는 일 |
|---|---|---|
| `status.py` | 아무거나 | 진행 상황 요약 |
| `extract_steps.py` | 아무거나 | trees.json → 단계별 반응 SMILES |
| `make_parrot_input.py` | 아무거나 | Parrot 입력 txt + 줄↔단계 대응표 |
| `summarize_parrot.py` | 아무거나 | Parrot 출력에 단계 번호 붙여 표로 |
| `run_askcos.py` | `askcos-env` | 조건 예측(온도) + 끓는점 자동 검증 |
| `run_rxn_yields.py` | `parrot-env` | Yield-BERT 수율 앙상블 |
| `run_drfp_yields.py` | `parrot-env` | DRFP + XGBoost 수율 |
| `draw_route.py` | `aizynth-env` | RDKit 반응식 이미지 |
| `run_pipeline.py` | `aizynth-env` | 위 전부를 한 번에 + 결과 통합 |
| `generate_report.py` | 아무거나 | Solar Pro 4로 보고서 장별 생성 |

conda 환경은 서로 충돌하는 의존성 때문에 나눠 쓴다 (`SKILL.md` 3절).
`run_pipeline.py`가 단계마다 알맞은 환경의 `python.exe`를 직접 부른다.

## 이 기기에서 주의할 것

- **RAM 8GB로 빠듯하다.** DRFP 단계는 수 GB를 쓴다. 무거운 작업 전에 여유 메모리를
  확인하고 부족하면 `--splits`를 줄인다. 백그라운드 작업이 메모리 부족으로
  강제 종료된 적이 있다.
- **한글이 든 JSON을 셸 인자로 curl에 넘기면 깨진다** (400 invalid_request_body).
  UTF-8 파일로 쓰고 `--data-binary @파일`로 보내거나 파이썬에서 직접 요청한다.
- 콘솔이 cp949라 파이썬 스크립트는 stdout을 UTF-8로 재설정한다 (기존 스크립트에 포함됨).

## 작업 방식

- **커밋·푸시는 묻지 않고 한다.** 작업 단위가 끝나면 바로 `main`에 올린다.
- **보고서는 직접 고치지 않는다.** `generate_report.py`의 프롬프트를 고치고 해당 장만
  다시 생성한다. 그래야 스킬이 다른 분자에도 동작한다.
- **SKILL.md에는 에러·경고가 났던 과정을 적지 않는다.** 최종 버전과 명령어만 적는다.
- API 키(`UPSTAGE_API_KEY`)는 환경변수에만 두고 repo에 넣지 않는다.
