#!/usr/bin/env python3
"""Merge item-level HanTalk encoder pair examples into derived aggregate files.

Item-level ``*_encoder_pair_examples.jsonl`` files are the SSOT. The ``all``
outputs produced by this script are derived artifacts and should be regenerated,
not manually appended.
"""

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
except ImportError:  # pragma: no cover - handled at runtime for xlsx output.
    openpyxl = None  # type: ignore[assignment]

try:
    from .detector.span_utils import format_span_segments, parse_span_segments
except ImportError:  # pragma: no cover - supports direct script execution.
    from detector.span_utils import format_span_segments, parse_span_segments

SUMMARY_SCHEMA_VERSION = "hantalk_all_encoder_examples_summary_v1"
EXPECTED_ROW_SCHEMA_VERSION = "hantalk_encoder_pair_example_v1"
EXPECTED_INPUT_CONSTRUCTION_VERSION = "hantalk_binary_pair_v1"
EXPECTED_SPAN_MARKER_STYLE = "[SPAN]...[/SPAN]"

ALLOWED_SPLITS = ("train", "dev", "test")
ALLOWED_ROLES = ("pos_conti", "pos_disconti", "neg_target_absent")
LABEL_KEYS = ("positive", "negative")
EXCLUDED_DISCOVER_DIRS = {"all", "tmp", "archive", "__pycache__"}
REQUIRED_KEYS = {
    "schema_version",
    "input_construction_version",
    "item_id",
    "example_id",
    "label",
    "split",
    "text_a",
    "text_b",
    "raw_text",
    "span_segments",
    "span_key",
    "span_text",
    "example_role",
}
XLSX_COLUMNS = [
    "item_id",
    "example_id",
    "label",
    "split",
    "example_role",
    "pattern_type",
    "raw_text",
    "span_segments",
    "span_key",
    "span_text",
    "text_a",
    "text_b",
    "corpus_domain",
    "source",
    "source_hit_id",
    "detect_rule_ids",
    "note",
]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")


def _json_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return str(value)


def _csv_cell(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if value is None:
        return ""
    return value


def _discover_inputs(artifact_root: Path) -> list[Path]:
    root = artifact_root.expanduser()
    if not root.exists():
        raise FileNotFoundError(f"--artifact-root does not exist: {root}")
    discovered: list[Path] = []
    for item_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        name = item_dir.name
        if name in EXCLUDED_DISCOVER_DIRS or name.startswith("."):
            continue
        candidate = item_dir / f"{name}_encoder_pair_examples.jsonl"
        if candidate.exists():
            discovered.append(candidate)
    if not discovered:
        raise FileNotFoundError(f"No item-level encoder pair JSONL files found under {root}")
    return discovered


def _resolve_input_paths(args: argparse.Namespace) -> list[Path]:
    has_inputs = bool(args.inputs)
    if has_inputs and args.discover:
        raise ValueError("Use either --input or --discover, not both")
    if not has_inputs and not args.discover:
        raise ValueError("Pass at least one --input or use --discover with --artifact-root")
    if args.discover:
        if args.artifact_root is None:
            raise ValueError("--discover requires --artifact-root")
        return _discover_inputs(args.artifact_root)
    return [Path(path).expanduser() for path in args.inputs]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} invalid JSON") from exc
            row["_source_file"] = str(path)
            row["_line_no"] = line_no
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no examples found")
    return rows


def _validate_and_normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    source = f"{row.get('_source_file')}:{row.get('_line_no')}"
    missing = sorted(key for key in REQUIRED_KEYS if key not in row)
    if missing:
        raise ValueError(f"{source}: missing required keys: {missing}")

    schema_version = str(row["schema_version"]).strip()
    if schema_version != EXPECTED_ROW_SCHEMA_VERSION:
        raise ValueError(
            f"{source}: invalid schema_version {schema_version!r}; expected {EXPECTED_ROW_SCHEMA_VERSION!r}"
        )
    input_version = str(row["input_construction_version"]).strip()
    if input_version != EXPECTED_INPUT_CONSTRUCTION_VERSION:
        raise ValueError(
            f"{source}: invalid input_construction_version {input_version!r}; "
            f"expected {EXPECTED_INPUT_CONSTRUCTION_VERSION!r}"
        )
    span_marker_style = str(row.get("span_marker_style") or EXPECTED_SPAN_MARKER_STYLE).strip()
    if span_marker_style != EXPECTED_SPAN_MARKER_STYLE:
        raise ValueError(
            f"{source}: invalid span_marker_style {span_marker_style!r}; expected {EXPECTED_SPAN_MARKER_STYLE!r}"
        )

    item_id = str(row["item_id"]).strip()
    example_id = str(row["example_id"]).strip()
    split = str(row["split"]).strip()
    example_role = str(row["example_role"]).strip()
    text_a = str(row["text_a"]).strip()
    text_b = str(row["text_b"]).strip()
    raw_text = str(row["raw_text"]).strip()
    span_key = str(row["span_key"]).strip()
    span_text = str(row["span_text"]).strip()

    if not item_id:
        raise ValueError(f"{source}: blank item_id")
    if not example_id:
        raise ValueError(f"{source}: blank example_id")
    if split not in ALLOWED_SPLITS:
        raise ValueError(f"{source}: invalid split {split!r}")
    if example_role not in ALLOWED_ROLES:
        raise ValueError(f"{source}: invalid example_role {example_role!r}")
    if not text_a:
        raise ValueError(f"{source}: blank text_a")
    if "[SPAN]" not in text_a or "[/SPAN]" not in text_a:
        raise ValueError(f"{source}: text_a must include [SPAN] and [/SPAN] markers")
    if not text_b:
        raise ValueError(f"{source}: blank text_b")
    if not raw_text:
        raise ValueError(f"{source}: blank raw_text")
    if not span_key:
        raise ValueError(f"{source}: blank span_key")
    if not span_text:
        raise ValueError(f"{source}: blank span_text")

    try:
        label = int(row["label"])
    except Exception as exc:
        raise ValueError(f"{source}: label must be 0 or 1") from exc
    if label not in {0, 1}:
        raise ValueError(f"{source}: label must be 0 or 1, got {row['label']!r}")
    if label == 1 and example_role not in {"pos_conti", "pos_disconti"}:
        raise ValueError(f"{source}: label=1 requires pos_conti or pos_disconti, got {example_role!r}")
    if label == 0 and example_role != "neg_target_absent":
        raise ValueError(f"{source}: label=0 requires neg_target_absent, got {example_role!r}")

    try:
        span_segments = parse_span_segments(row["span_segments"])
    except Exception as exc:
        raise ValueError(f"{source}: invalid span_segments") from exc

    normalized = {key: value for key, value in row.items() if not key.startswith("_")}
    normalized["schema_version"] = schema_version
    normalized["input_construction_version"] = input_version
    normalized["span_marker_style"] = span_marker_style
    normalized["item_id"] = item_id
    normalized["example_id"] = example_id
    normalized["label"] = label
    normalized["split"] = split
    normalized["example_role"] = example_role
    normalized["text_a"] = text_a
    normalized["text_b"] = text_b
    normalized["raw_text"] = raw_text
    normalized["span_segments"] = span_segments
    normalized["span_key"] = span_key
    normalized["span_text"] = span_text
    normalized["corpus_domain"] = str(row.get("corpus_domain") or "unknown").strip() or "unknown"
    normalized["source"] = str(row.get("source") or "").strip()
    normalized["source_hit_id"] = str(row.get("source_hit_id") or row.get("hit_id") or "").strip()
    normalized["pattern_type"] = str(row.get("pattern_type") or "").strip()
    normalized["note"] = str(row.get("note") or "").strip()
    return normalized


def _load_and_validate(input_paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_example_ids: dict[str, str] = {}
    seen_item_example_ids: dict[tuple[str, str], str] = {}
    seen_item_label_text_span: dict[tuple[str, int, str, str], str] = {}

    for input_path in input_paths:
        for raw_row in _read_jsonl(input_path):
            row = _validate_and_normalize_row(raw_row)
            source = f"{raw_row.get('_source_file')}:{raw_row.get('_line_no')}"
            example_id = row["example_id"]
            item_example_key = (row["item_id"], row["example_id"])
            item_label_text_span_key = (row["item_id"], row["label"], row["raw_text"], row["span_key"])

            if example_id in seen_example_ids:
                raise ValueError(
                    f"duplicate global example_id {example_id!r}: "
                    f"{seen_example_ids[example_id]} and {source}"
                )
            if item_example_key in seen_item_example_ids:
                raise ValueError(
                    f"duplicate (item_id, example_id) {item_example_key!r}: "
                    f"{seen_item_example_ids[item_example_key]} and {source}"
                )
            if item_label_text_span_key in seen_item_label_text_span:
                raise ValueError(
                    "duplicate (item_id, label, raw_text, span_key) "
                    f"{item_label_text_span_key!r}: {seen_item_label_text_span[item_label_text_span_key]} and {source}"
                )

            seen_example_ids[example_id] = source
            seen_item_example_ids[item_example_key] = source
            seen_item_label_text_span[item_label_text_span_key] = source
            rows.append(row)

    return sorted(rows, key=_sort_key)


def _sort_key(row: dict[str, Any]) -> tuple[str, int, str, str]:
    return (
        str(row["item_id"]),
        -int(row["label"]),
        str(row["example_role"]),
        str(row["example_id"]),
    )


def _write_xlsx(path: Path, rows: list[dict[str, Any]]) -> None:
    if openpyxl is None:
        raise RuntimeError("openpyxl is required to write .xlsx files")
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "examples"
    sheet.append(XLSX_COLUMNS)
    for row in rows:
        out_row = _xlsx_row(row)
        sheet.append([out_row[column] for column in XLSX_COLUMNS])
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    widths = {
        "A": 12,
        "B": 18,
        "C": 8,
        "D": 10,
        "E": 22,
        "F": 14,
        "G": 70,
        "H": 24,
        "I": 18,
        "J": 24,
        "K": 90,
        "L": 70,
        "M": 20,
        "N": 24,
        "O": 28,
        "P": 24,
        "Q": 90,
    }
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    workbook.save(path)


def _xlsx_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "item_id": str(row.get("item_id") or ""),
        "example_id": str(row.get("example_id") or ""),
        "label": str(row.get("label") if row.get("label") is not None else ""),
        "split": str(row.get("split") or ""),
        "example_role": str(row.get("example_role") or ""),
        "pattern_type": str(row.get("pattern_type") or ""),
        "raw_text": str(row.get("raw_text") or ""),
        "span_segments": format_span_segments(row.get("span_segments") or []),
        "span_key": str(row.get("span_key") or ""),
        "span_text": str(row.get("span_text") or ""),
        "text_a": str(row.get("text_a") or ""),
        "text_b": str(row.get("text_b") or ""),
        "corpus_domain": str(row.get("corpus_domain") or ""),
        "source": str(row.get("source") or ""),
        "source_hit_id": str(row.get("source_hit_id") or ""),
        "detect_rule_ids": _json_cell(row.get("detect_rule_ids")),
        "note": str(row.get("note") or ""),
    }


def _write_csv_debug(path: Path, rows: list[dict[str, Any]]) -> None:
    """Internal helper kept available for future debugging; not used by CLI."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=XLSX_COLUMNS)
        writer.writeheader()
        for row in rows:
            xlsx_row = _xlsx_row(row)
            writer.writerow({key: _csv_cell(value) for key, value in xlsx_row.items()})


def _label_name(label: int) -> str:
    return "positive" if label == 1 else "negative"


def _counter_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted((value, int(count)) for value, count in Counter(str(row.get(key) or "unknown") for row in rows).items()))


def _build_counts_by_item(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["item_id"])].append(row)

    result: dict[str, dict[str, int]] = {}
    for item_id, item_rows in sorted(grouped.items()):
        label_counter = Counter(_label_name(int(row["label"])) for row in item_rows)
        split_counter = Counter(str(row["split"]) for row in item_rows)
        role_counter = Counter(str(row["example_role"]) for row in item_rows)
        result[item_id] = {
            "n_examples": len(item_rows),
            "positive": int(label_counter.get("positive", 0)),
            "negative": int(label_counter.get("negative", 0)),
            "train": int(split_counter.get("train", 0)),
            "dev": int(split_counter.get("dev", 0)),
            "test": int(split_counter.get("test", 0)),
            "pos_conti": int(role_counter.get("pos_conti", 0)),
            "pos_disconti": int(role_counter.get("pos_disconti", 0)),
            "neg_target_absent": int(role_counter.get("neg_target_absent", 0)),
        }
    return result


def _build_summary(
    *,
    input_paths: list[Path],
    rows: list[dict[str, Any]],
    out_jsonl: Path,
    out_xlsx: Path,
) -> dict[str, Any]:
    label_counter = Counter(_label_name(int(row["label"])) for row in rows)
    split_counter = Counter(str(row["split"]) for row in rows)
    role_counter = Counter(str(row["example_role"]) for row in rows)
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "created_at": _now_utc(),
        "n_input_files": len(input_paths),
        "input_files": [str(path) for path in input_paths],
        "out_jsonl": str(out_jsonl),
        "out_xlsx": str(out_xlsx),
        "n_examples": len(rows),
        "item_counts": _counter_by(rows, "item_id"),
        "label_counts": {
            "positive": int(label_counter.get("positive", 0)),
            "negative": int(label_counter.get("negative", 0)),
        },
        "split_counts": {split: int(split_counter.get(split, 0)) for split in ALLOWED_SPLITS},
        "role_counts": {role: int(role_counter.get(role, 0)) for role in ALLOWED_ROLES},
        "counts_by_item": _build_counts_by_item(rows),
        "input_construction_versions": _counter_by(rows, "input_construction_version"),
        "schema_versions": _counter_by(rows, "schema_version"),
        "span_format": "json_list",
        "source_policy": {
            "item_level_jsonl_is_ssot": True,
            "all_files_are_derived": True,
            "manual_append_allowed": False,
            "note": "Do not edit all_encoder_* files manually. Regenerate them from item-level encoder pair JSONL files.",
        },
        "duplicates": {
            "global_example_id_duplicates": 0,
            "item_example_id_duplicates": 0,
            "item_label_raw_text_span_key_duplicates": 0,
        },
    }


def merge_encoder_examples(
    *,
    input_paths: list[Path],
    out_dir: Path,
) -> dict[str, Any]:
    if not input_paths:
        raise ValueError("No input files provided")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "all_encoder_pair_examples.jsonl"
    out_xlsx = out_dir / "all_encoder_examples.xlsx"
    out_summary = out_dir / "all_encoder_examples_summary.json"

    rows = _load_and_validate(input_paths)
    _write_jsonl(out_jsonl, rows)
    _write_xlsx(out_xlsx, rows)
    summary = _build_summary(input_paths=input_paths, rows=rows, out_jsonl=out_jsonl, out_xlsx=out_xlsx)
    _write_json(out_summary, summary)
    return summary


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        action="append",
        dest="inputs",
        help="Item-level encoder pair JSONL. Can be passed multiple times.",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Base artifact folder, e.g. /.../HanTalk_arti/example_making. Required with --discover.",
    )
    parser.add_argument("--discover", action="store_true", help="Discover {artifact_root}/{item_id}/{item_id}_encoder_pair_examples.jsonl files.")
    parser.add_argument("--out-dir", required=True, type=Path, help="Output directory for all_encoder_* aggregate files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        input_paths = _resolve_input_paths(args)
        summary = merge_encoder_examples(input_paths=input_paths, out_dir=args.out_dir.expanduser())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "n_input_files": summary["n_input_files"],
                "n_examples": summary["n_examples"],
                "item_counts": summary["item_counts"],
                "label_counts": summary["label_counts"],
                "split_counts": summary["split_counts"],
                "out_jsonl": summary["out_jsonl"],
                "out_xlsx": summary["out_xlsx"],
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
