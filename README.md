# FDT 엔진

더미(또는 LIVE) 금융 데이터 JSON을 받아 State/Behavior/Transition/Uncertainty를
조립하고, 5개 모드(FORECAST/WHATIF/GOAL/RISK/OPTIMIZE) 중 하나를 실행해
수치 결과와 발화용 사실(facts), 시각화 명세(viz)를 담은 JSON을 낸다.
자세한 계약은 `SPEC.md`, 구현 계획은 `PLAN.md`를 참조한다.

## 설치

```
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```

(uv가 있으면 `uv venv` + `uv pip install -e ".[dev]"`도 가능하다.)

## 실행 흐름 (예정)

아래 CLI 서브커맨드는 각 담당 작업(W1, W5 등)에서 순차로 구현된다. 현재
단계(W0)에서는 골격·taxonomy·errors·아키텍처 테스트만 갖춰져 있다.

```
fdt gen      --profile A_steady --seed 7 --months 6 --out data/seed/A_seed7/   # 예정
fdt build    --input data/seed/A_seed7/twin_input.json --out data/engines/A.engine.json  # 예정
fdt run      --engine data/engines/A.engine.json --mode RISK --horizon 30 --seed 42       # 예정
fdt validate --result out/A_risk.json                                                     # 예정
fdt render   --result out/A_risk.json --out out/A_risk/                                   # 예정
```

## 테스트

```
.venv/Scripts/python -m pytest -q
```
