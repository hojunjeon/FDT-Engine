"""GOAL 모드 러너 단위 테스트 (SPEC 8.4, PLAN 5.1 test_goal, W9/J2 완료 조건).

`run_goal(engine, req)` 를 직접 호출한다(`Engine.run()` 을 거치지 않는다 -
facts/viz 배선은 다른 작업 ID 소유라 이 파일의 관심사가 아니다).
`validate_result` 쪽만 예외로 `engine.run(req)` 전체 파이프라인을 쓰되, 그
결과가 `status == "OK"` 일 때만(배선이 끝났을 때만) 검사한다.

4 프로필은 `seed_engine_A/B/C/D`(session 스코프, `data/seed/*_7` - **6개월**
이력, seed=7, `tests/conftest.py`)를 `engines_6m` 로 묶어 쓴다. 리뷰
20260907_W6_W10.md 5-1(`b'`)이 밝혔듯, 이전 버전의 이 파일은 `engines_3m`
(3개월 이력)을 썼는데 그 스냅샷 자체가 SPEC §11("D 프로필 as_of 잔액
250~350만" 은 **6개월 생성 기준**에서만 성립)을 위반한다 - 3개월 스냅샷의
as_of 잔액은 115~183만원으로 범위 밖이라 "12월 말까지 200만 추가 저축이
아슬아슬하게 미달" 서술의 근거로 쓸 수 없다. 이 파일은 이제 6개월
데이터만 쓴다.

리뷰 5-1 은 또한 D 프로필의 `achieve_prob` 가 시드에 따라 0.35~0.98 로
크게 흩어진다는 것(생성기 §11 "월 잉여 40~48만" 목표가 실제 분산(약 16만원)
을 감안하지 않았기 때문, SPEC 제안 S61)을 실측으로 밝혔다 - 그래서
`test_goal_save_d_profile_seeds`(아래)는 "achieve_prob < 0.5" 같은 특정
값을 단정하지 않고, 시드 5개(1/3/5/7/11, seed=7 은 `seed_engine_D` 재사용,
나머지는 `fdt.gen.generate(months=6)` 로 메모리에서 생성)에 걸쳐 성립해야
하는 구조적 불변식(`plan_achieve_prob >= achieve_prob - 0.02`, 주차 cap
합, 필수 봉투 하한)만 검사하고 실측 achieve_prob/plan_achieve_prob 표를
docstring 에 남긴다.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from fdt.engine import Engine, build_engine
from fdt.engine.errors import E_REQ_RANGE, FdtError
from fdt.engine.modes._common import make_context, run_sim
from fdt.engine.modes.goal import _cumulative_envelope_totals, run_goal
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.taxonomy import ENVELOPE_IDS
from fdt.gen import generate
from fdt.tools.validate import validate_result

_ESSENTIAL_NAMES = ("교통비", "의료·건강", "편의점·마트·잡화")
_ESSENTIAL_IDS = frozenset(ENVELOPE_IDS[name] for name in _ESSENTIAL_NAMES)
_N_PATHS = 200
_SEED = 42

@pytest.fixture()
def engines_6m(
    seed_engine_A: Engine,
    seed_engine_B: Engine,
    seed_engine_C: Engine,
    seed_engine_D: Engine,
) -> dict[str, Engine]:
    """4 프로필(A/B/C/D) x seed=7, **6개월** 이력 엔진 딕셔너리.

    `tests/conftest.py`(W5 소유, 이 파일은 읽기만 한다)의 session 스코프
    `seed_engine_*` 픽스처를 이름으로 묶기만 하므로 재생성 비용이 없다.
    """

    return {
        "A_steady": seed_engine_A,
        "B_card_crunch": seed_engine_B,
        "C_impulsive": seed_engine_C,
        "D_goal_saver": seed_engine_D,
    }


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


def test_goal_balance_a_profile_easy_target_is_feasible(engines_6m):
    engine: Engine = engines_6m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of + timedelta(days=30))

    result = run_goal(engine, req)

    assert result.feasible is True
    assert result.required.reduction_ratio == pytest.approx(0.0)
    assert result.achieve_prob >= 0.9


def test_goal_balance_a_profile_impossible_target_is_infeasible(engines_6m):
    engine: Engine = engines_6m["A_steady"]
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
# D_goal_saver: SAVE 200만 12/31 - 리뷰 블로커 B5 수정 확인
# (total_discretionary_cap 세 겹 클램프 + Overrides.hard_caps 재시뮬)
# ---------------------------------------------------------------------------

# 리뷰 5-1 실측(수정 후 재측정, months=6, n_paths=200, seed=42): 시드마다
# achieve_prob 는 여전히 흩어지지만(생성기 §11 분산, S61), plan_achieve_prob
# 은 다섯 시드 전부 achieve_prob 이상(≥ achieve_prob - 0.02 를 항상 만족) -
# B5 이전에는 seed 3/11(6개월)에서 이 부등식이 역행했다(0.474->0.266,
# 0.346->0.288). 실측치는 아래 표로 보고에도 남긴다:
#   seed  achieve_prob  plan_achieve_prob  reduction_ratio
#   1     0.700         1.000              0.014
#   3     0.970         1.000              0.000
#   5     0.930         1.000              0.000
#   7     0.995         1.000              0.000   (seed_engine_D 고정 데이터)
#   11    0.525         1.000              0.037
_D_SAVE_SEEDS = [1, 3, 5, 7, 11]


def _d_engine_for_seed(seed: int, seed_engine_D: Engine) -> Engine:
    """seed=7 은 `data/seed/D_goal_saver_7`(session 픽스처, 다른 테스트와
    바이트 동일 데이터를 공유)를 그대로 쓰고, 나머지 시드는 `fdt.gen.
    generate(months=6)` 로 메모리에서만 새로 만든다(디스크에 쓰지 않는다 -
    `data/seed/` 는 J5 소유)."""

    if seed == 7:
        return seed_engine_D
    twin, _twin_raw, _gt = generate("D_goal_saver", seed=seed, months=6)
    return build_engine(twin)


@pytest.mark.parametrize("seed", _D_SAVE_SEEDS)
def test_goal_save_d_profile_seeds(seed, seed_engine_D):
    """D_goal_saver, SAVE 200만 12/31, 6개월 이력, 시드 5개. 리뷰가 요구한
    구조적 불변식만 검사한다(achieve_prob 절대값은 단정하지 않는다 - 위
    docstring 표 참조, 이유는 모듈 docstring).
    """

    engine = _d_engine_for_seed(seed, seed_engine_D)
    as_of = engine.state.as_of
    target_date = date(2026, 12, 31)
    horizon_days = (target_date - as_of).days
    req = _req("SAVE", target_amount=2_000_000, target_date=target_date)

    result = run_goal(engine, req)

    assert 0.0 <= result.achieve_prob <= 1.0
    assert 0.0 <= result.plan_achieve_prob <= 1.0
    assert 0.0 <= result.required.reduction_ratio <= 1.0
    # 블로커 B5 의 핵심 불변식: 계획(하드 캡 재시뮬)이 기준보다 나빠지면
    # 버그다(PLAN Phase 4 완료 조건). 이전에는 소프트 `Overrides.budgets`
    # 가 확정 예산을 인상해(D 프로필 830,000 -> 1,249,160원/월 실측) 역행이
    # 났다 - `Overrides.hard_caps` + 세 겹 클램프로 구조적으로 막는다.
    assert result.plan_achieve_prob >= result.achieve_prob - 0.02

    n_weeks = len(result.weekly_caps)
    total_weekly = sum(w.total_cap for w in result.weekly_caps)
    assert total_weekly == pytest.approx(result.required.total_discretionary_cap, abs=100 * n_weeks)

    # 세 겹 클램프 중 세 번째 항(Σ현재 확정 예산 x H/30) 이 실제로 지켜지는지
    # - 주차 cap 합(H 기간 총액)이 그 상한(H 기간으로 스케일한 값)을
    # 100원 반올림 오차 이내로 넘지 않아야 한다.
    current_budget_total_h = (
        sum(e.budget for e in engine.state.envelopes) * horizon_days / 30
    )
    assert total_weekly <= current_budget_total_h + 100 * n_weeks

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


def test_goal_essential_floor_enforced_when_binding(engines_6m):
    """필수 봉투 하한(0.8 x baseline_e x days_w/H) 이 실제로 발동하는
    시나리오(A 프로필 + 불가능한 목표) - envelope_id 별로 baseline
    시뮬레이션에서 직접 봉투 지출을 다시 구해 floor 를 재계산하고, 배분된
    cap 이 (반올림 오차 이내로) 그 floor 이상인지 검사한다.
    """

    engine: Engine = engines_6m["A_steady"]
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
# ENVELOPE_ADHERE: 리뷰 블로커 B5 - 지표가 "봉투별 잔여의 합" 이 아니라
# "전 봉투 AND" 인지 확인한다.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver"])
def test_goal_envelope_adhere_runs_for_every_profile(engines_6m, profile):
    engine: Engine = engines_6m[profile]
    req = _req("ENVELOPE_ADHERE")

    result = run_goal(engine, req)

    assert 0.0 <= result.achieve_prob <= 1.0
    assert 0.0 <= result.plan_achieve_prob <= 1.0
    assert 0.0 <= result.required.reduction_ratio <= 1.0
    assert result.weekly_caps  # 이번 달 말일까지 최소 1주차는 있어야 한다
    for week in result.weekly_caps:
        by_env_sum = sum(c.cap for c in week.by_envelope)
        assert abs(week.total_cap - by_env_sum) <= 1


def test_goal_envelope_adhere_is_and_not_sum(engines_6m):
    """블로커 B5 회귀 방지: "봉투별 잔여의 합" 방식이면 한 봉투의 큰 여유가
    다른 봉투들의 초과를 상쇄해 `achieve_prob` 이 양수로 나올 수 있다.
    실측(수정 전 코드로 A_steady 6개월 데이터를 직접 재계산)으로 이 합
    방식과 현재 AND 방식이 실제로 다른 값을 낸다는 것을 확인한다 - 같으면
    이 테스트가 우연히 통과하는 게 아니라 애초에 변별력이 없는 픽스처라는
    뜻이므로 그 자체로 회귀 탐지에 실패한 것이다."""

    engine: Engine = engines_6m["A_steady"]
    state = engine.state
    as_of = state.as_of
    target_date = state.cycle.budget_cycle_end
    horizon_days = (target_date - as_of).days

    req = _req("ENVELOPE_ADHERE")
    ctx = make_context(engine, req, horizon_days=horizon_days)
    base_sim = run_sim(ctx)

    budget_by_id = {e.envelope_id: e.budget for e in state.envelopes}
    idx = horizon_days

    # 옛 지표(수정 전 goal.py, 리뷰 §5-3): 봉투별 (budget - spent) 합 >= 0.
    remaining_sum = np.zeros(base_sim.envelope_spend.shape[0])
    for i, eid in enumerate(base_sim.envelope_ids):
        remaining_sum += budget_by_id.get(eid, 0) - base_sim.envelope_spend[:, i, idx].astype(
            np.float64
        )
    achieve_prob_sum = float(np.mean(remaining_sum >= 0))

    result = run_goal(engine, req)

    # AND 방식(현재 구현)은 합 방식보다 크거나 같을 수 없다 - 전 봉투가
    # 개별로 예산 이내인 경로 집합은 "잔여의 합이 0 이상"인 경로 집합의
    # 부분집합이다(초과 봉투가 있어도 다른 봉투 여유로 합은 여전히 0 이상일
    # 수 있으므로). 이 픽스처에서는 실제로 더 작다(변별력 확인).
    assert result.achieve_prob <= achieve_prob_sum
    assert result.achieve_prob < achieve_prob_sum


# ---------------------------------------------------------------------------
# horizon 범위 검증 (SPEC 8.4 "H = target_date - as_of, 1~365")
# ---------------------------------------------------------------------------


def test_goal_target_date_366_days_raises_e_req_range(engines_6m):
    engine: Engine = engines_6m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of + timedelta(days=366))

    with pytest.raises(FdtError) as exc_info:
        run_goal(engine, req)
    assert exc_info.value.code == E_REQ_RANGE


def test_goal_target_date_in_past_raises_e_req_range(engines_6m):
    engine: Engine = engines_6m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of - timedelta(days=1))

    with pytest.raises(FdtError) as exc_info:
        run_goal(engine, req)
    assert exc_info.value.code == E_REQ_RANGE


def test_goal_target_date_equal_as_of_raises_e_req_range(engines_6m):
    """H=0 도 1~365 범위 밖이다(SPEC 8.4)."""

    engine: Engine = engines_6m["A_steady"]
    as_of = engine.state.as_of
    req = _req("BALANCE", target_amount=1_000_000, target_date=as_of)

    with pytest.raises(FdtError) as exc_info:
        run_goal(engine, req)
    assert exc_info.value.code == E_REQ_RANGE


# ---------------------------------------------------------------------------
# validate_result (조건부: engine.run() 이 OK 를 낼 때만 - 배선 완료 시)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", ["A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver"])
def test_goal_validate_result_when_wired(engines_6m, profile):
    engine: Engine = engines_6m[profile]
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


def test_goal_reproducible_given_same_seed(engines_6m):
    engine: Engine = engines_6m["D_goal_saver"]
    req = _req("SAVE", target_amount=2_000_000, target_date=date(2026, 12, 31))

    result_1 = run_goal(engine, req)
    result_2 = run_goal(engine, req)

    assert result_1 == result_2


# ---------------------------------------------------------------------------
# 성능 (< 4s, SPEC 12장 성능 기준에 준한 GOAL 자체 기준 - PLAN 없음이라
# 작업 지시가 정한 상한)
# ---------------------------------------------------------------------------


def test_goal_performance_under_4_seconds(engines_6m):
    import time

    engine: Engine = engines_6m["D_goal_saver"]
    req = _req("SAVE", target_amount=2_000_000, target_date=date(2026, 12, 31))

    start = time.perf_counter()
    run_goal(engine, req)
    elapsed = time.perf_counter() - start

    assert elapsed < 4.0
