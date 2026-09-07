"""OPTIMIZE 모드 러너 (SPEC 8.6).

AUTO 후보 생성(8.6.1) -> 단일 후보 전부 CRN 평가 -> 상위 `k=6` -> 2~
`max_actions` 그리디 조합(8.6.2) 순으로 진행한다. 시뮬레이터/전이 규칙은
재구현하지 않고 `simulate()`(`run_sim` 경유)만 반복 호출한다.

목적함수(S56, 리뷰 B7): 세 `objective` 전부 **다단 사전식(lexicographic)**
값으로 비교한다. 확률이 0.0/1.0 에 포화되는 프로필(A/C/D 실측)에서 1차 항만
쓰면 전 후보가 동률이 되어 `ranked_bars` 가 빈 차트가 되므로, 2차 이하 항이
포화 구간을 갈라 순위를 살아있게 만든다:

- `MIN_SHORTFALL_PROB`: `(max(sp, csp), 기대 부족액, -최저 경제 잔액 중앙값,
  -말일 잔액 중앙값)`
- `MAX_END_BALANCE`: `(-말일 잔액 중앙값, max(sp, csp), 기대 부족액)`
- `REACH_GOAL`: `(-달성 확률, max(sp, csp), -말일 잔액 중앙값)`

전부 오름차순 정렬(작을수록 좋다)이 되도록 부호를 미리 맞춘 "정렬 키"다.
`effect["delta"]`/`effect["delta_dim"]` 은 정렬 키가 아니라 **원래 단위의
값**으로, 순위를 실제로 가른 첫 차원(기준선과 유의미하게 다른 첫 차원)의
(후보 - 기준) 값과 그 차원 이름을 담는다 - 1차 항이 포화돼 0 이어도 2차 항이
값을 실어 `ranked_bars` 가 죽지 않는다.

카드 출금 요일 변경 후보(8.6.1 4번째 항목)는 `AppliedAction.override`
(`OverrideSpec`, S57)로 표현한다 - `Injection` 유니온은 이 오버라이드를 담을
방법이 없어(N13) `AppliedAction` 이 `injection`/`override` 중 하나를
고르게 확장됐다.
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
    OverrideSpec,
    RankedAction,
    Recommended,
)
from fdt.engine.schemas.simulate import PathStats
from fdt.engine.schemas.state import State
from fdt.engine.simulate import Overrides, SimulationResult
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

# 사전식 목적값 비교/구분 시 "실질적으로 다르다"고 볼 허용 오차. 확률(0..1)과
# 원 단위 금액을 같은 상수로 비교하지만, 두 스케일 모두 같은 결정론적 CRN
# 계산에서 나오므로 진짜 무변화가 아니면 이 값을 훨씬 넘게 갈린다.
_DIM_EPS = 1e-6

_WEEKDAY_NAMES_KO = ("월", "화", "수", "목", "금", "토", "일")

_DIM_NAMES: dict[str, tuple[str, ...]] = {
    "MIN_SHORTFALL_PROB": (
        "shortfall_prob_max",
        "expected_shortfall",
        "min_economic_balance_median",
        "end_balance_median",
    ),
    "MAX_END_BALANCE": (
        "end_balance_median",
        "shortfall_prob_max",
        "expected_shortfall",
    ),
    "REACH_GOAL": (
        "achieve_prob",
        "shortfall_prob_max",
        "end_balance_median",
    ),
}


@dataclass
class ActionUnit:
    """`AppliedAction` 하나가 될 조각. `injection`/`override_*` 중 정확히
    하나만 채운다(S57)."""

    injection: Injection | None
    override_card_id: int | None
    override_weekday: int | None
    cut_ratio: float | None
    label: str | None

    def to_applied_action(self) -> AppliedAction:
        if self.injection is not None:
            return AppliedAction(
                injection=self.injection, cut_ratio=self.cut_ratio, label=self.label
            )
        assert self.override_card_id is not None and self.override_weekday is not None
        return AppliedAction(
            override=OverrideSpec(card_id=self.override_card_id, weekday=self.override_weekday),
            cut_ratio=self.cut_ratio,
            label=self.label,
        )


@dataclass
class Candidate:
    """AUTO/사용자 후보 1건 (아직 평가되지 않은 상태).

    `key` 는 조합 그리디에서 같은 후보를 두 번 뽑지 않게 막는 dedup 키다.
    `envelope_id` 가 있으면(=BUDGET_CHANGE) 그리디가 "한 봉투에 두 비율
    동시 금지"(SPEC 8.6.2)를 그 값으로 판단한다. `units` 는 보통 원소 1개지만
    카드 출금 요일 변경(8.6.1 4번째 항목)처럼 카드 여러 장을 한 번에
    바꾸는 후보는 카드마다 하나씩 여러 `ActionUnit` 을 담는다.
    """

    key: tuple[Any, ...]
    units: list[ActionUnit]
    envelope_id: int | None
    cost_of_action: str
    feasibility_note: str | None
    override: Overrides | None = None

    @property
    def injections(self) -> list[Injection]:
        return [u.injection for u in self.units if u.injection is not None]


def _single_injection_candidate(
    *,
    key: tuple[Any, ...],
    injection: Injection,
    label: str | None,
    cut_ratio: float | None,
    envelope_id: int | None,
    cost_of_action: str,
    feasibility_note: str | None,
) -> Candidate:
    return Candidate(
        key=key,
        units=[
            ActionUnit(
                injection=injection,
                override_card_id=None,
                override_weekday=None,
                cut_ratio=cut_ratio,
                label=label,
            )
        ],
        envelope_id=envelope_id,
        cost_of_action=cost_of_action,
        feasibility_note=feasibility_note,
    )


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
                _single_injection_candidate(
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
            _single_injection_candidate(
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


def _auto_card_weekday_candidate(ctx: SimContext) -> Candidate | None:
    """카드 출금 요일 변경(수입일 직후 요일) (SPEC 8.6.1 4번째 항목, N13/S57).

    `Overrides.card_withdrawal_weekday` 는 `simulate.py` 에 이미 구현돼
    있다(호출자만 없었다) - 카드가 여러 장이면 전부 같은 목표 요일로 바꾸고,
    카드마다 `AppliedAction`(override) 하나씩으로 나눠 담는다. 후보가 아무
    것도 바꾸지 않으면(모든 카드가 이미 목표 요일) None 을 반환한다.
    """

    state = ctx.state
    income = state.income
    if not state.cards or income.next_date is None:
        return None

    target_weekday = (income.next_date.weekday() + 1) % 7
    changing = [c for c in state.cards if c.withdrawal_weekday != target_weekday]
    if not changing:
        return None

    units = [
        ActionUnit(
            injection=None,
            override_card_id=c.id,
            override_weekday=target_weekday,
            cut_ratio=None,
            label=f"카드 {c.id} 출금 요일을 {_WEEKDAY_NAMES_KO[target_weekday]}요일로 변경",
        )
        for c in changing
    ]
    card_ids = ", ".join(str(c.id) for c in changing)
    weekday_name = _WEEKDAY_NAMES_KO[target_weekday]
    cost_of_action = f"카드({card_ids}) 출금일을 수입일 다음날({weekday_name}요일)로 이동"
    return Candidate(
        key=("CARD_WEEKDAY", target_weekday),
        units=units,
        envelope_id=None,
        cost_of_action=cost_of_action,
        feasibility_note=None,
        override=Overrides(card_withdrawal_weekday={c.id: target_weekday for c in changing}),
    )


def _auto_candidates(ctx: SimContext, constraints: OptimizeConstraints) -> list[Candidate]:
    out = _auto_budget_candidates(ctx.state, constraints) + _auto_subscription_candidates(ctx)
    card_weekday = _auto_card_weekday_candidate(ctx)
    if card_weekday is not None:
        out.append(card_weekday)
    return out


def _emergency_draw_candidate(state: State, baseline_eco: PathStats) -> Candidate | None:
    """비상금 이체 후보 (허용 시, 부족액만큼) (SPEC 8.6.1)."""

    if baseline_eco.min_balance >= 0:
        return None
    deficit = -baseline_eco.min_balance
    amount = min(deficit, state.emergency_fund)
    if amount <= 0:
        return None
    return _single_injection_candidate(
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
            _single_injection_candidate(
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


def _expected_shortfall(sim: SimulationResult) -> float:
    """부족 경로(실제 부족 또는 카드 부족)의 최저 경제 잔액 절대값 평균 (S56
    2차 목적항). `risk.py::run_risk` 의 `expected_shortfall` 계산과 같은
    형태이되, 1차 항이 `max(shortfall_prob, card_shortfall_prob)` 이므로
    마스크도 두 부족을 합쳐 쓴다."""

    mask = sim.any_shortfall | sim.card_shortfall
    if not mask.any():
        return 0.0
    mins = sim.economic[mask].min(axis=1)
    return float(np.abs(mins).mean())


@dataclass
class ObjectiveEval:
    """한 번의 `run_sim()` 결과를 목적함수 관점에서 요약한 값 (S56).

    `rank_key` 는 오름차순 정렬 시 항상 "작을수록 좋다"가 되도록 부호를
    미리 맞춘 사전식 튜플이고, `raw_dims` 는 같은 차원 순서를 **원래 단위**
    (부호 없이)로 담아 `effect.delta`/`delta_dim` 계산에 쓴다.
    """

    rank_key: tuple[float, ...]
    raw_dims: tuple[float, ...]
    shortfall_prob: float
    card_shortfall_prob: float
    end_balance_median: float
    expected_shortfall: float
    min_economic_balance_median: float
    achieve_prob: float | None


def _objective_eval(
    sim: SimulationResult, ctx: SimContext, params: OptimizeParams, injections: Sequence[Injection]
) -> ObjectiveEval:
    stats_real = sim.stats(economic=False)
    stats_eco = sim.stats(economic=True)
    sp = stats_real.shortfall_prob
    csp = stats_real.card_shortfall_prob
    sp_max = max(sp, csp)
    end_bal = float(stats_real.end_balance_median)
    exp_short = _expected_shortfall(sim)
    min_eco = float(stats_eco.min_balance)

    achieve_prob: float | None = None
    raw: tuple[float, ...]
    rank_key: tuple[float, ...]
    if params.objective == "MIN_SHORTFALL_PROB":
        raw = (sp_max, exp_short, min_eco, end_bal)
        rank_key = (sp_max, exp_short, -min_eco, -end_bal)
    elif params.objective == "MAX_END_BALANCE":
        raw = (end_bal, sp_max, exp_short)
        rank_key = (-end_bal, sp_max, exp_short)
    else:
        assert params.goal is not None
        achieve_prob = _achieve_prob(sim, ctx, params.goal, injections)
        raw = (achieve_prob, sp_max, end_bal)
        rank_key = (-achieve_prob, sp_max, -end_bal)

    return ObjectiveEval(
        rank_key=rank_key,
        raw_dims=raw,
        shortfall_prob=sp,
        card_shortfall_prob=csp,
        end_balance_median=end_bal,
        expected_shortfall=exp_short,
        min_economic_balance_median=min_eco,
        achieve_prob=achieve_prob,
    )


def _key_less(a: tuple[float, ...], b: tuple[float, ...], eps: float = _DIM_EPS) -> bool:
    """`a` 가 `b` 보다 사전식으로 더 좋은가(오름차순, 허용 오차 포함)."""

    for x, y in zip(a, b, strict=True):
        if x < y - eps:
            return True
        if x > y + eps:
            return False
    return False


def _delta_from_baseline(
    objective: str, raw_dims: tuple[float, ...], baseline_raw_dims: tuple[float, ...]
) -> tuple[str, float]:
    """순위를 실제로 가른(기준선과 유의미하게 다른) 첫 차원의 이름과
    (후보 - 기준) 값 (S56 "1차 항이 0 이면 2차 항의 델타를 담는다")."""

    names = _DIM_NAMES[objective]
    for name, cand_v, base_v in zip(names, raw_dims, baseline_raw_dims, strict=True):
        if abs(cand_v - base_v) > _DIM_EPS:
            return name, cand_v - base_v
    return names[-1], raw_dims[-1] - baseline_raw_dims[-1]


@dataclass
class _Entry:
    """평가를 마친 후보(단일 또는 조합) 1건. 순위 정렬·직렬화의 재료."""

    candidates: list[Candidate]
    objective_eval: ObjectiveEval
    effect: dict[str, float | int | str]
    feasibility_note: str | None


def _make_entry(
    candidates: list[Candidate],
    obj_eval: ObjectiveEval,
    objective: str,
    baseline_eval: ObjectiveEval,
) -> _Entry:
    delta_dim, delta = _delta_from_baseline(objective, obj_eval.raw_dims, baseline_eval.raw_dims)
    cost = "; ".join(c.cost_of_action for c in candidates)
    notes = [c.feasibility_note for c in candidates if c.feasibility_note]
    feasibility_note = "; ".join(notes) if notes else None

    effect: dict[str, float | int | str] = {
        "shortfall_prob": obj_eval.shortfall_prob,
        "card_shortfall_prob": obj_eval.card_shortfall_prob,
        "end_balance_median": obj_eval.end_balance_median,
        "expected_shortfall": obj_eval.expected_shortfall,
        "min_economic_balance_median": obj_eval.min_economic_balance_median,
        "delta": float(delta),
        "delta_dim": delta_dim,
        "cost_of_action": cost,
    }
    if obj_eval.achieve_prob is not None:
        effect["achieve_prob"] = obj_eval.achieve_prob

    return _Entry(
        candidates=candidates,
        objective_eval=obj_eval,
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
    baseline_eval = _objective_eval(baseline_sim, ctx, params, ())

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
        notes = [
            "적용 가능한 후보가 없다: 조정 가능한 유연(또는 허용된) 봉투 예산이 없고, "
            "활성 구독도 없다(N11)."
        ]
        return OptimizeResult(
            objective=params.objective,
            baseline=baseline_result,
            ranked=[],
            recommended=None,
            evaluated=0,
            sim_calls=sim_calls,
            notes=notes,
            n_paths_used=ctx.n_paths,
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
        sim = run_sim(ctx, injections=cand.injections, overrides=cand.override)
        sim_calls += 1
        obj_eval = _objective_eval(sim, ctx, params, cand.injections)
        single_entries.append(_make_entry([cand], obj_eval, params.objective, baseline_eval))

    single_entries.sort(key=lambda e: e.objective_eval.rank_key)
    top_k_entries = single_entries[: min(_TOP_K, len(single_entries))]

    all_entries: list[_Entry] = list(single_entries)

    if params.max_actions >= 2 and top_k_entries:
        best = top_k_entries[0]
        combo_candidates = list(best.candidates)
        combo_eval = best.objective_eval
        used_keys = {c.key for c in combo_candidates}
        used_env_ids = {c.envelope_id for c in combo_candidates if c.envelope_id is not None}

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
            base_candidates = list(combo_candidates)
            best_choice: Candidate | None = None
            best_eval: ObjectiveEval | None = None
            for cand_entry in pool:
                cand = cand_entry.candidates[0]
                trial_candidates = [*base_candidates, cand]
                trial_injections = [i for c in trial_candidates for i in c.injections]
                trial_overrides = next(
                    (c.override for c in trial_candidates if c.override is not None), None
                )
                sim = run_sim(ctx, injections=trial_injections, overrides=trial_overrides)
                sim_calls += 1
                obj_eval = _objective_eval(sim, ctx, params, trial_injections)
                if best_eval is None or _key_less(obj_eval.rank_key, best_eval.rank_key):
                    best_choice = cand
                    best_eval = obj_eval

            if (
                best_choice is None
                or best_eval is None
                or not _key_less(best_eval.rank_key, combo_eval.rank_key)
            ):
                break

            combo_candidates = [*combo_candidates, best_choice]
            used_keys.add(best_choice.key)
            if best_choice.envelope_id is not None:
                used_env_ids.add(best_choice.envelope_id)
            combo_eval = best_eval

        if len(combo_candidates) >= 2:
            all_entries.append(
                _make_entry(combo_candidates, combo_eval, params.objective, baseline_eval)
            )

    all_entries.sort(key=lambda e: e.objective_eval.rank_key)

    ranked: list[RankedAction] = []
    for i, entry in enumerate(all_entries, start=1):
        ranked.append(
            RankedAction(
                rank=i,
                actions=[unit.to_applied_action() for c in entry.candidates for unit in c.units],
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
        notes=[],
        n_paths_used=ctx.n_paths,
    )
