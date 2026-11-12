# 실행 결과 (소토라십, AiZynthFinder)

대상 물질: 소토라십 (Sotorasib, AMG 510), PubChem CID 137278711, C30H30F2N6O3

```
C[C@H]1CN(CCN1C2=NC(=O)N(C3=NC(=C(C=C32)F)C4=C(C=CC=C4F)O)C5=C(C=CN=C5C(C)C)C)C(=O)C=C
```

## 1. 환경 재현

```powershell
conda create -n aizynth-env python=3.11
conda activate aizynth-env
pip install aizynthfinder==4.4.1 pyarrow==17.0.0 onnxruntime==1.19.2
```

버전을 고정한 이유: pyarrow/NumPy와 onnxruntime의 DLL 충돌이 있어 이 조합에서만 동작한다.

모델·재고 데이터는 용량 때문에 repo 밖(`aizynth-data/`)에 두고 `.gitignore`로 제외했다.
AiZynthFinder 공개 모델을 받으면 같은 구성이 된다.

- expansion policy: `uspto`, `ringbreaker`
- filter policy: `uspto`
- stock: `zinc` (1742만 화합물)

`config.yml` 맨 아래 탐색 설정:

```yaml
search:
  max_transforms: 10
  iteration_limit: 500
  time_limit: 10800
```

## 2. 실행 명령

```powershell
conda activate aizynth-env
aizynthcli --config "$env:USERPROFILE\github\aizynth-data\config.yml" `
           --smiles "<SMILES>" `
           --policy uspto ringbreaker `
           --output sotorasib_trees_v4.json
```

`--policy`를 생략하면 expansion policy는 첫 번째 것(`uspto`)만 선택된다.

**주의 — `time_limit`은 벽시계 시간이다.** AiZynthFinder는 `time.time()`으로 경과를 재므로
노트북 절전 시간도 포함된다 (3차 실행이 312회에서 멈춘 원인). 끝까지 돌리려면:

```powershell
powercfg /change standby-timeout-ac 0     # 실행 전
powercfg /change standby-timeout-ac 30    # 실행 후 되돌리기
```

## 3. 4회 실행 비교

설정을 바꿔가며 4회 실행했다. 조건이 하나씩만 다르다.

| | 1차 | 2차 | 3차 | 4차 |
| --- | --- | --- | --- | --- |
| 파일 | `sotorasib_trees.json` | `sotorasib_trees_v2.json` | `sotorasib_trees_v3.json` | `sotorasib_trees_v4.json` |
| 정책 | uspto | uspto | uspto + ringbreaker | uspto + ringbreaker |
| 설정 | 기본 (transforms 6, iter 100) | transforms 10, iter 500 | 2차와 동일 | 2차와 동일, time_limit 10800 |
| 탐색 시간 | 91초 | 1012초 | 3401초 (절전 포함) | 1635초 |
| 반복 | 100 (한도 소진) | 500 (한도 소진) | 312 (절전으로 조기 종료) | 500 (한도 소진) |
| 노드 / 경로 | 603 / 144 | 5266 / 1068 | 3360 / 674 | 5325 / 1069 |
| 저장된 경로 수 | — | 8 | 7 | **15** |
| top score | 0.805 | 0.8336 | 0.8447790869906586 | 0.8447790869906586 |
| is_solved | False | False | False | False |
| 최상위 경로 깊이 | 5 | 7 | 9 | 9 |
| 전구체 (보유/전체) | 5 / 6 | 7 / 8 | 8 / 9 | 8 / 9 |

### 수렴 판정

4차는 3차보다 탐색량이 60% 많은데(500 vs 312회) top score가 소수점 끝까지 같고
(0.8447790869906586) 깊이·전구체 구성·막힌 전구체까지 같다. 저장된 경로 수만 7 → 15로 늘었고
v3의 7개가 v4에 전부 포함된다. 최고 경로는 수렴했고 변형의 가짓수만 늘었다고 보아
추가 실행은 하지 않았다. **보고서는 v4를 쓴다.**

### `is_solved: False`의 원인

재고(ZINC)에 없는 핵 중간체 1개 때문이다. 나머지 8개 전구체는 모두 상업적으로 구할 수 있다.

```
Cc1ccnc(Br)c1-n1c(N)cc(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O
```

## 4. 후속 처리

```powershell
# 단계별 반응 SMILES 추출 (조건·수율 모델 입력)
python scripts/extract_steps.py results/sotorasib_trees_v4.json --route 1 6

# 반응식·구조식 이미지 생성
python scripts/draw_route.py results/steps/route_1.json
python scripts/draw_route.py results/steps/route_6.json
```

경로 1과 6을 고른 이유:

- **route 1** — 최고 점수 (0.8448), 10단계
- **route 6** — 화학적으로 가장 정합적 (Bn + TFA 보호기를 도입·제거 모두 명시), 12단계

### 산출물

| 경로 | 위치 |
| --- | --- |
| 단계별 반응 SMILES (json) | `results/steps/route_1.json`, `route_6.json` |
| 단계 표 (markdown) | `results/steps/route_1.md`, `route_6.md` |
| 단계별 반응식 이미지 | `results/images/route_<n>/step_NN.png` |
| 전체 경로 한 장 | `results/images/route_<n>/route_overview.png` |
| 전구체 모음 | `results/images/route_<n>/precursors.png` |

`extract_steps.py`의 단계 번호는 정반응 순서다. 역합성 트리에서 깊은 reaction 노드가
먼저 일어나는 반응이므로 깊이 내림차순으로 정렬했다.

같은 깊이에 여러 반응이 있으면 (= 서로 독립인 가지) 서브트리가 깊은 쪽을 먼저 쓴다.
긴 쪽이 주 사슬, 짧은 쪽이 분기이므로 주 사슬이 연속 번호로 이어져 읽기 좋다.
route 1은 이 규칙으로 **주 사슬 1–7(포밀화 ~ POCl₃), 분기 8(아크릴로일 클로라이드 +
메틸피페라진), 결합 9–10(SNAr, Suzuki)** 이 된다.

route 6은 피페라진 분기가 2단계(6 TFA 보호, 8 탈벤질)여서 주 사슬과 같은 깊이에 걸친다.
깊이 내림차순을 지키는 한 분기가 주 사슬 사이에 끼는 것을 피할 수 없다
(주 사슬 1–5, 7 / 분기 6, 8 / 결합 9–12). 독립인 가지의 순서는 어느 쪽이든
위상 정렬상 유효하고 화학적으로도 같다.
