# FDT 엔진 구현 계획 (PLAN) v0.1

- 기준 문서: `SPEC.md` v0.1. 이 계획은 SPEC 의 절 번호를 그대로 참조한다. 설계가 바뀌면 SPEC 을 먼저 고치고 이 문서를 맞춘다.
- 작성일: 2026-09-07. 일정은 이 날을 D0 으로 한다.
- 대상 독자: 구현자(사람 또는 코딩 에이전트), 리뷰어, QA.

---

## 0. 목표와 완료 정의

**목표**: 더미 금융 데이터 JSON 을 넣어 엔진을 만들고, CLI 로 모드를 골라 실행하면 SPEC §9 계약을 만족하는 결과 JSON 이 나오며, §12 품질 기준을 통과한다.

**완료 정의 (Definition of Done, 전체)**

1. `fdt gen → build → run(5모드) → validate → render` 가 4 프로필 전부에서 예외 없이 끝난다.
2. `pytest -q` 전부 통과. 커버리지 `fdt/engine/` 85% 이상.
3. `fdt eval backtest`, `fdt eval calibration`, `fdt eval monotonic` 이 §12 기준을 만족하거나, 미달 항목마다 원인 분석 문서가 있다.
4. 재현성 테스트(같은 입력·시드 두 번 → 바이트 동일) 통과.
5. 아키텍처 테스트(LLM·네트워크 import 0건, ground_truth 참조 0건) 통과.
6. `docs/QA_REPORT.md` 에 §6 QA 시나리오 전부 실행 결과가 있고, 미해결 결함이 P0/P1 에 없다.

---

## 1. 기술 선택

| 항목 | 선택 | 이유 |
| --- | --- | --- |
| 언어 | Python 3.11+ | 선행 구현(03) 공식 이식 용이, numpy 벡터화 |
| 필수 의존 | `numpy`, `pydantic>=2`, `pyyaml`, `typer`(CLI) | 최소 |
| 개발 의존 | `pytest`, `pytest-cov`, `hypothesis`(속성 테스트), `matplotlib`(render 전용), `ruff`, `mypy` | |
| 패키징 | `pyproject.toml`, `uv` 또는 `venv` | 03 과 동일 방식 |
| 금지 | LLM SDK, HTTP 클라이언트, `random`, `time` 기반 시드 | SPEC §4.2 |
| 인코딩 | UTF-8 고정, Windows 에서 `PYTHONIOENCODING=utf-8` | 한글 출력 |

---

## 2. 저장소 구조 (목표 상태)

```
04_FDT_Engine/
  SPEC.md  PLAN.md  README.md  pyproject.toml
  fdt/
    __init__.py
    engine/                      # 숫자를 만드는 유일한 곳. 외부 I/O 없음
      schemas/
        input.py                 # TwinInput (SPEC §3)
        state.py                 # State, CardState, Committed, EnvelopeState
        behavior.py              # Behavior
        request.py               # ModeRequest + 모드별 params
        result.py                # EngineResult, facts, viz 모델
      taxonomy.py                # 봉투 7·세분류 22·필수/유연 봉투 집합·고정비 유형
      ledger.py                  # TwinInput → LedgerTx[], 흐름 판정, 대사 (§5.2)
      state.py                   # build_state, committed queue, propose_budgets (§5.3~5.5)
      behavior.py                # estimate_behavior (§6)
      simulate.py                # simulate, SimulationResult, PathStats (§7)
      modes/
        forecast.py  whatif.py  goal.py  risk.py  optimize.py   (§8)
      facts.py                   # 모드 result → facts[] (§9.2)
      viz.py                     # 모드 result → viz[] (§9.3)
      engine.py                  # Engine, build_engine, save/load, run
      errors.py                  # E-*/W-* 코드
    adapters/
      finapi.py                  # 금융망 응답 → TwinInput (선택 기능)
    gen/
      profiles/A_steady.yaml  B_card_crunch.yaml  C_impulsive.yaml  D_goal_saver.yaml
      generator.py               # 프로필 → TwinInput + ground_truth (§11)
    eval/
      backtest.py  calibration.py  monotonic.py  report.py
    tools/
      render.py                  # viz → PNG (matplotlib). 엔진 밖
      validate.py                # 결과 스키마·facts/viz 정합
    cli.py
  tests/
    unit/        test_ledger.py test_state.py test_behavior.py test_simulate.py
                 test_forecast.py test_whatif.py test_goal.py test_risk.py test_optimize.py
                 test_facts.py test_viz.py test_engine.py test_generator.py test_cli.py
    property/    test_invariants.py            # hypothesis + 프로필 표본
    golden/      test_golden.py  golden/*.json # 결과 스냅샷
    integration/ test_pipeline.py test_validate_render.py
    test_architecture.py
  data/
    seed/<profile>_<seed>/twin_input.json ground_truth.json profile.yaml
    engines/  out/  eval/
  docs/
    금융_api/  QA_REPORT.md  reviews/  decisions/
```

---

## 3. 단계별 계획 (Phase)

각 단계는 "산출물 / 완료 조건 / 검토 포인트" 를 가진다. 단계 완료 시 §7 리뷰 절차를 거친다.

### Phase 0. 골격과 계약 (D0 ~ D1)

산출물
- `pyproject.toml`, 패키지 골격, `ruff/mypy/pytest` 설정, `README.md`(실행법).
- `engine/schemas/*` 전부(pydantic). `TwinInput`, `State`, `Behavior`, `ModeRequest`(5 모드 params), `EngineResult`, `Fact`, `Viz` 8종.
- `taxonomy.py`: 봉투 7종, 세분류 22종(요구사항명세 표 그대로), 필수 봉투 {교통비, 의료·건강, 편의점·마트·잡화}, 유연 봉투 {외식, 쇼핑, 취미·여가, 기타}.
- `errors.py`: SPEC §3.3, §8.1 의 코드 전부.
- JSON Schema 내보내기 `fdt schema --out schemas/` (에이전트·프론트 팀 공유용).
- `test_architecture.py`: import 금지 목록, `ground_truth`/`hidden_params`/`yaml` 문자열이 `fdt/engine/` 에 없음.

완료 조건: 스키마 라운드트립 테스트(예시 JSON → 모델 → dump → 동일) 통과. 아키텍처 테스트 통과.

검토 포인트: SPEC §3.2 예시 JSON 이 그대로 검증을 통과하는가. 모드 params 의 필수/선택이 SPEC 과 일치하는가.

### Phase 1. 데이터 생성기와 원장 (D1 ~ D3)

산출물
- `gen/generator.py` + 4 프로필 YAML. 하루 처리 순서는 SPEC §7.2 와 동일(생성기가 시뮬레이터의 정답 분포).
- `ground_truth.json` 기록: 일별 계좌 잔액, 카드 부족, 체크 거절, 돌발, 봉투 진짜 지출, 수입 이벤트, 숨김 파라미터.
- `engine/ledger.py`: 정규화, 흐름 판정(§5.2), 취소 두 건 기록, 대사(§3.3), 중복 id 오류.
- `fdt gen`, `data/seed/` 4 프로필 × 시드 1 개 커밋(용량 확인, 1 프로필 6개월 ≈ 300KB 예상).

완료 조건
- 4 프로필 대사 차액 0. 봉투 월 순지출 == `envelope_true_spend`(원장 테스트).
- 같은 프로필·시드 → `twin_input.json` 바이트 동일(`generated_at` 제외).
- 취소 거래 순액 0, 카드대금이 봉투에 안 들어감.

검토 포인트: 생성기 처리 순서와 SPEC §7.2 를 나란히 놓고 대조. D_goal_saver 가 GOAL/OPTIMIZE 를 실제로 자극하는 수치인지(구독 5개, 12월 목표가 아슬아슬하게 불가능).

### Phase 2. State · Behavior · 엔진 빌드 (D3 ~ D5)

산출물
- `engine/state.py`: PRIMARY/EMERGENCY 판정, unbilled/issued_unpaid, 약정 큐(§5.4), 예산 소스 우선순위, 엔진 제안(§5.5), 지표.
- `engine/behavior.py`: §6 표 전부. 클립·기본값.
- `engine/engine.py`: `build_engine`, `save/load`, `engine_id`, `fork`, warnings 수집.
- `fdt build`, `fdt inspect`.

완료 조건
- `State.liquidity == ground_truth.daily_balance[as_of][primary]` (4 프로필 × as_of 3개).
- as_of 두 개로 같은 원장 → 뒤 날짜 거래가 앞 State 에 영향 없음.
- 큐: B 프로필 화요일 as_of 에서 카드 미청구·미결제 due·금액이 수작업 계산과 일치. 월요일 as_of 의 unbilled 경계.
- Behavior: 요일 배수 평균 1.0(±1e-9), A 규칙적 수입 25일, C 불규칙, 수입 1건 None.
- `save → load` 후 `run` 결과가 재계산 엔진과 바이트 동일.

검토 포인트: 예산 소스 우선순위(CONFIRMED > PROPOSED > ENGINE)가 D 프로필에서 실제 CONFIRMED 를 쓰는가. `is_variable` 고정비 0원 경고가 facts 로 이어질 준비가 됐는가.

### Phase 3. 시뮬레이터 + FORECAST + RISK (D5 ~ D8)

산출물
- `engine/simulate.py`: §7.2 8단계 벡터화, `overrides`, `injections`, `event_log`, `stats`, `payment_risks`.
- `modes/forecast.py`, `modes/risk.py`(Safe-to-Spend, 우려 결제, 가속도, health 포함).
- `facts.py`, `viz.py` 의 FORECAST/RISK 부분. `fdt run --mode FORECAST|RISK`.

완료 조건
- 재현성: 같은 시드 → `balances` 바이트 동일.
- `daily_rate=0`, 돌발 0 → 전 경로 동일, 궤적이 큐·수입만 반영한 계단.
- 수작업 3일 시나리오(수입일·고정비·월요일 청구·출금 요일)에서 기대 잔액 정확 일치.
- 카드 출금 부족 → `card_shortfall`, 잔액 유지, 다음 날 재시도 성공.
- `payment_risks` 의 fail_prob 이 경로 집계와 일치(직접 세어 비교).
- 우려 결제 SPEC §15.B 표 3행 판정 일치. health 경계 70/40.
- 성능: 1000경로 × 30일 < 1.5 s.

검토 포인트: 경제 잔액 정의(§7.2 8단계)가 RISK 판정에 쓰이는지, FORECAST 궤적은 실제 잔액인지 구분이 코드에 명확한가. `event_log` 의 성공 비율이 `payment_risks` 와 이중 계산되지 않는가.

### Phase 4. WHATIF + GOAL (D8 ~ D11)

산출물
- `modes/whatif.py`: 7 종 주입(§8.3 표), CRN, 델타, 판정.
- `modes/goal.py`: 3 goal_type, 역산 상한, 필수 봉투 하한, **상한 주입 재시뮬** `plan_achieve_prob`.
- facts/viz 의 WHATIF/GOAL 부분. `fdt run --mode WHATIF|GOAL --params/--params-file`.

완료 조건
- 주입 0원 → 델타 전부 0. 지출 주입 ≥ 0 → 분기 최저 ≤ 기준 최저, 부족 확률 비감소(전 프로필·as_of 표본, 현금·카드·기준일/1일 후/말일 주입).
- `BUDGET_CHANGE behavior_follows=true` 가 elasticity_gate 기준을 바꾸고 false 면 안 바꿈.
- `FIXED_CHANGE cancel` 후 해당 큐 항목이 분기에서 사라짐. `EXTERNAL price_index_mult=1.1` 이 소비 금액만 10% 올림.
- GOAL: 목표 < 현 잔액이고 수입 충분 → feasible, reduction 0, achieve_prob ≥ 0.9. 불가능 목표 → infeasible + gap. 주차 상한 합 == available(±100원 × 주 수). 필수 봉투 하한 80%. `plan_achieve_prob ≥ achieve_prob − 0.02`(계획이 기준보다 나빠지면 버그).
- 목표일 366일 이상 → `E-REQ-RANGE`.

검토 포인트: CRN 이 `injections` 유무에 따라 난수 소비 순서를 바꾸지 않는지(주입 단계가 별도 rng 스트림을 쓰는지). GOAL 의 확정 유입 계산이 시뮬레이터의 수입 일정 함수를 **재사용**하는지(중복 구현 금지).

### Phase 5. OPTIMIZE (D11 ~ D13)

산출물
- `modes/optimize.py`: AUTO 후보 생성(§8.6.1), 단일 평가 → 상위 k → 그리디 조합, 시뮬 예산 ≤ 40, n_paths 자동 하향, `cost_of_action`/`feasibility_note`.
- facts/viz OPTIMIZE 부분(`ranked_bars`, `delta_bars`).

완료 조건
- 후보 0개(유연 봉투 예산 0, 구독 없음) → `ranked=[]`, status OK, note.
- 목적 `MIN_SHORTFALL_PROB` 에서 1위 효과 ≤ 기준(개선 방향), `MAX_END_BALANCE` 에서 ≥ 기준.
- `constraints.protect_essential` 시 필수 봉투 후보 0. `max_cut_ratio` 초과 후보 없음.
- 같은 봉투 두 비율 동시 조합 없음. `sim_calls ≤ 40`.
- D 프로필에서 구독 해지 후보가 상위 3 안에 들어옴(설계 의도 확인).
- 성능 < 25 s.

검토 포인트: 조합 평가에 CRN 을 유지하는가(기준과 같은 시드). `cost_of_action` 문구가 facts 값만 쓰는가.

### Phase 6. 출력 계약 마감: facts · viz · validate · render (D13 ~ D15)

산출물
- `facts.py` 완성: 모드별 필수 facts(§9.4), `allowed_renderings` 생성 규칙(원 단위·만원·약 표기·상대 날짜).
- `viz.py` 완성: 모드별 필수 viz, annotations 는 facts 값만.
- `tools/validate.py`: 스키마, 필수 facts/viz 존재, annotations·caption 숫자 ⊂ facts 표기 집합, viz data 길이 일관(x 와 y 길이).
- `tools/render.py`: 8 종 kind → PNG. 개발·QA 전용.
- `fdt validate`, `fdt render`.

완료 조건
- 4 프로필 × 5 모드 = 20 결과가 `validate` 통과.
- 렌더 20 세트 PNG 생성, QA 육안 검수 체크리스트(§6.3) 통과.
- golden 스냅샷 20개 커밋, `test_golden.py` 통과.

검토 포인트: viz 에 색상·픽셀·라이브러리명이 없는가. facts 의 확률 단위가 모드 내 통일인가(M1).

### Phase 7. 평가와 QA 마감 (D15 ~ D18)

산출물
- `eval/backtest.py`(sMAPE, 최저점 오차, 커버리지), `eval/calibration.py`(ECE, Brier, 구간 표본), `eval/monotonic.py`, `eval/report.py`(마크다운 표).
- 시드 교란 프로필 20개 생성(커밋하지 않고 재생성 스크립트만).
- `docs/QA_REPORT.md`, `docs/reviews/*.md`, README 최종.

완료 조건: §12 기준 충족 또는 항목별 원인 분석. §6 QA 시나리오 전부 실행·기록.

---

## 4. 작업 분할(WBS)과 병렬 규칙

파일 소유를 나눠 병렬 투입한다. 한 작업은 자기 소유 파일과 자기 테스트만 수정한다. 공용 파일(`schemas/*`, `taxonomy.py`, `errors.py`)은 Phase 0 에서 잠그고, 변경은 "설계 변경" 커밋으로 따로 낸다.

| 작업 ID | 소유 파일 | 선행 | 예상 |
| --- | --- | --- | --- |
| W0 골격·스키마 | `pyproject`, `schemas/*`, `taxonomy`, `errors`, `test_architecture` | 없음 | 1일 |
| W1 생성기 | `gen/*`, `tests/unit/test_generator.py` | W0 | 2일 |
| W2 원장 | `engine/ledger.py`, `test_ledger.py` | W0 | 1일 (W1 과 병렬) |
| W3 State | `engine/state.py`, `test_state.py` | W1, W2 | 1.5일 |
| W4 Behavior | `engine/behavior.py`, `test_behavior.py` | W1, W2 | 1일 (W3 과 병렬) |
| W5 엔진 빌드·CLI 기본 | `engine/engine.py`, `cli.py`(gen/build/inspect), `test_engine.py`, `test_cli.py` | W3, W4 | 1일 |
| W6 시뮬레이터 | `engine/simulate.py`, `test_simulate.py` | W3, W4 | 2일 |
| W7 FORECAST·RISK | `modes/forecast.py`, `modes/risk.py`, 해당 테스트 | W6 | 1.5일 |
| W8 WHATIF | `modes/whatif.py`, 테스트 | W6 | 1.5일 (W7 과 병렬) |
| W9 GOAL | `modes/goal.py`, 테스트 | W6, W8(BUDGET_CHANGE 주입 재사용) | 1.5일 |
| W10 OPTIMIZE | `modes/optimize.py`, 테스트 | W8, W9 | 2일 |
| W11 facts·viz | `facts.py`, `viz.py`, `test_facts.py`, `test_viz.py` | W7~W10 결과 스키마 확정 시점부터, 모드별 점진 | 2일 |
| W12 validate·render | `tools/*`, `test_validate_render.py` | W11 | 1.5일 |
| W13 속성·골든·통합 | `tests/property`, `tests/golden`, `tests/integration` | W7~W12 | 1.5일 |
| W14 평가 | `eval/*` | W7 (backtest·calibration), W8 (monotonic) | 2일 |
| W15 QA·문서 | `docs/QA_REPORT.md`, `README.md`, `docs/reviews/` | 전부 | 1.5일 |

병렬 규칙
- 함수 시그니처는 SPEC 이 계약이다. 시그니처를 바꾸려면 SPEC 수정 커밋을 먼저 낸다.
- 공용 fixture(`tests/conftest.py`: 4 프로필 엔진, 짧은 n_paths=200)는 W5 가 만들고 이후 작업은 읽기만 한다.
- 테스트가 깨진 상태로 푸시하지 않는다. 다른 작업의 테스트를 고치지 않는다(소유자에게 넘긴다).
- 코딩 에이전트에 넘길 때 프롬프트에 "SPEC §번호, 소유 파일 목록, 완료 조건, 금지 사항(§4.2)" 네 가지를 반드시 적는다.

---

## 5. 테스트 계획

### 5.1 단위 테스트 (모듈별 필수 케이스)

`test_ledger.py`
- 취소 CARD 거래 → SPEND(−)+REFUND(+) 두 건, 순액 0.
- `CARD_BILL` 은 envelope None. 봉투 월 순지출 == ground_truth.
- `exclude_tag` EMERGENCY/CARRYOVER 는 봉투 차감 제외, DUTCH 입금은 봉투 +.
- 같은 id 다른 내용 → `E-INPUT-DUP`. 같은 id 같은 내용 → 1건.
- 대사 차액 0(4 프로필). `strict=True` 에서 인위적 차액 → 오류.
- `flow_hint` 가 있으면 판정 건너뜀.

`test_state.py`
- as_of 이후 거래 무영향. `liquidity == daily_balance[as_of]`.
- 예산 소스 우선순위 3 케이스. `propose_budgets` 완결 월 3/1/0 케이스, 만원 올림·하한.
- 큐: 화요일 as_of(B) 미청구·미결제 due/금액. 월요일 경계. 변동형 고정비 중앙값/0원 경고. LOAN 이자 10원 단위, `loan_rate_delta_bp` 반영.
- 중복 제거: fixed_expenses 우선.

`test_behavior.py`
- 요일 배수 평균 1, `n<10` 전부 1. sigma 클립. pooled/기본값 경로.
- 수입 일정 A/C/1건. 탄력도 저잔여 5일 미만 1.0. 돌발 0건 기본값.
- 순환 금지 문자열 검사(아키텍처 테스트와 중복이지만 모듈 단위로도).

`test_simulate.py`
- 재현성 바이트 동일. 결정론 계단 케이스. 수작업 3일 시나리오. 카드 부족 재시도.
- 경제 잔액 = 실제 − 미결제 − 거절 의무 − 억제 수요(수작업 케이스).
- `overrides` 가 원본 state 를 바꾸지 않음(깊은 비교).
- 주입 단계 rng 분리: 주입 유무로 소비 난수가 달라지지 않음(`envelope_spend` 동일).
- `payment_risks` fail_prob == 경로 직접 집계. 성능.

`test_forecast.py` : `median[0] == liquidity`. 봉투 `exhaust_date_median` 이 `spent_now ≥ budget` 이면 as_of. `overrun_prob ∈ [0,1]`. 이벤트 목록이 큐·수입 전부 포함.

`test_risk.py` : SPEC §15.B 3행. Safe-to-Spend ≥ 0, 고정비 > 잔액 → 0 + note. 가속도 노이즈 플로어. health 경계. `recent_tx_ids` 지정 시 그것만 검사.

`test_whatif.py` : 주입 0 → 델타 0. 단조성 표본. 7 종 주입 각 1 케이스. 판정 3 단계 경계값. `crn=true`.

`test_goal.py` : feasible/infeasible/상한 합/필수 하한/`plan_achieve_prob`/366일 오류/ENVELOPE_ADHERE 타입.

`test_optimize.py` : 후보 0, 방향성, 제약, 조합 중복 금지, `sim_calls ≤ 40`, D 프로필 구독 해지 상위권.

`test_facts.py` : 모드별 필수 키 존재. `allowed_renderings` 규칙(19,100 → "19,100원","1만 9천원","1.9만원","약 2만원"). 확률 단위 통일. 날짜 상대 표기.

`test_viz.py` : 모드별 필수 kind. data 길이 일관. annotations 라벨 숫자 ⊂ facts. 금지 키(color, px, library) 없음.

`test_engine.py` : `engine_id` 안정성(같은 입력 → 같은 id, 거래 1건 변경 → 다른 id). save/load 동일 결과. load 시 id 불일치 거부. warnings 수집.

`test_generator.py` : 재현성. ground_truth 필드 전부 존재. 4 프로필 특성 확인(A 부족 0, B 카드 부족 ≥ 1, C 체크 거절 ≥ 10, D 구독 5개·예산 CONFIRMED).

`test_cli.py` : 각 서브커맨드 종료 코드 0, `--mode` 누락 → 2, 잘못된 params → `E-REQ-*` JSON 과 종료 코드 1, UTF-8 출력.

### 5.2 속성(불변식) 테스트 (`tests/property/test_invariants.py`)

4 프로필 × as_of 표본(데이터 90일 이후 매주 월요일) × n_paths 200:
- `0 ≤ shortfall_prob, card_shortfall_prob ≤ 1`, `card_shortfall_prob ≤ shortfall_prob + 0.05`.
- `forecast.median[0] == liquidity`. `p10 ≤ median ≤ p90` 전 구간.
- `health.score ∈ [0,100]`, `risk_score ∈ [0,100]`.
- WHATIF 단조성(현금·카드, 금액 1만/10만/100만, 시점 3종).
- GOAL: `weekly_caps` 합 == `total_discretionary_cap`(±100원 × 주 수). 필수 봉투 하한.
- OPTIMIZE: 1위 효과가 기준보다 나쁘지 않음.
- hypothesis: 임의 `TwinInput`(작은 규모) 생성 → `build_engine` 이 예외 대신 E-/W- 코드로만 실패.

### 5.3 골든 스냅샷 (`tests/golden/`)

4 프로필 × 5 모드 결과 JSON(`elapsed_ms` 제거) 커밋. 공식 변경 시 골든 갱신은 "설계 변경" 커밋과 함께만 허용. 골든 차이 리포트는 키 단위 diff 로 출력.

### 5.4 통합 테스트 (`tests/integration/`)

- `test_pipeline.py`: 임시 디렉터리에서 `gen(3개월) → build → run 5모드 → validate` 가 4 프로필에서 끝난다.
- `test_validate_render.py`: 20 결과 렌더가 PNG 파일을 만들고 크기 > 0. 잘못된 viz(길이 불일치, facts 밖 숫자) 를 validate 가 잡는다.

### 5.5 평가 (`fdt eval`)

| 평가 | 절차 | 기준(SPEC §12) |
| --- | --- | --- |
| backtest | 프로필별 `as_of = end − 30`, FORECAST 1000경로, 정답 `daily_balance` 와 비교 | sMAPE A ≤ .15, B ≤ .25, C ≤ .40, D ≤ .20. 최저점 오차 ≤ 30만(C 50만). 커버리지 .6~.95 |
| calibration | 4 프로필 + 시드 교란 20 = 24 사용자, as_of 7일 간격, RISK `card_shortfall_prob` vs 실제 30일 내 부족 | ECE ≤ .15, Brier < 기준율. 구간 표본 < 15 는 보류 표시 |
| monotonic | 속성 테스트와 같은 표본을 1000경로로 재실행 | 위반 0건 |
| perf | 12 항목 벤치 | SPEC §12 |

결과는 `data/eval/*.json` 과 `docs/EVAL_REPORT.md`(표) 로 남긴다. 미달 항목은 원인·다음 조치를 적는다. 기준을 낮춰 통과시키지 않는다.

---

## 6. QA 계획

### 6.1 QA 원칙

- QA 는 구현자가 아닌 사람(또는 별도 에이전트)이 CLI 만으로 수행한다. 코드를 읽지 않고 SPEC 과 결과 JSON·PNG 만 본다.
- 결함은 `docs/QA_REPORT.md` 에 ID(`QA-###`), 재현 명령, 기대(SPEC 절), 실제, 심각도(P0 계산 오류·재현성 붕괴 / P1 계약 위반 / P2 표기·문구) 로 기록한다.

### 6.2 시나리오 (모드 선택은 QA 가 직접)

| ID | 시나리오 | 명령 | 확인 |
| --- | --- | --- | --- |
| QA-01 | 엔진 생성 기본 | `gen A → build → inspect` | 잔액·봉투·큐가 twin_input 과 손으로 맞춘 값과 일치. warnings 0 |
| QA-02 | 오염 입력 | 카드의 계좌 참조 삭제, 거래 id 중복, as_of 이후 거래 삽입 | 각각 `E-INPUT-REF`, `E-INPUT-DUP`, `W-INPUT-FUTURE_TX` |
| QA-03 | 짧은 이력 | 거래 20일치만 | `W-INPUT-SHORT_HISTORY`, Behavior 기본값 비중, FORECAST 정상 |
| QA-04 | FORECAST A/B/C/D | `run --mode FORECAST` | 최저점·말일 잔액이 렌더 PNG 와 일치. C 밴드가 A 보다 넓음. 이벤트가 큐와 일치 |
| QA-05 | RISK B | `run --mode RISK` | 가장 위험한 결제가 카드대금. Safe-to-Spend ≥ 0. table 과 gauge 의 숫자가 facts 와 동일 |
| QA-06 | 우려 결제 | B 의 as_of 당일에 25만원 쇼핑 거래 추가 후 RISK | `CONCERNING_TX DANGER` |
| QA-07 | WHATIF 카드 15만 3일 뒤 | `run --mode WHATIF --params ...` | 분기 최저 ≤ 기준, verdict 합리적, 2 시리즈 line_band |
| QA-08 | WHATIF 구독 해지 | `FIXED_CHANGE cancel` | 분기 말일 잔액 ≥ 기준, 해당 이벤트가 분기에서 사라짐 |
| QA-09 | WHATIF 물가 +10% | `EXTERNAL price_index_mult 1.1` | 봉투 지출 중앙값 ≈ 기준 × 1.1 (±3%) |
| QA-10 | GOAL D 12월 200만 | `run --mode GOAL` | `achieve_prob` 와 `plan_achieve_prob` 순서, step_bars 합 == cap, 필수 봉투 하한 |
| QA-11 | GOAL 불가능 목표 | 목표 1억 | `feasible=false`, gap 음수, 상한 0 아님(필수만) |
| QA-12 | OPTIMIZE D | `run --mode OPTIMIZE` | 구독 해지 상위권, `sim_calls ≤ 40`, 1위 효과 개선 방향 |
| QA-13 | OPTIMIZE 제약 | `protect_essential=false, max_cut_ratio=0.1` | 필수 봉투 후보 등장, 비율 > 0.1 후보 없음 |
| QA-14 | 재현성 | 같은 명령 2회, `diff` | `elapsed_ms` 외 동일 |
| QA-15 | 시드 변경 | `--seed 43` | 확률 값 변동 ≤ 0.05, 판정 동일(B 기준) |
| QA-16 | save/load | `build → run` vs `load → run` | 동일 |
| QA-17 | validate 부정 케이스 | 결과 JSON 의 caption 숫자를 손으로 바꿈 | `validate` 실패 |
| QA-18 | 잘못된 요청 | `--mode GOAL` 에 target_date 누락, horizon 400 | `E-REQ-MISSING`, `E-REQ-RANGE`, 기본값 대체 없음 |
| QA-19 | 금융망 어댑터 | 03 저장소 `snapshot.json` → `adapters/finapi` → build | 성공, 대사 0 |
| QA-20 | 성능 | 12 항목 시간 측정 | SPEC §12 |

### 6.3 viz 육안 검수 체크리스트 (`fdt render` PNG)

- `line_band`: 밴드가 중앙값을 감싼다. 최저점 annotation 위치·라벨 숫자가 facts 와 같다. WHATIF 는 두 선이 구분된다.
- `event_timeline`: 이벤트 날짜가 `result.events` 와 같다. fail_prob 높은 이벤트가 눈에 띈다.
- `gauge`: 임계값 20/50 표시, level 텍스트 일치.
- `progress_bars`: 초과 봉투가 100% 를 넘게 표시된다. projected 가 있으면 구분된다.
- `step_bars`: 주차 합이 total 과 같다.
- `ranked_bars`: 순위·효과 값이 result.ranked 와 같다.
- `table`: 단위 표기(원, %, 날짜) 일관.
- 공통: caption 의 숫자가 facts 표기 중 하나다. 한글 깨짐 없음.

### 6.4 SPEC 대조 감사

QA 마감 전, SPEC §3.3, §8.1~8.6, §9.4, §12 의 표를 한 줄씩 체크박스로 옮겨 `docs/QA_REPORT.md` 부록에 붙이고 전부 확인 표시가 있어야 한다.

---

## 7. 리뷰 절차

1. 구현자는 커밋(또는 PR) 설명에 **SPEC 절 번호, 완료 조건 대비 결과, 테스트 목록, 벤치 수치** 를 적는다.
2. 리뷰어는 §8 체크리스트로 확인하고 `docs/reviews/YYYYMMDD_<작업ID>.md` 에 결과를 남긴다.
3. 설계와 다르게 구현했으면 SPEC 수정 커밋을 먼저 낸다. 골든 갱신은 그 커밋에 포함한다.
4. Phase 3, 5, 7 종료 시점에 전체 리뷰(아키텍처·불변식·성능)를 한 번씩 한다.
5. 코딩 에이전트가 구현한 코드는 다른 모델 또는 사람이 리뷰한다. 자기 리뷰만으로 통과시키지 않는다.

---

## 8. 코드 리뷰 체크리스트

- [ ] `fdt/engine/` 에 LLM·HTTP import 없음. `random`, `time` 시드 없음.
- [ ] 원장 불변. What-if 는 `fork` 또는 `overrides` 로만.
- [ ] 금액 정수. 100원/1,000원/만원 단위 규칙이 SPEC 과 일치.
- [ ] `as_of` 필터가 모든 원장 접근에 있음.
- [ ] 다섯 모드가 `simulate()` 하나만 호출. 모드 안에 전이 규칙 재구현 없음.
- [ ] 수입 일정·큐 계산이 State/Behavior 함수를 재사용(GOAL, OPTIMIZE 에서 중복 구현 금지).
- [ ] 필수 파라미터 누락을 기본값으로 대체하지 않음.
- [ ] facts 의 값이 result 에서 파생됨(재계산 없음). viz annotations 숫자 ⊂ facts.
- [ ] 출력에 색상·픽셀·라이브러리명 없음.
- [ ] 테스트가 SPEC 의 수치 예(§15.B 등)를 그대로 사용.
- [ ] 성능 기준 측정값이 설명에 있음.
- [ ] 한글 출력 UTF-8. 문서·주석에 SPEC 절 참조.

---

## 9. 일정 (D0 = 2026-09-07)

| 기간 | Phase | 병렬 작업 | 마일스톤 |
| --- | --- | --- | --- |
| D0~D1 | 0 | W0 | 스키마 잠금, JSON Schema 배포 |
| D1~D3 | 1 | W1 ∥ W2 | 4 프로필 seed 커밋, 대사 0 |
| D3~D5 | 2 | W3 ∥ W4 → W5 | `fdt build/inspect` 동작 |
| D5~D8 | 3 | W6 → W7 | FORECAST·RISK 결과 JSON, 1차 전체 리뷰 |
| D8~D11 | 4 | W8 ∥ W7 잔여 → W9 | WHATIF·GOAL |
| D11~D13 | 5 | W10, W11 시작 | OPTIMIZE, 2차 전체 리뷰 |
| D13~D15 | 6 | W11, W12, W13 | validate·render, 골든 20개 |
| D15~D18 | 7 | W14, W15 | 평가 리포트, QA 리포트, 3차 리뷰, v0.1 태그 |

여유 2일(D18~D20)은 평가 미달 원인 분석과 SPEC v0.2 항목(급여 주기 앵커, 수입 간격 분포) 정리에 쓴다.

---

## 10. 리스크와 대응 (계획 관점)

| # | 리스크 | 징후 | 대응 |
| --- | --- | --- | --- |
| P1 | 생성기와 시뮬레이터 처리 순서 불일치 | 백테스트 A 조차 sMAPE 초과 | Phase 1 에서 두 코드를 나란히 리뷰. 공통 상수 모듈(`taxonomy`, 청구 규칙)을 공유 |
| P2 | 공용 스키마 잦은 변경으로 병렬 작업 충돌 | 스키마 커밋이 하루 2회 이상 | Phase 0 에서 예시 JSON 5 모드 전부 작성해 잠금. 변경은 설계 변경 커밋으로만 |
| P3 | OPTIMIZE 시간 초과 | 25 s 초과 | n_paths 400 하향, 후보 k 축소, 조합 깊이 2 로 제한 |
| P4 | 캘리브레이션 표본 부족 | 구간 표본 < 15 | 시드 교란 20 → 40 으로 확대(생성만, 커밋 안 함) |
| P5 | facts 표기 규칙이 에이전트 팀 요구와 다름 | 통합 시 문장 충실도 실패 | Phase 0 에 JSON Schema 와 예시를 공유하고 M1 을 D5 전에 합의 |
| P6 | 03 저장소 코드 이식 시 스키마 혼선 | 금융망 필드명이 엔진 코어에 남음 | 이식은 공식·테스트 케이스만, 코드는 `TwinInput` 기준으로 재작성. 어댑터에만 금융망 필드 허용 |
| P7 | Windows 한글 인코딩 | 콘솔 깨짐, 테스트 실패 | 모든 파일 I/O `encoding="utf-8"`, CLI 진입점에서 stdout 재설정 |

---

## 11. 선행 저장소(03) 활용 방침

- **가져오는 것**: Behavior 추정 공식, 전이 8단계, 우려 결제·Safe-to-Spend·health 공식, 백테스트·캘리브레이션 절차, 테스트 케이스 아이디어, A/B/C 프로필 파라미터, 카드 청구 주기 예시.
- **가져오지 않는 것**: 금융망 스키마 기반 인입 코드, 에이전트·LLM·웹·대시보드, 툴 정의.
- 이식한 함수는 `TwinInput`/`State` 스키마에 맞춰 재작성하고, 원 설계서 절 번호를 docstring 에 남긴다(`# from 03 §7.2.1`).
- 03 의 `snapshot.json` 은 `adapters/finapi.py` 의 회귀 입력으로 쓴다(QA-19).

---

## 12. 산출물 체크리스트 (v0.1 태그 조건)

- [ ] `SPEC.md` v0.1 확정(미결 M1, M2 결정 반영)
- [ ] `fdt/engine/` 전 모듈, `fdt/gen/`, `fdt/eval/`, `fdt/tools/`, `cli.py`
- [ ] `schemas/*.schema.json` 내보내기
- [ ] `data/seed/` 4 프로필, `tests/golden/` 20개
- [ ] `pytest -q` 통과, 커버리지 ≥ 85%
- [ ] `docs/EVAL_REPORT.md`, `docs/QA_REPORT.md`, `docs/reviews/` 3회 전체 리뷰
- [ ] `README.md`: 설치, `gen → build → run → validate → render` 5분 안내, 모드별 요청 예시 5개
