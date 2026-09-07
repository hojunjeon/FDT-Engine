# QA 리포트 (W15, 담당 L2)

QA 원칙(PLAN §6.1)에 따라 코드는 읽지 않고 SPEC.md v0.6 과 CLI 실행 결과(JSON·PNG)만으로 판정했다.
`--help` 는 명령 사용법 확인 목적으로만 사용했다.

## 0. 요약

- 시나리오 QA-01~QA-20: **PASS 17 / PARTIAL(확인 불가) 2 (QA-08, QA-09) / 미구현 1 (QA-19)**. 시나리오 자체가 FAIL 로 끝난 항목은 없다.
- viz 육안 검수·SPEC 대조 감사 과정에서 발견한 결함: **8건**(P0 0 / P1 6 / P2 2).
- 결함은 전부 `fdt/tools/render.py`(viz 렌더러), 모드별 결과 직렬화(OPTIMIZE `AppliedAction`/`Injection` 필드명), FORECAST 이벤트 집계 범위에 있다. **엔진의 핵심 수치 계산(잔액·확률·상한·순위 판정) 자체가 틀린 사례는 발견하지 못했다.**
- 미해결 P0 없음. 미해결 P1 6건(QA-101, 102, 104, 106, 107, 108) — 아래 §2 참조.
- 참고: `docs/EVAL_REPORT.md`(§12 자동 평가)에는 이미 C 프로필 sMAPE 초과, 전 프로필 커버리지 미달이 FAIL 로 기록되어 있다. 이 리포트는 그 항목들을 새 QA-ID 로 중복 채번하지 않고 §4 SPEC 대조 감사에서만 인용한다(소유: EVAL_REPORT/L1).

## 1. 환경

- 저장소: `04_FDT_Engine` (git 아님), Python `.venv/Scripts/python`, `PYTHONIOENCODING=utf-8`.
- 엔진 4종 재빌드 시각: 2026-09-07 17:01 (본 리포트의 모든 시나리오 결과는 이 시점 이후 재확인한 값이다).
- **동시 작업 유의사항**: 이 QA 는 L1(behavior.py/engine.py)·L3(SPEC/PLAN) 과 동시에 진행됐다. 세션 초반에 만든 `data/engines/B.engine.json` 과 세션 후반에 동일 입력으로 재빌드한 파일의 `behavior.envelopes[].daily_rate` 가 달랐던 사례가 있었는데, 원인은 재현성 결함이 아니라 **그 사이 L1 이 `behavior.py` 를 수정**했기 때문으로 확인했다(QA-16 참조, 동일 시점 연속 3회 빌드는 완전히 바이트 동일했다). 이 때문에 아래 모든 수치는 §1 의 재빌드 시각 기준 산출물로 통일해 재확인했다.
- CLI: `.venv/Scripts/python -m fdt.cli <command> ...`.
- n_paths 는 명시하지 않으면 1000, seed 는 42.

## 2. 시나리오 (QA-01 ~ QA-20)

| ID | 명령(재현) | 기대(SPEC) | 실제 | 판정 |
| --- | --- | --- | --- | --- |
| QA-01 | `build --input data/seed/A_steady_7/twin_input.json --out data/engines/A.engine.json` → `inspect --engine data/engines/A.engine.json` | §4.1/§5.1: 잔액·봉투·큐가 twin_input 값과 일치, warnings 0 | liquidity=5,796,000(계좌10 balance 그대로), emergency_fund=2,100,000(계좌11 balance 그대로), `meta.warnings=[]` | **PASS** |
| QA-02 | (a) `cards[0].withdrawal_account_id=999999` 로 편집한 사본 build (b) `transactions` 의 id 를 다른 내용으로 중복시킨 사본 build (c) `as_of`(9/7) 이후 날짜(9/8) 거래를 추가한 사본 build | §3.3: 각각 `E-INPUT-REF`, `E-INPUT-DUP`, `W-INPUT-FUTURE_TX`(무시하고 성공) | (a) `{"error":{"code":"E-INPUT-REF","message":"card 20 -> account 999999 없음"}}` (b) `{"error":{"code":"E-INPUT-DUP","message":"transaction 1001 가 서로 다른 내용으로 중복됨"}}` (c) `built engine ...` + `warning: W-INPUT-FUTURE_TX` | **PASS** |
| QA-03 | A 의 거래를 as_of 이전 20일치만 남긴 사본 build → `inspect` → `run --mode FORECAST` | §3.3: `W-INPUT-SHORT_HISTORY`, Behavior 기본값 비중 증가, FORECAST 정상 | `warning: W-INPUT-SHORT_HISTORY`, `window_days=21`(<28), 전 봉투 `elasticity=1.00`(기본값), `payday_boost=1.00 pre_payday_damp=1.00`(기본값). `run --mode FORECAST --validate` → `validate: ok` | **PASS** |
| QA-04 | A/B/C/D 각각 `run --mode FORECAST --horizon 30 --n-paths 1000 --seed 42` | §8.2: min/end 잔액이 PNG(§6.3) 와 일치, C 밴드가 A 보다 넓음, 이벤트가 큐와 일치 | A: `min_point{date:2026-09-24, median:4,828,550}` (render PNG 라벨 "최저점 4,828,550원"과 일치) `end_point{median:6,559,150}`. 평균 밴드폭(p90-p10) A=328,248, C=699,843 (C>A). **단, C 의 `events[]` 가 committed queue(§3 참조)와 불일치 — QA-108 로 별도 기록** | **PASS**(수치·밴드폭 기준). 이벤트 정합성은 QA-108 결함 참조 |
| QA-05 | `run --engine B.engine.json --mode RISK` | §8.5: 가장 위험한 결제=카드대금, safe_to_spend≥0, table/gauge 숫자=facts | `risk_score=13(SAFE)`, `max(fail_prob)` 결제 = `2026-09-22 CARD_BILL 카드대금 KB 톡톡 Pay fail_prob=0.13`(카드대금 맞음), `safe_to_spend_today=26,000≥0`. facts.risk_score=13=gauge.value=13=table 첫 행 amount 일치 | **PASS** |
| QA-06 | B 의 twin_input 사본에 as_of(9/7) 당일 25만원 CARD 쇼핑(subcategory 16) 거래 추가 → build → `run --mode RISK` | §8.5.2: `CONCERNING_TX` `DANGER` | `alerts=[{"kind":"ACCELERATION","severity":"DANGER",...},{"kind":"CONCERNING_TX","severity":"DANGER","tx_id":2915,"amount":250000,...}]` | **PASS** |
| QA-07 | `run --engine B --mode WHATIF --params '{"injections":[{"type":"SPEND","days_from_now":3,"amount":150000,"envelope_id":5,"method":"CARD"}]}'` | §8.3: 분기 최저 ≤ 기준, verdict 합리적, 2 시리즈 line_band | base.min_point.median=24,150(≥0) vs branch.min_point.median=-125,850(<0) → 불변식(주입≥0 → 분기 최저≤기준) 성립. `verdict="DANGER"`(기준 최저≥0 이고 분기 최저<0 조건과 일치), `branch_level="WARNING"`. line_band 시리즈명 `["기준","분기"]` | **PASS** |
| QA-08 | `run --engine D --mode WHATIF --params '{"injections":[{"type":"FIXED_CHANGE","fixed_expense_id":44,"cancel":true,"from":"2026-09-07"}]}'`(정수기 렌탈 해지) | §8.3: 분기 말일 잔액≥기준, 해당 이벤트가 분기에서 사라짐 | `base.end_point.median=3,645,600` vs `branch.end_point.median=3,670,600`(≥, delta=+25,000=월 렌탈료와 일치) | **PASS**(잔액 조건). "이벤트가 분기에서 사라짐"은 §8.3 `result.base/branch` 스키마에 `events[]` 필드가 아예 없어(트레젝토리·min/end/확률만 포함) JSON 만으로 확인 불가 — 스펙상 정의 부재이며 결함으로 보지 않음 |
| QA-09 | `run --engine D --mode FORECAST`(기준) vs `run --engine D --mode WHATIF --params '{"injections":[{"type":"EXTERNAL","price_index_mult":1.1}]}'` | §8.3: 봉투 지출 중앙값 ≈ 기준 × 1.1 (±3%) | FORECAST 의 `result.envelopes[].projected_month_end_median` 은 봉투별 값을 주지만, WHATIF 결과의 `delta.envelopes` 는 `EXTERNAL` 주입에 대해 **빈 배열**(`[]`)이라 봉투별 실제 지출액이 노출되지 않는다. 전체 말일 잔액 델타(`-114,350`/30일)만 간접 확인 가능 | **PARTIAL(확인 불가)** — ±3% 정밀 검증에 필요한 봉투별 수치가 WHATIF 결과 스키마에 없음. 결함으로 단정하지 않음(§8.3 예시가 SPEND 케이스만 보여 EXTERNAL 의 envelope 델타 포함 여부가 SPEC 에 명시돼 있지 않음) |
| QA-10 | `run --engine D --mode GOAL --horizon 120 --params '{"goal_type":"SAVE","target_amount":2000000,"target_date":"2026-12-31","protect_essential":true}'` | §8.4: achieve_prob·plan_achieve_prob 순서, step_bars 합==cap, 필수 봉투 하한 | `achieve_prob=0.831 < plan_achieve_prob=1.0`(순서 정상, 계획이 기준보다 낫다). `Σweekly_caps.total_cap=3,181,672 ≈ required.total_discretionary_cap=3,181,667`(17주 반올림 오차 5원). viz `step_bars`: 17주 전부 `Σstacks[i].y == total[i]` | **PASS** |
| QA-11 | 위와 동일 engine, `target_amount=100000000` | §8.4: `feasible=false`, gap 음수, 상한 0 아님(필수만) | `feasible=false`, `gap.median=-97,776,450`(음수). `required.total_discretionary_cap=0`(재량 봉투 전부 0)이지만 필수 봉투(교통비=16,200/의료·건강=13,000/편의점·마트·잡화=36,863)는 0이 아님(80% 하한 유지) | **PASS** |
| QA-12 | `run --engine D --mode OPTIMIZE --params '{"objective":"MIN_SHORTFALL_PROB","candidates":"AUTO","max_actions":3,"constraints":{"protect_essential":true,"max_cut_ratio":0.5,"allow_emergency_draw":false}}'` | §8.6: 구독 해지 상위권, `sim_calls≤40`, 1위 효과 개선 방향 | `sim_calls=28≤40`, `n_paths_used=400`. 1위 조합=[카드 출금요일 변경, 헬스장 정기결제 해지, 정수기 렌탈 해지] (구독 해지 2건 포함), `effect.end_balance_median` +278,800(개선 방향 정상) | **PASS** |
| QA-13 | 위 engine, `constraints={"protect_essential":false,"max_cut_ratio":0.1,"allow_emergency_draw":false}` | §8.6: 필수 봉투 후보 등장, 비율>0.1 후보 없음 | `BUDGET_CHANGE` 후보에 필수 봉투(교통비=2, 의료·건강=3, 편의점·마트·잡화=6) 등장. 등장한 모든 `cut_ratio`==0.1(0.2/0.3 후보는 상한 필터로 제외) | **PASS** |
| QA-14 | `run --mode RISK`(B) 동일 커맨드 2회 실행 | §12: 재현성, `elapsed_ms` 제외 바이트 동일 | 두 결과 JSON 에서 `meta.elapsed_ms` 제거 후 dict 비교 → `True`(완전 동일) | **PASS** |
| QA-15 | `run --mode RISK`(B) `--seed 43` | §6.2: 확률 값 변동≤0.05, 판정 동일(B 기준) | `shortfall_prob 0.151→0.154`(Δ0.003), `card_shortfall_prob 0.134→0.142`(Δ0.008), `risk_score 13→14`(Δ0.01), `level SAFE→SAFE`(동일) | **PASS** |
| QA-16 | 동일 입력을 3회 연속 `build`(같은 세션·같은 코드 시점) → 각각 `run --mode RISK` | §12: build→run 결과가 재로드 후 실행한 결과와 동일 | `data/out/qa/B_rebuild_{1,2,3}.engine.json` 3파일 완전 바이트 동일. 그 중 2개로 각각 `run` 한 결과도 `elapsed_ms` 제외 완전 동일 | **PASS**(§1 의 동시 편집 유의사항 참고: 세션 시간차를 두고 만든 파일끼리 비교하면 L1 의 코드 수정 때문에 달라질 수 있으나 이는 build 자체의 비결정성이 아니다) |
| QA-17 | `B_risk.json` 의 gauge caption 숫자를 손으로 `13`→`9999` 로 변조 → `validate --result` | §9.3 R7: validate 실패 | 변조본: `validate ...: FAIL (1건)` (`viz risk caption 의 숫자 '9999' 가 facts 표기 집합에 없다`), exit=1. 원본: `validate ...: OK`, exit=0 | **PASS** |
| QA-18 | (a) `--mode GOAL --params '{"goal_type":"BALANCE","target_amount":2000000}'`(target_date 누락) (b) `--mode FORECAST --horizon 400`(범위 밖) (c) `--horizon 400 --n-paths 50`(동시 위반) | §8.1: `E-REQ-MISSING`, `E-REQ-RANGE`, 기본값 대체 없음, 동시 실패 전부 보고 | (a) `E-REQ-MISSING`(BALANCE 는 target_amount, target_date 모두 필요) (b) `E-REQ-RANGE`(horizon_days 는 1~365) (c) `error.details.errors[]` 에 `E-REQ-RANGE`(horizon_days) 와 `E-REQ-RANGE`(n_paths) **둘 다** 보고됨 | **PASS** |
| QA-19 | (03 저장소 `snapshot.json` → `fdt/adapters/finapi` → build) | 성공, 대사 0 | `fdt/adapters/` 디렉터리는 존재하나 비어 있다(`finapi.py` 없음). 저장소 전체를 찾아도 `finapi*` 파일 없음 | **미구현, v0.2**(테스트 불가) |
| QA-20 | §12 표 12항목 시간 측정 | SPEC §12 기준 전부 통과 | `docs/EVAL_REPORT.md` 측정치(B_card_crunch seed7): build 9.1ms/1000, simulate 39.0ms/1500, whatif 89.0ms/3000, goal 56.0ms/4000, optimize 655.0ms/25000 — 전부 기준의 1/10 이하. 본 세션에서 개별 `meta.elapsed_ms` 로 재확인: RISK 51ms, WHATIF 92ms, GOAL 239ms, OPTIMIZE 604ms — 전부 기준 이내 | **PASS** |

## 3. 결함 목록

| ID | 요약 | 재현 | 기대 | 실제 | 심각도 | 추정 소유 모듈 |
| --- | --- | --- | --- | --- | --- | --- |
| QA-101 | OPTIMIZE `AppliedAction.override` 의 필드명이 SPEC 과 다름 | `run --engine D --mode OPTIMIZE ...` 후 `result.ranked[].actions[].override` 확인 | SPEC §8.6 S57: `OverrideSpec = CARD_WITHDRAWAL_WEEKDAY { card_id: int, new_weekday: int }` | 실제 JSON 은 `{"type":"CARD_WITHDRAWAL_WEEKDAY","card_id":20,"weekday":5}` — 필드명이 `new_weekday` 가 아니라 `weekday` | P1(계약 위반) | 결과 직렬화(OPTIMIZE 러너, `fdt/engine/*optimize*`) |
| QA-102 | `FIXED_CHANGE` Injection 의 날짜 필드가 `from` 이 아니라 `from_` 로 직렬화됨 | `run --engine D --mode WHATIF --params '{"injections":[{"type":"FIXED_CHANGE","fixed_expense_id":44,"cancel":true,"from":"2026-09-07"}]}'` 후 결과의 `request.params.injections[0]` 확인, 또는 QA-12 의 `ranked[].actions[].injection` 확인 | SPEC §8.3: `FIXED_CHANGE` 필드는 `from`(필수) | `request` 에코와 OPTIMIZE `AppliedAction.injection` 양쪽 모두 `"from_":"2026-09-07"` — 트레일링 언더스코어가 그대로 노출(Python 예약어 회피용 별칭이 직렬화 alias 로 연결되지 않음) | P1(계약 위반) | Injection 스키마(`fdt/engine/schemas` 계열) |
| QA-103 | `table` viz 가 column 의 `unit` 을 표기에 반영하지 않음 | `render --result data/out/qa/A_risk_full.json --out ...` 후 `payments_table.png` 확인 | SPEC §9.3: column `{"key":"amount","unit":"KRW"}`, `{"key":"fail_prob","unit":"%"}`. §6.3 체크리스트: "단위 표기(원,%,날짜) 일관" | PNG 표의 금액 셀이 `62000`(원 없음), 부족 확률 셀이 `0`(% 없음) — 값은 맞지만 단위 접미사가 전혀 붙지 않음 | P2(표기) | `fdt/tools/render.py` |
| QA-104 | `event_timeline` 라벨이 겹쳐 읽을 수 없고 x축이 날짜가 아닌 정수 인덱스 | `render --result data/out/qa/A_forecast.json`(또는 `A_risk_full.json`) 후 `events_event_timeline.png`/`risk_events_event_timeline.png` 확인(이벤트 10개 안팎) | §9.3 encoding: `x:"date"`. §6.3: "이벤트 날짜가 result.events 와 같다" | x축 눈금이 `0,2,4,6,8`(정수)이고 각 점 위 텍스트 라벨(항목명+날짜)이 서로 겹쳐 글자가 뒤섞여 판독 불가(예: "관리비"와 "카드대금 신한 체크카드"가 겹침). 이벤트 수가 적은 RISK(C, 4건)에서는 겹치지 않아 문제가 드러나지 않음 | P1(필수 viz 무력화) | `fdt/tools/render.py` |
| QA-105 | 다수 viz caption 문장이 "…원다." 로 끝나 한국어 문법 오류(→ "…원이다.") | 아무 결과나: `A_risk_full.json` 의 `payments`/`risk_events` caption, `A_whatif_full.json` 의 `base_vs_branch` caption, `*_goal_full.json` 의 `goal_cap_trajectory` caption | 자연스러운 한국어 문장 | "오늘 안심 소비 한도는 181,100원다.", "부족액(중앙값)은 +7,296,400원다.", "판정은 OK, 최저 잔액 변화는 -150,000원다." 등 4 프로필 전체에서 동일 패턴 재현 | P2(표기·문구) | caption/facts 문구 템플릿 |
| QA-106 | OPTIMIZE `ranked_bars` 가 서로 다른 단위(KRW/확률)의 delta 를 전부 ×100 해서 "%" 로 라벨링, 순위와 막대 길이가 무관해짐 | `run --engine A --mode OPTIMIZE ...` 후 `render` → `ranked_actions_ranked_bars.png` | §6.3: "순위·효과 값이 result.ranked 와 같다" | `result.ranked[8]`(9위, `delta_dim="end_balance_median"`, `delta=141,600`원)의 viz `effect` 값이 `14,160,000`(unit `"%"`)으로 나와 1위(`effect=5,510,000`)보다 훨씬 큰 막대로 그려짐 — 확률 델타가 아닌 KRW 델타까지 ×100 배 하면서 unit 을 "%"로 고정한 것이 원인 | P1(계약 위반/오도) | `fdt/tools/render.py`(및 `result.ranked[].effect` 스케일링 로직) |
| QA-107 | `delta_bars` 가 확률(0~1)과 KRW(수백만) 델타를 같은 선형 축에 그려 확률 막대가 사실상 보이지 않음 | `run --engine B --mode WHATIF ...` 후 `render` → `whatif_delta_delta_bars.png` | §6.3: 델타 항목들이 알아볼 수 있게 표시 | `부족 확률` 델타(+0.21)가 `말일 잔액`(-150,000~+1,200,000 스케일)과 같은 축(1e6 단위)에 그려져 막대 길이가 0에 가까워 육안으로 안 보임(caption 텍스트 "+21%d" 는 맞지만 그래프가 이를 반영 못함) | P1(필수 viz 무력화) | `fdt/tools/render.py` |
| QA-108 | FORECAST `events[]` 가 committed queue 와 무관하게 거의 매일 CARD_BILL/INCOME 을 나열함(C_impulsive) | `run --engine C --mode FORECAST --horizon 30` 후 `result.events` 확인. 대조: `data/engines/C.engine.json` 의 `state.committed`(빌드 시점 큐) | §5.4 약정 큐: 근접 30일 내 CARD_BILL 은 1건(2026-09-10), TELECOM 3건뿐. §11: C 프로필 수입은 "월 2~4회"(`inspect` 출력도 평균간격=11일) | `result.events` 에 CARD_BILL 이 2026-09-10부터 10-07까지 **거의 매일**(금액이 102,100→235,100→…→440,900 로 계속 변함) 나열되고, INCOME 도 09-13부터 매일 나열됨 — 월 2~4회 불규칙 수입 프로필의 이벤트 타임라인으로는 비현실적이며, 필수 viz(`event_timeline`)를 사실상 무의미하게 만든다 | P1(계약/일관성 위반) | FORECAST 이벤트 집계(`fdt/engine/simulate.py` 추정) |

## 4. viz 육안 검수 (`fdt render`, 4 프로필 × 5 모드, 47 PNG)

산출 위치: `data/out/render/<A|B|C|D>_<forecast|risk|whatif|goal|optimize>/`.

- **line_band**(FORECAST/WHATIF/GOAL): 밴드가 중앙값을 감싼다(확인, A/C 모두). 최저점 annotation 이 facts 의 `min_point`/`min_balance` 값과 일치(A: "최저점 4,828,550원" = JSON `min_point.median_balance`). WHATIF 는 "기준"/"분기" 2 시리즈가 색으로 구분됨(확인). GOAL 의 line_band(`goal_cap_trajectory`)는 잔액이 아니라 누적 지출 상한 대비 총 재량 지출 한도 hline 을 그리는 방식으로 구현돼 있음 — SPEC 이 "목표선 hline" 의 구체적 지표를 못박지 않아 결함으로 보지 않음.
- **event_timeline**(FORECAST/RISK): 이벤트가 많을 때(A, 10건 안팎) 라벨이 겹쳐 읽을 수 없음(QA-104), C 처럼 이벤트가 적을 때는 문제없이 표시됨. fail_prob 은 색 농도로 표시되어 높은 이벤트가 눈에 띔(확인, C_risk 에서 진한 원=고위험 확인).
- **gauge**(RISK/GOAL): 임계값 20/50 이 호(arc) 위 빨간 눈금 두 개로 표시됨(확인). level 텍스트가 facts/level 과 일치(A_risk "0 (SAFE)", A_goal "100 (SAFE)").
- **progress_bars**(FORECAST): 현재 사용률(막대)과 예상(projected, 세로선 마커)이 구분되어 표시됨. C_impulsive 는 다수 봉투의 projected 마커가 1.0(100%) 선을 훌쩍 넘겨 표시됨(확인, 정상).
- **step_bars**(GOAL): 주차별 스택 합이 total 선과 일치(QA-10 에서 17주 전수 확인).
- **ranked_bars**(OPTIMIZE): 순위 순서와 막대 길이가 일치하지 않는 경우 발견 — QA-106(P1).
- **delta_bars**(WHATIF/OPTIMIZE): 서로 다른 단위(확률/KRW)를 같은 축에 그려 확률 막대가 사실상 보이지 않는 경우 발견 — QA-107(P1).
- **table**(RISK): 열 순서·내용은 맞지만 단위 표기 누락 — QA-103(P2).
- **공통**: 확인한 모든 PNG 에서 한글 텍스트 깨짐(글리프 누락/네모 박스)은 없었다. caption 의 숫자는 (QA-105 문법 오류를 제외하면) facts 표기 중 하나와 일치했다.

## 5. SPEC 대조 감사 (§3.3, §8.1~8.6, §9.4, §12)

### §3.3 입력 검증

- [x] `as_of` 이후 거래 → `W-INPUT-FUTURE_TX`(무시): QA-02c 확인
- [x] 봉투/세분류 taxonomy 불일치 → `E-INPUT-TAXONOMY`: 별도 오염 입력(`envelopes` 1개 삭제)으로 확인 — `E-INPUT-TAXONOMY` 발생 확인
- [x] 카드 `withdrawal_account_id` 참조 없음 → `E-INPUT-REF`: QA-02a 확인
- [x] 배열 id 중복(내용 다름) → `E-INPUT-DUP`: QA-02b 확인
- [x] 계좌 대사 불일치 → `W-RECON`(기본)/`E-RECON`(`--strict`): 별도 오염 입력(계좌 balance 를 999,999원 어긋나게 편집)으로 양쪽 다 확인(`build` 기본 실행 시 경고, `--strict` 시 `{"code":"E-RECON",...}`)
- [x] `is_managed` 계좌 0개 → `E-INPUT-EMPTY`: 별도 오염 입력(모든 계좌 `is_managed=false`)으로 확인
- [x] 거래 이력 <28일 → `W-INPUT-SHORT_HISTORY`: QA-03 확인

### §8.1 공통 요청

- [x] 모드는 요청자가 명시(`--mode` 필수, CLI 가 추론하지 않음): `--help` 로 확인(옵션에 `*` 필수 표시)
- [x] 필수 파라미터 누락 → `E-REQ-MISSING`: QA-18(a) 확인
- [x] 범위 밖 → `E-REQ-RANGE`: QA-18(b) 확인
- [x] 동시 다중 실패 → `error.details.errors[]` 전부 보고: QA-18(c)(horizon+n_paths 동시 위반) 확인

### §8.2 FORECAST

- [x] `trajectory`(dates/median/p10/p90/mean), `min_point`, `end_point`, `envelopes[]`, `events[]`, `shortfall_prob`, `card_shortfall_prob` 필드 전부 존재(A/B/C/D 확인)
- [x] 금액은 정수 원(반올림): `min_point`/`end_point` 값 전부 정수 확인
- [ ] `events[]` 가 committed queue 를 정확히 반영 — **QA-108 로 불일치 확인(C 프로필)**

### §8.3 WHATIF

- [x] `base`/`branch`(trajectory·min/end·shortfall_prob·card_shortfall_prob), `delta`, `verdict`, `branch_level`, `crn` 필드 존재(QA-07/08/09 확인)
- [x] `verdict` 판정식(S52): QA-07 에서 "기준 최저≥0, 분기 최저<0 → DANGER" 규칙 일치 확인
- [x] CRN 불변식(주입≥0 → 분기 최저≤기준, 확률 비감소): QA-07 확인(base 24,150 ≥ branch -125,850)
- [ ] Injection 필드명 `from` — **QA-102 로 `from_` 오기 확인**

### §8.4 GOAL

- [x] `feasible`, `achieve_prob`, `achieve_prob_ci`, `gap`, `required`, `weekly_caps`, `plan_achieve_prob`, `notes` 필드 존재
- [x] 주차 상한 합 상한 규칙(S55, 하드캡): QA-10/11 에서 필수 봉투 하한 유지 확인
- [x] step_bars 스택 합==total: QA-10 확인(17주 전수)

### §8.5 RISK

- [x] `risk_score`, `level`, `shortfall_prob`, `card_shortfall_prob`, `worst_day`, `expected_shortfall`, `payment_risks[]`, `alerts[]`, `safe_to_spend_today`, `health` 필드 존재
- [x] `risk_score` 계산식(`round(100×max(card_shortfall_prob, 0.6×shortfall_prob))`, 문턱 20/50): QA-05 에서 `13=round(100×0.134)` 일치 확인
- [x] `CONCERNING_TX`/`ACCELERATION` 판정: QA-06 확인
- [x] Safe-to-Spend ≥0, 100원 단위 절사: QA-05(26,000), QA-06 케이스에서 양수·100원 단위 확인

### §8.6 OPTIMIZE

- [x] `objective`, `baseline`, `ranked[]`, `recommended`, `evaluated`, `sim_calls`, `n_paths_used`, `notes` 필드 존재
- [x] `sim_calls ≤ 40`: QA-12(28), QA-13 에서 확인
- [x] S56 사전식 순위(1차 항 포화 시 2~4차 항으로 결정): D 는 baseline 이 이미 SAFE(shortfall_prob=0)라 전 순위가 `end_balance_median`/`min_economic_balance_median` 델타로 갈리는 것을 확인(QA-12/QA-106 데이터)
- [ ] `AppliedAction.override` 필드명 `new_weekday` — **QA-101 로 `weekday` 오기 확인**

### §9.4 모드별 필수 facts·viz

- [x] FORECAST: `end_balance_median`, `min_balance_median`, `min_balance_date`, `shortfall_prob` 존재(facts 확인), `line_band`/`progress_bars`/`event_timeline` priority=1 존재(A/B/C/D `render` 성공)
- [x] WHATIF: `delta_min_balance`, `delta_shortfall_prob`, `verdict`, `branch_min_balance_date` 상당 facts 존재, `line_band`(2 시리즈)/`delta_bars` 존재(단 QA-107 로 delta_bars 가독성 문제)
- [x] GOAL: `feasible`, `achieve_prob`, `gap_median`, `reduction_ratio`, `plan_achieve_prob` facts 존재, `gauge`/`step_bars`/`line_band` 존재
- [x] RISK: `risk_score`, `level`, `worst_day`, `expected_shortfall`, `safe_to_spend_today` facts 존재, `gauge`/`table`/`event_timeline` 존재(단 QA-103/104 문제)
- [x] OPTIMIZE: 1위 행동 라벨·효과·델타, `baseline_shortfall_prob` facts 존재, `ranked_bars`/`delta_bars` 존재(단 QA-106/107 문제)

### §12 성능·품질 기준

- [x] `build_engine`<1.0s, `simulate`<1.5s, WHATIF<3s, GOAL<4s, OPTIMIZE<25s: `docs/EVAL_REPORT.md` 수치(전부 기준의 1/10 이하) + 본 세션 재확인(§2 QA-20) 일치
- [x] 재현성(바이트 동일, elapsed_ms 제외): QA-14/16 확인
- [ ] 백테스트 sMAPE — **`docs/EVAL_REPORT.md` 에 이미 FAIL 로 기록**: A(0.0176) PASS, B(0.0935) FAIL(기준 0.25, 4/5 시드 통과했으나 평균은 기준 내여도 리포트가 seed5 초과로 FAIL 판정), C(0.5301) FAIL(기준 0.40), D(0.0119) PASS — 본 QA 는 이 판정을 그대로 인용하며 새 QA-ID 를 채번하지 않음(소유: L1/EVAL)
- [ ] P10~P90 커버리지 0.6~0.95 — **전 프로필 FAIL 로 이미 기록**(EVAL_REPORT, 시드별 3~4/5 통과)
- [x] 리스크 캘리브레이션 ECE≤0.15, Brier<기준율: `card_shortfall_prob` ECE 0.0243, `shortfall_prob` ECE 0.0311 — PASS(EVAL_REPORT)
- [x] 단조성: 128건 중 위반 2건(1.56%, 전부 C, 부동소수 반올림 경계로 추정) — EVAL_REPORT 판정을 인용, 사실상 PASS 로 간주할 수 있는 수준

## 6. 결론

- **미해결 P0: 없음.** 계산 오류나 재현성 붕괴로 분류할 결함은 발견하지 못했다(QA-16 에서 발견한 불일치는 동시 편집으로 인한 것으로 원인을 특정했고, 동일 코드 시점 재현 시 완전한 결정성을 확인했다).
- **미해결 P1: 6건**(QA-101, 102, 104, 106, 107, 108). 이 중 QA-101/102 는 OPTIMIZE·WHATIF 결과의 필드명이 SPEC 문자열과 달라 SPEC 을 그대로 신뢰하는 하위 소비자(에이전트 프롬프트 빌더 등)가 파싱에 실패할 수 있는 계약 위반이며, QA-104/106/107 은 `fdt/tools/render.py`(viz, §10 "개발·QA 전용" 명시)의 문제라 엔진 코어에는 영향이 없지만 §6.3 육안 검수 자체가 요구하는 "필수 viz 의 가독성"을 훼손한다. QA-108 은 FORECAST 의 필수 viz(`event_timeline`)가 불규칙 수입 프로필(C)에서 사실상 무의미해지는 문제로, RISK/GOAL 발화 품질에도 영향을 줄 수 있다.
- **미해결 P2: 2건**(QA-103, 105). 단위 표기 누락과 "…원다." 문법 오류로, 기능에는 영향이 없으나 최종 사용자 대면 시 신뢰도를 낮춘다.
- §12 의 sMAPE/커버리지 FAIL 은 이미 `docs/EVAL_REPORT.md` 에 원인 분석과 함께 기록돼 있으므로 이 리포트에서 중복 결함으로 채번하지 않았다. 다만 v0.1 태그 조건(PLAN §12) 판단 시 EVAL_REPORT 의 미해결 FAIL 과 본 리포트의 P1 6건을 함께 고려해야 한다.
