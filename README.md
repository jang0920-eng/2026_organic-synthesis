# 2026_organic-synthesis

AI 기반 신약 합성경로 예측 — 유기합성학 기말 프로젝트

공개 AI 모델로 표적 분자의 **합성경로 · 합성조건 · 산출율**을 예측하고, 그 결과를
실제 상용 공정 문헌과 비교해 모델의 성능과 한계를 정리한다.
보고서는 `SKILL.md`를 읽은 Solar Pro 4가 작성한다.

## 대상 물질

**소토라십 (Sotorasib, AMG 510)** — KRAS G12C 저해제, PubChem CID 137278711

```
C[C@H]1CN(CCN1C2=NC(=O)N(C3=NC(=C(C=C32)F)C4=C(C=CC=C4F)O)C5=C(C=CN=C5C(C)C)C)C(=O)C=C
```

분자식 C30H30F2N6O3, (S)-이성질체. 축 비대칭(atropisomerism)을 가진다.

이 물질을 고른 이유는 상용 공정 논문(*Org. Process Res. Dev.* **2022**)에 단계별 수율과
반응 조건이 숫자로 공개되어 있어, 세 가지 예측을 모두 같은 분자에 대해 실측값과
정량 비교할 수 있기 때문이다. 자세한 근거는 `HANDOFF.md` 1장에 있다.

## 사용한 예측 모델

| 역할 | 모델 | 상태 |
|---|---|---|
| 합성경로 | [AiZynthFinder](https://github.com/MolecularAI/aizynthfinder) | 사용 |
| 합성경로 | [SynthEx](https://github.com/schwallergroup/synthex/tree/submission) | 미사용 |
| 합성조건 | [Parrot](https://github.com/wangxr0526/Parrot) | 사용 — **온도는 예측하지 않음** |
| 합성조건 | [ASKCOS context recommender](https://gitlab.com/mlpds_mit/askcosv2/context_recommender) | 사용 — 온도 포함 |
| 산출율 | [rxn_yields](https://github.com/rxn4chemistry/rxn_yields) (Yield-BERT) | 사용 |
| 산출율 | [DRFP](https://github.com/reymond-group/drfp) + XGBoost | 사용 |

조건 모델을 둘 쓰는 이유는 Parrot의 공개 가중치가 온도를 내지 않기 때문이다
(온도를 내는 쪽은 Reaxys 라이선스가 필요해 배포되지 않는다).
수율 모델을 둘 쓰는 이유는 같은 데이터를 쓰되 반응 표현 방식이 다른 두 모델을
비교하기 위해서다.

## 결과 요약

- 경로 22단계(route 1은 10단계, route 6은 12단계)에 대해 조건·온도·수율을 모두 예측
- 조건 66개 중 **12개가 용매 끓는점을 넘었고, 전부 Suzuki 커플링 단계였다**
- 실제로 일어나지 않는 반응 하나가 **네 모델을 모두 통과했다** (경로 → 조건 → 온도 → 수율)

자세한 분석은 각 결과 폴더의 `README.md`를 본다.

## 구성

| 경로 | 내용 |
|---|---|
| `CLAUDE.md` | 작업 환경과 주의사항 요약 |
| `HANDOFF.md` | 전체 맥락 — 선정 근거, 일정, 실행 결과, 문헌 비교, 한계점 |
| `SKILL.md` | 스킬 정의 — 모델 설치·실행 절차, 보고서 목차, 화학적 검증 규칙 |
| `scripts/` | 실행 스크립트 |
| `results/steps/` | 단계별 반응 SMILES (조건·수율 모델의 입력) |
| `results/parrot/` | Parrot 조건 예측 |
| `results/askcos/` | ASKCOS 조건 예측(온도) + 끓는점 검증 |
| `results/yields/` | Yield-BERT와 DRFP 수율 예측 |
| `results/images/` | RDKit 반응식·구조식 |
| `results/pipeline/` | 통합 결과 json |
| `results/report/` | 생성된 보고서 |

## 재현 방법

### 1. 외부 저장소 받기

모델 소스는 용량이 커서 이 repo에 포함하지 않는다. **이 repo와 같은 폴더에 나란히**
받으면 스크립트가 자동으로 찾는다. 다른 위치에 받았다면 환경변수
(`PARROT_REPO`, `ASKCOS_REPO`, `RXN_YIELDS_REPO`) 또는 `--repo`로 알려준다.

```powershell
cd ..
git clone https://github.com/wangxr0526/Parrot.git parrot-src
git clone https://gitlab.com/mlpds_mit/askcosv2/context_recommender.git askcos-context-src
git clone https://github.com/rxn4chemistry/rxn_yields.git rxn-yields-src
```

### 2. conda 환경 만들기

모델들이 서로 충돌하는 의존성을 요구하므로 환경을 나눠 쓴다.
설치 명령은 `SKILL.md` 3절에 모델별로 적어두었다.

| 환경 | 모델 |
|---|---|
| `aizynth-env` | AiZynthFinder, RDKit 작도 |
| `parrot-env` | Parrot, rxn_yields, DRFP |
| `askcos-env` | ASKCOS |

### 3. Windows 패치 적용

Parrot의 `inference.py`는 Windows에서 그대로는 돌지 않는다
(fork가 없어 pandarallel 워커가 모듈 전역 함수를 찾지 못한다).

```powershell
python scripts/patch_parrot.py
```

여러 번 실행해도 안전하고, 원본은 `inference.py.orig`로 백업된다.

### 4. 모델 가중치 받기

ASKCOS와 Parrot은 가중치를 따로 받아야 한다. **Docker는 필요 없다.**
명령은 `SKILL.md` 3절에 있다.

### 5. 실행

```powershell
python scripts/run_pipeline.py
```

경로 추출 → 조건(Parrot·ASKCOS) → 수율(Yield-BERT·DRFP) → 이미지 → 통합을
한 번에 돌리고 `results/pipeline/sotorasib_pipeline.json` 하나로 모은다.

단계를 골라 돌리려면 `--only` 또는 `--skip`을 쓴다.
**RAM이 8GB 이하면 `--splits 5` 정도로 줄인다** (DRFP 단계가 XGBoost를 10번 학습한다).

진행 상황은 아래로 확인한다.

```powershell
python scripts/status.py
```
