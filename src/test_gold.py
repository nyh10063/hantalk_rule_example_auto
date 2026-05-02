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
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from detector.engine import DetectorEngine
    from detector.span_utils import spans_overlap
except ImportError:  # pragma: no cover - supports `python -m src.test_gold`.
    from src.detector.engine import DetectorEngine
    from src.detector.span_utils import spans_overlap


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


def _candidate_matches_item(candidate: dict[str, Any], item_id: str) -> bool:
    return candidate.get("unit_id") == item_id or item_id in (candidate.get("member_e_ids") or [])


def _candidate_exact(candidate: dict[str, Any], spans: list[tuple[int, int, str]]) -> bool:
    candidate_segments = [[int(start), int(end)] for start, end in candidate.get("span_segments") or []]
    gold_segments = [[int(start), int(end)] for start, end, _ in spans]
    return candidate_segments == gold_segments


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
        "eval_mode": "regex_versions",
        "eval_id": str(regex_record.get("regex_version")),
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


def evaluate_detector_bundle(
    *,
    item_id: str,
    engine: DetectorEngine,
    gold_records: list[dict[str, Any]],
    active_unit_ids: list[str],
    bundle_match_policy: str,
) -> dict[str, Any]:
    selected_gold = [r for r in gold_records if r.get("item_id") == item_id]
    fn_records: list[dict[str, Any]] = []
    matched_records: list[dict[str, Any]] = []
    sentence_matched_count = 0
    span_overlap_count = 0
    span_exact_count = 0
    hard_failed_total = 0
    component_span_success_count = 0
    component_span_fallback_count = 0
    component_span_regex_match_count = 0
    span_source_counts: Counter[str] = Counter()

    for record in selected_gold:
        sentence = str(record.get("sentence") or "")
        spans = _target_spans(record)
        detector_result = engine.detect(sentence, active_unit_ids=active_unit_ids, text_id=str(record.get("example_id") or ""))
        candidates = [c for c in detector_result.get("candidates", []) if _candidate_matches_item(c, item_id)]
        rejected_candidates = [
            c for c in detector_result.get("rejected_candidates", []) if _candidate_matches_item(c, item_id)
        ]
        hard_failed_total += len(rejected_candidates)
        for candidate in candidates:
            span_source_counts[str(candidate.get("span_source") or "unknown")] += 1

        sentence_matched = bool(candidates)
        span_overlap = any(
            spans_overlap(candidate.get("span_segments") or [], [[start, end] for start, end, _ in spans])
            for candidate in candidates
        )
        span_exact = any(_candidate_exact(candidate, spans) for candidate in candidates)
        if sentence_matched:
            sentence_matched_count += 1
        if span_overlap:
            span_overlap_count += 1
        if span_exact:
            span_exact_count += 1
        if any(candidate.get("span_source") == "component_spans" for candidate in candidates):
            component_span_success_count += 1
        if any(candidate.get("span_source") == "regex_match_fallback" for candidate in candidates):
            component_span_fallback_count += 1
        if any(candidate.get("span_source") == "regex_match" for candidate in candidates):
            component_span_regex_match_count += 1

        matched = sentence_matched if bundle_match_policy == "sentence" else span_overlap
        row = {
            "item_id": item_id,
            "eval_mode": "detector_bundle",
            "example_id": record.get("example_id"),
            "source_example_id": record.get("source_example_id"),
            "split": record.get("split"),
            "pattern_type": record.get("pattern_type"),
            "gold_example_role": record.get("gold_example_role"),
            "target_text": record.get("target_text"),
            "target_spans": record.get("target_spans"),
            "sentence_matched": sentence_matched,
            "span_overlap": span_overlap,
            "span_exact": span_exact,
            "candidates": candidates,
            "rejected_candidates": rejected_candidates,
            "detector_summary": detector_result.get("summary"),
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
        "eval_mode": "detector_bundle",
        "eval_id": "bundle_" + "_".join(active_unit_ids) + f"_{bundle_match_policy}",
        "bundle_path": engine.bundle_path,
        "active_unit_ids": active_unit_ids,
        "bundle_match_policy": bundle_match_policy,
        "span_source": "detector_candidate_spans",
        "component_span_enabled": component_span_success_count > 0,
        "component_span_success_count": component_span_success_count,
        "component_span_success_rate": component_span_success_count / total if total else 0.0,
        "component_span_fallback_count": component_span_fallback_count,
        "component_span_fallback_rate": component_span_fallback_count / total if total else 0.0,
        "component_span_regex_match_count": component_span_regex_match_count,
        "span_source_counts": dict(sorted(span_source_counts.items())),
        "gold_total": total,
        "gold_matched": matched_count,
        "gold_recall": recall,
        "fn_count": len(fn_records),
        "sentence_matched_count": sentence_matched_count,
        "sentence_recall": sentence_matched_count / total if total else 0.0,
        "span_overlap_count": span_overlap_count,
        "span_overlap_recall": span_overlap_count / total if total else 0.0,
        "span_exact_count": span_exact_count,
        "span_exact_recall": span_exact_count / total if total else 0.0,
        "hard_failed_candidate_count": hard_failed_total,
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
    parser.add_argument("--bundle", type=Path, default=None, help="Detector bundle path for DetectorEngine evaluation.")
    parser.add_argument(
        "--active-unit-id",
        action="append",
        default=None,
        help="Runtime unit id to execute in bundle mode. Repeat to enable multiple units. Default: item id.",
    )
    parser.add_argument(
        "--bundle-match-policy",
        choices=["sentence", "overlap"],
        default="sentence",
        help="Bundle mode pass criterion. sentence uses any candidate for the item; overlap requires candidate/gold span overlap.",
    )
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
        gold_records = _read_jsonl(gold_path)
        if args.bundle:
            active_unit_ids = args.active_unit_id or [item_id]
            engine = DetectorEngine.from_bundle(args.bundle)
            result = evaluate_detector_bundle(
                item_id=item_id,
                engine=engine,
                gold_records=gold_records,
                active_unit_ids=active_unit_ids,
                bundle_match_policy=args.bundle_match_policy,
            )
        else:
            regex_records = _read_jsonl(versions_path)
            regex_record = _select_regex_version(regex_records, item_id, args.regex_version)
            result = evaluate(
                item_id=item_id,
                regex_record=regex_record,
                gold_records=gold_records,
                match_policy=args.match_policy,
            )
    except Exception as exc:  # noqa: BLE001 - CLI should print friendly error.
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    eval_id = result["eval_id"]
    report_path = args.report or Path("logs") / f"{item_id}_gold_eval_{eval_id}.json"
    fn_report_path = args.fn_report or Path("logs") / f"{item_id}_fn_report_{eval_id}.jsonl"

    fn_records = result.pop("fn_records")
    _write_json(report_path, result)
    _write_jsonl(fn_report_path, fn_records)

    print(f"eval_mode={result['eval_mode']}")
    print(f"item_id={result['item_id']}")
    if result["eval_mode"] == "regex_versions":
        print(f"regex_version={result['regex_version']}")
        print(f"match_policy={result['match_policy']}")
    else:
        print(f"bundle={result['bundle_path']}")
        print(f"active_unit_ids={','.join(result['active_unit_ids'])}")
        print(f"bundle_match_policy={result['bundle_match_policy']}")
    print(f"gold_total={result['gold_total']}")
    print(f"gold_matched={result['gold_matched']}")
    print(f"gold_recall={result['gold_recall']:.6f}")
    if result["eval_mode"] == "detector_bundle":
        print(f"sentence_recall={result['sentence_recall']:.6f}")
        print(f"span_overlap_recall={result['span_overlap_recall']:.6f}")
        print(f"span_exact_recall={result['span_exact_recall']:.6f}")
        print(f"component_span_success_count={result['component_span_success_count']}")
        print(f"component_span_fallback_count={result['component_span_fallback_count']}")
        print(f"span_source_counts={json.dumps(result['span_source_counts'], ensure_ascii=False)}")
        print(f"hard_failed_candidate_count={result['hard_failed_candidate_count']}")
    print(f"fn_count={result['fn_count']}")
    print(f"report={report_path}")
    print(f"fn_report={fn_report_path}")

    if args.fail_on_fn and fn_records:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
