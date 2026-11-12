# v4 route 6 — 단계별 반응 SMILES

- 목표 분자: `C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(-c4c(O)cccc4F)c(F)cc23)[C@@H](C)C1`
- 단계 수: 12
- 전구체: 8 / 9 재고 보유
- state score: 0.8445680756022761
- number of reactions: 12
- number of pre-cursors: 9
- number of pre-cursors in stock: 8

단계 번호는 정반응 순서다 (역합성 트리의 깊은 노드가 먼저 일어나는 반응).

| # | 정책 | p | 분류 | 반응 SMILES |
| --- | --- | --- | --- | --- |
| 1 | uspto | 0.036 | 0.0 Unrecognized | `C=C(C)B1OC(C)(C)C(C)(C)O1.Cc1ccnc(Br)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O` |
| 2 | ringbreaker | 0.036 | 0.0 Unrecognized | `CC(=O)Cl.C=C(C)c1nccc(C)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O>>C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21` |
| 3 | uspto | 0.008 | 0.0 Unrecognized | `C=C(C)c1nccc(C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21` |
| 4 | uspto | 0.012 | 0.0 Unrecognized | `F[N+]12CC[N+](CCl)(CC1)CC2.Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2ccc(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21` |
| 5 | uspto | 0.010 | 0.0 Unrecognized | `Cc1ccnc(C(C)C)c1-n1c(=O)nc(O[Si](C(C)C)(C(C)C)C(C)C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21` |
| 6 | uspto | 0.669 | 0.0 Unrecognized | `C[C@H]1CNCCN1Cc1ccccc1.O=C(OC(=O)C(F)(F)F)C(F)(F)F>>C[C@H]1CN(C(=O)C(F)(F)F)CCN1Cc1ccccc1` |
| 7 | uspto | 0.132 | 0.0 Unrecognized | `O=P(Cl)(Cl)Cl.Cc1ccnc(C(C)C)c1-n1c(=O)nc(O)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21` |
| 8 | uspto | 0.175 | 0.0 Unrecognized | `C[C@H]1CN(C(=O)C(F)(F)F)CCN1Cc1ccccc1>>C[C@H]1CN(C(=O)C(F)(F)F)CCN1` |
| 9 | uspto | 0.067 | 0.0 Unrecognized | `C[C@H]1CN(C(=O)C(F)(F)F)CCN1.Cc1ccnc(C(C)C)c1-n1c(=O)nc(Cl)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCN(C(=O)C(F)(F)F)C[C@@H]2C)c2cc(F)c(Cl)nc21` |
| 10 | uspto | 0.042 | 0.0 Unrecognized | `Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCN(C(=O)C(F)(F)F)C[C@@H]2C)c2cc(F)c(Cl)nc21>>Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCNC[C@@H]2C)c2cc(F)c(Cl)nc21` |
| 11 | uspto | 0.255 | 0.0 Unrecognized | `C=CC(=O)O.Cc1ccnc(C(C)C)c1-n1c(=O)nc(N2CCNC[C@@H]2C)c2cc(F)c(Cl)nc21>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1` |
| 12 | uspto | 0.002 | 0.0 Unrecognized | `CC1(C)OB(c2c(O)cccc2F)OC1(C)C.C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(Cl)c(F)cc23)[C@@H](C)C1>>C=CC(=O)N1CCN(c2nc(=O)n(-c3c(C)ccnc3C(C)C)c3nc(-c4c(O)cccc4F)c(F)cc23)[C@@H](C)C1` |

## 전구체

- `CC1(C)OB(c2c(O)cccc2F)OC1(C)C` — 재고 보유
- `C=CC(=O)O` — 재고 보유
- `C[C@H]1CNCCN1Cc1ccccc1` — 재고 보유
- `O=C(OC(=O)C(F)(F)F)C(F)(F)F` — 재고 보유
- `O=P(Cl)(Cl)Cl` — 재고 보유
- `F[N+]12CC[N+](CCl)(CC1)CC2` — 재고 보유
- `CC(=O)Cl` — 재고 보유
- `C=C(C)B1OC(C)(C)C(C)(C)O1` — 재고 보유
- `Cc1ccnc(Br)c1-n1c(N)c(C=O)c(O[Si](C(C)C)(C(C)C)C(C)C)nc1=O` — **재고 미보유**
