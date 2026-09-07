"""OPTIMIZE 모드 러너 (SPEC 8.6).

AUTO 후보 생성(8.6.1) -> 단일 후보 전부 CRN 평가 -> 상위 `k=6` -> 2~
`max_actions` 그리디 조합(8.6.2) 순으로 진행한다. 시뮬레이터/전이 규칙은
재구현하지 않고 `simulate()`(`run_sim` 경유)만 반복 호출한다.

카드 출금 요일 변경 후보(8.6.1 4번째 항목, `override.card_withdrawal_weekday`)
는 `AppliedAction.injection` 이 7종 `Injection` 유니온만 담을 수 있어(S9)
표현할 방법이 없다 - v0.1 에서는 제외한다(작업 지시 및 보고 참조).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import numpy as np

from fdt.engine import taxonomy
from fdt.engine.modes import register
from fdt.engine.modes._common import SimContext, make_context, run_sim
from fdt.engine.schemas.request import (
    BudgetChangeInjection,
    EmergencyDrawInjection,
    FixedChangeInjection,
    GoalParams,
    Injection,
    ModeRequest,
    OptimizeConstraints,
    OptimizeParams,
)
from fdt.engine.schemas.result import (
    AppliedAction,
    OptimizeBaseline,
    OptimizeResult,
    RankedAction,
    Recommended,
)
from fdt.engine.schemas.simulate import PathStats
from fdt.engine.schemas.state import State
from fdt.engine.simulate import SimulationResult
from fdt.engine.taxonomy import Mode

__all__ = ["run_optimize"]

# SPEC 8.6.2 "총 시뮬 횟수 <= 40", "상위 k=6". max_actions 는 1~3(S10).
_SIM_BUDGET = 40
_TOP_K = 6
_CUT_RATIOS: tuple[float, ...] = (0.1, 0.2, 0.3)

# n_paths 자동 하향(SPEC 8.6.2, §12 "n_paths 400 으로 자동 하향") 판단 기준.
# SPEC 은 정확한 임계값을 정의하지 않는다 - "후보 수 x n_paths" 총 작업량이
# 이 값을 넘으면 400 으로 낮춘다(요청값이 이미 400 이하면 그대로 둔다).
_N_PATHS_DOWNSHIFT_WORKLOAD = 8000
_DOWNSHIFTED_N_PATHS = 400


@dataclass
class Candidate:
    """AUTO/사용자 후보 1건 (아직 평가되지 않은 상태).

    `key` 는 조합 그리디에서 같은 후보를 두 번 뽑지 않게 막는 dedup 키다.
    `envelope_id` 가 있으면(=BUDGET_CHANGE) 그리디가 "한 봉투에 두 비율
    동시 금지"(SPEC 8.6.2)를 그 값으로 판단한다.
    """

    key: tuple[Any, ...]
    injection: Injection
    label: str | None
    cut_ratio: float | None
    envelope_id: int | None
    cost_of_action: str
    feasibility_note: str | None


@dataclass
class _Entry:
    """평가를 마친 후보(단일 또는 조합) 1건. 순위 정렬·직렬화의 재료."""

    candidates: list[Candidate]
    value: float
    end_balance_median: float
    effect: dict[str, float | int | str]
    feasibility_note: str | None


def _auto_budget_candidates(state: State, constraints: OptimizeConstraints) -> list[Candidate]:
    """유연(+ protect_essential=false 면 필수) 봉투 -10/-20/-30% (SPEC 8.6.1)."""

    names = set(taxonomy.FLEXIBLE_ENVELOPES)
    if not constraints.protect_essential:
        names |= set(taxonomy.ESSENTIAL_ENVELOPES)

    out: list[Candidate] = []
    for name in sorted(names):
        eid = taxonomy.ENVELOPE_IDS[name]
        env = state.envelope_by_id(eid)
        if env is None or env.budget <= 0:
            continue
        for ratio in _CUT_RATIOS:
            if ratio > constraints.max_cut_ratio + 1e-9:
                continue
            new_budget = round(env.budget * (1 - ratio))
            cut_amount = env.budget - new_budget
            out.append(
                Candidate(
                    key=("BUDGET", eid, ratio),
                    injection=BudgetChangeInjection(
                        envelope_id=eid, new_budget=new_budget, behavior_follows=True
                    ),
                    label=f"{name} 예산 {round(ratio * 100)}% 축소",
                    cut_ratio=ratio,
                    envelope_id=eid,
                    cost_of_action=f"{name} 월 {cut_amount:,}원 감소",
                    feasibility_note=(
                        f"이번 달 이미 사용 {env.spent:,}원, "
                        f"남은 한도 {new_budget - env.spent:,}원"
                    ),
                )
            )
    return out


def _auto_subscription_candidates(ctx: SimContext) -> list[Candidate]:
    """활성 SUBSCRIPTION 고정비 각각 해지 (SPEC 8.6.1)."""

    as_of = ctx.state.as_of
    out: list[Candidate] = []
    seen: set[int] = set()
    for item in ctx.committed:
        if item.kind != "SUBSCRIPTION" or item.source_fixed_expense_id is None:
            continue
        fx_id = item.source_fixed_expense_id
        if fx_id in seen:
            continue
        seen.add(fx_id)
        out.append(
            Candidate(
                key=("SUB", fx_id),
                injection=FixedChangeInjection(
                    fixed_expense_id=fx_id,
                    cancel=True,
                    **{"from": as_of + timedelta(days=1)},  # type: ignore[arg-type]
                ),
                label=f"{item.name} 구독 해지",
                cut_ratio=None,
                envelope_id=None,
                cost_of_action=f"{item.name} 월 {item.amount:,}원 절감",
                feasibility_note=None,
            )
        )
    return out


def _auto_candidates(ctx: SimContext, constraints: OptimizeConstraints) -> list[Candidate]:
    return _auto_budget_candidates(ctx.state, constraints) + _auto_subscription_candidates(ctx)


def _emergency_draw_candidate(
    state: State, baseline_eco: PathStats
) -> Candidate | None:
    """비상금 이체 후보 (허용 시, 부족액만큼) (SPEC 8.6.1)."""

    if baseline_eco.min_balance >= 0:
        return None
    deficit = -baseline_eco.min_balance
    amount = min(deficit, state.emergency_fund)
    if amount <= 0:
        return None
    return Candidate(
        key=("EMERGENCY",),
        injection=EmergencyDrawInjection(on=baseline_eco.min_balance_date, amount=amount),
        label="비상금 이체",
        cut_ratio=None,
        envelope_id=None,
        cost_of_action=f"비상금 {amount:,}원 이체",
        feasibility_note=f"비상금 잔액 {state.emergency_fund:,}원 중 {amount:,}원 사용",
    )


def _user_candidates(injections: Sequence[Injection], state: State) -> list[Candidate]:
    """`params.candidates` 가 injections 목록이면 각 항목이 후보 1건이다."""

    out: list[Candidate] = []
    for i, inj in enumerate(injections):
        cut_ratio: float | None = None
        envelope_id: int | None = None
        if inj.type == "BUDGET_CHANGE":
            envelope_id = inj.envelope_id
            env = state.envelope_by_id(inj.envelope_id)
            if env is not None and env.budget > 0:
                cut_ratio = 1 - inj.new_budget / env.budget
        out.append(
            Candidate(
                key=("USER", i),
                injection=inj,
                label=None,
                cut_ratio=cut_ratio,
                envelope_id=envelope_id,
                cost_of_action=f"사용자 지정 행동 {i + 1}",
                feasibility_note=None,
            )
        )
    return out


def _budgets_for(injections: Sequence[Injection], state: State) -> dict[int, int]:
    budgets = {env.envelope_id: env.budget for env in state.envelopes}
    for inj in injections:
        if inj.type == "BUDGET_CHANGE" and inj.behavior_follows:
            budgets[inj.envelope_id] = inj.new_budget
    return budgets


def _achieve_prob(
    sim: SimulationResult, ctx: SimContext, goal: GoalParams, injections: Sequence[Injection]
) -> float:
    """REACH_GOAL 지표 (SPEC 8.4 정의를 여기서 간단히 재사용, GOAL 모듈 미참조)."""

    idx = ctx.horizon_days
    if goal.goal_type == "BALANCE":
        target = goal.target_amount
        assert target is not None
        return float((sim.balances[:, idx] >= target).mean())
    if goal.goal_type == "SAVE":
        target = goal.target_amount
        assert target is not None
        increase = sim.balances[:, idx] - sim.balances[:, 0]
        return float((increase >= target).mean())

    # ENVELOPE_ADHERE: 목표 기간(이번 달 말) 끝에 전 봉투가 예산 내인 경로 비율.
    budgets = _budgets_for(injections, ctx.state)
    n_paths = sim.balances.shape[0]
    ok = np.ones(n_paths, dtype=bool)
    for i, eid in enumerate(sim.envelope_ids):
        ok &= sim.envelope_spend[:, i, idx] <= budgets.get(eid, 0)
    return float(ok.mean())


def _objective_value(
    sim: SimulationResult, ctx: SimContext, params: OptimizeParams, injections: Sequence[Injection]
) -> float:
    if params.objective == "MIN_SHORTFALL_PROB":
        s = sim.stats(economic=False)
        return max(s.shortfall_prob, s.card_shortfall_prob)
    if params.objective == "MAX_END_BALANCE":
        return float(sim.stats(economic=False).end_balance_median)
    assert params.goal is not None
    return _achieve_prob(sim, ctx, params.goal, injections)


def _rank_key(objective: str, value: float, end_balance_median: float) -> tuple[float, float]:
    """오름차순 정렬 키. 앞이 작을수록 좋다(SPEC 8.6.2 순위).

    MIN_SHORTFALL_PROB 는 값 자체가 낮을수록 좋고, MAX_END_BALANCE 와
    REACH_GOAL 은 값이 높을수록 좋으므로 부호를 뒤집는다. 동률이면
    end_balance_median 이 큰 쪽을 우선한다(SPEC 8.6 "동률이면 end_balance
    큰 쪽" - MAX_END_BALANCE/REACH_GOAL 에도 같은 동률 규칙을 확장 적용).
    """

    primary = value if objective == "MIN_SHORTFALL_PROB" else -value
    return (primary, -end_balance_median)


def _improves(objective: str, new_value: float, cur_value: float) -> bool:
    if objective == "MIN_SHORTFALL_PROB":
        return new_value < cur_value - 1e-12
    return new_value > cur_value + 1e-12


def _make_entry(
    candidates: list[Candidate],
    value: float,
    stats_real: PathStats,
    objective: str,
    baseline_value: float,
) -> _Entry:
    delta = value - baseline_value
    cost = "; ".join(c.cost_of_action for c in candidates)
    notes = [c.feasibility_note for c in candidates if c.feasibility_note]
    feasibility_note = "; ".join(notes) if notes else None

    effect: dict[str, float | int | str] = {
        "shortfall_prob": stats_real.shortfall_prob,
        "card_shortfall_prob": stats_real.card_shortfall_prob,
        "end_balance_median": float(stats_real.end_balance_median),
        "delta": float(delta),
        "cost_of_action": cost,
    }
    if objective == "REACH_GOAL":
        effect["achieve_prob"] = value

    return _Entry(
        candidates=candidates,
        value=value,
        end_balance_median=float(stats_real.end_balance_median),
        effect=effect,
        feasibility_note=feasibility_note,
    )


@register(Mode.OPTIMIZE)
def run_optimize(engine, req: ModeRequest) -> OptimizeResult:
    params = req.params
    # `ModeRequest._parse_params_by_mode`/`_check_params_match_mode` 가 mode 로
    # params 클래스를 이미 확정했다(request.py) - mypy 를 위한 좁히기.
    assert isinstance(params, OptimizeParams)
    constraints = params.constraints
    state = engine.state
    as_of = state.as_of

    if params.objective == "REACH_GOAL":
        goal = params.goal
        assert goal is not None
        if goal.goal_type == "ENVELOPE_ADHERE":
            horizon_days = (state.cycle.budget_cycle_end - as_of).days
        else:
            assert goal.target_date is not None
            horizon_days = (goal.target_date - as_of).days
        horizon_days = max(1, min(365, horizon_days))
    else:
        horizon_days = req.horizon_days

    ctx = make_context(engine, req, horizon_days=horizon_days)

    candidates_param = params.candidates
    candidates_is_auto = isinstance(candidates_param, str)
    if isinstance(candidates_param, str):
        pre_candidates = _auto_candidates(ctx, constraints)
        upper_count = len(pre_candidates) + (1 if constraints.allow_emergency_draw else 0)
    else:
        pre_candidates = _user_candidates(candidates_param, state)
        upper_count = len(pre_candidates)

    # n_paths 자동 하향(SPEC 8.6.2/§12) - baseline 을 포함한 이 호출의 모든
    # simulate() 가 같은 n_paths 를 써야 CRN 비교가 성립하므로, 첫 시뮬 전에
    # 후보 수를 먼저 세어 결정한다.
    if (
        upper_count * req.n_paths > _N_PATHS_DOWNSHIFT_WORKLOAD
        and ctx.n_paths > _DOWNSHIFTED_N_PATHS
    ):
        ctx.n_paths = _DOWNSHIFTED_N_PATHS

    sim_calls = 0
    baseline_sim = run_sim(ctx)
    sim_calls += 1
    baseline_stats = baseline_sim.stats(economic=False)
    baseline_stats_eco = baseline_sim.stats(economic=True)
    baseline_value = _objective_value(baseline_sim, ctx, params, ())

    baseline_result = OptimizeBaseline(
        shortfall_prob=baseline_stats.shortfall_prob,
        card_shortfall_prob=baseline_stats.card_shortfall_prob,
        end_balance_median=float(baseline_stats.end_balance_median),
    )

    if candidates_is_auto and constraints.allow_emergency_draw:
        emergency = _emergency_draw_candidate(state, baseline_stats_eco)
        if emergency is not None:
            pre_candidates.append(emergency)

    candidates = pre_candidates

    if not candidates:
        return OptimizeResult(
            objective=params.objective,
            baseline=baseline_result,
            ranked=[],
            recommended=None,
            evaluated=0,
            sim_calls=sim_calls,
        )

    k = min(_TOP_K, len(candidates))
    # 2..max_actions 조합 그리디의 각 단계는 남은 top-k 후보를 최대
    # (k - 이미 고른 개수)개 시도한다(SPEC 8.6.2) - 이 상한을 먼저 예약해
    # 총 호출이 40 을 넘으면 단일 후보 쪽을 잘라낸다(문서화 대상).
    combo_reserve = sum(max(0, k - i) for i in range(1, params.max_actions))
    allowed_singles = max(0, _SIM_BUDGET - sim_calls - combo_reserve)
    truncated = candidates[:allowed_singles] if len(candidates) > allowed_singles else candidates

    single_entries: list[_Entry] = []
    for cand in truncated:
        sim = run_sim(ctx, injections=[cand.injection])
        sim_calls += 1
        stats_real = sim.stats(economic=False)
        value = _objective_value(sim, ctx, params, [cand.injection])
        single_entries.append(
            _make_entry([cand], value, stats_real, params.objective, baseline_value)
        )

    single_entries.sort(key=lambda e: _rank_key(params.objective, e.value, e.end_balance_median))
    top_k_entries = single_entries[: min(_TOP_K, len(single_entries))]

    all_entries: list[_Entry] = list(single_entries)

    if params.max_actions >= 2 and top_k_entries:
        best = top_k_entries[0]
        combo_candidates = list(best.candidates)
        combo_value = best.value
        used_keys = {c.key for c in combo_candidates}
        used_env_ids = {c.envelope_id for c in combo_candidates if c.envelope_id is not None}
        combo_final_stats: PathStats | None = None

        for _step in range(2, params.max_actions + 1):
            pool = [
                e
                for e in top_k_entries
                if e.candidates[0].key not in used_keys
                and (
                    e.candidates[0].envelope_id is None
                    or e.candidates[0].envelope_id not in used_env_ids
                )
            ]
            if not pool:
                break
            base_injections = [c.injection for c in combo_candidates]
            best_choice: Candidate | None = None
            best_value: float | None = None
            best_stats: PathStats | None = None
            for cand_entry in pool:
                cand = cand_entry.candidates[0]
                trial_injections = [*base_injections, cand.injection]
                sim = run_sim(ctx, injections=trial_injections)
                sim_calls += 1
                stats_real = sim.stats(economic=False)
                value = _objective_value(sim, ctx, params, trial_injections)
                if best_value is None or _improves(params.objective, value, best_value):
                    best_choice = cand
                    best_value = value
                    best_stats = stats_real

            if (
                best_choice is None
                or best_value is None
                or not _improves(params.objective, best_value, combo_value)
            ):
                break

            combo_candidates = [*combo_candidates, best_choice]
            used_keys.add(best_choice.key)
            if best_choice.envelope_id is not None:
                used_env_ids.add(best_choice.envelope_id)
            combo_value = best_value
            combo_final_stats = best_stats

        if len(combo_candidates) >= 2 and combo_final_stats is not None:
            all_entries.append(
                _make_entry(
                    combo_candidates, combo_value, combo_final_stats, params.objective,
                    baseline_value,
                )
            )

    all_entries.sort(key=lambda e: _rank_key(params.objective, e.value, e.end_balance_median))

    ranked: list[RankedAction] = []
    for i, entry in enumerate(all_entries, start=1):
        ranked.append(
            RankedAction(
                rank=i,
                actions=[
                    AppliedAction(injection=c.injection, cut_ratio=c.cut_ratio, label=c.label)
                    for c in entry.candidates
                ],
                effect=entry.effect,
                feasibility_note=entry.feasibility_note,
            )
        )

    recommended: Recommended | None = None
    if ranked:
        top_entry = all_entries[0]
        combined_effect: dict[str, Any] = dict(top_entry.effect)
        combined_effect["n_paths_used"] = ctx.n_paths
        recommended = Recommended(rank=1, combined_effect=combined_effect)

    return OptimizeResult(
        objective=params.objective,
        baseline=baseline_result,
        ranked=ranked,
        recommended=recommended,
        evaluated=max(0, sim_calls - 1),
        sim_calls=sim_calls,
    )
