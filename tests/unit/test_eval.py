"""평가 도구 단위 테스트 (SPEC §12, PLAN §4 W14).

작은 규모(1 프로필, 2 시드, `months=3`~`4`, `n_paths=200`)로 각 함수가
리포트 구조를 만드는지, 지표 범위가 타당한지(0<=ECE/Brier/coverage<=1
등), sMAPE·캘리브레이션 구간 집계가 손계산과 일치하는지 확인한다. 실제
전체 규모 실행(`fdt eval all`)은 `docs/EVAL_REPORT.md` 생성으로 별도
검증한다(이 파일은 단위 테스트만).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fdt.eval import smape
from fdt.eval.backtest import run_backtest
from fdt.eval.calibration import _channel_calibration, run_calibration
from fdt.eval.monotonic import run_monotonic
from fdt.eval.perf import run_perf
from fdt.eval.report import render_markdown, write_json_reports

# ---------------------------------------------------------------------------
# sMAPE (SPEC §12 정의)
# ---------------------------------------------------------------------------


def test_smape_manual_example() -> None:
    # |110-100| / ((110+100)/2 + 100000) = 10 / 100105
    assert smape(110, 100) == pytest.approx(10 / 100105)
    assert smape(0, 0) == 0.0
    # 부호에 무관(절대값), 대칭
    assert smape(100, 110) == pytest.approx(smape(110, 100))


# ---------------------------------------------------------------------------
# backtest
# ---------------------------------------------------------------------------


def test_run_backtest_structure() -> None:
    report = run_backtest(["A_steady"], [1, 3], months=3, horizon=10, n_paths=200)

    assert report.months == 3
    assert report.horizon == 10
    assert len(report.profiles) == 1
    pb = report.profiles[0]
    assert pb.profile == "A_steady"
    assert len(pb.per_seed) == 2
    for m in pb.per_seed:
        assert 0.0 <= m.smape
        assert 0.0 <= m.coverage <= 1.0
        assert m.mae >= 0.0
    assert 0.0 <= pb.mean_smape
    assert 0.0 <= pb.mean_coverage <= 1.0
    assert pb.threshold_smape == pytest.approx(0.15)  # A 프로필 SPEC §12 기준
    assert pb.coverage_range == (0.6, 0.95)


# ---------------------------------------------------------------------------
# calibration
# ---------------------------------------------------------------------------


def test_channel_calibration_manual_example() -> None:
    """5구간 ECE/Brier 를 손으로 계산한 값과 대조한다.

    표본 4개, 전부 [0.0, 0.2) 구간: p=[0.05, 0.1, 0.15, 0.1], y=[0,1,0,1].
    관측 빈도 = 2/4 = 0.5, 평균 예측 = (0.05+0.1+0.15+0.1)/4 = 0.1.
    그 구간만 표본이 있으므로 ECE = |0.1-0.5| = 0.4.
    Brier = mean((p-y)^2) = (0.05^2+0.9^2+0.15^2+0.9^2)/4.
    기준율 = 0.5, 기준율 Brier = 0.5*0.5 = 0.25.
    """

    pairs = [(0.05, False), (0.1, True), (0.15, False), (0.1, True)]
    ch = _channel_calibration("test", pairs)

    assert ch.n == 4
    assert ch.base_rate == pytest.approx(0.5)
    assert ch.ece == pytest.approx(0.4, abs=1e-9)
    expected_brier = (0.05**2 + 0.9**2 + 0.15**2 + 0.9**2) / 4
    assert ch.brier == pytest.approx(expected_brier)
    assert ch.brier_baseline == pytest.approx(0.25)
    assert ch.passed_ece is False  # 0.4 > 0.15
    # 표본이 채워진 구간 하나뿐이고 count=4 < 15 -> 보류 표시
    filled = [b for b in ch.bins if b.count > 0]
    assert len(filled) == 1
    assert filled[0].count == 4
    assert filled[0].reliable is False
    empty = [b for b in ch.bins if b.count == 0]
    assert len(empty) == 4
    for b in empty:
        assert b.mean_pred is None
        assert b.observed_freq is None


def test_channel_calibration_empty() -> None:
    ch = _channel_calibration("empty", [])
    assert ch.n == 0
    assert ch.ece == 0.0
    assert ch.brier == 0.0
    assert all(b.count == 0 for b in ch.bins)


def test_run_calibration_structure() -> None:
    # months=3 인 프로필은 데이터시작+90일 창이 end-horizon 보다 늦어 as_of
    # 표본이 0개가 되므로(§11 6개월 생성 기준과 다름), 이 테스트만 데이터가
    # 조금 더 긴 months=4 + 짧은 horizon 을 써서 창을 확보한다.
    report = run_calibration(
        ["A_steady"], [1, 2], months=4, horizon=5, step_days=3, n_paths=200
    )

    assert report.horizon == 5
    assert report.step_days == 3
    assert len(report.samples) > 0

    for ch in (report.card_channel, report.new_channel):
        assert ch.n == len(report.samples)
        assert 0.0 <= ch.ece <= 1.0
        assert 0.0 <= ch.brier <= 1.0
        assert 0.0 <= ch.brier_baseline <= 1.0
        assert 0.0 <= ch.base_rate <= 1.0
        total_binned = sum(b.count for b in ch.bins)
        assert total_binned == ch.n
        for b in ch.bins:
            if b.count > 0:
                assert 0.0 <= b.mean_pred <= 1.0  # type: ignore[operator]
                assert 0.0 <= b.observed_freq <= 1.0  # type: ignore[operator]
                assert b.reliable == (b.count >= 15)


# ---------------------------------------------------------------------------
# monotonic
# ---------------------------------------------------------------------------


def test_run_monotonic_structure() -> None:
    report = run_monotonic(
        ["A_steady"],
        months=3,
        horizon=10,
        amounts=(50_000, 200_000),
        days_from_now=(0, 5),
        n_paths=200,
    )

    # 1 프로필 x 1 as_of x 2 방식 x 2 시점 x (2개 금액 -> 인접쌍 1개) x 검사 2종
    assert report.total_checks == 1 * 2 * 2 * 1 * 2
    assert 0 <= report.violation_count <= report.total_checks
    assert 0.0 <= report.violation_rate <= 1.0
    for v in report.violations:
        assert v.check in ("min_balance", "shortfall_prob")
        assert v.profile == "A_steady"


# ---------------------------------------------------------------------------
# perf
# ---------------------------------------------------------------------------


def test_run_perf_structure() -> None:
    report = run_perf(
        profile="A_steady", seed=1, months=3, n_paths=200, repro_profiles=["A_steady"]
    )

    names = {t.name for t in report.timings}
    assert names == {"build_engine", "simulate_forecast", "whatif", "goal", "optimize"}
    for t in report.timings:
        assert t.elapsed_ms >= 0.0
        assert t.threshold_ms > 0.0

    assert len(report.repro_checks) == 5  # 1 프로필 x 5 모드
    modes = {c.mode for c in report.repro_checks}
    assert modes == {"forecast", "whatif", "goal", "risk", "optimize"}
    for c in report.repro_checks:
        assert c.identical is True  # 같은 입력·시드는 바이트 동일해야 한다


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def test_write_json_reports_and_markdown(tmp_path: Path) -> None:
    backtest = run_backtest(["A_steady"], [1], months=3, horizon=10, n_paths=200)
    written = write_json_reports(tmp_path, backtest=backtest)
    assert len(written) == 1
    assert written[0].exists()

    md = render_markdown(backtest=backtest)
    assert "# 평가 리포트" in md
    assert "A_steady" in md
