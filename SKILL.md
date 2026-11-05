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

   - 출력: 탐색 통계는 터미널에, 상위 경로는 `trees.json`에 저장된다.
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
8. **AI 모델의 성능과 한계점** (필수): 예측이 실패하거나 문헌과 다른 경우를 구체적으로 정리한다.
9. **추가 분석** (선택): <!-- TODO: MOPAC, EPI Suite, Discovery Studio, 하네스 비교 -->
10. **참고문헌**

## 6. 작성 규칙

<!-- TODO: 첫 보고서를 생성한 뒤 어색한 부분을 보고 다듬는다 -->

- 한국어 문어체(~이다, ~한다)로 쓴다.
- 수치는 모델 출력값을 그대로 쓰고, 계산값이나 추정값은 "추정값"이라고 표시한다.
- 모델 출력에 없는 내용을 지어내지 않는다. 결과가 없으면 "예측 실패"로 적고 8장에 정리한다.
- 그림과 표에는 번호와 제목을 붙인다.
