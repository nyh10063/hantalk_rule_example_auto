#!/usr/bin/env python3
"""Evaluate a grammar-item regex against exported gold JSONL.

The first Phase 1 loop is intentionally small:
regex version JSONL -> gold JSONL -> recall/FN report.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}: {exc}") from exc
    return records


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _select_regex_version(
    records: list[dict[str, Any]],
    item_id: str,
    regex_version: str,
) -> dict[str, Any]:
    item_records = [r for r in records if r.get("item_id") == item_id]
    if not item_records:
        raise ValueError(f"No regex records for item_id={item_id}")
    if regex_version == "latest":
        return item_records[-1]
    for record in item_records:
        if record.get("regex_version") == regex_version:
            return record
    raise ValueError(f"No regex record for item_id={item_id}, regex_version={regex_version}")


def _target_spans(record: dict[str, Any]) -> list[tuple[int, int, str]]:
    spans = record.get("target_spans") or []
    out: list[tuple[int, int, str]] = []
    for idx, span in enumerate(spans):
        try:
            start = int(span["start"])
            end = int(span["end"])
            text = str(span.get("text", ""))
        except Exception as exc:  # noqa: BLE001 - report malformed gold with context.
            example_id = record.get("example_id", "<unknown>")
            raise ValueError(f"Malformed target_spans[{idx}] for {example_id}: {span}") from exc
        out.append((start, end, text))
    return out


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return max(a_start, b_start) < min(a_end, b_end)


def _find_matches(pattern: re.Pattern[str], sentence: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for match in pattern.finditer(sentence):
        start, end = match.span()
        if start == end:
            continue
        matches.append({"start": start, "end": end, "text": match.group(0)})
    return matches


def _is_matched(
    matches: list[dict[str, Any]],
    spans: list[tuple[int, int, str]],
    match_policy: str,
) -> bool:
    if match_policy == "sentence":
        return bool(matches)
    if not matches or not spans:
        return False
    return any(
        _overlaps(int(m["start"]), int(m["end"]), span_start, span_end)
        for m in matches
        for span_start, span_end, _ in spans
    )


def evaluate(
    *,
    item_id: str,
    regex_record: dict[str, Any],
    gold_records: list[dict[str, Any]],
    match_policy: str,
) -> dict[str, Any]:
    pattern_text = regex_record.get("pattern")
    if not isinstance(pattern_text, str) or not pattern_text:
        raise ValueError("Selected regex record has no non-empty pattern")
    try:
        pattern = re.compile(pattern_text)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern: {exc}") from exc

    selected_gold = [r for r in gold_records if r.get("item_id") == item_id]
    fn_records: list[dict[str, Any]] = []
    matched_records: list[dict[str, Any]] = []

    for record in selected_gold:
        sentence = str(record.get("sentence") or "")
        spans = _target_spans(record)
        matches = _find_matches(pattern, sentence)
        matched = _is_matched(matches, spans, match_policy)
        row = {
            "item_id": item_id,
            "regex_version": regex_record.get("regex_version"),
            "example_id": record.get("example_id"),
            "source_example_id": record.get("source_example_id"),
            "split": record.get("split"),
            "pattern_type": record.get("pattern_type"),
            "gold_example_role": record.get("gold_example_role"),
            "target_text": record.get("target_text"),
            "target_spans": record.get("target_spans"),
            "matches": matches,
            "sentence": sentence,
        }
        if matched:
            matched_records.append(row)
        else:
            fn_records.append(row)

    total = len(selected_gold)
    matched_count = len(matched_records)
    recall = matched_count / total if total else 0.0
    return {
        "item_id": item_id,
        "regex_version": regex_record.get("regex_version"),
        "pattern": pattern_text,
        "match_policy": match_policy,
        "gold_total": total,
        "gold_matched": matched_count,
        "gold_recall": recall,
        "fn_count": len(fn_records),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fn_records": fn_records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate regex recall on exported gold JSONL.")
    parser.add_argument("--item-id", default="df003", help="Grammar item id. Default: df003")
    parser.add_argument(
        "--gold",
        type=Path,
        default=None,
        help="Gold JSONL path. Default: exported_gold/{item_id}_gold_50.jsonl",
    )
    parser.add_argument(
        "--versions",
        type=Path,
        default=None,
        help="Regex versions JSONL path. Default: regex/{item_id}_versions.jsonl",
    )
    parser.add_argument("--regex-version", default="latest", help="Regex version id or latest.")
    parser.add_argument(
        "--match-policy",
        choices=["overlap", "sentence"],
        default="overlap",
        help="overlap requires a regex match to overlap a gold target span. sentence only requires any match in the sentence.",
    )
    parser.add_argument("--report", type=Path, default=None, help="Summary JSON output path.")
    parser.add_argument("--fn-report", type=Path, default=None, help="FN JSONL output path.")
    parser.add_argument("--fail-on-fn", action="store_true", help="Exit non-zero if any FN remains.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    item_id = args.item_id
    gold_path = args.gold or Path("exported_gold") / f"{item_id}_gold_50.jsonl"
    versions_path = args.versions or Path("regex") / f"{item_id}_versions.jsonl"

    try:
        regex_records = _read_jsonl(versions_path)
        regex_record = _select_regex_version(regex_records, item_id, args.regex_version)
        gold_records = _read_jsonl(gold_path)
        result = evaluate(
            item_id=item_id,
            regex_record=regex_record,
            gold_records=gold_records,
            match_policy=args.match_policy,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should print friendly error.
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    version = result["regex_version"]
    report_path = args.report or Path("logs") / f"{item_id}_gold_eval_{version}.json"
    fn_report_path = args.fn_report or Path("logs") / f"{item_id}_fn_report_{version}.jsonl"

    fn_records = result.pop("fn_records")
    _write_json(report_path, result)
    _write_jsonl(fn_report_path, fn_records)

    print(f"item_id={result['item_id']}")
    print(f"regex_version={result['regex_version']}")
    print(f"match_policy={result['match_policy']}")
    print(f"gold_total={result['gold_total']}")
    print(f"gold_matched={result['gold_matched']}")
    print(f"gold_recall={result['gold_recall']:.6f}")
    print(f"fn_count={result['fn_count']}")
    print(f"report={report_path}")
    print(f"fn_report={fn_report_path}")

    if args.fail_on_fn and fn_records:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
