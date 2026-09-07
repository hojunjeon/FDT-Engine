"""`fdt/tools/render.py` 단위 테스트 (작업 ID J4, SPEC 9.3, 10장, §6.3).

합성 result(=`test_facts.py` 의 빌더 재사용) 로 8종 viz kind 가 전부 PNG
한 장씩(파일 크기 > 0)으로 그려지는지, 그리고 4 프로필(엔진 fixture) x 5
모드 = 20 결과를 실제로 `engine.run()` 해 렌더한 PNG 도 전부 만들어지는지
검사한다.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib.patches
import matplotlib.pyplot as plt
import matplotlib.table
import numpy as np
import pytest

from fdt.engine.engine import Engine
from fdt.engine.schemas.request import ModeRequest
from fdt.engine.schemas.result import (
    ColumnSpec,
    DeltaBarsData,
    DeltaBarsViz,
    DeltaItem,
    EventPoint,
    EventTimelineData,
    EventTimelineViz,
    RankedBarsData,
    RankedBarsViz,
    RankedItem,
    TableData,
    TableViz,
)
from fdt.engine.taxonomy import Mode
from fdt.tools.render import (
    _build_delta_bars_fig,
    _build_event_timeline_fig,
    _build_ranked_bars_fig,
    _build_table_fig,
    render_result,
    render_viz,
)
from tests.unit.test_facts import AS_OF, RESULT_BUILDERS, build_ok_result

ALL_VIZ_KINDS = {
    "line_band",
    "event_timeline",
    "gauge",
    "progress_bars",
    "delta_bars",
    "step_bars",
    "ranked_bars",
    "table",
}


@pytest.mark.parametrize("mode", list(Mode))
def test_render_viz_writes_nonempty_png_for_every_kind(mode: Mode, tmp_path: Path) -> None:
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    seen_kinds = set()
    for v in engine_result.viz:
        out_path = render_viz(v, tmp_path)
        assert out_path.exists()
        assert out_path.stat().st_size > 0, f"{mode}:{v.id} PNG 가 비어 있다"
        seen_kinds.add(v.kind)
    assert seen_kinds  # 최소 한 종류는 그려졌다


def test_all_eight_viz_kinds_render_across_modes(tmp_path: Path) -> None:
    """5 모드를 합치면 SPEC 9.3 의 8종 kind 가 전부 등장하고, 전부 렌더된다."""

    seen_kinds: set[str] = set()
    for mode in Mode:
        result = RESULT_BUILDERS[mode]()
        engine_result = build_ok_result(mode, result)
        for v in engine_result.viz:
            out_path = render_viz(v, tmp_path)
            assert out_path.stat().st_size > 0
            seen_kinds.add(v.kind)
    assert seen_kinds == ALL_VIZ_KINDS, seen_kinds


def test_render_result_from_json_file(tmp_path: Path) -> None:
    mode = Mode.RISK
    result = RESULT_BUILDERS[mode]()
    engine_result = build_ok_result(mode, result)
    result_path = tmp_path / "result.json"
    result_path.write_text(engine_result.model_dump_json(), encoding="utf-8")

    out_dir = tmp_path / "png"
    written = render_result(result_path, out_dir)

    assert written, "RISK 결과에 viz 가 있는데 PNG 가 하나도 안 만들어졌다"
    for path in written:
        assert path.exists()
        assert path.stat().st_size > 0


def test_render_result_error_status_writes_nothing(tmp_path: Path) -> None:
    dumped: dict[str, object] = {
        "schema_version": "engine-result/1",
        "meta": {
            "engine_id": "a3f9c1d2e4b5",
            "as_of": AS_OF.isoformat(),
            "mode": "FORECAST",
            "seed": 42,
            "n_paths": 200,
            "horizon_days": 30,
            "elapsed_ms": 10,
            "engine_version": "0.1.0",
            "warnings": [],
        },
        "request": {
            "mode": "FORECAST",
            "horizon_days": 30,
            "n_paths": 200,
            "seed": 42,
            "params": {},
        },
        "result": None,
        "facts": [],
        "viz": [],
        "status": "ERROR",
        "error": {"code": "E-TEST", "message": "테스트 오류", "details": {}},
    }
    result_path = tmp_path / "error.json"
    import json

    result_path.write_text(json.dumps(dumped, ensure_ascii=False), encoding="utf-8")

    written = render_result(result_path, tmp_path / "png")
    assert written == []


# ---------------------------------------------------------------------------
# 엔진 fixture(4 프로필) x 5 모드 = 20 결과 렌더
# ---------------------------------------------------------------------------


def _request_for(mode: Mode) -> ModeRequest:
    params: dict[str, object]
    if mode is Mode.WHATIF:
        params = {
            "injections": [
                {
                    "type": "SPEND",
                    "days_from_now": 1,
                    "amount": 150000,
                    "envelope_id": 5,
                    "method": "CARD",
                }
            ]
        }
    elif mode is Mode.GOAL:
        params = {
            "goal_type": "BALANCE",
            "target_amount": 2_000_000,
            "target_date": "2026-12-31",
        }
    elif mode is Mode.OPTIMIZE:
        params = {"objective": "MIN_SHORTFALL_PROB"}
    else:
        params = {}
    return ModeRequest(
        mode=mode, horizon_days=30, n_paths=200, seed=42, params=params  # type: ignore[arg-type]
    )


def test_render_20_results_from_engine_fixtures(
    engines_3m: dict[str, Engine], tmp_path: Path
) -> None:
    """4 프로필 x 5 모드 = 20 결과를 실제로 `engine.run()` 해 렌더한다.

    PLAN Phase 6 완료 조건 "렌더 20 세트 PNG 생성" 을 3개월 fixture 규모로
    확인한다(6개월 골든 세트는 통합 테스트가 별도로 다룬다).
    """

    total_png = 0
    for name, engine in engines_3m.items():
        for mode in Mode:
            req = _request_for(mode)
            result = engine.run(req)
            assert result.status == "OK", (name, mode, result.error)
            out_dir = tmp_path / name / mode.value
            written = render_result_from_engine_result(result, out_dir)
            assert written, f"{name}:{mode} 결과에서 PNG 가 하나도 안 만들어졌다"
            for path in written:
                assert path.stat().st_size > 0
            total_png += len(written)
    assert total_png > 0


def render_result_from_engine_result(result, out_dir: Path):
    from fdt.tools.render import render_viz

    out_dir.mkdir(parents=True, exist_ok=True)
    return [render_viz(v, out_dir) for v in result.viz]


# ---------------------------------------------------------------------------
# QA-103: table 의 unit 표기 (KRW 콤마+"원", % → "%", date → 그대로)
# ---------------------------------------------------------------------------


def _make_table_viz() -> TableViz:
    return TableViz(
        id="payments",
        title="결제일별 부족 확률",
        priority=1,
        data=TableData(
            columns=[
                ColumnSpec(key="due", label="결제일", unit="date"),
                ColumnSpec(key="name", label="항목"),
                ColumnSpec(key="amount", label="금액", unit="KRW"),
                ColumnSpec(key="fail_prob", label="부족 확률", unit="%"),
            ],
            rows=[
                {"due": "2026-09-22", "name": "카드대금", "amount": 62000, "fail_prob": 13},
                {"due": "2026-09-25", "name": "관리비", "amount": 1234567, "fail_prob": 0},
            ],
        ),
        caption="",
    )


def test_table_applies_unit_formatting_qa103() -> None:
    fig = _build_table_fig(_make_table_viz())
    try:
        ax = fig.axes[0]
        table = None
        for child in ax.get_children():
            if isinstance(child, matplotlib.table.Table):
                table = child
                break
        assert table is not None
        cells = table.get_celld()
        # 헤더는 row index 0, 데이터는 1부터. 열 순서: due, name, amount, fail_prob
        assert cells[(1, 2)].get_text().get_text() == "62,000원"
        assert cells[(1, 3)].get_text().get_text() == "13%"
        assert cells[(2, 2)].get_text().get_text() == "1,234,567원"
        assert cells[(2, 3)].get_text().get_text() == "0%"
        # date 컬럼은 그대로 (isoformat 문자열 유지, 접미사 없음)
        assert cells[(1, 0)].get_text().get_text() == "2026-09-22"
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# QA-104: event_timeline 실제 날짜 x축 + 밀집 시 라벨 정리
# ---------------------------------------------------------------------------


def _make_events(n: int) -> list[EventPoint]:
    events = []
    for i in range(n):
        events.append(
            EventPoint(
                date=date(2026, 9, 10 + i),
                kind="CARD_BILL" if i % 2 == 0 else "TELECOM",
                name=f"결제{i}",
                amount=10000 * (i + 1),
                fail_prob=round(0.01 * (i + 1), 2),
            )
        )
    return events


def test_event_timeline_x_axis_is_real_dates_qa104() -> None:
    viz = EventTimelineViz(
        id="events",
        title="이벤트",
        priority=1,
        data=EventTimelineData(events=_make_events(4)),
        caption="",
    )
    fig = _build_event_timeline_fig(viz)
    try:
        ax = fig.axes[0]
        tick_labels = [t.get_text() for t in ax.get_xticklabels()]
        assert tick_labels, "x축 눈금 라벨이 비어 있다"
        for label in tick_labels:
            # "09-10" 형식(월-일), 순수 정수 인덱스가 아니어야 한다
            assert "-" in label
            assert not label.isdigit()
    finally:
        plt.close(fig)


def test_event_timeline_dense_labels_top5_only_qa104() -> None:
    events = _make_events(10)
    viz = EventTimelineViz(
        id="events",
        title="이벤트",
        priority=1,
        data=EventTimelineData(events=events),
        caption="",
    )
    fig = _build_event_timeline_fig(viz)
    try:
        ax = fig.axes[0]
        # annotate 로 붙인 텍스트만 센다(축 눈금 라벨 제외).
        annotation_texts = [
            t.get_text() for t in ax.texts if t.get_text() and "\n" in t.get_text()
        ]
        assert len(annotation_texts) == 5, annotation_texts

        top5_names = {
            e.name for e in sorted(events, key=lambda e: e.fail_prob, reverse=True)[:5]
        }
        for text in annotation_texts:
            name = text.split("\n")[0]
            assert name in top5_names
    finally:
        plt.close(fig)


def test_event_timeline_same_day_events_stack_vertically_qa104() -> None:
    events = [
        EventPoint(date=date(2026, 9, 10), kind="CARD_BILL", name="A", amount=1000, fail_prob=0.1),
        EventPoint(date=date(2026, 9, 10), kind="TELECOM", name="B", amount=2000, fail_prob=0.2),
        EventPoint(date=date(2026, 9, 10), kind="INCOME", name="C", amount=3000, fail_prob=0.3),
    ]
    viz = EventTimelineViz(
        id="events",
        title="이벤트",
        priority=1,
        data=EventTimelineData(events=events),
        caption="",
    )
    fig = _build_event_timeline_fig(viz)
    try:
        ax = fig.axes[0]
        scatter = next(c for c in ax.collections if hasattr(c, "get_offsets"))
        offsets = np.asarray(scatter.get_offsets())
        y_values = sorted(offsets[:, 1].tolist())
        assert y_values == [0.0, 1.0, 2.0], y_values
        x_values = {round(x) for x in offsets[:, 0].tolist()}
        assert x_values == {0}, "같은 날짜 이벤트는 같은 x 위치여야 한다"

        legend = ax.get_legend()
        assert legend is not None
        legend_labels = {t.get_text() for t in legend.get_texts()}
        assert legend_labels == {"CARD_BILL", "TELECOM", "INCOME"}
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# QA-106: ranked_bars 단위 분기 + 순위-길이 일관성
# ---------------------------------------------------------------------------


def _make_ranked_bars_viz() -> RankedBarsViz:
    return RankedBarsViz(
        id="ranked_actions",
        title="행동 후보 효과 순위",
        priority=1,
        data=RankedBarsData(
            items=[
                RankedItem(rank=1, label="구독 해지", effect=5_510_000, unit="KRW"),
                RankedItem(rank=2, label="카드 요일 변경", effect=1_200_000, unit="KRW"),
                RankedItem(rank=3, label="예산 축소", effect=-3.2, unit="%"),
            ]
        ),
        caption="",
    )


def test_ranked_bars_bar_length_matches_rank_order_qa106() -> None:
    viz = _make_ranked_bars_viz()
    fig = _build_ranked_bars_fig(viz)
    try:
        ax = fig.axes[0]
        bars = [p for p in ax.patches if isinstance(p, matplotlib.patches.Rectangle)]
        widths = [b.get_width() for b in bars]
        # 위에서부터(y=0=1위, invert_yaxis 이므로 화면상 맨 위) 순서로
        # 막대가 rank 순서와 같은 순서로 그려졌는지: rank1 효과(5,510,000)
        # >= rank2(1,200,000) > rank3(|-3.2|=3.2) 순서.
        assert widths[0] == pytest.approx(5_510_000)
        assert widths[1] == pytest.approx(1_200_000)
        assert widths[2] == pytest.approx(3.2)
        assert widths[0] > widths[1] > widths[2]
    finally:
        plt.close(fig)


def test_ranked_bars_unit_branch_formatting_qa106() -> None:
    viz = _make_ranked_bars_viz()
    fig = _build_ranked_bars_fig(viz)
    try:
        ax = fig.axes[0]
        labels = [t.get_text() for t in ax.get_yticklabels()]
        assert any("5,510,000원" in label for label in labels)
        assert any("1,200,000원" in label for label in labels)
        # 확률(%) 차원은 x100 되지 않고, 음수 부호가 라벨에 남아야 한다
        assert any("-3.2%" in label for label in labels)
        assert not any("320" in label for label in labels)
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# QA-107: delta_bars 단위별 서브플롯 분리
# ---------------------------------------------------------------------------


def test_delta_bars_single_unit_uses_one_axes_qa107() -> None:
    viz = DeltaBarsViz(
        id="whatif_delta",
        title="델타",
        priority=1,
        data=DeltaBarsData(
            items=[
                DeltaItem(
                    name="말일 잔액", base=1_000_000, branch=1_200_000, delta=200_000, unit="KRW"
                ),
                DeltaItem(
                    name="최저 잔액", base=-50_000, branch=100_000, delta=150_000, unit="KRW"
                ),
            ]
        ),
        caption="",
    )
    fig = _build_delta_bars_fig(viz)
    try:
        assert len(fig.axes) == 1
    finally:
        plt.close(fig)


def test_delta_bars_mixed_units_split_into_subplots_qa107() -> None:
    viz = DeltaBarsViz(
        id="whatif_delta",
        title="델타",
        priority=1,
        data=DeltaBarsData(
            items=[
                DeltaItem(name="부족 확률", base=13, branch=34, delta=21, unit="%"),
                DeltaItem(
                    name="말일 잔액", base=1_000_000, branch=850_000, delta=-150_000, unit="KRW"
                ),
            ]
        ),
        caption="",
    )
    fig = _build_delta_bars_fig(viz)
    try:
        assert len(fig.axes) == 2

        xlabels = [ax.get_xlabel() for ax in fig.axes]
        assert any("%" in lbl for lbl in xlabels)
        assert any("KRW" in lbl for lbl in xlabels)

        # 각 서브플롯은 자신의 단위 항목만 담아, 확률 막대가 KRW 스케일에
        # 눌려 안 보이는 일이 없어야 한다 - 확률 축의 막대 너비가 값 그대로
        # (13, 34 근처)이어야 한다.
        for ax in fig.axes:
            if "%" in ax.get_xlabel():
                rects = [p for p in ax.patches if isinstance(p, matplotlib.patches.Rectangle)]
                widths = [abs(r.get_width()) for r in rects]
                assert all(w <= 100 for w in widths)
    finally:
        plt.close(fig)
