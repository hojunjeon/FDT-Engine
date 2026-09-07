"""FORECAST 모드 러너 (SPEC 8.2).

`simulate()` 한 번만 호출하고(SPEC 4.2-5), 그 결과에서 궤적·봉투·이벤트를
그대로 뽑아낸다 - 전이 규칙 재구현은 하지 않는다(작업 지시 금지 사항).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from fdt.engine.modes import register
from fdt.engine.modes._common import (
    envelope_name,
    events_from,
    make_context,
    point_stats,
    run_sim,
    to_int,
    trajectory_from,
)
from fdt.engine.schemas.request import ForecastParams, ModeRequest
from fdt.engine.schemas.result import EconomicStats, EnvelopeForecast, ForecastResult
from fdt.engine.taxonomy import Mode

__all__ = ["run_forecast"]


@register(Mode.FORECAST)
def run_forecast(engine, req: ModeRequest) -> ForecastResult:
    params = req.params
    # `ModeRequest._parse_params_by_mode` 가 mode 로 params 클래스를 이미
    # 확정해 두므로(SPEC 8.1) 런타임에는 항상 참이다 - mypy 에 유니온을
    # 좁혀 알려주는 assert 다(예외를 던지려는 목적이 아니다).
    assert isinstance(params, ForecastParams)

    ctx = make_context(engine, req)
    sim = run_sim(ctx)

    stats_real = sim.stats(economic=False)
    stats_eco = sim.stats(economic=True)

    trajectory = trajectory_from(stats_real)
    economic = EconomicStats(
        median=[float(v) for v in stats_eco.median],
        p10=[float(v) for v in stats_eco.p10],
        p90=[float(v) for v in stats_eco.p90],
    )
    min_point, end_point = point_stats(stats_real)

    envelopes: list[EnvelopeForecast] = []
    if params.include_envelopes:
        as_of = ctx.state.as_of
        month_end = ctx.state.cycle.budget_cycle_end
        horizon_end_date = as_of + timedelta(days=ctx.horizon_days)
        # 이번 달 말일이 horizon 밖이면(짧은 horizon 요청) 그 안에서 낼 수
        # 있는 마지막 날까지만 투영한다 - simulate() 가 안 만든 날짜를
        # 재계산으로 만들어내지 않는다(작업 지시 금지 사항).
        projection_date = min(month_end, horizon_end_date)
        proj_idx = (projection_date - as_of).days

        for env in sorted(ctx.state.envelopes, key=lambda e: e.envelope_id):
            eid = env.envelope_id
            ei = sim.envelope_ids.index(eid)
            projected_median = float(np.median(sim.envelope_spend[:, ei, proj_idx]))

            # `simulate()` 의 8단계 루프는 k=1 부터만 돌아 as_of 시점(k=0)에
            # 이미 예산을 넘은 경우를 못 잡는다(SPEC 7.1 "실제 8단계는
            # k=1..horizon_days"). 이미 넘어 있으면 그 사실 자체가
            # exhaust_date_median=as_of, overrun_prob=1.0 이다 - simulate 결과를
            # 무시하는 게 아니라 simulate 가 다루지 않는 시점(k=0)을 채우는
            # 것이다.
            exhaust_date_median: date | None
            if env.spent >= env.budget:
                exhaust_date_median = as_of
                overrun_prob = 1.0
            else:
                exhaust_date_median = stats_real.envelope_exhaust_date_median.get(eid)
                overrun_prob = stats_real.envelope_overrun_prob.get(eid, 0.0)

            envelopes.append(
                EnvelopeForecast(
                    envelope_id=eid,
                    name=envelope_name(eid),
                    budget=env.budget,
                    spent_now=env.spent,
                    projected_month_end_median=to_int(projected_median),
                    exhaust_date_median=exhaust_date_median,
                    overrun_prob=overrun_prob,
                )
            )

    events = events_from(sim, as_of=ctx.state.as_of) if params.include_events else []

    return ForecastResult(
        trajectory=trajectory,
        economic=economic,
        min_point=min_point,
        end_point=end_point,
        envelopes=envelopes,
        events=events,
        shortfall_prob=stats_real.shortfall_prob,
        card_shortfall_prob=stats_real.card_shortfall_prob,
    )
