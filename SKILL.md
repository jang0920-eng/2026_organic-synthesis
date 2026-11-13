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

모델들이 서로 충돌하는 의존성을 요구하므로 conda 환경을 나눠 쓴다. 한 환경에 다 몰아넣으려 하지 않는다.

| 환경 | 쓰는 모델 | 핵심 버전 |
|---|---|---|
| `aizynth-env` | AiZynthFinder, RDKit 작도 | Python 3.11, aizynthfinder 4.4.1, onnxruntime 1.19.2 |
| `parrot-env` | Parrot, rxn_yields, DRFP | Python 3.9, torch 1.13.1, transformers 4.18.0 |
| `askcos-env` | ASKCOS context recommender | Python 3.8, tensorflow-cpu 2.7.4 |

`run_pipeline.py`가 단계마다 해당 환경의 `python.exe`를 직접 부르므로, 환경을 번갈아 활성화할 필요는 없다.

**Windows 공통 주의**: 옛 버전을 고정하면 pip가 소스 빌드로 빠져 실패하는 경우가 많다. `--only-binary=:all:`로 wheel을 강제하고, wheel이 없는 순수 파이썬 패키지는 따로 설치한다.

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

**Docker는 필요 없다.** repo의 Docker/Singularity는 FastAPI 서비스를 감싸는 포장이고, 예측기 클래스를 직접 import하면 서비스 없이 쓸 수 있다. conda 환경 하나(약 1.5GB)로 끝난다.

```powershell
git clone https://gitlab.com/mlpds_mit/askcosv2/context_recommender.git askcos-context-src
conda create -n askcos-env python=3.8 -y
conda activate askcos-env
pip install --only-binary=:all: tensorflow-cpu==2.7.4 scikit-learn==1.0.2 `
            scipy==1.7.3 "numpy<1.24" rdkit==2022.9.5 protobuf==3.19.0
```

모델 가중치는 Dropbox 직링크라 로그인 없이 받는다 (143MB). repo의 `scripts/download_trained_models.sh`는 `wget`·`tar`를 쓰므로 Windows에서는 아래처럼 받는다.

```powershell
curl -L -o v1.tar.gz "https://www.dropbox.com/scl/fi/97g21iqzxz4gw4l83xjye/v1.tar.gz?rlkey=orny64sno8kd3cbspgbs53qd0&dl=1"
tar xzf v1.tar.gz -C app/resources/models/context/
```

`weights.h5`(155MB), `model.json`, 라벨 사전 5개, 용매 EHS 점수표가 들어 있다.

**이 모델만 온도를 예측한다.** Parrot의 공개본은 온도를 내지 않으므로, 보고서의 "합성 조건" 중 온도는 여기서 나온다.

### rxn_yields

Parrot과 같은 스택(rxnfp + simpletransformers)을 쓰므로 `parrot-env`를 그대로 쓴다.

```powershell
git clone https://github.com/rxn4chemistry/rxn_yields.git rxn-yields-src
conda activate parrot-env
```

학습된 모델 818MB가 repo에 동봉되어 있어 별도 다운로드가 필요 없다.

**출력은 표준화된 값이다.** 학습 세트의 mean·std로 역표준화하고 ×100, 0–100 클립해야 수율(%)이 된다. 이 보정을 빼면 숫자가 의미가 없다.

| 동봉 모델 | 보정 가능? |
|---|---|
| `suzuki_miyaura` | 가능 — HTE 데이터가 repo에 있다 (mean 0.4033, std 0.2819) |
| `buchwald_hartwig` | 가능 — HTE 데이터가 repo에 있다 |
| `uspto` (범용) | **불가능** — 학습 데이터가 로그인이 필요한 IBM Box에 있다 |

Windows에서 두 곳을 고쳐야 한다.

- `model.loss_fct = None`을 넣는다. rxnfp 0.1.0이 옛 simpletransformers 기준이라 이 속성을 설정하지 않는데, 0.63.6의 `predict`가 요구한다.
- `use_multiprocessing: False`, `process_count: 1`로 둔다. fork가 없어 피처 변환이 배치당 30초 이상 걸린다.

### DRFP

**DRFP은 지문 인코더일 뿐 수율 모델이 아니다.** 회귀 모델을 직접 학습해야 한다. Yield-BERT와 같은 HTE 데이터·같은 split으로 XGBoost를 학습하면 반응 표현만 다른 비교가 된다.

```powershell
conda activate parrot-env
pip install drfp
pip install --only-binary=:all: xgboost
```

Windows 패치가 하나 필요하다. drfp 0.3.6은 `blake2b(digest_size=4)` 결과를 `np.int32`에 담는데, 이 값은 부호 없는 32비트라 2^31을 넘으면 `OverflowError`가 난다. `np.uint32`로 담으면 된다 (digest의 원래 의미에도 맞다).

### Parrot

repo는 Linux에서만 테스트되었다. 동봉된 `envs_cpu.yaml`은 Linux 전용 빌드 문자열이 박힌 conda export라 Windows에서 쓸 수 없으므로, 코드가 실제로 import하는 것만 설치한다.

```powershell
git clone https://github.com/wangxr0526/Parrot.git parrot-src
conda create -n parrot-env python=3.9 -y
conda activate parrot-env

pip install torch==1.13.1
pip install transformers==4.18.0 tokenizers==0.12.1 huggingface-hub==0.11.1 `
            simpletransformers==0.63.6 numpy==1.23.5 pandas==1.3.5
pip install --no-deps rxnfp
pip install --only-binary=:all: scipy==1.10.1 scikit-learn==1.3.2 rdkit==2023.9.6 `
            matplotlib seaborn ipython pyyaml
pip install tensorboardX bertviz pandarallel gdown
pip install --only-binary=:all: pyarrow==12.0.1
pip uninstall -y sentencepiece
```

Windows에서 반드시 필요한 조치 네 가지다.

| 조치 | 이유 |
|---|---|
| `--only-binary=:all:`로 wheel 강제 | numpy를 낮게 고정하면 pip가 scipy를 2019년 sdist까지 거슬러 내려가 소스 빌드에 실패한다 |
| `sentencepiece` 제거 | `pandas` 뒤에 import하면 access violation으로 프로세스가 죽는다. Parrot은 BERT 토크나이저만 쓰므로 없어도 된다 |
| `pyarrow==12.0.1` 고정 | `datasets 2.13.2`가 최신 pyarrow에서 삭제된 `PyExtensionType`을 참조한다 |
| `rxnfp`는 `--no-deps` | rxnfp가 Windows wheel이 없는 옛 버전을 하드 핀한다. 실제로 쓰는 `rxnfp.models`의 의존성은 이미 설치되어 있다 |

`inference.py`는 한 곳을 고쳐야 한다. `pandarallel`의 `parallel_apply`가 Windows에서 `NameError`로 죽는다 (fork가 없어 워커가 spawn으로 뜨고 자식이 모듈 전역 함수를 찾지 못한다). Windows에서는 단일 프로세스 `apply`를 쓴다.

모델·데이터는 추론에 필요한 두 개만 받는다.

```powershell
gdown "https://drive.google.com/uc?id=1aX70qzZrJ9TZ9KpqnvUVR8WBxiTwXOsI" -O dataset/source_dataset/USPTO_condition_final.zip
gdown "https://drive.google.com/uc?id=1gFV2KdVKaLCTeb3nrzopyYHXbM0G_cr_" -O outputs/Parrot_train_in_USPTO_Condition_enhance.zip
```

데이터셋 zip은 전부 풀면 2.3GB다. 추론이 읽는 것은 `USPTO_condition_alldata_idx.pkl`(9.7KB) 하나이므로 작은 파일만 푼다.

**온도는 예측되지 않는다.** 공개된 USPTO 모델의 출력은 촉매 1개·용매 2개·시약 2개뿐이다. 온도를 내는 모델은 Reaxys-TotalSyn-Condition 학습본인데 Reaxys 라이선스가 필요해 배포되지 않는다.

## 4. 실행 순서

1. **경로 예측 (AiZynthFinder)**

   ```powershell
   conda activate aizynth-env
   aizynthcli --config "$env:USERPROFILE\github\aizynth-data\config.yml" --smiles "<SMILES>"
   ```

   - 별도 옵션이 없으면 expansion policy `uspto`, filter policy `uspto`, stock `zinc`가 사용된다.
   - 출력: 탐색 통계는 터미널에, 상위 경로는 `trees.json`에 저장된다 (`--output`으로 파일 이름 지정 가능).
   - `trees.json`은 **경로 리스트**다. 각 경로는 mol 노드와 reaction 노드가 번갈아 나오는 트리이고, 리스트 앞쪽일수록 점수가 높다. 상위 n개를 쓰려면 앞에서 n개를 자르면 된다.
   - mol 노드: `smiles`, `in_stock`, `children`. 루트의 `scores`에 `state score`·`number of reactions`·`number of pre-cursors in stock`이 있다.
   - reaction 노드: `metadata`에 `policy_name`, `policy_probability`, `classification`이 있다. **`smiles` 필드는 역합성 템플릿이지 반응식이 아니다.**
   - `is_solved: false`여도 경로는 저장된다. 재고에 없는 전구체가 남았다는 뜻이므로, 그 전구체가 무엇인지 확인해 보고서에 적는다.
2. **경로 예측 (SynthEx)**: <!-- TODO -->
3. **단계별 반응 SMILES 추출**

   ```powershell
   python scripts/extract_steps.py results/sotorasib_trees_v4.json --route 1 6
   ```

   - reaction 노드의 `smiles`는 역합성 템플릿이지 반응식이 아니다. 실제 반응은 (자식 mol들) `>>` (부모 mol)로 조립한다.
   - 단계 번호는 정반응 순서다. 역합성 트리의 깊은 노드가 먼저 일어나는 반응이므로 깊이 내림차순으로 정렬하고, 같은 깊이면 서브트리가 깊은 쪽(주 사슬)을 먼저 쓴다.
   - 출력: `results/steps/route_<n>.json`(반응 SMILES와 메타데이터), `route_<n>.md`(표).
4. **합성 조건 예측 (Parrot, ASKCOS)**

   ```powershell
   python scripts/make_parrot_input.py results/steps/route_1.json results/steps/route_6.json

   conda activate parrot-env
   cd parrot-src
   python inference.py --config_path configs/config_inference_use_uspto.yaml `
                       --input_path  <repo>/results/parrot/route_1_input.txt `
                       --output_path <repo>/results/parrot/route_1_conditions.csv `
                       --num_workers 2 --inference_batch_size 8 --gpu -1
   ```

   - `--gpu -1`이 CPU 추론이다. 10단계에 3분 남짓 걸린다.
   - 출력 csv의 열은 `rxn_smiles, top-k, catalyst1, solvent1, solvent2, reagent1, reagent2, scores`다. **온도 열은 없다.** `rxn_smiles`는 각 반응의 첫 행에만 채워지고 나머지는 빈 칸이며, 단계마다 top-15가 나온다.
   - 출력에는 단계 번호가 없다. `make_parrot_input.py`가 만든 `route_<n>_index.csv`로 줄 번호와 단계 번호를 맞춘다.
   - 읽을 수 있는 표로 정리: `python scripts/summarize_parrot.py --route 1 6`
   - `scores`는 빔 서치의 로그 확률이라 0에 가까울수록 확신이 높다.

   온도는 ASKCOS로 채운다. Docker 없이 예측기를 직접 호출한다.

   ```powershell
   conda activate askcos-env
   python scripts/run_askcos.py --route 1 6
   ```

   - 출력: 조건마다 `[온도(°C), 용매, 시약, 촉매, EHS점수, 최고EHS여부]`.
   - 스크립트가 7.1절의 끓는점 규칙을 자동으로 적용해, 예측 온도가 용매 끓는점을 넘는 조건에 `끓는점 초과` 표시를 단다. **이 표시가 붙은 조건은 보고서에 그대로 쓰지 않는다.**
5. **수율 예측 (Yield-BERT, DRFP)**

   ```powershell
   conda activate parrot-env
   python scripts/run_rxn_yields.py  --route 1 6 --splits 10
   python scripts/run_drfp_yields.py --route 1 6 --splits 10
   ```

   - 두 모델 모두 **같은 Suzuki HTE 데이터, 같은 split**으로 학습한다. 반응 표현 방식만 다르므로 비교가 공정하다.
   - 출력: 단계마다 `yield_mean_pct`와 `yield_std_pct`(앙상블 10개의 표준편차). 편차가 크면 그 예측은 신뢰할 수 없다는 뜻이다.
   - `run_drfp_yields.py`는 홀드아웃 R²·RMSE를 함께 출력한다. **이 값이 정상인데 대상 분자 예측이 빗나가면 모델 결함이 아니라 학습 도메인 밖이라는 뜻이다.** 보고서에 이 구분을 적는다.
   - **메모리 주의**: DRFP 단계는 XGBoost를 10번 학습해 수 GB를 쓴다. RAM 8GB 이하에서는 `--splits`를 5 이하로 줄인다.

6. **구조 이미지 생성 (RDKit)**

   ```powershell
   conda activate aizynth-env
   python scripts/draw_route.py results/steps/route_1.json
   ```

   - 출력(`results/images/route_<n>/`): 단계별 반응식 `step_NN.png`, 목표 분자 `target.png`, 전구체 모음 `precursors.png`, 전체 경로 `route_overview.png`.
   - `--format svg`로 벡터 이미지도 만들 수 있다. 보고서에 크게 넣을 때 쓴다.

7. **결과 취합**

   ```powershell
   python scripts/run_pipeline.py --only merge
   ```

   - `results/pipeline/sotorasib_pipeline.json` 하나에 단계마다 반응 SMILES, 경로 모델 확률, 조건 후보(Parrot·ASKCOS 각 3개), 수율 2종, 끓는점 검증 결과, 반응식 이미지 경로가 들어간다.
   - 요약 표는 `sotorasib_pipeline.md`다. 보고서 5·6장의 표를 여기서 가져온다.
   - 전체를 처음부터 돌리려면 `python scripts/run_pipeline.py`. 단계는 `--only`·`--skip`으로 고른다.
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
| 이탈기의 행방 | 원자 수지(atom balance)가 맞으니 그 단계는 성립한다 | 원자 수지가 맞는다고 메커니즘이 성립하는 것은 아니다. 이탈기(아실 클로라이드의 Cl 등)가 생성물에 치환기로 남아 있는 단계는 틀린 단계로 본다 |
| 조건 예측의 신뢰 범위 | 조건 모델이 그럴듯한 조건을 냈으니 그 반응은 일어난다 | 조건 모델은 반응이 성립하는지 검증하지 않고, 성립한다고 전제하고 조건만 맞춘다. 화학적으로 불가능한 단계에도 표준 조건을 아무 경고 없이 낸다. 반응 타당성은 경로 단계에서 따로 판정한다 |
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
