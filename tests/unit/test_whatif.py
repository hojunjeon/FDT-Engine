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
from fdt.engine.modes._common import level_from_probs, make_context, run_sim
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
# (원래는 B 프로필 as_of+1..+6 이 카드 재시도 캐스케이드로 단조성이 깨질 수
# 있어 [0, 10, 25] 로만 고정했었다 - 리뷰 20260907_W6_W10.md 항목 4b 가 밝힌
# 위반 1/192(C_impulsive, days_from_now=6, 5만원)의 원인이 이탈 (b)(현금
# 소비 전부-또는-전무 게이트)였고, W6/J1 이 블로커 B2 로 부분 체결로
# 고쳤으므로 1..6 도 표본에 포함한다 - 위반이 여전히 남으면 이 테스트가
# 그대로 실패해 보고 대상이 된다.)
# ---------------------------------------------------------------------------

_DAYS = [0, 1, 2, 3, 4, 5, 6, 10, 25]
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
    """블로커 B3 수정 확인(리뷰 20260907_W6_W10.md §4d): `behavior_follows`
    와 무관하게 **표시 예산**(`envelope_budgets`, 봉투 remaining/overrun_prob
    계산에 쓰는 값)은 항상 새 예산으로 바뀐다 - 예전에는 `false` 가 아무
    효과도 없어(예산 자체도 그대로) "예산만 줄이면 얼마나 초과하나?" 라는
    질문에 조용히 0 을 답하는 결함이 있었다.

    `elasticity_gate` **문턱**(내부 `gate_budget_arr`, 스키마에 노출되지
    않는다)은 `behavior_follows=true` 일 때만 새 예산을 본다 - `false` 는
    원래 예산 기준으로 게이트를 판정한다. 이 차이를 직접 관측할 수는
    없으므로(전이 규칙 재구현 금지), 두 분기의 그 봉투 지출 중앙값이
    달라진다는 사실(문턱이 실제로 다른 값을 보고 있다는 간접 증거)로
    검증한다 - 방향은 봉투의 elasticity 값(>1 이면 문턱 초과 시 오히려
    소비가 늘 수 있다, 리뷰 5-2)에 따라 달라지므로 단정하지 않는다."""

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
        ],
        horizon_days=60,
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

    # B3: 표시 예산은 behavior_follows 와 무관하게 새 예산으로 바뀐다.
    assert sim_true.envelope_budgets[_DINING] == new_budget
    assert sim_false.envelope_budgets[_DINING] == new_budget

    # gate 문턱만 다르므로(true=새 예산, false=원 예산) 그 봉투 지출
    # 중앙값이 서로 달라야 한다 - 문턱이 정말 분리돼 있다는 간접 증거.
    spend_true = sim_true.stats().envelope_spend_median.get(_DINING, 0)
    spend_false = sim_false.stats().envelope_spend_median.get(_DINING, 0)
    assert spend_true != spend_false


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
        # `EXTERNAL(price_index_mult)` 도 `elasticity_gate` 문턱이 보는
        # 누적치를 통해 λ 를 흔든다(리뷰 4a/N6, S46 이 근본 해결 대상으로
        # 남겨 둔 항목 - CRN 이 이 주입에 대해 완전히 성립하지 않는다).
        # C 프로필은 억제 게이트가 상시 발동해 이 오염이 가장 크게 나타나
        # 순수 10% 근처가 아니라 넓은 허용폭이 필요하다 - "정확히 1.10배"
        # 를 보증하는 테스트가 아니라 "터무니없이 벗어나지 않는다" 만 검사.
        assert 1.1 * 0.8 <= ratio <= 1.1 * 1.2
    assert result.crn is True


def test_injection_emergency_draw(engines_3m: dict[str, Engine]) -> None:
    engine = engines_3m["D_goal_saver"]
    req = _req([{"type": "EMERGENCY_DRAW", "days_from_now": 5, "amount": 100_000}])
    result = run_whatif(engine, req)
    # 비상금 -> PRIMARY 이체는 유동성 총합을 보존하지만, 이체된 즉시 가용
    # 유동성(liquidity/economic)에는 편입되므로 분기 최저는 기준 이상이어야 한다.
    assert result.branch.min_point.median_balance >= result.base.min_point.median_balance


# ---------------------------------------------------------------------------
# 판정 3단계 경계값 (SPEC 8.3.1 + 리뷰 S52 재정의) - 시뮬레이션과 분리된
# 순수 함수로 직접 검사. `verdict` 는 이제 델타(주입의 효과) 기준만 본다 -
# 분기의 절대 위험은 `test_level_from_probs_*`(아래) 가 따로 검사한다.
# ---------------------------------------------------------------------------


def test_verdict_danger_by_delta_card_shortfall() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=900_000,
        delta_card_shortfall_prob=0.3,
        delta_shortfall_prob=0.0,
    )
    assert v == "DANGER"


def test_verdict_danger_by_newly_negative_branch_min() -> None:
    # 기준 최저는 0 이상이었는데 주입 이후 분기 최저가 마이너스로 떨어짐.
    v = classify_verdict(
        base_min_balance=100,
        branch_min_balance=-1,
        delta_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.0,
    )
    assert v == "DANGER"


def test_verdict_not_danger_when_base_already_negative() -> None:
    # 기준 최저가 이미 마이너스면(기준선 자체의 절대 위험) "새로 마이너스가
    # 됨" 조건이 아니다 - S52: 기준선의 절대 위험이 verdict 를 삼키지 않는다.
    v = classify_verdict(
        base_min_balance=-500,
        branch_min_balance=-1_000,
        delta_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.0,
    )
    assert v != "DANGER"


def test_verdict_caution_by_delta_shortfall() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=900_000,
        delta_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.15,
    )
    assert v == "CAUTION"


def test_verdict_caution_by_min_ratio() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=499_999,
        delta_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.0,
    )
    assert v == "CAUTION"


def test_verdict_ok() -> None:
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=900_000,
        delta_card_shortfall_prob=0.1,
        delta_shortfall_prob=0.05,
    )
    assert v == "OK"


def test_verdict_ok_boundary_just_under_thresholds() -> None:
    # delta_shortfall_prob 가 문턱보다 살짝 작고, ratio 문턱도 살짝 넘는 경우.
    v = classify_verdict(
        base_min_balance=1_000_000,
        branch_min_balance=500_001,
        delta_card_shortfall_prob=0.299,
        delta_shortfall_prob=0.149,
    )
    assert v == "OK"


# ---------------------------------------------------------------------------
# `branch_level` (S52) - 분기의 절대 위험. RISK `risk_score`/`level` 규칙
# 재사용(`level_from_probs`). C 프로필처럼 기준선 자체가 이미 위험해도
# `verdict` 는 델타만 보고, `branch_level` 이 그 절대 위험을 담는다.
# ---------------------------------------------------------------------------


def test_level_from_probs_safe() -> None:
    assert level_from_probs(0.0, 0.0) == "SAFE"


def test_level_from_probs_warning() -> None:
    # score = round(100 * max(0.3, 0.6*0.1)) = 30 -> WARNING
    assert level_from_probs(0.1, 0.3) == "WARNING"


def test_level_from_probs_danger() -> None:
    assert level_from_probs(1.0, 1.0) == "DANGER"


def test_verdict_can_be_ok_while_branch_level_is_danger() -> None:
    """C 프로필처럼 기준선이 이미 위험(card_shortfall_prob=1.0)한데 주입
    효과(델타)가 0이면 - verdict 는 OK, branch_level 은 DANGER 여야 한다
    (리뷰 §4c: "C 에 대한 WHATIF 는 무엇을 물어도 DANGER" 문제의 수정)."""

    verdict = classify_verdict(
        base_min_balance=-935_254,
        branch_min_balance=-935_254,
        delta_card_shortfall_prob=0.0,
        delta_shortfall_prob=0.0,
    )
    branch_level = level_from_probs(1.0, 1.0)
    assert verdict == "OK"
    assert branch_level == "DANGER"


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
    assert result.branch_level in {"SAFE", "WARNING", "DANGER"}
    assert result.branch.min_point.median_balance <= result.base.min_point.median_balance
