"""평가 결과 -> `data/eval/*.json` + `docs/EVAL_REPORT.md` (SPEC §12, PLAN Phase 7).

각 리포트 함수는 이미 만들어진 dataclass 결과를 JSON/마크다운으로 옮기기만
한다 - 지표를 다시 계산하지 않는다.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from fdt.eval.backtest import BacktestReport
from fdt.eval.calibration import CalibrationReport
from fdt.eval.monotonic import MonotonicReport
from fdt.eval.perf import PerfReport

__all__ = [
    "render_markdown",
    "write_json_reports",
    "write_markdown_report",
]


def _to_jsonable(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {k: _to_jsonable(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def write_json_reports(
    out_dir: Path,
    *,
    backtest: BacktestReport | None = None,
    calibration: CalibrationReport | None = None,
    monotonic: MonotonicReport | None = None,
    perf: PerfReport | None = None,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    named = [
        ("backtest.json", backtest),
        ("calibration.json", calibration),
        ("monotonic.json", monotonic),
        ("perf.json", perf),
    ]
    for name, report in named:
        if report is None:
            continue
        path = out_dir / name
        path.write_text(
            json.dumps(_to_jsonable(report), ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        written.append(path)
    return written


def _pass_str(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def render_markdown(
    *,
    backtest: BacktestReport | None = None,
    calibration: CalibrationReport | None = None,
    monotonic: MonotonicReport | None = None,
    perf: PerfReport | None = None,
    note: str = "",
) -> str:
    lines: list[str] = ["# 평가 리포트 (SPEC §12)", ""]
    if note:
        lines += [note, ""]

    # -- 백테스트 -----------------------------------------------------------
    if backtest is not None:
        lines += [
            "## 백테스트 (sMAPE / 커버리지 / 최저점 오차)",
            "",
            f"프로필·시드마다 `months={backtest.months}`, `horizon={backtest.horizon}`, "
            f"`n_paths={backtest.n_paths}`, 시뮬 시드 `{backtest.sim_seed}`.",
            "",
            "| 프로필 | 기준 sMAPE | 평균 sMAPE | 최대 sMAPE | 시드 통과 | 판정 | "
            "커버리지 범위 | 평균 커버리지 | 시드 통과 | 판정 | "
            "최저점 오차 기준 | 시드 통과 | 판정 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- "
            "| --- | --- | --- |",
        ]
        for pb in backtest.profiles:
            n = len(pb.per_seed)
            lines.append(
                f"| {pb.profile} | {pb.threshold_smape:.2f} | {pb.mean_smape:.4f} | "
                f"{pb.max_smape:.4f} | {pb.smape_pass_count}/{n} | {_pass_str(pb.passed_smape)} | "
                f"{pb.coverage_range[0]}~{pb.coverage_range[1]} | {pb.mean_coverage:.3f} | "
                f"{pb.coverage_pass_count}/{n} | {_pass_str(pb.passed_coverage)} | "
                f"{pb.min_point_error_threshold:,}원 | {pb.min_amount_pass_count}/{n} | "
                f"{_pass_str(pb.passed_min_point)} |"
            )
        lines.append("")
        lines.append("시드별 상세:")
        lines.append("")
        lines.append(
            "| 프로필 | 시드 | sMAPE | MAE | 커버리지 | 최저점 예측(일자) | "
            "최저점 정답(일자) | 금액오차 | 일자오차 |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for pb in backtest.profiles:
            for m in pb.per_seed:
                lines.append(
                    f"| {m.profile} | {m.seed} | {m.smape:.4f} | {m.mae:,.0f} | {m.coverage:.3f} | "
                    f"{m.pred_min_amount:,} ({m.pred_min_date}) | "
                    f"{m.gt_min_amount:,} ({m.gt_min_date}) | {m.min_amount_error:+,} | "
                    f"{m.min_date_error_days:+d}일 |"
                )
        lines.append("")

    # -- 캘리브레이션 --------------------------------------------------------
    if calibration is not None:
        lines += [
            "## 리스크 캘리브레이션 (ECE / Brier)",
            "",
            f"표본 {len(calibration.samples)}건 (`horizon={calibration.horizon}`, "
            f"`step_days={calibration.step_days}`, `n_paths={calibration.n_paths}`).",
            "",
            "| 채널 | n | 기준율 | ECE | 기준 | 판정 | Brier | 기준율 Brier | 판정 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for ch in (calibration.card_channel, calibration.new_channel):
            lines.append(
                f"| {ch.name} | {ch.n} | {ch.base_rate:.3f} | {ch.ece:.4f} | ≤ 0.15 | "
                f"{_pass_str(ch.passed_ece)} | {ch.brier:.4f} | {ch.brier_baseline:.4f} | "
                f"{_pass_str(ch.passed_brier)} |"
            )
        lines.append("")
        for ch in (calibration.card_channel, calibration.new_channel):
            lines.append(f"`{ch.name}` 구간별:")
            lines.append("")
            lines.append("| 구간 | 표본 수 | 평균 예측 | 관측 빈도 | 신뢰(>=15) |")
            lines.append("| --- | --- | --- | --- | --- |")
            for b in ch.bins:
                mp = f"{b.mean_pred:.3f}" if b.mean_pred is not None else "-"
                of = f"{b.observed_freq:.3f}" if b.observed_freq is not None else "-"
                reliable = "예" if b.reliable else "보류"
                lines.append(f"| {b.lo:.1f}~{b.hi:.1f} | {b.count} | {mp} | {of} | {reliable} |")
            lines.append("")

    # -- 단조성 --------------------------------------------------------------
    if monotonic is not None:
        lines += [
            "## 단조성",
            "",
            f"총 검사 {monotonic.total_checks}건 중 위반 {monotonic.violation_count}건 "
            f"({monotonic.violation_rate:.2%}).",
            "",
        ]
        if monotonic.violations:
            lines.append("| 프로필 | as_of | 방식 | days_from_now | 검사 | 금액 | 값 |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for v in monotonic.violations:
                lines.append(
                    f"| {v.profile} | {v.as_of} | {v.method} | {v.days_from_now} | {v.check} | "
                    f"{v.amount_from:,}→{v.amount_to:,} | {v.value_from:,.2f}→{v.value_to:,.2f} |"
                )
            lines.append("")

    # -- 성능·재현성 ----------------------------------------------------------
    if perf is not None:
        lines += [
            "## 성능·재현성",
            "",
            f"측정 프로필 `{perf.profile}` seed={perf.seed} months={perf.months} "
            f"n_paths={perf.n_paths}.",
            "",
            "| 항목 | 기준(ms) | 실측(ms) | 판정 |",
            "| --- | --- | --- | --- |",
        ]
        for t in perf.timings:
            lines.append(
                f"| {t.name} | {t.threshold_ms:,.0f} | {t.elapsed_ms:,.1f} | "
                f"{_pass_str(t.passed)} |"
            )
        lines.append("")
        lines.append("재현성(같은 입력·시드, `elapsed_ms` 제외 바이트 동일):")
        lines.append("")
        lines.append("| 프로필 | 모드 | 동일 |")
        lines.append("| --- | --- | --- |")
        for c in perf.repro_checks:
            lines.append(f"| {c.profile} | {c.mode} | {_pass_str(c.identical)} |")
        lines.append("")

    lines.append("## 미달 항목 원인 메모")
    lines.append("")
    lines.append("(작성자가 채운다 - 자동 생성 리포트는 이 절을 비워 둔다.)")
    lines.append("")
    return "\n".join(lines)


def write_markdown_report(
    out_path: Path,
    *,
    backtest: BacktestReport | None = None,
    calibration: CalibrationReport | None = None,
    monotonic: MonotonicReport | None = None,
    perf: PerfReport | None = None,
    note: str = "",
) -> Path:
    text = render_markdown(
        backtest=backtest, calibration=calibration, monotonic=monotonic, perf=perf, note=note
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path
