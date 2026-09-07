"""공용 날짜 유틸 (SPEC 8.4, 리뷰 N10).

`_clamped_month_date`/`_add_month` 조합("매월 같은 일자, 말일 보정")이
`simulate.py`, `state.py`, `goal.py` 세 곳에 중복 구현돼 있었다(리뷰
20260907_W6_W10.md N10). 순수 날짜 계산이라 어느 모듈의 private 로직도
아니므로 이 공용 모듈로 뽑는다.

`fdt/engine/modes/goal.py` 는 이 모듈을 쓴다. `simulate.py`/`state.py` 의
동일 사본 교체는 이 파일 소유자(J2)가 아니라 J1 소관이다 - 보고에 남긴다.
"""

from __future__ import annotations

import calendar
from datetime import date

__all__ = ["add_months", "clamped_month_date"]


def clamped_month_date(year: int, month: int, day: int) -> date:
    """`(year, month)` 의 말일을 넘지 않도록 `day` 를 눌러 담은 날짜.

    예: `clamped_month_date(2026, 2, 31) == date(2026, 2, 28)`.
    """

    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last_day))


def add_months(d: date, n: int) -> date:
    """`d` 에서 `n`개월 뒤(음수면 이전) 날짜, 일자는 `d.day` 기준으로 말일
    보정한다("매월 같은 일자, 말일 보정" - SPEC 8.4 확정 유입 계산 문단).

    `d.day` 를 고정 앵커로 매번 다시 계산하므로(중간 결과의 클램프된 일자를
    다음 계산의 기준으로 삼지 않는다), 같은 앵커에서 `n=1,2,3...` 을 반복
    호출해도 앵커 일자가 절대 드리프트하지 않는다.
    """

    total_month_index = d.year * 12 + (d.month - 1) + n
    year, month0 = divmod(total_month_index, 12)
    month = month0 + 1
    return clamped_month_date(year, month, d.day)
