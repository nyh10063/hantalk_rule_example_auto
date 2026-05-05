#!/usr/bin/env python3
"""Import manually added rows from encoder_examples.xlsx into item JSONL.

This is a recovery/bridge utility for cases where a human adds supplemental
examples to the gold-like Excel ledger. It keeps item-level JSONL as the
machine-friendly SSOT by converting Excel-only rows into pair examples, then
rewriting the item JSONL/XLSX/summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import openpyxl
except ImportError:  # pragma: no cover - handled at runtime.
    openpyxl = None  # type: ignore[assignment]

try:
    from .detector.span_utils import (
        DEFAULT_GAP_MARKER,
        format_span_segments,
        inject_span_markers,
        make_span_key,
        make_span_text,
        parse_span_segments,
        validate_span_segments,
    )
    from .export_encoder_examples import (
        INPUT_CONSTRUCTION_VERSION,
        SCHEMA_VERSION,
        SPAN_MARKER_STYLE,
        _assign_instance_ids,
        _counter_by,
        _load_item_metadata,
        _write_jsonl,
        _write_xlsx,
    )
except ImportError:  # pragma: no cover - supports direct script execution.
    from detector.span_utils import (
        DEFAULT_GAP_MARKER,
        format_span_segments,
        inject_span_markers,
        make_span_key,
        make_span_text,
        parse_span_segments,
        validate_span_segments,
    )
    from export_encoder_examples import (
        INPUT_CONSTRUCTION_VERSION,
        SCHEMA_VERSION,
        SPAN_MARKER_STYLE,
        _assign_instance_ids,
        _counter_by,
        _load_item_metadata,
        _write_jsonl,
        _write_xlsx,
    )


SUMMARY_SCHEMA_VERSION = "hantalk_encoder_excel_additions_import_summary_v1"
LABEL_KEYS = ("positive", "negative")
ROLE_KEYS = ("pos_conti", "pos_disconti", "neg_target_absent")
SPLIT_KEYS = ("train", "dev", "test")
VALID_SPLITS = set(SPLIT_KEYS)
VALID_ROLES = set(ROLE_KEYS)


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} invalid JSONL") from exc
    return rows


def _normalize_header(value: Any) -> str:
    return str(value or "").strip()


def _read_excel_rows(path: Path) -> list[dict[str, Any]]:
    if openpyxl is None:
        raise RuntimeError("openpyxl is required to read/write .xlsx files")
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
        raise ValueError(f"{path}: blank header inside used header range")
    duplicates = sorted(header for header in set(headers) if headers.count(header) > 1)
    if duplicates:
        raise ValueError(f"{path}: duplicate header(s): {duplicates}")

    rows: list[dict[str, Any]] = []
    for row_no, values in enumerate(rows_iter, start=2):
        trimmed = list(values[: len(headers)])
        if not any(value is not None and str(value).strip() for value in trimmed):
            continue
        row = {header: value for header, value in zip(headers, trimmed)}
        row["_row_no"] = row_no
        rows.append(row)
    return rows


def _string(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _label_for_role(example_role: str) -> tuple[int, str, str | None]:
    if example_role in {"pos_conti", "pos_disconti"}:
        return 1, "positive", None
    if example_role == "neg_target_absent":
        return 0, "negative", "target_absent"
    raise ValueError(f"unsupported example_role={example_role!r}")


def _domain_from_source(source: str) -> str:
    if "일상대화" in source:
        return "daily_conversation"
    if "신문" in source or "뉴스" in source:
        return "news"
    if "비출판" in source:
        return "non_published"
    if "학습자" in source:
        return "learner_spoken_5_6"
    return "manual_supplement"


def _stable_text_id(item_id: str, raw_text: str) -> str:
    # Import hashlib lazily here to keep the top-level imports focused.
    import hashlib

    digest = hashlib.sha1(raw_text.encode("utf-8")).hexdigest()[:12]
    return f"{item_id}_manual_{digest}"


def _convert_excel_row(
    *,
    row: dict[str, Any],
    item_id: str,
    item_meta: dict[str, str],
    source_excel: Path,
    source_tag: str,
) -> dict[str, Any]:
    row_no = int(row.get("_row_no") or 0)
    row_item_id = _string(row.get("item_id"))
    if row_item_id != item_id:
        raise ValueError(f"{source_excel}:{row_no} item_id={row_item_id!r} does not match --item-id={item_id!r}")

    example_id = _string(row.get("example_id"))
    if not example_id:
        raise ValueError(f"{source_excel}:{row_no} blank example_id")
    raw_text = "" if row.get("target_sentence") is None else str(row.get("target_sentence"))
    if not raw_text.strip():
        raise ValueError(f"{source_excel}:{row_no} blank target_sentence")
    split = _string(row.get("split"))
    if split not in VALID_SPLITS:
        raise ValueError(f"{source_excel}:{row_no} invalid split={split!r}")
    example_role = _string(row.get("example_role"))
    if example_role not in VALID_ROLES:
        raise ValueError(f"{source_excel}:{row_no} invalid example_role={example_role!r}")
    label, label_name, negative_type = _label_for_role(example_role)

    span_segments = validate_span_segments(raw_text, parse_span_segments(row.get("span_segments")))
    span_key = make_span_key(span_segments)
    span_text = make_span_text(raw_text, span_segments, gap_marker=DEFAULT_GAP_MARKER)
    pattern_type = _string(row.get("pattern_type")) or ("conti" if len(span_segments) == 1 else "disconti")
    expected_pattern_type = "conti" if len(span_segments) == 1 else "disconti"
    if pattern_type != expected_pattern_type:
        raise ValueError(
            f"{source_excel}:{row_no} pattern_type={pattern_type!r} does not match span_segments "
            f"expected={expected_pattern_type!r}"
        )

    source = _string(row.get("source")) or source_tag
    source_hit_id = f"{source_tag}-{example_id}"
    text_id = _stable_text_id(item_id, raw_text)
    instance_id_text = _string(row.get("instance_id")) or "1"
    try:
        instance_id = int(instance_id_text)
    except ValueError as exc:
        raise ValueError(f"{source_excel}:{row_no} invalid instance_id={instance_id_text!r}") from exc
    if instance_id <= 0:
        raise ValueError(f"{source_excel}:{row_no} instance_id must be positive")

    return {
        "schema_version": SCHEMA_VERSION,
        "input_construction_version": INPUT_CONSTRUCTION_VERSION,
        "span_marker_style": SPAN_MARKER_STYLE,
        "item_id": item_id,
        "example_id": example_id,
        "instance_id": instance_id,
        "label": label,
        "label_name": label_name,
        "example_role": example_role,
        "negative_type": negative_type,
        "split": split,
        "text_a": inject_span_markers(raw_text, span_segments),
        "text_b": item_meta["text_b"],
        "raw_text": raw_text,
        "target_sentence": raw_text,
        "span_segments": span_segments,
        "span_key": span_key,
        "span_text": span_text,
        "span_value_source": "encoder_examples_xlsx",
        "canonical_form": item_meta["canonical_form"],
        "gloss": item_meta["gloss"],
        "group": item_meta["group"],
        "pattern_type": pattern_type,
        "source_hit_id": source_hit_id,
        "hit_id": source_hit_id,
        "candidate_index": str(instance_id),
        "batch_id": source_tag,
        "text_id": text_id,
        "corpus_domain": _domain_from_source(source),
        "source": source,
        "source_file": str(source_excel),
        "source_row_index": str(row_no),
        "source_line_no": str(row_no),
        "regex_match_text": span_text,
        "span_source": "manual_supplement",
        "component_span_status": "manual_supplement",
        "detect_rule_ids": [],
        "human_label": "tp" if label == 1 else "fp",
        "span_status": "ok",
        "memo": "",
        "reviewer": "manual_excel_addition",
        "review_file": str(source_excel),
        "note": (
            f"manual_supplement_from={source_excel.name}; source_tag={source_tag}; "
            f"original_example_id={example_id}; example_role={example_role}"
        ),
    }


def _sort_key(record: dict[str, Any]) -> tuple[int, str]:
    return (0 if int(record.get("label") or 0) == 1 else 1, str(record.get("example_id") or ""))


def _build_summary(
    *,
    item_id: str,
    source_excel: Path,
    base_jsonl: Path,
    out_jsonl: Path,
    out_xlsx: Path,
    out_summary: Path,
    combined_records: list[dict[str, Any]],
    imported_records: list[dict[str, Any]],
    skipped_existing: int,
    skipped_duplicate_content: list[dict[str, str]],
    instance_summary: dict[str, Any],
) -> dict[str, Any]:
    label_counts = Counter("positive" if int(record.get("label") or 0) == 1 else "negative" for record in combined_records)
    role_counts = Counter(str(record.get("example_role") or "unknown") for record in combined_records)
    split_counts = Counter(str(record.get("split") or "unknown") for record in combined_records)
    positive_count = int(label_counts.get("positive", 0))
    negative_count = int(label_counts.get("negative", 0))
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "item_id": item_id,
        "created_at": _now_utc(),
        "import_mode": "encoder_examples_xlsx_additions",
        "source_excel": str(source_excel),
        "base_jsonl": str(base_jsonl),
        "out_jsonl": str(out_jsonl),
        "out_xlsx": str(out_xlsx),
        "out_summary": str(out_summary),
        "n_rows_exported": len(combined_records),
        "n_existing_jsonl_rows": len(combined_records) - len(imported_records),
        "n_imported_rows": len(imported_records),
        "n_excel_rows_skipped_existing_example_id": skipped_existing,
        "n_excel_rows_skipped_duplicate_content": len(skipped_duplicate_content),
        "skipped_duplicate_content": skipped_duplicate_content[:100],
        "label_counts": {key: int(label_counts.get(key, 0)) for key in LABEL_KEYS},
        "role_counts": {key: int(role_counts.get(key, 0)) for key in ROLE_KEYS},
        "split_counts": {key: int(split_counts.get(key, 0)) for key in SPLIT_KEYS},
        "counts_by_domain": _counter_by(combined_records, "corpus_domain"),
        "target_reached": {
            "positive_100": positive_count >= 100,
            "negative_100": negative_count >= 100,
            "positive_target": positive_count >= 100,
            "negative_target": negative_count >= 100,
        },
        "ready_for_training": positive_count >= 100 and negative_count >= 100,
        "class_balance": {
            "positive_count": positive_count,
            "negative_count": negative_count,
            "total": positive_count + negative_count,
            "positive_ratio": positive_count / (positive_count + negative_count) if positive_count + negative_count else 0.0,
            "negative_ratio": negative_count / (positive_count + negative_count) if positive_count + negative_count else 0.0,
            "downsampling_applied": False,
        },
        "instance_policy": {
            "scope": "item_id + text_id when available; manual imports receive stable text_id from raw_text hash",
            "ordering": "span_start, span_end, candidate_index, span_key, hit_id",
            "one_based": True,
        },
        "multi_instance_summary": instance_summary,
        "span_format": "json_list",
        "input_construction_version": INPUT_CONSTRUCTION_VERSION,
        "span_marker_style": SPAN_MARKER_STYLE,
        "warnings": [
            "This import recovered manually added Excel rows into item-level JSONL. Keep JSONL as SSOT after this step."
        ],
    }


def import_encoder_excel_additions(
    *,
    item_id: str,
    bundle_path: Path,
    excel_path: Path,
    jsonl_path: Path,
    out_jsonl: Path,
    out_xlsx: Path,
    out_summary: Path,
    source_tag: str,
) -> dict[str, Any]:
    item_id = item_id.strip()
    if not item_id:
        raise ValueError("--item-id must not be blank")
    if not excel_path.exists():
        raise FileNotFoundError(excel_path)
    if not bundle_path.exists():
        raise FileNotFoundError(bundle_path)
    item_meta = _load_item_metadata(bundle_path, item_id)
    existing_records = _read_jsonl(jsonl_path)
    existing_example_ids = {str(record.get("example_id") or "") for record in existing_records}
    content_keys = {
        (
            str(record.get("item_id") or ""),
            int(record.get("label") or 0),
            str(record.get("raw_text") or ""),
            str(record.get("span_key") or ""),
        )
        for record in existing_records
    }

    imported_records: list[dict[str, Any]] = []
    skipped_existing = 0
    skipped_duplicate_content: list[dict[str, str]] = []
    for row in _read_excel_rows(excel_path):
        example_id = _string(row.get("example_id"))
        if not example_id:
            continue
        if example_id in existing_example_ids:
            skipped_existing += 1
            continue
        record = _convert_excel_row(
            row=row,
            item_id=item_id,
            item_meta=item_meta,
            source_excel=excel_path,
            source_tag=source_tag,
        )
        content_key = (
            str(record.get("item_id") or ""),
            int(record.get("label") or 0),
            str(record.get("raw_text") or ""),
            str(record.get("span_key") or ""),
        )
        if content_key in content_keys:
            skipped_duplicate_content.append(
                {
                    "example_id": str(record.get("example_id") or ""),
                    "raw_text": str(record.get("raw_text") or ""),
                    "span_key": str(record.get("span_key") or ""),
                }
            )
            continue
        existing_example_ids.add(example_id)
        content_keys.add(content_key)
        imported_records.append(record)

    combined_records = list(existing_records) + imported_records
    combined_records.sort(key=_sort_key)
    instance_summary = _assign_instance_ids(combined_records)
    _write_jsonl(out_jsonl, combined_records)
    _write_xlsx(out_xlsx, combined_records)
    summary = _build_summary(
        item_id=item_id,
        source_excel=excel_path,
        base_jsonl=jsonl_path,
        out_jsonl=out_jsonl,
        out_xlsx=out_xlsx,
        out_summary=out_summary,
        combined_records=combined_records,
        imported_records=imported_records,
        skipped_existing=skipped_existing,
        skipped_duplicate_content=skipped_duplicate_content,
        instance_summary=instance_summary,
    )
    _write_json(out_summary, summary)
    return summary


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", required=True)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--excel", required=True, type=Path, help="Edited {item_id}_encoder_examples.xlsx")
    parser.add_argument("--jsonl", required=True, type=Path, help="Current item-level encoder_pair_examples.jsonl")
    parser.add_argument("--out-jsonl", required=True, type=Path)
    parser.add_argument("--out-xlsx", required=True, type=Path)
    parser.add_argument("--out-summary", required=True, type=Path)
    parser.add_argument("--source-tag", default="manual_supplement_dep_noun_de")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        summary = import_encoder_excel_additions(
            item_id=args.item_id,
            bundle_path=args.bundle,
            excel_path=args.excel,
            jsonl_path=args.jsonl,
            out_jsonl=args.out_jsonl,
            out_xlsx=args.out_xlsx,
            out_summary=args.out_summary,
            source_tag=args.source_tag,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should emit concise fatal message.
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "item_id": summary["item_id"],
                "n_rows_exported": summary["n_rows_exported"],
                "n_imported_rows": summary["n_imported_rows"],
                "label_counts": summary["label_counts"],
                "role_counts": summary["role_counts"],
                "split_counts": summary["split_counts"],
                "ready_for_training": summary["ready_for_training"],
                "out_jsonl": summary["out_jsonl"],
                "out_xlsx": summary["out_xlsx"],
                "out_summary": summary["out_summary"],
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
