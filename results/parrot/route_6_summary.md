# v4 route 6 — Parrot 반응 조건 예측

모델: Parrot, USPTO-Condition으로 학습한 공개 가중치
(`Parrot_train_in_USPTO_Condition_enhance`), CPU 추론.

**이 모델은 온도를 예측하지 않는다.** 출력 항목은 촉매·용매 2개·시약 2개뿐이다. 온도까지 내는 모델은 Reaxys-TotalSyn-Condition으로 학습한 쪽인데, Reaxys 라이선스가 필요해 배포되지 않는다.

`score`는 빔 서치의 로그 확률이라 값이 클수록(0에 가까울수록) 모델이 확신한다는 뜻이다.

## 단계 1

- 경로 모델 정책: uspto (p=0.036)
- 반응 SMILES: `C=C(C)B1OC(C)(C)C(C)(C)O1.Cc1ccnc(Br)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | Na2CO3 | — | -2.2555 |
| top-2 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | K2CO3 | — | -2.4067 |
| top-3 | — | 1,4-다이옥세인 | 물 | K2CO3 | — | -3.8611 |

## 단계 2

- 경로 모델 정책: ringbreaker (p=0.036)
- 반응 SMILES: `C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O.CC(=O)Cl>>C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | DCM | — | 트라이에틸아민 | — | -2.166 |
| top-2 | — | DCM | — | — | — | -3.1233 |
| top-3 | — | DCM | — | c1ccncc1 | — | -3.2652 |

## 단계 3

- 경로 모델 정책: uspto (p=0.008)
- 반응 SMILES: `C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd | 에틸 아세테이트 | — | — | — | -2.2124 |
| top-2 | — | THF | — | — | — | -2.9911 |
| top-3 | Pd | 에틸 아세테이트 | — | 수소 | — | -3.1045 |

## 단계 4

- 경로 모델 정책: uspto (p=0.012)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21.F[N+]12CC[N+](CCl)(CC1)CC2>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 아세토나이트릴 | — | NaI | — | -0.8531 |
| top-2 | — | 아세토나이트릴 | — | C1CCC2=NCCCN2CC1 | — | -1.7282 |
| top-3 | — | 아세토나이트릴 | — | — | — | -2.0233 |

## 단계 5

- 경로 모델 정책: uspto (p=0.010)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | THF | — | HCl | — | -1.6614 |
| top-2 | — | THF | — | CCCC[N+](CCCC)(CCCC)CCCC.[F-] | — | -1.9788 |
| top-3 | — | THF | — | 물 | CCCC[N+](CCCC)(CCCC)CCCC.[F-] | -2.7887 |

## 단계 6

- 경로 모델 정책: uspto (p=0.669)
- 반응 SMILES: `C[C@H]1CNCCN1Cc1ccccc1.O=C(OC(=O)C(F)(F)F)C(F)(F)F>>C[C@H]1CN(C(=O)C(F)(F)F)CCN1Cc1ccccc1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | DCM | — | 트라이에틸아민 | — | -1.0203 |
| top-2 | — | DCM | — | DIPEA | — | -2.3691 |
| top-3 | — | DCM | — | — | — | -2.5656 |

## 단계 7

- 경로 모델 정책: uspto (p=0.132)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21.O=P(Cl)(Cl)Cl>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 톨루엔 | — | DIPEA | — | -2.0012 |
| top-2 | — | DCM | — | DIPEA | — | -2.2316 |
| top-3 | — | 아세토나이트릴 | — | DIPEA | — | -2.5716 |

## 단계 8

- 경로 모델 정책: uspto (p=0.175)
- 반응 SMILES: `C[C@H]1CN(C(=O)C(F)(F)F)CCN1Cc1ccccc1>>C[C@H]1CN(C(=O)C(F)(F)F)CCN1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd | 메탄올 | — | — | — | -1.2654 |
| top-2 | Pd | 메탄올 | — | 수소 | — | -1.7942 |
| top-3 | Pd | 에탄올 | — | — | — | -1.9715 |

## 단계 9

- 경로 모델 정책: uspto (p=0.067)
- 반응 SMILES: `C[C@H]1CN(C(=O)C(F)(F)F)CCN1.Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCN(C(=O)C(F)(F)F)C[C@@H]2C)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 아세토나이트릴 | — | 트라이에틸아민 | HCl | -1.1024 |
| top-2 | — | 클로로폼 | — | 트라이에틸아민 | HCl | -1.7868 |
| top-3 | — | 아세토나이트릴 | — | DIPEA | HCl | -2.2202 |

## 단계 10

- 경로 모델 정책: uspto (p=0.042)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCN(C(=O)C(F)(F)F)C[C@@H]2C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCNC[C@@H]2C)c2cc(F)c(Cl)nc21`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | 물 | — | 황산 | — | -2.3486 |
| top-2 | — | THF | 물 | [Li+].[OH-] | — | -2.7511 |
| top-3 | — | 메탄올 | — | K2CO3 | — | -2.8682 |

## 단계 11

- 경로 모델 정책: uspto (p=0.255)
- 반응 SMILES: `C=CC(=O)O.Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCNC[C@@H]2C)c2cc(F)c(Cl)nc21>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | — | DMF | — | DIPEA | CN(C)C(On1nnc2cccnc21)=[N+](C)C.F[P-](F)(F)(F)(F)F | -1.8645 |
| top-2 | — | DCM | — | DIPEA | CN(C)C(On1nnc2cccnc21)=[N+](C)C.F[P-](F)(F)(F)(F)F | -2.1128 |
| top-3 | — | 에틸 아세테이트 | DMF | DIPEA | CN(C)C(On1nnc2cccnc21)=[N+](C)C.F[P-](F)(F)(F)(F)F | -2.177 |

## 단계 12

- 경로 모델 정책: uspto (p=0.002)
- 반응 SMILES: `C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1.CC1(C)OB(c2c(O)cccc2F)OC1(C)C>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(-c4c(O)cccc4F)c(F)cc23)[C@@H](C)C1`

| 순위 | 촉매 | 용매 1 | 용매 2 | 시약 1 | 시약 2 | score |
| --- | --- | --- | --- | --- | --- | --- |
| top-1 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | Cs2CO3 | — | -2.8179 |
| top-2 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | K2CO3 | — | -2.8521 |
| top-3 | Pd(PPh3)4 | 1,4-다이옥세인 | 물 | Na2CO3 | — | -3.5986 |

