"""시뮬레이터: Transition + Uncertainty (SPEC 7장).

다섯 모드(FORECAST/WHATIF/GOAL/RISK/OPTIMIZE)가 전부 이 모듈의 `simulate()`
하나만 호출한다(SPEC 4.2-5). 이 모듈은 State/Behavior/Externals 만 읽고,
`fdt/gen/generator.py` 를 import 하지 않는다 - 하루 처리 순서(SPEC 7.2)는
생성기와 "같은 규칙"을 따르지만 코드는 독립적으로 다시 쓴다(작업 지시
"코드 복사는 금지, 규칙만 맞춘다").

공개 이름 (W7 FORECAST/RISK, W8 WHATIF, W9 GOAL, W10 OPTIMIZE 가 그대로
import 하는 계약): `simulate`, `Overrides`, `SimulationResult`.

## 하루 처리 순서 구현 노트 (SPEC 7.2, 보고서에도 요약)

- **day index.** `dates[0] = as_of` 는 이미 확정된 스냅샷이라 어떤 단계도
  거기서 실행되지 않는다. 실제 8단계는 `k=1..horizon_days`(날짜
  `as_of+1..as_of+horizon_days`)에 대해서만 돈다.
- **카드 청구 주기는 `state.committed` 를 거치지 않는다.** `Committed.kind
  == "CARD_BILL"` 항목(SPEC 5.4 "카드대금(미청구)"/"카드대금(미결제)")은
  as_of 시점 스냅샷일 뿐이고, 시뮬레이터는 매주 새 청구서를 스스로
  만들어야 하므로 `state.cards[]`(unbilled/issued_unpaid/withdrawal_weekday)
  에서 매일 직접 재구성한다. 이 항목을 그대로 2단계(고정비)에서 처리하면
  같은 청구가 두 번(약정 큐 스냅샷 + 카드 자체 로직) 반영된다 - 그래서
  `_daily_committed_schedule` 가 이 kind 를 걸러낸다. (W6 착수 메모 6의
  "어느 쪽인지 W6 이 정하고 적을 것" 에 대한 답.)
- **카드 밀린 청구서(backlog) 는 경로별 슬롯 배열로 추적한다.** 청구서는
  발행 순서(=만기 순서)대로만 시도되고(SPEC 7.2 4단계 "오래된 것부터"), 한
  카드가 그 날 하나라도 실패하면 그 카드의 남은 청구서는 건너뛴다. 슬롯
  용량은 `len(초기 issued_unpaid) + horizon_days//7 + 4`(매주 최대 한 장만
  새로 쌓이므로 이 상한을 넘을 일이 거의 없다)로 잡고, 그래도 넘치면
  `_grow_card_capacity` 가 두 배로 늘린다.
- **벡터화 근사(중요, 보고서 참조).** 생성기(`fdt/gen/generator.py`)는
  거래 하나하나를 순서대로 잔액에 반영하지만, SPEC 7.1/7.2 자신이 "포아송은
  `rng.poisson(λ, n_paths)`, 금액은 총 건수만큼 한 번에 뽑는다" 고 벡터화를
  명시적으로 요구한다. 그래서 이 시뮬레이터는 하루·봉투·경로 단위로
  "현금 합계 대 잔액" 을 한 번만 비교한다(그 합계가 부족하면 그 날 그
  봉투의 현금 지출 전부가 억제된다) - 거래를 하나씩 순서대로 판정하는
  생성기보다 거칠지만, SPEC 이 명시한 벡터화 방향과 정확히 같다.
- **CRN(공통 난수).** `rng_main = default_rng(seed)` 가 수입 잡음·소비
  건수/금액·카드-현금 배정·돌발을 전부 뽑고, `rng_inj = default_rng(seed +
  10_007)` 는 주입 전용으로 예약해 둔다. SPEC 8.3 표의 주입 7종은 전부
  **결정론적 금액**(무작위 요소가 없다)이라 현재는 `rng_inj` 를 실제로
  소비하는 경로가 없다 - 그래도 자리를 분리해 두는 이유는 향후 주입에
  무작위 요소가 추가돼도 `rng_main` 의 소비 순서가 흔들리지 않게 하기
  위해서다. `injections` 유무·`overrides` 유무가 `rng_main` 이 소비하는
  난수의 "개수" 자체에 영향을 주는 경우는 딱 하나 남아 있다:
  `BUDGET_CHANGE(behavior_follows=true)` 가 elasticity_gate 문턱을
  바꾸면 그 봉투의 포아송 λ 가 달라지고, 그 결과 그날 뽑는 로그정규 표본
  개수(`total_n`)도 달라진다 - 이건 "예산이 바뀌면 소비 분포 자체가
  바뀐다" 는 SPEC 의 의도된 효과이지 버그가 아니다(§6 설명 참조). 순수
  `SPEND`/`INCOME`/`RECURRING_SPEND`/`EMERGENCY_DRAW`/`FIXED_CHANGE`/
  `EXTERNAL(price_index_mult만)` 주입은 λ 를 전혀 건드리지 않으므로 이
  경우엔 완전히 동일한 순서로 소비된다(테스트로 고정) - 그래서 `SPEND`/
  `RECURRING_SPEND` 주입이 늘리는 지출은 `elasticity_gate` 가 보는 누적치
  (`gate_spent`)에는 절대 합산하지 않고, 출력용 누적치(`injected_spent`,
  둘을 더한 값이 `envelope_spend`)에만 더한다 - 주입 자체가 "그 봉투가
  저잔여 구간에 들어가는 시점" 을 앞당겨 버리면 그 뒤 모든 날짜의 λ 가
  갈라져 `rng_main` 표본 개수가 달라지고, 결국 "주입 유무로 소비 난수
  순서가 안 바뀐다" 는 SPEC 요구를 깨기 때문이다.
"""

from __future__ import annotations

import calendar
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np

from fdt.engine.schemas.behavior import Behavior
from fdt.engine.schemas.input import Externals
from fdt.engine.schemas.request import Injection
from fdt.engine.schemas.simulate import DayEvents, Event, PathStats, PaymentRisk
from fdt.engine.schemas.state import Committed, State
from fdt.engine.taxonomy import ENVELOPE_IDS

__all__ = ["Overrides", "SimulationResult", "simulate"]

_INJECTION_RNG_OFFSET = 10_007
_ENVELOPE_IDS_SORTED: tuple[int, ...] = tuple(sorted(ENVELOPE_IDS.values()))
_YEAR_DAYS = 365.25


# ---------------------------------------------------------------------------
# 날짜 헬퍼 (state.py 의 동명 private 헬퍼와 의도적으로 별개 구현 - 모듈 간
# private 심볼 의존을 피한다. 아주 작은 순수 날짜 계산이라 "생성기 코드
# 복사" 금지와는 무관하다)
# ---------------------------------------------------------------------------


def _clamped_month_date(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def _add_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _first_weekday_on_or_after(d: date, weekday: int) -> date:
    delta = (weekday - d.weekday()) % 7
    return d + timedelta(days=delta)


def _resolve_event_date(on: date | None, days_from_now: int | None, as_of: date) -> date:
    if on is not None:
        return on
    assert days_from_now is not None
    return as_of + timedelta(days=days_from_now)


def _expand_recurring_dates(inj: Any, as_of: date, horizon_end: date) -> list[date]:
    until = min(inj.until, horizon_end) if inj.until is not None else horizon_end
    out: list[date] = []
    if inj.every_days is not None:
        d = inj.start
        step = timedelta(days=inj.every_days)
        while d <= until:
            if as_of < d <= horizon_end:
                out.append(d)
            d += step
        return out

    day_of_month = inj.day_of_month
    year, month = inj.start.year, inj.start.month
    candidate = _clamped_month_date(year, month, day_of_month)
    if candidate < inj.start:
        year, month = _add_month(year, month)
        candidate = _clamped_month_date(year, month, day_of_month)
    while candidate <= until:
        if as_of < candidate <= horizon_end:
            out.append(candidate)
        year, month = _add_month(year, month)
        candidate = _clamped_month_date(year, month, day_of_month)
    return out


# ---------------------------------------------------------------------------
# Overrides (SPEC 7.1)
# ---------------------------------------------------------------------------


@dataclass
class Overrides:
    """시뮬 기간 동안만 적용하는 상태 변경 (SPEC 7.1). 원본 `State` 는
    건드리지 않는다 - `simulate()` 는 이 필드들을 지역 변수/배열로만
    읽는다.
    """

    budgets: dict[int, int] | None = None
    cancel_committed: set[int] | None = None
    committed_amount_override: dict[int, int] | None = None
    externals: Externals | None = None
    card_withdrawal_weekday: dict[int, int] | None = None


# ---------------------------------------------------------------------------
# SimulationResult (SPEC 7.3)
# ---------------------------------------------------------------------------


@dataclass
class SimulationResult:
    """`simulate()` 의 반환값 (SPEC 7.3).

    ndarray 를 직접 들고 있어 pydantic 모델이 아니다(JSON 직렬화가 필요한
    조각은 `stats()`/`payment_risks()` 가 `fdt.engine.schemas.simulate` 의
    pydantic 모델로 변환해 돌려준다).
    """

    as_of: date
    dates: list[date]
    balances: np.ndarray  # int64 (n_paths, horizon_days+1)
    economic: np.ndarray  # int64 (n_paths, horizon_days+1)
    envelope_spend: np.ndarray  # int64 (n_paths, n_env, horizon_days+1)
    envelope_ids: list[int]
    envelope_budgets: dict[int, int]
    any_shortfall: np.ndarray  # bool (n_paths,)
    card_shortfall: np.ndarray  # bool (n_paths,)
    first_shortfall_idx: np.ndarray  # int64 (n_paths,), -1 = 없음
    event_log: list[DayEvents]
    first_exhaust_idx: np.ndarray  # int64 (n_paths, n_env), -1 = 없음
    payment_records: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def stats(self, economic: bool = False) -> PathStats:
        """SPEC 7.3 `stats(economic=False) -> PathStats`."""

        arr = self.economic if economic else self.balances
        n_paths = arr.shape[0]

        median = np.median(arr, axis=0)
        p10 = np.percentile(arr, 10, axis=0)
        p90 = np.percentile(arr, 90, axis=0)
        mean = arr.mean(axis=0)

        min_idx = int(np.argmin(median))
        min_balance = round(float(median[min_idx]))
        min_balance_date = self.dates[min_idx]
        end_balance_median = round(float(median[-1]))

        shortfall_prob = float(self.any_shortfall.mean()) if n_paths else 0.0
        card_shortfall_prob = float(self.card_shortfall.mean()) if n_paths else 0.0

        valid_first = self.first_shortfall_idx[self.first_shortfall_idx >= 0]
        first_shortfall_date_median: date | None = None
        if len(valid_first) * 2 >= n_paths and len(valid_first) > 0:
            idx = round(float(np.median(valid_first)))
            first_shortfall_date_median = self.dates[idx]

        env_spend_median: dict[int, int] = {}
        env_overrun_prob: dict[int, float] = {}
        env_exhaust_date: dict[int, date | None] = {}
        for i, eid in enumerate(self.envelope_ids):
            env_spend_median[eid] = round(float(np.median(self.envelope_spend[:, i, -1])))
            exhaust_col = self.first_exhaust_idx[:, i]
            valid = exhaust_col[exhaust_col >= 0]
            env_overrun_prob[eid] = float((exhaust_col >= 0).mean()) if n_paths else 0.0
            if len(valid) * 2 >= n_paths and len(valid) > 0:
                idx = round(float(np.median(valid)))
                env_exhaust_date[eid] = self.dates[idx]
            else:
                env_exhaust_date[eid] = None

        return PathStats(
            dates=self.dates,
            median=[round(float(v)) for v in median],
            p10=[round(float(v)) for v in p10],
            p90=[round(float(v)) for v in p90],
            mean=[float(v) for v in mean],
            min_balance=min_balance,
            min_balance_date=min_balance_date,
            end_balance_median=end_balance_median,
            shortfall_prob=shortfall_prob,
            card_shortfall_prob=card_shortfall_prob,
            first_shortfall_date_median=first_shortfall_date_median,
            envelope_spend_median=env_spend_median,
            envelope_overrun_prob=env_overrun_prob,
            envelope_exhaust_date_median=env_exhaust_date,
        )

    def payment_risks(self) -> list[PaymentRisk]:
        """SPEC 7.3 `payment_risks() -> list[PaymentRisk]`."""

        return [
            PaymentRisk(
                due=r["due"],
                kind=r["kind"],
                name=r["name"],
                amount=r["amount"],
                fail_prob=r["fail_prob"],
                median_balance_before=r["median_balance_before"],
                source_fixed_expense_id=r.get("source_fixed_expense_id"),
                source_loan_id=r.get("source_loan_id"),
                source_card_id=r.get("source_card_id"),
            )
            for r in self.payment_records
        ]


# ---------------------------------------------------------------------------
# simulate() (SPEC 7.1, 7.2)
# ---------------------------------------------------------------------------


def simulate(
    state: State,
    behavior: Behavior,
    externals: Externals,
    *,
    horizon_days: int = 30,
    n_paths: int = 1000,
    seed: int = 42,
    injections: Sequence[Injection] = (),
    overrides: Overrides | None = None,
    committed: list[Committed] | None = None,
) -> SimulationResult:
    """SPEC 7.1 시그니처. `committed` 가 `None` 이면 `state.committed` 를
    쓴다(SPEC 5.1 은 `as_of+90` 까지만 채운다 - `horizon_days > 90` 요청은
    호출자가 `build_committed_queue(horizon_cap=horizon_days+7)` 로 큐를
    다시 만들어 넘겨야 한다, SPEC 7.1/S42. 이 함수 자신은 큐를 다시 만들지
    않는다)."""

    as_of = state.as_of
    rng_main = np.random.default_rng(seed)
    rng_inj = np.random.default_rng(seed + _INJECTION_RNG_OFFSET)  # noqa: F841 (예약, docstring 참조)

    ov = overrides or Overrides()
    eff_externals = ov.externals or externals
    budgets_map: dict[int, int] = dict(ov.budgets or {})
    cancel_set: set[int] = set(ov.cancel_committed or ())
    amount_override_map: dict[int, int] = dict(ov.committed_amount_override or {})
    card_weekday_override: dict[int, int] = dict(ov.card_withdrawal_weekday or {})

    # `FixedChangeInjection.from_` 는 스키마상 `date | None` 이지만
    # `_check_change` 검증기가 항상 값을 요구하므로 실제로는 None 이 될 수
    # 없다(SPEC 8.3 S8: "from(적용 시작일) 필수").
    fixed_change: dict[int, tuple[date | None, int | None, bool]] = {}
    day_spend: dict[date, list[tuple[int, int, str]]] = {}
    day_income: dict[date, list[int]] = {}
    day_emergency_draw: dict[date, list[int]] = {}
    horizon_end = as_of + timedelta(days=horizon_days)

    for inj in injections:
        # mypy 는 판별 필드(`inj.type`)를 직접 비교할 때만 유니온을 좁힌다
        # (중간 변수에 복사하면 좁혀지지 않는다) - 그래서 각 분기가
        # `inj.type ==` 를 직접 쓴다.
        if inj.type == "BUDGET_CHANGE":
            if inj.behavior_follows:
                budgets_map[inj.envelope_id] = inj.new_budget
        elif inj.type == "FIXED_CHANGE":
            fixed_change[inj.fixed_expense_id] = (inj.from_, inj.new_amount, inj.cancel)
        elif inj.type == "EXTERNAL":
            updates: dict[str, Any] = {}
            if inj.price_index_mult is not None:
                updates["price_index_mult"] = inj.price_index_mult
            if inj.loan_rate_delta_bp is not None:
                updates["loan_rate_delta_bp"] = inj.loan_rate_delta_bp
            if inj.income_growth_pct is not None:
                updates["income_growth_pct"] = inj.income_growth_pct
            eff_externals = eff_externals.model_copy(update=updates)
        elif inj.type == "SPEND":
            d = _resolve_event_date(inj.on, inj.days_from_now, as_of)
            day_spend.setdefault(d, []).append((inj.envelope_id, inj.amount, inj.method))
        elif inj.type == "INCOME":
            d = _resolve_event_date(inj.on, inj.days_from_now, as_of)
            day_income.setdefault(d, []).append(inj.amount)
        elif inj.type == "RECURRING_SPEND":
            for d in _expand_recurring_dates(inj, as_of, horizon_end):
                day_spend.setdefault(d, []).append((inj.envelope_id, inj.amount, inj.method))
        elif inj.type == "EMERGENCY_DRAW":
            d = _resolve_event_date(inj.on, inj.days_from_now, as_of)
            day_emergency_draw.setdefault(d, []).append(inj.amount)

    # -- 약정 큐를 일자별 스케줄로 (CARD_BILL 은 제외 - 모듈 docstring 참조) --
    committed_items = committed if committed is not None else list(state.committed)
    committed_by_date: dict[date, list[Committed]] = {}
    for item in committed_items:
        if item.kind == "CARD_BILL":
            continue
        fx_id = item.source_fixed_expense_id
        amount = item.amount
        if fx_id is not None and fx_id in cancel_set:
            continue
        if fx_id is not None and fx_id in amount_override_map:
            amount = amount_override_map[fx_id]
        if fx_id is not None and fx_id in fixed_change:
            from_date, new_amount, cancel = fixed_change[fx_id]
            assert from_date is not None  # 검증기가 보장(위 주석 참조)
            if item.due >= from_date:
                if cancel:
                    continue
                if new_amount is not None:
                    amount = new_amount
        if amount != item.amount:
            item = item.model_copy(update={"amount": amount})
        committed_by_date.setdefault(item.due, []).append(item)

    # -- 봉투 파라미터 --------------------------------------------------
    env_ids = list(_ENVELOPE_IDS_SORTED)
    env_index = {eid: i for i, eid in enumerate(env_ids)}
    n_env = len(env_ids)

    beh_by_env = {eb.envelope_id: eb for eb in behavior.envelopes}
    daily_rate = np.array([beh_by_env[e].daily_rate for e in env_ids], dtype=np.float64)
    weekday_mult = np.array([beh_by_env[e].weekday_mult for e in env_ids], dtype=np.float64)
    amount_mu = np.array([beh_by_env[e].amount_mu for e in env_ids], dtype=np.float64)
    amount_sigma = np.array([beh_by_env[e].amount_sigma for e in env_ids], dtype=np.float64)
    card_share = np.array([beh_by_env[e].card_share for e in env_ids], dtype=np.float64)
    elasticity = np.array([beh_by_env[e].elasticity for e in env_ids], dtype=np.float64)
    avg_card_share = float(card_share.mean()) if n_env else 0.0

    state_env_by_id = {es.envelope_id: es for es in state.envelopes}
    budget_arr = np.array(
        [budgets_map.get(e, state_env_by_id[e].budget) for e in env_ids], dtype=np.int64
    )
    spent_init = np.array([state_env_by_id[e].spent for e in env_ids], dtype=np.int64)

    # -- 수입 일정 (SPEC 5.1 income, 6장 payday_boost/pre_payday_damp) ---
    income = state.income
    income_anchor_day = income.next_date.day if income.next_date is not None else None
    next_income_date = income.next_date
    last_income_date: date | None = None
    if income.next_date is not None and income.median_gap_days is not None:
        last_income_date = income.next_date - timedelta(days=income.median_gap_days)

    payday_boost = behavior.payday_boost
    pre_payday_damp = behavior.pre_payday_damp
    shock_prob = behavior.shock.daily_prob
    shock_mu = behavior.shock.mu
    shock_sigma = behavior.shock.sigma
    price_index_mult = eff_externals.price_index_mult
    income_growth_pct = eff_externals.income_growth_pct

    # -- 카드 상태 --------------------------------------------------------
    cards = list(state.cards)
    n_cards = len(cards)
    card_id_to_idx = {c.id: i for i, c in enumerate(cards)}
    card_weekday = [card_weekday_override.get(c.id, c.withdrawal_weekday) for c in cards]
    unbilled = [np.full(n_paths, c.unbilled, dtype=np.int64) for c in cards]

    pending_amt: list[np.ndarray] = []
    pending_due: list[np.ndarray] = []
    pending_count: list[np.ndarray] = []
    pending_cap: list[int] = []
    for ci, c in enumerate(cards):
        issued_sorted = sorted(c.issued_unpaid, key=lambda b: b.billing_date)
        cap = max(4, len(issued_sorted) + horizon_days // 7 + 4)
        amt = np.zeros((n_paths, cap), dtype=np.int64)
        due = np.zeros((n_paths, cap), dtype=np.int64)
        cnt = np.full(n_paths, len(issued_sorted), dtype=np.int64)
        for i, billing in enumerate(issued_sorted):
            first_due = _first_weekday_on_or_after(billing.billing_date, card_weekday[ci])
            amt[:, i] = billing.amount
            due[:, i] = first_due.toordinal()
        pending_amt.append(amt)
        pending_due.append(due)
        pending_count.append(cnt)
        pending_cap.append(cap)

    def _grow_card_capacity(ci: int) -> None:
        old_cap = pending_cap[ci]
        new_cap = old_cap * 2
        new_amt = np.zeros((n_paths, new_cap), dtype=np.int64)
        new_due = np.zeros((n_paths, new_cap), dtype=np.int64)
        new_amt[:, :old_cap] = pending_amt[ci]
        new_due[:, :old_cap] = pending_due[ci]
        pending_amt[ci] = new_amt
        pending_due[ci] = new_due
        pending_cap[ci] = new_cap

    def _issued_unpaid_sum() -> np.ndarray:
        total = np.zeros(n_paths, dtype=np.int64)
        for ci in range(n_cards):
            col_idx = np.arange(pending_cap[ci])
            mask = col_idx[None, :] < pending_count[ci][:, None]
            total += (pending_amt[ci] * mask).sum(axis=1)
        return total

    # -- 상태 배열 --------------------------------------------------------
    dates = [as_of + timedelta(days=k) for k in range(horizon_days + 1)]
    balances = np.zeros((n_paths, horizon_days + 1), dtype=np.int64)
    economic = np.zeros((n_paths, horizon_days + 1), dtype=np.int64)
    envelope_spend = np.zeros((n_paths, n_env, horizon_days + 1), dtype=np.int64)

    liquidity = np.full(n_paths, state.liquidity, dtype=np.int64)
    emergency_fund = np.full(n_paths, state.emergency_fund, dtype=np.int64)
    gate_spent = np.tile(spent_init, (n_paths, 1)).astype(np.int64)
    # 주입(SPEND/RECURRING_SPEND) 이 늘리는 지출은 여기(injected_spent)
    # 에만 쌓고 gate_spent 에는 절대 반영하지 않는다 - elasticity_gate 는
    # gate_spent 만 보므로, 주입이 있고 없고에 따라 이후 날짜의 lambda
    # (그리고 rng_main 이 뽑는 표본 개수)가 달라지지 않는다(SPEC "주입
    # 유무로 소비 난수 소비 순서가 바뀌면 안 된다"). envelope_spend(출력)
    # 에는 두 값의 합을 기록해 그 봉투의 실제(가정 포함) 지출을 보여준다.
    injected_spent = np.zeros((n_paths, n_env), dtype=np.int64)

    unpaid_obligation_cum = np.zeros(n_paths, dtype=np.int64)
    suppressed_demand_cum = np.zeros(n_paths, dtype=np.int64)

    any_shortfall = np.zeros(n_paths, dtype=bool)
    first_shortfall_idx = np.full(n_paths, -1, dtype=np.int64)
    card_shortfall = np.zeros(n_paths, dtype=bool)
    first_exhaust_idx = np.full((n_paths, n_env), -1, dtype=np.int64)

    events_by_day: dict[int, list[Event]] = {}
    payment_records: list[dict[str, Any]] = []
    pending_bill_records: list[dict[str, Any]] = []

    balances[:, 0] = liquidity
    economic[:, 0] = (
        liquidity - _issued_unpaid_sum() - unpaid_obligation_cum - suppressed_demand_cum
    )
    envelope_spend[:, :, 0] = gate_spent + injected_spent

    for k in range(1, horizon_days + 1):
        d = dates[k]
        d_ord = d.toordinal()
        day_events: list[Event] = []

        if d.day == 1:
            gate_spent[:, :] = 0
            injected_spent[:, :] = 0

        # 1. 수입 -------------------------------------------------------
        if next_income_date is not None and d == next_income_date:
            years_elapsed = (d - as_of).days / _YEAR_DAYS
            growth_mult = (1.0 + income_growth_pct) ** years_elapsed
            if income.irregular:
                noise = rng_main.lognormal(mean=0.0, sigma=0.4, size=n_paths)
                amount_paths = np.round(income.expected * growth_mult * noise).astype(np.int64)
            else:
                scalar_amount = round(income.expected * growth_mult)
                amount_paths = np.full(n_paths, scalar_amount, dtype=np.int64)
            liquidity += amount_paths
            last_income_date = d
            day_events.append(
                Event(
                    kind="INCOME",
                    name="수입",
                    amount=round(float(np.median(amount_paths))),
                    success_ratio=1.0,
                )
            )
            if income.irregular and income.median_gap_days is not None:
                next_income_date = d + timedelta(days=income.median_gap_days)
            elif income_anchor_day is not None:
                y, m = _add_month(d.year, d.month)
                next_income_date = _clamped_month_date(y, m, income_anchor_day)
            else:
                next_income_date = None

        # 2. 고정비/SELF_TRANSFER (CARD_BILL 은 카드 자체 로직에서 처리) --
        for item in committed_by_date.get(d, []):
            if item.kind == "SELF_TRANSFER":
                mask = liquidity >= item.amount
                liquidity[mask] -= item.amount
                emergency_fund[mask] += item.amount
                sr = float(mask.mean()) if n_paths else 1.0
            elif item.card_id is not None:
                item_card_idx = card_id_to_idx.get(item.card_id)
                if item_card_idx is not None:
                    unbilled[item_card_idx] += item.amount
                mask = np.ones(n_paths, dtype=bool)
                sr = 1.0
            else:
                mask = liquidity >= item.amount
                liquidity[mask] -= item.amount
                unpaid_obligation_cum[~mask] += item.amount
                sr = float(mask.mean()) if n_paths else 1.0
            day_events.append(
                Event(
                    kind=item.kind,
                    name=item.name,
                    amount=item.amount,
                    success_ratio=sr,
                    source_fixed_expense_id=item.source_fixed_expense_id,
                    source_loan_id=item.source_loan_id,
                    source_card_id=item.source_card_id,
                )
            )
            payment_records.append(
                {
                    "due": d,
                    "kind": item.kind,
                    "name": item.name,
                    "amount": item.amount,
                    "fail_prob": 1.0 - sr,
                    "median_balance_before": round(float(np.median(balances[:, k - 1]))),
                    "source_fixed_expense_id": item.source_fixed_expense_id,
                    "source_loan_id": item.source_loan_id,
                    "source_card_id": item.source_card_id,
                }
            )

        # 3. 청구 발행 (월요일) ------------------------------------------
        if d.weekday() == 0:
            for ci, card in enumerate(cards):
                has_bill = unbilled[ci] > 0
                if has_bill.any():
                    while (pending_count[ci] + has_bill.astype(np.int64)).max() > pending_cap[ci]:
                        _grow_card_capacity(ci)
                    rows = np.nonzero(has_bill)[0]
                    cols = pending_count[ci][rows]
                    pending_amt[ci][rows, cols] = unbilled[ci][rows]
                    first_due = _first_weekday_on_or_after(d, card_weekday[ci])
                    pending_due[ci][rows, cols] = first_due.toordinal()
                    pending_count[ci][rows] = cols + 1
                    pending_bill_records.append(
                        {
                            "card_id": card.id,
                            "name": f"카드 {card.id} 대금",
                            "due": first_due,
                            "amounts": unbilled[ci].copy(),
                            "has_bill": has_bill.copy(),
                        }
                    )
                unbilled[ci][:] = 0

        # 4. 카드 출금 (예정 출금일 이후 매일 재시도, 실패 시 그 카드 중단) --
        for ci, card in enumerate(cards):
            failed_today = np.zeros(n_paths, dtype=bool)
            attempted_today = np.zeros(n_paths, dtype=bool)
            attempted_amt = np.zeros(n_paths, dtype=np.int64)
            for _pass in range(pending_cap[ci] + 1):
                cnt = pending_count[ci]
                active = cnt > 0
                if not active.any():
                    break
                due0 = pending_due[ci][:, 0]
                amt0 = pending_amt[ci][:, 0]
                attempt = active & (due0 <= d_ord) & (~failed_today)
                if not attempt.any():
                    break
                # amt0 는 이번 패스에서 시도되는 금액의 스냅샷이다 - 지불 후
                # 배열을 왼쪽으로 밀면(shift) slot0 값이 바뀌므로, 로깅용
                # 금액은 밀기 전에 여기서 기록해 둔다.
                attempted_amt[attempt] = amt0[attempt]
                attempted_today |= attempt
                afford = liquidity >= amt0
                pay_mask = attempt & afford
                fail_mask = attempt & ~afford
                if pay_mask.any():
                    liquidity[pay_mask] -= amt0[pay_mask]
                    pending_amt[ci][pay_mask, :-1] = pending_amt[ci][pay_mask, 1:]
                    pending_amt[ci][pay_mask, -1] = 0
                    pending_due[ci][pay_mask, :-1] = pending_due[ci][pay_mask, 1:]
                    pending_due[ci][pay_mask, -1] = 0
                    pending_count[ci][pay_mask] -= 1
                if fail_mask.any():
                    failed_today |= fail_mask
                    card_shortfall[fail_mask] = True
                if not pay_mask.any():
                    break
            if attempted_today.any():
                sr = float((attempted_today & ~failed_today).sum() / attempted_today.sum())
                day_events.append(
                    Event(
                        kind="CARD_BILL",
                        name=f"카드 {card.id} 대금 출금",
                        amount=round(float(np.median(attempted_amt[attempted_today]))),
                        success_ratio=sr,
                        source_card_id=card.id,
                    )
                )

            resolved = [
                r for r in pending_bill_records if r["card_id"] == card.id and r["due"] == d
            ]
            for r in resolved:
                still_present = (pending_due[ci] == d_ord).any(axis=1)
                has_bill_mask = r["has_bill"]
                n_has = int(has_bill_mask.sum())
                fail_mask_r = still_present & has_bill_mask
                fail_prob = float(fail_mask_r.sum() / n_has) if n_has else 0.0
                amount_repr = round(float(np.median(r["amounts"][has_bill_mask]))) if n_has else 0
                payment_records.append(
                    {
                        "due": d,
                        "kind": "CARD_BILL",
                        "name": r["name"],
                        "amount": amount_repr,
                        "fail_prob": fail_prob,
                        "median_balance_before": round(float(np.median(balances[:, k - 1]))),
                        "source_card_id": r["card_id"],
                    }
                )
            if resolved:
                pending_bill_records = [
                    r
                    for r in pending_bill_records
                    if not (r["card_id"] == card.id and r["due"] == d)
                ]

        # 5. 소비 --------------------------------------------------------
        weekday = d.weekday()
        boost = 1.0
        if last_income_date is not None and 0 <= (d - last_income_date).days <= 6:
            boost *= payday_boost
        if next_income_date is not None and 1 <= (next_income_date - d).days <= 5:
            boost *= pre_payday_damp

        budget_f = np.where(budget_arr > 0, budget_arr, 1).astype(np.float64)
        remaining_ratio = 1.0 - gate_spent.astype(np.float64) / budget_f[None, :]
        gate = np.where(remaining_ratio < 0.2, elasticity[None, :], 1.0)
        gate[:, budget_arr <= 0] = 1.0

        for ei, _eid in enumerate(env_ids):
            lam = np.clip(
                daily_rate[ei] * weekday_mult[ei, weekday] * boost * gate[:, ei], 0.0, None
            )
            n_events = rng_main.poisson(lam)
            total_n = int(n_events.sum())
            if total_n > 0:
                path_index = np.repeat(np.arange(n_paths), n_events)
                raw_amounts = rng_main.lognormal(
                    mean=amount_mu[ei], sigma=amount_sigma[ei], size=total_n
                )
                amounts = (np.round(raw_amounts * price_index_mult / 100.0) * 100).astype(np.int64)
                via_card = rng_main.random(total_n) < card_share[ei]

                if n_cards == 0:
                    cash_total = np.bincount(
                        path_index, weights=amounts, minlength=n_paths
                    ).astype(np.int64)
                else:
                    cash_amt = np.where(via_card, 0, amounts)
                    cash_total = np.bincount(
                        path_index, weights=cash_amt, minlength=n_paths
                    ).astype(np.int64)
                    if n_cards == 1:
                        card_total = np.bincount(
                            path_index, weights=np.where(via_card, amounts, 0), minlength=n_paths
                        ).astype(np.int64)
                        unbilled[0] += card_total
                    else:
                        card_tx_count = int(via_card.sum())
                        if card_tx_count > 0:
                            card_choice = rng_main.integers(0, n_cards, size=card_tx_count)
                            card_path_idx = path_index[via_card]
                            card_amounts = amounts[via_card]
                            for c_i in range(n_cards):
                                sel = card_choice == c_i
                                if sel.any():
                                    unbilled[c_i] += np.bincount(
                                        card_path_idx[sel],
                                        weights=card_amounts[sel],
                                        minlength=n_paths,
                                    ).astype(np.int64)

                needs_cash = cash_total > 0
                afford = liquidity >= cash_total
                pay_mask = needs_cash & afford
                fail_mask = needs_cash & ~afford
                liquidity[pay_mask] -= cash_total[pay_mask]
                suppressed_demand_cum[fail_mask] += cash_total[fail_mask]

                card_success_total = np.zeros(n_paths, dtype=np.int64)
                if n_cards > 0:
                    card_success_total = np.bincount(
                        path_index, weights=np.where(via_card, amounts, 0), minlength=n_paths
                    ).astype(np.int64)
                successful = np.where(pay_mask, cash_total, 0) + card_success_total
                gate_spent[:, ei] += successful

            envelope_spend[:, ei, k] = gate_spent[:, ei] + injected_spent[:, ei]
            newly_exhausted = (envelope_spend[:, ei, k] >= budget_arr[ei]) & (
                first_exhaust_idx[:, ei] < 0
            )
            first_exhaust_idx[newly_exhausted, ei] = k

        # 6. 돌발 ----------------------------------------------------------
        other_idx = env_index.get(7)
        if shock_prob > 0 and other_idx is not None:
            hit_mask = rng_main.random(n_paths) < shock_prob
            hit_count = int(hit_mask.sum())
            if hit_count > 0:
                raw = rng_main.lognormal(mean=shock_mu, sigma=shock_sigma, size=hit_count)
                shock_amounts = (np.round(raw / 100.0) * 100).astype(np.int64)
                via_card = rng_main.random(hit_count) < avg_card_share
                hit_paths = np.nonzero(hit_mask)[0]

                cash_total = np.zeros(n_paths, dtype=np.int64)
                cash_total[hit_paths] = np.where(via_card, 0, shock_amounts)
                if n_cards > 0:
                    card_total = np.zeros(n_paths, dtype=np.int64)
                    card_total[hit_paths] = np.where(via_card, shock_amounts, 0)
                    if n_cards == 1:
                        unbilled[0] += card_total
                    else:
                        card_hit = hit_paths[via_card]
                        card_amt = shock_amounts[via_card]
                        if len(card_hit) > 0:
                            choice = rng_main.integers(0, n_cards, size=len(card_hit))
                            for c_i in range(n_cards):
                                sel = choice == c_i
                                if sel.any():
                                    unbilled[c_i][card_hit[sel]] += card_amt[sel]
                else:
                    cash_total[hit_paths] = shock_amounts

                needs_cash = cash_total > 0
                afford = liquidity >= cash_total
                pay_mask = needs_cash & afford
                fail_mask = needs_cash & ~afford
                liquidity[pay_mask] -= cash_total[pay_mask]
                suppressed_demand_cum[fail_mask] += cash_total[fail_mask]

                card_success = np.zeros(n_paths, dtype=np.int64)
                card_success[hit_paths] = np.where(via_card, shock_amounts, 0)
                successful = np.where(pay_mask, cash_total, 0) + card_success
                gate_spent[:, other_idx] += successful
                envelope_spend[:, other_idx, k] = (
                    gate_spent[:, other_idx] + injected_spent[:, other_idx]
                )
                newly_exhausted = (
                    envelope_spend[:, other_idx, k] >= budget_arr[other_idx]
                ) & (first_exhaust_idx[:, other_idx] < 0)
                first_exhaust_idx[newly_exhausted, other_idx] = k

        # 7. 주입 -----------------------------------------------------------
        for income_amt in day_income.get(d, []):
            liquidity += income_amt
            day_events.append(
                Event(kind="INCOME", name="주입 수입", amount=income_amt, success_ratio=1.0)
            )

        for draw_amt in day_emergency_draw.get(d, []):
            drawn = np.minimum(draw_amt, emergency_fund)
            liquidity += drawn
            emergency_fund -= drawn
            day_events.append(
                Event(kind="EMERGENCY_DRAW", name="비상금 인출", amount=draw_amt, success_ratio=1.0)
            )

        for envelope_id, spend_amount, method in day_spend.get(d, []):
            ei = env_index[envelope_id]
            if method == "CARD" and n_cards > 0:
                unbilled[0] += spend_amount
                injected_spent[:, ei] += spend_amount
                envelope_spend[:, ei, k] = gate_spent[:, ei] + injected_spent[:, ei]
                day_events.append(
                    Event(kind="SPEND", name="주입 소비", amount=spend_amount, success_ratio=1.0)
                )
            else:
                # 정규 소비(5단계)는 봉투·하루 단위 "합계 대 잔액" 전부-또는-
                # 전무 판정을 쓰지만(모듈 docstring "벡터화 근사" 참조), 주입은
                # 단 하나의 확정 이벤트다. 여기서 전부-또는-전무를 쓰면 금액을
                # 늘렸을 때 "감당 못 해서 오히려 아무 일도 안 일어나는" 경우가
                # 생겨 분기 최저 잔액이 더 높아질 수 있다 - SPEC 8.3.1 이 요구하는
                # "지출 주입 ≥ 0 이면 분기 최저 ≤ 기준 최저" 불변식을 깬다. 그래서
                # 감당 가능한 만큼만 부분 체결(partial fill)하고 나머지만
                # suppressed_demand 로 넘긴다 - `liquidity` 는 절대 음수가 되지
                # 않으므로(다른 모든 단계와 동일한 불변식) `min(amount, liquidity)`
                # 는 금액이 커질수록 단조 비감소하지 않는다(오히려 그 반대인
                # `liquidity - paid` 가 단조 비증가).
                paid = np.minimum(spend_amount, liquidity)
                liquidity -= paid
                suppressed_demand_cum += spend_amount - paid
                injected_spent[:, ei] += paid
                envelope_spend[:, ei, k] = gate_spent[:, ei] + injected_spent[:, ei]
                sr = float((paid == spend_amount).mean()) if n_paths else 1.0
                day_events.append(
                    Event(kind="SPEND", name="주입 소비", amount=spend_amount, success_ratio=sr)
                )
            newly_exhausted = (envelope_spend[:, ei, k] >= budget_arr[ei]) & (
                first_exhaust_idx[:, ei] < 0
            )
            first_exhaust_idx[newly_exhausted, ei] = k

        # 8. 기록 ------------------------------------------------------------
        if day_events:
            events_by_day[k] = day_events
        balances[:, k] = liquidity
        economic[:, k] = (
            liquidity - _issued_unpaid_sum() - unpaid_obligation_cum - suppressed_demand_cum
        )
        # W7 최소 수정(오케스트레이터 결정, SPEC 7.2 8단계 "liquidity < 0 ->
        # any_shortfall"의 실제 의미): `liquidity`(실제 잔액)는 모든 단계가
        # "감당 못 하면 거절" 로 게이트돼 있어 구조적으로 절대 음수가 되지
        # 않는다(W6 조사 노트, tests/unit/test_simulate.py 의
        # test_profile_stats_invariants 주석 참조) - 그래서 `liquidity < 0`
        # 를 그대로 쓰면 `shortfall_prob` 이 항상 0에 수렴해 RISK/FORECAST
        # 어디에도 못 쓴다. SPEC 8.5 는 애초에 "부족"을 경제 잔액(청구서·
        # 미납·억제 수요까지 반영한 잠재 부족)으로 정의하므로, 여기서는
        # `economic`(이미 위에서 계산)을 판정 기준으로 쓴다.
        newly_short = (economic[:, k] < 0) & (~any_shortfall)
        first_shortfall_idx[newly_short] = k
        any_shortfall |= economic[:, k] < 0

    event_log = [DayEvents(date=dates[k], events=events_by_day[k]) for k in sorted(events_by_day)]

    return SimulationResult(
        as_of=as_of,
        dates=dates,
        balances=balances,
        economic=economic,
        envelope_spend=envelope_spend,
        envelope_ids=env_ids,
        envelope_budgets={eid: int(budget_arr[env_index[eid]]) for eid in env_ids},
        any_shortfall=any_shortfall,
        card_shortfall=card_shortfall,
        first_shortfall_idx=first_shortfall_idx,
        event_log=event_log,
        first_exhaust_idx=first_exhaust_idx,
        payment_records=payment_records,
    )
