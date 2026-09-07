"""성능·재현성 측정 (SPEC §12 시간·재현성 행).

시간은 SPEC 4.2-2 가 허용하는 `time.perf_counter()` 만 쓴다. 각 모드
호출은 `Engine.run(ModeRequest(...))` 결과의 `meta.elapsed_ms`(엔진이 이미
같은 방식으로 잰 값, SPEC 9.1)를 그대로 쓴다 - 같은 구간을 이중으로 재지
않는다. `build_engine` 만은 `Engine.run` 이 재지 않으므로 여기서
`time.perf_counter()` 로 직접 잰다.

재현성은 "같은 입력·시드 -> 결과 JSON 바이트 동일(`elapsed_ms` 제외)"
(SPEC §12)을 4 프로필 x 5 모드로 확인한다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from fdt.engine import Engine, ModeRequest, TwinInput, build_engine
from fdt.engine.schemas.request import (
    ForecastParams,
    GoalParams,
    OptimizeParams,
    RiskParams,
    SpendInjection,
    WhatIfParams,
)
from fdt.engine.taxonomy import OTHER_ENVELOPE_ID, Mode
from fdt.gen import PROFILE_NAMES, generate

__all__ = [
    "PERF_THRESHOLDS_MS",
    "PerfReport",
    "PerfTiming",
    "ReproCheck",
    "run_perf",
]

# SPEC §12 (초 -> ms).
PERF_THRESHOLDS_MS: dict[str, float] = {
    "build_engine": 1_000,
    "simulate_forecast": 1_500,
    "whatif": 3_000,
    "goal": 4_000,
    "optimize": 25_000,
}


@dataclass(frozen=True, slots=True)
class PerfTiming:
    name: str
    threshold_ms: float
    elapsed_ms: float
    passed: bool


@dataclass(frozen=True, slots=True)
class ReproCheck:
    profile: str
    mode: str
    identical: bool


@dataclass(frozen=True, slots=True)
class PerfReport:
    profile: str
    seed: int
    months: int
    n_paths: int
    timings: list[PerfTiming] = field(default_factory=list)
    repro_checks: list[ReproCheck] = field(default_factory=list)

    @property
    def all_timings_passed(self) -> bool:
        return all(t.passed for t in self.timings)

    @property
    def all_repro_passed(self) -> bool:
        return all(c.identical for c in self.repro_checks)


def _mode_requests(envelope_id: int, n_paths: int = 1000) -> dict[str, ModeRequest]:
    return {
        "forecast": ModeRequest(
            mode=Mode.FORECAST,
            horizon_days=30,
            n_paths=n_paths,
            seed=42,
            params=ForecastParams(),
        ),
        "whatif": ModeRequest(
            mode=Mode.WHATIF,
            n_paths=n_paths,
            seed=42,
            params=WhatIfParams(
                injections=[
                    SpendInjection(
                        days_from_now=5,
                        amount=100_000,
                        envelope_id=envelope_id,
                        method="CASH",
                    )
                ]
            ),
        ),
        "goal": ModeRequest(mode=Mode.GOAL, params=GoalParams(goal_type="ENVELOPE_ADHERE")),
        "risk": ModeRequest(mode=Mode.RISK, params=RiskParams()),
        "optimize": ModeRequest(
            mode=Mode.OPTIMIZE, params=OptimizeParams(objective="MIN_SHORTFALL_PROB")
        ),
    }


def _timing_twin(profile: str, seed: int, months: int) -> TwinInput:
    twin, _twin_raw, _gt = generate(profile, seed=seed, months=months)
    return twin


def _time_build(twin: TwinInput) -> tuple[Engine, float]:
    t0 = time.perf_counter()
    engine = build_engine(twin)
    elapsed = (time.perf_counter() - t0) * 1000
    return engine, elapsed


def _identical_json(a, b) -> bool:
    dump_a = a.model_dump_json(exclude={"meta": {"elapsed_ms"}})
    dump_b = b.model_dump_json(exclude={"meta": {"elapsed_ms"}})
    return dump_a == dump_b


def run_perf(
    *,
    profile: str = "B_card_crunch",
    seed: int = 7,
    months: int = 6,
    n_paths: int = 1000,
    envelope_id: int = OTHER_ENVELOPE_ID,
    repro_profiles: list[str] | None = None,
) -> PerfReport:
    """SPEC §12 시간 5 항목 + 재현성.

    시간 5 항목은 `profile`/`seed`/`months` 데이터 한 벌로 잰다(SPEC 표는
    "6개월, 거래 3천 건" 규모를 가리키므로 기본값은 리뷰가 쓴 B 프로필
    seed=7 이다). 재현성은 `repro_profiles`(기본 SPEC §11 4 프로필) x 5 모드
    전부를 두 번 빌드·실행해 바이트 동일성을 확인한다.
    """

    twin = _timing_twin(profile, seed, months)
    engine, build_ms = _time_build(twin)
    reqs = _mode_requests(envelope_id, n_paths)

    timings = [
        PerfTiming(
            name="build_engine",
            threshold_ms=PERF_THRESHOLDS_MS["build_engine"],
            elapsed_ms=build_ms,
            passed=build_ms < PERF_THRESHOLDS_MS["build_engine"],
        )
    ]

    name_map = {
        "forecast": "simulate_forecast",
        "whatif": "whatif",
        "goal": "goal",
        "optimize": "optimize",
    }
    for key, out_name in name_map.items():
        result = engine.run(reqs[key])
        assert result.status == "OK", f"{key} 실패: {result.error}"
        elapsed = float(result.meta.elapsed_ms)
        threshold = PERF_THRESHOLDS_MS[out_name]
        timings.append(
            PerfTiming(
                name=out_name,
                threshold_ms=threshold,
                elapsed_ms=elapsed,
                passed=elapsed < threshold,
            )
        )

    repro_names = list(repro_profiles) if repro_profiles else list(PROFILE_NAMES)
    repro_checks: list[ReproCheck] = []
    for p in repro_names:
        p_twin = _timing_twin(p, 1, months)
        p_reqs = _mode_requests(envelope_id, n_paths)
        for mode_key, req in p_reqs.items():
            e1 = build_engine(p_twin)
            e2 = build_engine(p_twin)
            r1 = e1.run(req)
            r2 = e2.run(req)
            repro_checks.append(
                ReproCheck(profile=p, mode=mode_key, identical=_identical_json(r1, r2))
            )

    return PerfReport(
        profile=profile,
        seed=seed,
        months=months,
        n_paths=n_paths,
        timings=timings,
        repro_checks=repro_checks,
    )
