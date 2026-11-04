# 2026_organic-synthesis

AI 기반 신약 합성경로 예측 — 유기합성학 기말 프로젝트

공개 AI 모델을 이용해 표적 분자의 **합성경로 · 합성조건 · 산출율**을 예측하고, 각 모델의 추론 결과를 취합해 합성 실험에 대한 결론을 정리한다. 보고서는 `SKILL.md`를 읽은 Solar Pro4가 작성한다.

## 대상 물질

**소토라십 (Sotorasib, AMG 510)** — KRAS G12C 저해제

```
CC1=CC(C)=NC(=C1C1=C2C(=O)N(C(=O)N(C2=CC(F)=C1)[C@@H]1CCCN(C1)C(=O)C=C)C)C(C)C
```

선정 근거는 `docs/material-selection.md`. 백업 후보는 오시머티닙(Osimertinib).

## 구성

| 경로 | 내용 |
|---|---|
| `SKILL.md` | 물질 정보를 입력받아 보고서를 생성하는 스킬 정의 |
| `scripts/` | 모델별 실행 스크립트 |
| `results/` | 모델별 예측 결과 (json) |
| `figures/` | 구조 · 합성경로 이미지 |
| `docs/` | 물질 선정 근거, 문헌 수율 등 작업 메모 |
| `report/` | 최종 보고서 (docx / pdf) |

## 사용한 예측 모델

**합성경로**
- [AiZynthFinder](https://github.com/MolecularAI/aizynthfinder)
- [Synthex](https://github.com/schwallergroup/synthex/tree/submission)

**합성조건**
- [ASKCOS context recommender](https://gitlab.com/mlpds_mit/askcosv2/context_recommender)
- [Parrot](https://github.com/wangxr0526/Parrot)

**산출율**
- [rxn_yields](https://github.com/rxn4chemistry/rxn_yields)
- [DRFP](https://github.com/reymond-group/drfp)

## 환경 구축

AiZynthFinder는 Python 3.10–3.12를 요구한다.

```powershell
conda create -n aizynth-env python=3.11 -y
conda activate aizynth-env
python -m pip install aizynthfinder[all]
conda install -c conda-forge graphviz -y

mkdir "$env:USERPROFILE\github\aizynth-data"
download_public_data "$env:USERPROFILE\github\aizynth-data"
```

`download_public_data`는 6개 파일(expansion policy, ringbreaker, 각 템플릿, filter policy, ZINC 재고)을 모두 받은 뒤에야 `config.yml`을 생성한다. 중간에 끊기면 `config.yml`이 없으므로 처음부터 다시 받아야 한다.

경로 이미지 생성에는 graphviz의 `dot` 실행파일이 PATH에 있어야 한다 (`dot -V`로 확인).

모델·재고 파일과 `config.yml`은 용량과 머신 의존성 때문에 repo에 포함하지 않는다. repo 바깥(`../aizynth-data`)에 둔다.

## 재현 방법

(모델 연결이 끝난 뒤 작성)
