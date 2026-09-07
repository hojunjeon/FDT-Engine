"""`facts.py` 단위 테스트 (작업 ID W11a, SPEC 9.2, 9.4).

`renderings_for()` 의 표기 규칙과, 5 모드 각각 합성 result 로 만든
`build_facts()` 가 SPEC 9.4 필수 fact 키·importance 를 내는지 검사한다.
합성 result 는 SPEC 8장 예시 JSON 값을 그대로 손으로 옮겨 만든다.

이 파일의 `_forecast_result()` 등 빌더 함수는 `test_viz.py`/`test_validate.py`
에서도 재사용한다(같은 작업(W11a) 소유 파일이라 셋이 공유해도 안전하다).
"""

from __future__ import annotations

from datetime import date

from fdt.engine.facts import build_facts, renderings_for
from fdt.engine.schemas.request import (
    ForecastParams,
    GoalParams,
    ModeRequest,
    OptimizeParams,
    RiskParams,
    WhatIfParams,
)
from fdt.engine.schemas.result import (
    AppliedAction,
    BranchSummary,
    EconomicStats,
    EngineMeta,
    EngineResult,
    EnvelopeCap,
    EnvelopeDelta,
    EnvelopeForecast,
    EventForecast,
    FirstShortfallDate,
    ForecastResult,
    Gap,
    GoalResult,
    Health,
    OptimizeBaseline,
    OptimizeResult,
    PaymentRisk,
    PointStat,
    RankedAction,
    Required,
    RiskResult,
    Trajectory,
    TrajectorySummary,
    WeeklyCap,
    WhatIfDelta,
    WhatIfResult,
)
from fdt.engine.taxonomy import Mode

AS_OF = date(2026, 9, 7)


# ---------------------------------------------------------------------------
# 합성 result 빌더 (SPEC 8장 예시 값)
# ---------------------------------------------------------------------------


def _forecast_result() -> ForecastResult:
    dates = [date(2026, 9, 7 + i) for i in range(5)]
    return ForecastResult(
        trajectory=Trajectory(
            dates=dates,
            median=[2013000.0, 1900000.0, 1500000.0, 1200000.0, 2013000.0],
            p10=[1800000.0, 1600000.0, 900000.0, -64000.0, 1600000.0],
            p90=[2200000.0, 2100000.0, 2000000.0, 1800000.0, 2400000.0],
            mean=[2010000.0, 1890000.0, 1490000.0, 1190000.0, 2000000.0],
        ),
        economic=EconomicStats(median=[2000000.0] * 5, p10=[1800000.0] * 5, p90=[2200000.0] * 5),
        min_point=PointStat(date=date(2026, 9, 24), median_balance=118000, p10_balance=-64000),
        end_point=PointStat(date=date(2026, 10, 7), median_balance=2013000),
        envelopes=[
            EnvelopeForecast(
                envelope_id=1,
                name="외식",
                budget=300000,
                spent_now=212400,
                projected_month_end_median=338000,
                exhaust_date_median=date(2026, 9, 21),
                overrun_prob=0.71,
            ),
            EnvelopeForecast(
                envelope_id=5,
                name="쇼핑",
                budget=200000,
                spent_now=210000,
                projected_month_end_median=260000,
                exhaust_date_median=date(2026, 9, 15),
                overrun_prob=0.9,
            ),
        ],
        events=[
            EventForecast(
                date=date(2026, 9, 9),
                kind="CARD_BILL",
                name="KB 체크",
                amount=183500,
                fail_prob=0.02,
            ),
            EventForecast(
                date=date(2026, 9, 16),
                kind="CARD_BILL",
                name="KB 체크",
                amount=175000,
                fail_prob=0.35,
            ),
            EventForecast(
                date=date(2026, 9, 25), kind="INCOME", name="급여", amount=2870000, fail_prob=0.0
            ),
        ],
        shortfall_prob=0.09,
        card_shortfall_prob=0.04,
    )


def _whatif_result() -> WhatIfResult:
    base_traj = TrajectorySummary(
        median=[2000000.0, 1900000.0], p10=[1800000.0, 1700000.0], p90=[2200000.0, 2100000.0]
    )
    branch_traj = TrajectorySummary(
        dates=[date(2026, 9, 7), date(2026, 9, 8)],
        median=[1850000.0, 1750000.0],
        p10=[1650000.0, 1550000.0],
        p90=[2050000.0, 1950000.0],
    )
    base = BranchSummary(
        trajectory=base_traj,
        min_point=PointStat(date=date(2026, 9, 20), median_balance=650000),
        end_point=PointStat(date=date(2026, 10, 7), median_balance=2163000),
        shortfall_prob=0.02,
        card_shortfall_prob=0.0,
    )
    branch = BranchSummary(
        trajectory=branch_traj,
        min_point=PointStat(date=date(2026, 9, 24), median_balance=500000),
        end_point=PointStat(date=date(2026, 10, 7), median_balance=2013000),
        shortfall_prob=0.13,
        card_shortfall_prob=0.06,
    )
    return WhatIfResult(
        base=base,
        branch=branch,
        delta=WhatIfDelta(
            min_balance=-150000,
            end_balance=-150000,
            shortfall_prob=0.11,
            card_shortfall_prob=0.06,
            first_shortfall_date=FirstShortfallDate(base=None, branch=date(2026, 9, 24)),
            envelopes=[
                EnvelopeDelta(envelope_id=5, remaining_change=-150000, overrun_prob_change=0.42)
            ],
        ),
        verdict="CAUTION",
        crn=True,
    )


def _goal_result() -> GoalResult:
    return GoalResult(
        feasible=True,
        achieve_prob=0.62,
        gap=Gap(median=-180000, p10=-640000),
        required=Required(
            total_discretionary_cap=1920000, reduction_ratio=0.23, baseline_discretionary=2490000
        ),
        weekly_caps=[
            WeeklyCap(
                week_start=date(2026, 9, 8),
                days=7,
                total_cap=210000,
                by_envelope=[
                    EnvelopeCap(envelope_id=1, cap=58000),
                    EnvelopeCap(envelope_id=5, cap=152000),
                ],
            ),
            WeeklyCap(
                week_start=date(2026, 9, 15),
                days=7,
                total_cap=200000,
                by_envelope=[
                    EnvelopeCap(envelope_id=1, cap=50000),
                    EnvelopeCap(envelope_id=5, cap=150000),
                ],
            ),
        ],
        plan_achieve_prob=0.88,
        notes=["불규칙 수입은 기대치의 80%만 반영"],
    )


def _risk_result() -> RiskResult:
    return RiskResult(
        risk_score=37,
        level="WARNING",
        shortfall_prob=0.31,
        card_shortfall_prob=0.37,
        worst_day=date(2026, 9, 16),
        expected_shortfall=142000,
        payment_risks=[
            PaymentRisk(
                due=date(2026, 9, 9),
                kind="CARD_BILL",
                name="KB 체크",
                amount=183500,
                fail_prob=0.02,
                median_balance_before=1640000,
            ),
            PaymentRisk(
                due=date(2026, 9, 16),
                kind="CARD_BILL",
                name="KB 체크",
                amount=175000,
                fail_prob=0.35,
                median_balance_before=161000,
            ),
            PaymentRisk(
                due=date(2026, 9, 25),
                kind="RENT",
                name="월세",
                amount=700000,
                fail_prob=0.30,
                median_balance_before=690000,
            ),
        ],
        alerts=[],
        safe_to_spend_today=19100,
        health=Health(score=58, level="WARNING", coverage=0.61, adherence=0.72, risk=0.63),
    )


def _optimize_result() -> OptimizeResult:
    return OptimizeResult(
        objective="MIN_SHORTFALL_PROB",
        baseline=OptimizeBaseline(
            shortfall_prob=0.31, card_shortfall_prob=0.37, end_balance_median=780000
        ),
        ranked=[
            RankedAction(
                rank=1,
                actions=[
                    AppliedAction(
                        injection={  # type: ignore[arg-type]
                            "type": "BUDGET_CHANGE",
                            "envelope_id": 5,
                            "new_budget": 280000,
                            "behavior_follows": True,
                        },
                        cut_ratio=0.3,
                        label="쇼핑 예산 30% 축소",
                    )
                ],
                effect={
                    "shortfall_prob": 0.12,
                    "delta": -0.19,
                    "end_balance_median": 1010000,
                    "cost_of_action": "쇼핑 월 12만원 감소",
                },
                feasibility_note="이번 달 이미 사용 21만원, 남은 한도 7만원",
            ),
            RankedAction(
                rank=2,
                actions=[
                    AppliedAction(
                        injection={  # type: ignore[arg-type]
                            "type": "FIXED_CHANGE",
                            "fixed_expense_id": 3,
                            "cancel": True,
                            "from": "2026-09-08",
                        },
                        label="구독 해지",
                    )
                ],
                effect={"shortfall_prob": 0.2, "delta": -0.11, "end_balance_median": 900000},
            ),
        ],
        recommended=None,
        evaluated=23,
        sim_calls=24,
        n_paths_used=200,
    )


def _meta(mode: Mode) -> EngineMeta:
    return EngineMeta(
        engine_id="a3f9c1d2e4b5",
        as_of=AS_OF,
        mode=mode,
        seed=42,
        n_paths=200,
        horizon_days=30,
        elapsed_ms=10,
        engine_version="0.1.0",
        warnings=[],
    )


def _request(mode: Mode) -> ModeRequest:
    params: ForecastParams | WhatIfParams | GoalParams | RiskParams | OptimizeParams
    if mode is Mode.FORECAST:
        params = ForecastParams()
    elif mode is Mode.WHATIF:
        params = WhatIfParams(
            injections=[
                {  # type: ignore[list-item]
                    "type": "SPEND",
                    "days_from_now": 1,
                    "amount": 150000,
                    "envelope_id": 5,
                    "method": "CARD",
                }
            ]
        )
    elif mode is Mode.GOAL:
        params = GoalParams(
            goal_type="BALANCE",
            target_amount=2000000,
            target_date="2026-12-31",  # type: ignore[arg-type]
        )
    elif mode is Mode.RISK:
        params = RiskParams()
    else:
        params = OptimizeParams(objective="MIN_SHORTFALL_PROB")
    return ModeRequest(mode=mode, params=params)


def build_ok_result(mode: Mode, result) -> EngineResult:
    """모드 + result -> facts/viz 를 채운 `EngineResult`(status=OK)."""

    from fdt.engine.viz import build_viz

    facts = build_facts(mode, result, as_of=AS_OF)
    viz = build_viz(mode, result, facts, as_of=AS_OF)
    return EngineResult(
        meta=_meta(mode),
        request=_request(mode),
        result=result,
        facts=facts,
        viz=viz,
        status="OK",
    )


RESULT_BUILDERS = {
    Mode.FORECAST: _forecast_result,
    Mode.WHATIF: _whatif_result,
    Mode.GOAL: _goal_result,
    Mode.RISK: _risk_result,
    Mode.OPTIMIZE: _optimize_result,
}


# ---------------------------------------------------------------------------
# renderings_for() 표기 규칙
# ---------------------------------------------------------------------------


def test_krw_renderings_19100():
    out = renderings_for(19100, "KRW", -2)
    assert "19,100원" in out
    assert "1만 9천원" in out
    assert "1.9만원" in out
    assert "약 2만원" in out


def test_krw_renderings_118000():
    out = renderings_for(118000, "KRW", -2)
    assert "11만 8천원" in out
    assert "약 12만원" in out
    assert "118,000원" in out


def test_krw_renderings_100man_and_above():
    assert "118만원" in renderings_for(1_180_000, "KRW", -4)
    assert "1억 2천만원" in renderings_for(120_000_000, "KRW", -4)


def test_krw_renderings_zero():
    assert renderings_for(0, "KRW", -2) == ["0원"]


def test_krw_renderings_under_1000_is_won_only():
    # N15/S60: 1,000원 미만은 "약 …"/"…만원" 표기가 반올림하면 0이 되어
    # 무의미하다("0만원" 은 한국어로 성립하지 않는다) - 원 단위 표기 하나만.
    assert renderings_for(100, "KRW", -2) == ["100원"]
    assert renderings_for(4, "KRW", -2) == ["4원"]
    assert renderings_for(999, "KRW", -2) == ["999원"]


def test_krw_renderings_no_zero_man_won_when_rounded_to_zero():
    # 1,000원 이상이어도 만원 단위로 반올림하면 0이 되는 값(예: 1,400원)은
    # "약 0원"/"0만원" 표기를 만들지 않는다.
    out = renderings_for(1400, "KRW", -2)
    assert not any("약" in r for r in out)
    assert not any("0만원" in r for r in out)
    assert "1,400원" in out


def test_krw_renderings_negative_has_ascii_hyphen_and_shortfall_label():
    out = renderings_for(-150000, "KRW", -2, signed=False)
    assert any(r.startswith("-") for r in out)
    assert not any("−" in r for r in out)  # noqa: RUF001 - 유니코드 마이너스 기호 자체를 검사한다
    assert any(r.startswith("부족 ") for r in out)


def test_krw_renderings_signed_positive_has_plus():
    out = renderings_for(150000, "KRW", -2, signed=True)
    assert any(r.startswith("+") for r in out)


def test_pct_renderings():
    out = renderings_for(37, "%", 0)
    assert out == ["37%", "약 40%"]


def test_prob_renderings():
    assert renderings_for(0.37, "prob", 2) == ["0.37"]


def test_ratio_renderings():
    out = renderings_for(0.23, "ratio", 2)
    assert "0.23" in out
    assert "23%" in out


def test_date_renderings_relative_today_tomorrow_and_n_days():
    as_of = date(2026, 9, 7)
    today = renderings_for("2026-09-07", "date", 0, as_of=as_of)
    tomorrow = renderings_for("2026-09-08", "date", 0, as_of=as_of)
    later = renderings_for("2026-09-24", "date", 0, as_of=as_of)
    assert "오늘" in today
    assert "내일" in tomorrow
    assert "17일 뒤" in later
    assert "2026-09-24" in later
    assert "9월 24일" in later
    assert not any("요일" in r for r in later)  # "다음 주 화요일" 류는 하지 않는다


# ---------------------------------------------------------------------------
# 모드별 build_facts: SPEC 9.4 필수 키 존재 + importance == 1
# ---------------------------------------------------------------------------


def test_forecast_required_facts_present():
    facts = build_facts(Mode.FORECAST, _forecast_result(), as_of=AS_OF)
    by_key = {f.key: f for f in facts}
    for key in ("end_balance_median", "min_balance_median", "min_balance_date", "shortfall_prob"):
        assert key in by_key, key
        assert by_key[key].importance == 1
    # 소진 예상 봉투 최대 2개 -> 2개 다 exhaust_date_median 이 있으므로 둘 다 나온다
    assert "envelope_exhaust_date_1" in by_key
    assert "envelope_exhaust_date_2" in by_key


def test_whatif_required_facts_present():
    facts = build_facts(Mode.WHATIF, _whatif_result(), as_of=AS_OF)
    by_key = {f.key: f for f in facts}
    for key in ("delta_min_balance", "delta_shortfall_prob", "verdict", "branch_min_balance_date"):
        assert key in by_key, key
        assert by_key[key].importance == 1
    assert by_key["verdict"].value == "CAUTION"


def test_goal_required_facts_present():
    facts = build_facts(Mode.GOAL, _goal_result(), as_of=AS_OF)
    by_key = {f.key: f for f in facts}
    for key in ("feasible", "achieve_prob", "gap_median", "reduction_ratio", "plan_achieve_prob"):
        assert key in by_key, key
        assert by_key[key].importance == 1


def test_risk_required_facts_present():
    facts = build_facts(Mode.RISK, _risk_result(), as_of=AS_OF)
    by_key = {f.key: f for f in facts}
    for key in ("risk_score", "level", "worst_day", "expected_shortfall", "safe_to_spend_today"):
        assert key in by_key, key
        assert by_key[key].importance == 1
    # 최고 위험 결제 1건
    assert "payment_risk_amount_1" in by_key
    assert by_key["payment_risk_amount_1"].importance == 1


def test_optimize_required_facts_present():
    facts = build_facts(Mode.OPTIMIZE, _optimize_result(), as_of=AS_OF)
    by_key = {f.key: f for f in facts}
    assert "baseline_shortfall_prob" in by_key
    assert by_key["baseline_shortfall_prob"].importance == 1
    assert "top_action_label" in by_key
    assert by_key["top_action_label"].value == "쇼핑 예산 30% 축소"


def test_facts_do_not_recompute_values_they_only_reformat():
    # gap.median 은 -180000 그대로 fact 값에 옮겨져야 한다(재계산 금지).
    facts = build_facts(Mode.GOAL, _goal_result(), as_of=AS_OF)
    by_key = {f.key: f for f in facts}
    assert by_key["gap_median"].value == -180000


def test_all_facts_have_nonempty_allowed_renderings():
    for mode, builder in RESULT_BUILDERS.items():
        facts = build_facts(mode, builder(), as_of=AS_OF)
        for f in facts:
            assert f.allowed_renderings, f"{mode}:{f.key} 의 allowed_renderings 가 비었다"
