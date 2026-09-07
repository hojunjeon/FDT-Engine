"""WHATIF 단조성 회귀 (SPEC §12 "단조성": 지출 주입 증가 -> 부족 확률
비감소, 최저 잔액 비증가).

4 프로필 x `as_of` 표본 x 현금/카드 x 금액 3종 x 시점(`days_from_now`)
[0,3,10,25] 를 `WhatIfParams(injections=[SpendInjection(...)])` 로 돌려,
같은 (프로필, as_of, method, days_from_now) 안에서 금액을 올렸을 때
`branch.min_point.median_balance` 가 증가하거나 `branch.shortfall_prob` 이
감소하면 위반으로 센다. `Engine.run(mode=WHATIF)` 하나만 호출한다 - 전이
규칙을 재구현하지 않는다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import pairwise
from typing import Literal

from fdt.engine import ModeRequest, build_engine
from fdt.engine.schemas.request import SpendInjection, WhatIfParams
from fdt.engine.schemas.result import WhatIfResult
from fdt.engine.taxonomy import OTHER_ENVELOPE_ID, Mode
from fdt.eval import gt_date_range
from fdt.gen import generate

__all__ = [
    "DEFAULT_AMOUNTS",
    "DEFAULT_DAYS_FROM_NOW",
    "AmountPoint",
    "MonotonicReport",
    "MonotonicViolation",
    "run_monotonic",
]

DEFAULT_AMOUNTS: tuple[int, ...] = (50_000, 200_000, 500_000)
DEFAULT_DAYS_FROM_NOW: tuple[int, ...] = (0, 3, 10, 25)


@dataclass(frozen=True, slots=True)
class AmountPoint:
    amount: int
    min_balance: int
    shortfall_prob: float


@dataclass(frozen=True, slots=True)
class MonotonicViolation:
    profile: str
    as_of: date
    method: str
    days_from_now: int
    check: str  # "min_balance" | "shortfall_prob"
    amount_from: int
    amount_to: int
    value_from: float
    value_to: float


@dataclass(frozen=True, slots=True)
class MonotonicReport:
    total_checks: int
    violations: list[MonotonicViolation] = field(default_factory=list)

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def violation_rate(self) -> float:
        return self.violation_count / self.total_checks if self.total_checks else 0.0


def _as_of_samples(gt: dict, twin_as_of: date, horizon: int, n: int) -> list[date]:
    """데이터 범위 안에서 `n` 개 `as_of` 표본을 고르게 뽑는다.

    항상 홀드아웃 표준 지점(`twin_as_of - horizon`)을 포함한다(백테스트와
    같은 시점이라 비교하기 쉽다). `n<=1` 이면 그 지점 하나만 쓴다.
    """

    start, _end = gt_date_range(gt)
    hold = twin_as_of - timedelta(days=horizon)
    if n <= 1:
        return [hold]
    span = (hold - start).days
    step = max(1, span // (n - 1))
    return sorted({start + timedelta(days=i * step) for i in range(n)} | {hold})


def _amount_point(
    engine,
    *,
    envelope_id: int,
    method: Literal["CASH", "CARD"],
    days_from_now: int,
    amount: int,
    n_paths: int,
) -> AmountPoint:
    req = ModeRequest(
        mode=Mode.WHATIF,
        n_paths=n_paths,
        seed=42,
        params=WhatIfParams(
            injections=[
                SpendInjection(
                    days_from_now=days_from_now,
                    amount=amount,
                    envelope_id=envelope_id,
                    method=method,
                )
            ]
        ),
    )
    result = engine.run(req)
    assert result.status == "OK", f"WHATIF 실패: {result.error}"
    assert isinstance(result.result, WhatIfResult)
    branch = result.result.branch
    return AmountPoint(
        amount=amount,
        min_balance=branch.min_point.median_balance,
        shortfall_prob=branch.shortfall_prob,
    )


def run_monotonic(
    profiles: list[str],
    *,
    seed: int = 1,
    months: int = 6,
    horizon: int = 30,
    as_of_samples: int = 1,
    amounts: tuple[int, ...] = DEFAULT_AMOUNTS,
    days_from_now: tuple[int, ...] = DEFAULT_DAYS_FROM_NOW,
    n_paths: int = 1000,
    envelope_id: int = OTHER_ENVELOPE_ID,
) -> MonotonicReport:
    sorted_amounts = sorted(amounts)
    violations: list[MonotonicViolation] = []
    total_checks = 0

    for profile in profiles:
        twin, _twin_raw, gt = generate(profile, seed=seed, months=months)
        for as_of in _as_of_samples(gt, twin.as_of, horizon, as_of_samples):
            engine = build_engine(twin, as_of=as_of)
            methods: tuple[Literal["CASH", "CARD"], Literal["CASH", "CARD"]] = ("CASH", "CARD")
            for method in methods:
                for dfn in days_from_now:
                    points = [
                        _amount_point(
                            engine,
                            envelope_id=envelope_id,
                            method=method,
                            days_from_now=dfn,
                            amount=amt,
                            n_paths=n_paths,
                        )
                        for amt in sorted_amounts
                    ]
                    for prev, nxt in pairwise(points):
                        total_checks += 2
                        if nxt.min_balance > prev.min_balance:
                            violations.append(
                                MonotonicViolation(
                                    profile=profile,
                                    as_of=as_of,
                                    method=method,
                                    days_from_now=dfn,
                                    check="min_balance",
                                    amount_from=prev.amount,
                                    amount_to=nxt.amount,
                                    value_from=prev.min_balance,
                                    value_to=nxt.min_balance,
                                )
                            )
                        if nxt.shortfall_prob < prev.shortfall_prob:
                            violations.append(
                                MonotonicViolation(
                                    profile=profile,
                                    as_of=as_of,
                                    method=method,
                                    days_from_now=dfn,
                                    check="shortfall_prob",
                                    amount_from=prev.amount,
                                    amount_to=nxt.amount,
                                    value_from=prev.shortfall_prob,
                                    value_to=nxt.shortfall_prob,
                                )
                            )

    return MonotonicReport(total_checks=total_checks, violations=violations)
