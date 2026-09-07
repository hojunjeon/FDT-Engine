"""발화용 사실(facts) 빌더 (SPEC 9.2, 9.4).

`build_facts(mode, result, as_of=...)` 는 모드별 `ResultUnion` 에서 사용자
노출 수치를 **재계산 없이** 뽑아 `Fact` 목록으로 낸다. 각 수치는
`renderings_for()` 로 단위·정밀도에 맞는 한국어 표기 후보(`allowed_renderings`)
를 만든다. 이 표기 집합은 에이전트가 문장에 그대로 써도 되는 숫자의 전체
집합이고(SPEC 9.2), `fdt/tools/validate.py`(R7) 가 viz 의 annotations·caption
숫자가 이 집합에 포함되는지 검사한다.

facts.py 는 엔진 코어(`fdt/engine/**`)이므로 파일·콘솔 I/O 를 하지 않는다
(SPEC 4.2). 값은 result 에 이미 있는 것만 반올림·표기 변환하고, 합·차·비율을
새로 계산하지 않는다(금지 사항).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

from fdt.engine.schemas.result import (
    Fact,
    ForecastResult,
    GoalResult,
    OptimizeResult,
    ResultUnion,
    RiskResult,
    WhatIfResult,
)
from fdt.engine.taxonomy import Mode

_MAN = 10_000
_EOK = 100_000_000

# ---------------------------------------------------------------------------
# 한국어 금액 표기 (KRW)
# ---------------------------------------------------------------------------


def _format_group4(n: int) -> str:
    """0~9999 를 "천" 단위까지만 축약한 표기.

    2000 -> "2천" (딱 떨어지는 천 배수), 11 -> "11"(그 외엔 아라비아 숫자
    그대로). 재무 금액 표기 관례("2천만원", "11만원")를 단순화해 따른다.
    """

    if n == 0:
        return ""
    if n % 1000 == 0:
        return f"{n // 1000}천"
    return str(n)


def _won_text(av: int) -> str:
    """0 이상 정수 원을 억/만/천 단위로 묶어 표기한다(SPEC 9.2 표기 예시).

    - 19100 -> "1만 9천"
    - 118000 -> "11만 8천"
    - 1180000 -> "118만"
    - 120000000 -> "1억 2천만"
    100원 미만 잔돈은 버린다(천 단위까지만 표기).
    """

    eok, rem_after_eok = divmod(av, _EOK)
    man, rem = divmod(rem_after_eok, _MAN)
    cheon = rem // 1000

    chunks: list[str] = []
    if eok:
        chunks.append(f"{eok}억")
    if man:
        chunks.append(f"{_format_group4(man)}만")
    if cheon:
        chunks.append(f"{cheon}천")
    if not chunks:
        return "0"
    return " ".join(chunks)


def _krw_renderings(value: int | float, *, signed: bool = False) -> list[str]:
    """SPEC 9.2 KRW `allowed_renderings` 규칙.

    0 -> ["0원"]. 음수는 "-"(ASCII 하이픈) 로 표시하고 "부족 X원" 표기를
    추가한다. 100만 미만이고 만원 단위 나머지가 있으면 "X.Y만원" 소수 표기도
    추가한다.
    """

    iv = round(value)
    if iv == 0:
        return ["0원"]

    sign = "-" if iv < 0 else ""
    av = abs(iv)

    out: list[str] = []
    plus = "+" if (signed and iv > 0) else ""
    out.append(f"{plus}{sign}{av:,}원")
    out.append(f"{plus}{sign}{_won_text(av)}원")

    rem_man = av % _MAN
    if 0 < av < 100_000 and rem_man != 0:
        decimal = round(av / _MAN, 1)
        out.append(f"{plus}{sign}{decimal:g}만원")

    rounded_units = round(av / _MAN)
    rounded = rounded_units * _MAN
    out.append(f"약 {plus}{sign}{_won_text(rounded)}원")

    if iv < 0:
        out.append(f"부족 {av:,}원")

    return out


def _pct_renderings(
    prob_or_pct: float, *, already_pct: bool = False, signed: bool = False
) -> list[str]:
    """확률/비율을 `%` 정수 표기로 낸다(M1: 모드 내 확률 표기 % 정수 통일).

    `already_pct=True` 면 입력이 이미 0~100 스케일(예: 델타 %), 아니면 0~1
    확률로 보고 100을 곱한다.
    """

    pct = prob_or_pct if already_pct else prob_or_pct * 100
    rounded = round(pct)
    plus = "+" if (signed and rounded > 0) else ""
    ten_rounded = round(pct / 10.0) * 10
    return [f"{plus}{rounded}%", f"약 {plus}{ten_rounded}%"]


def _ratio_renderings(value: float) -> list[str]:
    """ratio 단위: 소수 2자리 + 정수 % 둘 다(SPEC 9.2 예시 "0.23","23%")."""

    return [f"{value:.2f}", f"{round(value * 100)}%"]


def _prob_renderings(value: float) -> list[str]:
    return [f"{value:.2f}"]


def _score_renderings(value: int | float, *, suffix: str = "점") -> list[str]:
    iv = round(value)
    return [str(iv), f"{iv}{suffix}"]


def _date_renderings(d: date, *, as_of: date) -> list[str]:
    """절대 날짜 2 종 + as_of 기준 상대 표현(SPEC 9.2).

    "다음 주 화요일" 같은 요일 상대 표현은 만들지 않는다(작업 지시 명시).
    """

    delta = (d - as_of).days
    out = [d.isoformat(), f"{d.month}월 {d.day}일"]
    if delta == 0:
        out.append("오늘")
    elif delta == 1:
        out.append("내일")
    elif delta > 1:
        out.append(f"{delta}일 뒤")
    else:
        out.append(f"{abs(delta)}일 전")
    return out


def _bool_renderings(value: bool) -> list[str]:
    return ["예" if value else "아니오", "true" if value else "false"]


def _text_renderings(value: Any) -> list[str]:
    return [str(value)]


def renderings_for(
    value: Any,
    unit: str,
    precision: int = 0,
    *,
    as_of: date | None = None,
    signed: bool = False,
) -> list[str]:
    """단위별 `allowed_renderings` 후보 목록을 만든다 (SPEC 9.2).

    `precision` 은 KRW 값이 이미 반올림된 정밀도를 나타낸다(-2: 100원,
    -4: 만원). 표기 후보 생성 자체는 원본 정수를 그대로 쓰고, precision 은
    호출자가 Fact.precision 필드에 담아 "이 값이 어느 단위까지만 정확한지"를
    알리는 용도다(추가 반올림은 하지 않는다 - 이미 반올림된 값이 들어온다).
    """

    if unit == "KRW":
        return _krw_renderings(value, signed=signed)
    if unit == "%":
        return _pct_renderings(value, already_pct=True, signed=signed)
    if unit == "prob":
        return _prob_renderings(value)
    if unit == "ratio":
        return _ratio_renderings(value)
    if unit in ("점",):
        return _score_renderings(value, suffix="점")
    if unit == "일":
        return [str(round(value)), f"{round(value)}일"]
    if unit == "date":
        if as_of is None:
            raise ValueError("date 단위 렌더링은 as_of 가 필요하다")
        d = value if isinstance(value, date) else date.fromisoformat(str(value))
        return _date_renderings(d, as_of=as_of)
    if isinstance(value, bool):
        return _bool_renderings(value)
    return _text_renderings(value)


# ---------------------------------------------------------------------------
# Fact 생성 헬퍼
# ---------------------------------------------------------------------------


def _krw_fact(
    key: str,
    label: str,
    amount: int | float,
    importance: int,
    *,
    precision: int = -2,
    hint: str | None = None,
    signed: bool = False,
) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=round(amount),
        unit="KRW",
        precision=precision,
        allowed_renderings=renderings_for(amount, "KRW", precision, signed=signed),
        importance=importance,
        hint=hint,
    )


def _pct_fact(
    key: str,
    label: str,
    prob: float,
    importance: int,
    *,
    hint: str | None = None,
    signed: bool = False,
    already_pct: bool = False,
) -> Fact:
    pct_value = prob if already_pct else prob * 100
    return Fact(
        key=key,
        label=label,
        value=round(pct_value),
        unit="%",
        precision=0,
        allowed_renderings=_pct_renderings(prob, already_pct=already_pct, signed=signed),
        importance=importance,
        hint=hint,
    )


def _ratio_fact(
    key: str, label: str, value: float, importance: int, *, hint: str | None = None
) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=value,
        unit="ratio",
        precision=2,
        allowed_renderings=_ratio_renderings(value),
        importance=importance,
        hint=hint,
    )


def _score_fact(
    key: str, label: str, value: int | float, importance: int, *, hint: str | None = None
) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=round(value),
        unit="점",
        precision=0,
        allowed_renderings=_score_renderings(value),
        importance=importance,
        hint=hint,
    )


def _date_fact(
    key: str, label: str, d: date, importance: int, as_of: date, *, hint: str | None = None
) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=d.isoformat(),
        unit="date",
        precision=0,
        allowed_renderings=_date_renderings(d, as_of=as_of),
        importance=importance,
        hint=hint,
    )


def _text_fact(
    key: str, label: str, value: Any, importance: int, *, hint: str | None = None
) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=str(value),
        unit="text",
        precision=0,
        allowed_renderings=_text_renderings(value),
        importance=importance,
        hint=hint,
    )


def _bool_fact(
    key: str, label: str, value: bool, importance: int, *, hint: str | None = None
) -> Fact:
    return Fact(
        key=key,
        label=label,
        value=value,
        unit="text",
        precision=0,
        allowed_renderings=_bool_renderings(value),
        importance=importance,
        hint=hint,
    )


# ---------------------------------------------------------------------------
# 모드별 facts (SPEC 9.4)
# ---------------------------------------------------------------------------


def _facts_forecast(result: ForecastResult, as_of: date) -> list[Fact]:
    facts: list[Fact] = [
        _krw_fact(
            "end_balance_median", "말일 예상 잔액(중앙값)", result.end_point.median_balance, 1
        ),
        _krw_fact(
            "min_balance_median", "최저 예상 잔액(중앙값)", result.min_point.median_balance, 1
        ),
        _date_fact("min_balance_date", "최저 잔액 예상일", result.min_point.date, 1, as_of),
        _pct_fact("shortfall_prob", "부족 확률", result.shortfall_prob, 1),
        _pct_fact("card_shortfall_prob", "카드대금 부족 확률", result.card_shortfall_prob, 2),
    ]

    if result.min_point.p10_balance is not None:
        facts.append(
            _krw_fact("min_balance_p10", "최저 예상 잔액(P10)", result.min_point.p10_balance, 2)
        )

    exhausting = [e for e in result.envelopes if e.exhaust_date_median is not None]
    exhausting.sort(key=lambda e: e.exhaust_date_median)  # type: ignore[arg-type, return-value]
    for i, env in enumerate(exhausting[:2], start=1):
        assert env.exhaust_date_median is not None
        facts.append(
            _date_fact(
                f"envelope_exhaust_date_{i}",
                f"{env.name} 예산 소진 예상일",
                env.exhaust_date_median,
                1,
                as_of,
                hint=f"envelope_id={env.envelope_id}",
            )
        )
        facts.append(
            _pct_fact(
                f"envelope_overrun_prob_{i}",
                f"{env.name} 예산 초과 확률",
                env.overrun_prob,
                2,
                hint=f"envelope_id={env.envelope_id}",
            )
        )

    events_sorted = sorted(result.events, key=lambda ev: (-ev.fail_prob, ev.date))
    for i, ev in enumerate(events_sorted[:3], start=1):
        facts.append(
            _krw_fact(
                f"event_amount_{i}",
                f"{ev.name} 금액",
                ev.amount,
                3,
                hint=f"date={ev.date.isoformat()},kind={ev.kind}",
            )
        )
        facts.append(
            _pct_fact(
                f"event_fail_prob_{i}",
                f"{ev.name} 부족 확률",
                ev.fail_prob,
                3,
                hint=f"date={ev.date.isoformat()}",
            )
        )

    return facts


def _facts_whatif(result: WhatIfResult, as_of: date) -> list[Fact]:
    facts: list[Fact] = [
        _krw_fact("delta_min_balance", "최저 잔액 변화", result.delta.min_balance, 1, signed=True),
        _pct_fact(
            "delta_shortfall_prob",
            "부족 확률 변화",
            result.delta.shortfall_prob * 100,
            1,
            already_pct=True,
            signed=True,
        ),
        _text_fact("verdict", "판정", result.verdict, 1),
        _date_fact(
            "branch_min_balance_date",
            "분기 최저 잔액 예상일",
            result.branch.min_point.date,
            1,
            as_of,
        ),
        _krw_fact("delta_end_balance", "말일 잔액 변화", result.delta.end_balance, 2, signed=True),
        _pct_fact(
            "delta_card_shortfall_prob",
            "카드대금 부족 확률 변화",
            result.delta.card_shortfall_prob * 100,
            2,
            already_pct=True,
            signed=True,
        ),
        _krw_fact("base_min_balance", "기준 최저 잔액", result.base.min_point.median_balance, 2),
        _krw_fact(
            "branch_min_balance", "분기 최저 잔액", result.branch.min_point.median_balance, 2
        ),
    ]

    if result.delta.first_shortfall_date.branch is not None:
        facts.append(
            _date_fact(
                "branch_first_shortfall_date",
                "분기 첫 부족일",
                result.delta.first_shortfall_date.branch,
                3,
                as_of,
            )
        )

    envs = sorted(result.delta.envelopes, key=lambda e: e.remaining_change)
    for i, env in enumerate(envs[:2], start=1):
        facts.append(
            _krw_fact(
                f"envelope_remaining_change_{i}",
                f"봉투 잔여 변화 {i}",
                env.remaining_change,
                3,
                signed=True,
                hint=f"envelope_id={env.envelope_id}",
            )
        )

    return facts


def _facts_goal(result: GoalResult, as_of: date) -> list[Fact]:
    facts: list[Fact] = [
        _bool_fact("feasible", "목표 달성 가능", result.feasible, 1),
        _pct_fact("achieve_prob", "목표 달성 확률", result.achieve_prob, 1),
        _krw_fact("gap_median", "부족액(중앙값)", result.gap.median, 1, signed=True),
        _ratio_fact("reduction_ratio", "지출 축소 비율", result.required.reduction_ratio, 1),
        _pct_fact("plan_achieve_prob", "계획 실행 시 달성 확률", result.plan_achieve_prob, 1),
        _krw_fact("gap_p10", "부족액(P10)", result.gap.p10, 2, signed=True),
        _krw_fact(
            "total_discretionary_cap",
            "총 재량 지출 한도",
            result.required.total_discretionary_cap,
            2,
        ),
        _krw_fact(
            "baseline_discretionary", "기준 재량 지출", result.required.baseline_discretionary, 2
        ),
    ]

    if result.weekly_caps:
        first = result.weekly_caps[0]
        facts.append(_krw_fact("first_week_cap", "첫 주 지출 상한", first.total_cap, 2))

    for i, note in enumerate(result.notes[:2], start=1):
        facts.append(_text_fact(f"note_{i}", "참고", note, 3))

    return facts


def _facts_risk(result: RiskResult, as_of: date) -> list[Fact]:
    facts: list[Fact] = [
        _score_fact("risk_score", "위험 점수", result.risk_score, 1, hint=f"level={result.level}"),
        _text_fact("level", "위험 단계", result.level, 1),
        _date_fact("worst_day", "가장 위험한 날", result.worst_day, 1, as_of),
        _krw_fact("expected_shortfall", "예상 부족액", result.expected_shortfall, 1),
        _krw_fact("safe_to_spend_today", "오늘 안심 소비 한도", result.safe_to_spend_today, 1),
        _pct_fact("shortfall_prob", "부족 확률", result.shortfall_prob, 2),
        _pct_fact("card_shortfall_prob", "카드대금 부족 확률", result.card_shortfall_prob, 2),
        _score_fact(
            "health_score", "재무 건강 점수", result.health.score, 2, hint=result.health.level
        ),
        _text_fact("health_level", "재무 건강 단계", result.health.level, 3),
    ]

    payment_risks_sorted = sorted(result.payment_risks, key=lambda p: -p.fail_prob)
    for i, pr in enumerate(payment_risks_sorted[:3], start=1):
        importance = 1 if i == 1 else (2 if i == 2 else 3)
        facts.append(
            _date_fact(f"payment_risk_due_{i}", f"위험 결제일 {i}", pr.due, importance, as_of)
        )
        facts.append(
            _krw_fact(f"payment_risk_amount_{i}", f"위험 결제 금액 {i}", pr.amount, importance)
        )
        facts.append(
            _pct_fact(
                f"payment_risk_fail_prob_{i}", f"위험 결제 부족 확률 {i}", pr.fail_prob, importance
            )
        )
        facts.append(
            _text_fact(f"payment_risk_name_{i}", f"위험 결제 항목 {i}", pr.name, importance)
        )

    return facts


def _facts_optimize(result: OptimizeResult, as_of: date) -> list[Fact]:
    facts: list[Fact] = [
        _pct_fact("baseline_shortfall_prob", "기준 부족 확률", result.baseline.shortfall_prob, 1),
    ]

    if result.ranked:
        top = result.ranked[0]
        label = (
            top.actions[0].label if top.actions and top.actions[0].label else f"행동 {top.rank}위"
        )
        facts.append(_text_fact("top_action_label", "1위 행동", label, 1))

        delta_val = top.effect.get("delta")
        if isinstance(delta_val, (int, float)):
            if result.objective == "MIN_SHORTFALL_PROB":
                facts.append(
                    _pct_fact(
                        "top_action_delta",
                        "1위 행동 효과",
                        delta_val * 100,
                        1,
                        already_pct=True,
                        signed=True,
                    )
                )
            elif result.objective == "MAX_END_BALANCE":
                facts.append(
                    _krw_fact("top_action_delta", "1위 행동 효과", delta_val, 1, signed=True)
                )
            else:
                facts.append(_ratio_fact("top_action_delta", "1위 행동 효과", delta_val, 1))

        for i, ranked_action in enumerate(result.ranked[1:3], start=2):
            r_label = (
                ranked_action.actions[0].label
                if ranked_action.actions and ranked_action.actions[0].label
                else f"행동 {ranked_action.rank}위"
            )
            facts.append(_text_fact(f"rank{i}_action_label", f"{i}위 행동", r_label, 3))

    facts.append(_text_fact("evaluated", "평가한 후보 수", result.evaluated, 3))
    facts.append(_text_fact("sim_calls", "시뮬레이션 호출 수", result.sim_calls, 3))

    return facts


_MODE_BUILDERS: dict[Mode, Callable[[Any, date], list[Fact]]] = {
    Mode.FORECAST: _facts_forecast,
    Mode.WHATIF: _facts_whatif,
    Mode.GOAL: _facts_goal,
    Mode.RISK: _facts_risk,
    Mode.OPTIMIZE: _facts_optimize,
}


def build_facts(mode: Mode, result: ResultUnion, *, as_of: date) -> list[Fact]:
    """모드별 result -> facts 목록 (SPEC 9.2, 9.4). 값 재계산 없음."""

    builder = _MODE_BUILDERS.get(mode)
    if builder is None:
        raise ValueError(f"알 수 없는 모드: {mode!r}")
    return builder(result, as_of)  # type: ignore[arg-type]


__all__ = ["build_facts", "renderings_for"]
