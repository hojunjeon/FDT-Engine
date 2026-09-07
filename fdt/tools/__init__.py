"""fdt.tools: 엔진 밖 보조 도구 모음 (CLI 등에서 사용, 외부 I/O 허용).

`fdt/engine/**` 는 SPEC §4.2 "엔진 코어는 외부 I/O 없음" 을 지켜야 하므로,
파일 쓰기·표준출력 등을 하는 코드는 이 패키지에 둔다.
"""

from __future__ import annotations
