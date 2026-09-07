"""모드 러너 공용 헬퍼 (SPEC 7~8장).

다섯 모드 러너(FORECAST/WHATIF/GOAL/RISK/OPTIMIZE)가 전부 재사용하는 조각만
여기 둔다: `simulate()` 호출 준비(`SimContext`/`make_context`), 실제 호출
(`run_sim`), `PathStats` -> 출력 스키마 변환(`trajectory_from`/`point_stats`/
`events_from`), 반올림(`to_int`). 모드별 고유 계산(FORECAST 의 envelopes,
RISK 의 alerts/health 등)은 각 모드 파일이 직접 한다 - 여기서는 하지 않는다
(작업 지시 "facts/viz 에서 재계산 금지" 와 같은 원칙: 공용 헬퍼도 각 모드의
결정을 대신 내리지 않는다).

공개 이름 (W8 WHATIF, W9 GOAL, W10 OPTIMIZE 가 그대로 import 하는 계약):
`SimContext`, `make_context`, `run_sim`, `to_int`, `trajectory_from`,
`point_stats`, `events_from`, `envelope_name`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from fdt.engine.schemas.behavior import Behavior
from fdt.engine.schemas.input import Externals
from fdt.engine.schemas.request import Injection, ModeRequest
from fdt.engine.schemas.result import EventForecast, PointStat, Trajectory
from fdt.engine.schemas.simulate import PathStats
from fdt.engine.schemas.state import Committed, State
from fdt.engine.simulate import Overrides, SimulationResult, simulate
from fdt.engine.state import build_committed_queue
from fdt.engine.taxonomy import ENVELOPE_IDS

__all__ = [
    "SimContext",
    "envelope_name",
    "events_from",
    "make_context",
    "point_stats",
    "run_sim",
    "to_int",
    "trajectory_from",
]

_ENVELOPE_NAME_BY_ID: dict[int, str] = {idx: name for name, idx in ENVELOPE_IDS.items()}

# `state.committed` 는 as_of+90 까지만 채워져 있다(SPEC 5.4/7.1, S42). 그보다
# 긴 horizon 을 요청하면 `build_committed_queue` 를 이 여유(+7일)를 두고
# 다시 만든다 - `simulate()` 자신은 큐를 재생성하지 않는다(SPEC 7.1).
_COMMITTED_HORIZON_CAP = 90
_REBUILD_MARGIN_DAYS = 7


def envelope_name(envelope_id: int) -> str:
    """봉투 id -> 한국어 이름. 알 수 없는 id 는 문자열로 그대로 반환한다."""

    return _ENVELOPE_NAME_BY_ID.get(envelope_id, str(envelope_id))


@dataclass
class SimContext:
    """`simulate()` 호출에 필요한 재료 한 벌 (SPEC 7.1 시그니처와 1:1).

    `committed` 는 `horizon_days > 90` 요청이면 이미 재생성된 큐이고, 그
    이하면 `state.committed` 그대로다(S42) - 모드 러너는 이 필드를 신경쓸
    필요 없이 그대로 `run_sim` 에 넘기면 된다.
    """

    state: State
    behavior: Behavior
    externals: Externals
    committed: list[Committed]
    horizon_days: int
    n_paths: int
    seed: int


def make_context(engine, req: ModeRequest, *, horizon_days: int | None = None) -> SimContext:
    """`Engine` + `ModeRequest` -> `SimContext` (SPEC 7.1, S42).

    `horizon_days` 인자로 `req.horizon_days` 를 덮어쓸 수 있다(예: GOAL 이
    `target_date` 기준의 별도 horizon 으로 재시뮬할 때). 생략하면
    `req.horizon_days` 를 쓴다.
    """

    horizon = horizon_days if horizon_days is not None else req.horizon_days
    state = engine.state

    if horizon > _COMMITTED_HORIZON_CAP:
        committed = build_committed_queue(
            engine.twin,
            engine.ledger,
            state.as_of,
            state.cards,
            horizon_cap=horizon + _REBUILD_MARGIN_DAYS,
        )
    else:
        committed = list(state.committed)

    return SimContext(
        state=state,
        behavior=engine.behavior,
        externals=engine.externals,
        committed=committed,
        horizon_days=horizon,
        n_paths=req.n_paths,
        seed=req.seed,
    )


def run_sim(
    ctx: SimContext,
    *,
    injections: Sequence[Injection] = (),
    overrides: Overrides | None = None,
) -> SimulationResult:
    """`SimContext` 로 `simulate()` 를 호출한다(같은 seed = CRN, SPEC 8.3).

    `ctx.committed` 를 그대로 넘겨(재생성하지 않는다, SPEC 7.1) 매 호출이
    같은 큐를 공유하게 한다 - 기준/분기가 서로 다른 큐를 보면 CRN 비교가
    깨진다.
    """

    return simulate(
        ctx.state,
        ctx.behavior,
        ctx.externals,
        horizon_days=ctx.horizon_days,
        n_paths=ctx.n_paths,
        seed=ctx.seed,
        injections=injections,
        overrides=overrides,
        committed=ctx.committed,
    )


def to_int(x: float | int) -> int:
    """반올림 정수 원(SPEC 8.2/8.5 "정수 원(반올림)")."""

    return round(x)


def trajectory_from(stats: PathStats) -> Trajectory:
    """`PathStats` -> `Trajectory`(SPEC 8.2 `trajectory`, mean 필수).

    `PathStats.median/p10/p90` 은 이미 정수로 반올림돼 있지만(SPEC 8.2
    "trajectory 배열만 float"), pydantic 이 int -> float 변환을 해 주므로
    그대로 넘겨도 스키마와 맞는다.
    """

    return Trajectory(
        dates=stats.dates,
        median=[float(v) for v in stats.median],
        p10=[float(v) for v in stats.p10],
        p90=[float(v) for v in stats.p90],
        mean=list(stats.mean),
    )


def point_stats(stats: PathStats) -> tuple[PointStat, PointStat]:
    """`PathStats` -> `(min_point, end_point)`(SPEC 8.2, 정수 원 반올림).

    `min_point.p10_balance` 는 최저점 인덱스의 P10 값을 담는다(SPEC 8.2
    예시 `min_point` 에 `p10_balance` 가 있다).
    """

    min_idx = stats.median.index(stats.min_balance) if stats.min_balance in stats.median else 0
    # `min_balance`(SimulationResult.stats 계산) 는 median 배열에서 argmin 한
    # 값 그대로이므로 위 index() 는 항상 성공한다. 방어적으로만 fallback.
    min_point = PointStat(
        date=stats.min_balance_date,
        median_balance=to_int(stats.min_balance),
        p10_balance=to_int(stats.p10[min_idx]),
    )
    end_point = PointStat(
        date=stats.dates[-1],
        median_balance=to_int(stats.end_balance_median),
    )
    return min_point, end_point


def events_from(sim: SimulationResult, *, as_of: date | None = None) -> list[EventForecast]:
    """`SimulationResult.event_log` -> `EventForecast` 목록(SPEC 8.2 `events`).

    `fail_prob = 1 - success_ratio`. `as_of` 당일(`event_log[0]`이 없는 이유는
    시뮬레이터가 k=1부터만 이벤트를 기록해서다, SPEC 7.1 "실제 8단계는
    k=1..horizon_days 에 대해서만 돈다") 이전 이벤트는 없다.
    """

    out: list[EventForecast] = []
    for day_events in sim.event_log:
        if as_of is not None and day_events.date <= as_of:
            continue
        for ev in day_events.events:
            out.append(
                EventForecast(
                    date=day_events.date,
                    kind=ev.kind,
                    name=ev.name,
                    amount=ev.amount,
                    fail_prob=round(1.0 - ev.success_ratio, 4),
                )
            )
    return out
