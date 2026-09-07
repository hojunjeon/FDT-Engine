"""FORECAST 모드 러너 단위 테스트 (SPEC 8.2, PLAN §5.1 test_forecast).

`engines_3m`/`seed_engine_*`(conftest.py, session 스코프)로 4 프로필 엔진을
얻어 `Engine.run(ModeRequest(mode=FORECAST, ...))` 을 호출하는 통합 경로와,
`run_forecast()` 를 가벼운 fake engine(State/Behavior/Externals 만 있는
`types.SimpleNamespace`, `make_context` 가 `engine.state/.behavior/.externals`
만 읽으므로 충분하다)에 직접 호출하는 수작업 경로를 함께 쓴다.
"""

from __future__ import annotations

import time
import types
from datetime import date

from fdt.engine import Engine
from fdt.engine.modes.forecast import run_forecast
from fdt.engine.schemas.behavior import Behavior, EnvelopeBehavior, ShockModel
from fdt.engine.schemas.input import Externals
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.state import (
    AccountState,
    Committed,
    Cycle,
    EnvelopeState,
    IncomeSchedule,
    Indicators,
    State,
)
from fdt.tools.validate import validate_result

_EXTERNALS = Externals()


# ---------------------------------------------------------------------------
# 수작업 State/Behavior 헬퍼 (test_simulate.py 와 같은 패턴, 이 파일 전용 복사)
# ---------------------------------------------------------------------------


def _make_state(
    *,
    as_of: date,
    liquidity: int,
    committed: list[Committed] | None = None,
    income: IncomeSchedule | None = None,
    envelope_budgets: dict[int, int] | None = None,
    envelope_spent: dict[int, int] | None = None,
) -> State:
    envelope_budgets = envelope_budgets or {}
    envelope_spent = envelope_spent or {}
    envelopes = [
        EnvelopeState(
            envelope_id=i,
            name=str(i),
            budget=envelope_budgets.get(i, 1_000_000),
            spent=envelope_spent.get(i, 0),
            remaining=envelope_budgets.get(i, 1_000_000) - envelope_spent.get(i, 0),
            budget_source="ENGINE",
        )
        for i in range(1, 8)
    ]
    return State(
        as_of=as_of,
        accounts=[AccountState(id=10, role="PRIMARY", balance=liquidity)],
        liquidity=liquidity,
        emergency_fund=0,
        cards=[],
        committed=committed or [],
        envelopes=envelopes,
        income=income
        or IncomeSchedule(next_date=None, expected=0, irregular=True, median_gap_days=None),
        indicators=Indicators(
            spend_7d_avg=0, spend_90d_avg=0, acceleration=1.0, unconfirmed_count=0
        ),
        cycle=Cycle(
            budget_cycle_start=as_of.replace(day=1), budget_cycle_end=as_of, progress=0.5
        ),
    )


def _make_behavior(*, as_of: date, daily_rate: float = 0.0) -> Behavior:
    envelopes = [
        EnvelopeBehavior(
            envelope_id=i,
            daily_rate=daily_rate,
            weekday_mult=[1.0] * 7,
            amount_mu=9.0,
            amount_sigma=0.5,
            card_share=0.5,
            elasticity=1.0,
            n_obs=0,
        )
        for i in range(1, 8)
    ]
    return Behavior(
        as_of=as_of,
        window_days=90,
        envelopes=envelopes,
        payday_boost=1.0,
        pre_payday_damp=1.0,
        shock=ShockModel(daily_prob=0.0, mu=9.0, sigma=0.5),
        income=IncomeSchedule(next_date=None, expected=0, irregular=True, median_gap_days=None),
    )


def _fake_engine(state: State, behavior: Behavior) -> types.SimpleNamespace:
    """`run_forecast(engine, req)` 가 실제로 읽는 필드(state/behavior/
    externals)만 채운 가벼운 대역 - `Engine` 전체(twin/ledger/meta)를
    조립하는 비용 없이 수작업 시나리오를 검증한다."""

    return types.SimpleNamespace(state=state, behavior=behavior, externals=_EXTERNALS)


def _default_req(**overrides) -> ModeRequest:
    params = {"include_envelopes": True, "include_events": True}
    params.update(overrides.pop("params", {}))
    return ModeRequest(mode="FORECAST", params=params, **overrides)


# ---------------------------------------------------------------------------
# 1. median[0] == liquidity, p10 <= median <= p90, economic <= trajectory
# ---------------------------------------------------------------------------


def test_median_at_day0_equals_liquidity(engines_3m: dict[str, Engine]) -> None:
    for name, engine in engines_3m.items():
        result = engine.run(_default_req(n_paths=200, seed=42))
        assert result.status == "OK", (name, result.error)
        assert result.result.trajectory.median[0] == engine.state.liquidity, name


def test_p10_le_median_le_p90(engines_3m: dict[str, Engine]) -> None:
    for name, engine in engines_3m.items():
        result = engine.run(_default_req(n_paths=200, seed=42))
        traj = result.result.trajectory
        for i in range(len(traj.dates)):
            assert traj.p10[i] <= traj.median[i] <= traj.p90[i], (name, i)


def test_economic_median_le_trajectory_median(engines_3m: dict[str, Engine]) -> None:
    """경제 잔액 = 실제 잔액 - 미결제 - 억제 수요(SPEC 7.2 8단계) 이므로
    항상 실제 잔액 이하다."""

    for name, engine in engines_3m.items():
        result = engine.run(_default_req(n_paths=200, seed=42))
        traj = result.result.trajectory
        eco = result.result.economic
        for i in range(len(traj.median)):
            assert eco.median[i] <= traj.median[i], (name, i)


# ---------------------------------------------------------------------------
# 2. exhaust_date_median / overrun_prob
# ---------------------------------------------------------------------------


def test_exhaust_date_median_is_as_of_when_already_over_budget() -> None:
    as_of = date(2026, 9, 7)
    state = _make_state(
        as_of=as_of,
        liquidity=1_000_000,
        envelope_budgets={1: 100_000},
        envelope_spent={1: 150_000},  # 이미 예산 초과
    )
    behavior = _make_behavior(as_of=as_of)
    engine = _fake_engine(state, behavior)
    req = _default_req(n_paths=100, seed=1)

    result = run_forecast(engine, req)

    env1 = next(e for e in result.envelopes if e.envelope_id == 1)
    assert env1.exhaust_date_median == as_of
    assert env1.overrun_prob == 1.0


def test_overrun_prob_in_unit_interval(engines_3m: dict[str, Engine]) -> None:
    for name, engine in engines_3m.items():
        result = engine.run(_default_req(n_paths=200, seed=42))
        for env in result.result.envelopes:
            assert 0.0 <= env.overrun_prob <= 1.0, (name, env.envelope_id)


# ---------------------------------------------------------------------------
# 3. events 는 큐·수입을 포함한다
# ---------------------------------------------------------------------------


def test_events_include_committed_queue_and_income() -> None:
    as_of = date(2026, 9, 7)
    committed = [
        Committed(
            kind="RENT",
            name="월세",
            due=date(2026, 9, 20),
            amount=500_000,
            certainty=1.0,
            account_id=10,
            source_fixed_expense_id=1,
        )
    ]
    income = IncomeSchedule(
        next_date=date(2026, 9, 25), expected=2_000_000, irregular=False, median_gap_days=30
    )
    state = _make_state(as_of=as_of, liquidity=1_000_000, committed=committed, income=income)
    behavior = _make_behavior(as_of=as_of)
    engine = _fake_engine(state, behavior)
    req = _default_req(n_paths=100, seed=1)

    result = run_forecast(engine, req)

    kinds = {ev.kind for ev in result.events}
    assert "RENT" in kinds
    assert "INCOME" in kinds


def test_include_flags_suppress_envelopes_and_events() -> None:
    as_of = date(2026, 9, 7)
    committed = [
        Committed(
            kind="RENT",
            name="월세",
            due=date(2026, 9, 20),
            amount=500_000,
            certainty=1.0,
            account_id=10,
            source_fixed_expense_id=1,
        )
    ]
    state = _make_state(as_of=as_of, liquidity=1_000_000, committed=committed)
    behavior = _make_behavior(as_of=as_of)
    engine = _fake_engine(state, behavior)
    req = ModeRequest(
        mode="FORECAST",
        params={"include_envelopes": False, "include_events": False},
        n_paths=100,
        seed=1,
    )

    result = run_forecast(engine, req)

    assert result.envelopes == []
    assert result.events == []


# ---------------------------------------------------------------------------
# 4. 4 프로필 validate_result 통과
# ---------------------------------------------------------------------------


def test_all_profiles_validate(engines_3m: dict[str, Engine]) -> None:
    for name, engine in engines_3m.items():
        result = engine.run(_default_req(n_paths=200, seed=42))
        report = validate_result(result)
        assert report.ok, (name, report.errors)


# ---------------------------------------------------------------------------
# 5. 재현성
# ---------------------------------------------------------------------------


def test_reproducibility(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["C_impulsive"]
    r1 = engine.run(_default_req(n_paths=200, seed=42))
    r2 = engine.run(_default_req(n_paths=200, seed=42))
    assert r1.strip_volatile() == r2.strip_volatile()


# ---------------------------------------------------------------------------
# 6. 성능: 30일 x 1000경로 < 2s
# ---------------------------------------------------------------------------


def test_forecast_30d_1000paths_under_2s(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["B_card_crunch"]
    req = _default_req(horizon_days=30, n_paths=1000, seed=42)

    t0 = time.perf_counter()
    result = engine.run(req)
    elapsed = time.perf_counter() - t0

    assert result.status == "OK"
    assert elapsed < 2.0, f"FORECAST 30일 x 1000경로가 {elapsed:.3f}s 걸렸다(기준 < 2s)"


# ---------------------------------------------------------------------------
# 7. horizon 120 에서 고정비(월세) 4회 (S42 committed 재생성)
# ---------------------------------------------------------------------------


def test_horizon_120_rebuilds_committed_queue_for_monthly_fixed_expense(
    engines_3m: dict[str, Engine],
) -> None:
    """`state.committed` 는 as_of+90 까지만 채워진다(SPEC 5.1/7.1, S42) -
    horizon_days=120 요청은 모드 러너가 `build_committed_queue(horizon_cap=
    horizon_days+7)` 로 재생성해야 월세(매월 반복) 가 4회(9/10/11/12월) 다
    나온다. B_card_crunch 프로필은 매월 25일 RENT 700,000원이 있다."""

    engine = engines_3m["B_card_crunch"]
    req = _default_req(horizon_days=120, n_paths=100, seed=42)

    result = engine.run(req)

    assert result.status == "OK"
    rent_events = [ev for ev in result.result.events if ev.kind == "RENT"]
    assert len(rent_events) == 4, [ev.date for ev in rent_events]
