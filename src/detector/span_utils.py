"""Span helpers for detector output.

All spans use Python's 0-based [start, end) convention.
"""

from __future__ import annotations

from typing import Iterable

SpanSegment = list[int]


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
        normalized.append([start, end])
    if not normalized:
        raise ValueError("span_segments must not be empty")
    return normalized


def make_span_key(span_segments: Iterable[Iterable[int]]) -> str:
    """Build a stable key such as '10:13|15:16'."""
    return "|".join(f"{int(start)}:{int(end)}" for start, end in span_segments)


def make_span_text(
    raw_text: str,
    span_segments: Iterable[Iterable[int]],
    *,
    gap_marker: str = " ... ",
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
