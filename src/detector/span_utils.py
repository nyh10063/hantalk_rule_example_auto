"""Span helpers for detector output.

All spans use Python's 0-based [start, end) convention.
"""

from __future__ import annotations

import ast
import json
from typing import Iterable

SpanSegment = list[int]
DEFAULT_GAP_MARKER = " ... "
SPAN_START_MARKER = "[SPAN]"
SPAN_END_MARKER = "[/SPAN]"


def validate_span_segments(raw_text: str, span_segments: Iterable[Iterable[int]]) -> list[SpanSegment]:
    """Return normalized span segments or raise ValueError.

    Segments must be non-empty, ordered pairs within the raw text boundaries.
    """
    normalized: list[SpanSegment] = []
    text_len = len(raw_text)
    for idx, segment in enumerate(span_segments):
        values = list(segment)
        if len(values) != 2:
            raise ValueError(f"span segment {idx} must have exactly 2 values: {values}")
        start, end = int(values[0]), int(values[1])
        if start < 0 or end < 0:
            raise ValueError(f"span segment {idx} has negative boundary: {values}")
        if start >= end:
            raise ValueError(f"span segment {idx} must satisfy start < end: {values}")
        if end > text_len:
            raise ValueError(f"span segment {idx} exceeds raw_text length {text_len}: {values}")
        if normalized and start < normalized[-1][1]:
            raise ValueError(f"span segment {idx} overlaps or is out of order: {values}")
        normalized.append([start, end])
    if not normalized:
        raise ValueError("span_segments must not be empty")
    return normalized


def parse_span_segments(value: object) -> list[SpanSegment]:
    """Parse JSON-style or legacy Python-style span segments.

    New HanTalk outputs should use JSON-style spans such as
    ``[[10,13],[15,16]]``. The legacy Python tuple style
    ``[(10,13),(15,16)]`` is accepted for backward compatibility.
    """
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("span_segments must not be blank")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = ast.literal_eval(text)
    else:
        parsed = value

    if not isinstance(parsed, (list, tuple)):
        raise ValueError(f"span_segments must be a list: {parsed!r}")

    normalized: list[SpanSegment] = []
    for idx, segment in enumerate(parsed):
        if not isinstance(segment, (list, tuple)):
            raise ValueError(f"span segment {idx} must be a list/tuple: {segment!r}")
        values = list(segment)
        if len(values) != 2:
            raise ValueError(f"span segment {idx} must have exactly 2 values: {values!r}")
        normalized.append([int(values[0]), int(values[1])])
    if not normalized:
        raise ValueError("span_segments must not be empty")
    return normalized


def format_span_segments(span_segments: Iterable[Iterable[int]]) -> str:
    """Format spans as compact JSON list text for Excel/CSV cells."""
    normalized = [[int(start), int(end)] for start, end in span_segments]
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def inject_span_markers(
    raw_text: str,
    span_segments: Iterable[Iterable[int]],
    *,
    start_marker: str = SPAN_START_MARKER,
    end_marker: str = SPAN_END_MARKER,
) -> str:
    """Return raw_text with each span wrapped in marker tokens."""
    normalized = validate_span_segments(raw_text, span_segments)
    marked = raw_text
    for start, end in reversed(normalized):
        marked = marked[:start] + start_marker + marked[start:end] + end_marker + marked[end:]
    return marked


def make_span_key(span_segments: Iterable[Iterable[int]]) -> str:
    """Build a stable key such as '10:13|15:16'."""
    return "|".join(f"{int(start)}:{int(end)}" for start, end in span_segments)


def make_span_text(
    raw_text: str,
    span_segments: Iterable[Iterable[int]],
    *,
    gap_marker: str = DEFAULT_GAP_MARKER,
) -> str:
    """Join span text pieces using a gap marker for discontinuous spans."""
    normalized = validate_span_segments(raw_text, span_segments)
    return gap_marker.join(raw_text[start:end] for start, end in normalized)


def make_envelope(span_segments: Iterable[Iterable[int]]) -> SpanSegment:
    """Return the smallest continuous [start, end) envelope for segments."""
    normalized = [[int(start), int(end)] for start, end in span_segments]
    if not normalized:
        raise ValueError("span_segments must not be empty")
    return [min(start for start, _ in normalized), max(end for _, end in normalized)]


def make_char_window(
    raw_text: str,
    span_segments: Iterable[Iterable[int]],
    *,
    window_chars: int = 20,
) -> dict[str, int | str]:
    """Return a character window around the span envelope.

    window_chars means N characters to the left and N characters to the right.
    """
    if window_chars < 0:
        raise ValueError("window_chars must be >= 0")
    start, end = make_envelope(span_segments)
    window_start = max(0, start - window_chars)
    window_end = min(len(raw_text), end + window_chars)
    return {
        "start": window_start,
        "end": window_end,
        "text": raw_text[window_start:window_end],
    }


def spans_overlap(
    a_segments: Iterable[Iterable[int]],
    b_segments: Iterable[Iterable[int]],
) -> bool:
    """Return True if any segment pair overlaps."""
    a_norm = [[int(start), int(end)] for start, end in a_segments]
    b_norm = [[int(start), int(end)] for start, end in b_segments]
    return any(max(a_start, b_start) < min(a_end, b_end) for a_start, a_end in a_norm for b_start, b_end in b_norm)
