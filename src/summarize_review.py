#!/usr/bin/env python3
"""Summarize human-labeled review files for example collection."""

from __future__ import annotations

import argparse
import csv
import json
import re
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
BATCH_ID_RE = re.compile(r"batch[_-](\d{3,})", re.IGNORECASE)

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


def _resolve_summary_out_path(
    *,
    item_id: str,
    out_path: Path | None,
    artifact_root: Path | None,
) -> Path:
    if out_path is not None:
        return out_path
    if artifact_root is None:
        raise ValueError("Missing --out. Pass --out explicitly or use --artifact-root to derive {artifact_root}/{item_id}/{item_id}_review_summary.json.")
    return artifact_root / item_id / f"{item_id}_review_summary.json"


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


def _build_rule_refinement_status(
    *,
    tp_count: int,
    fp_count: int,
    processed_batches: int,
    max_processed_batches: int,
    fp_tp_ratio_threshold: float,
    has_cleanup_issue: bool,
) -> dict[str, Any]:
    ratio_available = tp_count > 0 or fp_count > 0
    ratio_is_infinite = tp_count == 0 and fp_count > 0
    if tp_count > 0:
        fp_tp_ratio: float | None = fp_count / tp_count
    else:
        fp_tp_ratio = None

    should_consider_rule_update = False
    if has_cleanup_issue:
        reason = "needs_label_cleanup"
    elif processed_batches >= max_processed_batches:
        reason = "processed_batches_limit_reached"
    elif not ratio_available:
        reason = "fp_tp_ratio_unavailable"
    elif ratio_is_infinite:
        should_consider_rule_update = True
        reason = "fp_tp_ratio_infinite"
    elif fp_tp_ratio is not None and fp_tp_ratio > fp_tp_ratio_threshold:
        should_consider_rule_update = True
        reason = "fp_tp_ratio_above_threshold"
    else:
        reason = "fp_tp_ratio_within_threshold"

    return {
        "tp_count": tp_count,
        "fp_count": fp_count,
        "fp_tp_ratio": fp_tp_ratio,
        "fp_tp_ratio_available": ratio_available,
        "fp_tp_ratio_is_infinite": ratio_is_infinite,
        "processed_batches": processed_batches,
        "should_consider_rule_update": should_consider_rule_update,
        "reason": reason,
        "note": "Rule updates require gold 50 recall=1 recheck before corpus search.",
    }


def _item_reference(row: dict[str, str]) -> tuple[str | None, str | None, str | None]:
    origin_e_id = str(row.get("origin_e_id") or "").strip()
    unit_id = str(row.get("unit_id") or "").strip()
    if origin_e_id:
        return "origin_e_id", origin_e_id, unit_id
    if unit_id:
        return "unit_id", unit_id, unit_id
    return None, None, None


def _extract_batch_id(row: dict[str, str], input_path: Path) -> str:
    """Return a normalized batch id from row metadata or filename."""
    candidates = [
        str(row.get("batch_id") or "").strip(),
        str(row.get("hit_id") or "").strip(),
        input_path.name,
    ]
    for candidate in candidates:
        if not candidate:
            continue
        match = BATCH_ID_RE.search(candidate)
        if match:
            return f"batch_{match.group(1)}"
    return "unknown"


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
    target_pos: int,
    target_neg: int,
    max_batches: int,
    fp_tp_ratio_threshold: float,
) -> dict[str, Any]:
    if not item_id.strip():
        raise ValueError("--item-id must not be blank")
    if not input_paths:
        raise ValueError("At least one --input is required")
    if target_pos < 0:
        raise ValueError("--target-pos must be >= 0")
    if target_neg < 0:
        raise ValueError("--target-neg must be >= 0")
    if max_batches <= 0:
        raise ValueError("--max-batches must be > 0")
    if fp_tp_ratio_threshold <= 0:
        raise ValueError("--fp-tp-ratio-threshold must be > 0")
    expected_item_id = item_id.strip()

    label_counts: Counter[str] = Counter()
    span_status_counts: Counter[str] = Counter()
    by_domain: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_span_source: defaultdict[str, Counter[str]] = defaultdict(Counter)
    by_component_span_status: defaultdict[str, Counter[str]] = defaultdict(Counter)
    input_summaries: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    cleanup_flags: list[str] = []
    warnings: list[str] = []
    seen_hit_ids: dict[str, str] = {}
    duplicate_hit_ids: list[dict[str, str]] = []
    item_mismatch_rows: list[dict[str, Any]] = []
    missing_item_reference_rows: list[dict[str, Any]] = []
    n_rows = 0
    n_tp_blank_span_status = 0
    processed_batch_ids: set[str] = set()

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
            processed_batch_ids.add(_extract_batch_id(row, input_path))

            item_ref_column, item_ref_value, unit_id_value = _item_reference(row)
            if item_ref_value is None:
                missing_item_reference_rows.append(
                    {
                        "input_file": str(input_path),
                        "row_index": row_index,
                        "hit_id": hit_id,
                    }
                )
            elif item_ref_value != expected_item_id and unit_id_value != expected_item_id:
                item_mismatch_rows.append(
                    {
                        "input_file": str(input_path),
                        "row_index": row_index,
                        "hit_id": hit_id,
                        "item_id": expected_item_id,
                        "checked_column": item_ref_column,
                        "checked_value": item_ref_value,
                        "origin_e_id": str(row.get("origin_e_id") or "").strip(),
                        "unit_id": str(row.get("unit_id") or "").strip(),
                    }
                )

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
    if item_mismatch_rows:
        examples = item_mismatch_rows[:10]
        raise ValueError(f"Review file item_id mismatch for --item-id={expected_item_id}: {examples}")
    if missing_item_reference_rows:
        warnings.append("item_reference_missing")

    normalized_label_counts = _counter_to_counts(label_counts, LABEL_KEYS)
    normalized_span_status_counts = _counter_to_counts(span_status_counts, SPAN_STATUS_KEYS)
    positive_count = normalized_label_counts["tp"]
    negative_count = normalized_label_counts["fp"]
    positive_target_reached = positive_count >= target_pos
    negative_target_reached = negative_count >= target_neg
    all_targets_reached = positive_target_reached and negative_target_reached
    sorted_batch_ids = sorted(processed_batch_ids)
    processed_batches = len(processed_batch_ids)
    max_batches_reached = processed_batches >= max_batches
    target_reached = {
        "positive_100": positive_target_reached,
        "negative_100": negative_target_reached,
        "positive_target": positive_target_reached,
        "negative_target": negative_target_reached,
    }

    if normalized_label_counts["blank"] or normalized_label_counts["invalid"]:
        cleanup_flags.append("human_label_blank_or_invalid")
    if normalized_span_status_counts["invalid"]:
        cleanup_flags.append("span_status_invalid")
    if n_tp_blank_span_status:
        cleanup_flags.append("tp_span_status_blank")

    if cleanup_flags:
        stop_reason = "needs_label_cleanup"
        next_action = "needs_label_cleanup"
    elif all_targets_reached:
        stop_reason = "target_reached"
        next_action = "ready_for_encoder_export"
    elif max_batches_reached:
        stop_reason = "max_batches_reached"
        next_action = "max_batches_reached"
    else:
        stop_reason = "continue_batch_search"
        next_action = "continue_batch_search"

    collection_policy = {
        "target_pos": target_pos,
        "target_neg": target_neg,
        "max_processed_batches": max_batches,
        "cli_flag": "--max-batches",
    }
    collection_status = {
        "processed_batches": processed_batches,
        "processed_batch_ids": sorted_batch_ids,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_target_reached": positive_target_reached,
        "negative_target_reached": negative_target_reached,
        "all_targets_reached": all_targets_reached,
        "max_batches_reached": max_batches_reached,
        "stop_reason": stop_reason,
        "next_action": next_action,
    }
    rule_refinement_policy = {
        "fp_tp_ratio_threshold": fp_tp_ratio_threshold,
        "use_human_label_only": True,
        "rule_update_basis": "gold_fn_or_human_confirmed_systematic_fp",
    }
    rule_refinement_status = _build_rule_refinement_status(
        tp_count=positive_count,
        fp_count=negative_count,
        processed_batches=processed_batches,
        max_processed_batches=max_batches,
        fp_tp_ratio_threshold=fp_tp_ratio_threshold,
        has_cleanup_issue=bool(cleanup_flags),
    )

    summary = {
        "schema_version": "hantalk_review_summary_v1",
        "item_id": expected_item_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_files": [str(path) for path in input_paths],
        "n_files": len(input_paths),
        "n_rows": n_rows,
        "duplicate_policy": "error",
        "item_id_validation": {
            "policy": "error_on_mismatch_warn_on_missing_reference",
            "expected_item_id": expected_item_id,
            "checked_columns": ["origin_e_id", "unit_id"],
            "n_missing_item_reference_rows": len(missing_item_reference_rows),
            "missing_item_reference_rows": missing_item_reference_rows[:100],
            "n_missing_item_reference_rows_listed": min(len(missing_item_reference_rows), 100),
        },
        "label_counts": normalized_label_counts,
        "span_status_counts": normalized_span_status_counts,
        "by_domain": _group_counts_to_dict(by_domain),
        "by_span_source": _group_counts_to_dict(by_span_source),
        "by_component_span_status": _group_counts_to_dict(by_component_span_status),
        "collection_policy": collection_policy,
        "collection_status": collection_status,
        "rule_refinement_policy": rule_refinement_policy,
        "rule_refinement_status": rule_refinement_status,
        "target_reached": target_reached,
        "next_action": next_action,
        "cleanup_flags": cleanup_flags,
        "warnings": warnings,
        "invalid_rows": invalid_rows[:100],
        "n_invalid_rows_total": len(invalid_rows),
        "n_invalid_rows_listed": min(len(invalid_rows), 100),
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
    parser.add_argument("--out", help="Output summary JSON path")
    parser.add_argument(
        "--artifact-root",
        help="Base artifact folder, e.g. /.../HanTalk_arti/example_making. Used to derive {artifact_root}/{item_id}/{item_id}_review_summary.json when --out is omitted.",
    )
    parser.add_argument("--target-pos", type=int, default=100)
    parser.add_argument("--target-neg", type=int, default=100)
    parser.add_argument(
        "--max-batches",
        type=int,
        default=3,
        help="Maximum number of processed labeled review batches to summarize before stopping collection/refinement.",
    )
    parser.add_argument(
        "--fp-tp-ratio-threshold",
        type=float,
        default=2.0,
        help="If FP/TP is above this threshold before --max-batches is reached, flag the item for systematic FP rule-update review.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        out_path = _resolve_summary_out_path(
            item_id=args.item_id.strip(),
            out_path=Path(args.out) if args.out else None,
            artifact_root=Path(args.artifact_root) if args.artifact_root else None,
        )
        summary = summarize_reviews(
            item_id=args.item_id,
            input_paths=[Path(path) for path in args.inputs],
            out_path=out_path,
            target_pos=args.target_pos,
            target_neg=args.target_neg,
            max_batches=args.max_batches,
            fp_tp_ratio_threshold=args.fp_tp_ratio_threshold,
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
                "collection_status": summary["collection_status"],
                "rule_refinement_status": summary["rule_refinement_status"],
                "next_action": summary["next_action"],
                "out": str(out_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
