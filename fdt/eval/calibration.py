"""리스크 캘리브레이션 (SPEC §12 "리스크 캘리브레이션").

4 프로필 x 시드 교란(SPEC §11) 사용자마다, 데이터 시작+90일부터
`twin.as_of - horizon` 까지 `step_days` 간격으로 `as_of` 를 이동하며
`RISK` 결과의 두 확률을 실제 30일 내 사건과 대조한다:

- `card_shortfall_prob` vs `ground_truth.card_shortfalls` 가 `(as_of,
  as_of+horizon]` 에 있는지(SPEC 요구사항 2 "기존 정의").
- `shortfall_prob` vs `card_shortfalls` 합집합 `declined_debits` 가 같은 창에
  있는지(요구사항 2 "새 부족 정의" - 리뷰 S45 가 `shortfall_prob` 을 관측
  가능한 실패 사건 기준으로 재정의한 것과 1:1 대응한다).

5 구간(0~.2, .2~.4, .4~.6, .6~.8, .8~1.0) ECE·Brier·기준율 Brier·구간
표본 수를 낸다. 표본 15 미만인 구간은 `reliable=False` 로 표시한다(요구사항
2 "<15 보류 표시") - ECE 계산에서 제외하지는 않는다(가중 평균이 이미 표본
수로 가중되므로 작은 구간의 영향은 원래 작다. 표시만 별도로 한다).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from fdt.engine import ModeRequest, build_engine
from fdt.engine.schemas.request import RiskParams
from fdt.engine.schemas.result import RiskResult
from fdt.engine.taxonomy import Mode
from fdt.eval import gt_date_range, primary_account_ids  # noqa: F401  (재노출 일관성)
from fdt.gen import generate

__all__ = [
    "BINS",
    "ECE_THRESHOLD",
    "BinStat",
    "CalibrationReport",
    "ChannelCalibration",
    "Sample",
    "run_calibration",
]

BINS: list[tuple[float, float]] = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
ECE_THRESHOLD = 0.15
MIN_BIN_SAMPLES = 15


@dataclass(frozen=True, slots=True)
class Sample:
    profile: str
    seed: int
    as_of: date
    p_card: float
    y_card: bool
    p_new: float
    y_new: bool


@dataclass(frozen=True, slots=True)
class BinStat:
    lo: float
    hi: float
    count: int
    mean_pred: float | None
    observed_freq: float | None
    reliable: bool


@dataclass(frozen=True, slots=True)
class ChannelCalibration:
    name: str
    n: int
    base_rate: float
    ece: float
    brier: float
    brier_baseline: float
    bins: list[BinStat]
    passed_ece: bool
    passed_brier: bool


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    step_days: int
    horizon: int
    n_paths: int
    card_channel: ChannelCalibration
    new_channel: ChannelCalibration
    samples: list[Sample] = field(default_factory=list)


def _events_in_window(entries: list[dict], lo: date, hi: date) -> bool:
    """`lo < date(e) <= hi` 인 원소가 하나라도 있는가."""

    for e in entries:
        d = date.fromisoformat(e["date"])
        if lo < d <= hi:
            return True
    return False


def _collect_samples(
    profiles: list[str],
    seeds: list[int],
    *,
    months: int,
    horizon: int,
    step_days: int,
    n_paths: int,
) -> list[Sample]:
    samples: list[Sample] = []
    for profile in profiles:
        for seed in seeds:
            twin, _twin_raw, gt = generate(profile, seed=seed, months=months)
            start, _end = gt_date_range(gt)
            window_start = start + timedelta(days=90)
            window_end = twin.as_of - timedelta(days=horizon)
            as_of_list = []
            d = window_start
            while d <= window_end:
                as_of_list.append(d)
                d += timedelta(days=step_days)

            for as_of in as_of_list:
                engine = build_engine(twin, as_of=as_of)
                req = ModeRequest(
                    mode=Mode.RISK,
                    horizon_days=horizon,
                    n_paths=n_paths,
                    seed=42,
                    params=RiskParams(),
                )
                result = engine.run(req)
                assert result.status == "OK", f"RISK 실패: {result.error}"
                assert isinstance(result.result, RiskResult)
                risk = result.result

                window_hi = as_of + timedelta(days=horizon)
                y_card = _events_in_window(gt["card_shortfalls"], as_of, window_hi)
                y_new = y_card or _events_in_window(gt["declined_debits"], as_of, window_hi)

                samples.append(
                    Sample(
                        profile=profile,
                        seed=seed,
                        as_of=as_of,
                        p_card=risk.card_shortfall_prob,
                        y_card=y_card,
                        p_new=risk.shortfall_prob,
                        y_new=y_new,
                    )
                )
    return samples


def _channel_calibration(name: str, pairs: list[tuple[float, bool]]) -> ChannelCalibration:
    n = len(pairs)
    base_rate = sum(1 for _p, y in pairs if y) / n if n else 0.0
    brier = sum((p - float(y)) ** 2 for p, y in pairs) / n if n else 0.0
    brier_baseline = base_rate * (1 - base_rate)

    bins: list[BinStat] = []
    ece_sum = 0.0
    for lo, hi in BINS:
        in_bin = [
            (p, y)
            for p, y in pairs
            if (lo <= p < hi) or (hi == 1.0 and p == 1.0)
        ]
        count = len(in_bin)
        if count == 0:
            bins.append(
                BinStat(lo=lo, hi=hi, count=0, mean_pred=None, observed_freq=None, reliable=False)
            )
            continue
        mean_pred = sum(p for p, _y in in_bin) / count
        observed = sum(1 for _p, y in in_bin if y) / count
        ece_sum += count * abs(mean_pred - observed)
        bins.append(
            BinStat(
                lo=lo,
                hi=hi,
                count=count,
                mean_pred=mean_pred,
                observed_freq=observed,
                reliable=count >= MIN_BIN_SAMPLES,
            )
        )
    ece = ece_sum / n if n else 0.0

    return ChannelCalibration(
        name=name,
        n=n,
        base_rate=base_rate,
        ece=ece,
        brier=brier,
        brier_baseline=brier_baseline,
        bins=bins,
        passed_ece=ece <= ECE_THRESHOLD,
        passed_brier=brier < brier_baseline,
    )


def run_calibration(
    profiles: list[str],
    seeds: list[int],
    *,
    months: int = 6,
    horizon: int = 30,
    step_days: int = 7,
    n_paths: int = 1000,
) -> CalibrationReport:
    samples = _collect_samples(
        profiles, seeds, months=months, horizon=horizon, step_days=step_days, n_paths=n_paths
    )
    card_channel = _channel_calibration(
        "card_shortfall_prob", [(s.p_card, s.y_card) for s in samples]
    )
    new_channel = _channel_calibration(
        "shortfall_prob(new)", [(s.p_new, s.y_new) for s in samples]
    )
    return CalibrationReport(
        step_days=step_days,
        horizon=horizon,
        n_paths=n_paths,
        card_channel=card_channel,
        new_channel=new_channel,
        samples=samples,
    )
