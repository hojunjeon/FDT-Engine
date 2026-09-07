"""RISK 모드 러너 단위 테스트 (SPEC 8.5, 15.B, PLAN §5.1 test_risk).

결정론 부분(`_concerning_tx_alerts`/`_acceleration_alert`/`_health`/
`_safe_to_spend_today`)은 모듈 내부 헬퍼를 직접 호출해 화이트박스로
검증하고(시뮬레이션이 끼어들 여지가 없는 순수 계산이라 State/원장만
수작업으로 준비하면 된다), `risk_score`/`level`/`worst_day`/
`expected_shortfall` 처럼 시뮬레이션 결과에 의존하는 값은 daily_rate=0·
shock=0 인 결정론 시나리오로 `run_risk()` 전체를 호출해 검증한다.
"""

from __future__ import annotations

import types
from datetime import date, time, timedelta

from fdt.engine import Engine
from fdt.engine.ledger import LedgerTx
from fdt.engine.modes.risk import (
    _acceleration_alert,
    _concerning_tx_alerts,
    _health,
    _safe_to_spend_today,
    run_risk,
)
from fdt.engine.schemas.behavior import Behavior, EnvelopeBehavior, ShockModel
from fdt.engine.schemas.input import Externals
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.state import (
    AccountState,
    CardState,
    Committed,
    Cycle,
    EnvelopeState,
    IncomeSchedule,
    Indicators,
    IssuedBilling,
    State,
)
from fdt.engine.taxonomy import ConfirmStatus, ExcludeTag, Flow
from fdt.tools.validate import validate_result

_EXTERNALS = Externals()


# ---------------------------------------------------------------------------
# 수작업 State/Behavior/Ledger 헬퍼
# ---------------------------------------------------------------------------


def _make_state(
    *,
    as_of: date,
    liquidity: int,
    cycle_end_day: int = 30,
    cards: list[CardState] | None = None,
    committed: list[Committed] | None = None,
    income: IncomeSchedule | None = None,
    envelope_budgets: dict[int, int] | None = None,
    envelope_spent: dict[int, int] | None = None,
    progress: float = 0.0,
    spend_7d_avg: float = 0.0,
    acceleration: float = 1.0,
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
        cards=cards or [],
        committed=committed or [],
        envelopes=envelopes,
        income=income
        or IncomeSchedule(next_date=None, expected=0, irregular=True, median_gap_days=None),
        indicators=Indicators(
            spend_7d_avg=spend_7d_avg,
            spend_90d_avg=max(spend_7d_avg, 1000),
            acceleration=acceleration,
            unconfirmed_count=0,
        ),
        cycle=Cycle(
            budget_cycle_start=as_of.replace(day=1),
            budget_cycle_end=as_of.replace(day=cycle_end_day),
            progress=progress,
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


def _tx(
    tx_id: int,
    *,
    envelope_id: int,
    amount: int,
    d: date,
    t: time = time(12, 0, 0),
    exclude_tag: ExcludeTag = ExcludeTag.NONE,
) -> LedgerTx:
    """SPEND 레코드 한 줄(원장 조회용 최소 필드만 채운다)."""

    return LedgerTx(
        id=tx_id,
        date=d,
        time=t,
        account_id=10,
        card_id=None,
        signed_amount=-amount,
        flow=Flow.SPEND,
        envelope_id=envelope_id,
        subcategory_id=1,
        confidence=1.0,
        source="SEED",
        merchant_name_raw=None,
        exclude_tag=exclude_tag,
        confirm_status=ConfirmStatus.AUTO,
        origin_tx_id=tx_id,
        counterparty_account_id=None,
    )


def _fake_engine(state: State, behavior: Behavior, ledger: list[LedgerTx]) -> types.SimpleNamespace:
    """`run_risk`/그 헬퍼가 읽는 필드(state/behavior/externals/ledger)만
    채운 가벼운 대역."""

    return types.SimpleNamespace(
        state=state, behavior=behavior, externals=_EXTERNALS, ledger=ledger
    )


def _default_req(**overrides) -> ModeRequest:
    params = overrides.pop("params", {})
    overrides.setdefault("n_paths", 100)
    overrides.setdefault("seed", 1)
    return ModeRequest(mode="RISK", params=params, **overrides)


# ---------------------------------------------------------------------------
# 1. SPEC §15.B 우려 결제 규칙 3행
# ---------------------------------------------------------------------------


def test_spec_15b_concerning_tx_three_rows() -> None:
    as_of = date(2026, 9, 16)  # 9월 말일 30일

    # 각 행을 별개 봉투(1/2/3)로 분리해 spent_before 가 서로 간섭하지 않게
    # 한다. budget=600,000 은 세 행 공통(SPEC §15.B).
    budgets = {1: 600_000, 2: 600_000, 3: 600_000}
    # spent_before = budget - remaining_before. 사전 지출 레코드(더 이른
    # 시각, 더 작은 id)로 그 금액을 만든다.
    prior = [
        _tx(1001, envelope_id=1, amount=600_000 - 20_000, d=as_of - timedelta(days=1)),
        _tx(1002, envelope_id=2, amount=600_000 - 200_000, d=as_of - timedelta(days=1)),
        _tx(1003, envelope_id=3, amount=600_000 - 200_000, d=as_of - timedelta(days=1)),
    ]
    # 검사 대상 결제(당일, 사전 지출보다 늦은 시각).
    candidates = [
        _tx(2001, envelope_id=1, amount=15_000, d=as_of, t=time(14, 0, 0)),  # 미발동
        _tx(2002, envelope_id=2, amount=120_000, d=as_of, t=time(14, 0, 0)),  # WARNING
        _tx(2003, envelope_id=3, amount=250_000, d=as_of, t=time(14, 0, 0)),  # DANGER
    ]
    ledger = prior + candidates

    state = _make_state(as_of=as_of, liquidity=10_000_000, envelope_budgets=budgets)
    engine = _fake_engine(state, _make_behavior(as_of=as_of), ledger)

    alerts = _concerning_tx_alerts(engine, state, [])
    by_tx = {a.tx_id: a for a in alerts}

    assert 2001 not in by_tx, "0.5x잔여=10,000·3x pace=60,000 미만이라 미발동이어야 한다"
    assert by_tx[2002].severity == "WARNING"
    assert by_tx[2003].severity == "DANGER"


def test_recent_tx_ids_restricts_candidates_to_specified_ids() -> None:
    as_of = date(2026, 9, 16)
    ledger = [
        _tx(1001, envelope_id=2, amount=600_000 - 200_000, d=as_of - timedelta(days=1)),
        _tx(2001, envelope_id=2, amount=15_000, d=as_of, t=time(14, 0, 0)),  # 미발동(제외 대상)
        _tx(2002, envelope_id=2, amount=120_000, d=as_of, t=time(15, 0, 0)),  # WARNING(지정 대상)
    ]
    state = _make_state(as_of=as_of, liquidity=10_000_000, envelope_budgets={2: 600_000})
    engine = _fake_engine(state, _make_behavior(as_of=as_of), ledger)

    alerts_all = _concerning_tx_alerts(engine, state, [])
    alerts_restricted = _concerning_tx_alerts(engine, state, [2002])

    assert {a.tx_id for a in alerts_all} == {2002}  # 2001 은 애초에 미발동
    assert {a.tx_id for a in alerts_restricted} == {2002}

    # recent_tx_ids 가 2001 만 가리키면(WARNING 이 안 나는 거래) 결과가
    # 비어야 한다 - "지정한 것만 검사한다" 는 실제로 다른 후보를 배제한다.
    alerts_only_2001 = _concerning_tx_alerts(engine, state, [2001])
    assert alerts_only_2001 == []


# ---------------------------------------------------------------------------
# 2. Safe-to-Spend: 0 이상, 고정비 > 잔액이면 0
# ---------------------------------------------------------------------------


def test_safe_to_spend_is_nonnegative_and_zero_when_committed_exceeds_liquidity() -> None:
    as_of = date(2026, 9, 7)
    income = IncomeSchedule(
        next_date=date(2026, 9, 17), expected=0, irregular=False, median_gap_days=30
    )
    committed = [
        Committed(
            kind="RENT",
            name="월세",
            due=date(2026, 9, 10),
            amount=5_000_000,  # 잔액보다 훨씬 큰 고정비
            certainty=1.0,
            account_id=10,
            source_fixed_expense_id=1,
        )
    ]
    state = _make_state(as_of=as_of, liquidity=100_000, income=income, committed=committed)
    engine = _fake_engine(state, _make_behavior(as_of=as_of), [])

    safe = _safe_to_spend_today(engine, state)

    assert safe >= 0
    assert safe == 0


def test_safe_to_spend_positive_when_liquidity_covers_committed() -> None:
    as_of = date(2026, 9, 7)
    income = IncomeSchedule(
        next_date=date(2026, 9, 17), expected=0, irregular=False, median_gap_days=30
    )
    state = _make_state(as_of=as_of, liquidity=1_000_000, income=income, committed=[])
    engine = _fake_engine(state, _make_behavior(as_of=as_of), [])

    safe = _safe_to_spend_today(engine, state)

    assert safe > 0


# ---------------------------------------------------------------------------
# 3. 가속도 알림 노이즈 플로어 (SPEC 8.5.2)
# ---------------------------------------------------------------------------


def test_acceleration_alert_floor_and_thresholds() -> None:
    as_of = date(2026, 9, 7)

    # spend_7d_avg < 10,000 이면 acceleration 이 아무리 높아도 미발동(노이즈 플로어).
    below_floor = _make_state(as_of=as_of, liquidity=1, spend_7d_avg=9_999, acceleration=5.0)
    assert _acceleration_alert(below_floor) is None

    warning = _make_state(as_of=as_of, liquidity=1, spend_7d_avg=10_000, acceleration=1.3)
    alert = _acceleration_alert(warning)
    assert alert is not None and alert.severity == "WARNING"

    danger = _make_state(as_of=as_of, liquidity=1, spend_7d_avg=10_000, acceleration=1.6)
    alert = _acceleration_alert(danger)
    assert alert is not None and alert.severity == "DANGER"

    safe = _make_state(as_of=as_of, liquidity=1, spend_7d_avg=10_000, acceleration=1.29)
    assert _acceleration_alert(safe) is None


# ---------------------------------------------------------------------------
# 4. health 경계 70/40 (SPEC 8.5.3)
# ---------------------------------------------------------------------------


def test_health_score_boundaries_70_and_40() -> None:
    as_of = date(2026, 9, 7)

    def _state_for_coverage(c: float) -> State:
        # coverage = clip((liquidity - committed_30d)/(spend_90d_avg*30), 0, 1)
        # committed_30d=0 이 되도록 committed 를 비운다.
        spend_90d_avg = 100_000.0
        liquidity = round(c * spend_90d_avg * 30)
        # adherence = 1 - mean_e clip(spent_e/budget_e - progress, 0, 1),
        # progress=0 이면 spent_e/budget_e = 1-c 로 맞춘다(모든 봉투 동일).
        budget = 1_000_000
        spent = round((1.0 - c) * budget)
        return _make_state(
            as_of=as_of,
            liquidity=liquidity,
            envelope_budgets={i: budget for i in range(1, 8)},
            envelope_spent={i: spent for i in range(1, 8)},
            progress=0.0,
            spend_7d_avg=0.0,
        ).model_copy(update={"indicators": Indicators(
            spend_7d_avg=0, spend_90d_avg=spend_90d_avg, acceleration=1.0, unconfirmed_count=0
        )})

    engine = _fake_engine(_state_for_coverage(0.7), _make_behavior(as_of=as_of), [])

    # risk = 1 - card_shortfall_prob = c 가 되도록 card_shortfall_prob=1-c.
    state_70 = _state_for_coverage(0.7)
    health_70 = _health(engine, state_70, card_shortfall_prob=0.3)
    assert health_70.score == 70
    assert health_70.level == "SAFE"

    state_40 = _state_for_coverage(0.4)
    health_40 = _health(engine, state_40, card_shortfall_prob=0.6)
    assert health_40.score == 40
    assert health_40.level == "WARNING"

    state_39 = _state_for_coverage(0.39)
    health_39 = _health(engine, state_39, card_shortfall_prob=0.61)
    assert health_39.score == 39
    assert health_39.level == "DANGER"


# ---------------------------------------------------------------------------
# 5. risk_score 공식 / level / worst_day / expected_shortfall (결정론 시나리오)
# ---------------------------------------------------------------------------


def test_risk_score_zero_and_safe_when_no_shortfall_possible() -> None:
    as_of = date(2026, 9, 7)
    state = _make_state(as_of=as_of, liquidity=10_000_000, committed=[])
    engine = _fake_engine(state, _make_behavior(as_of=as_of), [])

    result = run_risk(engine, _default_req())

    assert result.risk_score == 0
    assert result.level == "SAFE"
    assert result.shortfall_prob == 0.0
    assert result.card_shortfall_prob == 0.0


def test_risk_score_100_and_danger_when_card_always_fails() -> None:
    """카드 미결제(500,000원)가 잔액(1,000원)보다 훨씬 커서 매 경로·매일
    실패하는 결정론 시나리오(daily_rate=0). 카드 출금이 첫날부터 계속
    실패하므로(관측 가능한 결제 실패 사건, B1/S45) shortfall_prob=
    card_shortfall_prob=1.0, risk_score=100, DANGER. `expected_shortfall`
    은 그 미결제 카드 청구서 전액(다른 미납/억제 없음)이다."""

    as_of = date(2026, 9, 7)
    withdrawal_weekday = (as_of + timedelta(days=1)).weekday()
    card = CardState(
        id=1,
        withdrawal_weekday=withdrawal_weekday,
        withdrawal_account_id=10,
        unbilled=0,
        issued_unpaid=[
            IssuedBilling(billing_date=as_of - timedelta(days=7), amount=500_000)
        ],
    )
    state = _make_state(as_of=as_of, liquidity=1_000, cards=[card], committed=[])
    engine = _fake_engine(state, _make_behavior(as_of=as_of), [])

    result = run_risk(engine, _default_req(horizon_days=10))

    assert result.shortfall_prob == 1.0
    assert result.card_shortfall_prob == 1.0
    assert result.risk_score == 100
    assert result.level == "DANGER"
    assert result.worst_day == as_of + timedelta(days=1)
    assert result.expected_shortfall == 500_000


# ---------------------------------------------------------------------------
# 6. 4 프로필 실측: A SAFE, B level != SAFE, validate 통과
# ---------------------------------------------------------------------------


def test_profile_a_is_safe_and_b_is_not(engines_3m: dict[str, Engine]) -> None:
    req = ModeRequest(mode="RISK", horizon_days=30, n_paths=300, seed=42, params={})

    result_a = engines_3m["A_steady"].run(req)
    result_b = engines_3m["B_card_crunch"].run(req)

    assert result_a.status == "OK" and result_b.status == "OK"
    assert result_a.result.level == "SAFE"
    assert result_b.result.level != "SAFE"


def test_all_profiles_risk_validate(engines_3m: dict[str, Engine]) -> None:
    req = ModeRequest(mode="RISK", horizon_days=30, n_paths=300, seed=42, params={})
    for name, engine in engines_3m.items():
        result = engine.run(req)
        assert result.status == "OK", (name, result.error)
        report = validate_result(result)
        assert report.ok, (name, report.errors)
