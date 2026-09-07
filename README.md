# FDT 엔진

가계부 더미(또는 실제 연동) 데이터를 입력받아 State(현재 상태)·Behavior(소비
행동 추정)·Transition/Uncertainty(몬테카를로 시뮬레이터)를 조립하고, 5개
모드(FORECAST/WHATIF/GOAL/RISK/OPTIMIZE) 중 요청자가 지정한 하나를 실행해
수치 결과·발화용 사실(facts)·시각화 명세(viz)를 담은 JSON 을 낸다. 렌더러나
대화 에이전트는 이 JSON 만 보고 동작하며, 엔진 코어(`fdt/engine/**`)는 입출력
포맷(색상·문구·차트 라이브러리)에 관여하지 않는다. 자세한 계약은
`SPEC.md`(v0.6), 구현 계획은 `PLAN.md` 를 참조한다.

## 설치

```
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```

(uv 가 있으면 `uv venv` + `uv pip install -e ".[dev]"` 도 가능하다.)

모든 CLI 출력은 UTF-8 로 고정돼 있다. Windows 콘솔에서 한글이 깨지면 실행 전에
`export PYTHONIOENCODING=utf-8`(bash) 또는 `$env:PYTHONIOENCODING="utf-8"`
(PowerShell) 을 설정한다.

## 5분 안내: gen → build → run → validate → render

아래는 실제로 동작하는 명령이다(프로필 `A_steady`, 시드 `7` 기준).

```
# 1) 더미 데이터 생성: TwinInput + ground_truth
.venv/Scripts/python -m fdt.cli gen --profile A_steady --seed 7 --months 6 --out data/seed/

# 2) TwinInput -> Engine (State/Behavior 조립, 입력 검증)
.venv/Scripts/python -m fdt.cli build --input data/seed/A_steady_7/twin_input.json --out data/engines/A.engine.json

# 3) 모드 실행 (예: RISK, 30일, 1000경로)
.venv/Scripts/python -m fdt.cli run --engine data/engines/A.engine.json --mode RISK --horizon 30 --n-paths 1000 --seed 42 --out data/out/A_risk.json

# 4) 결과 검증: 스키마 + 필수 facts/viz + annotations 숫자 정합
.venv/Scripts/python -m fdt.cli validate --result data/out/A_risk.json

# 5) viz 8종을 PNG 로 렌더 (matplotlib, 개발·QA 전용)
.venv/Scripts/python -m fdt.cli render --result data/out/A_risk.json --out data/out/A_risk_png/
```

`run` 에 `--validate` 를 붙이면 4)를 별도로 호출하지 않아도 된다(검증 실패 시
종료 코드 1). `inspect` 로 State/Behavior 요약을 표로 볼 수 있다:

```
.venv/Scripts/python -m fdt.cli inspect --engine data/engines/A.engine.json
```

## 모드별 요청 예시 (`--params`)

`--engine` 은 위 2)에서 만든 파일, `--params` 는 JSON 문자열(또는
`--params-file` 로 파일 경로)이다.

```
# FORECAST: 30일 잔액 예측 + 봉투 소진 전망
.venv/Scripts/python -m fdt.cli run --engine data/engines/A.engine.json --mode FORECAST \
  --horizon 30 --params '{"include_envelopes":true,"include_events":true}' --out data/out/A_forecast.json

# WHATIF: 3일 뒤 카드로 15만원 지출 시 분기
.venv/Scripts/python -m fdt.cli run --engine data/engines/B.engine.json --mode WHATIF \
  --params '{"injections":[{"type":"SPEND","days_from_now":3,"amount":150000,"envelope_id":5,"method":"CARD"}]}' \
  --out data/out/B_whatif.json

# GOAL: 12월 말까지 200만원 추가 저축(SAVE) 달성 가능성 + 주차별 상한
.venv/Scripts/python -m fdt.cli run --engine data/engines/D.engine.json --mode GOAL --horizon 120 \
  --params '{"goal_type":"SAVE","target_amount":2000000,"target_date":"2026-12-31","protect_essential":true}' \
  --out data/out/D_goal.json

# RISK: 결제 부족 위험 점수·안심 소비 한도
.venv/Scripts/python -m fdt.cli run --engine data/engines/B.engine.json --mode RISK --horizon 30 \
  --params '{"recent_tx_ids":[]}' --out data/out/B_risk.json

# OPTIMIZE: 부족 확률을 최소화하는 행동 후보 순위(최대 3개 조합, 시뮬 ≤40회)
.venv/Scripts/python -m fdt.cli run --engine data/engines/D.engine.json --mode OPTIMIZE --horizon 30 \
  --params '{"objective":"MIN_SHORTFALL_PROB","candidates":"AUTO","max_actions":3,"constraints":{"protect_essential":true,"max_cut_ratio":0.5,"allow_emergency_draw":false}}' \
  --out data/out/D_optimize.json
```

모드 선택은 항상 요청자가 명시한다(`--mode` 필수). 엔진은 모드를 추론하지
않는다.

## 출력 구조

`EngineResult` JSON(스키마 `engine-result/1`)은 다섯 봉투로 구성된다(SPEC §9.1).

- `meta`: `engine_id`, `as_of`, `mode`, `seed`, `n_paths`, `horizon_days`,
  `elapsed_ms`, `warnings[]`(코드화된 `W-*` 경고).
- `request`: 보낸 `ModeRequest` 원문(재현용).
- `result`: 모드별 결과 본문(§8) — 예: RISK 는 `risk_score`, `payment_risks[]`,
  `safe_to_spend_today` 등.
- `facts[]`: 에이전트가 문장에 넣어도 되는 숫자의 전체 집합
  (`key`/`label`/`value`/`unit`/`allowed_renderings`). 이 밖의 숫자를 답변에
  쓰면 충실도 검사에서 실패해야 한다.
- `viz[]`: 렌더러 독립 시각화 명세 8종(`line_band`/`event_timeline`/`gauge`/
  `progress_bars`/`delta_bars`/`step_bars`/`ranked_bars`/`table`) 중 모드별
  필수 항목(§9.4)을 포함한다. `annotations[].label`/`caption`/`title` 의
  숫자는 반드시 `facts` 표기와 일치해야 한다(`fdt validate` 가 검사).
- `status`: `OK` 또는 `ERROR`(에러면 `result` 없이 `error{code,message,details}`).

## 평가·QA 문서

- `docs/EVAL_REPORT.md` — `fdt eval all` 이 만드는 자동 평가 리포트(SPEC §12
  기준: 백테스트 sMAPE·커버리지, 리스크 캘리브레이션 ECE/Brier, WHATIF
  단조성, 성능·재현성). 프로필/시드별 상세 표와 미달 항목 원인 메모 포함.
- `docs/QA_REPORT.md` — 사람(또는 별도 에이전트)이 CLI 만으로 수행한 QA
  리포트(PLAN §6). 시나리오 QA-01~QA-20 판정, viz 육안 검수, SPEC 대조 감사,
  발견한 결함 목록(P0/P1/P2)을 담는다.
- `docs/reviews/` — Phase 별 코드 리뷰 기록(`YYYYMMDD_<작업ID>.md`).

## SPEC / PLAN

- `SPEC.md` — 입력 계약(`TwinInput`)부터 모드 계약(§8), 출력 계약(§9),
  성능·품질 기준(§12)까지 담은 단일 진실 소스. 구현이 SPEC 과 다르면 SPEC 을
  먼저 고친다.
- `PLAN.md` — 단계별 계획(Phase 0~7), 작업 분할(WBS), 테스트 계획, QA 계획,
  코드 리뷰 체크리스트, 일정·리스크.

## 아키텍처 규칙 요약

- `fdt/engine/**`(State·Behavior·Transition·모드 러너)는 **입출력 형식에
  관여하지 않는다**: 파일 I/O, 색상·문구·차트 라이브러리 선택은 전부
  `fdt/cli.py`·`fdt/tools/**`(render/validate) 쪽 책임이다. 엔진은 `viz` 를
  렌더러 독립 명세로만 낸다.
- `Engine` 은 불변 원칙(SPEC §4.2)을 지킨다: 같은 `Engine` 객체에 같은
  `ModeRequest`(같은 seed) 를 몇 번 실행해도 같은 결과가 나와야 한다.
- 모든 입력 검증 실패는 `FdtError(code)` 로 던지고 pydantic
  `ValidationError` 메시지를 파싱하지 않는다(`extract_errors` 로 구조화).
  여러 오류가 동시에 나면 `error.details.errors[]` 에 전부 담는다.
- 생성기(`fdt/gen/`)가 만드는 `ground_truth.json` 은 엔진에 숨겨진 정답
  분포이며, **엔진 코드는 이를 읽지 않는다**(백테스트 전용).
- 렌더러(`fdt/tools/render.py`)는 개발·QA 전용 도구다(matplotlib). 실제
  서비스의 시각화는 `viz` 명세를 받아 별도로 그린다.

## 프로젝트 상태

- 테스트: `.venv/Scripts/python -m pytest -q` 기준 680개 수집(`tests/unit`,
  `tests/property`, `tests/integration`, `tests/golden`).
- 구현 단계: PLAN Phase 0~6 완료, Phase 7(평가·QA 마감) 진행 중. CLI
  서브커맨드(`schema/gen/build/inspect/run/validate/render/eval`) 전부 동작.
- 평가·QA 요약(자세한 수치는 각 문서 참조):
  - `docs/EVAL_REPORT.md`: 성능·재현성·캘리브레이션·단조성은 기준 통과. 백테스트
    sMAPE 는 A/D 통과, B/C 미달(C 미달 폭이 큼, 원인 분석은 문서 참조). P10~P90
    커버리지는 전 프로필 시드별로 3~4/5 만 기준 범위 안(미달).
  - `docs/QA_REPORT.md`: 시나리오 QA-01~QA-20 은 FAIL 없이 통과(2건 확인 불가,
    1건 미구현 어댑터). viz 렌더러·결과 필드명에서 P1 6건·P2 2건의 결함을
    발견했다(핵심 수치 계산 자체의 오류는 없음).
