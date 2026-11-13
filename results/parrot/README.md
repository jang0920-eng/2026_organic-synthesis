# Parrot 반응 조건 예측 (소토라십)

모델: [Parrot](https://github.com/wangxr0526/Parrot) — Wang et al., *Research* 2023, 6, 0231.
사용한 가중치: `Parrot_train_in_USPTO_Condition_enhance` (USPTO-Condition 학습, 공개본), CPU 추론.

입력은 AiZynthFinder v4의 route 1(10단계)과 route 6(12단계)에서 뽑은 반응 SMILES다.
22개 반응 전부 정규화를 통과했고 빠진 것은 없다.

## 1. 가장 중요한 제약 — 온도는 예측되지 않는다

공개된 USPTO 모델의 출력 항목은 **촉매 1개, 용매 2개, 시약 2개**뿐이다. 온도 열이 없다.

온도까지 내는 모델은 Reaxys-TotalSyn-Condition으로 학습한 쪽인데,
`configs/config_inference_use_reaxys.yaml`에 이렇게 적혀 있다.

```
database_fname: Reaxys_total_syn_condition.csv     # The license of Reaxys is required. It will not be shared here!
```

데이터도 학습된 가중치도 배포되지 않는다. 따라서 보고서가 요구하는 "용매·시약·촉매·온도" 중
**온도는 Parrot으로 채울 수 없다.**

그 결과 `SKILL.md` 7.1절의 검증 규칙 "예측 온도가 용매 끓는점보다 높으면 그 조건은 쓸 수 없다"를
Parrot 출력에는 적용할 수 없다. 이 규칙은 온도를 내는 다른 모델에만 적용된다.

## 2. 환경 구축 (Windows)

repo는 Linux에서만 테스트되었고, `envs_cpu.yaml`은 Linux 전용 빌드 문자열
(`_libgcc_mutex`, `h7b6447c_0`)이 박힌 conda export라 Windows에서 쓸 수 없다.
코드가 실제로 import하는 것만 추려 환경을 직접 만들었다.

```powershell
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

Windows에서 막힌 곳과 해결 방법은 아래와 같다. 네 가지 모두 Linux에서는 나타나지 않는다.

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `conda env create -f envs_cpu.yaml` 실패 | Linux 전용 빌드 문자열이 박힌 conda export | 코드의 실제 import만 추려 수동 설치 |
| scipy 설치 중 소스 빌드 실패 (`CCompiler is not defined`) | `numpy==1.21.5` 핀 때문에 pip가 scipy를 2019년 sdist(1.4.1)까지 거슬러 내려감 | numpy 1.23.5로 올리고 `--only-binary=:all:`로 wheel 강제 |
| import 중 **segfault** (access violation) | `pandas` 뒤에 `sentencepiece`를 import하면 죽는다 (transformers의 T5 토크나이저 경유) | Parrot은 BERT 토크나이저만 쓰므로 `sentencepiece` 제거 |
| `AttributeError: module 'pyarrow' has no attribute 'PyExtensionType'` | `datasets 2.13.2`가 최신 pyarrow에서 삭제된 API를 참조 | `pyarrow==12.0.1`로 고정 |

`rxnfp`를 `--no-deps`로 넣은 이유: rxnfp 0.1.0이 matplotlib 3.2.2 · scikit-learn 0.23.1 ·
scipy 1.4.1을 하드 핀하는데, 전부 Windows wheel이 없는 옛 버전이다. 실제로 쓰는 것은
`rxnfp.models`뿐이고 그 의존성(transformers · torch · simpletransformers)은 이미 설치되어 있다.

### 코드 수정 1곳

`inference.py`가 `pandarallel`의 `parallel_apply`에서 `NameError`로 죽는다.
Windows에는 fork가 없어 워커가 spawn으로 뜨고, 자식 프로세스가 모듈 전역 함수
`caonicalize_rxn_smiles`를 찾지 못한다. Windows에서만 단일 프로세스 `apply`를 쓰도록 고쳤다.
결과는 같고, 22개 반응 규모에서는 속도 차이도 없다.

## 3. 모델·데이터 다운로드

추론에 필요한 것은 두 개뿐이다 (pretrain 가중치 3개는 학습용이라 받지 않았다).

```powershell
cd parrot-src
gdown "https://drive.google.com/uc?id=1aX70qzZrJ9TZ9KpqnvUVR8WBxiTwXOsI" -O dataset/source_dataset/USPTO_condition_final.zip
gdown "https://drive.google.com/uc?id=1gFV2KdVKaLCTeb3nrzopyYHXbM0G_cr_" -O outputs/Parrot_train_in_USPTO_Condition_enhance.zip
```

`preprocess_script/download_data.py`는 쓰지 않았다. 5개를 전부 받고 `unzip`
(Windows에 없는 명령)으로 푸는데, 필요 없는 파일까지 받는다.

**데이터셋 zip은 전부 풀면 안 된다.** 압축 해제 시 2.3GB인데, 추론이 실제로 읽는 것은
`USPTO_condition_alldata_idx.pkl`(9.7KB) 하나다 (`models/utils.py`의 `inference_load`가
csv 경로를 계산만 하고 열지 않는다). 작은 파일만 풀었다.

```powershell
python -c "import zipfile; z=zipfile.ZipFile('dataset/source_dataset/USPTO_condition_final.zip'); [z.extract(i,'dataset/source_dataset') for i in z.infolist() if i.file_size < 2_000_000 and not i.is_dir()]"
python -c "import zipfile; zipfile.ZipFile('outputs/Parrot_train_in_USPTO_Condition_enhance.zip').extractall('outputs')"
```

## 4. 실행

```powershell
conda activate parrot-env
cd parrot-src
python inference.py --config_path configs/config_inference_use_uspto.yaml `
                    --input_path  <repo>/results/parrot/route_1_input.txt `
                    --output_path <repo>/results/parrot/route_1_conditions.csv `
                    --num_workers 2 --inference_batch_size 8 --gpu -1
```

`--gpu -1`이 CPU 추론이다. 10단계 기준 3분 남짓 걸린다.

입력·정리 스크립트는 이 repo에 있다.

```powershell
python scripts/make_parrot_input.py results/steps/route_1.json results/steps/route_6.json
python scripts/summarize_parrot.py --route 1 6
```

### 산출물

| 파일 | 내용 |
| --- | --- |
| `route_<n>_input.txt` | Parrot 입력 (반응 SMILES 한 줄에 하나) |
| `route_<n>_index.csv` | 줄 번호 ↔ 단계 번호 대응표 (Parrot 출력에는 단계 번호가 없다) |
| `route_<n>_conditions.csv` | Parrot 원본 출력, 단계마다 top-15 |
| `route_<n>_summary.md` | 단계 번호를 붙이고 SMILES를 이름으로 바꾼 표 (top-3) |

## 5. 문헌 공정과의 비교 (route 1 top-1)

실제 Amgen 공정 조건은 `docs/analysis.md` 4장 표가 ground truth다.

| 단계 | 반응 | AI 예측 (top-1) | 실제 공정 | 판정 |
| --- | --- | --- | --- | --- |
| 7 | POCl₃ 염소화 | **톨루엔 + DIPEA** | POCl₃ + DIPEA, **톨루엔** | **일치** |
| 9 | 피페라진 SNAr | 아세토나이트릴 + 트라이에틸아민 | i-PrOAc–DCM, 20 °C (3차 아민 염기) | **부분 일치** — 염기는 같은 부류, 용매가 다름 |
| 10 | Suzuki 커플링 | Pd(PPh3)4 / 1,4-다이옥세인–물 / K2CO3 | Pd(dpe)PhosCl₂ 0.3 mol% / 2-MeTHF–H₂O 9:1 / KOAc, 78 °C | **부류만 일치** — Pd(0)/염기/함수 용매 구성은 맞지만 공정 최적화된 시약은 아님 |
| 8 | 아크릴로일 클로라이드 아마이드화 | DCM + 트라이에틸아민 | 아크릴로일 클로라이드, 재결정 EtOH/H₂O | **타당** |
| 2 | Suzuki (아이소프로페닐) | Pd(PPh3)4 / 1,4-다이옥세인–물 / Na2CO3 | (실제 공정에 없는 단계) | 반응 부류에 맞는 교과서적 조건 |
| 4 | 아이소프로페닐 환원 | Pd / 에틸 아세테이트 | (실제 공정에 없는 단계) | 수소화 조건으로 타당 |

**해석**: 조건 예측은 경로 예측보다 성적이 좋다. POCl₃ 염소화는 용매·염기가 문헌과 그대로 같고,
Suzuki·아마이드화·수소화도 반응 부류에 맞는 조건을 냈다. 다만 **교과서적 조건에 머문다.**
최종 Suzuki에서 실제 공정은 Pd(dpe)PhosCl₂ 0.3 mol%에 KOAc·2-MeTHF를 쓰는데, 모델은
Pd(PPh3)4 · K2CO3 · 다이옥세인이라는 가장 흔한 조합을 냈다. 공정화학의 선택(촉매 사용량 절감,
친환경 용매, 후처리 용이성)은 USPTO 반응 데이터에 드러나지 않으므로 재현되지 않는다.
이는 경로 예측에서 "흔한 변환은 맞히고 공정화학의 판단은 못 맞힌다"고 본 것과 같은 패턴이다.

## 6. 한계점 (보고서용)

1. **온도를 예측하지 않는다.** 공개 모델의 출력은 촉매·용매·시약뿐이다 (1절 참조).
2. **화학적으로 불가능한 단계에도 그럴듯한 조건을 낸다.** route 1의 3단계는 아세틸 클로라이드로
   융합고리를 만드는 실제로 일어나지 않는 변환인데, Parrot은 여기에 DCM + 트라이에틸아민이라는
   아실화의 표준 조건을 아무 경고 없이 제시했다. **조건 모델은 반응이 성립하는지 검증하지 않고,
   주어진 반응을 성립한다고 전제하고 조건만 맞춘다.** 경로 모델의 오류가 조건 모델을 그대로 통과한다.
3. **조건이 교과서적 평균에 머문다.** 최종 Suzuki의 top-3가 촉매·용매는 모두 같고 염기만
   K2CO3 / Cs2CO3 / Na2CO3로 바뀐다. 실제 공정이 쓴 KOAc는 top-3에 없다.
4. **확신도가 낮은 단계일수록 조건도 평범해진다.** 경로 모델이 p=0.002를 준 최종 Suzuki에
   가장 낮은 score(-2.85)가 나왔다.

이 중 2번이 가장 중요하다. 기존 한계점 1(원자 수지가 맞아도 메커니즘은 성립하지 않는다)과
한계점 6(점수가 화학적 타당성을 재지 않는다)에 이어, **파이프라인의 뒷단 모델도 앞단의 오류를
걸러내지 못한다**는 것을 보여준다. 세 가지를 묶으면 "각 모델이 자기 영역의 수치만 최적화하고
화학적 타당성은 누구도 검증하지 않는다"는 결론이 된다.
