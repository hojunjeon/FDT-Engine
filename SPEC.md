# FDT 엔진 명세 (SPEC) v0.1

- 상태: 초안 (2026-09-07). 구현은 이 문서를 단일 기준으로 삼고, 변경은 이 문서를 먼저 고친다.
- 범위: **엔진만**. 자연어 라우팅(에이전트), 코칭 문장 생성, 대시보드, 이체 실행은 전부 범위 밖이다.
- 상위 문서: `../../00_특화PJT_기획/07_FINAL/01_KeyFin_기획의도.md`, `02_KeyFin_요구사항명세.md`, `FDT.md`, ERD `ERD_v1.1`(erdcloud RvbfSXjYXdjM8RdjK), 금융망 API 문서 `docs/금융_api/`.
- 선행 구현: `../03_Finance-Digital-Twin` 의 트윈 코어 공식(설계서 §7)을 계승한다. 계승·변경 내역은 §13에 적는다.
- 표기: MUST 는 위반 시 반려, SHOULD 는 사유를 적으면 예외 가능.

---

## 0. 한 페이지 요약

**입력** 더미(또는 LIVE) 금융 데이터 JSON 한 묶음을 넣으면
**엔진** 이 State(t) + Behavior + Transition + Uncertainty + Externals 로 조립되고,
**모드** 5개(FORECAST / WHATIF / GOAL / RISK / OPTIMIZE) 중 하나를 요청 JSON 으로 골라 실행하면
**출력** 으로 수치 결과 + 발화용 사실 목록(facts) + 시각화 명세(viz) 가 담긴 정형 JSON 이 나온다.

```
TwinInput(JSON) ──build_engine()──▶ Engine ──run(ModeRequest)──▶ EngineResult(JSON)
                                    │                              ├ result   : 모드별 수치
   State(t)  Behavior  Transition   │                              ├ facts    : 단위 붙은 키-값 사실
   Uncertainty  Externals           │                              ├ viz      : 차트/표 명세 (렌더러 독립)
                                    │                              └ meta     : engine_id, seed, 소요시간
                                    └ save()/load() : 엔진 스냅샷 JSON
```

핵심 원칙 네 가지. (1) 숫자는 엔진만 만든다. LLM 의존성은 0이다. (2) 같은 입력·같은 시드는 바이트 단위로 같은 출력을 낸다. (3) 다섯 모드는 **하나의 시뮬레이터**를 다르게 호출하는 것이다. (4) 출력은 렌더러를 모르는 명세다. 차트 라이브러리 이름이 출력에 나오면 반려.

---

## 1. 범위와 비범위

### 1.1 범위

| ID | 이름 | 산출물 |
| --- | --- | --- |
| ENG-BUILD | 엔진 생성 | `TwinInput` JSON → `Engine`. 검증·대사·State/Behavior 추정 포함 |
| ENG-SAVE | 엔진 스냅샷 | `Engine.save()` / `Engine.load()` JSON. 재현성 보장 |
| ENG-GEN | 더미 데이터 생성기 | 프로필 YAML + 시드 → `TwinInput` + `ground_truth` |
| MODE-FORECAST | 미래 상태 예측 | 일별 잔액 궤적(중앙값·P10·P90), 봉투 궤적, 약정 이벤트 타임라인 |
| MODE-WHATIF | What-if 분기 | 기준 vs 분기 궤적, 델타, 판정 |
| MODE-GOAL | 목표 실현 가능성 | 달성 확률, 부족액, 주차별·봉투별 지출 상한 |
| MODE-RISK | 리스크 분석 | 결제일별 부족 확률, 위험 점수, 우려 결제·가속도 알림 |
| MODE-OPTIMIZE | 최적 행동 탐색 | 행동 후보별 기대 효과, 순위, 권장 조합 |
| OUT-FACTS | 발화용 사실 | 모든 모드 공통. 단위·정밀도·허용 표기 집합 포함 |
| OUT-VIZ | 시각화 명세 | 모든 모드 공통. §9 어휘 8종 |
| CLI | 테스트용 실행기 | `fdt build / run / gen / inspect / render` |

### 1.2 비범위 (결정)

- 자연어 → 모드 라우팅, 파라미터 추출. 엔진은 `ModeRequest` JSON 만 받는다. 테스트 중 모드 선택은 사람이 CLI 플래그로 한다.
- 코칭 문장, 페르소나. 엔진은 `facts` 까지만 낸다.
- 화면 렌더링. `viz` 명세를 검수하기 위한 개발용 PNG 렌더러(`fdt render`)는 두되 `fdt/engine/` 밖에 둔다.
- 이체·결제 실행, 금융망 쓰기 API 호출 전부.
- 가맹점 분류 모델. 입력은 이미 `subcategory_id` 가 붙어 들어온다고 가정한다(KeyFin 원장이 담당). 미분류 거래는 봉투 `기타` 로 본다.
- 정책·상품 추천, 방/캐릭터 매핑(INT-02). 후자는 `facts` 의 `health_level` 로 대체 가능하다.

---

## 2. 용어

| 용어 | 뜻 |
| --- | --- |
| as_of | 엔진 기준일. 이 날짜(포함) 이전 거래만 State/Behavior 에 쓴다 |
| 봉투 (envelope) | 7대 소비 예산 카테고리. 고정비·수입·카드대금·내계좌이체는 봉투가 아니다 |
| 흐름 (flow) | 거래 성격: INCOME / FIXED / CARD_BILL / TRANSFER_INTERNAL / REFUND / SPEND |
| 약정 큐 (committed queue) | as_of 이후 나갈 확정·준확정 지출 목록. 카드 청구 예정액 포함 |
| 경로 (path) | 시뮬레이션 1회가 만든 일별 상태 시계열. `n_paths` 개 |
| 공통 난수 (CRN) | 기준·분기 시뮬레이션에 같은 시드를 써서 차이가 잡음이 아니라 개입 효과만 반영되게 함 |
| 경제 잔액 (economic balance) | 실제 잔액 − 카드 미결제 부채 − 거절된 의무. 비교·리스크 판정에 쓴다 |
| 사실 (fact) | 에이전트가 문장에 넣을 수 있는 하나의 수치. 키·값·단위·표기 허용 집합을 가진다 |

---

## 3. 입력 계약 `TwinInput`

### 3.1 설계 결정

- **ERD 정렬.** KeyFin DB 테이블(transactions, accounts, cards, card_billings, fixed_expenses, budgets, budget_envelopes, envelopes, subcategories, user_profiles)을 그대로 JSON 배열로 옮긴 형태를 1급 입력으로 한다. 서비스 연동 시 DB → JSON 덤프만 하면 된다.
- 금융망 원본 응답 형식(`FinSnapshot`)은 어댑터 `adapters/finapi.py` 가 `TwinInput` 으로 변환한다. 엔진 코어는 `TwinInput` 만 안다.
- 금액은 정수 원(`int`). 날짜는 `YYYY-MM-DD`, 시각은 `HH:MM:SS`. 숫자를 문자열로 받지 않는다(금융망 어댑터에서 변환).
- 모든 배열은 `id` 유일. 같은 id·다른 내용은 오류(조용히 덮어쓰지 않는다).

### 3.2 스키마 (pydantic v2, `fdt/engine/schemas/input.py`)

```jsonc
{
  "schema_version": "twin-input/1",
  "as_of": "2026-09-07",                      // 필수. 이 날짜까지의 데이터만 본다
  "user": {                                    // users + user_profiles
    "id": 1, "employment_status": "EMPLOYED", "income_band": null, "birth_date": null
  },
  "envelopes":     [{"id":1,"name":"외식"}, ...],                     // 7종 고정
  "subcategories": [{"id":1,"envelope_id":1,"name":"음식점"}, ...],   // 22종
  "accounts": [{
    "id": 10, "fin_account_no": "0011234567890123", "bank_code": "001",
    "alias": "월급통장", "is_managed": true, "is_income": true,
    "balance": 1830000,                        // as_of 시점 잔액 (필수)
    "opening_balance": null                    // 선택. 없으면 balance − Σ거래 로 역산
  }],
  "cards": [{
    "id": 20, "issuer_code": "1001", "card_name": "KB 체크", "kind": "CREDIT",   // CREDIT | DEBIT
    "withdrawal_account_id": 10, "withdrawal_weekday": 1,                    // 0=월 … 6=일 (금융망 1~7 은 어댑터가 변환)
    "is_managed": true
  }],
  "card_billings": [{
    "id": 30, "card_id": 20, "billing_date": "2026-09-01", "total_amount": 183500,
    "status": "UNPAID", "paid_at": null
  }],
  "fixed_expenses": [{
    "id": 40, "name": "월세", "expense_type": "RENT",   // RENT|SUBSCRIPTION|CARD_BILL|LOAN|UTILITY|INSURANCE|TELECOM
    "amount": 700000, "is_variable": false, "payment_day": 25,
    "withdrawal_account_id": 10, "card_id": null,      // 카드 결제형 고정비면 card_id
    "active": true
  }],
  "loans": [{                                         // 선택. 금융망 대출 API 대응
    "id": 50, "balance": 12000000, "annual_rate_pct": 6.8, "interest_day": 15,
    "withdrawal_account_id": 10, "repayment": "INTEREST_ONLY"   // INTEREST_ONLY | AMORTIZING(원리금균등)
  }],
  "budgets": [{                                       // budgets + budget_envelopes (선택. 없으면 엔진이 제안)
    "budget_month": "202609", "status": "CONFIRMED",
    "envelopes": [{"envelope_id":1,"proposed_amount":350000,"confirmed_amount":300000}, ...]
  }],
  "transactions": [{
    "id": 1001, "source": "SEED",                     // SEED | LIVE
    "tx_type": "CARD",                                // CARD | DEPOSIT | WITHDRAW | TRANSFER
    "account_id": 10, "card_id": 20, "merchant_id": 7, "merchant_name_raw": "스타벅스",
    "amount": 5600,                                   // 항상 양수. 방향은 tx_type + flow 로 결정
    "tx_date": "2026-09-06", "tx_time": "13:20:00",
    "subcategory_id": 2,                              // null 이면 기타 처리
    "confirm_status": "AUTO",                         // AUTO | PENDING | CONFIRMED
    "exclude_tag": "NONE",                            // NONE | DUTCH | SELF_TRANSFER | EMERGENCY | CARRYOVER
    "status": "NORMAL",                               // NORMAL | CANCELED
    "flow_hint": null,                                // 선택. INCOME|FIXED|CARD_BILL|TRANSFER_INTERNAL|REFUND|SPEND. 없으면 엔진이 판정(§5.2)
    "counterparty_account_id": null                   // TRANSFER 일 때 상대 계좌가 내 계좌면 id
  }],
  "externals": {                                      // 선택. 외부 변수 기본값
    "price_index_mult": 1.0,                          // 소비 금액 배수 (물가)
    "loan_rate_delta_bp": 0,                          // 대출 금리 가감(bp)
    "income_growth_pct": 0.0                          // 수입 성장률 (연)
  }
}
```

### 3.3 입력 검증 (MUST, `build_engine` 첫 단계)

| 검사 | 실패 시 |
| --- | --- |
| `as_of` 이후 날짜의 거래 존재 | 경고 `W-INPUT-FUTURE_TX` 후 **무시**(홀드아웃 평가를 위해 허용) |
| 봉투 7종·세분류→봉투 매핑 누락 | 오류 `E-INPUT-TAXONOMY` |
| 카드의 `withdrawal_account_id` 가 accounts 에 없음 | 오류 `E-INPUT-REF` |
| 거래 id 중복(다른 내용) | 오류 `E-INPUT-DUP` |
| 계좌 대사: `opening_balance + Σ부호거래 ≠ balance` | 경고 `W-RECON` 와 차액. `strict=true` 면 오류 |
| 관리 대상(`is_managed`) 계좌·카드 0개 | 오류 `E-INPUT-EMPTY` |
| 거래 이력 < 28일 | 경고 `W-INPUT-SHORT_HISTORY`, Behavior 는 기본값 비중 증가 |

---

## 4. 엔진 객체 `Engine`

### 4.1 구성

```
Engine
├ meta        : engine_id(입력 해시 12자), built_at, as_of, schema_version, warnings[]
├ ledger      : LedgerTx[]  (정규화·분류된 불변 원장)
├ state       : State(t)             §5
├ behavior    : Behavior             §6
├ externals   : Externals            §3.2
└ run(req: ModeRequest) -> EngineResult   §7~§9
```

- `build_engine(twin_input, *, budgets_override=None, strict=False) -> Engine`
- `Engine.save(path)` : ledger·state·behavior·externals·meta 를 JSON 으로. `Engine.load(path)` 는 재계산 없이 복원. `engine_id` 가 다르면 로드 거부.
- `Engine.fork()` : What-if 용 얕은 복제. 원장은 공유(불변), state 만 복사.
- 엔진은 **as_of 를 바꾸지 않는다**. 다른 기준일은 새 엔진이다(홀드아웃 누수 방지).

### 4.2 불변 원칙 (MUST)

1. `fdt/engine/**` 는 `openai`, `anthropic`, `ollama`, `requests`, `httpx` 를 import 하지 않는다. 테스트 `test_architecture.py` 가 검사한다.
2. 난수는 `numpy.random.default_rng(seed)` 만. `random`, `hash()`, `time` 기반 시드 금지.
3. 금액 연산은 정수. 확률·비율·로그정규 파라미터만 float.
4. `ledger` 는 생성 후 변경 불가(`tuple` 또는 frozen dataclass).
5. 다섯 모드는 모두 `simulate()` 하나를 호출한다. 모드별로 별도 전이 규칙을 두지 않는다.
6. 출력 JSON 에 차트 라이브러리·색상 코드·픽셀 값이 들어가지 않는다.

---

## 5. State(t)

### 5.1 정의 (`schemas/state.py`)

```jsonc
{
  "as_of": "2026-09-07",
  "accounts": [{"id":10,"role":"PRIMARY","balance":1830000}, {"id":11,"role":"EMERGENCY","balance":350000}],
  "liquidity": 1830000,            // PRIMARY 잔액
  "emergency_fund": 350000,        // EMERGENCY 합. 시뮬레이션이 자동 사용하지 않는다
  "cards": [{
    "id":20, "withdrawal_weekday":1, "unbilled":92300,        // 이번 청구 주기 누적(승인−취소)
    "issued_unpaid":[{"billing_date":"2026-09-01","amount":183500}]
  }],
  "committed": [{                  // 약정 큐, as_of+1 ~ as_of+horizon_cap(90)
    "kind":"RENT","name":"월세","due":"2026-09-25","amount":700000,"certainty":1.0,"account_id":10,"card_id":null
  }],
  "envelopes": [{
    "envelope_id":1,"name":"외식","budget":300000,"spent":212400,"remaining":87600,"budget_source":"CONFIRMED"   // CONFIRMED|PROPOSED|ENGINE
  }],
  "income": {"next_date":"2026-09-25","expected":2870000,"irregular":false,"median_gap_days":30},
  "indicators": {"spend_7d_avg":41200,"spend_90d_avg":36800,"acceleration":1.12,"unconfirmed_count":3},
  "cycle": {"budget_cycle_start":"2026-09-01","budget_cycle_end":"2026-09-30","progress":0.233}
}
```

### 5.2 원장 정규화와 흐름 판정 (`engine/ledger.py`)

`transactions[]` → `LedgerTx(id, date, time, account_id, card_id, signed_amount, flow, envelope_id, subcategory_id, confidence, source)`.

흐름 판정 순서(`flow_hint` 가 있으면 그대로):

1. `status == CANCELED` 인 CARD 거래 → 원 승인 `SPEND(−)` 와 같은 시각 `REFUND(+)` 두 건으로 기록(이력 보존, 순액 0).
2. `exclude_tag == SELF_TRANSFER` 또는 `counterparty_account_id` 가 내 계좌 → `TRANSFER_INTERNAL` (봉투 없음).
3. 고정비 매칭: `fixed_expenses` 의 (계좌 또는 카드, 금액 ±10%, payment_day ±3일) 에 맞으면 `FIXED`. 카드대금은 `merchant_name_raw` 에 "카드대금" 또는 `fixed_expenses.expense_type == CARD_BILL` 매칭 → `CARD_BILL`.
4. `tx_type == DEPOSIT` 이고 `is_income` 계좌 → `INCOME`. 그 외 DEPOSIT 은 `REFUND`(더치페이 입금 포함, `exclude_tag == DUTCH` 면 해당 봉투에 +).
5. 나머지 CARD/WITHDRAW → `SPEND`. `subcategory_id` 로 봉투 결정. null 이면 `기타`, confidence 0.3.

원장 규칙 (NFR-BGT-01): 카드 승인은 봉투를 깎고 `CARD_BILL` 출금은 봉투를 **다시 깎지 않는다**. 봉투 순지출 = `SPEND + REFUND(봉투 있는 것)` 절대값. `exclude_tag ∈ {EMERGENCY, CARRYOVER}` 는 봉투 차감 제외.

### 5.3 계산 규칙

| 항목 | 규칙 |
| --- | --- |
| PRIMARY 계좌 | 카드 `withdrawal_account_id` 최다 참조 계좌. 카드 없으면 `is_income` 계좌. 그것도 없으면 INCOME 거래 최다 계좌 |
| EMERGENCY | PRIMARY 외 관리 계좌 합 |
| 잔액 | 입력 `balance` 를 as_of 잔액으로 신뢰. `opening_balance` 가 있으면 대사 검사(§3.3) |
| `unbilled` | 이번 청구 주기(직전 월요일 ~ as_of, as_of 가 월요일이면 당일부터) 카드 `SPEND+FIXED−REFUND` 순액 |
| `issued_unpaid` | `card_billings[status=UNPAID, billing_date ≤ as_of]`. 없고 직전 주 승인이 원장에 `CARD_BILL` 로 안 보이면 재구성 |
| 약정 큐 | §5.4 |
| 봉투 예산 | `budgets[budget_month == as_of 월]` 의 `confirmed_amount` → 없으면 `proposed_amount` → 없으면 엔진 제안(§5.5) |
| `spent` | 이번 달 1일 ~ as_of 봉투 순지출 |
| 수입 일정 | §6.6 |
| `spend_7d_avg`, `spend_90d_avg`, `acceleration` | 봉투 순지출 7일/90일 일평균, 비 = 7d / max(90d, 1000) |
| `unconfirmed_count` | 이번 달 `SPEND` 중 `confirm_status == PENDING` 건수 |

### 5.4 약정 큐 `build_committed_queue(horizon_cap=90)`

| 종류 | 근거 | 다음 예정일 | 금액 | certainty |
| --- | --- | --- | --- | --- |
| RENT/UTILITY/INSURANCE/TELECOM/SUBSCRIPTION | `fixed_expenses[active]` | `payment_day` 의 다음 발생일(말일 보정), 매월 반복 | `amount`. `is_variable` 이면 원장 최근 3회 중앙값, 없으면 0 + 경고 | 1.0 (변동형 0.8) |
| LOAN 이자 | `loans[]` | `interest_day` | `balance × (rate+delta_bp/100)/100/12`, 10원 단위. AMORTIZING 이면 원리금균등 월납 | 1.0 |
| 카드대금(미청구) | `cards.unbilled` | 다음 월요일 발행 후 첫 `withdrawal_weekday` | `unbilled` | 0.9 |
| 카드대금(미결제) | `issued_unpaid` | 다음 `withdrawal_weekday`(as_of 포함) | 청구액 | 1.0 |
| 원장 탐지 반복 고정비 | `FIXED` 거래를 (계좌/카드, 이름) 로 묶어 월 1회(간격 25~35일) 2회 이상 반복 | 마지막 발생 + 1개월 | 최근 3회 중앙값 | 0.9 |

중복 제거: `fixed_expenses` 와 원장 탐지가 같은 이름이면 `fixed_expenses` 우선. 동일 (kind, name, due) 는 하나.

### 5.5 엔진 예산 제안 `propose_budgets`

완결 월(1일~말일 모두 as_of 이전) 봉투 순지출 → 3개월 이상 중앙값, 1~2개월 평균, 0개월은 최근 28일 × 30/28. 만원 단위 올림, 하한 10,000원. `budget_source = "ENGINE"`.

---

## 6. Behavior (행동 모델)

윈도우 `[as_of − 89, as_of]`(90일, 최소 28일). `SPEND` 만 사용, 같은 날·같은 카드·같은 금액의 승인+취소 쌍은 제거.

| 파라미터 | 추정 | 클립·기본값 |
| --- | --- | --- |
| `daily_rate[e]` | 봉투 e 건수 / 윈도우 일수 | |
| `weekday_mult[e][w]` | `(c_w + 2) / (E_w + 2)` 후 평균 1 정규화 | `n_e < 10` 이면 전부 1.0 |
| `amount_mu[e], amount_sigma[e]` | 로그정규 MLE | sigma [0.2, 1.5]. `n_e < 5` 면 전 봉투 통합, 통합도 5 미만이면 `mu=ln 10000, sigma=0.6` |
| `card_share[e]` | 카드 건수 / 건수 | `n_e=0` 이면 전체 비율, 그것도 0이면 0.5 |
| `payday_boost` | 수입 후 7일 일평균 / 그 외 일평균 | [0.7, 2.0]. 표본 14일 미만이면 1.0 |
| `elasticity[e]` | 봉투 잔여율 < 0.2 인 날 일평균 / 그 외 | [0.5, 2.0]. 저잔여일 5일 미만이면 1.0 |
| `shock_daily_prob, shock_mu, shock_sigma` | `금액 ≥ max(50,000, 5·exp(mu_e))` 건 | 0건이면 `0.01, ln 100000, 0.6` |
| 수입 일정 (§6.6) | INCOME 거래 일자 간격 cv ≤ 0.25 이고 day-of-month 최빈 비율 ≥ 0.6 → 규칙적. 그 외 불규칙 | 1건 이하면 `next=None, expected=0` |

Behavior 는 **원장만** 읽는다. 생성기의 프로필 YAML·`ground_truth` 를 읽으면 반려(순환 검증 금지).

---

## 7. Transition + Uncertainty (시뮬레이터)

### 7.1 시그니처

```python
simulate(state, behavior, externals, *, horizon_days=30, n_paths=1000, seed=42,
         injections=(), overrides=None) -> SimulationResult
```

- `injections`: What-if 가상 이벤트 목록(§8.2 표).
- `overrides`: 시뮬 기간 동안만 적용하는 상태 변경(예산 변경, 고정비 중단, 외부 변수 변경). 원본 `state` 는 건드리지 않는다.
- 결과 배열 shape `(n_paths, horizon_days+1)`. `dates[0] = as_of`(기록값은 as_of 잔액).

### 7.2 하루 처리 순서 (MUST, 생성기와 동일)

```
1 수입      d == next_income → liquidity += expected × (1+income_growth)^(년). 불규칙이면 금액에 LogNormal(0, 0.4) 잡음, 다음일 = d + median_gap
2 고정비    큐 due == d. 계좌형: cash ≥ amount 면 차감, 부족하면 당일 거절 → unpaid_obligation 누적(재시도 없음). 카드형: card.unbilled += amount
3 청구 발행 d.weekday()==0 → 카드별 issued.append(unbilled); unbilled = 0
4 카드 출금 d.weekday()==withdrawal_weekday 또는 미결제 청구서가 있는 날(매일 재시도) → 오래된 것부터, cash ≥ total 이면 차감·제거, 부족하면 card_shortfall[p]=True, 청구서 유지
5 소비      봉투별 λ = daily_rate × weekday_mult[wd] × boost × elasticity_gate × 1(price_index 는 금액에)
            n ~ Poisson(λ); 금액 ~ LogNormal(mu, sigma) × price_index_mult, 100원 반올림
            card_share 만큼 unbilled 로, 나머지는 cash ≥ amount 일 때 즉시 차감, 부족하면 suppressed_demand 누적
            envelope_spend[p,e] += Σ. 달이 바뀌면 spent 리셋
6 돌발      Bernoulli(shock_daily_prob) → LogNormal(shock_mu, shock_sigma). 봉투 기타. 카드 비율은 전체 평균
7 주입      injections 중 on == d → 5와 같은 방식. (수입 주입은 1과 같은 방식)
8 기록      balances[p,k] = liquidity
            economic[p,k] = liquidity − Σissued_unpaid − unpaid_obligation − suppressed_demand
            liquidity < 0 → any_shortfall[p]; 처음이면 first_shortfall_idx[p]=k
            결제 이벤트가 있던 날은 event_log[k] 에 (kind, amount, 성공 경로 비율) 기록
```

벡터화: 경로 축을 numpy 배열로 동시에 진행. 포아송은 `rng.poisson(λ, n_paths)`, 금액은 총 건수만큼 한 번에 뽑아 `np.add.reduceat`.

### 7.3 `SimulationResult`

```python
dates: list[date]; balances, economic, envelope_spend: ndarray
any_shortfall, card_shortfall: bool[n_paths]; first_shortfall_idx: int[n_paths]
event_log: list[DayEvents]
def stats(economic=False) -> PathStats  # median/p10/p90/mean by day, min_balance, min_balance_date,
                                        # shortfall_prob, card_shortfall_prob, first_shortfall_date_median,
                                        # end_balance_median, envelope_spend_median[e]
def payment_risks() -> list[PaymentRisk]  # 약정 이벤트별 (due, kind, name, amount, fail_prob, median_balance_before)
```

---

## 8. 모드 계약

### 8.1 공통 요청 `ModeRequest`

```jsonc
{
  "schema_version": "mode-request/1",
  "mode": "FORECAST",                     // FORECAST | WHATIF | GOAL | RISK | OPTIMIZE
  "horizon_days": 30,                     // 1~365. 기본 30
  "n_paths": 1000,                        // 100~10000. 기본 1000. 테스트는 200
  "seed": 42,
  "params": { ... }                       // 모드별 §8.2~8.6
}
```

- 모드 선택은 **요청자가 명시**한다. 엔진은 추론하지 않는다. 테스트 시 CLI `--mode` 로 지정한다(§10).
- 필수 파라미터 누락은 `E-REQ-MISSING`, 범위 밖은 `E-REQ-RANGE`. 0 이나 기본값으로 조용히 바꾸지 않는다.
- 금액 파라미터는 0 ~ 1,000,000,000,000 정수 원.

### 8.2 FORECAST (미래 상태 예측)

`params`: `{ "include_envelopes": true, "include_events": true }`

`result`:
```jsonc
{
  "trajectory": {"dates":[...], "median":[...], "p10":[...], "p90":[...], "mean":[...]},
  "economic":   {"median":[...], "p10":[...], "p90":[...]},
  "min_point":  {"date":"2026-09-24","median_balance":118000,"p10_balance":-64000},
  "end_point":  {"date":"2026-10-07","median_balance":2013000},
  "envelopes":  [{"envelope_id":1,"name":"외식","budget":300000,"spent_now":212400,
                  "projected_month_end_median":338000,"exhaust_date_median":"2026-09-21","overrun_prob":0.71}],
  "events":     [{"date":"2026-09-09","kind":"CARD_BILL","name":"KB 체크","amount":183500,"fail_prob":0.02},
                 {"date":"2026-09-25","kind":"INCOME","name":"급여","amount":2870000,"fail_prob":0.0}],
  "shortfall_prob": 0.09, "card_shortfall_prob": 0.04
}
```

### 8.3 WHATIF (분기 생성)

`params.injections[]` (1개 이상):

| type | 필드 | 의미 |
| --- | --- | --- |
| `SPEND` | `on`(날짜 또는 `days_from_now`), `amount`, `envelope_id`, `method`(CARD/CASH) | 단건 지출 |
| `INCOME` | `on`, `amount` | 단건 수입 |
| `RECURRING_SPEND` | `start`, `every_days` 또는 `day_of_month`, `amount`, `envelope_id`, `method`, `until?` | 구독 추가 등 |
| `FIXED_CHANGE` | `fixed_expense_id`, `new_amount` 또는 `cancel: true`, `from` | 고정비 변경·해지 |
| `BUDGET_CHANGE` | `envelope_id`, `new_budget`, `behavior_follows`(bool, 기본 true) | 예산 변경. true 면 elasticity_gate 기준이 함께 바뀜 |
| `EXTERNAL` | `price_index_mult?`, `loan_rate_delta_bp?`, `income_growth_pct?` | 외부 변수 시나리오 |
| `EMERGENCY_DRAW` | `on`, `amount` | 비상금 → PRIMARY 이체 |

`result`:
```jsonc
{
  "base":   { FORECAST.result 축약: trajectory.median/p10/p90, min_point, end_point, shortfall_prob, card_shortfall_prob },
  "branch": { 동일 },
  "delta":  {"min_balance": -150000, "end_balance": -150000, "shortfall_prob": +0.11, "card_shortfall_prob": +0.06,
             "first_shortfall_date": {"base":null,"branch":"2026-09-24"},
             "envelopes":[{"envelope_id":5,"remaining_change":-150000,"overrun_prob_change":+0.42}]},
  "verdict": "CAUTION",            // OK | CAUTION | DANGER  (§8.3.1)
  "crn": true
}
```

8.3.1 판정: 분기 `card_shortfall_prob ≥ 0.5` 또는 `min_point.median_balance < 0` → DANGER. `delta.shortfall_prob ≥ 0.15` 또는 분기 최저 < 기준 최저 × 0.5 → CAUTION. 그 외 OK. 기준·분기는 같은 시드(CRN). 지출 주입 ≥ 0 이면 분기 최저 ≤ 기준 최저, 부족 확률 비감소가 **불변식**이다.

### 8.4 GOAL (목표 실현 가능성)

`params`:
```jsonc
{ "goal_type": "BALANCE",                 // BALANCE(목표일 잔액 ≥ target) | SAVE(기간 누적 저축 ≥ target) | ENVELOPE_ADHERE(이번 달 전 봉투 예산 내)
  "target_amount": 2000000, "target_date": "2026-12-31",    // ENVELOPE_ADHERE 는 둘 다 생략
  "protect_essential": true }             // 필수 봉투(교통비·의료건강·편의점마트잡화) 하한 80% 보장
```

`result`:
```jsonc
{
  "feasible": true, "achieve_prob": 0.62,          // 기준 행동 그대로일 때 경로 중 목표 도달 비율
  "gap": {"median": -180000, "p10": -640000},      // 음수 = 부족
  "required": {"total_discretionary_cap": 1920000, "reduction_ratio": 0.23, "baseline_discretionary": 2490000},
  "weekly_caps": [{"week_start":"2026-09-08","days":7,"total_cap":210000,
                   "by_envelope":[{"envelope_id":1,"cap":58000}, ...]}],
  "plan_achieve_prob": 0.88,                        // weekly_caps 를 BUDGET_CHANGE 로 주입해 재시뮬한 도달 확률
  "notes": ["불규칙 수입은 기대치의 80%만 반영"]
}
```

계산: `H = target_date − as_of`(1~365). 기준 시뮬 → `achieve_prob`. 확정 유입 `I`(규칙적 수입 확정, 불규칙 ×0.8), 확정 유출 `F`(큐 + 월 반복). `available = liquidity + I − F − target`. `available < 0` → `feasible=false`, `gap` 보고. 주차 상한 = `available × days_w / H` 를 기준선 봉투 비율로 배분, 필수 봉투 하한 보장. **상한을 실제 주입해 재시뮬**한 `plan_achieve_prob` 를 함께 낸다(계획이 통계적으로도 통하는지 확인).

### 8.5 RISK (리스크 분석)

`params`: `{ "recent_tx_ids": [] }` (우려 결제 검사 대상. 비면 as_of 당일 SPEND 전부)

`result`:
```jsonc
{
  "risk_score": 37, "level": "WARNING",            // score = round(100 × max(card_shortfall_prob, 0.6 × shortfall_prob)), <20 SAFE, <50 WARNING
  "shortfall_prob": 0.31, "card_shortfall_prob": 0.37,
  "worst_day": "2026-09-16", "expected_shortfall": 142000,        // 부족 경로 최저 경제 잔액 절대값 평균
  "payment_risks": [{"due":"2026-09-09","kind":"CARD_BILL","name":"KB 체크","amount":183500,"fail_prob":0.02,"median_balance_before":1640000},
                    {"due":"2026-09-16","kind":"CARD_BILL","name":"KB 체크","amount":175000,"fail_prob":0.35,"median_balance_before":161000},
                    {"due":"2026-09-25","kind":"RENT","name":"월세","amount":700000,"fail_prob":0.30,"median_balance_before":690000}],
  "alerts": [{"kind":"ACCELERATION","severity":"WARNING","ratio":1.42},
             {"kind":"CONCERNING_TX","severity":"DANGER","tx_id":1001,"amount":250000,"envelope_id":5,"remaining_before":200000,"threshold":100000}],
  "safe_to_spend_today": 19100,                    // §8.5.1
  "health": {"score":58,"level":"WARNING","coverage":0.61,"adherence":0.72,"risk":0.63}
}
```

8.5.1 Safe-to-Spend: `days = max(1, next_income − as_of)`(없으면 30). `committed = Σ큐 amount (as_of < due < next_income)`. `raw_daily = (liquidity − committed)/days`. `factor = 1/acceleration if acceleration > 1 else 1`. `safe_today = max(0, floor((raw_daily × factor − spent_today)/100) × 100)`.

8.5.2 우려 결제: `threshold = max(0.5 × remaining_before, 3 × budget/말일, 20,000)`. `amount ≥ threshold` → WARNING, `amount ≥ remaining_before` → DANGER. 가속도: `acceleration ≥ 1.3` 이고 `spend_7d_avg ≥ 10,000` → WARNING, `≥ 1.6` DANGER.

8.5.3 health: `cov = clip((liquidity − committed_30d)/max(spend_90d_avg × 30, 1), 0, 1)`, `adh = 1 − mean_e clip(spent_e/budget_e − progress, 0, 1)`, `rsk = 1 − card_shortfall_prob`, `score = 100(0.4cov + 0.3adh + 0.3rsk)`, ≥70 SAFE, ≥40 WARNING.

### 8.6 OPTIMIZE (최적 행동 탐색)

`params`:
```jsonc
{ "objective": "MIN_SHORTFALL_PROB",     // MIN_SHORTFALL_PROB | MAX_END_BALANCE | REACH_GOAL(goal 파라미터 동반)
  "candidates": "AUTO",                  // AUTO 이면 §8.6.1 기본 후보 생성, 또는 injections 형식의 후보 배열
  "max_actions": 3,                      // 조합 시 최대 행동 수
  "constraints": {"protect_essential": true, "max_cut_ratio": 0.5, "allow_emergency_draw": false} }
```

8.6.1 AUTO 후보 (각각 하나의 `override` 또는 `injection`):
- 유연 봉투(외식·쇼핑·취미여가·기타) 각각 −10%, −20%, −30% (`BUDGET_CHANGE`, behavior_follows)
- 활성 SUBSCRIPTION 고정비 각각 해지 (`FIXED_CHANGE cancel`)
- 비상금 이체 (허용 시, 부족액만큼 `EMERGENCY_DRAW`)
- 카드 출금 요일 변경(수입일 직후 요일) (`override.card_withdrawal_weekday`)

8.6.2 탐색: 단일 행동 전부 CRN 평가 → 목적함수 개선 상위 `k=6` 를 골라 2~`max_actions` 조합 그리디(한 봉투에 두 비율 동시 금지). 총 시뮬 횟수 ≤ 40 을 넘으면 후보를 잘라낸다.

`result`:
```jsonc
{
  "objective": "MIN_SHORTFALL_PROB",
  "baseline": {"shortfall_prob":0.31,"card_shortfall_prob":0.37,"end_balance_median":780000},
  "ranked": [{"rank":1,"actions":[{"type":"BUDGET_CHANGE","envelope_id":5,"new_budget":280000,"cut_ratio":0.3}],
              "effect":{"shortfall_prob":0.12,"delta":-0.19,"end_balance_median":1010000,"cost_of_action":"쇼핑 월 12만원 감소"},
              "feasibility_note":"이번 달 이미 사용 21만원, 남은 한도 7만원"},
             ...],
  "recommended": {"rank":1, "combined_effect":{...}},
  "evaluated": 23, "sim_calls": 24
}
```

---

## 9. 출력 계약 `EngineResult`

### 9.1 봉투 구조

```jsonc
{
  "schema_version": "engine-result/1",
  "meta": {"engine_id":"a3f9c1d2e4b5","as_of":"2026-09-07","mode":"RISK","seed":42,"n_paths":1000,
           "horizon_days":30,"elapsed_ms":812,"engine_version":"0.1.0","warnings":[]},
  "request": { ModeRequest 원문 },
  "result": { §8 모드별 },
  "facts":  [ §9.2 ],
  "viz":    [ §9.3 ],
  "status": "OK"                          // OK | ERROR. ERROR 면 result 없음, error{code,message}
}
```

### 9.2 facts (발화용 사실)

에이전트가 문장에 넣어도 되는 숫자의 **전체 집합**. 이 밖의 숫자를 문장에 쓰면 충실도 검사에서 실패해야 한다(검사 자체는 에이전트 영역).

```jsonc
{"key":"risk_score","label":"위험 점수","value":37,"unit":"점","precision":0,
 "allowed_renderings":["37","37점"],"importance":1,           // 1 높음 ~ 3 낮음
 "hint":"level=WARNING"}
{"key":"safe_to_spend_today","label":"오늘 안심 소비 한도","value":19100,"unit":"KRW","precision":-2,
 "allowed_renderings":["19,100원","1만 9천원","1.9만원","약 2만원"],"importance":1}
```

규칙: 금액은 원 단위 정수, `precision=-2` 는 100원, `-4` 는 만원 반올림 표기 허용. 확률은 `unit:"%"` 정수 또는 `unit:"prob"` 소수 둘 중 하나로 통일(모드 내 일관). 날짜는 `unit:"date"` 이고 `allowed_renderings` 에 절대 날짜와 상대 표현("17일 뒤") 둘 다 넣는다. 모드별 필수 fact 목록은 §9.4.

### 9.3 viz (시각화 명세 어휘 8종)

렌더러 독립 명세. 각 항목은 `{"kind","id","title","priority","data","encoding","annotations","caption"}`. `priority` 1은 답변에 반드시 포함, 2는 상세 보기, 3은 선택.

| kind | 용도 | data | encoding 필수 | 모드 |
| --- | --- | --- | --- | --- |
| `line_band` | 시계열 중앙값 + P10~P90 밴드 | `{x:[dates], series:[{name,y:[]}], band:{lower:[],upper:[]}}` | `x:"date", y:"KRW"` | FORECAST, WHATIF(2 시리즈), GOAL |
| `event_timeline` | 결제·수입 이벤트 점 | `{events:[{date,kind,name,amount,fail_prob}]}` | `x:"date", size:"amount", color:"fail_prob"` | FORECAST, RISK |
| `gauge` | 0~100 점수 또는 확률 | `{value, min:0, max:100, thresholds:[20,50], level}` | `unit` | RISK, GOAL(achieve_prob) |
| `progress_bars` | 봉투별 사용률 | `{items:[{name,value,max,projected?}]}` | `unit:"KRW"` | FORECAST, RISK |
| `delta_bars` | 기준 vs 분기 지표 차이 | `{items:[{name,base,branch,delta,unit}]}` | | WHATIF, OPTIMIZE |
| `step_bars` | 주차별 상한(스택: 봉투) | `{x:[week_start], stacks:[{name,y:[]}], total:[]}` | `x:"date", y:"KRW"` | GOAL |
| `ranked_bars` | 행동 후보 효과 순위 | `{items:[{rank,label,effect,unit,detail}]}` | | OPTIMIZE |
| `table` | 결제일별 위험, 이벤트 상세 | `{columns:[{key,label,unit}], rows:[...]}` | | 전 모드(상세) |

annotations: `[{"type":"point|vline|hline|range","x?":date,"y?":number,"label":"최저점 11.8만원"}]`. 수치 라벨은 반드시 `facts` 에 있는 값만 쓴다(테스트로 검사).

`caption` 은 한 문장 한국어 요약. 숫자는 facts 표기만 사용.

### 9.4 모드별 필수 facts · viz

| 모드 | 필수 facts(importance 1) | 필수 viz(priority 1) |
| --- | --- | --- |
| FORECAST | `end_balance_median`, `min_balance_median`, `min_balance_date`, `shortfall_prob`, 소진 예상 봉투 최대 2개 | `line_band`(잔액), `progress_bars`(봉투), `event_timeline` |
| WHATIF | `delta_min_balance`, `delta_shortfall_prob`, `verdict`, `branch_min_balance_date` | `line_band`(base·branch 2 시리즈), `delta_bars` |
| GOAL | `feasible`, `achieve_prob`, `gap_median`, `reduction_ratio`, `plan_achieve_prob` | `gauge`(achieve_prob), `step_bars`(주차 상한), `line_band`(목표선 hline) |
| RISK | `risk_score`, `level`, `worst_day`, `expected_shortfall`, `safe_to_spend_today`, 최고 위험 결제 1건 | `gauge`, `table`(payment_risks), `event_timeline` |
| OPTIMIZE | 1위 행동 라벨·효과·델타, `baseline_shortfall_prob` | `ranked_bars`, `delta_bars`(권장 조합) |

---

## 10. 실행 인터페이스 (테스트용 CLI)

```
fdt gen   --profile A_steady --seed 7 --months 6 --out data/seed/A_seed7/     # TwinInput + ground_truth
fdt build --input data/seed/A_seed7/twin_input.json --out data/engines/A.engine.json
fdt run   --engine data/engines/A.engine.json --mode RISK --horizon 30 --seed 42 --out out/A_risk.json
fdt run   --engine ... --mode WHATIF --params '{"injections":[{"type":"SPEND","days_from_now":3,"amount":150000,"envelope_id":5,"method":"CARD"}]}'
fdt run   --engine ... --mode GOAL   --params-file req/goal_dec.json
fdt inspect --engine ...            # State/Behavior 요약 표 출력
fdt render  --result out/A_risk.json --out out/A_risk/    # viz 명세 → PNG (개발용, matplotlib)
fdt validate --result out/A_risk.json                      # 스키마 + facts/viz 정합 검사
```

- 모드 선택은 `--mode` 필수. 라우팅 기능은 없다.
- Python API: `from fdt.engine import build_engine, ModeRequest; Engine.run(ModeRequest(...))`.
- 출력 인코딩 UTF-8 고정(`PYTHONIOENCODING=utf-8`).

---

## 11. 더미 데이터 생성기 (`fdt/gen/`)

프로필 YAML(A_steady, B_card_crunch, C_impulsive, D_goal_saver) + 시드 → `TwinInput` 과 `ground_truth.json`.

| 프로필 | 특징 | 주로 검증하는 모드 |
| --- | --- | --- |
| A_steady | 고정 급여 25일 315만, 체크카드 위주, 탄력도 0.75, 월 30만 비상금 적립 | FORECAST 기준선, RISK 가 조용히 SAFE |
| B_card_crunch | 급여 287만, 카드 2장(화·토 출금) 90%, 월세 70만·대출 1,200만 6.8% | RISK, WHATIF(카드 청구 큐 전이) |
| C_impulsive | 프리랜서 불규칙 입금 월 2~4회, 주말 배수 2.4, 탄력도 1.4, 돌발 잦음 | FORECAST 밴드 폭, OPTIMIZE |
| D_goal_saver | 급여 10일 260만, 구독 5개, 예산 확정 상태, 12월 200만 목표 | GOAL, OPTIMIZE(구독 해지 후보) |

생성 규칙은 §7.2 하루 처리 순서와 **동일**해야 한다(생성기가 시뮬레이터의 정답 분포). 생성기가 엔진에 숨기는 변수: payday_boost, pre_payday_damp, elasticity, 돌발 분포, 취소 확률, 더치페이, 잔액 부족 시 체크 거절(원장 미기록). `ground_truth.json`: `daily_balance`, `card_shortfalls[]`, `declined_debits[]`, `shocks[]`, `envelope_true_spend`, `income_events[]`, `hidden_params`. **엔진 코드는 ground_truth 를 읽지 않는다.**

시드 교란: `fdt gen --profile B --seed 1..20` 으로 캘리브레이션 표본 확보.

---

## 12. 성능·품질 기준

| 항목 | 기준 |
| --- | --- |
| `build_engine` (6개월, 거래 3천 건) | < 1.0 s |
| `simulate` 1000경로 × 30일 | < 1.5 s |
| WHATIF (2회) | < 3 s |
| GOAL (기준 + 재시뮬) | < 4 s |
| OPTIMIZE (≤ 40회, n_paths 400 으로 자동 하향) | < 25 s |
| 재현성 | 같은 입력·시드 → 결과 JSON 바이트 동일 (`elapsed_ms` 제외) |
| 백테스트 sMAPE (30일, primary 잔액) | A ≤ 0.15, B ≤ 0.25, C ≤ 0.40, D ≤ 0.20 |
| P10~P90 커버리지 | 0.6 ~ 0.95 (C 는 0.5~0.95) |
| 리스크 캘리브레이션 (23 사용자 × 7일 간격 as_of) | ECE ≤ 0.15, Brier < 기준율 Brier |
| 단조성 | 지출 주입 증가 → 부족 확률 비감소, 최저 잔액 비증가 (전 프로필·as_of 표본) |

---

## 13. 선행 구현(03 저장소) 대비 계승·변경

| 항목 | 03 | 본 엔진 | 이유 |
| --- | --- | --- | --- |
| 입력 | 금융망 응답 형식 `FinSnapshot` | ERD 정렬 `TwinInput` (+ 금융망 어댑터) | KeyFin DB 가 실제 공급원 |
| 기능 축 | SIM-01~04, ANL-01~03, INT, WEB | 5 모드로 재편. ANL 은 RISK 에, INT-02 는 facts 로 흡수 | 사용자 정의 5 모드 |
| OPTIMIZE | 없음(ANL-02 재배분만) | 신설. CRN 후보 평가 + 그리디 조합 | "최적 행동 탐색" 모드 |
| GOAL | 역산 상한만 | 상한 + 도달 확률 + 계획 재시뮬 확률 | 실현 가능성을 확률로 |
| 에이전트·LLM·대시보드 | 포함 | 제외 | 엔진만 |
| 출력 | 툴별 pydantic dump | 공통 봉투 + facts + viz 어휘 | 시각화·발화 계약 명시 |
| 전이 순서·Behavior 공식·우려 결제 규칙·health | §7 | 그대로 계승 | 검증된 규칙 |
| 외부 변수 | 없음 | `externals` 3종 + WHATIF EXTERNAL | 사용자 다이어그램의 External Variables |
| 비상금 | 자동 미사용 | 동일. `EMERGENCY_DRAW` 주입으로만 | FR-BGT-09 사용자 선택 |

---

## 14. 리스크·미결

| # | 항목 | 대응 |
| --- | --- | --- |
| R1 | 미결제 청구서 재시도 규칙이 금융망 실제와 다를 수 있음 | 생성기·시뮬레이터 같은 가정. LIVE 검증 후 §7.2 4단계만 수정 |
| R2 | 카드 할부 API 부재(요구사항 미결 #6) | `loans[AMORTIZING]` 으로 재현. 할부 개념은 엔진에 두지 않음 |
| R3 | 봉투 주기가 달력 월인데 급여일이 다름 | v0.1 달력 월 고정. `cycle_anchor: PAYDAY` 옵션은 v0.2 |
| R4 | OPTIMIZE 후보 폭발 | 시뮬 ≤ 40회, n_paths 자동 하향, 결과에 `evaluated/sim_calls` 명시 |
| R5 | 불규칙 수입 예측 오차 | 기준 완화(C). v0.2 에 수입 간격 분포 샘플링 |
| R6 | `is_variable` 고정비 금액 추정 실패 | 원장 중앙값 없으면 0 + 경고. facts 에 `unknown_variable_fixed` 노출 |
| R7 | facts 와 viz 라벨 불일치 | `fdt validate` 가 annotations·caption 의 숫자를 facts 집합과 대조 |
| M1 | 확률 표기를 % 정수로 할지 소수로 할지 | 모드 내 통일만 강제. 에이전트 팀과 합의 후 고정 |
| M2 | GOAL `SAVE` 타입의 "저축" 정의(비상금 이체 포함 여부) | v0.1: PRIMARY 잔액 증가분으로 정의 |

---

## 15. 부록

### A. 카드 청구 주기 예시 (B 프로필, 화요일 출금)

| 날짜 | 요일 | 사건 |
| --- | --- | --- |
| 9/1~9/7 | 월~일 | 승인 누적 103,500 |
| 9/8 07:30 | 월 | 청구서 발행 103,500 |
| 9/9 16:00 | 화 | 출금 103,500 |
| 9/15 07:30 | 월 | 청구서 167,800 |
| 9/16 16:00 | 화 | 잔액 120,000 → 부족. `card_shortfall`, 청구서 유지 |
| 9/17 16:00 | 수 | 재시도. 잔액 200,000 → 출금 |

### B. 우려 결제 규칙 수치 예

| 예산 | 잔여(직전) | 결제 | 0.5×잔여 | 3×pace | 판정 |
| --- | --- | --- | --- | --- | --- |
| 600,000 | 20,000 | 15,000 | 10,000 | 60,000 | 미발동 (월말 과민 방지) |
| 600,000 | 200,000 | 120,000 | 100,000 | 60,000 | WARNING |
| 600,000 | 200,000 | 250,000 | 100,000 | 60,000 | DANGER |

### C. RISK 결과 viz 예 (축약)

```jsonc
[{"kind":"gauge","id":"risk","title":"30일 결제 부족 위험","priority":1,
  "data":{"value":37,"min":0,"max":100,"thresholds":[20,50],"level":"WARNING"},"encoding":{"unit":"점"},
  "caption":"위험 점수 37점, 주의 단계."},
 {"kind":"table","id":"payments","title":"결제일별 부족 확률","priority":1,
  "data":{"columns":[{"key":"due","label":"결제일","unit":"date"},{"key":"name","label":"항목"},
                     {"key":"amount","label":"금액","unit":"KRW"},{"key":"fail_prob","label":"부족 확률","unit":"%"}],
          "rows":[{"due":"2026-09-16","name":"KB 체크 카드대금","amount":175000,"fail_prob":35}]},
  "annotations":[{"type":"point","x":"2026-09-16","label":"가장 위험한 결제일"}],
  "caption":"9월 16일 카드대금 17만 5천원의 부족 확률이 35%로 가장 높다."}]
```
