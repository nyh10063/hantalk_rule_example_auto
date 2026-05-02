#!/usr/bin/env python3
"""Summarize human-labeled review files for example collection."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import openpyxl
except ImportError:  # pragma: no cover - handled at runtime for xlsx input.
    openpyxl = None  # type: ignore[assignment]

LABEL_KEYS = ("tp", "fp", "unclear", "blank", "invalid")
SPAN_STATUS_KEYS = ("ok", "span_wrong", "not_applicable", "blank", "invalid")
REQUIRED_COLUMNS = {"hit_id", "human_label", "span_status"}

LABEL_ALIASES = {
    "tp": "tp",
    "t": "tp",
    "true_positive": "tp",
    "true positive": "tp",
    "positive": "tp",
    "pos": "tp",
    "fp": "fp",
    "f": "fp",
    "false_positive": "fp",
    "false positive": "fp",
    "negative": "fp",
    "neg": "fp",
    "unclear": "unclear",
    "unsure": "unclear",
    "unknown": "unclear",
    "?": "unclear",
}

SPAN_STATUS_ALIASES = {
    "ok": "ok",
    "o": "ok",
    "span_wrong": "span_wrong",
    "span wrong": "span_wrong",
    "wrong": "span_wrong",
    "not_applicable": "not_applicable",
    "not applicable": "not_applicable",
    "na": "not_applicable",
    "n/a": "not_applicable",
    "none": "not_applicable",
}


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def _normalize_header(value: Any) -> str:
    return str(value or "").strip()


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_group_value(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "unknown"


def _normalize_label(value: Any) -> str:
    text = _normalize_key(value)
    if not text:
        return "blank"
    return LABEL_ALIASES.get(text, "invalid")


def _normalize_span_status(value: Any) -> str:
    text = _normalize_key(value)
    if not text:
        return "blank"
    return SPAN_STATUS_ALIASES.get(text, "invalid")


def _counter_to_counts(counter: Counter[str], keys: tuple[str, ...]) -> dict[str, int]:
    return {key: int(counter.get(key, 0)) for key in keys}


def _group_counts_to_dict(group_counts: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {
        group: _counter_to_counts(counter, LABEL_KEYS)
        for group, counter in sorted(group_counts.items())
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing header row")
        normalized_fieldnames = [_normalize_header(name) for name in reader.fieldnames]
        if any(not name for name in normalized_fieldnames):
            raise ValueError(f"{path}: blank header cell inside header row")
        if len(set(normalized_fieldnames)) != len(normalized_fieldnames):
            duplicates = sorted(
                name for name in set(normalized_fieldnames) if normalized_fieldnames.count(name) > 1
            )
            raise ValueError(f"{path}: duplicate header after strip: {duplicates}")
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append(
                {
                    normalized_name: str(row.get(original_name) or "").strip()
                    for original_name, normalized_name in zip(reader.fieldnames, normalized_fieldnames)
                }
            )
        return rows


def _read_xlsx(path: Path) -> list[dict[str, str]]:
    if openpyxl is None:
        raise RuntimeError("openpyxl is required to read .xlsx files")
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.worksheets[0]
    rows_iter = sheet.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        raise ValueError(f"{path}: empty workbook") from None
    headers = [_normalize_header(value) for value in header_row]
    while headers and not headers[-1]:
        headers.pop()
    if not headers:
        raise ValueError(f"{path}: missing header row")
    if any(not header for header in headers):
        raise ValueError(f"{path}: blank header cell inside header row")
    if len(set(headers)) != len(headers):
        duplicates = sorted(header for header in set(headers) if headers.count(header) > 1)
        raise ValueError(f"{path}: duplicate header after strip: {duplicates}")

    rows: list[dict[str, str]] = []
    for values in rows_iter:
        trimmed_values = list(values[: len(headers)])
        if not any(value is not None and str(value).strip() for value in trimmed_values):
            continue
        row: dict[str, str] = {}
        for header, value in zip(headers, trimmed_values):
            row[header] = "" if value is None else str(value).strip()
        rows.append(row)
    return rows


def _read_review_file(path: Path) -> list[dict[str, str]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".xlsx":
        return _read_xlsx(path)
    raise ValueError(f"Unsupported review file extension: {path}")


def _validate_columns(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError(f"{path}: no data rows")
    columns = set(rows[0])
    missing = sorted(REQUIRED_COLUMNS - columns)
    if missing:
        raise ValueError(f"{path}: missing required columns: {missing}")


def summarize_reviews(
    *,
    item_id: str,
    input_paths: list[Path],
    out_path: Path,
) -> dict[str, Any]:
    if not item_id.strip():
        raise ValueError("--item-id must not be blank")
    if not input_paths:
        raise ValueError("At least one --input is required")

    label_counts: Counter[str] = Counter()
    span_status_counts: Counter[str] = Counter()
    by_domain: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_span_source: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_component_span_status: defaultdict[str, Counter[str]] = defaultdict(Counter)
    input_summaries: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    cleanup_flags: list[str] = []
    seen_hit_ids: dict[str, str] = {}
    duplicate_hit_ids: list[dict[str, str]] = []
    n_rows = 0
    n_tp_blank_span_status = 0

    for input_path in input_paths:
        rows = _read_review_file(input_path)
        _validate_columns(input_path, rows)
        file_counts: Counter[str] = Counter()
        for row_index, row in enumerate(rows, start=2):
            hit_id = str(row.get("hit_id") or "").strip()
            if not hit_id:
                raise ValueError(f"{input_path}:{row_index} blank hit_id")
            if hit_id in seen_hit_ids:
                duplicate_hit_ids.append(
                    {
                        "hit_id": hit_id,
                        "first_file": seen_hit_ids[hit_id],
                        "duplicate_file": str(input_path),
                    }
                )
                continue
            seen_hit_ids[hit_id] = str(input_path)

            label = _normalize_label(row.get("human_label"))
            span_status = _normalize_span_status(row.get("span_status"))
            domain = _normalize_group_value(row.get("corpus_domain"))
            span_source = _normalize_group_value(row.get("span_source"))
            component_status = _normalize_group_value(row.get("component_span_status"))

            n_rows += 1
            label_counts[label] += 1
            span_status_counts[span_status] += 1
            by_domain[domain][label] += 1
            by_span_source[span_source][label] += 1
            by_component_span_status[component_status][label] += 1
            file_counts[label] += 1

            if label in {"blank", "invalid"} or span_status == "invalid" or (label == "tp" and span_status == "blank"):
                invalid_rows.append(
                    {
                        "input_file": str(input_path),
                        "row_index": row_index,
                        "hit_id": hit_id,
                        "human_label": row.get("human_label", ""),
                        "normalized_label": label,
                        "span_status": row.get("span_status", ""),
                        "normalized_span_status": span_status,
                    }
                )
            if label == "tp" and span_status == "blank":
                n_tp_blank_span_status += 1

        input_summaries.append(
            {
                "input_file": str(input_path),
                "n_rows": len(rows),
                "label_counts": _counter_to_counts(file_counts, LABEL_KEYS),
            }
        )

    if duplicate_hit_ids:
        examples = duplicate_hit_ids[:10]
        raise ValueError(f"Duplicate hit_id found under duplicate_policy=error: {examples}")

    normalized_label_counts = _counter_to_counts(label_counts, LABEL_KEYS)
    normalized_span_status_counts = _counter_to_counts(span_status_counts, SPAN_STATUS_KEYS)
    target_reached = {
        "positive_100": normalized_label_counts["tp"] >= 100,
        "negative_100": normalized_label_counts["fp"] >= 100,
    }

    if normalized_label_counts["blank"] or normalized_label_counts["invalid"]:
        cleanup_flags.append("human_label_blank_or_invalid")
    if normalized_span_status_counts["invalid"]:
        cleanup_flags.append("span_status_invalid")
    if n_tp_blank_span_status:
        cleanup_flags.append("tp_span_status_blank")

    if cleanup_flags:
        next_action = "needs_label_cleanup"
    elif target_reached["positive_100"] and target_reached["negative_100"]:
        next_action = "ready_for_encoder_export"
    else:
        next_action = "continue_batch_search"

    summary = {
        "schema_version": "hantalk_review_summary_v1",
        "item_id": item_id.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_files": [str(path) for path in input_paths],
        "n_files": len(input_paths),
        "n_rows": n_rows,
        "duplicate_policy": "error",
        "label_counts": normalized_label_counts,
        "span_status_counts": normalized_span_status_counts,
        "by_domain": _group_counts_to_dict(by_domain),
        "by_span_source": _group_counts_to_dict(by_span_source),
        "by_component_span_status": _group_counts_to_dict(by_component_span_status),
        "target_reached": target_reached,
        "next_action": next_action,
        "cleanup_flags": cleanup_flags,
        "invalid_rows": invalid_rows[:100],
        "n_invalid_rows_reported": len(invalid_rows),
        "duplicate_hit_ids": [],
        "input_summaries": input_summaries,
    }
    _write_json(out_path, summary)
    return summary


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", required=True, help="Grammar item id, e.g. df003")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        dest="inputs",
        help="Labeled review .xlsx or .csv file. Can be passed multiple times.",
    )
    parser.add_argument("--out", required=True, help="Output summary JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        summary = summarize_reviews(
            item_id=args.item_id,
            input_paths=[Path(path) for path in args.inputs],
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "item_id": summary["item_id"],
                "n_rows": summary["n_rows"],
                "label_counts": summary["label_counts"],
                "target_reached": summary["target_reached"],
                "next_action": summary["next_action"],
                "out": args.out,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
