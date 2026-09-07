"""`fdt/engine/modes/whatif.py` 단위 테스트 (SPEC 8.3, PLAN 5.1/5.2 test_whatif).

`engine.run()` 의 WHATIF 배선은 W7 이 `modes.load_all()` 을 `Engine.run()` 에
연결해야 완성된다(작업 지시서 참조) - 이 파일은 그와 무관하게
`run_whatif(engine, req)` 를 직접 호출해서 검증한다. `validate_result`
통합 검증(§9.4)만 `engine.run()` 이 실제로 WHATIF 를 OK 로 돌려줄 때
조건부로 수행한다(`test_conditional_engine_run_validate`).
"""

from __future__ import annotations

import time
from datetime import date

import pytest

from fdt.engine import Engine
from fdt.engine.facts import build_facts
from fdt.engine.modes._common import make_context, run_sim
from fdt.engine.modes.whatif import classify_verdict, run_whatif
from fdt.engine.schemas.request import ModeRequest, WhatIfParams
from fdt.engine.taxonomy import ENVELOPE_IDS, Mode
from fdt.engine.viz import build_viz
from fdt.tools.validate import validate_result

_DINING = ENVELOPE_IDS["외식"]
_SHOPPING = ENVELOPE_IDS["쇼핑"]

_PROFILES = ["A_steady", "B_card_crunch", "C_impulsive", "D_goal_saver"]
_N_PATHS = 200
_SEED = 42
_HORIZON = 30


def _req(
    injections: list[dict],
    *,
    horizon_days: int = _HORIZON,
    n_paths: int = _N_PATHS,
) -> ModeRequest:
    return ModeRequest(
        mode=Mode.WHATIF,
        horizon_days=horizon_days,
        n_paths=n_paths,
        seed=_SEED,
        params=WhatIfParams(injections=injections),
    )


# ---------------------------------------------------------------------------
# 주입 0원 -> 델타 0
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", _PROFILES)
def test_zero_amount_spend_injection_gives_zero_delta(
    profile: str, engines_3m: dict[str, Engine]
) -> None:
    engine = engines_3m[profile]
    req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 5,
                "amount": 0,
                "envelope_id": _DINING,
                "method": "CASH",
            }
        ]
    )
    result = run_whatif(engine, req)

    assert result.delta.min_balance == 0
    assert result.delta.end_balance == 0
    assert result.delta.shortfall_prob == pytest.approx(0.0, abs=1e-9)
    assert result.delta.card_shortfall_prob == pytest.approx(0.0, abs=1e-9)
    assert result.delta.first_shortfall_date.base == result.delta.first_shortfall_date.branch
    # 주입이 0원이면 분기는 기준과 완전히 같은 시뮬레이션이다 - 판정은
    # "변화가 없다"가 아니라 그 프로필의 기준 상태 자체를 반영하므로(SPEC
    # 8.3.1 은 분기의 절대 수치도 본다, 예: B 프로필은 기준부터 이미
    # card_shortfall_prob 가 높아 DANGER 일 수 있다), 여기서는 base==branch
    # 라는 사실 자체만 검사한다.
    assert result.base.min_point.median_balance == result.branch.min_point.median_balance
    assert result.base.card_shortfall_prob == result.branch.card_shortfall_prob


# ---------------------------------------------------------------------------
# 단조성: 지출 주입 >= 0 -> 분기 최저 <= 기준 최저, 부족 확률 비감소
# (W6 함정: B 프로필 as_of+1..+6 은 카드 재시도 캐스케이드로 단조성이 깨질
# 수 있어 시점을 [0, 10, 25] 로 고정한다 - 작업 지시서 그대로)
# ---------------------------------------------------------------------------

_DAYS = [0, 10, 25]
_AMOUNTS = [10_000, 100_000, 1_000_000]
_METHODS = ["CASH", "CARD"]


@pytest.mark.parametrize("profile", _PROFILES)
@pytest.mark.parametrize("method", _METHODS)
@pytest.mark.parametrize("day", _DAYS)
def test_spend_injection_monotonic(
    profile: str, method: str, day: int, engines_3m: dict[str, Engine]
) -> None:
    engine = engines_3m[profile]
    branch_mins: list[int] = []
    shortfall_probs: list[float] = []
    for amount in _AMOUNTS:
        req = _req(
            [
                {
                    "type": "SPEND",
                    "days_from_now": day,
                    "amount": amount,
                    "envelope_id": _DINING,
                    "method": method,
                }
            ]
        )
        result = run_whatif(engine, req)
        # 불변식 그 자체: 지출 주입 >= 0 이면 분기 최저 <= 기준 최저.
        assert result.branch.min_point.median_balance <= result.base.min_point.median_balance
        assert result.branch.shortfall_prob >= result.base.shortfall_prob - 1e-9
        branch_mins.append(result.branch.min_point.median_balance)
        shortfall_probs.append(result.branch.shortfall_prob)

    # 금액이 커질수록(같은 기준 대비) 분기 최저는 비증가, 부족 확률은 비감소.
    for i in range(1, len(_AMOUNTS)):
        assert branch_mins[i] <= branch_mins[i - 1], (profile, method, day, branch_mins)
        assert shortfall_probs[i] >= shortfall_probs[i - 1] - 1e-9, (
            profile,
            method,
            day,
            shortfall_probs,
        )


@pytest.mark.parametrize("profile", _PROFILES)
def test_income_injection_improves_branch(profile: str, engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m[profile]
    req = _req([{"type": "INCOME", "days_from_now": 10, "amount": 500_000}])
    result = run_whatif(engine, req)
    assert result.branch.min_point.median_balance >= result.base.min_point.median_balance
    assert result.branch.shortfall_prob <= result.base.shortfall_prob + 1e-9


# ---------------------------------------------------------------------------
# 7종 주입 각 1 케이스
# ---------------------------------------------------------------------------


def test_injection_spend(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["A_steady"]
    req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 10,
                "amount": 150_000,
                "envelope_id": _DINING,
                "method": "CARD",
            }
        ]
    )
    result = run_whatif(engine, req)
    assert result.branch.min_point.median_balance <= result.base.min_point.median_balance
    assert result.delta.envelopes
    assert result.delta.envelopes[0].envelope_id == _DINING


def test_injection_income(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["A_steady"]
    req = _req([{"type": "INCOME", "days_from_now": 3, "amount": 1_000_000}])
    result = run_whatif(engine, req)
    assert result.delta.min_balance >= 0


def test_injection_recurring_spend(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["A_steady"]
    req = _req(
        [
            {
                "type": "RECURRING_SPEND",
                "start": date(2026, 9, 8),
                "every_days": 7,
                "amount": 20_000,
                "envelope_id": _SHOPPING,
                "method": "CASH",
            }
        ]
    )
    result = run_whatif(engine, req)
    assert result.branch.min_point.median_balance <= result.base.min_point.median_balance
    assert result.delta.envelopes[0].envelope_id == _SHOPPING


def test_injection_fixed_change_cancel(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["B_card_crunch"]
    zero_spend_req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 1,
                "amount": 0,
                "envelope_id": 1,
                "method": "CASH",
            }
        ]
    )
    ctx = make_context(engine, zero_spend_req)
    candidates = [
        item
        for item in ctx.committed
        if item.source_fixed_expense_id is not None and item.kind != "CARD_BILL"
    ]
    assert candidates, "B 프로필에 취소 가능한 고정비 큐 항목이 있어야 한다"
    target = min(candidates, key=lambda it: it.due)

    req = _req(
        [
            {
                "type": "FIXED_CHANGE",
                "fixed_expense_id": target.source_fixed_expense_id,
                "cancel": True,
                "from": target.due,
            }
        ]
    )
    result = run_whatif(engine, req)
    # 고정비 해지 -> 그 금액을 안 내므로 분기 말일 잔액은 기준 이상이어야 한다.
    assert result.branch.end_point.median_balance >= result.base.end_point.median_balance
    assert result.delta.end_balance >= 0


def test_injection_budget_change_behavior_follows_true_changes_gate(
    engines_3m: dict[str, Engine],
) -> None:
    """`behavior_follows=true` 는 `elasticity_gate` 기준(=budget_arr)을 바꾸고
    `false` 는 안 바꾼다 (PLAN 4 Phase 4 완료 조건). `simulate()` 내부
    `budgets_map` 은 `behavior_follows` 일 때만 갱신되므로, `run_sim` 이 돌려준
    `SimulationResult.envelope_budgets` 를 직접 비교해 확인한다(전이 규칙
    재구현이 아니라 시뮬레이터가 이미 계산한 값을 읽기만 한다)."""

    engine = engines_3m["A_steady"]
    req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 1,
                "amount": 0,
                "envelope_id": 1,
                "method": "CASH",
            }
        ]
    )
    ctx = make_context(engine, req)
    base_budget = ctx.state.envelope_by_id(_DINING).budget
    new_budget = max(10_000, base_budget // 5)

    inj_true = {
        "type": "BUDGET_CHANGE",
        "envelope_id": _DINING,
        "new_budget": new_budget,
        "behavior_follows": True,
    }
    inj_false = {**inj_true, "behavior_follows": False}

    from fdt.engine.schemas.request import BudgetChangeInjection

    sim_true = run_sim(ctx, injections=[BudgetChangeInjection.model_validate(inj_true)])
    sim_false = run_sim(ctx, injections=[BudgetChangeInjection.model_validate(inj_false)])

    assert sim_true.envelope_budgets[_DINING] == new_budget
    assert sim_false.envelope_budgets[_DINING] == base_budget


def test_injection_external_price_index(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["C_impulsive"]
    req = _req([{"type": "EXTERNAL", "price_index_mult": 1.1}])
    result = run_whatif(engine, req)

    ctx = make_context(engine, req)
    base_sim = run_sim(ctx)
    branch_sim = run_sim(ctx, injections=req.params.injections)
    base_stats = base_sim.stats(economic=True)
    branch_stats = branch_sim.stats(economic=True)

    total_base = sum(base_stats.envelope_spend_median.values())
    total_branch = sum(branch_stats.envelope_spend_median.values())
    if total_base > 0:
        ratio = total_branch / total_base
        assert 1.1 * 0.95 <= ratio <= 1.1 * 1.05
    assert result.crn is True


def test_injection_emergency_draw(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["D_goal_saver"]
    req = _req([{"type": "EMERGENCY_DRAW", "days_from_now": 5, "amount": 100_000}])
    result = run_whatif(engine, req)
    # 비상금 -> PRIMARY 이체는 유동성 총합을 보존하지만, 이체된 즉시 가용
    # 유동성(liquidity/economic)에는 편입되므로 분기 최저는 기준 이상이어야 한다.
    assert result.branch.min_point.median_balance >= result.base.min_point.median_balance


# ---------------------------------------------------------------------------
# 판정 3단계 경계값 (SPEC 8.3.1) - 시뮬레이션과 분리된 순수 함수로 직접 검사
# ---------------------------------------------------------------------------


def test_verdict_danger_by_card_shortfall() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=900_000,
        branch_card_shortfall_prob=0.5,
        delta_shortfall_prob=0.0,
    )
    assert v == "DANGER"


def test_verdict_danger_by_negative_branch_min() -> None:
    v = classify_verdict(
        base_min_balance=100,
        branch_min_balance=-1,
        branch_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.0,
    )
    assert v == "DANGER"


def test_verdict_caution_by_delta_shortfall() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=900_000,
        branch_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.15,
    )
    assert v == "CAUTION"


def test_verdict_caution_by_min_ratio() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=499_999,
        branch_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.0,
    )
    assert v == "CAUTION"


def test_verdict_ok() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=900_000,
        branch_card_shortfall_prob=0.1,
        delta_shortfall_prob=0.05,
    )
    assert v == "OK"


def test_verdict_ok_boundary_just_under_thresholds() -> None:
    # delta_shortfall_prob 가 문턱보다 살짝 작고, ratio 문턱도 살짝 넘는 경우.
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=500_001,
        branch_card_shortfall_prob=0.499,
        delta_shortfall_prob=0.149,
    )
    assert v == "OK"


# ---------------------------------------------------------------------------
# 재현성
# ---------------------------------------------------------------------------


def test_reproducibility(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["A_steady"]
    req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 5,
                "amount": 150_000,
                "envelope_id": _DINING,
                "method": "CARD",
            }
        ]
    )
    r1 = run_whatif(engine, req)
    r2 = run_whatif(engine, req)
    assert r1.model_dump(mode="json") == r2.model_dump(mode="json")


# ---------------------------------------------------------------------------
# 성능: WHATIF(2회) < 3s, n_paths=1000
# ---------------------------------------------------------------------------


def test_performance(seed_engine_A: Engine) -> None:
    req = ModeRequest(
        mode=Mode.WHATIF,
        horizon_days=30,
        n_paths=1000,
        seed=42,
        params=WhatIfParams(
            injections=[
                {
                    "type": "SPEND",
                    "days_from_now": 10,
                    "amount": 150_000,
                    "envelope_id": _DINING,
                    "method": "CARD",
                }
            ]
        ),
    )
    start = time.perf_counter()
    run_whatif(seed_engine_A, req)
    elapsed = time.perf_counter() - start
    assert elapsed < 3.0, elapsed


# ---------------------------------------------------------------------------
# validate_result 통합 검증 - engine.run() 이 WHATIF 를 실제로 OK 로 배선했을
# 때만 수행한다(W7 이 modes.load_all() 을 Engine.run() 에 연결하기 전까지는
# E-MODE-NOT_IMPLEMENTED 로 끝나는 게 정상이다). 어느 경로든 테스트는 통과한다.
# ---------------------------------------------------------------------------


def test_conditional_engine_run_validate(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["A_steady"]
    req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 10,
                "amount": 150_000,
                "envelope_id": _DINING,
                "method": "CARD",
            }
        ]
    )
    engine_result = engine.run(req)

    if engine_result.status == "OK":
        assert engine_result.result is not None
        facts = build_facts(Mode.WHATIF, engine_result.result, as_of=engine.state.as_of)
        viz = build_viz(Mode.WHATIF, engine_result.result, facts, as_of=engine.state.as_of)
        engine_result.facts = facts
        engine_result.viz = viz
        report = validate_result(engine_result)
        assert report.ok, report.errors
    else:
        # 아직 배선 전: 모드 미구현 오류만 정상으로 인정한다.
        assert engine_result.error is not None
        assert engine_result.error.code in {"E-MODE-NOT_IMPLEMENTED", "E-MODE-NOT-IMPLEMENTED"}


# ---------------------------------------------------------------------------
# 4 프로필 요약(보고용 스모크 - 카드 15만원 10일 뒤)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", _PROFILES)
def test_profile_smoke_card_150k_in_10_days(profile: str, engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m[profile]
    req = _req(
        [
            {
                "type": "SPEND",
                "days_from_now": 10,
                "amount": 150_000,
                "envelope_id": _DINING,
                "method": "CARD",
            }
        ]
    )
    result = run_whatif(engine, req)
    assert result.verdict in {"OK", "CAUTION", "DANGER"}
    assert result.branch.min_point.median_balance <= result.base.min_point.median_balance
