"""`fdt render` 의 코어 함수 (SPEC 9.3, 10장, PLAN Phase 6/§6.3).

`render_result(result_json_path, out_dir)` 는 이미 `fdt run` 이 써 둔
`EngineResult` JSON 파일을 읽어, 그 안의 `viz`(SPEC 9.3 8종) 항목마다 PNG
파일 하나씩을 그려 `out_dir` 에 쓴다. 개발·QA 전용 도구다(§6.3 viz 육안
검수 체크리스트) - 에이전트가 실제로 쓰는 산출물이 아니다.

`fdt/tools/` 에 있으므로 파일 I/O 를 한다(SPEC §4.2, 엔진 코어 밖).
matplotlib 은 여기서만 쓰고 `fdt/engine/**` 는 이 모듈을 참조하지 않는다
(viz 명세 자체가 렌더러 독립이어야 한다는 SPEC 0 원칙 4 를 지킨다).
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from fdt.engine.errors import E_REQ_INVALID, FdtError
from fdt.engine.schemas.result import (
    DeltaBarsViz,
    EngineResult,
    EventTimelineViz,
    GaugeViz,
    LineBandViz,
    ProgressBarsViz,
    RankedBarsViz,
    StepBarsViz,
    TableViz,
    Viz,
)

__all__ = ["render_result", "render_viz"]

_KOREAN_FONT_CANDIDATES = ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR")


def _configure_korean_font() -> None:
    """Windows 우선(`Malgun Gothic`), 없으면 다른 한글 폰트, 그것도 없으면
    경고 후 기본 폰트로 그린다(한글이 네모(tofu)로 깨질 수 있다는 경고)."""

    available = {f.name for f in fm.fontManager.ttflist}
    for name in _KOREAN_FONT_CANDIDATES:
        if name in available:
            matplotlib.rcParams["font.family"] = name
            matplotlib.rcParams["axes.unicode_minus"] = False
            return
    warnings.warn(
        "한글 폰트를 찾지 못했다(Malgun Gothic 등) - 렌더된 PNG 에서 한글이 "
        "깨질 수 있다(개발용 도구이므로 경고만 하고 계속 진행한다).",
        stacklevel=2,
    )


def _wrap_caption(fig: plt.Figure, title: str, caption: str) -> None:
    fig.suptitle(title, fontsize=13, fontweight="bold")
    if caption:
        fig.text(0.5, 0.01, caption, ha="center", va="bottom", fontsize=9, color="#444444")


def _annotation_x_as_float(ann_x: Any, x_values: list[Any]) -> float | None:
    """annotation 의 날짜 x 를 line_band 의 x 축(정수 인덱스)에 맞춘다."""

    if ann_x is None:
        return None
    try:
        return float(x_values.index(ann_x))
    except ValueError:
        return None


def _render_line_band(viz: LineBandViz, out_path: Path) -> None:
    data = viz.data
    x_idx = list(range(len(data.x)))
    fig, ax = plt.subplots(figsize=(8, 4.5))

    ax.fill_between(x_idx, data.band.lower, data.band.upper, alpha=0.2, color="#4C72B0")
    for series in data.series:
        ax.plot(x_idx, series.y, marker="o", markersize=2, label=series.name)

    for ann in viz.annotations:
        ax_x = _annotation_x_as_float(ann.x, data.x)
        if ann.type == "hline" and ann.y is not None:
            ax.axhline(ann.y, color="#C44E52", linestyle="--", linewidth=1)
            ax.text(x_idx[-1] if x_idx else 0, ann.y, ann.label, fontsize=8, color="#C44E52")
        elif ann.type in ("point", "vline") and ax_x is not None:
            if ann.type == "vline":
                ax.axvline(ax_x, color="#C44E52", linestyle=":", linewidth=1)
            elif ann.y is not None:
                ax.scatter([ax_x], [ann.y], color="#C44E52", zorder=5)
            ax.annotate(ann.label, (ax_x, ann.y if ann.y is not None else 0), fontsize=8)

    ax.set_xticks(x_idx[:: max(1, len(x_idx) // 8)] if x_idx else [])
    ax.set_xticklabels(
        [data.x[i].isoformat() for i in ax.get_xticks().astype(int)] if x_idx else [],
        rotation=45,
        ha="right",
        fontsize=7,
    )
    if len(data.series) > 1:
        ax.legend(fontsize=8)
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_event_timeline(viz: EventTimelineViz, out_path: Path) -> None:
    events = viz.data.events
    fig, ax = plt.subplots(figsize=(8, 3.5))
    if events:
        xs = list(range(len(events)))
        amounts = [e.amount for e in events]
        max_amount = max(amounts) if max(amounts) > 0 else 1
        sizes = [30 + 400 * (a / max_amount) for a in amounts]
        colors = [e.fail_prob for e in events]
        scatter = ax.scatter(xs, [0] * len(xs), s=sizes, c=colors, cmap="Greys", vmin=0, vmax=1)
        for x, e in zip(xs, events, strict=True):
            ax.annotate(
                f"{e.name}\n{e.date.isoformat()}",
                (x, 0),
                textcoords="offset points",
                xytext=(0, 12),
                ha="center",
                fontsize=7,
            )
        fig.colorbar(scatter, ax=ax, label="fail_prob", shrink=0.6)
        ax.set_yticks([])
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_gauge(viz: GaugeViz, out_path: Path) -> None:
    import numpy as np

    data = viz.data
    fig, ax = plt.subplots(figsize=(5, 3.2), subplot_kw={"aspect": "equal"})
    span = data.max - data.min if data.max != data.min else 1
    frac = max(0.0, min(1.0, (data.value - data.min) / span))

    theta = np.linspace(0, np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), color="#cccccc", linewidth=10, solid_capstyle="round")
    value_theta = np.linspace(0, np.pi * frac, max(2, int(100 * frac)))
    ax.plot(
        np.cos(np.pi - value_theta),
        np.sin(np.pi - value_theta),
        color="#4C72B0",
        linewidth=10,
        solid_capstyle="round",
    )
    for threshold in data.thresholds:
        t_frac = max(0.0, min(1.0, (threshold - data.min) / span))
        tx, ty = np.cos(np.pi * (1 - t_frac)), np.sin(np.pi * (1 - t_frac))
        ax.plot([0.85 * tx, tx], [0.85 * ty, ty], color="#C44E52", linewidth=2)

    ax.text(0, -0.15, f"{data.value:g} ({data.level})", ha="center", fontsize=13, fontweight="bold")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.3, 1.2)
    ax.axis("off")
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.88))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_progress_bars(viz: ProgressBarsViz, out_path: Path) -> None:
    items = viz.data.items
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.5 * len(items))))
    ys = list(range(len(items)))
    ratios = [it.value / it.max if it.max else 0.0 for it in items]
    colors = ["#C44E52" if r > 1 else "#4C72B0" for r in ratios]
    ax.barh(ys, ratios, color=colors)
    ax.axvline(1.0, color="#333333", linestyle="--", linewidth=1)
    for it in items:
        if it.projected is not None and it.max:
            proj_ratio = it.projected / it.max
            y = items.index(it)
            ax.scatter([proj_ratio], [y], color="#333333", marker="|", s=200, zorder=5)
    ax.set_yticks(ys)
    ax.set_yticklabels([it.name for it in items], fontsize=9)
    ax.set_xlabel("사용률 (1.0 = 예산 100%)")
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_delta_bars(viz: DeltaBarsViz, out_path: Path) -> None:
    items = viz.data.items
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.6 * len(items))))
    ys = list(range(len(items)))
    width = 0.35
    ax.barh([y + width / 2 for y in ys], [it.base for it in items], height=width, label="기준")
    ax.barh([y - width / 2 for y in ys], [it.branch for it in items], height=width, label="분기")
    ax.set_yticks(ys)
    ax.set_yticklabels([it.name for it in items], fontsize=9)
    ax.legend(fontsize=8)
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_step_bars(viz: StepBarsViz, out_path: Path) -> None:
    data = viz.data
    xs = list(range(len(data.x)))
    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = [0.0] * len(xs)
    for stack in data.stacks:
        ax.bar(xs, stack.y, bottom=bottom, label=stack.name)
        bottom = [b + y for b, y in zip(bottom, stack.y, strict=True)]
    ax.plot(xs, data.total, color="#333333", marker="o", linestyle="--", label="total")
    ax.set_xticks(xs)
    ax.set_xticklabels([d.isoformat() for d in data.x], rotation=45, ha="right", fontsize=7)
    ax.legend(fontsize=7, ncol=2)
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_ranked_bars(viz: RankedBarsViz, out_path: Path) -> None:
    items = sorted(viz.data.items, key=lambda it: it.rank)
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.5 * len(items))))
    ys = list(range(len(items)))
    ax.barh(ys, [it.effect for it in items], color="#4C72B0")
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{it.rank}. {it.label}" for it in items], fontsize=8)
    ax.invert_yaxis()
    unit = items[0].unit if items else ""
    ax.set_xlabel(f"효과 ({unit})" if unit else "효과")
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def _render_table(viz: TableViz, out_path: Path) -> None:
    data = viz.data
    fig, ax = plt.subplots(figsize=(7, max(1.5, 0.4 * (len(data.rows) + 1))))
    ax.axis("off")
    col_labels = [c.label for c in data.columns]
    cell_text = [[str(row.get(c.key, "")) for c in data.columns] for row in data.rows]
    table = ax.table(cellText=cell_text, colLabels=col_labels, loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


_RENDERERS: dict[str, Any] = {
    "line_band": _render_line_band,
    "event_timeline": _render_event_timeline,
    "gauge": _render_gauge,
    "progress_bars": _render_progress_bars,
    "delta_bars": _render_delta_bars,
    "step_bars": _render_step_bars,
    "ranked_bars": _render_ranked_bars,
    "table": _render_table,
}


def render_viz(viz: Viz, out_dir: Path) -> Path:
    """viz 명세 하나를 PNG 한 장으로 그려 `out_dir/<id>_<kind>.png` 에 쓴다."""

    _configure_korean_font()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{viz.id}_{viz.kind}.png"
    renderer = _RENDERERS.get(viz.kind)
    if renderer is None:
        raise FdtError(code=E_REQ_INVALID, message=f"알 수 없는 viz kind: {viz.kind}")
    renderer(viz, out_path)
    return out_path


def render_result(result_json_path: str | Path, out_dir: str | Path) -> list[Path]:
    """`fdt run` 이 쓴 `EngineResult` JSON -> viz 8종 PNG 목록 (SPEC 10장, §6.3).

    `status=ERROR` 인 결과(viz 가 없음)는 빈 목록을 반환한다.
    """

    in_path = Path(result_json_path)
    try:
        raw = json.loads(in_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FdtError(
            code=E_REQ_INVALID, message=f"결과 파일을 읽을 수 없다: {in_path} ({exc})"
        ) from exc
    except json.JSONDecodeError as exc:
        raise FdtError(code=E_REQ_INVALID, message=f"결과 JSON 파싱 실패: {exc}") from exc

    result_obj = EngineResult.model_validate(raw)
    out_dir_path = Path(out_dir)
    written: list[Path] = []
    for viz in result_obj.viz:
        written.append(render_viz(viz, out_dir_path))
    return written
