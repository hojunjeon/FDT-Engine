"""홀드아웃 백테스트 (SPEC §12 "백테스트 sMAPE"/"P10~P90 커버리지", §11).

측정 방식은 리뷰 `docs/reviews/20260907_W6_W10.md` 항목 2 를 정본으로
따른다: `as_of = twin.as_of - horizon`, `build_engine(twin, as_of=hold)` ->
`Engine.run(ModeRequest(mode=FORECAST, horizon_days=horizon, n_paths=n_paths,
seed=seed))`, 정답은 `ground_truth.daily_balance` 의 PRIMARY 계좌 합, sMAPE 는
SPEC §12 정의(+100,000 가산)로 `k=1..horizon` 만 채점한다(`k=0` 은 이미 확정된
as_of 스냅샷이라 예측이 아니다).

`Engine.run` 하나만 호출한다 - 전이 규칙이나 궤적을 여기서 재계산하지
않는다(작업 지시 "fdt/engine 을 수정하거나 import 이외로 의존하지 않는다").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from fdt.engine import ModeRequest, build_engine
from fdt.engine.schemas.request import ForecastParams
from fdt.engine.schemas.result import ForecastResult
from fdt.engine.taxonomy import Mode
from fdt.eval import gt_primary_balance, primary_account_ids, profile_letter, smape
from fdt.gen import generate

__all__ = [
    "COVERAGE_RANGES",
    "MIN_POINT_ERROR_AMOUNT",
    "SMAPE_THRESHOLDS",
    "BacktestReport",
    "ProfileBacktest",
    "SeedMetric",
    "run_backtest",
]

# SPEC §12 표.
SMAPE_THRESHOLDS: dict[str, float] = {"A": 0.15, "B": 0.25, "C": 0.40, "D": 0.20}
COVERAGE_RANGES: dict[str, tuple[float, float]] = {
    "A": (0.6, 0.95),
    "B": (0.6, 0.95),
    "C": (0.5, 0.95),
    "D": (0.6, 0.95),
}
# SPEC §12 최저점 오차 기준(리뷰 20260907_W6_W10.md §2-2): C 는 50만, 그 외 30만.
MIN_POINT_ERROR_AMOUNT: dict[str, int] = {"A": 300_000, "B": 300_000, "C": 500_000, "D": 300_000}


@dataclass(frozen=True, slots=True)
class SeedMetric:
    profile: str
    seed: int
    smape: float
    mae: float
    coverage: float
    pred_min_amount: int
    pred_min_date: date
    gt_min_amount: int
    gt_min_date: date
    min_amount_error: int
    min_date_error_days: int


@dataclass(frozen=True, slots=True)
class ProfileBacktest:
    profile: str
    threshold_smape: float
    coverage_range: tuple[float, float]
    min_point_error_threshold: int
    per_seed: list[SeedMetric]
    mean_smape: float
    max_smape: float
    smape_pass_count: int
    mean_coverage: float
    coverage_pass_count: int
    min_amount_pass_count: int
    passed_smape: bool
    passed_coverage: bool
    passed_min_point: bool


@dataclass(frozen=True, slots=True)
class BacktestReport:
    months: int
    horizon: int
    n_paths: int
    sim_seed: int
    profiles: list[ProfileBacktest] = field(default_factory=list)


def _one_seed(
    profile: str, seed: int, *, months: int, horizon: int, n_paths: int, sim_seed: int
) -> SeedMetric:
    twin, _twin_raw, gt = generate(profile, seed=seed, months=months)
    hold = twin.as_of - timedelta(days=horizon)
    engine = build_engine(twin, as_of=hold)
    primary_ids = primary_account_ids(engine)

    req = ModeRequest(
        mode=Mode.FORECAST,
        horizon_days=horizon,
        n_paths=n_paths,
        seed=sim_seed,
        params=ForecastParams(include_envelopes=False),
    )
    result = engine.run(req)
    assert result.status == "OK", f"FORECAST 실패: {result.error}"
    assert isinstance(result.result, ForecastResult)
    traj = result.result.trajectory

    errors = []
    smapes = []
    in_band = 0
    gt_by_k: dict[int, int] = {}
    for k in range(1, horizon + 1):
        d = traj.dates[k]
        m = traj.median[k]
        t = gt_primary_balance(gt, primary_ids, d)
        gt_by_k[k] = t
        errors.append(abs(m - t))
        smapes.append(smape(m, t))
        if traj.p10[k] <= t <= traj.p90[k]:
            in_band += 1

    n = horizon
    mean_smape = sum(smapes) / n
    mae = sum(errors) / n
    coverage = in_band / n

    pred_min_k = min(range(1, horizon + 1), key=lambda k: traj.median[k])
    pred_min_amount = round(traj.median[pred_min_k])
    pred_min_date = traj.dates[pred_min_k]

    gt_min_k = min(gt_by_k, key=lambda k: gt_by_k[k])
    gt_min_amount = gt_by_k[gt_min_k]
    gt_min_date = traj.dates[gt_min_k]

    return SeedMetric(
        profile=profile,
        seed=seed,
        smape=mean_smape,
        mae=mae,
        coverage=coverage,
        pred_min_amount=pred_min_amount,
        pred_min_date=pred_min_date,
        gt_min_amount=gt_min_amount,
        gt_min_date=gt_min_date,
        min_amount_error=pred_min_amount - gt_min_amount,
        min_date_error_days=(pred_min_date - gt_min_date).days,
    )


def run_backtest(
    profiles: list[str],
    seeds: list[int],
    *,
    months: int = 6,
    horizon: int = 30,
    n_paths: int = 1000,
    seed: int = 42,
) -> BacktestReport:
    """`profiles` x `seeds` 홀드아웃 백테스트 (SPEC §12).

    `seed` 는 시뮬레이션 CRN 시드(기본 42, 리뷰 정본과 동일)이고, `seeds` 는
    데이터 생성(프로필 시드 교란, SPEC §11) 시드 목록이다 - 서로 다른
    역할이라 이름이 겹치지 않게 함수 인자는 `seed=` 키워드로만 받는다.
    """

    out: list[ProfileBacktest] = []
    for profile in profiles:
        letter = profile_letter(profile)
        per_seed = [
            _one_seed(profile, s, months=months, horizon=horizon, n_paths=n_paths, sim_seed=seed)
            for s in seeds
        ]
        smapes = [m.smape for m in per_seed]
        coverages = [m.coverage for m in per_seed]
        thr_smape = SMAPE_THRESHOLDS[letter]
        lo, hi = COVERAGE_RANGES[letter]
        thr_min_point = MIN_POINT_ERROR_AMOUNT[letter]

        smape_pass_count = sum(1 for v in smapes if v <= thr_smape)
        coverage_pass_count = sum(1 for v in coverages if lo <= v <= hi)
        min_amount_pass_count = sum(
            1 for m in per_seed if abs(m.min_amount_error) <= thr_min_point
        )

        out.append(
            ProfileBacktest(
                profile=profile,
                threshold_smape=thr_smape,
                coverage_range=(lo, hi),
                min_point_error_threshold=thr_min_point,
                per_seed=per_seed,
                mean_smape=sum(smapes) / len(smapes),
                max_smape=max(smapes),
                smape_pass_count=smape_pass_count,
                mean_coverage=sum(coverages) / len(coverages),
                coverage_pass_count=coverage_pass_count,
                min_amount_pass_count=min_amount_pass_count,
                # 전체 판정은 "전 시드 통과" 를 기준으로 삼는다(SPEC §12 는
                # 프로필별 단일 기준치이지 평균 완화가 아니다) - 리포트에
                # 평균/최대/개별 통과 수를 함께 실어 원인 분석을 돕는다.
                passed_smape=all(v <= thr_smape for v in smapes),
                passed_coverage=all(lo <= v <= hi for v in coverages),
                passed_min_point=all(
                    abs(m.min_amount_error) <= thr_min_point for m in per_seed
                ),
            )
        )
    return BacktestReport(
        months=months, horizon=horizon, n_paths=n_paths, sim_seed=seed, profiles=out
    )
