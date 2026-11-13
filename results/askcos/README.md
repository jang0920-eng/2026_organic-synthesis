# ASKCOS 반응 조건 예측 (소토라십) — 온도 포함

모델: [ASKCOS v1 context recommender](https://gitlab.com/mlpds_mit/askcosv2/context_recommender)
— Gao et al., *ACS Cent. Sci.* **2018**, 4, 1465의 신경망 조건 추천 모델.

입력은 AiZynthFinder v4의 route 1(10단계)·route 6(12단계) 반응 SMILES 22개다.
22개 전부 예측에 성공했다.

## 1. Docker 없이 실행했다

repo의 README는 Docker 또는 Singularity로 서비스를 띄우라고 안내하지만,
**그 컨테이너는 FastAPI 서비스를 감싸는 포장일 뿐이다.** 예측기 클래스를 직접
import해서 `recommend()`를 부르면 서비스도 Docker도 필요 없다.

이 노트북에는 Docker도 WSL2도 설치되어 있지 않았고, Windows 11 Home에서
Docker Desktop을 쓰려면 WSL2 + 재부팅 + 6~10GB가 필요했다. 아래 방법은
conda 환경 하나(약 1.5GB)로 끝난다.

```powershell
git clone https://gitlab.com/mlpds_mit/askcosv2/context_recommender.git askcos-context-src
conda create -n askcos-env python=3.8 -y
conda activate askcos-env
pip install --only-binary=:all: tensorflow-cpu==2.7.4 scikit-learn==1.0.2 `
            scipy==1.7.3 "numpy<1.24" rdkit==2022.9.5 protobuf==3.19.0
```

모델 가중치는 Dropbox 직링크라 로그인 없이 받을 수 있다 (143MB).

```powershell
curl -L -o v1.tar.gz "https://www.dropbox.com/scl/fi/97g21iqzxz4gw4l83xjye/v1.tar.gz?rlkey=orny64sno8kd3cbspgbs53qd0&dl=1"
tar xzf v1.tar.gz -C app/resources/models/context/
```

받은 것: `weights.h5`(155MB), `model.json`, 라벨 사전 5개(촉매·용매1·용매2·시약1·시약2),
용매 EHS 점수표.

실행:

```powershell
conda activate askcos-env
python scripts/run_askcos.py --route 1 6
```

`scripts/run_askcos.py`가 `app/v1/services/predictor.py`의
`NeuralNetContextRecommender`를 직접 불러온다. 설정이 `app/resources` 상대경로를
쓰므로 모델 로드는 repo 폴더 안에서 해야 한다.

### 출력 형식

`recommend()`는 조건마다
`[온도(°C), 용매, 시약, 촉매, EHS점수, 최고EHS여부]`를 돌려준다.
EHS는 용매의 환경·건강·안전 점수로 낮을수록 좋다.

## 2. Parrot이 못 하는 것 — 온도

| | Parrot (USPTO 공개본) | ASKCOS v1 |
| --- | --- | --- |
| 촉매 | 예측함 | 예측함 |
| 용매 | 2개까지 | 2개까지 |
| 시약 | 2개까지 | 2개까지 |
| **온도** | **예측하지 않음** | **예측함** |
| 용매 EHS 점수 | 없음 | 있음 |

Parrot에서 온도를 내려면 Reaxys-TotalSyn-Condition 학습본이 필요한데 라이선스 때문에
배포되지 않는다 (`results/parrot/README.md` 1절). **온도는 ASKCOS로만 채울 수 있다.**

## 3. 가장 중요한 결과 — 끓는점을 넘는 조건이 체계적으로 나온다

`SKILL.md` 7.1절의 검증 규칙을 처음으로 적용할 수 있게 되었다.

> 열린 플라스크는 용매 끓는점보다 뜨거워지지 않는다.
> 예측 온도가 용매 끓는점보다 높으면 용매를 바꾸거나 가압 조건임을 명시해야 한다.

전체 조건 66개(22단계 × top-3) 중 **12개가 용매 끓는점을 넘었다.** top-1만 보면 4개다.

**그 12개가 전부 Suzuki 커플링 단계다.** 두 개의 Suzuki 반응에 제시된 조건 6개가
하나도 빠짐없이 끓는점을 넘는다.

| 반응 | 순위 | 예측 온도 | 용매 | 끓는점 | 초과 |
| --- | --- | --- | --- | --- | --- |
| 아이소프로페닐 Suzuki | top-1 | 81.2 °C | THF / 물 | 66 °C | +15 °C |
| | top-2 | 81.4 °C | THF / 물 | 66 °C | +15 °C |
| | top-3 | 84.6 °C | THF / 물 | 66 °C | +19 °C |
| 플루오로페놀 Suzuki (최종) | top-1 | 107.1 °C | 1,4-다이옥세인 / 물 | 100 °C | +7 °C |
| | top-2 | 112.0 °C | 아세토나이트릴 / 물 | 81.6 °C | +30 °C |
| | top-3 | 115.4 °C | 아세토나이트릴 / 물 | 81.6 °C | +34 °C |

**해석.** 모델은 문헌에서 "Suzuki 커플링은 80~115 °C로 가열한다"를 배웠고
"Suzuki에는 THF·다이옥세인·아세토나이트릴에 물을 섞는다"도 배웠다. 그런데 이 둘을
**따로 배워서 함께 쓸 수 없다는 것을 모른다.** 온도와 용매를 각각 맞히고 둘 사이의
물리적 제약은 보지 않는다.

실제 Amgen 공정은 이 문제를 정확히 피해 간다. **2-MeTHF–H₂O 9:1에서 78 °C**로
돌리는데, 2-MeTHF의 끓는점이 80 °C라 **끓는점 바로 아래**다. 공정 화학자는 원하는
온도를 견디는 용매를 고른 것이고, 모델은 그 선택을 재현하지 못했다.

## 4. 문헌 공정과의 비교 (route 1 top-1)

| 단계 | 반응 | ASKCOS | Parrot | 실제 공정 |
| --- | --- | --- | --- | --- |
| 7 | POCl₃ 염소화 | 26.0 °C, DCM | 톨루엔 + DIPEA | POCl₃ + DIPEA, **톨루엔** |
| 9 | 피페라진 SNAr | 61.2 °C, DMF | 아세토나이트릴 + Et₃N | i-PrOAc–DCM, **20 °C** |
| 10 | Suzuki 커플링 | **107.1 °C**, 다이옥세인–물 | Pd(PPh₃)₄ / 다이옥세인–물 / K₂CO₃ | Pd(dpe)PhosCl₂ / 2-MeTHF–H₂O / KOAc, **78 °C** |
| 8 | 아크릴로일 아마이드화 | 13.1 °C, DCM | DCM + Et₃N | 아크릴로일 클로라이드, 저온 |

읽을 점 세 가지다.

1. **두 조건 모델이 서로 다른 답을 낸다.** 7단계에서 Parrot은 톨루엔(문헌과 일치),
   ASKCOS는 DCM을 골랐다. 용매·염기만 보면 **Parrot이 문헌에 더 가깝다.**
2. **ASKCOS만 온도를 낸다.** 8단계의 13.1 °C는 아실 클로라이드 아마이드화의 표준
   저온 조건과 맞고, 9단계 SNAr의 61.2 °C는 실제 20 °C보다 높지만 타당한 범위다.
3. **온도를 내는 대신 온도에서 틀린다.** 최종 Suzuki를 107.1 °C로 예측했는데 실제는
   78 °C다. 29 °C 높고, 게다가 용매 끓는점을 넘는다.

## 5. 한계점 (보고서용)

1. **온도와 용매를 독립적으로 예측해 물리적으로 모순된 조건을 낸다.** Suzuki 단계에
   제시된 조건 6개가 전부 용매 끓는점을 넘었다. 모델에는 "액체가 끓으면 그 온도를
   유지할 수 없다"는 제약이 들어 있지 않다. **수업 자료에 명시된 금지 사항이
   모델 출력에서 실제로 관찰된 사례다.**

2. **물리적으로 불가능한 온도를 낸다.** 1단계 DMF 포밀화에 −33.2 °C, 5단계
   Selectfluor 불소화에 −51.3 °C를 제시했다. 두 반응 모두 저온에서 진행될 이유가 없다.
   (덧붙여 두 단계 모두 실제 공정에 없는, 경로 모델이 지어낸 단계다.)

3. **조건 모델끼리 일치하지 않는다.** 같은 반응에 Parrot은 톨루엔, ASKCOS는 DCM을
   제시했다. 둘 중 어느 쪽이 맞는지 모델 출력만으로는 가릴 수 없고, 문헌을 봐야
   Parrot이 맞다는 것을 알 수 있다. **모델을 여러 개 돌리면 답이 여러 개 나올 뿐,
   신뢰도가 올라가지 않는다.**

4. **여기서도 불가능한 반응을 걸러내지 않는다.** route 1의 3단계(아세틸 클로라이드로
   융합고리 형성, 실제로 일어나지 않는 반응)에 16.0 °C · DCM이라는 조건을
   score 0.381 — 전체에서 두 번째로 높은 확신도 — 로 제시했다.

### 파이프라인 전체 결론 (갱신)

route 1의 3단계 하나가 **네 모델을 모두 통과했다.**

| 모델 | 3단계에 대한 출력 | 경고 |
| --- | --- | --- |
| AiZynthFinder | 경로에 포함, ringbreaker p=0.036 | 없음 |
| Parrot | DCM + Et₃N | 없음 |
| **ASKCOS** | **16.0 °C, DCM, score 0.381 (2위)** | **없음** |
| Yield-BERT | 수율 15.3% | 없음 |

실제로 일어나지 않는 반응에 대해 경로·조건·온도·수율이 모두 생성되었고,
어느 단계에서도 "이 반응은 성립하지 않는다"는 신호가 나오지 않았다.
각 모델이 자기 영역의 수치만 최적화하고 화학적 타당성은 누구도 검증하지 않는다.

반대로, **검증 규칙을 사람이 적용하면 오류가 잡힌다.** 끓는점 규칙 하나로
Suzuki 단계의 조건 12개를 전부 걸러냈다. 모델 출력을 그대로 쓰지 않고
수업에서 배운 규칙으로 검산하는 절차가 파이프라인에 반드시 필요하다는 뜻이다.
