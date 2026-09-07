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
from datetime import date
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from fdt.engine.errors import E_REQ_INVALID, FdtError
from fdt.engine.schemas.result import (
    DeltaBarsViz,
    DeltaItem,
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

# QA-104: event_timeline 의 `kind` 범례용 고정 팔레트(질적 색상, 10 색 순환).
_KIND_PALETTE = (
    "#4C72B0",
    "#DD8452",
    "#55A868",
    "#C44E52",
    "#8172B2",
    "#937860",
    "#DA8BC3",
    "#8C8C8C",
    "#CCB974",
    "#64B5CD",
)


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


# ---------------------------------------------------------------------------
# event_timeline (QA-104: 실제 날짜 x축 + 이벤트 밀집 시 라벨 정리)
# ---------------------------------------------------------------------------


def _build_event_timeline_fig(viz: EventTimelineViz) -> plt.Figure:
    events = list(viz.data.events)
    fig, ax = plt.subplots(figsize=(9, 4.2))

    if events:
        base_date = min(e.date for e in events)

        # 같은 날짜에 여러 이벤트가 있으면 세로로 스택해 겹침을 피한다.
        by_date: dict[date, list[int]] = {}
        for i, e in enumerate(events):
            by_date.setdefault(e.date, []).append(i)

        x_by_idx = [0] * len(events)
        y_by_idx = [0] * len(events)
        for d, idxs in by_date.items():
            offset = (d - base_date).days
            for stack_pos, i in enumerate(idxs):
                x_by_idx[i] = offset
                y_by_idx[i] = stack_pos

        amounts = [e.amount for e in events]
        max_amount = max(amounts) if max(amounts) > 0 else 1
        sizes = [30 + 400 * (a / max_amount) for a in amounts]
        fail_probs = [e.fail_prob for e in events]

        # 색은 계속 fail_prob 회색조(§9.3 encoding.color)로 유지하고,
        # kind 구분은 마커 테두리 색 + 범례로 별도 인코딩한다.
        kinds = sorted({e.kind for e in events})
        kind_color = {k: _KIND_PALETTE[i % len(_KIND_PALETTE)] for i, k in enumerate(kinds)}
        edgecolors = [kind_color[e.kind] for e in events]

        scatter = ax.scatter(
            x_by_idx,
            y_by_idx,
            s=sizes,
            c=fail_probs,
            cmap="Greys",
            vmin=0,
            vmax=1,
            edgecolors=edgecolors,
            linewidths=1.8,
            zorder=3,
        )

        # 이벤트가 8개 이상이면 fail_prob 상위 5개만 텍스트 라벨을 달고
        # 나머지는 점만 남긴다(겹침 방지). 그 미만이면 전부 라벨을 단다.
        if len(events) >= 8:
            label_idx = set(
                sorted(range(len(events)), key=lambda i: events[i].fail_prob, reverse=True)[:5]
            )
        else:
            label_idx = set(range(len(events)))

        # 라벨을 x 위치 순으로 훑으면서, 바로 앞 라벨과 x 가 가까우면
        # 세로 단(段)을 하나씩 올려 텍스트가 옆 라벨과 겹치지 않게 한다.
        _LABEL_X_GAP_THRESHOLD = 6  # 일 단위, 이보다 가까우면 층을 바꾼다
        _LABEL_MAX_TIERS = 3
        _LABEL_TIER_STEP = 46  # pt, 층 사이 간격(폰트 2줄 높이보다 넉넉하게)
        last_x: int | None = None
        tier = 0
        for i in sorted(label_idx, key=lambda i: x_by_idx[i]):
            e = events[i]
            if last_x is not None and abs(x_by_idx[i] - last_x) < _LABEL_X_GAP_THRESHOLD:
                tier = (tier + 1) % _LABEL_MAX_TIERS
            else:
                tier = 0
            last_x = x_by_idx[i]
            ax.annotate(
                f"{e.name}\n{e.date.strftime('%m-%d')}",
                (x_by_idx[i], y_by_idx[i]),
                textcoords="offset points",
                xytext=(0, 12 + 9 * y_by_idx[i] + _LABEL_TIER_STEP * tier),
                ha="center",
                fontsize=7,
            )

        unique_dates = sorted(by_date.keys())
        step = max(1, len(unique_dates) // 8)
        tick_dates = unique_dates[::step]
        ax.set_xticks([(d - base_date).days for d in tick_dates])
        ax.set_xticklabels(
            [d.strftime("%m-%d") for d in tick_dates], rotation=45, ha="right", fontsize=7
        )
        ax.set_xlabel("날짜 (월-일)")
        ax.set_yticks([])
        max_stack = max(y_by_idx) if y_by_idx else 0
        ax.set_ylim(-0.6, max_stack + 1.4)

        fig.colorbar(scatter, ax=ax, label="fail_prob", shrink=0.6)

        legend_handles = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                linestyle="",
                markerfacecolor="none",
                markeredgecolor=kind_color[k],
                markeredgewidth=1.8,
                markersize=8,
                label=k,
            )
            for k in kinds
        ]
        ax.legend(
            handles=legend_handles,
            fontsize=7,
            loc="upper left",
            bbox_to_anchor=(1.15, 1.0),
            title="kind",
            title_fontsize=7,
        )

    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 0.82, 0.9))
    return fig


def _render_event_timeline(viz: EventTimelineViz, out_path: Path) -> None:
    fig = _build_event_timeline_fig(viz)
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


# ---------------------------------------------------------------------------
# delta_bars (QA-107: 단위별 서브플롯으로 분리)
# ---------------------------------------------------------------------------


def _build_delta_bars_fig(viz: DeltaBarsViz) -> plt.Figure:
    items = viz.data.items

    groups: dict[str, list[DeltaItem]] = {}
    for it in items:
        groups.setdefault(it.unit, []).append(it)
    unit_keys = list(groups.keys())
    n_rows = max(1, len(unit_keys))

    row_heights = [max(1.6, 0.6 * len(groups[u]) + 0.8) for u in unit_keys] or [2.5]
    fig, axes = plt.subplots(n_rows, 1, figsize=(7, sum(row_heights)), squeeze=False)
    axes_flat = list(axes[:, 0])

    for ax, unit in zip(axes_flat, unit_keys, strict=False):
        group_items = groups[unit]
        ys = list(range(len(group_items)))
        width = 0.35
        ax.barh(
            [y + width / 2 for y in ys],
            [it.base for it in group_items],
            height=width,
            label="기준",
            color="#4C72B0",
        )
        ax.barh(
            [y - width / 2 for y in ys],
            [it.branch for it in group_items],
            height=width,
            label="분기",
            color="#DD8452",
        )
        ax.set_yticks(ys)
        ax.set_yticklabels([it.name for it in group_items], fontsize=9)
        ax.set_xlabel(f"단위: {unit}" if unit else "값")
        ax.legend(fontsize=8)

    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    return fig


def _render_delta_bars(viz: DeltaBarsViz, out_path: Path) -> None:
    fig = _build_delta_bars_fig(viz)
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


# ---------------------------------------------------------------------------
# ranked_bars (QA-106: 단위별 표기 분기 + 순위-길이 일관성)
# ---------------------------------------------------------------------------


def _format_effect(value: float, unit: str) -> str:
    """부호 있는 effect 값을 unit 에 맞춰 사람이 읽을 문자열로 만든다.

    확률 차원(`%`/`prob`)은 소수 첫째 자리 `%`, KRW 차원은 천단위 콤마 +
    "원". 그 외 단위는 값 뒤에 그대로 붙인다. 부호는 항상 라벨에 표시하고
    (막대 길이 자체는 절대값을 쓰므로) 방향은 여기서만 드러난다.
    """

    sign = "+" if value >= 0 else "-"
    av = abs(value)
    if unit in ("%", "prob"):
        return f"{sign}{av:.1f}%"
    if unit == "KRW":
        return f"{sign}{av:,.0f}원"
    if unit:
        return f"{sign}{av:g}{unit}"
    return f"{sign}{av:g}"


def _build_ranked_bars_fig(viz: RankedBarsViz) -> plt.Figure:
    items = sorted(viz.data.items, key=lambda it: it.rank)
    fig, ax = plt.subplots(figsize=(7, max(2.5, 0.5 * len(items))))
    ys = list(range(len(items)))

    # 막대 길이는 항상 절대값을 쓴다(개선 방향이 음수인 차원도 길이로는
    # 비교 가능하게 하고, 부호·방향은 라벨과 막대 색으로만 구분한다).
    # 순위(`rank`)는 이미 정렬 순서를 결정하므로, 여기서 뒤집는 y축과
    # 함께 1위가 맨 위/가장 두드러진 위치에 오도록만 하고 막대 길이 자체를
    # 임의로 재조정하지 않는다(각 항목의 실제 효과 크기를 왜곡 없이 반영).
    lengths = [abs(it.effect) for it in items]
    colors = ["#C44E52" if it.effect < 0 else "#4C72B0" for it in items]
    ax.barh(ys, lengths, color=colors)
    ax.set_yticks(ys)
    ax.set_yticklabels(
        [f"{it.rank}. {it.label} ({_format_effect(it.effect, it.unit)})" for it in items],
        fontsize=8,
    )
    ax.invert_yaxis()

    units = {it.unit for it in items}
    if len(units) == 1:
        unit_label = next(iter(units))
        ax.set_xlabel(f"효과 크기 (절대값, {unit_label})" if unit_label else "효과 크기 (절대값)")
    else:
        ax.set_xlabel("효과 크기 (절대값, 단위는 각 라벨 참고)")

    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    return fig


def _render_ranked_bars(viz: RankedBarsViz, out_path: Path) -> None:
    fig = _build_ranked_bars_fig(viz)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------------------
# table (QA-103: unit 표기 - KRW 천단위 콤마 + "원", % → "%", date → 그대로)
# ---------------------------------------------------------------------------


def _format_table_cell(value: Any, unit: str | None) -> str:
    if unit == "KRW" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:,.0f}원"
    if unit == "%" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return f"{value:g}%"
    return str(value)


def _build_table_fig(viz: TableViz) -> plt.Figure:
    data = viz.data
    fig, ax = plt.subplots(figsize=(7, max(1.5, 0.4 * (len(data.rows) + 1))))
    ax.axis("off")
    col_labels = [c.label for c in data.columns]
    cell_text = [
        [_format_table_cell(row.get(c.key, ""), c.unit) for c in data.columns]
        for row in data.rows
    ]
    table = ax.table(cellText=cell_text, colLabels=col_labels, loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    _wrap_caption(fig, viz.title, viz.caption)
    fig.tight_layout(rect=(0, 0.04, 1, 0.9))
    return fig


def _render_table(viz: TableViz, out_path: Path) -> None:
    fig = _build_table_fig(viz)
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
