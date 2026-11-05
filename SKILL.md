---
name: synthesis-route-report
description: 약물 이름 또는 SMILES가 주어지면 AI 모델로 합성 경로, 합성 조건, 수율을 예측하고 그 결과를 정리한 한국어 합성 보고서(docx/pdf, 20쪽 이하)를 작성한다.
---

# 합성 경로 예측 보고서 스킬

이 스킬은 주어진 약물에 대해 여섯 개의 AI 모델(경로 2, 조건 2, 수율 2)을 실행하고, 그 결과를 모아 합성 실험 결론까지 담은 보고서를 작성한다.

## 1. 입력

다음 중 하나를 받는다.

- 약물 이름 (예: `Sotorasib`)
- SMILES 문자열 (예: `CC(=O)Nc1ccc(O)cc1`)

이름만 주어지면 PubChem에서 canonical SMILES를 찾아 사용하고, 사용한 SMILES를 보고서에 적는다.

## 2. 사용하는 모델

| 역할 | 모델 | GitHub |
|---|---|---|
| 합성 경로 | AiZynthFinder | https://github.com/MolecularAI/aizynthfinder |
| 합성 경로 | SynthEx | https://github.com/schwallergroup/synthex/tree/submission |
| 합성 조건 | ASKCOS context recommender | https://gitlab.com/mlpds_mit/askcosv2/context_recommender |
| 합성 조건 | Parrot | https://github.com/wangxr0526/Parrot |
| 수율 | Yield-BERT (rxn_yields) | https://github.com/rxn4chemistry/rxn_yields |
| 수율 | DRFP | https://github.com/reymond-group/drfp |

## 3. 환경 설치

<!-- TODO: 모델별 conda 환경과 설치 명령어 -->

### AiZynthFinder

```powershell
conda create -n aizynth-env python=3.11 -y
conda activate aizynth-env
pip install aizynthfinder==4.4.1 pyarrow==17.0.0 onnxruntime==1.19.2
mkdir "$env:USERPROFILE\github\aizynth-data"
download_public_data "$env:USERPROFILE\github\aizynth-data"
```

`download_public_data`가 받는 파일과 자동으로 만드는 `config.yml`은 다음과 같다. `config.yml` 안의 경로는 내려받은 폴더의 절대경로로 채워진다.

| 구분 | 이름 | 파일 |
|---|---|---|
| expansion policy | `uspto` | `uspto_model.onnx`, `uspto_templates.csv.gz` |
| expansion policy | `ringbreaker` | `uspto_ringbreaker_model.onnx`, `uspto_ringbreaker_templates.csv.gz` |
| filter policy | `uspto` | `uspto_filter_model.onnx` |
| stock | `zinc` | `zinc_stock.hdf5` |

### SynthEx
<!-- TODO -->

### ASKCOS context recommender
<!-- TODO -->

### Parrot
<!-- TODO -->

### rxn_yields
<!-- TODO -->

### DRFP
<!-- TODO -->

## 4. 실행 순서

<!-- TODO: 모델을 하나씩 붙일 때마다 명령어와 출력 형식을 채운다 -->

1. **경로 예측 (AiZynthFinder)**

   ```powershell
   conda activate aizynth-env
   aizynthcli --config "$env:USERPROFILE\github\aizynth-data\config.yml" --smiles "<SMILES>"
   ```

   - 별도 옵션이 없으면 expansion policy `uspto`, filter policy `uspto`, stock `zinc`가 사용된다.
   - 출력: 탐색 통계는 터미널에, 상위 경로는 `trees.json`에 저장된다 (`--output`으로 파일 이름 지정 가능).
   - <!-- TODO: trees.json 구조, 상위 3개 경로 추출 방법 -->
2. **경로 예측 (SynthEx)**: <!-- TODO -->
3. **단계별 반응 SMILES 추출**: <!-- TODO -->
4. **합성 조건 예측 (Parrot, ASKCOS)**: <!-- TODO -->
5. **수율 예측 (Yield-BERT, DRFP)**: <!-- TODO -->
6. **구조 이미지 생성 (RDKit)**: <!-- TODO -->
7. **결과 취합**: <!-- TODO: 모든 결과를 하나의 json으로 모으는 방법 -->
8. **보고서 작성**: 아래 5~6절에 따라 작성한다.

## 5. 보고서 목차

보고서는 docx 또는 pdf로, 20쪽 이하로 작성한다.

1. **요약**: 대상 물질, 예측된 최적 경로, 예상 총수율, 핵심 결론을 반 쪽 이내로 쓴다.
2. **대상 물질과 선정 이유** (필수): 물질의 구조, 용도, 이 물질을 고른 이유를 쓴다.
3. **사용한 AI 모델과 방법**: 2절의 표를 넣고, 각 모델이 무엇을 입력받아 무엇을 출력하는지 쓴다.
4. **예측 합성 경로** (필수): 경로마다 단계별 반응식을 구조 이미지로 넣고, 단계마다 반응 유형과 메커니즘(친핵체, 친전자체, 이탈기 등)을 설명한다.
5. **단계별 합성 조건** (필수): 단계마다 용매, 시약, 촉매, 온도를 표로 정리하고 두 모델의 예측을 비교한다.
6. **단계별 예측 수율** (필수): 단계별 수율과 총수율을 표로 정리하고 두 모델의 예측을 비교한다.
7. **종합 결론**: 모든 모델의 결과를 취합해 실제로 시도할 합성 경로와 조건을 제안한다.
8. **AI 모델의 성능과 한계점** (필수): 예측이 실패하거나 문헌과 다른 경우를 구체적으로 정리한다. 7절의 검증 규칙에 걸린 예측은 모두 여기에 적는다.
9. **추가 분석** (선택): MOPAC 양자 계산, EPI Suite 물성 예측, Discovery Studio Visualizer 3차원 구조, 하네스별 결과 비교. 7.3절과 7.4절의 사용 범위를 지킨다. <!-- TODO: 각 도구 실행 명령어 -->
10. **참고문헌**

## 6. 작성 규칙

<!-- TODO: 첫 보고서를 생성한 뒤 어색한 부분을 보고 다듬는다 -->

- 한국어 문어체(~이다, ~한다)로 쓴다.
- 수치는 모델 출력값을 그대로 쓰고, 계산값이나 추정값은 "추정값"이라고 표시한다.
- 모델 출력에 없는 내용을 지어내지 않는다. 결과가 없으면 "예측 실패"로 적고 8장에 정리한다.
- 그림과 표에는 번호와 제목을 붙인다.

## 7. 화학적 검증 규칙 (반드시 지킬 것)

아래는 보고서에 **써서는 안 되는 주장**이다. AI 모델이 이런 결과를 냈더라도 그대로 쓰지 않고, 8장 "AI 모델의 성능과 한계점"에 예측 실패 사례로 정리한다. 각 항목은 모델 출력을 보고서에 옮기기 전에 확인한다.

### 7.1 반응 타당성

| 검증 항목 | 쓰면 안 되는 주장 | 확인 방법 |
|---|---|---|
| SN2 가능 여부 | sp² 탄소(방향족 고리, 비닐)나 고리 탄소에 SN2(뒤쪽 공격)가 일어난다 | 공격받는 탄소가 sp³인지 확인한다. LUMO 에너지가 낮아도 sp²면 SN2는 불가능하다. 방향족 C–N 결합은 Pd 촉매(Buchwald–Hartwig)로 만든다 |
| SN1 가능 여부 | 1차(1°) 탄소나 메틸 탄소에서 SN1이 일어난다 | 카보양이온 안정성은 3° > 2° > 1° > 메틸이다. 1°에서는 양이온이 불안정해 SN1이 일어나지 않는다 |
| 카복실산 유도체 변환 | 아마이드에서 acid chloride를, 또는 반응성이 낮은 유도체에서 높은 유도체를 직접 만든다 | 반응성 높음 → 낮음 방향으로만 변환된다. acid chloride → 아마이드는 가능하지만 역방향은 불가능하다 |
| 아민 알킬화 | 아민에 알킬 할라이드를 넣으면 한 번만 반응해 단일 생성물이 나온다 | N–H가 둘 이상이면 overalkylation이 일어난다. N–H가 하나뿐일 때만 한 번에 멈춘다 |
| 염기 선택 | NaOH로 알코올을 완전히 알콕사이드로 만든다 | 짝산 pKa를 비교한다. 물 15.7과 에탄올 16은 비슷해서 반만 진행된다. 완전히 탈양성자화하려면 NaH 같은 더 강한 염기가 필요하다 |
| 무수 조건 | NaH, LiAlH₄를 물이나 알코올 용매에서 쓴다 | 이 시약들은 물을 만나면 H₂를 내며 분해된다. 반드시 무수 조건으로 적는다 |
| 반응 온도 | 예측된 반응 온도가 용매의 끓는점보다 높다 | 열린 플라스크는 용매 끓는점보다 뜨거워지지 않는다. 예측 온도가 용매 끓는점보다 높으면 용매를 바꾸거나 가압 조건임을 명시한다 |
| 반응 단계 분류 | 같은 반응을 한 가지 역할로만 설명한다 | 같은 화학 반응이 경로에 따라 목표 결합 형성일 수도, 보호(protection)일 수도 있다. AiZynthFinder가 분류한 이름을 그대로 쓰지 말고 경로 안에서의 역할로 판단한다 |

### 7.2 전하와 극성 표기

- δ+·δ−(부분전하)를 실제 +1·−1 전하나 형식전하로 쓰지 않는다. 카보닐의 C와 O는 둘 다 형식전하 0이다.
- 형식전하는 FC = V − N − B로 계산한다 (V 원자가전자, N 비공유전자 수, B 결합차수 합).
- 결합 극성과 분자 극성을 구분한다. 결합이 극성이어도 대칭이면 분자는 무극성이다 (CO₂).
- 1°·2°·3° 탄소 구분은 결합 차수(단일·이중·삼중)가 아니라 서로 다른 탄소 이웃의 개수로 센다.

### 7.3 MOPAC 결과 사용 범위 (9장 추가 분석)

- pKa 계산은 **O–H(산소에 붙은 이온화 가능 수소)에만** 적용한다. 다음은 적용 범위가 아니므로 보고서에 쓰지 않는다.
  - N–H의 일반적인 이온화
  - 염기성 site의 protonation
  - 분자 전체의 ionization-state 예측
  - 실험적 pKa 값으로의 해석
- pKa 옵션은 PM6에서만 작동한다. 키워드 줄에 `PM6`와 `pKa`를 함께 쓴다. PM6가 없으면 `Calculation abandoned`로 끝난다.
- geometry optimization 단계에 COSMO를 넣지 않는다. pKa 단계에서 MOPAC이 임시로 사용한다.
- `CHARGES`와 `CHARGE=n`은 다른 키워드다. `CHARGES`는 전하를 띠는 원자를 진단한 뒤 종료하고, `CHARGE=n`은 계산계의 총전하를 지정한다. `CHARGES`를 `CHARGE`의 복수형으로 설명하지 않는다.
- `.out`이나 `.arc` 파일을 직접 수정한 값은 재계산 결과가 아니다. 값을 바꿀 때는 `.mop`을 고쳐 다시 실행한다.
- `.out` 마지막 줄에 `JOB ENDED NORMALLY`가 있는 결과만 보고서에 쓴다. 보고서에 MOPAC 버전, 대상 원자 번호, 값, 종료 상태를 함께 적는다.
- MOPAC 계산값은 추정값이며 실험적 진실이 아니다. 숫자 옆에 "추정값"을 붙인다.

### 7.4 EPI Suite 결과 사용 범위 (9장 추가 분석)

- ESTIMATED 값과 EXPERIMENTAL 값을 구분해서 적는다. 둘을 섞어 하나의 값으로 제시하지 않는다.
- 어느 모델로 계산한 값인지 모델 이름까지 적는다 (끓는점 MPBPWIN, 물용해도 WSKOWWIN·WATERNT 등). 모델마다 값이 다르므로 모델 이름 없는 값은 쓰지 않는다.
- 물성 값을 쓸 때 온도, pH, 이온화 상태, 고체 형태 조건을 함께 적는다.
- 실험값이 있으면 출처(문헌 이름과 연도)를 적고, 없으면 "실험값 없음"으로 적는다.
