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
- **벡터화 근사, 부분 체결(리뷰 B2/S46 수정 반영).** 생성기
  (`fdt/gen/generator.py`)는 거래 하나하나를 순서대로 잔액에 반영하지만,
  SPEC 7.1/7.2 자신이 "포아송은 `rng.poisson(λ, n_paths)`, 금액은 총
  건수만큼 한 번에 뽑는다" 고 벡터화를 명시적으로 요구한다. 그래서 이
  시뮬레이터는 하루·봉투·경로 단위로 현금 지출 합계를 한 번에 계산하되,
  그 합계를 잔액에 **부분 체결**한다(`paid = min(cash_total, liquidity)`,
  나머지는 `suppressed_demand`) - 거래를 하나씩 순서대로 판정하는 생성기와
  결과가 완전히 같지는 않지만, "감당하는 만큼만 나가고 나머지만 억제된다"
  는 성질은 같다. 이전 버전은 그 합계가 조금이라도 잔액을 넘으면 그 날 그
  봉투의 현금 지출 **전부**를 억제했는데(전부-또는-전무), 이는 SPEC 이
  명시한 것은 벡터화 "방향" 이지 "판정 입도" 가 아니었다 - 실측상 C 프로필
  (현금 지출이 잔액 대비 상시 빠듯한 프로필) 백테스트 sMAPE 를 기준 초과로
  악화시켰다(리뷰 B2). 주입 경로(아래 "7. 주입" 참조)는 처음부터 이
  부분 체결 방식을 썼다 - 이번 수정으로 정규 소비(5단계)·돌발(6단계)도
  같은 규칙으로 통일했다.
- **CRN(공통 난수) - 실제로 성립하는 것과 안 하는 것 (N6, 정직하게 다시
  적음).** `rng_main = default_rng(seed)` 가 수입 잡음·소비 건수/금액·
  카드-현금 배정·돌발을 전부 뽑고, `rng_inj = default_rng(seed + 10_007)`
  는 주입 전용으로 예약해 둔다(SPEC 8.3 주입 7종이 전부 결정론적 금액이라
  현재는 실제로 소비되지 않지만, 향후 주입에 무작위 요소가 생겨도
  `rng_main` 소비 순서가 흔들리지 않도록 자리를 분리해 둔다). **확실히
  성립하는 것**: `injections`·`overrides` 가 전혀 없으면 두 번의 `simulate()`
  호출은 바이트 단위로 동일하다(테스트로 고정, `whatif.py` 의 CRN 브랜치가
  이것에 의존한다). **성립하지 않는 것**: "순수 SPEND/INCOME/RECURRING_
  SPEND/EMERGENCY_DRAW 주입은 이후 소비 난수 소비 순서를 전혀 안 바꾼다"
  는 이전 버전 docstring의 주장은 거짓이었다(리뷰 W6 4a 실측) -
  `SPEND`/`RECURRING_SPEND` 주입이 늘리는 지출은 `elasticity_gate` 가
  보는 누적치(`gate_spent`)에는 합산하지 않지만(`injected_spent`에만
  더함, 아래), `INCOME`/`EMERGENCY_DRAW`/`SPEND` 주입은 모두 `liquidity`
  자체를 바꾸고, `liquidity` 는 5단계 정규 소비의 현금 부분 체결
  (`paid = min(cash_total, liquidity)`)이 매일 참조하는 공유 상태다 -
  그래서 주입이 있으면 이후 날짜 정규 소비의 `paid`(따라서 `gate_spent`,
  `remaining_ratio`, `gate`, λ, 그날 뽑는 로그정규 표본 개수)가 주입 없는
  분기와 달라질 수 있다. 이 어긋남은 봉투 현금 지출이 잔액 대비 빠듯한
  프로필(B·C)에서만 관측되고(A·D 는 무해), 그 근본 해결(주입이 `paid` 에
  영향을 주지 않게 하려면 정규 소비와 주입을 완전히 분리된 잔액으로
  추적해야 한다)은 이번 수정 범위 밖이다(S46 이후 과제). `BUDGET_CHANGE
  (behavior_follows=true)` 가 elasticity_gate 문턱을 바꿔 λ 가 달라지는
  것은 "예산이 바뀌면 소비 분포 자체가 바뀐다" 는 SPEC 의 의도된 효과다
  (§6 설명 참조, 버그 아님).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

import numpy as np

from fdt.engine._dateutil import add_months, clamped_month_date
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
# 날짜 헬퍼 (리뷰 N10: `_clamped_month_date`/`_add_month` 사본을 공용
# `fdt/engine/_dateutil.py`(J2) 로 교체했다. `_next_month` 만 이 모듈에 남긴다
# - `add_months(d, n)` 는 `d.day` 를 앵커로 쓰므로, "day_of_month 를 고정하고
# 월만 넘긴다" 패턴에는 매번 day=1 인 날짜로 호출해야 앵커 일자 드리프트가
# 없다(1일은 모든 달에 유효해 클램프가 절대 일어나지 않는다).)
# ---------------------------------------------------------------------------


def _next_month(year: int, month: int) -> tuple[int, int]:
    nxt = add_months(date(year, month, 1), 1)
    return nxt.year, nxt.month


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
    candidate = clamped_month_date(year, month, day_of_month)
    if candidate < inj.start:
        year, month = _next_month(year, month)
        candidate = clamped_month_date(year, month, day_of_month)
    while candidate <= until:
        if as_of < candidate <= horizon_end:
            out.append(candidate)
        year, month = _next_month(year, month)
        candidate = clamped_month_date(year, month, day_of_month)
    return out


# ---------------------------------------------------------------------------
# Overrides (SPEC 7.1)
# ---------------------------------------------------------------------------


@dataclass
class Overrides:
    """시뮬 기간 동안만 적용하는 상태 변경 (SPEC 7.1). 원본 `State` 는
    건드리지 않는다 - `simulate()` 는 이 필드들을 지역 변수/배열로만
    읽는다.

    `budgets`: elasticity_gate 문턱까지 바꾸는 "행동 추종" 예산 변경(주입
    `BUDGET_CHANGE(behavior_follows=true)` 와 같은 효과, GOAL 러너가 씀).
    `hard_caps`(S55): 봉투별 이번 달 누적 **체결분**(gate_spent, 주입은
    포함하지 않음)이 이 캡에 닿으면 그 달 남은 기간 그 봉투의 λ 를 0 으로
    만든다 - "예산을 줄이면 그만큼만 덜 쓴다" 는 소프트 유도(behavior_
    follows)와 달리 하드 상한이다. GOAL 이 재시뮬로 목표 달성 가능성을
    검증할 때 쓴다(리뷰 B5: 소프트 캡은 확정 예산을 오히려 인상해
    `plan_achieve_prob` 이 역행하는 결함이 있었다). 필수 봉투 하한(80%
    등)은 호출자가 이미 하한을 반영한 캡 값을 넘겨야 한다 - 이 함수는
    그 값을 그대로 하드 상한으로 쓸 뿐 별도 하한 로직을 넣지 않는다.
    `committed_amount_override`(B4): 키는 `f"{kind}:{source_id}"`
    (`source_id` 는 `source_fixed_expense_id` 또는 `source_loan_id`) -
    그 약정 큐 항목의 금액을 지정한 값으로 덮어쓴다.
    `card_withdrawal_weekday`: 카드 id -> 요일(0=월). 청구 발행/카드
    출금 예정일 계산에 그대로 반영된다(§8.6.1 네 번째 AUTO 후보).
    `cancel_committed`: `source_fixed_expense_id` 집합 - 그 항목을 약정
    스케줄에서 제거한다.
    """

    budgets: dict[int, int] | None = None
    cancel_committed: set[int] | None = None
    committed_amount_override: dict[str, int] | None = None
    externals: Externals | None = None
    card_withdrawal_weekday: dict[int, int] | None = None
    hard_caps: dict[int, int] | None = None


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
    # `gate_budgets_map`: elasticity_gate 문턱 계산에만 쓰는 예산(behavior_
    # follows 예산 변경). `display_budgets_map`: 실제 봉투 예산(exhaustion/
    # envelope_budgets 출력)에 쓰는 예산 - `Overrides.budgets` 는 둘 다
    # 바꾸지만(GOAL 의 기존 "행동 추종" 캡 용법과 호환), 주입
    # `BUDGET_CHANGE(behavior_follows=false)` 는 후자만 바꾼다(B3 수정).
    gate_budgets_map: dict[int, int] = dict(ov.budgets or {})
    display_budgets_map: dict[int, int] = dict(ov.budgets or {})
    hard_cap_map: dict[int, int] = dict(ov.hard_caps or {})
    cancel_set: set[int] = set(ov.cancel_committed or ())
    amount_override_map: dict[str, int] = dict(ov.committed_amount_override or {})
    card_weekday_override: dict[int, int] = dict(ov.card_withdrawal_weekday or {})

    # `FixedChangeInjection.from_` 는 스키마상 `date | None` 이지만
    # `_check_change` 검증기가 항상 값을 요구하므로 실제로는 None 이 될 수
    # 없다(SPEC 8.3 S8: "from(적용 시작일) 필수").
    fixed_change: dict[int, tuple[date | None, int | None, bool]] = {}
    day_spend: dict[date, list[tuple[int, int, str, int | None]]] = {}
    day_income: dict[date, list[int]] = {}
    day_emergency_draw: dict[date, list[int]] = {}
    horizon_end = as_of + timedelta(days=horizon_days)

    for inj in injections:
        # mypy 는 판별 필드(`inj.type`)를 직접 비교할 때만 유니온을 좁힌다
        # (중간 변수에 복사하면 좁혀지지 않는다) - 그래서 각 분기가
        # `inj.type ==` 를 직접 쓴다.
        if inj.type == "BUDGET_CHANGE":
            # B3 수정: `behavior_follows` 와 무관하게 실제 예산(따라서
            # envelope_budgets/exhaustion/overrun_prob)은 바뀐다. 소비
            # 행동(elasticity_gate 문턱)만 `behavior_follows=true` 일 때
            # 함께 바뀐다 - "예산만 줄이고 행동은 그대로면 얼마나
            # 초과하나?" 라는 질문에 `false` 가 조용히 0 을 답하던 결함을
            # 고친다(리뷰 B3, S53).
            display_budgets_map[inj.envelope_id] = inj.new_budget
            if inj.behavior_follows:
                gate_budgets_map[inj.envelope_id] = inj.new_budget
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
            card_id = getattr(inj, "card_id", None)  # N4: 스키마 필드는 J3 소유
            day_spend.setdefault(d, []).append((inj.envelope_id, inj.amount, inj.method, card_id))
        elif inj.type == "INCOME":
            d = _resolve_event_date(inj.on, inj.days_from_now, as_of)
            day_income.setdefault(d, []).append(inj.amount)
        elif inj.type == "RECURRING_SPEND":
            card_id = getattr(inj, "card_id", None)
            for d in _expand_recurring_dates(inj, as_of, horizon_end):
                day_spend.setdefault(d, []).append(
                    (inj.envelope_id, inj.amount, inj.method, card_id)
                )
        elif inj.type == "EMERGENCY_DRAW":
            d = _resolve_event_date(inj.on, inj.days_from_now, as_of)
            day_emergency_draw.setdefault(d, []).append(inj.amount)

    # -- 약정 큐를 일자별 스케줄로 (CARD_BILL 은 제외 - 모듈 docstring 참조) --
    loan_rate_delta_bp = eff_externals.loan_rate_delta_bp
    committed_items = committed if committed is not None else list(state.committed)
    committed_by_date: dict[date, list[Committed]] = {}
    for item in committed_items:
        if item.kind == "CARD_BILL":
            continue
        fx_id = item.source_fixed_expense_id
        amount = item.amount

        # B4: `EXTERNAL.loan_rate_delta_bp` 가 대출이자 금액에 실제 영향을
        # 주려면 여기서 rate 를 다시 계산해야 한다(build 시점 큐는 그
        # 시점의 delta 로 이미 고정돼 있다). `INTEREST_ONLY` 만 재계산
        # 가능하다 - `AMORTIZING` 은 원금균등분할 가정(`term_months`)을
        # 다시 풀어야 정확한 재계산이 되는데 그 가정 자체가 build 쪽에만
        # 있어 여기서는 재현할 수 없다(한계를 그대로 둔다, 리뷰 B4 결정).
        if (
            item.kind == "LOAN"
            and item.loan_repayment == "INTEREST_ONLY"
            and item.rate_pct is not None
            and item.principal is not None
        ):
            adjusted_rate_pct = item.rate_pct + loan_rate_delta_bp / 100
            monthly_rate = adjusted_rate_pct / 100 / 12
            amount = round(item.principal * monthly_rate / 10) * 10

        if fx_id is not None and fx_id in cancel_set:
            continue
        # B4: `committed_amount_override` 키는 `f"{kind}:{source_id}"`
        # (source_id 는 source_fixed_expense_id 또는 source_loan_id) - 이
        # 항목이 명시적으로 지정되면 위 대출 재계산 결과보다 우선한다.
        src_id = fx_id if fx_id is not None else item.source_loan_id
        if src_id is not None:
            override_key = f"{item.kind}:{src_id}"
            if override_key in amount_override_map:
                amount = amount_override_map[override_key]
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
    # `budget_arr`: 실제 예산(exhaustion/envelope_budgets 출력에 쓴다).
    # `gate_budget_arr`: elasticity_gate 문턱 계산에만 쓴다(B3 수정 - 둘을
    # 분리해야 `BUDGET_CHANGE(behavior_follows=false)` 가 "예산은 바뀌지만
    # 소비 행동은 그대로" 를 표현할 수 있다).
    budget_arr = np.array(
        [display_budgets_map.get(e, state_env_by_id[e].budget) for e in env_ids], dtype=np.int64
    )
    gate_budget_arr = np.array(
        [gate_budgets_map.get(e, state_env_by_id[e].budget) for e in env_ids], dtype=np.int64
    )
    # S55: 봉투별 하드 캡(-1 = 캡 없음). GOAL 이 재시뮬 검증에 쓴다.
    hard_cap_arr = np.array([hard_cap_map.get(e, -1) for e in env_ids], dtype=np.int64)
    spent_init = np.array([state_env_by_id[e].spent for e in env_ids], dtype=np.int64)

    # -- 수입 일정 (SPEC 5.1 income, 6장 payday_boost/pre_payday_damp) ---
    # S48(리뷰 U1): 불규칙 수입은 다음 입금일 자체가 경로마다 흔들려야 한다
    # (생성기 `fdt/gen/generator.py:_step_income` 의
    # `actual_gap = max(3, round(gap + N(0, 0.3*gap)))` 와 동일 분포). 이전
    # 버전은 `next = d + median_gap_days` 로 전 경로가 같은 날 입금돼(결정론)
    # C 프로필 커버리지가 좁아지는 정량적 원인이었다(리뷰 항목 2, U1). 규칙적
    # 수입(SALARY)은 날짜가 이미 결정론이라 잡음도, 난수 소비도 없다(CRN
    # 보존 - A/B/D 프로필은 이 블록에서 `rng_main` 을 전혀 건드리지 않는다).
    income = state.income
    income_anchor_day = income.next_date.day if income.next_date is not None else None
    # `irregular_income`: `income.irregular` 이고 다음 입금일이 실제로 잡혀
    # 있을 때만 경로별 배열을 쓴다. behavior.py 는 `irregular=True` 이면서
    # `next_date` 가 있으면 `median_gap_days` 도 항상 채운다(1건 이하일 때만
    # `next_date=None` 이 되므로) - 그래도 방어적으로 둘 다 확인한다.
    irregular_income = (
        income.irregular and income.next_date is not None and income.median_gap_days is not None
    )

    next_income_date: date | None = None
    last_income_date: date | None = None
    next_income_ord: np.ndarray | None = None
    last_income_ord: np.ndarray | None = None

    if irregular_income:
        assert income.next_date is not None and income.median_gap_days is not None
        next_income_ord = np.full(n_paths, income.next_date.toordinal(), dtype=np.int64)
        last_income_ord = np.full(
            n_paths,
            (income.next_date - timedelta(days=income.median_gap_days)).toordinal(),
            dtype=np.int64,
        )
    else:
        next_income_date = income.next_date
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

    # QA-108(b): 시뮬 시작 시점에 이미 청구서가 발행돼 있던 상태
    # (`CardState.issued_unpaid`, as_of 스냅샷)도 "카드별 예정 출금일 1건"
    # 규칙을 똑같이 적용해야 한다 - 이 배치는 위 카드 초기화 루프에서
    # `pending_amt`/`pending_due` 에만 채워지고 `pending_bill_records` 에는
    # 없어서, 이 등록이 없으면 첫 출금(성공이든 실패든)이 FORECAST
    # `events[]` 에 전혀 안 잡힌다. `synthetic_forecast_only=True` 로 표시해
    # `payment_records`(§8.5 RISK `payment_risks()` 의 원천)에는 더하지
    # 않는다 - RISK 는 이 초기 잔여 청구서를 이미 다른 경로(`unbilled`/
    # `issued_unpaid` 상태 자체)로 다루고 있어, 여기서 새로 payment_records
    # 항목을 만들면 RISK 쪽 결과가 이 수정과 무관하게 바뀐다(범위 밖). 예정일이
    # 이미 as_of 이전/당일이면(이미 밀린 청구서) 시뮬레이터가 실제로 시도하는
    # 첫날(k=1)로 당겨 이벤트를 낸다 - 과거 날짜에 이벤트를 낼 수는 없다.
    for ci, c in enumerate(cards):
        for billing in sorted(c.issued_unpaid, key=lambda b: b.billing_date):
            first_due = _first_weekday_on_or_after(billing.billing_date, card_weekday[ci])
            due_clipped = first_due if first_due > as_of else as_of + timedelta(days=1)
            pending_bill_records.append(
                {
                    "card_id": c.id,
                    "name": f"카드대금 {c.card_name}",
                    "due": due_clipped,
                    "amounts": np.full(n_paths, billing.amount, dtype=np.int64),
                    "has_bill": np.ones(n_paths, dtype=bool),
                    "synthetic_forecast_only": True,
                }
            )

    # QA-108(a): 불규칙 수입은 경로마다 입금일이 흔들려(위 S48 설명) 하루
    # 루프 안에서 그대로 이벤트를 쌓으면 거의 매일 INCOME 이벤트가 생긴다.
    # 대신 경로별 "몇 번째 입금인지" 카운터(`path_income_count`)와 그 날의
    # 순서(ordinal)만 회차별로 모아뒀다가(`income_occurrence_days`), 루프가
    # 끝난 뒤 회차마다 경로들의 날짜 중앙값 하루에만 이벤트 1건을 만든다
    # (오케스트레이터 결정. 규칙적 수입은 애초에 전 경로가 같은 날 입금돼
    # 이미 회차당 1건이라 이 경로를 타지 않는다).
    income_occurrence_days: dict[int, list[int]] = {}
    path_income_count = np.zeros(n_paths, dtype=np.int64) if irregular_income else None

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
        if irregular_income:
            # S48/U1: 경로별로 다음 입금일이 흔들리므로, 오늘 입금일이 된
            # 경로만 골라(`due_mask`) 금액·다음 입금일을 갱신한다. 규칙적
            # 수입과 달리 이 분기는 `rng_main` 을 두 번 더 소비한다(금액
            # 잡음 + 간격 잡음) - 그래서 규칙적 프로필의 CRN 은 이 분기를
            # 절대 타지 않는다(위 `irregular_income` 분리 참조).
            assert next_income_ord is not None and last_income_ord is not None
            due_mask = next_income_ord == d_ord
            if due_mask.any():
                years_elapsed = (d - as_of).days / _YEAR_DAYS
                growth_mult = (1.0 + income_growth_pct) ** years_elapsed
                n_due = int(due_mask.sum())
                noise = rng_main.lognormal(mean=0.0, sigma=0.4, size=n_due)
                amounts = np.round(income.expected * growth_mult * noise).astype(np.int64)
                liquidity[due_mask] += amounts
                last_income_ord[due_mask] = d_ord
                # QA-108(a): 여기서 바로 이벤트를 만들지 않는다(위 설명) -
                # 회차(occurrence)별 날짜만 모아 루프 종료 후 집계한다.
                assert path_income_count is not None
                due_idx = np.nonzero(due_mask)[0]
                for occurrence in path_income_count[due_idx].tolist():
                    income_occurrence_days.setdefault(occurrence, []).append(d_ord)
                path_income_count[due_idx] += 1
                # 생성기와 동일 분포: actual_gap = max(3, round(gap + N(0, 0.3*gap)))
                gap = income.median_gap_days
                assert gap is not None  # irregular_income 조건이 이미 보장
                gap_noise = rng_main.normal(0.0, gap * 0.3, size=n_due)
                actual_gap = np.maximum(3, np.round(gap + gap_noise).astype(np.int64))
                next_income_ord[due_mask] = d_ord + actual_gap
        elif next_income_date is not None and d == next_income_date:
            years_elapsed = (d - as_of).days / _YEAR_DAYS
            growth_mult = (1.0 + income_growth_pct) ** years_elapsed
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
            if income_anchor_day is not None:
                y, m = _next_month(d.year, d.month)
                next_income_date = clamped_month_date(y, m, income_anchor_day)
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
                            "name": f"카드대금 {card.card_name}",  # S47/N2: 큐와 이름 통일
                            "due": first_due,
                            "amounts": unbilled[ci].copy(),
                            "has_bill": has_bill.copy(),
                        }
                    )
                unbilled[ci][:] = 0

        # 4. 카드 출금 (예정 출금일 이후 매일 재시도, 실패 시 그 카드 중단) --
        for ci, card in enumerate(cards):
            failed_today = np.zeros(n_paths, dtype=bool)
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
            # QA-108(b): 예전에는 `attempted_today.any()`(재시도까지 포함해
            # 밀린 청구서가 남아있는 한 매일 참) 기준으로 CARD_BILL 이벤트를
            # 매일 만들어, FORECAST `events[]` 가 거의 매일 카드대금을
            # 나열했다(결함 QA-108). 이제 FORECAST 이벤트는 카드별 **예정
            # 출금일(첫 시도일) 1건**만 만든다 - 아래 `resolved`(그 배치의
            # 예정일이 오늘인 건) 루프에서 `payment_records` 와 같은 소스로
            # 만든다(재시도 성공/실패는 별도 이벤트로 나열하지 않는다).

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
                if not r.get("synthetic_forecast_only"):
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
                if n_has:
                    # `fail_prob` 은 "예정일 당일 실패 비율"이다(오케스트레이터
                    # 결정, docstring 명시 - QA-108(b)). 말일까지 미결제로
                    # 남는 비율은 이 이벤트에 넣지 않고 facts(§9.2)로만 낸다.
                    day_events.append(
                        Event(
                            kind="CARD_BILL",
                            name=r["name"],
                            amount=amount_repr,
                            success_ratio=1.0 - fail_prob,
                            source_card_id=r["card_id"],
                        )
                    )
            if resolved:
                pending_bill_records = [
                    r
                    for r in pending_bill_records
                    if not (r["card_id"] == card.id and r["due"] == d)
                ]

        # 5. 소비 --------------------------------------------------------
        weekday = d.weekday()
        boost: float | np.ndarray
        if irregular_income:
            # S48: 입금일이 경로별로 갈라지므로 payday_boost/pre_payday_damp
            # 창도 경로별 배열이 된다(생성기와 달리 벡터화 시뮬레이터라서
            # "이 경로는 지금 payday 창 안" 을 불리언 마스크로 표현한다).
            assert next_income_ord is not None and last_income_ord is not None
            boost = np.ones(n_paths, dtype=np.float64)
            since_last = d_ord - last_income_ord
            payday_mask = (since_last >= 0) & (since_last <= 6)
            boost = np.where(payday_mask, payday_boost, boost)
            until_next = next_income_ord - d_ord
            pre_mask = (until_next >= 1) & (until_next <= 5)
            boost = np.where(pre_mask, boost * pre_payday_damp, boost)
        else:
            boost = 1.0
            if last_income_date is not None and 0 <= (d - last_income_date).days <= 6:
                boost *= payday_boost
            if next_income_date is not None and 1 <= (next_income_date - d).days <= 5:
                boost *= pre_payday_damp

        # B3: elasticity_gate 문턱은 `gate_budget_arr`(behavior_follows 예산)
        # 로 계산한다 - 실제 봉투 예산(`budget_arr`, exhaustion/출력용)과
        # 분리한다.
        budget_f = np.where(gate_budget_arr > 0, gate_budget_arr, 1).astype(np.float64)
        remaining_ratio = 1.0 - gate_spent.astype(np.float64) / budget_f[None, :]
        gate = np.where(remaining_ratio < 0.2, elasticity[None, :], 1.0)
        gate[:, gate_budget_arr <= 0] = 1.0

        for ei, _eid in enumerate(env_ids):
            lam = np.clip(
                daily_rate[ei] * weekday_mult[ei, weekday] * boost * gate[:, ei], 0.0, None
            )
            if hard_cap_arr[ei] >= 0:
                # S55: 이번 달 누적 체결분(gate_spent, 주입 제외)이 하드
                # 캡에 닿은 경로는 그 달 남은 기간 이 봉투의 λ 를 0 으로
                # 만든다(GOAL 재시뮬 전용, 리뷰 B5).
                capped = gate_spent[:, ei] >= hard_cap_arr[ei]
                lam = np.where(capped, 0.0, lam)
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

                # B2/S46: 하루·봉투 합계 현금 지출을 부분 체결한다 - 감당
                # 가능한 만큼만 잔액에서 나가고 나머지는 suppressed_demand
                # 로 넘어간다(주입 경로 "7. 주입" 과 같은 규칙, 모듈
                # docstring "벡터화 근사" 참조). 이전 버전의 전부-또는-전무
                # 게이트는 C 프로필 백테스트를 기준 초과로 악화시켰다.
                paid = np.minimum(cash_total, liquidity)
                liquidity -= paid
                suppressed_demand_cum += cash_total - paid

                card_success_total = np.zeros(n_paths, dtype=np.int64)
                if n_cards > 0:
                    card_success_total = np.bincount(
                        path_index, weights=np.where(via_card, amounts, 0), minlength=n_paths
                    ).astype(np.int64)
                successful = paid + card_success_total
                gate_spent[:, ei] += successful

            envelope_spend[:, ei, k] = gate_spent[:, ei] + injected_spent[:, ei]
            if budget_arr[ei] > 0:  # N3: 예산 0 봉투는 "소진" 판정에서 제외
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
                # N7: 5단계 정규 소비와 대칭으로 price_index_mult 를 곱한다
                # (SPEC 7.2 6단계는 이를 명시하지 않지만 비대칭을 없앤다).
                shock_amounts = (np.round(raw * price_index_mult / 100.0) * 100).astype(np.int64)
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

                # B2/S46: 5단계와 같은 부분 체결 규칙(위 참조).
                paid = np.minimum(cash_total, liquidity)
                liquidity -= paid
                suppressed_demand_cum += cash_total - paid

                card_success = np.zeros(n_paths, dtype=np.int64)
                card_success[hit_paths] = np.where(via_card, shock_amounts, 0)
                successful = paid + card_success
                gate_spent[:, other_idx] += successful
                envelope_spend[:, other_idx, k] = (
                    gate_spent[:, other_idx] + injected_spent[:, other_idx]
                )
                if budget_arr[other_idx] > 0:  # N3
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

        for envelope_id, spend_amount, method, spend_card_id in day_spend.get(d, []):
            ei = env_index[envelope_id]
            if method == "CARD" and n_cards > 0:
                # N4: 명시된 카드가 있으면 그 카드로, 없으면 첫 관리 카드로
                # (이전 버전은 항상 `unbilled[0]` 이라 출금 요일이 다른 카드가
                # 여럿이면 어느 카드로 잡히는지가 결과를 바꿨다).
                card_idx = 0
                if spend_card_id is not None and spend_card_id in card_id_to_idx:
                    card_idx = card_id_to_idx[spend_card_id]
                unbilled[card_idx] += spend_amount
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
            if budget_arr[ei] > 0:  # N3
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
        # B1/S45(리뷰 이탈 (d) 수정): "부족"을 **관측 가능한 결제 실패
        # 사건**으로 정의한다 - 카드 출금 실패(`card_shortfall`) 또는 미납
        # 고정비(`unpaid_obligation_cum > 0`) 또는 억제된 소비/돌발 수요
        # (`suppressed_demand_cum > 0`). 이전 버전(`economic < 0`)은
        # `issued_unpaid`(정상적으로 예정된 카드 청구서 float)까지 부족으로
        # 세어, 주 단위 청구 주기를 쓰는 카드 사용자는 실제 결제 실패가
        # 전혀 없어도 `shortfall_prob` 이 상시 절반 가까이 나오는 오탐을
        # 만들었다(리뷰 B1 실측, B 프로필 오탐률 약 45%). 새 정의는
        # 정답 데이터의 카드 부족·거절 결제 이력(SPEC 11장)과 1:1 대응하므로
        # Phase 7 캘리브레이션이 성립한다. `economic`(위 줄)은
        # 지표로는 계속 노출하되(§8.2 `economic` 필드, `stats(economic=True)`)
        # 이 판정에는 쓰지 않는다. `card_shortfall`/`unpaid_obligation_cum`/
        # `suppressed_demand_cum` 은 전부 단조 비감소(사건이 한 번 일어나면
        # 계속 참/양수)이므로 이 사건도 한 번 True 가 되면 계속 True 다.
        day_short = card_shortfall | (unpaid_obligation_cum > 0) | (suppressed_demand_cum > 0)
        newly_short = day_short & (~any_shortfall)
        first_shortfall_idx[newly_short] = k
        any_shortfall |= day_short

    if income_occurrence_days:
        # QA-108(a): 회차별 경로들의 입금일 중앙값 하루에 INCOME 이벤트
        # 1건만 만든다. 금액은 실현 잡음이 아니라 기대치(expected)를 쓴다
        # (오케스트레이터 결정 - "회차/기대치" 는 실현 금액 분포가 아니라
        # 예정된 수입 일정을 보여주는 용도라서다). 다만 horizon 끝에
        # 가까운 회차는 "실제로 빨리 입금된 소수 경로"만 그 회차에 도달해
        # (간격 잡음 sigma=0.3*gap) 표본이 얇은 채로 중앙값을 낸다 - 그대로
        # 두면 다수결이 아닌 꼬리 표본이 이벤트를 만들어 horizon 끝자락에
        # 가짜 이벤트가 몰린다. 그 회차에 실제로 도달한 경로가 **과반**일
        # 때만 이벤트로 승격한다(경로 절반 이상이 그 회차 수입을 받았다고
        # 볼 수 있을 때만 "예정된 수입"으로 표시).
        expected_amount = round(income.expected)
        first_ord = dates[1].toordinal()
        last_ord = dates[-1].toordinal()
        majority = n_paths / 2
        for occurrence in sorted(income_occurrence_days):
            day_ords = income_occurrence_days[occurrence]
            if len(day_ords) < majority:
                continue
            median_ord = round(float(np.median(day_ords)))
            median_ord = min(max(median_ord, first_ord), last_ord)
            k_evt = median_ord - as_of.toordinal()
            events_by_day.setdefault(k_evt, []).append(
                Event(kind="INCOME", name="수입", amount=expected_amount, success_ratio=1.0)
            )

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
