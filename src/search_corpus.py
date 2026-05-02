#!/usr/bin/env python3
"""Search a prepared corpus with DetectorEngine and export review files."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .detector.engine import DetectorEngine
except ImportError:  # pragma: no cover - supports direct script execution.
    from detector.engine import DetectorEngine

REVIEW_COLUMNS = [
    "hit_id",
    "candidate_index",
    "batch_id",
    "text_id",
    "corpus_domain",
    "source",
    "source_file",
    "source_row_index",
    "source_line_no",
    "origin_e_id",
    "unit_id",
    "unit_type",
    "member_e_ids",
    "canonical_form",
    "group",
    "regex_match_span",
    "raw_text",
    "regex_match_text",
    "human_label",
    "span_segments",
    "span_key",
    "span_text",
    "span_source",
    "component_span_status",
    "component_span_enabled",
    "partial_span_text",
    "matched_component_ids",
    "missing_required_component_ids",
    "partial_component_spans",
    "partial_span_segments",
    "applied_bridge_ids",
    "detect_rule_ids",
    "hard_fail_rule_ids",
    "llm_temp_label",
    "llm_note",
    "span_status",
    "corrected_span_segments",
    "corrected_span_text",
    "memo",
    "reviewer",
]

BATCH_ID_RE = re.compile(r"(batch_\d+)")


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def _json_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict, bool, int, float)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return str(value)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} invalid JSONL") from exc
    return records


def _derive_batch_id(input_jsonl: Path, explicit_batch_id: str | None = None) -> str:
    if explicit_batch_id is not None:
        batch_id = explicit_batch_id.strip()
        if not batch_id:
            raise ValueError("--batch-id must not be blank")
        return batch_id
    match = BATCH_ID_RE.search(input_jsonl.stem)
    if match:
        return match.group(1)
    return input_jsonl.stem


def _resolve_output_paths(
    *,
    active_unit_ids: list[str],
    input_jsonl: Path,
    artifact_root: Path | None,
    batch_id: str | None,
    out_jsonl: Path | None,
    review_csv: Path | None,
    report_json: Path | None,
) -> tuple[Path, Path, Path]:
    if out_jsonl and review_csv and report_json:
        return out_jsonl, review_csv, report_json
    if artifact_root is None:
        missing = [
            name
            for name, value in [
                ("--out-jsonl", out_jsonl),
                ("--review-csv", review_csv),
                ("--report-json", report_json),
            ]
            if value is None
        ]
        raise ValueError(
            f"Missing output path(s): {', '.join(missing)}. "
            "Pass them explicitly or use --artifact-root to derive item-specific paths."
        )
    if len(active_unit_ids) != 1:
        raise ValueError(
            "Automatic item-specific output paths require exactly one --active-unit-id. "
            "Pass explicit output paths for multi-item search."
        )

    item_id = active_unit_ids[0]
    batch_label = _derive_batch_id(input_jsonl, batch_id)
    item_dir = artifact_root / item_id
    return (
        out_jsonl or item_dir / f"{item_id}_{batch_label}_detection.jsonl",
        review_csv or item_dir / f"{item_id}_{batch_label}_human_review.csv",
        report_json or item_dir / f"{item_id}_{batch_label}_search_report.json",
    )


def _review_row(
    *,
    hit_id: str,
    candidate_index: int,
    record: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, str]:
    row = {
        "hit_id": hit_id,
        "candidate_index": str(candidate_index),
        "batch_id": str(record.get("batch_id") or ""),
        "text_id": str(record.get("text_id") or ""),
        "corpus_domain": str(record.get("corpus_domain") or ""),
        "source": str(record.get("source") or ""),
        "source_file": str(record.get("source_file") or ""),
        "source_row_index": str(record.get("source_row_index") if record.get("source_row_index") is not None else ""),
        "source_line_no": str(record.get("source_line_no") if record.get("source_line_no") is not None else ""),
        "raw_text": str(record.get("raw_text") or ""),
        "origin_e_id": str(candidate.get("origin_e_id") or ""),
        "unit_id": str(candidate.get("unit_id") or ""),
        "unit_type": str(candidate.get("unit_type") or ""),
        "member_e_ids": _json_cell(candidate.get("member_e_ids") or []),
        "canonical_form": str(candidate.get("canonical_form") or ""),
        "group": str(candidate.get("group") or ""),
        "regex_match_span": _json_cell(candidate.get("regex_match_span") or []),
        "regex_match_text": str(candidate.get("regex_match_text") or ""),
        "span_segments": _json_cell(candidate.get("span_segments") or []),
        "span_key": str(candidate.get("span_key") or ""),
        "span_text": str(candidate.get("span_text") or ""),
        "span_source": str(candidate.get("span_source") or ""),
        "component_span_status": str(candidate.get("component_span_status") or ""),
        "component_span_enabled": _json_cell(candidate.get("component_span_enabled")),
        "partial_span_text": str(candidate.get("partial_span_text") or ""),
        "matched_component_ids": _json_cell(candidate.get("matched_component_ids") or []),
        "missing_required_component_ids": _json_cell(candidate.get("missing_required_component_ids") or []),
        "partial_component_spans": _json_cell(candidate.get("partial_component_spans") or {}),
        "partial_span_segments": _json_cell(candidate.get("partial_span_segments") or []),
        "applied_bridge_ids": _json_cell(candidate.get("applied_bridge_ids") or []),
        "detect_rule_ids": _json_cell(candidate.get("detect_rule_ids") or []),
        "hard_fail_rule_ids": _json_cell(candidate.get("hard_fail_rule_ids") or []),
        "llm_temp_label": "",
        "llm_note": "",
        "human_label": "",
        "span_status": "",
        "corrected_span_segments": "",
        "corrected_span_text": "",
        "memo": "",
        "reviewer": "",
    }
    return {column: row.get(column, "") for column in REVIEW_COLUMNS}


def search_corpus(
    *,
    bundle_path: Path,
    input_jsonl: Path,
    active_unit_ids: list[str],
    out_jsonl: Path,
    review_csv: Path,
    report_json: Path,
    allow_experimental_polyset: bool = False,
    include_debug: bool = False,
) -> dict[str, Any]:
    if not active_unit_ids:
        raise ValueError("At least one --active-unit-id is required")

    start_time = time.perf_counter()
    engine = DetectorEngine.from_bundle(bundle_path)
    records = _read_jsonl(input_jsonl)

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    review_csv.parent.mkdir(parents=True, exist_ok=True)

    n_texts_with_hits = 0
    n_candidates = 0
    candidates_by_domain: Counter[str] = Counter()
    candidates_by_unit_id: Counter[str] = Counter()
    span_source_counts: Counter[str] = Counter()
    component_status_counts: Counter[str] = Counter()
    input_by_domain: Counter[str] = Counter()
    text_hit_by_domain: Counter[str] = Counter()
    detector_summary_totals: Counter[str] = Counter()

    with out_jsonl.open("w", encoding="utf-8") as jsonl_f, review_csv.open("w", encoding="utf-8-sig", newline="") as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()

        for record in records:
            raw_text = str(record.get("raw_text") or "")
            domain = str(record.get("corpus_domain") or "unknown")
            input_by_domain[domain] += 1
            result = engine.detect(
                raw_text,
                active_unit_ids=active_unit_ids,
                allow_experimental_polyset=allow_experimental_polyset,
                text_id=str(record.get("text_id") or ""),
                include_debug=include_debug,
            )
            candidates = result.get("candidates") or []
            summary = result.get("summary") or {}
            for key in [
                "n_detect_matches",
                "n_candidates_before_verify",
                "n_candidates_after_verify",
                "n_candidates_hard_failed",
                "n_matches_truncated",
                "n_component_span_success",
                "n_component_span_fallback",
                "n_component_span_regex_only",
            ]:
                detector_summary_totals[key] += int(summary.get(key) or 0)

            if not candidates:
                continue

            n_texts_with_hits += 1
            text_hit_by_domain[domain] += 1
            detection_record = {
                "schema_version": "hantalk_corpus_detection_v1",
                "text_id": record.get("text_id"),
                "batch_id": record.get("batch_id"),
                "batch_index": record.get("batch_index"),
                "corpus_domain": record.get("corpus_domain"),
                "source": record.get("source"),
                "source_file": record.get("source_file"),
                "source_row_index": record.get("source_row_index"),
                "source_line_no": record.get("source_line_no"),
                "raw_text": raw_text,
                "active_unit_ids": active_unit_ids,
                "detector_summary": summary,
                "candidates": candidates,
            }
            jsonl_f.write(json.dumps(detection_record, ensure_ascii=False, allow_nan=False) + "\n")

            for candidate_index, candidate in enumerate(candidates, start=1):
                n_candidates += 1
                unit_id = str(candidate.get("unit_id") or "unknown")
                span_source = str(candidate.get("span_source") or "unknown")
                component_status = str(candidate.get("component_span_status") or "unknown")
                candidates_by_domain[domain] += 1
                candidates_by_unit_id[unit_id] += 1
                span_source_counts[span_source] += 1
                component_status_counts[component_status] += 1
                hit_id = f"{record.get('text_id')}-cand{candidate_index:02d}"
                writer.writerow(
                    _review_row(
                        hit_id=hit_id,
                        candidate_index=candidate_index,
                        record=record,
                        candidate=candidate,
                    )
                )

    elapsed_sec = time.perf_counter() - start_time
    report = {
        "schema_version": "hantalk_corpus_search_report_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bundle_path": str(bundle_path),
        "input_jsonl": str(input_jsonl),
        "out_jsonl": str(out_jsonl),
        "review_csv": str(review_csv),
        "active_unit_ids": active_unit_ids,
        "n_input_texts": len(records),
        "n_input_by_domain": dict(sorted(input_by_domain.items())),
        "n_texts_with_hits": n_texts_with_hits,
        "n_texts_with_hits_by_domain": dict(sorted(text_hit_by_domain.items())),
        "n_candidates": n_candidates,
        "n_candidates_by_domain": dict(sorted(candidates_by_domain.items())),
        "n_candidates_by_unit_id": dict(sorted(candidates_by_unit_id.items())),
        "span_source_counts": dict(sorted(span_source_counts.items())),
        "component_span_status_counts": dict(sorted(component_status_counts.items())),
        "n_component_span_success": int(span_source_counts.get("component_spans", 0)),
        "n_component_span_fallback": int(span_source_counts.get("regex_match_fallback", 0)),
        "n_component_span_regex_only": int(span_source_counts.get("regex_match", 0)),
        "detector_summary_totals": dict(sorted(detector_summary_totals.items())),
        "elapsed_sec": elapsed_sec,
    }
    _write_json(report_json, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--input-jsonl", required=True, type=Path)
    parser.add_argument("--active-unit-id", action="append", dest="active_unit_ids", required=True)
    parser.add_argument("--out-jsonl", type=Path)
    parser.add_argument("--review-csv", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="Base artifact folder, e.g. /.../HanTalk_arti/example_making. Missing output paths are written under {artifact_root}/{item_id}/.",
    )
    parser.add_argument(
        "--batch-id",
        help="Batch label for derived filenames. Defaults to the first batch_### token in --input-jsonl.",
    )
    parser.add_argument("--allow-experimental-polyset", action="store_true")
    parser.add_argument("--include-debug", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        out_jsonl, review_csv, report_json = _resolve_output_paths(
            active_unit_ids=args.active_unit_ids,
            input_jsonl=args.input_jsonl,
            artifact_root=args.artifact_root,
            batch_id=args.batch_id,
            out_jsonl=args.out_jsonl,
            review_csv=args.review_csv,
            report_json=args.report_json,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    report = search_corpus(
        bundle_path=args.bundle,
        input_jsonl=args.input_jsonl,
        active_unit_ids=args.active_unit_ids,
        out_jsonl=out_jsonl,
        review_csv=review_csv,
        report_json=report_json,
        allow_experimental_polyset=args.allow_experimental_polyset,
        include_debug=args.include_debug,
    )
    print(
        json.dumps(
            {
                "n_input_texts": report["n_input_texts"],
                "n_texts_with_hits": report["n_texts_with_hits"],
                "n_candidates": report["n_candidates"],
                "n_candidates_by_domain": report["n_candidates_by_domain"],
                "span_source_counts": report["span_source_counts"],
                "report": str(report_json),
                "review_csv": str(review_csv),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
