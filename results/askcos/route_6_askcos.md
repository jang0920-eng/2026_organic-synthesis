# v4 route 6 — ASKCOS 반응 조건 예측 (온도 포함)

모델: ASKCOS v1 neural network context recommender. Docker 없이 예측기를 직접 호출했다.

Parrot과 달리 **온도를 예측한다.** EHS는 용매의 환경·건강·안전 점수로 낮을수록 좋다.

> **검증 규칙 (SKILL.md 7.1).** 열린 플라스크는 용매 끓는점보다 뜨거워지지 않는다. 예측 온도가 용매 끓는점을 넘으면 가압 조건이거나 재현할 수 없는 조건이다. 해당 행에 `끓는점 초과` 표시를 달았다.

## 단계 1

- 경로 모델 정책: uspto (p=0.036)
- 반응 SMILES: `C=C(C)B1OC(C)(C)C(C)(C)O1.Cc1ccnc(Br)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 81.2 | THF / 물 | O=C([O-])[O-] / [K+] | c1ccc([P](c2ccccc2)(c2ccccc2)[Pd]([P](c2ccccc2)(c2ccccc2)c2ccccc2)([P](c2ccccc2)(c2ccccc2)c2ccccc2)[P](c2ccccc2)(c2ccccc2)c2ccccc2)cc1 | 7 | 0.139 | **끓는점 초과** (66 °C) |
| top-2 | 81.4 | THF / 물 | O=C([O-])[O-] / [Na+] | c1ccc([P](c2ccccc2)(c2ccccc2)[Pd]([P](c2ccccc2)(c2ccccc2)c2ccccc2)([P](c2ccccc2)(c2ccccc2)c2ccccc2)[P](c2ccccc2)(c2ccccc2)c2ccccc2)cc1 | 7 | 0.094 | **끓는점 초과** (66 °C) |
| top-3 | 84.6 | THF / 물 | O=C([O-])[O-] / [Cs+] | Reaxys Name (1,1'-bis(diphenylphosphino)ferrocene)palladium(II) dichloride | 7 | 0.038 | **끓는점 초과** (66 °C) |

## 단계 2

- 경로 모델 정책: ringbreaker (p=0.036)
- 반응 SMILES: `CC(=O)Cl.C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 16.0 | DCM | 피리딘 | — | 4 | 0.381 | — |
| top-2 | 14.2 | DCM | 트라이에틸아민 | — | 4 | 0.212 | — |
| top-3 | 19.1 | DCM | — | — | 4 | 0.195 | — |

## 단계 3

- 경로 모델 정책: uspto (p=0.008)
- 반응 SMILES: `C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 72.3 | — | O | — | None | 0.062 | — |
| top-2 | 55.8 | — | CO | — | None | 0.054 | — |
| top-3 | 43.1 | 메탄올 | — | — | 2 | 0.030 | — |

## 단계 4

- 경로 모델 정책: uspto (p=0.012)
- 반응 SMILES: `F[N+]12CC[N+](CCl)(CC1)CC2.Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | -51.3 | THF / THF | [Li]CCCC | — | 4.0 | 0.120 | — |
| top-2 | -0.7 | THF / THF | [Li+] / [Cl-] / [Cl-] / C[Mg]N1CCCC(C)C1(C)C | — | 4.0 | 0.028 | — |
| top-3 | -48.7 | THF / THF | CC1(C)CCCC(C)(C)N1 / [Li]CCCC | — | 4.0 | 0.025 | — |

## 단계 5

- 경로 모델 정책: uspto (p=0.010)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 54.0 | 1,2-다이클로로에탄 | — | — | 6 | 0.134 | — |
| top-2 | 28.3 | DCM | CC(=O)O | — | 4 | 0.132 | — |
| top-3 | 48.1 | 1,2-다이클로로에탄 | CC(=O)O | — | 6 | 0.102 | — |

## 단계 6

- 경로 모델 정책: uspto (p=0.669)
- 반응 SMILES: `C[C@H]1CNCCN1Cc1ccccc1.O=C(OC(=O)C(F)(F)F)C(F)(F)F>>C[C@H]1CN(C(=O)C(F)(F)F)CCN1Cc1ccccc1`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 13.2 | DCM | — | — | 4 | 0.586 | — |
| top-2 | 8.1 | DCM | 트라이에틸아민 | — | 4 | 0.131 | — |
| top-3 | 18.1 | 클로로폼 | — | — | 6 | 0.095 | — |

## 단계 7

- 경로 모델 정책: uspto (p=0.132)
- 반응 SMILES: `O=P(Cl)(Cl)Cl.Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 26.0 | DCM | — | — | 4 | 0.351 | — |
| top-2 | 50.5 | — | — | — | None | 0.112 | — |
| top-3 | 43.1 | 아세토나이트릴 | — | — | 3 | 0.071 | — |

## 단계 8

- 경로 모델 정책: uspto (p=0.175)
- 반응 SMILES: `C[C@H]1CN(C(=O)C(F)(F)F)CCN1Cc1ccccc1>>C[C@H]1CN(C(=O)C(F)(F)F)CCN1`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 29.2 | 메탄올 | [H][H] | [Pd] | 2 | 0.100 | — |
| top-2 | 31.5 | 에탄올 | [H][H] | [Pd] | 1 | 0.067 | — |
| top-3 | 29.4 | 메탄올 | [H][H] | [OH-] / [Pd+2] | 2 | 0.059 | — |

## 단계 9

- 경로 모델 정책: uspto (p=0.067)
- 반응 SMILES: `C[C@H]1CN(C(=O)C(F)(F)F)CCN1.Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCN(C(=O)C(F)(F)F)C[C@@H]2C)c2cc(F)c(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 65.9 | DMF | DIPEA | — | 7 | 0.531 | — |
| top-2 | 73.5 | — | DIPEA | — | None | 0.341 | — |
| top-3 | 70.9 | — | CC(C)NC(C)C | — | None | 0.021 | — |

## 단계 10

- 경로 모델 정책: uspto (p=0.042)
- 반응 SMILES: `Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCN(C(=O)C(F)(F)F)C[C@@H]2C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCNC[C@@H]2C)c2cc(F)c(Cl)nc21`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 29.3 | 메탄올 / 물 | O=C([O-])[O-] / [K+] | — | 1.5 | 0.376 | — |
| top-2 | 28.8 | 메탄올 / 물 | HCl | — | 1.5 | 0.059 | — |
| top-3 | 25.9 | 메탄올 / 물 | [OH-] / [Na+] | — | 1.5 | 0.031 | — |

## 단계 11

- 경로 모델 정책: uspto (p=0.255)
- 반응 SMILES: `C=CC(=O)O.Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCNC[C@@H]2C)c2cc(F)c(Cl)nc21>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 19.8 | DMF | 트라이에틸아민 / O=P(O)(C1=CC=CC=C1)C1=CC=CC=C1 | — | 7 | 0.273 | — |
| top-2 | 27.9 | THF | 트라이에틸아민 / N#N=NP(=O)(OC1=CC=CC=C1)OC1=CC=CC=C1 | — | 4 | 0.141 | — |
| top-3 | 40.6 | — | 트라이에틸아민 / N#N=NP(=O)(OC1=CC=CC=C1)OC1=CC=CC=C1 | — | None | 0.042 | — |

## 단계 12

- 경로 모델 정책: uspto (p=0.002)
- 반응 SMILES: `CC1(C)OB(c2c(O)cccc2F)OC1(C)C.C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(-c4c(O)cccc4F)c(F)cc23)[C@@H](C)C1`

| 순위 | 온도 (°C) | 용매 | 시약 | 촉매 | EHS | score | 검증 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| top-1 | 107.1 | 1,4-다이옥세인 / 물 | O=C([O-])[O-] / [Na+] | c1ccc([P](c2ccccc2)(c2ccccc2)[Pd]([P](c2ccccc2)(c2ccccc2)c2ccccc2)([P](c2ccccc2)(c2ccccc2)c2ccccc2)[P](c2ccccc2)(c2ccccc2)c2ccccc2)cc1 | 3.0 | 0.276 | **끓는점 초과** (100 °C) |
| top-2 | 112.0 | 아세토나이트릴 / 물 | O=C([O-])[O-] / [Na+] | c1ccc([P](c2ccccc2)(c2ccccc2)[Pd]([P](c2ccccc2)(c2ccccc2)c2ccccc2)([P](c2ccccc2)(c2ccccc2)c2ccccc2)[P](c2ccccc2)(c2ccccc2)c2ccccc2)cc1 | 2.0 | 0.172 | **끓는점 초과** (82 °C) |
| top-3 | 115.4 | 아세토나이트릴 / 물 | O=C([O-])[O-] / [Na+] | Reaxys Name (1,1'-bis(diphenylphosphino)ferrocene)palladium(II) dichloride | 2.0 | 0.067 | **끓는점 초과** (82 °C) |

