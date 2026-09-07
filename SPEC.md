# FDT 엔진 명세 (SPEC) v0.7

- 상태: v0.7 (2026-09-07, S49 앞당김 반영). 구현은 이 문서를 단일 기준으로 삼고, 변경은 이 문서를 먼저 고친다.
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
    "id": 1, "employment_status?": "EMPLOYED", "income_band?": null, "birth_date?": null
    // employment_status/income_band/birth_date 는 선택(?). 엔진 계산에 쓰이지 않음(어댑터 호환용)
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
    // kind 는 CREDIT | DEBIT 이나 표시용이다. cards[] 의 카드는 kind 와 무관하게 전부 주 단위 청구 주기를 따른다(금융망 카드 모델).
    // 체크카드 즉시 출금 소비는 이 카드 청구 주기가 아니라 tx_type=WITHDRAW 계좌 거래로 표현한다
    "id": 20, "issuer_code": "1001", "card_name": "KB 체크", "kind": "CREDIT",   // CREDIT | DEBIT
    "withdrawal_account_id": 10, "withdrawal_weekday": 1,                    // 0=월 … 6=일 (금융망 1~7 은 어댑터가 변환)
    "is_managed": true
  }],
  "card_billings": [{
    "id": 30, "card_id": 20, "billing_date": "2026-09-01", "total_amount": 183500,
    "status": "UNPAID", "paid_at": null                // status 값 집합: UNPAID | PAID
  }],
  "fixed_expenses": [{
    "id": 40, "name": "월세", "expense_type": "RENT",   // RENT|SUBSCRIPTION|CARD_BILL|LOAN|UTILITY|INSURANCE|TELECOM
    "amount": 700000, "is_variable": false, "payment_day": 25,
    "withdrawal_account_id": 10, "card_id": null,      // 카드 결제형 고정비면 card_id
    "active": true
  }],
  "loans": [{                                         // 선택. 금융망 대출 API 대응
    "id": 50, "balance": 12000000, "annual_rate_pct": 6.8, "interest_day": 15,
    "withdrawal_account_id": 10, "repayment": "INTEREST_ONLY",  // INTEREST_ONLY | AMORTIZING(원리금균등)
    "term_months?": 36                                 // 선택. 잔여 상환 개월. 없으면 36개월 가정(§5.4)
  }],
  "budgets": [{                                       // budgets + budget_envelopes (선택. 없으면 엔진이 제안)
    "budget_month": "202609", "status": "CONFIRMED",   // status 값 집합: PROPOSED | CONFIRMED
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
| 봉투 7종·세분류→봉투 매핑 누락, 또는 봉투 id↔이름·세분류 22종·세분류→봉투 매핑이 `taxonomy` 와 완전히 일치하지 않음 | 오류 `E-INPUT-TAXONOMY` |
| 카드의 `withdrawal_account_id` 가 accounts 에 없음 | 오류 `E-INPUT-REF` |
| 모든 배열의 id 중복(다른 내용). 같은 id·같은 내용은 1건으로 정리 | 오류 `E-INPUT-DUP` |
| 계좌 대사: `opening_balance + Σ부호거래 ≠ balance` | 경고 `W-RECON` 와 차액. `strict=true` 면 오류 |
| 관리 대상(`is_managed`) 계좌 0개 | 오류 `E-INPUT-EMPTY` |
| 거래 이력 < 28일 | 경고 `W-INPUT-SHORT_HISTORY`, Behavior 는 기본값 비중 증가 |

`as_of` 를 `twin.as_of` 보다 앞으로 당겨 빌드한 경우(홀드아웃) 대사·잔액 역산은 그 `as_of` 를 기준으로 한다. 즉 `opening_balance + Σ부호거래(≤ as_of) ≠ balance_at(as_of)` 로 대사하고, `opening_balance is None` 이면 `balance(twin.as_of) − Σ부호거래(as_of < date ≤ twin.as_of)` 로 역산한다(§4.1 구현 규칙 참조).

모든 입력 검증 실패(`E-INPUT-*` 포함)는 `FdtError(code)` 로 던진다. pydantic `ValidationError` 는 메시지를 파싱하지 않고 `extract_errors` 로 구조화해 `FdtError` 로 감싼다. 여러 오류가 동시에 발생하면 전부 보고한다(`error.details.errors[]`, §9.1).

---

## 4. 엔진 객체 `Engine`

### 4.1 구성

```
Engine
├ meta        : engine_id(입력 해시 12자), built_at, as_of, schema_version, warnings[]
├ ledger      : LedgerTx[]  (정규화·분류된 불변 원장. 전체 기간, as_of 로 자르지 않는다)
├ state       : State(t)             §5
├ behavior    : Behavior             §6
├ externals   : Externals            §3.2
└ run(req: ModeRequest) -> EngineResult   §7~§9
```

- `build_engine(twin_input, *, budgets_override=None, strict=False) -> Engine`
- **구현 규칙(S34):** `build_engine` 은 전체 원장으로 대사·잔액 역산을 한 뒤 `as_of` 이하로 절단한 원장만 엔진에 보관한다. 즉 `account_balance_at`/`reconcile` 은 절단 전 전체 원장에 대해 그 `as_of` 기준으로 수행하고, `Engine.ledger` 에는 절단된 결과만 남긴다(§3.3 대사 규칙 참조). 이렇게 해야 과거 `as_of` 로 빌드해도 미래 거래가 잔액에 누수되지 않고, `reconcile` 이 그 `as_of` 잔액과 맞아 오탐 경고가 나지 않는다.
- `Engine.to_dict()` / `Engine.from_dict()` : ledger·state·behavior·externals·meta 를 dict(직렬화 가능 구조)로 왕복한다. 파일 I/O 는 하지 않는다(§4.2-7). 파일 저장·복원은 `fdt/tools/engine_io.py` 의 `save_engine(engine, path)` / `load_engine(path) -> Engine` 이 맡는다(내부에서 `to_dict`/`from_dict` 를 호출). `engine_id` 가 다르면 `load_engine` 이 로드를 거부한다(`E-ENGINE-ID-MISMATCH`).
- `Engine.fork()` : What-if 용 얕은 복제. 원장은 공유(불변), state 만 복사. `meta` 도 복사한다(분기가 경고를 추가해도 원본을 오염시키지 않는다).
- 엔진은 **as_of 를 바꾸지 않는다**. 다른 기준일은 새 엔진이다(홀드아웃 누수 방지).
- **`EngineBuildMeta`(엔진 내부, dataclass) vs `EngineMeta`(§9.1 출력, pydantic) 구분.** `EngineBuildMeta` 는 빌드 시점 불변 메타(`engine_id`, `as_of`, `engine_version`, `warnings`, `budgets_override` 등, 재현성을 위해 `built_at` 은 담지 않는다)이고 엔진 내부 전용이다. `Engine.run()` 이 매 호출마다 요청의 `mode`/`seed`/`n_paths`/`horizon_days`/`elapsed_ms` 를 채워 `schemas.result.EngineMeta` 로 옮기며, §9.1 `meta` 로 나가는 것은 오직 `EngineMeta` 뿐이다. `EngineMeta.warnings` 는 `ResultWarning{code, message, details}` 의 배열이다(§9.1).

### 4.2 불변 원칙 (MUST)

1. `fdt/engine/**` 는 `openai`, `anthropic`, `ollama`, `requests`, `httpx` 를 import 하지 않는다. 테스트 `test_architecture.py` 가 검사한다.
2. 난수 시드에 `time`/`hash()`/`random` 사용 금지. 시드는 `numpy.random.default_rng(seed)` 에만 넣는다. 성능 계측용 `time.perf_counter()` 만 허용(예: `EngineMeta.elapsed_ms` 측정).
3. 금액 연산은 정수. 확률·비율·로그정규 파라미터만 float.
4. `ledger` 는 생성 후 변경 불가(`tuple` 또는 frozen dataclass).
5. 다섯 모드는 모두 `simulate()` 하나를 호출한다. 모드별로 별도 전이 규칙을 두지 않는다.
6. 출력 JSON 에 차트 라이브러리·색상 코드·픽셀 값이 들어가지 않는다.
7. 엔진 코어(`fdt/engine/**`)는 파일·콘솔 I/O 를 하지 않는다. 스키마 내보내기 등 도구는 `fdt/tools/` 에 둔다.

---

## 5. State(t)

### 5.1 정의 (`schemas/state.py`)

```jsonc
{
  "as_of": "2026-09-07",
  "accounts": [{"id":10,"role":"PRIMARY","balance":1830000}, {"id":11,"role":"EMERGENCY","balance":350000}],
                                    // role: PRIMARY | EMERGENCY | OTHER(비관리 계좌. is_managed=false 인 계좌가 여기 담긴다)
  "liquidity": 1830000,            // PRIMARY 잔액
  "emergency_fund": 350000,        // EMERGENCY 합. 시뮬레이션이 자동 사용하지 않는다
  "cards": [{
    "id":20, "card_name":"KB 체크", "withdrawal_weekday":1, "withdrawal_account_id":10, "unbilled":92300,   // 이번 청구 주기 누적(승인−취소)
    "issued_unpaid":[{"billing_date":"2026-09-01","amount":183500}]
    // card_name(S47): 시뮬레이터가 약정 큐 없이 청구 이벤트를 만들 때(§7.2 3~4단계) 사람이 읽는 이름이 필요하다
  }],
  "committed": [{                  // 약정 큐, as_of+1 ~ as_of+horizon_cap(90)
    "kind":"RENT","name":"월세","due":"2026-09-25","amount":700000,"certainty":1.0,"account_id":10,"card_id":null,
    "source_fixed_expense_id":40,"source_loan_id":null,"source_card_id":null,
    "rate_pct?":null,"principal?":null
    // kind 허용 집합: RENT | UTILITY | INSURANCE | TELECOM | SUBSCRIPTION | LOAN | CARD_BILL | SELF_TRANSFER | DETECTED_FIXED
    // DETECTED_FIXED = 원장 탐지 일반 고정비(§5.4). source_fixed_expense_id/source_loan_id/source_card_id 는 선택(?), 근거가 없으면 null
    // rate_pct?/principal?(S64): kind==LOAN 항목에만 채운다(연이자율%, 원금). EXTERNAL.loan_rate_delta_bp 주입 시 재계산(§7.2 2단계)에 필요하다. 그 외 kind 는 null
    // 수입은 큐에 넣지 않는다(§8.2 events 로만 표현)
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

`transactions[]` → `LedgerTx(id, date, time, account_id, card_id, signed_amount, flow, envelope_id, subcategory_id, confidence, source, counterparty_account_id)`. `tx_type == CARD` 인 거래의 `LedgerTx.account_id` 는 `None` 이다(카드 승인은 계좌 잔액에 영향이 없고 `CARD_BILL` 출금에서만 반영된다. §3.3 계좌 대사의 전제).

흐름 판정 순서. `flow_hint` 는 판정 결과의 **흐름 라벨만** 덮어쓴다. 구조 변환(규칙 1 의 취소 2건 분할, 규칙 2 의 내 계좌 상대 레코드 생성)은 `flow_hint` 유무와 무관하게 항상 적용한다:

1. `status == CANCELED` 인 CARD 거래 → 원 승인 `SPEND(−)` 와 같은 시각 `REFUND(+)` 두 건으로 기록(이력 보존, 순액 0).
2. `exclude_tag == SELF_TRANSFER` 또는 `counterparty_account_id` 가 내 계좌 → `TRANSFER_INTERNAL` (봉투 없음).
3. 고정비 매칭: `fixed_expenses` 의 (계좌 또는 카드, 금액 ±10%, payment_day ±3일) 에 맞으면 `FIXED`. 카드대금은 `merchant_name_raw` 에 "카드대금" 또는 `fixed_expenses.expense_type == CARD_BILL` 매칭 → `CARD_BILL`. 단 `subcategory_id` 가 있는 거래는 소비로 보고 고정비 후보에서 제외한다(단, `fixed_expenses.name == merchant_name_raw` 면 예외로 매칭). 계좌 매칭은 `tx_type ∈ {WITHDRAW, TRANSFER}` 에만 적용하고, `tx_type == CARD` 는 `fixed_expenses.card_id` 와만 매칭한다.
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
| `issued_unpaid` | `card_billings[billing_date ≤ as_of, paid_at is null 또는 paid_at > as_of]`(`paid_at` 기준. `status` 는 `twin.as_of` 시점 값이라 홀드아웃 `as_of` 판정에 쓰지 않는다). 없고 직전 주 승인이 원장에 `CARD_BILL` 로 안 보이면 재구성 |
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
| LOAN 이자 | `loans[]` | `interest_day` | `balance × (rate+delta_bp/100)/100/12`, 10원 단위. `AMORTIZING` 은 `term_months` 로 원리금균등, `term_months` 가 없으면 36개월 가정 | 1.0 |
| 카드대금(미청구) | `cards.unbilled` | 다음 월요일 발행 후 첫 `withdrawal_weekday` | `unbilled` | 0.9 |
| 카드대금(미결제) | `issued_unpaid` | 다음 `withdrawal_weekday`(as_of 포함). 단 예정 출금일이 `as_of` 이하이면(연체) `due = as_of + 1` 로 둔다(§7.2 4단계의 매일 재시도와 정합) | 1.0 |
| 원장 탐지 반복 고정비 | `FIXED` 거래를 (계좌/카드, 이름) 로 묶어 월 1회(간격 25~35일) 2회 이상 반복. `kind = DETECTED_FIXED` 로 표기(§5.1) | 마지막 발생 + 1개월 | 최근 3회 중앙값 | 0.9 |
| 원장 탐지 반복 자기이체 | `TRANSFER_INTERNAL` 거래를 (출금 계좌, 상대 계좌, 금액 ±10%) 로 묶어 월 1회(간격 25~35일) 2회 이상 반복 | 마지막 발생 + 1개월 | 최근 3회 중앙값 | 0.9 |

`AMORTIZING` 을 실측 검증하려면 §11 프로필 중 하나(B 변형)에 `term_months` 지정 프로필을 추가해야 한다. 이는 v0.2 과제로 남긴다(SPEC 은 규칙만 정의).

**S44(약정 큐의 `CARD_BILL` 이중 반영 금지).** 약정 큐의 `kind == CARD_BILL` 항목(카드대금(미청구)/(미결제) 두 행)은 `state.cards[].unbilled`/`.issued_unpaid` 와 같은 정보를 담은 as_of 스냅샷이다. `simulate`(§7.2)는 이 큐 항목을 **처리하지 않고** 카드 상태(`cards[]`)에서 청구 주기를 직접 재구성한다(이중 반영 방지). 큐의 `CARD_BILL` 은 §8.2 `events` 표시와 §8.4 확정 유출 계산에만 쓰며, §8.4 확정 유출에서는 카드 상태 기반 값과 **중복 계상하지 않도록** 이 큐 항목을 제외한다(§8.4 참조).

**S64(대출이자 재계산, 한계 명시).** `EXTERNAL.loan_rate_delta_bp` 가 시뮬레이션 중 주입(§8.3 `EXTERNAL`)되면, `repayment == INTEREST_ONLY` 대출의 이자를 그 시점부터 `principal × (rate_pct + delta_bp/100) / 100 / 12` 로 재계산한다(10원 단위 반올림, `principal`/`rate_pct` 는 §5.1 `Committed` 의 LOAN 항목 필드). `repayment == AMORTIZING` 은 원리금 상환표가 고정돼 있어 금리 변경을 재계산하지 **않는다**(한계로 명시. 원리금균등 상환액의 금리 재산정은 v0.2 과제).

중복 제거: 동일 (kind, name, due, amount) 는 하나. `fixed_expenses`·`loans[]`·`cards[]` 에서 이미 만든 항목과 같은 (계좌 또는 카드, 이름) 을 갖는 원장 탐지 항목(`DETECTED_FIXED`)은 만들지 않는다(대출이자·카드대금 이중 계상 방지). 단 이 키로도 (b) 의미적 중복(예: 이름이 바뀐 고정비)까지는 못 잡을 수 있다.

`state.committed` 는 `as_of+1 ~ as_of+90` 구간만 담는다(§7.1 참조. `horizon_days > 90` 요청은 모드 러너가 큐를 재생성한다).

### 5.5 엔진 예산 제안 `propose_budgets`

완결 월(1일~말일 모두 as_of 이전) 봉투 순지출 → 3개월 이상 중앙값, 1~2개월 평균, 0개월은 최근 28일 × 30/28. 만원 단위 올림, 하한 10,000원. `budget_source = "ENGINE"`.

---

## 6. Behavior (행동 모델)

윈도우는 가용 이력 전체(상한 180일, 최소 28일. 부족하면 있는 만큼)를 쓴다(S49 적용, v0.7. 이전 고정 90일 창을 대체). `Behavior.window_days` 에 실제로 쓰인 값을 담는다. `SPEND` 만 사용, 같은 날·같은 카드·같은 금액의 승인+취소 쌍은 제거. 이력이 28일 미만이면 `window_days` 는 실제 이력 일수를 담고 `W-INPUT-SHORT_HISTORY` 경고를 낸다.

| 파라미터 | 추정 | 클립·기본값 |
| --- | --- | --- |
| `daily_rate[e]` | 봉투 e 건수(돌발로 분류된 건 제외, 아래 2-pass 참조) / 윈도우 일수 | |
| `weekday_mult[e][w]` | `(c_w + 2) / (E_w + 2)` 후 평균 1 정규화 | `n_e < 10` 이면 전부 1.0 |
| `amount_mu[e], amount_sigma[e]` | 돌발로 분류된 건을 제외한 표본의 로그정규 MLE(2-pass) | sigma [0.2, 1.5]. `n_e < 5` 면 전 봉투 통합, 통합도 5 미만이면 `mu=ln 10000, sigma=0.6`. 이력 < 28일이면 이 통합(pooled) 기준으로 `n_e < 10` 을 적용한다 |
| `card_share[e]` | 카드 건수 / 건수 | `n_e=0` 이면 전체 비율, 그것도 0이면 0.5 |
| `payday_boost` | 창 `[수입일, 수입일+6]` 일평균 / 그 외 일평균 | [0.7, 2.0]. 표본 14일 미만이면 1.0 |
| `pre_payday_damp` | 창 `[다음 수입일−5, 다음 수입일−1]` 일평균 / 그 외 일평균 | [0.5, 1.3]. 표본 10일 미만이면 1.0 |
| `elasticity[e]` | 봉투 잔여율 < 0.2 인 날 일평균 / 그 외 | 필수 봉투(교통비·의료·건강·편의점·마트·잡화) 클립 [0.8, 1.2], 유연 봉투(외식·쇼핑·취미·여가·기타) 클립 [0.5, 2.0]. **저잔여일 < 10일이면 1.0**(기존 5일 기준을 상향) |
| `shock_daily_prob, shock_mu, shock_sigma` | `금액 ≥ max(50,000, 5·exp(mu_e))` 건 | 0건이면 `0.01, ln 100000, 0.6`. `shock_sigma` 하한 0.3(절단분포로 인한 과소추정 방지, 원시값이 이보다 작으면 0.3 으로 올림) |
| 수입 일정 (§6.6) | INCOME 거래 일자 간격 cv ≤ 0.25 이고 day-of-month 최빈 비율 ≥ 0.6 → 규칙적. 그 외 불규칙. 최빈값이 동률이면 **작은 날짜** 를 고른다 | 1건 이하면 `next=None, expected=0` |

`payday_boost`/`pre_payday_damp` 겹침 규칙: 수입 간격 중앙값이 12일 미만이거나 불규칙이면 두 창이 겹칠 수 있다. 이 경우 **`pre_payday_damp` 는 1.0 으로 고정**하고, `payday_boost` 는 급여 전 창(`[다음 수입일−5, 다음 수입일−1]`)을 표본에서 제외하고 추정한다(추정기 규칙. §7.2 의 생성기는 이 규칙과 무관하게 두 계수를 곱하는 쪽이 정본이다). §11 C 프로필처럼 수입 간격이 10~11일인 사용자는 이 규칙이 적용되어 두 파라미터의 신뢰구간이 넓다는 점을 감안한다.

봉투 금액(`amount_mu`/`amount_sigma`)과 `daily_rate` 추정은 2-pass 로 한다. 1차로 `shock_daily_prob/mu/sigma` 판정 기준(금액 ≥ 임계)에 걸리는 건을 돌발로 분류하고, 2차로 그 건을 제외한 표본만으로 `daily_rate`/`amount_mu`/`amount_sigma` 를 다시 추정한다. 이렇게 하지 않으면 `기타` 봉투처럼 돌발이 몰리는 봉투의 일상 소비 분포가 돌발에 오염된다.

각주(N13): 잔액 부족 시 거절된 체크 소비는 원장에 남지 않는다(§11). 이 때문에 잔액이 얇은 사용자일수록 `daily_rate` 는 과소, `card_share` 는 과대 추정되는 구조적 편향이 있다. 시뮬레이터가 `suppressed_demand` 를 별도로 누적할 경우, 이 편향과 `suppressed_demand` 를 함께 반영하면 억제 효과를 이중으로 세게 된다. 두 메커니즘이 같은 현상(거절)을 서로 다른 경로로 반영하고 있음을 W6/W7 이 인지해야 한다.

**S49(적용, v0.7).** Behavior 추정 창을 고정 90일에서 "가용 이력 전체, 상한 180일, 하한 28일(부족하면 있는 만큼)" 로 완화했다. `daily_rate`/`amount_mu` 의 표준오차를 `Behavior` 에 함께 담아 축소 추정(shrinkage, α=14)을 적용하는 안은 이번 판에는 포함하지 않는다. L1 이 이를 추가 채택할 수 있으며, 그 결정은 L1 보고 후 다음 판에 반영한다. 근거는 §14 R10.

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
- **S65(Overrides 필드 명시).** `Overrides` 는 다음 필드만 갖는다(전부 선택):
  - `budgets: dict[envelope_id, int]`: 봉투 예산 값 자체를 바꾼다(§8.3 `BUDGET_CHANGE` 의 소프트 경로. `behavior_follows` 에 따라 `elasticity_gate` 동반 여부가 갈린다)
  - `hard_caps: dict[envelope_id, int]`: GOAL 하드 캡(S55). 그 달 봉투 누적이 캡에 닿으면 `λ → 0`, 필수 봉투는 하한 비율까지만 허용
  - `cancel_committed: list[source_fixed_expense_id]`: 약정 큐에서 해당 고정비 발생원을 제거
  - `committed_amount_override: dict["kind:source_id", int]`: 약정 큐 특정 항목의 금액을 덮어쓴다. 키는 `"{kind}:{source_fixed_expense_id|source_loan_id|source_card_id}"` 문자열
  - `externals: Externals`: `price_index_mult`/`loan_rate_delta_bp`/`income_growth_pct` 부분 또는 전체 덮어쓰기(§8.3 `EXTERNAL`)
  - `card_withdrawal_weekday: dict[card_id, int]`: 카드 출금 요일 임시 변경(§8.6.1 네 번째 후보, §8.6 `OverrideSpec`)
- 결과 배열 shape `(n_paths, horizon_days+1)`. `dates[0] = as_of`(기록값은 as_of 잔액).
- `state.committed` 는 `as_of+90` 까지만 채워져 있다(§5.4). `horizon_days > 90` 인 요청은 모드 러너가 `build_committed_queue(horizon_cap=horizon_days+7)` 로 큐를 재생성해 시뮬레이터에 넘긴다. `simulate` 자신은 큐를 다시 만들지 않는다.

### 7.2 하루 처리 순서 (MUST, 생성기와 동일)

```
1 수입      d == next_income → liquidity += expected × (1+income_growth)^(년).
            규칙적 수입(day-of-month 고정)은 다음일 = 정해진 날짜이며 난수를 소비하지 않는다(CRN 보존).
            불규칙 수입은 금액 ~ LogNormal(0, 0.4) 잡음을 곱하고, 다음 수입일 = d + max(3, round(median_gap + N(0, 0.3·median_gap)))(S48. 생성기 §11 규칙과 동일해야 한다)
2 고정비    큐 due == d, **단 kind == CARD_BILL 은 이 단계에서 처리하지 않는다**(S44. 청구·출금은 3~4단계가 `cards[]` 상태로 직접 진행한다. 큐의 CARD_BILL 은 §8.2 events 표시·§8.4 확정 유출에만 쓴다).
            계좌형: cash ≥ amount 면 차감, 부족하면 당일 거절 → unpaid_obligation 누적(재시도 없음). 카드형(카드 결제형 고정비): card.unbilled += amount
            kind == LOAN 이고 `EXTERNAL.loan_rate_delta_bp` 가 주입되어 있으면(§8.3) `repayment == INTEREST_ONLY` 인 항목만 `principal × (rate_pct+delta_bp/100)/100/12` 로 재계산한다(10원 단위, S64). `AMORTIZING` 은 재계산하지 않는다
            큐의 SELF_TRANSFER 는 PRIMARY 에서 차감하고 emergency_fund 에 가산한다. 부족하면 당일 건너뛴다(재시도 없음)
3 청구 발행 d.weekday()==0 → 카드별 issued.append(unbilled); unbilled = 0
4 카드 출금 청구서별 예정 출금일 = billing_date 이후(당일 포함) 첫 d.weekday()==withdrawal_weekday 인 날. 예정 출금일 전에는 그 청구서를 시도하지 않는다.
            예정 출금일 이후로는 결제될 때까지 매일 재시도한다. 오래된 것부터 시도해 cash ≥ total 이면 차감·제거하고,
            부족하면 card_shortfall[p]=True 로 표시하고 청구서를 유지한 채 그 카드의 그날 남은 청구서는 시도하지 않는다(중단).
            cards[] 의 카드는 kind(CREDIT|DEBIT) 와 무관하게 전부 이 주 단위 청구 주기를 따른다(금융망 카드 모델).
            체크카드(kind=DEBIT) 의 즉시 출금 소비는 이 단계가 아니라 tx_type=WITHDRAW 계좌 거래로 표현한다. kind 는 표시용이며 처리 로직을 분기하지 않는다.
5 소비      봉투별 λ = daily_rate × weekday_mult[wd] × boost(d) × elasticity_gate × 1(price_index 는 금액에)
            boost(d) = payday_boost^[수입일 ≤ d ≤ 수입일+6] × pre_payday_damp^[다음 수입일−5 ≤ d ≤ 다음 수입일−1]
            (두 창 자체가 겹칠 수 있는 날짜는 생성기가 두 계수를 곱해서 그대로 반영한다. 이것이 정본이며, §6 의 추정기 겹침 규칙과는 별개다)
            n ~ Poisson(λ); 금액 ~ LogNormal(mu, sigma) × price_index_mult, 100원 반올림
            card_share 만큼 unbilled 로, 나머지(현금분)는 그 봉투·그날 합계에 대해 **부분 체결**한다(S46): `paid = min(그 봉투·그날 현금 지출 합계, liquidity)`, `나머지 = suppressed_demand` 로 누적(개별 거래 단위 전부-또는-전무가 아니다. §7.1 벡터화 요구와 양립하고 §8.3 주입 처리와 같은 규칙이다)
            envelope_spend[p,e] += Σ(체결된 금액만). 달이 바뀌면 spent 리셋
6 돌발      Bernoulli(shock_daily_prob) → LogNormal(shock_mu, shock_sigma) × price_index_mult, 100원 반올림(S63). 봉투 기타. 카드 비율은 전체 평균
7 주입      injections 중 on == d → 5와 같은 방식(부분 체결 포함). (수입 주입은 1과 같은 방식). 주입 금액은 `elasticity_gate` 가 보는 누적치에 합산하지 않는다(CRN 보존, S46)
8 기록      balances[p,k] = liquidity
            economic[p,k] = liquidity − Σissued_unpaid − unpaid_obligation − suppressed_demand
            any_shortfall[p,k] = card_shortfall[p] ∨ unpaid_obligation[p] > 0 ∨ suppressed_demand[p] > 0(S45. `economic < 0` 여부는 부족 판정에 쓰지 않고 지표로만 노출한다). 처음이면 first_shortfall_idx[p]=k
            결제 이벤트가 있던 날은 event_log[k] 에 (kind, amount, 성공 경로 비율) 기록
```

생성기 전용: 7단계(주입) 자리에 생성기 전용 단계(카드 취소, 더치페이 수령)를 둔다. 이 단계는 시뮬레이터에 없다.

벡터화: 경로 축을 numpy 배열로 동시에 진행. 포아송은 `rng.poisson(λ, n_paths)`, 금액은 총 건수만큼 한 번에 뽑아 `np.add.reduceat`.

### 7.3 `SimulationResult`

```python
dates: list[date]; balances, economic, envelope_spend: ndarray
any_shortfall, card_shortfall: bool[n_paths]; first_shortfall_idx: int[n_paths]
# any_shortfall(S45) = card_shortfall ∨ unpaid_obligation末日누적>0 ∨ suppressed_demand末日누적>0 (§7.2 8단계). economic<0 은 부족 판정에 쓰지 않는다
event_log: list[DayEvents]
def stats(economic=False) -> PathStats  # median/p10/p90/mean by day, min_balance, min_balance_date,
                                        # shortfall_prob, card_shortfall_prob, first_shortfall_date_median,
                                        # end_balance_median, envelope_spend_median[e],
                                        # expected_shortfall: any_shortfall[p]==True 인 경로의 (말일 unpaid_obligation + 말일 Σissued_unpaid + 말일 suppressed_demand) 평균(S45, §8.5 참조)
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
- 필수 파라미터 누락은 `E-REQ-MISSING`, 범위 밖은 `E-REQ-RANGE`. 0 이나 기본값으로 조용히 바꾸지 않는다. 검증 실패는 `FdtError(code)` 로 던지며 메시지에 코드 문자열을 파싱 대상으로 포함하지 않는다(파싱 규약은 §9.1 참조). 여러 파라미터가 동시에 실패하면 오류 코드를 전부 보고한다(`error.details.errors[]`).
- 금액 파라미터는 0 ~ 1,000,000,000,000 정수 원.

### 8.2 FORECAST (미래 상태 예측)

`params`: `{ "include_envelopes": true, "include_events": true }`

`result`:
```jsonc
{
  "trajectory": {"dates":[...], "median":[...], "p10":[...], "p90":[...], "mean":[...]},  // mean 필수. trajectory 배열만 float, 그 외 금액은 정수 원(반올림)
  "economic":   {"median":[...], "p10":[...], "p90":[...]},
  "min_point":  {"date":"2026-09-24","median_balance":118000,"p10_balance":-64000},        // 정수 원(반올림)
  "end_point":  {"date":"2026-10-07","median_balance":2013000},                            // 정수 원(반올림)
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
| `SPEND` | `on`(날짜 또는 `days_from_now`), `amount`, `envelope_id`, `method`(CARD/CASH), `card_id?` | 단건 지출 |
| `INCOME` | `on`, `amount` | 단건 수입 |
| `RECURRING_SPEND` | `start`, `every_days` 또는 `day_of_month`, `amount`, `envelope_id`, `method`, `until?`(선택, 종료일), `card_id?` | 구독 추가 등 |
| `FIXED_CHANGE` | `fixed_expense_id`, `new_amount` 또는 `cancel: true`, `from`(필수, 적용 시작일) | 고정비 변경·해지 |
| `BUDGET_CHANGE` | `envelope_id`, `new_budget`, `behavior_follows`(bool, 기본 true) | 예산 변경(S53). `behavior_follows=true` 면 `elasticity_gate` 기준까지 바뀐다(새 예산 대비 잔여율로 재계산). `false` 면 예산 값 자체는 바뀌어 봉투 `remaining`/`overrun_prob` 계산에 반영되지만 소비 행동(λ)은 바뀌지 않는다(기존 예산 기준 `elasticity_gate` 유지) |
| `EXTERNAL` | `price_index_mult?`, `loan_rate_delta_bp?`, `income_growth_pct?` | 외부 변수 시나리오 |
| `EMERGENCY_DRAW` | `on`, `amount` | 비상금 → PRIMARY 이체 |

**S66(카드 지정).** `method == CARD` 인 `SPEND`/`RECURRING_SPEND` 는 `card_id?` 로 어느 카드의 `unbilled` 에 누적할지 지정한다. 생략하면 첫 관리 카드(`cards[]` 등록 순서 기준 `is_managed=true` 첫 항목)를 쓴다. 이 값은 이후 §8.2 events·§8.5 payment_risks 가 그 카드의 청구 이벤트를 구성할 때 그대로 반영된다.

`result`:
```jsonc
{
  "base":   { FORECAST.result 축약: trajectory.median/p10/p90, min_point, end_point, shortfall_prob, card_shortfall_prob },  // 최저·말일 잔액은 정수 원(반올림)
  "branch": { 동일 },
  "delta":  {"min_balance": -150000, "end_balance": -150000, "shortfall_prob": +0.11, "card_shortfall_prob": +0.06,
             "first_shortfall_date": {"base":null,"branch":"2026-09-24"},
             "envelopes":[{"envelope_id":5,"remaining_change":-150000,"overrun_prob_change":+0.42}]},
  "verdict": "CAUTION",            // OK | CAUTION | DANGER, 델타 기준 (§8.3.1)
  "branch_level": "WARNING",       // SAFE | WARNING | DANGER, 분기의 절대 위험 수준 (§8.3.1, S52)
  "crn": true
}
```

8.3.1 판정(S52: `verdict` 는 **개입 효과(델타) 기준**으로만 낸다. 기준선이 이미 위험한 사용자에게 0원 주입도 DANGER 가 나오는 것을 막기 위함).

- `verdict`: `delta.card_shortfall_prob ≥ 0.3` 또는 (기준 최저 ≥ 0 이면서 분기 최저 < 0) → DANGER. `delta.shortfall_prob ≥ 0.15` 또는 (기준 최저 > 0 이고 분기 최저 < 기준 최저 × 0.5, S51: 기준 최저가 0 이하면 이 조건은 적용하지 않는다. 부호가 뒤집히기 때문) → CAUTION. 그 외 OK.
- `branch_level`: 분기의 **절대** 위험 수준을 별도 필드로 낸다. §8.5 RISK 의 `level` 규칙(`risk_score` 문턱 <20 SAFE, <50 WARNING, 그 외 DANGER)을 분기 `card_shortfall_prob`/`shortfall_prob` 에 그대로 적용해 계산한다.
- 기준·분기는 같은 시드(CRN). 지출 주입 ≥ 0 이면 분기 최저 ≤ 기준 최저, 부족 확률 비감소가 **불변식**이다.

### 8.4 GOAL (목표 실현 가능성)

`params`:
```jsonc
{ "goal_type": "BALANCE",                 // BALANCE(목표일 절대 잔액 ≥ target) | SAVE(기간 누적 증분 저축 ≥ target, PRIMARY 잔액 증가분 기준. M2 확정) | ENVELOPE_ADHERE(이번 달 전 봉투 예산 내)
  "target_amount": 2000000, "target_date": "2026-12-31",    // ENVELOPE_ADHERE 는 둘 다 생략
  "protect_essential": true }             // 필수 봉투({교통비, 의료·건강, 편의점·마트·잡화}) 하한 80% 보장
```

`result`:
```jsonc
{
  "feasible": true, "achieve_prob": 0.62,          // 기준 행동 그대로일 때 경로 중 목표 도달 비율
  "achieve_prob_ci": [0.55, 0.69],                  // S54. n_paths 이항 표본오차 기반 95% CI. 표본이 얇으면 폭이 넓다
  "gap": {"median": -180000, "p10": -640000},      // 음수 = 부족
  "required": {"total_discretionary_cap": 1920000, "reduction_ratio": 0.23, "baseline_discretionary": 2490000},
  "weekly_caps": [{"week_start":"2026-09-08","days":7,"total_cap":210000,
                   "by_envelope":[{"envelope_id":1,"cap":58000}, ...]}],
  "plan_achieve_prob": 0.88,                        // weekly_caps 를 하드 캡(Overrides.hard_caps)으로 주입해 재시뮬한 도달 확률(S55)
  "notes": ["불규칙 수입은 기대치의 80%만 반영",
            "baseline_discretionary 추정 표본이 얇음(window_days=84 < 120): achieve_prob 신뢰구간이 넓을 수 있음"]  // S54: window_days<120 또는 봉투 건수<30 이면 이 경고를 반드시 넣는다
}
```

계산: `H = target_date − as_of`(1~365). 기준 시뮬 → `achieve_prob`(경제 잔액이 아니라 목표 정의(§8.4 goal_type)에 따른 잔액 지표 기준). `achieve_prob_ci` 는 이항 비율의 표본오차로 계산한다(S54).

`goal_type == SAVE` 의 저축 증분 지표는 **economic 기준**(카드 미결제·미납·억제 차감분을 반영한 잔액)으로 정의한다(S66). 즉 `SAVE` 의 "PRIMARY 잔액 증가분"(§8.4 params 주석, M2)은 `economic` 배열의 증가분을 말하며, 단순 `liquidity` 증가분이 아니다.

확정 유입 `I`(규칙적 수입 확정, 불규칙 ×0.8), 확정 유출 `F`(큐 + 월 반복). `F` 계산에서 약정 큐의 `kind == CARD_BILL` 항목은 `cards[]` 상태(`unbilled`+`issued_unpaid`) 기반 값으로 **1회만** 계상한다(S66, S44 연계. 큐와 카드 상태를 이중으로 더하지 않는다). `available = liquidity + I − F − target`. `available < 0` → `feasible=false`, `gap` 보고.

주차 상한 = `available × days_w / H` 를 기준선 봉투 비율로 배분, 필수 봉투 하한 보장. **주차 상한 합은 `min(available, baseline_discretionary, Σ현재 예산 × H/30)` 을 넘지 않는다**(S55).

**상한 적용 방식(S55).** 이전 버전(`BUDGET_CHANGE` 소프트 경로)은 캡 주입이 예산을 실질적으로 인상해 `plan_achieve_prob` 이 역행하는 사례가 있었다. GOAL 은 주차 상한을 `BUDGET_CHANGE` 가 아니라 **하드 캡**(`Overrides.hard_caps: dict[envelope_id, int]`, §7.1)으로 주입해 재시뮬한다. 그 달 봉투 누적 지출이 캡에 닿으면 그 봉투의 그 달 남은 기간 `λ → 0` 으로 강제하고, 필수 봉투는 하한 비율(80%, `protect_essential`)까지만 캡을 적용한다. 재시뮬 결과가 `plan_achieve_prob` 이다(계획이 통계적으로도 통하는지 확인).

### 8.5 RISK (리스크 분석)

`params`: `{ "recent_tx_ids": [] }` (우려 결제 검사 대상. 비면 as_of 당일 SPEND 전부)

`result`:
```jsonc
{
  "risk_score": 37, "level": "WARNING",            // score = round(100 × max(card_shortfall_prob, 0.6 × shortfall_prob)), <20 SAFE, <50 WARNING
  "shortfall_prob": 0.31, "card_shortfall_prob": 0.37,
  "worst_day": "2026-09-16", "expected_shortfall": 142000,        // any_shortfall 경로의 말일 (미결제+미납+억제) 합계 평균(S45, §7.3). 정수 원(반올림)
  "payment_risks": [{"due":"2026-09-09","kind":"CARD_BILL","name":"KB 체크","amount":183500,"fail_prob":0.02,"median_balance_before":1640000},   // median_balance_before 는 정수 원(반올림)
                    {"due":"2026-09-16","kind":"CARD_BILL","name":"KB 체크","amount":175000,"fail_prob":0.35,"median_balance_before":161000},
                    {"due":"2026-09-25","kind":"RENT","name":"월세","amount":700000,"fail_prob":0.30,"median_balance_before":690000}],
  "alerts": [{"kind":"ACCELERATION","severity":"WARNING","ratio":1.42},
             {"kind":"CONCERNING_TX","severity":"DANGER","tx_id":1001,"amount":250000,"envelope_id":5,"remaining_before":200000,"threshold":100000}],
  "safe_to_spend_today": 19100,                    // §8.5.1
  "health": {"score":58,"level":"WARNING","coverage":0.61,"adherence":0.72,"risk":0.63}
}
```

8.5.1 Safe-to-Spend: `days = max(1, next_income − as_of)`(없으면 30). `committed = Σ큐 amount (as_of < due < next_income)`. `raw_daily = (liquidity − committed)/days`. `factor = 1/acceleration if acceleration > 1 else 1`. `safe_today = max(0, floor((min(raw_daily × factor, Σ유연 봉투 잔여 / days, spend_7d_avg × 1.5) − spent_today)/100) × 100)`(S50: 상한 3종 중 최솟값. 유연 봉투는 §8.4/§8.6.1 정의와 동일한 `{외식, 쇼핑, 취미·여가, 기타}`. 근거: 급여 며칠 전 상한 없는 계산은 남은 유동성 전액을 하루치로 몰아 비현실적인 값을 낸다).

8.5.2 우려 결제: `threshold = max(0.5 × remaining_before, 3 × budget/말일, 20,000)`. `amount ≥ threshold` → WARNING, `amount ≥ remaining_before` → DANGER. 가속도: `acceleration ≥ 1.3` 이고 `spend_7d_avg ≥ 10,000` → WARNING, `≥ 1.6` DANGER.

8.5.3 health: `cov = clip((liquidity − committed_30d)/max(spend_90d_avg × 30, 1), 0, 1)`, `adh = 1 − mean_e clip(spent_e/budget_e − progress, 0, 1)`, `rsk = 1 − card_shortfall_prob`, `score = 100(0.4cov + 0.3adh + 0.3rsk)`, ≥70 SAFE, ≥40 WARNING.

### 8.6 OPTIMIZE (최적 행동 탐색)

`params`:
```jsonc
{ "objective": "MIN_SHORTFALL_PROB",     // MIN_SHORTFALL_PROB | MAX_END_BALANCE | REACH_GOAL(goal 파라미터 동반)
  "candidates": "AUTO",                  // AUTO 이면 §8.6.1 기본 후보 생성, 또는 injections 형식의 후보 배열
  "max_actions": 3,                      // 조합 시 최대 행동 수. 1..3 (상한 3, 시뮬 예산 ≤ 40 근거)
  "constraints": {"protect_essential": true, "max_cut_ratio": 0.5, "allow_emergency_draw": false} }
```

8.6.1 AUTO 후보 (각각 하나의 `override` 또는 `injection`):
- 유연 봉투(`{외식, 쇼핑, 취미·여가, 기타}`) 각각 −10%, −20%, −30% (`BUDGET_CHANGE`, behavior_follows)
- 활성 SUBSCRIPTION 고정비 각각 해지 (`FIXED_CHANGE cancel`)
- 비상금 이체 (허용 시, 부족액만큼 `EMERGENCY_DRAW`)
- 카드 출금 요일 변경(수입일 직후 요일) (`override.card_withdrawal_weekday`)

8.6.2 탐색: 단일 행동 전부 CRN 평가 → 목적함수 개선 상위 `k=6` 를 골라 2~`max_actions` 조합 그리디(한 봉투에 두 비율 동시 금지). 총 시뮬 횟수 ≤ 40 을 넘으면 후보를 잘라낸다.

**S56(목적값 다단 사전식 정의).** `MIN_SHORTFALL_PROB` 의 목적값은 후보를 다음 튜플의 **사전식 순서**(lexicographic, 각 항은 작을수록 좋음)로 비교한다:

```
(max(shortfall_prob, card_shortfall_prob), 기대 부족액(expected_shortfall), −최저 경제 잔액 중앙값, −말일 잔액 중앙값)
```

근거: `shortfall_prob` 이 0.0 또는 1.0 에 포화되는 프로필(예: 항상 안전하거나 항상 부족)에서 1차 항만으로는 후보가 전혀 변별되지 않아 `ranked_bars` 가 사실상 빈 차트가 된다. 2~4차 항이 동률을 깬다. `effect.delta` 는 이 튜플에서 실제로 순위를 가른 차원의 값을 담는다(1차 항이 동률이면 2차 항의 델타, 등).

`ranked[].actions[]` 의 원소 타입 `AppliedAction`(S57):
```
AppliedAction = { injection?: Injection, override?: OverrideSpec, cut_ratio?: float, label?: str }
```
`injection` 과 `override` 중 **정확히 하나만** 있어야 한다. `injection` 은 §8.3 Injection 유니온(7종) 그대로다. `override` 는 `OverrideSpec` 유니온으로, §8.6.1 네 번째 후보(카드 출금 요일 변경)처럼 Injection 으로 표현되지 않는 상태 변경을 담는다:
```
OverrideSpec = CARD_WITHDRAWAL_WEEKDAY { card_id: int, new_weekday: int }   // 0=월 … 6=일
```
`cut_ratio`/`label` 은 어떤 `Injection`/`OverrideSpec` 타입에도 없는 부가 정보이므로 `AppliedAction` 래퍼에서만 붙인다(Injection·OverrideSpec 유니온 자체는 `extra="forbid"` 를 유지한다).

`result`:
```jsonc
{
  "objective": "MIN_SHORTFALL_PROB",
  "baseline": {"shortfall_prob":0.31,"card_shortfall_prob":0.37,"end_balance_median":780000},
  "ranked": [{"rank":1,
              "actions":[{"injection":{"type":"BUDGET_CHANGE","envelope_id":5,"new_budget":280000,"behavior_follows":true},
                          "cut_ratio":0.3,"label":"쇼핑 예산 30% 축소"}],
              "effect":{"shortfall_prob":0.12,"delta":-0.19,"end_balance_median":1010000,"cost_of_action":"쇼핑 월 12만원 감소"},
              "feasibility_note":"이번 달 이미 사용 21만원, 남은 한도 7만원"},
             {"rank":2,
              "actions":[{"override":{"type":"CARD_WITHDRAWAL_WEEKDAY","card_id":20,"new_weekday":2},
                          "label":"카드 출금 요일을 수요일로 변경"}],
              "effect":{"shortfall_prob":0.31,"delta":0.0,"end_balance_median":780000,"cost_of_action":"카드 출금일 이동"},
              "feasibility_note":"1차 항 동률, 기대 부족액 감소로 순위 결정(S56)"},
             ...],
  "recommended": {"rank":1, "combined_effect":{...}},
  "evaluated": 23, "sim_calls": 24,
  "n_paths_used": 400,                              // S66. §12 근거로 자동 하향된 n_paths 실측값
  "notes": ["1차 목적항(shortfall_prob)이 다수 후보에서 포화되어 2~4차 항으로 순위를 결정함(S56)"]  // S66. OptimizeResult 에 notes[] 추가
}
```

---

## 9. 출력 계약 `EngineResult`

### 9.1 봉투 구조

```jsonc
{
  "schema_version": "engine-result/1",
  "meta": {"engine_id":"a3f9c1d2e4b5","as_of":"2026-09-07","mode":"RISK","seed":42,"n_paths":1000,
           "horizon_days":30,"elapsed_ms":812,"engine_version":"0.1.0",
           "warnings":[{"code":"W-RECON","message":"...","details":{"account_id":10,"diff":144600}}]},
  "request": { ModeRequest 원문 },
  "result": { §8 모드별 },
  "facts":  [ §9.2 ],
  "viz":    [ §9.3 ],
  "status": "OK"                          // OK | ERROR. ERROR 면 result 없음, error{code,message,details}
}
```

`meta.warnings` 는 `ResultWarning{code, message, details}` 의 배열이다. `code` 는 `W-*` 코드 문자열, `message` 는 사람이 읽는 설명, `details` 는 코드별 구조화 필드(자유 dict 가 아니라 각 `W-*` 코드가 정의한 키 집합)를 담는다.

`EngineError.code` 는 pydantic `ValidationError` 메시지를 파싱해서 채우지 않는다. 검증 지점에서 `FdtError(code=...)` 로 감싸 전달한 값을 그대로 옮긴다. pydantic 오류 메시지에는 코드 문자열이 포함되지만 메시지가 그 코드로 **시작함을 보장하지 않으므로**(필드명·위치가 앞에 붙는다) `startswith` 등으로 코드를 추출해서는 안 된다. 모든 검증 실패는 `FdtError(code)` 로 던지고, pydantic `ValidationError` 는 `extract_errors` 로 구조화한다(메시지 파싱 금지). 여러 파라미터·필드가 동시에 실패하면 전부 보고한다: `error.details.errors[]` 에 개별 실패를 나열한다(§8.1 참조).

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

**S60(KRW 반올림 표기 규칙).** `value < 1,000` 원이면 `allowed_renderings` 는 **원 단위 표기 하나만** 낸다(예: `["100원"]`). `약 …`/`…만원` 등 반올림 표기는 그 반올림 결과가 0 이 되면 생성하지 않는다(예: 100원은 `"0원"`/`"0만원"`/`"약 0원"` 을 내지 않는다).

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

**S58(제목의 요청 파라미터 값).** `title`/`caption` 에 `horizon_days` 처럼 요청 파라미터에서 온 값을 넣으려면 빌더(`build_viz`)가 그 값을 인자로 받아야 한다. 예: FORECAST/RISK 제목은 고정 문자열 `"30일 결제 부족 위험"` 이 아니라 `"{horizon_days}일 결제 부족 위험"` 로 짓는다(요청의 실제 `horizon_days` 를 채운다). 숫자를 뺄 수 있으면 빼도 된다.

**S59(수치 라벨 검사 범위·방법).**
1. "수치 라벨" 은 `annotations[].label`, `caption`, `title`, `data.*.{label,name,detail}` **전부**를 포함한다(어느 한 곳도 예외가 아니다).
2. 검사 방법: 그 문자열을 토큰화한 것을 facts `allowed_renderings` 를 토큰화한 **집합**과 **정확히 일치**시켜 검사한다(부분 문자열 포함 매칭은 허용하지 않는다. `fdt validate` R7 이 이 방식으로 구현돼야 한다).
3. 예외: 순위·개수 같은 서수·계수 표현(정규식 `\d+(위|개|건|번째)`, 예: "1위", "3개", "2건", "5번째")은 이 검사에서 제외한다(facts 에 없어도 된다). 그 외 수치는 전부 검사 대상이다.

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
fdt schema  --out schemas/                                  # TwinInput/State/Behavior/ModeRequest/EngineResult JSON Schema 내보내기
fdt eval    backtest|calibration|monotonic|perf|all          # §12 기준 자동 측정, data/eval/*.json + docs/EVAL_REPORT.md
```

- 모드 선택은 `--mode` 필수. 라우팅 기능은 없다.
- Python API: `from fdt.engine import build_engine, ModeRequest; Engine.run(ModeRequest(...))`.
- 출력 인코딩 UTF-8 고정(`PYTHONIOENCODING=utf-8`).

---

## 11. 더미 데이터 생성기 (`fdt/gen/`)

프로필 YAML(A_steady, B_card_crunch, C_impulsive, D_goal_saver) + 시드 → `TwinInput` 과 `ground_truth.json`.

| 프로필 | 특징 | 목표 수치 | pending_ratio | 주로 검증하는 모드 |
| --- | --- | --- | --- | --- |
| A_steady | 고정 급여 25일 315만, 체크카드 위주, 탄력도 0.75, 월 30만 비상금 적립 | 지출/수입 75~85% | .05 | FORECAST 기준선, RISK 가 조용히 SAFE |
| B_card_crunch | 급여 25일 287만, 카드 2장(화·토 출금) 90%, 월세 70만·대출 1,200만 6.8% | 지출/수입 88~96%, card_shortfalls 3~8건 | .10 | RISK, WHATIF(카드 청구 큐 전이) |
| C_impulsive | 프리랜서 불규칙 입금 월 2~4회, 주말 배수 2.4, 탄력도 1.4, 돌발 잦음 | - | .18 | FORECAST 밴드 폭, OPTIMIZE |
| D_goal_saver | 급여 10일 260만, 구독 5개, 예산 확정 상태, 12월 말까지 as_of 잔액 대비 200만원 추가 저축(goal_type SAVE) 이 현 소비 유지 시 아슬아슬하게 미달 | (S61) **6개월 생성 기준**: 완결 월 잉여 평균 45~52만, 월별 σ ≤ 9만, as_of 잔액 250~350만 | .08 | GOAL, OPTIMIZE(구독 해지 후보) |

(S61) D 프로필의 "as_of 잔액 250~350만" 목표는 `months=6` 생성에서만 성립한다(`months=3` 은 115~183만). 목표를 5 시드 실측 분산에 맞춰 재조정했다(이전 "월 잉여 40~48만"은 5시드×4완결월=20관측치 범위 101,500~702,000원, σ≈160,000 과 맞지 않았다). 재조정된 목표는 생성기 파라미터 튜닝(v0.2, W1 담당)이 완료된 뒤 실측으로 재검증한다.

생성 규칙은 §7.2 하루 처리 순서와 **동일**해야 한다(생성기가 시뮬레이터의 정답 분포). (S62) §7.2 2단계와 동일하게, **비상금 자기이체는 PRIMARY 잔액이 부족하면 당일 건너뛴다(재시도 없음)**. 이는 생성기·시뮬레이터 공통 규칙이며, 현재 생성기가 이를 어기고 있어 v0.2 에서 바로잡는다. 생성기가 엔진에 숨기는 변수: payday_boost, elasticity, 돌발 분포, 취소 확률, 더치페이, 잔액 부족 시 체크 거절(원장 미기록). 생성기는 `confirm_status` 의 `PENDING` 을 소비(SPEND) 거래에만 부여한다. 수입·고정비·카드대금·자기이체는 `CONFIRMED` 다. `ground_truth.json`: `daily_balance`, `card_shortfalls[]`, `declined_debits[]`(원소에 `kind`: FIXED | LOAN | SPEND 포함), `shocks[]`, `envelope_true_spend`, `income_events[]`, `hidden_params`, `unpaid_obligation`(일별 누적), `suppressed_demand`(일별 누적). **엔진 코드는 ground_truth 를 읽지 않는다.**

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

평가 도구: `fdt eval backtest|calibration|monotonic|perf|all`, 산출물 `data/eval/*.json`, `docs/EVAL_REPORT.md`.

**백테스트 실측(2026-09-07, 5 시드, `docs/EVAL_REPORT.md`, S46·S48 반영 후).** sMAPE A .018 PASS, B .094(4/5 시드 통과), C .530(2/5 시드 통과, 기준 .40 초과, **FAIL**), D .012 PASS. 커버리지는 전 프로필에서 일부 시드가 기준(0.6~0.95, C 는 0.5~0.95) 을 벗어난다. 캘리브레이션 ECE `card_shortfall_prob` .024, `shortfall_prob` .031(둘 다 PASS). 단조성 위반 2/128건(전부 C 프로필). 성능 12 항목 전부 PASS(기준의 1/10 이하). C sMAPE FAIL 과 커버리지 이탈의 원인은 §14 R10(Behavior 90일 창의 추정 표본오차)으로 특정했다. **S49 적용 후 재측정 예정**(본 표의 수치는 S49 반영 전 측정값이다).

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
| R5 | 불규칙 수입 예측 오차 | S48 적용(v0.1, v0.6). §7.2 1단계에 생성기와 동일한 간격 잡음 `d + max(3, round(median_gap + N(0, 0.3·median_gap)))` 을 시뮬레이터에도 반영했다(이전엔 결정론 `median_gap` 고정이었다). 정량 근거: C 프로필 커버리지가 5 시드 중 4회 0.6 이하로 나왔던 원인. 재측정으로 기준(§12) 재검증 필요 |
| R6 | `is_variable` 고정비 금액 추정 실패 | 원장 중앙값 없으면 0 + 경고. facts 에 `unknown_variable_fixed` 노출 |
| R7 | facts 와 viz 라벨 불일치 | `fdt validate` 가 annotations·caption 의 숫자를 facts 집합과 대조 |
| R8 | 생성기·시뮬레이터 규칙 발산 | §7.2 를 정본으로 삼는다. 두 코드가 공유 상수 모듈을 쓰게 하고, §15.A 표를 두 코드 공통 테스트로 고정한다 |
| R9 | C 프로필처럼 수입 간격이 짧은 사용자는 `payday_boost`/`pre_payday_damp` 신뢰구간이 넓다 | §6 겹침 규칙(수입 간격 < 12일 또는 불규칙 → `pre_payday_damp=1.0` 고정, `payday_boost` 는 급여 전 창 제외)으로 완화. 근본 해결은 v0.2 표본 확대·구간 추정 |
| R10 | Behavior 추정 표본 오차(90일 창)가 A·D 커버리지 이탈과 D GOAL `achieve_prob` 분산의 직접 원인 | 적용(v0.7). 정량 근거: 90일 창에서 봉투별 건수 추정이 시드에 따라 ±26% 흩어져 30일 누적 소비가 0.74~1.10배로 갈리고, 이것이 A·D 커버리지 이탈과 D GOAL `achieve_prob` 0.006~0.983 분산의 직접 원인이다. §6 추정 창을 가용 이력 전체(상한 180일, 하한 28일)로 확대했다(S49). 표준오차를 `Behavior` 에 노출하거나 축소 추정(α=14)을 적용하는 안은 이번 판에 포함하지 않았다. L1 이 이를 추가 채택할 수 있으며, 그 결정은 L1 보고 후 다음 판에 반영한다 |
| R11 | 커버리지 상한(.95) 초과 시드(A seed 1, D seed 7 등)는 밴드가 넓은 것이 아니라 정답 궤적이 좁게 예측 중심에 붙은 경우가 섞여 있어, 상한 기준의 타당성 자체를 재검토해야 한다 | 미결. 상한 기준의 타당성은 v0.2 에서 재검토 |
| M1 | 확률 표기를 % 정수로 할지 소수로 할지 | 모드 내 통일만 강제. 에이전트 팀과 합의 후 고정 |
| M2 | GOAL `SAVE` 타입의 "저축" 정의(비상금 이체 포함 여부) | v0.1: PRIMARY 잔액 증가분(economic 기준, S66)으로 정의 |
| M3 | A 프로필이 `level: SAFE` 인데 `alerts` 에 `ACCELERATION` `WARNING` 이 동반될 수 있다(§8.5.2 가속도 판정과 §8.5 전체 `level` 산식이 서로 다른 신호를 본다). 현재 `Alert` 스키마에 이 불일치를 표시할 참고 필드가 없어 소비자가 모순으로 오해할 수 있다 | 미결(N5). Alert 에 `context`/`note` 같은 참고 표시 필드 추가 여부를 다음 리뷰에서 결정 |

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
[{"kind":"gauge","id":"risk","title":"{horizon_days}일 결제 부족 위험","priority":1,
  "data":{"value":37,"min":0,"max":100,"thresholds":[20,50],"level":"WARNING"},"encoding":{"unit":"점"},
  "caption":"위험 점수 37점, 주의 단계."},
 {"kind":"table","id":"payments","title":"결제일별 부족 확률","priority":1,
  "data":{"columns":[{"key":"due","label":"결제일","unit":"date"},{"key":"name","label":"항목"},
                     {"key":"amount","label":"금액","unit":"KRW"},{"key":"fail_prob","label":"부족 확률","unit":"%"}],
          "rows":[{"due":"2026-09-16","name":"KB 체크 카드대금","amount":175000,"fail_prob":35}]},
  "annotations":[{"type":"point","x":"2026-09-16","label":"가장 위험한 결제일"}],
  "caption":"9월 16일 카드대금 17만 5천원의 부족 확률이 35%로 가장 높다."}]
```

---

## 16. 개정 이력

`docs/reviews/20260907_W0.md` W0 리뷰의 "SPEC 수정 제안" 반영 내역 (v0.1 → v0.2).

| # | 요약 |
| --- | --- |
| S1 | §3.2 `user.employment_status`/`income_band`/`birth_date` 를 선택(`?`)으로 표기하고 "엔진 계산에 쓰이지 않음(어댑터 호환용)" 명시 |
| S2 | §3.2 `card_billings.status` 값 집합 `UNPAID \| PAID`, `budgets.status` 값 집합 `PROPOSED \| CONFIRMED` 명시 |
| S3 | §3.3 `E-INPUT-EMPTY` 를 "관리 대상 계좌 0개" 로 명확화 |
| S4 | §3.3 `E-INPUT-TAXONOMY` 에 봉투 id↔이름·세분류 22종·세분류→봉투 매핑이 taxonomy 와 완전 일치해야 함을 명시 |
| S5 | §3.3 `E-INPUT-DUP` 를 거래 배열에서 모든 배열로 확대 |
| S6 | §5.1/§5.4 `committed.kind` 허용 집합을 열거하고 "수입은 큐에 넣지 않는다(§8.2 events 로만)" 명시 |
| S7 | §6 에 이력 28일 미만일 때 `window_days` 는 실제 이력 일수이고 `W-INPUT-SHORT_HISTORY` 경고를 낸다는 규약 추가 |
| S8 | §8.3 `FIXED_CHANGE.from` 을 필수(적용 시작일)로 명시하고 `RECURRING_SPEND.until?` 과 표기를 구분 |
| S9 | §8.6 `ranked[].actions[]` 원소 타입을 `AppliedAction = {injection: Injection, cut_ratio?: float, label?: str}` 로 정의하고 예시 JSON 을 그 구조로 수정 |
| S10 | §8.6 `max_actions` 상한을 `1..3` 으로 명시(시뮬 예산 ≤ 40 근거) |
| S11 | §9.1 에 `EngineError.code` 는 `ValidationError` 메시지 파싱이 아니라 검증 지점의 `FdtError(code)` 로 채운다고 명시. §8.1 문장도 "코드 문자열을 포함한 오류" 로 수정 |
| S12 | §4.2-2 를 "난수 시드에 `time`/`hash()`/`random` 사용 금지. 성능 계측용 `time.perf_counter()` 만 허용" 으로 구체화 |
| S13 | §8.2 `trajectory.mean` 을 필수로 명시 |
| S14 | §8.4/§8.6.1 필수·유연 봉투를 중괄호 집합 + 가운뎃점 포함 정식 이름으로 수정 |
| S15 | §10 CLI 목록에 `fdt schema --out <dir>` 추가 |
| 추가1 | §8.2 `min_point`/`end_point`, §8.5 `expected_shortfall`/`payment_risks[].median_balance_before`, §8.3 base/branch 요약의 최저·말일 잔액을 정수 원(반올림)으로 명시. `trajectory` 배열만 float 유지 |
| 추가2 | §4.2 에 "엔진 코어(`fdt/engine/**`)는 파일·콘솔 I/O 를 하지 않는다. 도구는 `fdt/tools/`" 항목 추가 |
| 추가3 | §5.1 `AccountState.role` 에 `OTHER`(비관리 계좌) 허용을 명시 |

`docs/reviews/20260907_W1_W2.md` W1·W2 리뷰의 "SPEC 수정 제안" 반영 내역 (v0.2 → v0.3).

| # | 요약 |
| --- | --- |
| S16 | §7.2 4단계 카드 출금 규칙을 §15.A 를 정본으로 정밀화. 예정 출금일 = billing_date 이후(당일 포함) 첫 withdrawal_weekday, 그 전엔 시도 안 함, 이후 매일 재시도, 부족 시 그 카드의 그날 남은 청구서는 시도하지 않는다(중단) |
| S17 | §5.2 규칙 3 에 판별자 추가. `subcategory_id` 가 있으면 소비로 보아 고정비 후보에서 제외(단 `fixed_expenses.name == merchant_name_raw` 면 예외), 계좌 매칭은 `tx_type ∈ {WITHDRAW, TRANSFER}` 에만, `tx_type == CARD` 는 `fixed_expenses.card_id` 와만 매칭 |
| S18 | §7.2 표 아래에 "생성기는 7단계(주입) 자리에 생성기 전용 단계(카드 취소, 더치페이 수령)를 둔다. 이 단계는 시뮬레이터에 없다" 한 줄 추가 |
| S19 | §5.2 흐름 판정 서문을 "`flow_hint` 는 흐름 라벨만 덮어쓰고, 구조 변환(취소 분할·내 계좌 상대 레코드 생성)은 `flow_hint` 유무와 무관하게 항상 적용한다" 로 정밀화 |
| S20 | §11 에 "생성기는 `confirm_status` 의 `PENDING` 을 소비(SPEND) 거래에만 부여한다. 수입·고정비·카드대금·자기이체는 `CONFIRMED` 다" 추가, 프로필 표에 `pending_ratio` 열 추가(A .05, B .10, C .18, D .08) |
| S21 | §11 D 프로필 행의 목표를 "12월 말까지 as_of 잔액 대비 200만원 추가 저축(goal_type SAVE) 이 현 소비 유지 시 아슬아슬하게 미달" 로 확정. §8.4 `goal_type` 정의에 `BALANCE`=절대 잔액, `SAVE`=증분 저축(PRIMARY 잔액 증가분 기준, M2 확정) 명시 |
| S22 | §5.4 약정 큐에 "원장 탐지 반복 자기이체" 행 추가, §5.1 `committed.kind` 허용 집합에 `SELF_TRANSFER` 추가, §7.2 2단계에 "큐의 `SELF_TRANSFER` 는 PRIMARY 차감 + `emergency_fund` 가산, 부족하면 당일 건너뜀" 추가. §5.2 `LedgerTx` 정의에 `counterparty_account_id` 필드 명시 |
| S23 | §7.2 5단계 `boost` 를 `boost(d) = payday_boost^[수입 후 7일] × pre_payday_damp^[다음 수입 5일 전]` 복합 계수로 정의. §6 표에 `pre_payday_damp` 행(다음 수입 5일 전 일평균 / 그 외, 클립 [0.5, 1.3], 표본 10일 미만 1.0) 추가, §11 숨김 변수 목록에서 `pre_payday_damp` 제거 |
| S24 | §6 `elasticity[e]` 행에 "탄력도는 유연 봉투 대표값이고 필수 봉투는 1.0 근처" 명시 |
| S25 | §5.2 `LedgerTx` 정의에 "`tx_type == CARD` 인 거래의 `account_id` 는 `None`" 명시. §3.2 `cards` 주석과 §7.2 4단계에 "`cards[]` 의 카드는 `kind` 와 무관하게 전부 주 단위 청구 주기를 따른다(금융망 카드 모델). 체크카드 즉시 출금 소비는 `tx_type=WITHDRAW` 계좌 거래로 표현한다. `kind` 는 표시용" 명시 |
| S26 | §11 `ground_truth.json` 필드 목록에 `declined_debits[].kind`, `unpaid_obligation`, `suppressed_demand` 추가 |
| S27 | §11 프로필 표 B 행에 "급여 25일 287만" 명시 |

`docs/reviews/20260907_W3_W4_W5.md` W3·W4·W5 리뷰의 "SPEC 수정 제안" 반영 내역 (v0.3 → v0.4).

| # | 요약 |
| --- | --- |
| S28 | §5.3 `issued_unpaid` 정의를 `card_billings[status=UNPAID, billing_date ≤ as_of]` 에서 `card_billings[billing_date ≤ as_of, paid_at is null 또는 paid_at > as_of]` 로 수정. 홀드아웃 `as_of` 판정은 `status`(twin.as_of 시점 값)가 아니라 `paid_at` 기준이어야 함을 명시 |
| S29 | §3.2 `loans[]` 에 `term_months?`(잔여 상환 개월) 추가. §5.4 LOAN 행에 "`AMORTIZING` 은 `term_months` 로 원리금균등, 없으면 36개월 가정" 명시. `AMORTIZING` 실측 검증을 위한 §11 B 변형 프로필 지정은 v0.2 과제로 메모만 남긴다 |
| S30 | §5.4 중복 제거 문장을 "동일 (kind, name, due, amount) 는 하나" 로 수정하고, "`fixed_expenses`·`loans[]`·`cards[]` 에서 이미 만든 항목과 같은 (계좌 또는 카드, 이름) 을 갖는 원장 탐지 항목은 만들지 않는다" 추가(대출이자 이중 계상 방지) |
| S31 | §5.1 `Committed.kind` 허용 집합에 `DETECTED_FIXED`(원장 탐지 일반 고정비) 추가. §5.4 원장 탐지 반복 고정비 행에 이 kind 로 표기함을 명시 |
| S32 | §5.1 `Committed` 에 `source_fixed_expense_id?`/`source_loan_id?`/`source_card_id?` 추가 |
| S33 | §5.1 `CardState` 에 `withdrawal_account_id` 추가 |
| S34 | §3.3/§4.1 에 "`as_of` 를 `twin.as_of` 보다 앞으로 당겨 빌드한 경우 대사·잔액 역산은 그 `as_of` 를 기준으로 한다" 추가. 구현 규칙으로 "`build_engine` 은 전체 원장으로 대사·잔액 역산을 한 뒤 `as_of` 이하로 절단한 원장만 엔진에 보관한다" 명시(홀드아웃 미래 누수·`W-RECON` 오탐 방지) |
| S35 | §6/§7.2 `payday_boost` 창을 `[수입일, 수입일+6]`, `pre_payday_damp` 창을 `[다음 수입일−5, 다음 수입일−1]` 로 명문화. 두 창이 겹치는 경우(수입 간격 중앙값 < 12일 또는 불규칙) 추정기 규칙을 "`pre_payday_damp` 는 1.0 고정, `payday_boost` 는 급여 전 창을 제외해 추정" 으로 정하고, 생성기는 두 계수를 곱하는 쪽을 정본으로 삼는다(§7.2). §14 R9, §6 각주로 C 프로필처럼 수입 간격이 짧으면 두 파라미터 신뢰구간이 넓음을 명시 |
| S36 | §6 `elasticity[e]` 행의 "봉투 잔여율" 을 "그 달 1일부터 전날까지의 봉투 순지출 누적 / 예산, 월 경계에서 리셋" 으로 명문화(생성기 `_elasticity_gate` 와 동일 정의) |
| S37 | §6 수입 일정의 day-of-month 최빈값 동률 시 "작은 날짜" 를 고른다 추가 |
| S38 | §6 돌발 모델 행에 `shock_sigma` 하한 0.3 명시 |
| S39 | §3.3/§9.1 에 "모든 검증 실패는 `FdtError(code)` 로 던지고 pydantic `ValidationError` 는 `extract_errors` 로 구조화한다(메시지 파싱 금지). 여러 오류는 전부 보고한다(`error.details.errors[]`)" 명시. §8.1 에도 동일 취지 추가 |
| S40 | §5.4 카드대금(미결제) 행에 "예정 출금일이 `as_of` 이하이면(연체) `due = as_of + 1` 로 둔다(§7.2 4단계의 매일 재시도와 정합)" 추가 |
| S41 | §6 `elasticity[e]` 가드를 "저잔여일 < 10일이면 1.0" 으로 상향하고, 필수 봉투 클립 [0.8, 1.2] / 유연 봉투 클립 [0.5, 2.0] 로 분리 |
| S42 | §5.1/§7.1 에 "`state.committed` 는 `as_of+90` 까지. `horizon_days > 90` 인 요청은 모드 러너가 `build_committed_queue(horizon_cap=horizon_days+7)` 로 큐를 재생성해 시뮬레이터에 넘긴다" 명시 |
| S43 | §6 봉투 금액·발생률(`daily_rate`/`amount_mu`/`amount_sigma`) 추정에서 돌발로 분류된 건을 제외하는 2-pass 절차 추가. 이력 < 28일이면 통합(pooled) 기준으로 `n_e < 10` 적용 |
| 추가1 | §9.1 `meta.warnings` 를 `ResultWarning{code, message, details}` 배열로 명시(자유 dict 지양) |
| 추가2 | §6 각주(N13)로 거절된 체크 소비(원장 미기록)로 인한 잔액 얇은 사용자의 `daily_rate` 과소·`card_share` 과대 편향과, 시뮬레이터 `suppressed_demand` 와의 이중 계산 위험을 명시 |
| 추가3 | §4.1 `Engine.save/load` 표기를 `fdt/tools/engine_io.save_engine`/`load_engine` 로 정정하고 `Engine.to_dict`/`from_dict` 를 명시. `EngineBuildMeta`(엔진 내부)와 `EngineMeta`(§9.1 출력) 를 구분하는 한 줄 추가 |

`docs/reviews/20260907_W6_W10.md` W6~W10 리뷰의 "SPEC 수정 제안" 반영 내역 (v0.4 → v0.5).

| # | 요약 |
| --- | --- |
| S44 | §5.4/§7.2 2단계에 "약정 큐의 `kind == CARD_BILL` 항목은 as_of 스냅샷이며 `state.cards[].unbilled`/`.issued_unpaid` 와 같은 정보다. `simulate` 는 이 항목을 처리하지 않고 카드 상태에서 청구 주기를 직접 재구성한다(이중 반영 방지). 큐의 `CARD_BILL` 은 §8.2 events 표시와 §8.4 확정 유출 계산에만 쓰며, 후자에서는 카드 상태 기반 값과 중복 계상하지 않도록 제외한다" 명시 |
| S45 | §7.2 8단계/§8.2/§8.5 "부족"(`any_shortfall`)의 정의를 `card_shortfall ∨ unpaid_obligation > 0 ∨ suppressed_demand > 0` 로 변경. `economic` 잔액은 지표로 계속 노출하되 부족 판정에 쓰지 않는다. `expected_shortfall` 을 "그 사건이 발생한 경로의 말일 미결제+미납+억제 합계 평균" 으로 재정의(§7.3, §8.5) |
| S46 | §7.2 5단계/§8.3 현금 소비 억제를 "그 봉투·그날 현금 지출 합계에 대한 부분 체결(`paid = min(합계, liquidity)`, 나머지는 `suppressed_demand`)" 로 명문화. 주입은 `elasticity_gate` 가 보는 누적치에 합산하지 않는다(CRN 보존)를 §7.2 7단계에 명시 |
| S47 | §5.1 `CardState` 에 `card_name` 필드 추가(시뮬레이터가 큐 없이 청구 이벤트를 만들 때 사람이 읽는 이름이 필요) |
| S48 | v0.2 로 이연. §14 R5 에 "C 프로필 커버리지 5시드 중 4회 0.6 이하" 정량 근거 기록. 불규칙 수입 간격 잡음(생성기와 동일 공식)을 시뮬레이터에도 반영하는 안 |
| S49 | v0.2 로 이연. §14 R10 신설: "추정 표본 오차 ±26%" 근거(90일 창에서 봉투별 건수 추정이 시드에 따라 ±26% 흩어져 30일 누적 소비가 0.74~1.10배로 갈리고, A·D 커버리지 이탈과 D GOAL achieve_prob 분산의 직접 원인) |
| S50 | §8.5.1 `safe_to_spend_today` 상한을 `min(raw_daily × factor, Σ유연 봉투 잔여/days, spend_7d_avg × 1.5)` 로 추가. 근거: 급여 3일 전 D 프로필에서 884,300원/일이 나온다 |
| S51 | §8.3.1 CAUTION 판정의 "분기 최저 < 기준 최저 × 0.5" 에 "기준 최저 > 0 일 때만 적용" 가드 추가(기준 최저가 음수면 부호가 뒤집힘) |
| S52 | §8.3.1 DANGER/CAUTION 판정을 델타 기준으로만 내도록 재정의(`delta.shortfall_prob ≥ 0.15` 등)하고, 분기의 절대 위험은 `branch_level` 필드(§8.5 RISK level 규칙)로 분리 |
| S53 | §8.3 표 `BUDGET_CHANGE` 설명을 "`behavior_follows=true` 면 `elasticity_gate` 기준까지 바뀐다. `false` 면 예산 값은 바뀌어 봉투 `remaining`/`overrun_prob` 계산에 반영되지만 소비 행동(λ)은 바뀌지 않는다" 로 명확화 |
| S54 | §8.4 `GoalResult` 에 `achieve_prob_ci` 추가. `baseline_discretionary` 추정 표본이 얇으면(`window_days < 120` 또는 봉투 건수 < 30) `notes` 에 경고를 넣도록 명시 |
| S55 | §8.4/§7.1 GOAL 의 "상한을 실제 주입해 재시뮬" 을 `BUDGET_CHANGE` 가 아니라 하드 캡(`Overrides.hard_caps: dict[envelope_id, int]`, 캡에 닿으면 λ→0, 필수 봉투는 하한 비율까지)으로 규정. "주차 상한 합 ≤ min(available, baseline_discretionary, Σ현 예산 × H/30)" 명시 |
| S56 | §8.6 `MIN_SHORTFALL_PROB` 의 목적값을 다단 사전식 `(max(shortfall_prob, card_shortfall_prob), 기대 부족액, −최저 경제 잔액 중앙값, −말일 잔액 중앙값)` 으로 정의. `effect.delta` 는 실제로 순위를 가른 차원의 값을 담는다 |
| S57 | §8.6 `AppliedAction` 을 `{ injection?: Injection, override?: OverrideSpec, cut_ratio?: float, label?: str }` 로 확장하고 `OverrideSpec = CARD_WITHDRAWAL_WEEKDAY { card_id, new_weekday }` 신설(§8.6.1 네 번째 후보 표현). `injection`/`override` 중 정확히 하나 |
| S58 | §9.3/§15.C viz `title`/`caption` 에 `horizon_days` 같은 요청 파라미터 값을 넣으려면 빌더가 그 값을 받아야 함을 명시하고, §15.C 예시 제목을 `"{horizon_days}일 결제 부족 위험"` 으로 수정 |
| S59 | §9.3/§14 R7 ①수치 라벨 범위를 `annotations[].label`·`caption`·`title`·`data.*.{label,name,detail}` 전부로 명시 ②검사 방법을 "facts `allowed_renderings` 를 토큰화한 집합과 정확 일치" 로 규정 ③서수·계수(`\d+(위|개|건|번째)`) 는 이 검사에서 예외 |
| S60 | §9.2 KRW `allowed_renderings` 규칙에 "1,000원 미만이면 원 단위 표기 하나만 낸다. 반올림 결과가 0 이면 `약 …`/`…만원` 표기를 생성하지 않는다" 추가 |
| S61 | §11 D 프로필 목표를 "6개월 생성 기준 완결 월 잉여 평균 45~52만, 월별 σ ≤ 9만, as_of 잔액 250~350만" 으로 재조정(5시드 실측 분산 근거) |
| S62 | §11 생성기 규칙에 "비상금 자기이체는 PRIMARY 잔액이 부족하면 당일 건너뛴다(재시도 없음)" 를 §7.2 2단계와 동일하게 다시 못 박음(현 생성기가 이를 어김) |
| S63 | §7.2 6단계 돌발 금액에도 `price_index_mult` 적용(100원 반올림) |
| S64 | §5.1 `Committed` 에 `rate_pct?`/`principal?`(LOAN) 추가. §5.4/§7.2 2단계에 "`EXTERNAL.loan_rate_delta_bp` 주입 시 `INTEREST_ONLY` 대출이자를 `principal×(rate+delta)/1200` 으로 재계산(10원 단위), `AMORTIZING` 은 재계산하지 않는다(한계 명시)" 추가 |
| S65 | §7.1 `Overrides` 필드 목록 명시: `budgets`, `hard_caps`, `cancel_committed(source_fixed_expense_id)`, `committed_amount_override(키 "kind:source_id")`, `externals`, `card_withdrawal_weekday` |
| S66 | §8.2/§8.3/§8.5 `SpendInjection.card_id?` 로 카드 지정(없으면 첫 관리 카드). §8.4 GOAL SAVE 지표를 economic 기준(카드 미결제 차감)으로 명시하고 확정 유출에서 큐 CARD_BILL 은 카드 상태 기반 값으로 1회만 계상(S44 연계). §8.6 `OptimizeResult` 에 `notes[]`, `n_paths_used` 추가 |
| 추가1 | §12 성능·품질 표에 "백테스트 예비 측정(2026-09-07, 5 시드)" 결과 요약(A .018, B .094, C .559 FAIL, D .022)과 C 프로필 기준 재검토 메모(v0.2) 추가 |

`docs/reviews/20260907_W6_W10.md` 후속 오케스트레이터 결정 반영 내역 (v0.5 → v0.6).

| # | 요약 |
| --- | --- |
| S48 적용(v0.6) | S48 을 v0.2 이연에서 v0.1 로 앞당김. §7.2 1단계에 "불규칙 수입의 다음 수입일 = d + max(3, round(median_gap + N(0, 0.3·median_gap))), 금액 LogNormal(0, 0.4). 규칙적 수입은 난수를 소비하지 않는다(CRN)" 명시. §14 R5 를 "이연"에서 "적용"으로 갱신. 생성기 §11 규칙과 동일해야 함을 명시 |

`docs/EVAL_REPORT.md`·`docs/reviews/20260907_W6_W10.md` 의 오케스트레이터 결정 반영 내역 (v0.6 → v0.7).

| # | 요약 |
| --- | --- |
| S49 적용(v0.7) | S49 를 v0.2 이연에서 v0.1 로 앞당김. §6 Behavior 추정 창을 고정 `[as_of − 89, as_of]`(90일)에서 "가용 이력 전체, 상한 180일, 하한 28일(부족하면 있는 만큼)" 로 확대하고 `Behavior.window_days` 에 실제 값을 담도록 명시. §14 R10 을 "이연"에서 "적용(v0.7)"으로 갱신하고 R11(커버리지 상한 초과 시드의 원인이 밴드 과다가 아니라 정답 궤적 쏠림일 수 있다는 점, 상한 기준 타당성은 v0.2 재검토) 신설. §12 백테스트 메모를 `docs/EVAL_REPORT.md` 실측치(A .018 PASS, B .094 4/5, C .530 2/5 FAIL, D .012 PASS, 커버리지 전 프로필 일부 시드 이탈, 캘리브레이션 ECE .024/.031 PASS, 단조성 2/128 C 만, 성능 전부 PASS)로 갱신하고 S49 적용 후 재측정 예정임을 표기. 축소 추정(α=14)은 L1 보고 후 다음 판에 반영 예정으로 이번 판에서는 창 확대만 적용 |
