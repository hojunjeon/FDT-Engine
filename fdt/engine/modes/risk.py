"""RISK 모드 러너 (SPEC 8.5).

`safe_to_spend_today`(8.5.1), `alerts`(8.5.2), `health`(8.5.3) 는 결정론
부분이라 시뮬레이션 없이 `State`(+ 원장 조회)만으로 계산한다 - `run_sim`
결과는 `risk_score`/`shortfall_prob`/`card_shortfall_prob`/`worst_day`/
`expected_shortfall`/`payment_risks` 에만 쓴다(작업 지시 "결정론 부분은
시뮬 없이 State 만으로 계산").
"""

from __future__ import annotations

from datetime import date, timedelta

from fdt.engine.modes import register
from fdt.engine.modes._common import make_context, run_sim, to_int
from fdt.engine.schemas.request import ModeRequest, RiskParams
from fdt.engine.schemas.result import (
    AccelerationAlert,
    Alert,
    ConcerningTxAlert,
    Health,
    RiskResult,
)
from fdt.engine.schemas.result import PaymentRisk as ResultPaymentRisk
from fdt.engine.schemas.state import State
from fdt.engine.taxonomy import ENVELOPE_IDS, Flow, Mode
from fdt.engine.taxonomy import ExcludeTag as _ExcludeTag

__all__ = ["run_risk"]

_ESSENTIAL_NAMES = ("교통비", "의료·건강", "편의점·마트·잡화")
_ESSENTIAL_IDS = frozenset(ENVELOPE_IDS[name] for name in _ESSENTIAL_NAMES)

# SPEC 5.2 "원장 규칙 NFR-BGT-01"(envelope_net_spend 문서)이 정의한 봉투
# 순지출 제외 태그. 이 값은 `fdt/engine/ledger.py` 의 private 상수와 같은
# 내용을 SPEC 규칙으로 재선언한 것이지(중복 목적), 그 모듈의 private 심볼을
# import 하지 않는다(모듈 간 private 의존 금지).
_ENVELOPE_EXCLUDED_TAGS = frozenset({_ExcludeTag.EMERGENCY, _ExcludeTag.CARRYOVER})

_SAFE_TO_SPEND_DEFAULT_DAYS = 30
_ACCEL_WARNING = 1.3
_ACCEL_DANGER = 1.6
_ACCEL_SPEND_FLOOR = 10_000
_CONCERNING_MIN_THRESHOLD = 20_000
_HEALTH_SAFE = 70
_HEALTH_WARNING = 40


def _engine_spend_today_amount(engine, as_of: date) -> int:
    total = 0
    for record in engine.ledger:
        if record.flow == Flow.SPEND and record.date == as_of:
            total += -record.signed_amount
    return total


def _acceleration_alert(state: State) -> AccelerationAlert | None:
    """SPEC 8.5.2 가속도 부분."""

    acceleration = state.indicators.acceleration
    spend_7d_avg = state.indicators.spend_7d_avg
    if spend_7d_avg < _ACCEL_SPEND_FLOOR:
        return None
    if acceleration >= _ACCEL_DANGER:
        return AccelerationAlert(severity="DANGER", ratio=acceleration)
    if acceleration >= _ACCEL_WARNING:
        return AccelerationAlert(severity="WARNING", ratio=acceleration)
    return None


def _spent_before(
    engine, envelope_id: int, month_start: date, tx_key: tuple
) -> int:
    """이 봉투에서 `tx_key`(정렬 키, `_tx_sort_key` 참조) 이전에 이미 확정된
    순지출(SPEC 5.2 envelope_net_spend 와 같은 제외 규칙)."""

    total = 0
    for record in engine.ledger:
        if record.envelope_id != envelope_id:
            continue
        if record.flow not in (Flow.SPEND, Flow.REFUND):
            continue
        if record.exclude_tag in _ENVELOPE_EXCLUDED_TAGS:
            continue
        if not (month_start <= record.date <= tx_key[0]):
            continue
        key = (record.date, record.time, record.id)
        if key >= tx_key:
            continue
        total += -record.signed_amount
    return total


def _concerning_tx_alerts(
    engine, state: State, recent_tx_ids: list[int]
) -> list[ConcerningTxAlert]:
    """SPEC 8.5.2 우려 결제 부분."""

    as_of = state.as_of
    month_start = state.cycle.budget_cycle_start
    last_day = state.cycle.budget_cycle_end.day
    budget_by_env = {env.envelope_id: env.budget for env in state.envelopes}

    if recent_tx_ids:
        wanted = set(recent_tx_ids)
        candidates = [
            r
            for r in engine.ledger
            if r.flow == Flow.SPEND and r.origin_tx_id in wanted and r.envelope_id is not None
        ]
    else:
        candidates = [
            r
            for r in engine.ledger
            if r.flow == Flow.SPEND and r.date == as_of and r.envelope_id is not None
        ]

    alerts: list[ConcerningTxAlert] = []
    for tx in candidates:
        envelope_id = tx.envelope_id
        assert envelope_id is not None
        amount = -tx.signed_amount
        budget = budget_by_env.get(envelope_id, 0)
        tx_key = (tx.date, tx.time, tx.id)
        spent_before = _spent_before(engine, envelope_id, month_start, tx_key)
        remaining_before = budget - spent_before

        threshold = max(
            0.5 * remaining_before, 3 * budget / max(last_day, 1), _CONCERNING_MIN_THRESHOLD
        )

        severity: str | None = None
        if amount >= remaining_before:
            severity = "DANGER"
        elif amount >= threshold:
            severity = "WARNING"

        if severity is not None:
            alerts.append(
                ConcerningTxAlert(
                    severity=severity,  # type: ignore[arg-type]
                    tx_id=tx.origin_tx_id,
                    amount=amount,
                    envelope_id=envelope_id,
                    remaining_before=to_int(remaining_before),
                    threshold=to_int(threshold),
                )
            )
    return alerts


def _health(engine, state: State, card_shortfall_prob: float) -> Health:
    """SPEC 8.5.3."""

    as_of = state.as_of
    committed_30d = sum(
        item.amount for item in state.committed if as_of < item.due <= as_of + timedelta(days=30)
    )
    spend_90d_avg = state.indicators.spend_90d_avg
    coverage = _clip((state.liquidity - committed_30d) / max(spend_90d_avg * 30, 1.0), 0.0, 1.0)

    progress = state.cycle.progress
    overrun_terms = []
    for env in state.envelopes:
        if env.budget <= 0:
            continue
        overrun_terms.append(_clip(env.spent / env.budget - progress, 0.0, 1.0))
    adherence = 1.0 - (sum(overrun_terms) / len(overrun_terms) if overrun_terms else 0.0)

    risk = 1.0 - card_shortfall_prob
    score = 100.0 * (0.4 * coverage + 0.3 * adherence + 0.3 * risk)
    score_int = to_int(score)

    if score_int >= _HEALTH_SAFE:
        level = "SAFE"
    elif score_int >= _HEALTH_WARNING:
        level = "WARNING"
    else:
        level = "DANGER"

    return Health(
        score=score_int,
        level=level,  # type: ignore[arg-type]
        coverage=coverage,
        adherence=adherence,
        risk=risk,
    )


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


@register(Mode.RISK)
def run_risk(engine, req: ModeRequest) -> RiskResult:
    params = req.params
    # `ModeRequest._parse_params_by_mode` 가 mode 로 params 클래스를 이미
    # 확정해 두므로(SPEC 8.1) 런타임에는 항상 참이다 - mypy 에 유니온을
    # 좁혀 알려주는 assert 다.
    assert isinstance(params, RiskParams)
    state = engine.state

    ctx = make_context(engine, req)
    sim = run_sim(ctx)

    stats_real = sim.stats(economic=False)
    stats_eco = sim.stats(economic=True)
    shortfall_prob = stats_real.shortfall_prob
    card_shortfall_prob = stats_real.card_shortfall_prob

    risk_score = to_int(100 * max(card_shortfall_prob, 0.6 * shortfall_prob))
    if risk_score < 20:
        level = "SAFE"
    elif risk_score < 50:
        level = "WARNING"
    else:
        level = "DANGER"

    worst_day = stats_eco.first_shortfall_date_median or stats_eco.min_balance_date

    # B1/S45: `expected_shortfall` 은 "부족 사건이 발생한 경로의 (미결제
    # 카드 청구 잔액 + 미납 고정비 + 억제된 수요) 말일 합계 평균"이다.
    # `balances[:, -1] - economic[:, -1]` 은 정의상
    # `issued_unpaid_sum + unpaid_obligation_cum + suppressed_demand_cum`
    # 의 말일 값과 같다(둘 다 `simulate()` 에서 그 식으로 계산됨) - 이전
    # 버전의 "부족 경로 최저 경제 잔액의 절대값"은 카드 청구 float 의
    # 크기를 재는 것이라 사건과 무관한 숫자를 냈다(리뷰 B1: B 프로필
    # 191,623원이 실제 사건 0건에 대한 값이었다).
    any_shortfall = sim.any_shortfall
    if any_shortfall.any():
        shortfall_amount_final = sim.balances[:, -1] - sim.economic[:, -1]
        expected_shortfall = to_int(float(shortfall_amount_final[any_shortfall].mean()))
    else:
        expected_shortfall = 0

    payment_risks = [
        ResultPaymentRisk(
            due=p.due,
            kind=p.kind,
            name=p.name,
            amount=p.amount,
            fail_prob=p.fail_prob,
            median_balance_before=p.median_balance_before,
        )
        for p in sim.payment_risks()
    ]

    alerts: list[Alert] = []
    accel_alert = _acceleration_alert(state)
    if accel_alert is not None:
        alerts.append(accel_alert)
    alerts.extend(_concerning_tx_alerts(engine, state, params.recent_tx_ids))

    safe_to_spend = _safe_to_spend_today(engine, state)
    health = _health(engine, state, card_shortfall_prob)

    return RiskResult(
        risk_score=risk_score,
        level=level,  # type: ignore[arg-type]
        shortfall_prob=shortfall_prob,
        card_shortfall_prob=card_shortfall_prob,
        worst_day=worst_day,
        expected_shortfall=expected_shortfall,
        payment_risks=payment_risks,
        alerts=alerts,
        safe_to_spend_today=safe_to_spend,
        health=health,
    )


def _safe_to_spend_today(engine, state: State) -> int:
    """SPEC 8.5.1. `engine.ledger` 를 직접 순회해야 하므로(State 는 원장
    자체를 담지 않는다) `engine` 을 함께 받는다."""

    as_of = state.as_of
    next_income = state.income.next_date
    if next_income is not None:
        bound_date = next_income
    else:
        bound_date = as_of + timedelta(days=_SAFE_TO_SPEND_DEFAULT_DAYS)
    days = max(1, (bound_date - as_of).days)

    committed = sum(item.amount for item in state.committed if as_of < item.due < bound_date)
    raw_daily = (state.liquidity - committed) / days

    acceleration = state.indicators.acceleration
    factor = 1.0 / acceleration if acceleration > 1 else 1.0

    spent_today = _engine_spend_today_amount(engine, as_of)

    return max(0, int((raw_daily * factor - spent_today) // 100) * 100)
