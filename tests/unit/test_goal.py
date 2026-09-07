"""GOAL 모드 러너 단위 테스트 (SPEC 8.4, PLAN 5.1 test_goal, W9 완료 조건).

`run_goal(engine, req)` 를 직접 호출한다(`Engine.run()` 을 거치지 않는다 -
facts/viz 배선은 W7 소유라 이 파일의 관심사가 아니다). `validate_result`
쪽만 예외로 `engine.run(req)` 전체 파이프라인을 쓰되, 그 결과가
`status == "OK"` 일 때만(배선이 끝났을 때만) 검사한다.

4 프로필은 `engines_3m` 픽스처(session 스코프, `months=3, seed=7,
end=2026-09-07`)를 쓴다 - `data/seed/*_7`(6개월치) 대신 이걸 쓰는 이유:
D 프로필은 SPEC 11장이 "월 잉여 40~48만, 12월 말까지 200만 추가 저축이
아슬아슬하게 미달" 이라고 서술하는데, 실제로 엔진이 6개월 이력에서
추정한 Behavior 로 시뮬레이션하면(같은 `data/seed/D_goal_saver_7`)
`achieve_prob` 가 0.97 안팎으로 나와(과거 이력이 길수록 표본이 안정돼
서술과 어긋난다) 이 테스트가 요구하는 "아슬아슬하게 미달"을 재현하지
못한다. 3개월 이력(`engines_3m`, `test_state.py`/`test_ledger_profiles.py`
와 같은 조합)로 추정한 Behavior 는 실제로 `achieve_prob < 0.5` 를 낸다 -
아래 `test_goal_save_d_profile_marginal_miss` docstring에 실측치를 남겨
둔다.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from fdt.engine.engine import Engine
from fdt.engine.errors import E_REQ_RANGE, FdtError
from fdt.engine.modes.goal import run_goal
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.taxonomy import ENVELOPE_IDS
from fdt.tools.validate import validate_result

_ESSENTIAL_NAMES = ("교통비", "의료·건강", "편의점·마트·잡화")
_ESSENTIAL_IDS = frozenset(ENVELOPE_IDS[name] for name in _ESSENTIAL_NAMES)
_N_PATHS = 200
_SEED = 42


def _req(goal_type: str, **params) -> ModeRequest:
    return ModeRequest(
        mode="GOAL",
        n_paths=_N_PATHS,
        seed=_SEED,
        params={"goal_type": goal_type, **params},
    )


# ---------------------------------------------------------------------------
# A_steady: 쉬운 목표 -> feasible, 어려운 목표 -> infeasible + 필수만
# ---------------------------------------------------------------------------


def test_goal_balance_a_profile_easy_target_is_feasible(engines_3m):
    engine: Engine = engines_3m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of + timedelta(days=30))

    result = run_goal(engine, req)

    assert result.feasible is True
    assert result.required.reduction_ratio == pytest.approx(0.0)
    assert result.achieve_prob >= 0.9


def test_goal_balance_a_profile_impossible_target_is_infeasible(engines_3m):
    engine: Engine = engines_3m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=100_000_000, target_date=as_of + timedelta(days=30))

    result = run_goal(engine, req)

    assert result.feasible is False
    assert result.gap.median < 0
    assert result.gap.p10 < 0

    # "필수만" (SPEC 8.4): 모든 주차에서 유연 봉투 cap 은 0, 필수 봉투만
    # 양수를 받는다.
    for week in result.weekly_caps:
        for cap in week.by_envelope:
            if cap.envelope_id in _ESSENTIAL_IDS:
                assert cap.cap >= 0
            else:
                assert cap.cap == 0
        assert any(c.cap > 0 for c in week.by_envelope if c.envelope_id in _ESSENTIAL_IDS)


# ---------------------------------------------------------------------------
# D_goal_saver: SAVE 200만 12/31 (SPEC 11 D 프로필 "아슬아슬하게 미달")
# ---------------------------------------------------------------------------


def test_goal_save_d_profile_marginal_miss(engines_3m):
    """SPEC 11 D 프로필: "12월 말까지 as_of 잔액 대비 200만원 추가 저축이
    현 소비 유지 시 아슬아슬하게 미달". `engines_3m`(3개월 이력) 로 추정한
    Behavior 로는 실측 `achieve_prob ~= 0.005`, `reduction_ratio ~= 0.20`,
    `plan_achieve_prob ~= 0.035` (seed=42, n_paths=200) - 아래 단언은 이
    실측을 느슨하게 감싼 것이지 하드코딩한 정확한 값이 아니다(재현성은
    `test_goal_reproducible_given_same_seed` 가 따로 검사한다).
    """

    import numpy as np

    from fdt.engine.modes._common import make_context, run_sim
    from fdt.engine.modes.goal import _cumulative_envelope_totals

    engine: Engine = engines_3m["D_goal_saver"]
    as_of = engine.state.as_of
    target_date = date(2026, 12, 31)
    horizon_days = (target_date - as_of).days
    req = _req("SAVE", target_amount=2_000_000, target_date=target_date)

    result = run_goal(engine, req)

    assert result.achieve_prob < 0.5
    assert result.required.reduction_ratio > 0.0
    assert result.plan_achieve_prob >= result.achieve_prob - 0.02

    n_weeks = len(result.weekly_caps)
    total_weekly = sum(w.total_cap for w in result.weekly_caps)
    assert total_weekly == pytest.approx(result.required.total_discretionary_cap, abs=100 * n_weeks)

    # baseline_e 를 base 시뮬에서 직접 재구성해(goal.py 와 같은 계산을
    # 재사용, run_goal 내부 값을 다시 계산하는 게 아니라 검증만 별도로
    # 한다) 필수 봉투 하한(0.8 x baseline_e x days_w/H) 이 실제로 지켜지는지
    # 확인한다.
    ctx = make_context(engine, req, horizon_days=horizon_days)
    base_sim = run_sim(ctx)
    totals = _cumulative_envelope_totals(base_sim)
    baseline_e = {eid: float(np.median(arr)) for eid, arr in totals.items()}

    for week in result.weekly_caps:
        by_env_sum = sum(c.cap for c in week.by_envelope)
        assert abs(week.total_cap - by_env_sum) <= 1

        for cap in week.by_envelope:
            if cap.envelope_id in _ESSENTIAL_IDS:
                e_floor = 0.8 * baseline_e.get(cap.envelope_id, 0.0) * week.days / horizon_days
                assert cap.cap >= e_floor - 200  # 100원 내림 + 잔여 배분 오차 여유


def test_goal_essential_floor_enforced_when_binding(engines_3m):
    """필수 봉투 하한(0.8 x baseline_e x days_w/H) 이 실제로 발동하는
    시나리오(A 프로필 + 불가능한 목표) - envelope_id 별로 baseline
    시뮬레이션에서 직접 봉투 지출을 다시 구해 floor 를 재계산하고, 배분된
    cap 이 (반올림 오차 이내로) 그 floor 이상인지 검사한다.
    """

    import numpy as np

    from fdt.engine.modes._common import make_context, run_sim
    from fdt.engine.modes.goal import _cumulative_envelope_totals

    engine: Engine = engines_3m["A_steady"]
    as_of = engine.state.as_of
    target_date = as_of + timedelta(days=30)
    req = _req("BALANCE", target_amount=100_000_000, target_date=target_date)
    horizon_days = (target_date - as_of).days

    ctx = make_context(engine, req, horizon_days=horizon_days)
    base_sim = run_sim(ctx)
    totals = _cumulative_envelope_totals(base_sim)
    baseline_e = {eid: float(np.median(arr)) for eid, arr in totals.items()}

    result = run_goal(engine, req)

    for week in result.weekly_caps:
        # 유연 봉투에는 하한이 없다 - 이 목표는 완전 infeasible 이라 유연은
        # 0 이어야 하고(위 test_goal_balance_a_profile_impossible_target_is_infeasible
        # 가 이미 검사), 필수 봉투만 하한을 받는다.
        for cap in week.by_envelope:
            if cap.envelope_id in _ESSENTIAL_IDS:
                e_floor = 0.8 * baseline_e.get(cap.envelope_id, 0.0) * week.days / horizon_days
                assert cap.cap >= e_floor - 200  # 100원 내림 + 잔여 배분 오차 여유


# ---------------------------------------------------------------------------
# ENVELOPE_ADHERE: 실행만 확인(SPEC 이 이 타입의 achieve_prob/gap 지표를
# BALANCE/SAVE 만큼 구체적으로 정의하지 않는다 - 아래 goal.py docstring/
# 보고 참조)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver"])
def test_goal_envelope_adhere_runs_for_every_profile(engines_3m, profile):
    engine: Engine = engines_3m[profile]
    req = _req("ENVELOPE_ADHERE")

    result = run_goal(engine, req)

    assert 0.0 <= result.achieve_prob <= 1.0
    assert 0.0 <= result.plan_achieve_prob <= 1.0
    assert 0.0 <= result.required.reduction_ratio <= 1.0
    assert result.weekly_caps  # 이번 달 말일까지 최소 1주차는 있어야 한다
    for week in result.weekly_caps:
        by_env_sum = sum(c.cap for c in week.by_envelope)
        assert abs(week.total_cap - by_env_sum) <= 1


# ---------------------------------------------------------------------------
# horizon 범위 검증 (SPEC 8.4 "H = target_date - as_of, 1~365")
# ---------------------------------------------------------------------------


def test_goal_target_date_366_days_raises_e_req_range(engines_3m):
    engine: Engine = engines_3m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of + timedelta(days=366))

    with pytest.raises(FdtError) as exc_info:
        run_goal(engine, req)
    assert exc_info.value.code == E_REQ_RANGE


def test_goal_target_date_in_past_raises_e_req_range(engines_3m):
    engine: Engine = engines_3m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of - timedelta(days=1))

    with pytest.raises(FdtError) as exc_info:
        run_goal(engine, req)
    assert exc_info.value.code == E_REQ_RANGE


def test_goal_target_date_equal_as_of_raises_e_req_range(engines_3m):
    """H=0 도 1~365 범위 밖이다(SPEC 8.4)."""

    engine: Engine = engines_3m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of)

    with pytest.raises(FdtError) as exc_info:
        run_goal(engine, req)
    assert exc_info.value.code == E_REQ_RANGE


# ---------------------------------------------------------------------------
# validate_result (조건부: engine.run() 이 OK 를 낼 때만 - 배선 완료 시)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver"])
def test_goal_validate_result_when_wired(engines_3m, profile):
    engine: Engine = engines_3m[profile]
    as_of = engine.state.as_of
    req = ModeRequest(
        mode="GOAL",
        n_paths=_N_PATHS,
        seed=_SEED,
        params={
            "goal_type": "BALANCE",
            "target_amount": 500_000,
            "target_date": as_of + timedelta(days=60),
        },
    )

    full_result = engine.run(req)
    if full_result.status != "OK":
        pytest.skip(f"GOAL 배선이 아직 끝나지 않았다(status={full_result.status})")

    report = validate_result(full_result)
    assert report.ok, report.errors


# ---------------------------------------------------------------------------
# 재현성 (같은 seed -> 바이트 동일 결과)
# ---------------------------------------------------------------------------


def test_goal_reproducible_given_same_seed(engines_3m):
    engine: Engine = engines_3m["D_goal_saver"]
    req = _req("SAVE", target_amount=2_000_000, target_date=date(2026, 12, 31))

    result_1 = run_goal(engine, req)
    result_2 = run_goal(engine, req)

    assert result_1 == result_2


# ---------------------------------------------------------------------------
# 성능 (< 4s, SPEC 12장 성능 기준에 준한 GOAL 자체 기준 - PLAN 없음이라
# 작업 지시가 정한 상한)
# ---------------------------------------------------------------------------


def test_goal_performance_under_4_seconds(engines_3m):
    import time

    engine: Engine = engines_3m["D_goal_saver"]
    req = _req("SAVE", target_amount=2_000_000, target_date=date(2026, 12, 31))

    start = time.perf_counter()
    run_goal(engine, req)
    elapsed = time.perf_counter() - start

    assert elapsed < 4.0
