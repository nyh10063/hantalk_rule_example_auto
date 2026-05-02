#!/usr/bin/env python3
"""Search a prepared corpus with DetectorEngine and export review files."""

from __future__ import annotations

import argparse
import csv
import json
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
    "raw_text",
    "origin_e_id",
    "unit_id",
    "unit_type",
    "member_e_ids",
    "canonical_form",
    "group",
    "regex_match_span",
    "regex_match_text",
    "span_segments",
    "span_key",
    "span_text",
    "span_source",
    "component_span_status",
    "component_span_enabled",
    "applied_bridge_ids",
    "detect_rule_ids",
    "hard_fail_rule_ids",
    "human_label",
    "span_status",
    "corrected_span_segments",
    "corrected_span_text",
    "memo",
    "reviewer",
]


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
        "applied_bridge_ids": _json_cell(candidate.get("applied_bridge_ids") or []),
        "detect_rule_ids": _json_cell(candidate.get("detect_rule_ids") or []),
        "hard_fail_rule_ids": _json_cell(candidate.get("hard_fail_rule_ids") or []),
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

    with out_jsonl.open("w", encoding="utf-8") as jsonl_f, review_csv.open("w", encoding="utf-8", newline="") as csv_f:
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
    parser.add_argument("--out-jsonl", required=True, type=Path)
    parser.add_argument("--review-csv", required=True, type=Path)
    parser.add_argument("--report-json", required=True, type=Path)
    parser.add_argument("--allow-experimental-polyset", action="store_true")
    parser.add_argument("--include-debug", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = search_corpus(
        bundle_path=args.bundle,
        input_jsonl=args.input_jsonl,
        active_unit_ids=args.active_unit_ids,
        out_jsonl=args.out_jsonl,
        review_csv=args.review_csv,
        report_json=args.report_json,
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
                "report": str(args.report_json),
                "review_csv": str(args.review_csv),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
