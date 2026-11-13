# v4 route 1 — Parrot 반응 조건 예측

모델: Parrot, USPTO-Condition으로 학습한 공개 가중치
(`Parrot_train_in_USPTO_Condition_enhance`), CPU 추론.

**이 모델은 온도를 예측하지 않는다.** 출력 항목은 촉매·용매 2개·시약 2개뿐이다. 온도까지 내는 모델은 Reaxys-TotalSyn-Condition으로 학습한 쪽인데, Reaxys 라이선스가 필요해 배포되지 않는다.

`score`는 빔 서치의 로그 확률이라 값이 클수록(0에 가까울수록) 모델이 확신한다는 뜻이다.

## 단계 1

- 경로 모델 정책: uspto (p=0.398)
- 반응 SMILES: `CN(C)C=O.Cc1ccnc(Br)c1-n1c(N)cc(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>Cc1ccnc(Br)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | THF | — | n-BuLi | — | -1.5529 |
| top-2 | — | THF | — | CC(C)[N-]C(C)C.[Li+] | — | -2.7159 |
| top-3 | — | THF | — | CC1(C)CCCC(C)(C)N1 | n-BuLi | -2.8259 |

## 단계 2

- 경로 모델 정책: uspto (p=0.036)
- 반응 SMILES: `C=C(C)B1OC(C)(C)C(C)(C)O1.Cc1ccnc(Br)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | Na2CO3 | — | -2.2599 |
| top-2 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | K2CO3 | — | -2.3896 |
| top-3 | — | 1,4-다이옥세인 | 물 | K2CO3 | — | -3.8552 |

## 단계 3

- 경로 모델 정책: ringbreaker (p=0.036)
- 반응 SMILES: `C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O.CC(=O)Cl>>C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | DCM | — | 트라이에틸아민 | — | -2.1615 |
| top-2 | — | DCM | — | — | — | -3.1299 |
| top-3 | — | DCM | — | c1ccncc1 | — | -3.2613 |

## 단계 4

- 경로 모델 정책: uspto (p=0.008)
- 반응 SMILES: `C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd | 에틸 아세테이트 | — | — | — | -2.216 |
| top-2 | — | THF | — | — | — | -3.01 |
| top-3 | Pd | 에틸 아세테이트 | — | 수소 | — | -3.1138 |

## 단계 5

- 경로 모델 정책: uspto (p=0.012)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21.F[N+]12CC[N+](CCl)(CC1)CC2>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 아세토나이트릴 | — | NaI | — | -0.8698 |
| top-2 | — | 아세토나이트릴 | — | C1CCC2=NCCCN2CC1 | — | -1.71 |
| top-3 | — | 아세토나이트릴 | — | — | — | -2.002 |

## 단계 6

- 경로 모델 정책: uspto (p=0.010)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | THF | — | HCl | — | -1.6615 |
| top-2 | — | THF | — | CCCC[N+](CCCC)(CCCC)CCCC.[F-] | — | -1.967 |
| top-3 | — | THF | — | 물 | CCCC[N+](CCCC)(CCCC)CCCC.[F-] | -2.7883 |

## 단계 7

- 경로 모델 정책: uspto (p=0.132)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21.O=P(Cl)(Cl)Cl>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 톨루엔 | — | DIPEA | — | -2.0012 |
| top-2 | — | DCM | — | DIPEA | — | -2.2316 |
| top-3 | — | 아세토나이트릴 | — | DIPEA | — | -2.5716 |

## 단계 8

- 경로 모델 정책: uspto (p=0.975)
- 반응 SMILES: `C=CC(=O)Cl.C[C@H]1CNCCN1>>C=CC(=O)N1CCN[C@@H](C)C1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | DCM | — | 트라이에틸아민 | — | -1.626 |
| top-2 | — | DCM | — | — | — | -1.7492 |
| top-3 | — | DCM | — | DIPEA | — | -2.3341 |

## 단계 9

- 경로 모델 정책: uspto (p=0.016)
- 반응 SMILES: `C=CC(=O)N1CCN[C@@H](C)C1.Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 아세토나이트릴 | — | 트라이에틸아민 | — | -2.0514 |
| top-2 | — | 아세토나이트릴 | — | — | — | -2.1679 |
| top-3 | — | 클로로폼 | — | — | — | -2.4225 |

## 단계 10

- 경로 모델 정책: uspto (p=0.002)
- 반응 SMILES: `C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1.CC1(C)OB(c2c(O)cccc2F)OC1(C)C>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(-c4c(O)cccc4F)c(F)cc23)[C@@H](C)C1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | K2CO3 | — | -2.8483 |
| top-2 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | Cs2CO3 | — | -2.8537 |
| top-3 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | Na2CO3 | — | -3.5624 |

