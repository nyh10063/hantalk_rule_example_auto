#!/usr/bin/env python3
"""Run one corpus-search review batch for a validated detector unit.

This orchestrator intentionally does not export detector bundles. The human
managed dict Excel remains the source for bundles, and bundle export/gold
validation should stay explicit before corpus search automation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .apply_first_pass_review import apply_first_pass_review
    from .detector.engine import DetectorEngine
    from .prepare_codex_review import prepare_codex_review
    from .prepare_example_corpus import prepare_corpus
    from .search_corpus import search_corpus
    from .test_gold import evaluate_detector_bundle
except ImportError:  # pragma: no cover - supports direct script execution.
    from apply_first_pass_review import apply_first_pass_review
    from detector.engine import DetectorEngine
    from prepare_codex_review import prepare_codex_review
    from prepare_example_corpus import prepare_corpus
    from search_corpus import search_corpus
    from test_gold import evaluate_detector_bundle


SCHEMA_VERSION = "hantalk_corpus_review_batch_run_v1"
GOLD_BUNDLE_MATCH_POLICY = "overlap"


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return records


def _batch_id_from_manifest(manifest_path: Path, batch_index: int) -> str:
    manifest = _load_json(manifest_path)
    prefix = str(manifest.get("batch_id_prefix") or "example_making")
    return f"{prefix}_batch_{batch_index:03d}"


def _output_paths(*, artifact_root: Path, unit_id: str, batch_label: str) -> dict[str, Path]:
    item_dir = artifact_root / unit_id
    return {
        "item_dir": item_dir,
        "detection_jsonl": item_dir / f"{unit_id}_{batch_label}_detection.jsonl",
        "human_review_csv": item_dir / f"{unit_id}_{batch_label}_human_review.csv",
        "search_report_json": item_dir / f"{unit_id}_{batch_label}_search_report.json",
        "codex_review_csv": item_dir / f"{unit_id}_{batch_label}_codex_review.csv",
        "codex_review_xlsx": item_dir / f"{unit_id}_{batch_label}_codex_review.xlsx",
        "codex_review_report_json": item_dir / f"{unit_id}_{batch_label}_codex_review_report.json",
        "first_pass_csv": item_dir / f"{unit_id}_{batch_label}_codex_review_first_pass.csv",
        "first_pass_xlsx": item_dir / f"{unit_id}_{batch_label}_codex_review_first_pass.xlsx",
        "first_pass_report_json": item_dir / f"{unit_id}_{batch_label}_codex_review_first_pass_report.json",
        "run_report_json": item_dir / f"{unit_id}_{batch_label}_run_report.json",
    }


def _prepared_paths(*, prepared_root: Path, batch_id: str) -> dict[str, Path]:
    return {
        "prepared_jsonl": prepared_root / f"{batch_id}.jsonl",
        "prepared_report_json": prepared_root / f"{batch_id}_report.json",
    }


def _ensure_input_file(path: Path, *, label: str, hint: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}. {hint}")
    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")


def _guard_outputs(paths: dict[str, Path], *, overwrite: bool) -> None:
    checked_keys = [
        "detection_jsonl",
        "human_review_csv",
        "search_report_json",
        "codex_review_csv",
        "codex_review_xlsx",
        "codex_review_report_json",
        "first_pass_csv",
        "first_pass_xlsx",
        "first_pass_report_json",
        "run_report_json",
    ]
    if overwrite:
        for key in checked_keys:
            path = paths[key]
            if path.exists():
                if not path.is_file():
                    raise FileExistsError(f"Cannot overwrite non-file output path: {path}")
                path.unlink()
        return
    existing = [paths[key] for key in checked_keys if paths[key].exists()]
    if existing:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Output file(s) already exist. Use --overwrite to regenerate:\n{formatted}")


def _new_report(
    *,
    unit_id: str,
    batch_index: int,
    batch_id: str,
    args: argparse.Namespace,
    prepared_jsonl: Path,
    prepared_report_json: Path,
    outputs: dict[str, Path],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "unit_id": unit_id,
        "batch_index": batch_index,
        "batch_id": batch_id,
        "created_at": _now_utc(),
        "inputs": {
            "gold": str(args.gold),
            "bundle": str(args.bundle),
            "manifest": str(args.manifest),
            "corpus_root": str(args.corpus_root),
            "prepared_jsonl": str(prepared_jsonl),
            "prepared_report_json": str(prepared_report_json),
            "allow_polyset": bool(args.allow_polyset),
        },
        "steps": {
            "gold_gate": {"status": "pending"},
            "prepare_corpus": {"status": "pending"},
            "search_corpus": {"status": "pending"},
            "prepare_codex_review": {"status": "pending"},
            "first_pass_review": {"status": "pending"},
        },
        "gold_gate": None,
        "prepare_corpus_summary": None,
        "search_summary": None,
        "codex_review_summary": None,
        "first_pass_review_summary": None,
        "outputs": {
            "detection_jsonl": str(outputs["detection_jsonl"]),
            "human_review_csv": str(outputs["human_review_csv"]),
            "search_report_json": str(outputs["search_report_json"]),
            "codex_review_csv": str(outputs["codex_review_csv"]),
            "codex_review_xlsx": str(outputs["codex_review_xlsx"]),
            "codex_review_report_json": str(outputs["codex_review_report_json"]),
            "first_pass_csv": str(outputs["first_pass_csv"]),
            "first_pass_xlsx": str(outputs["first_pass_xlsx"]),
            "first_pass_report_json": str(outputs["first_pass_report_json"]),
            "run_report_json": str(outputs["run_report_json"]),
        },
        "review_workflow": {
            "base_codex_review_file": str(outputs["codex_review_xlsx"]),
            "human_working_file": str(outputs["first_pass_xlsx"]),
            "human_working_file_policy": (
                "Use *_codex_review_first_pass.xlsx/csv as the human working file when generated. "
                "It preserves the base codex_review columns and places Codex first-pass columns after regex_match_text. "
                "If no first-pass profile exists, the run is not failed; labels remain blank/no-profile for manual review."
            ),
        },
        "status": "running",
        "failure_reason": None,
    }


def _gold_gate(
    *,
    unit_id: str,
    gold_path: Path,
    bundle_path: Path,
    allow_polyset: bool,
) -> dict[str, Any]:
    gold_records = _read_jsonl(gold_path)
    engine = DetectorEngine.from_bundle(bundle_path)
    result = evaluate_detector_bundle(
        item_id=unit_id,
        engine=engine,
        gold_records=gold_records,
        active_unit_ids=[unit_id],
        bundle_match_policy=GOLD_BUNDLE_MATCH_POLICY,
        allow_polyset=allow_polyset,
    )
    fn_records = result.pop("fn_records", [])
    result["fn_records_preview"] = fn_records[:20]
    result["fn_records_preview_truncated"] = len(fn_records) > 20
    return result


def _is_gold_gate_ok(gold_result: dict[str, Any]) -> bool:
    return float(gold_result.get("gold_recall") or 0.0) >= 1.0 and int(gold_result.get("fn_count") or 0) == 0


def run_corpus_review_batch(args: argparse.Namespace) -> dict[str, Any]:
    unit_id = str(args.unit_id).strip()
    if not unit_id:
        raise ValueError("--unit-id must not be blank")
    if args.batch_index < 0:
        raise ValueError("--batch-index must be >= 0")

    _ensure_input_file(
        args.gold,
        label="gold JSONL",
        hint="Run src.export_gold first, then rerun this corpus review batch.",
    )
    _ensure_input_file(
        args.bundle,
        label="detector bundle",
        hint="Run src.detector.export_bundle first and confirm warnings/gold recall before corpus search.",
    )
    _ensure_input_file(args.manifest, label="corpus manifest", hint="Pass configs/corpus/example_making_manifest.json.")
    if not args.corpus_root.exists():
        raise FileNotFoundError(f"corpus root not found: {args.corpus_root}")

    batch_id = _batch_id_from_manifest(args.manifest, args.batch_index)
    batch_label = f"batch_{args.batch_index:03d}"
    prepared = _prepared_paths(prepared_root=args.prepared_root, batch_id=batch_id)
    outputs = _output_paths(artifact_root=args.artifact_root, unit_id=unit_id, batch_label=batch_label)
    outputs["item_dir"].mkdir(parents=True, exist_ok=True)
    _guard_outputs(outputs, overwrite=args.overwrite)

    report = _new_report(
        unit_id=unit_id,
        batch_index=args.batch_index,
        batch_id=batch_id,
        args=args,
        prepared_jsonl=prepared["prepared_jsonl"],
        prepared_report_json=prepared["prepared_report_json"],
        outputs=outputs,
    )

    try:
        gold_result = _gold_gate(
            unit_id=unit_id,
            gold_path=args.gold,
            bundle_path=args.bundle,
            allow_polyset=args.allow_polyset,
        )
        report["gold_gate"] = {
            "bundle_match_policy": GOLD_BUNDLE_MATCH_POLICY,
            "gold_total": gold_result.get("gold_total"),
            "gold_matched": gold_result.get("gold_matched"),
            "gold_recall": gold_result.get("gold_recall"),
            "fn_count": gold_result.get("fn_count"),
            "sentence_recall": gold_result.get("sentence_recall"),
            "span_overlap_recall": gold_result.get("span_overlap_recall"),
            "span_exact_recall": gold_result.get("span_exact_recall"),
            "component_span_success_count": gold_result.get("component_span_success_count"),
            "component_span_fallback_count": gold_result.get("component_span_fallback_count"),
            "span_source_counts": gold_result.get("span_source_counts"),
            "fn_records_preview": gold_result.get("fn_records_preview"),
            "fn_records_preview_truncated": gold_result.get("fn_records_preview_truncated"),
        }
        if not _is_gold_gate_ok(gold_result):
            report["steps"]["gold_gate"] = {"status": "failed"}
            report["status"] = "blocked"
            report["failure_reason"] = "gold_recall_fix_required"
            return report
        report["steps"]["gold_gate"] = {"status": "ok"}

        if prepared["prepared_jsonl"].exists():
            report["steps"]["prepare_corpus"] = {
                "status": "skipped_existing",
                "prepared_jsonl": str(prepared["prepared_jsonl"]),
                "prepared_report_json": str(prepared["prepared_report_json"]),
            }
            if prepared["prepared_report_json"].exists():
                report["prepare_corpus_summary"] = _load_json(prepared["prepared_report_json"])
        else:
            corpus_report = prepare_corpus(
                manifest_path=args.manifest,
                corpus_root=args.corpus_root,
                batch_index=args.batch_index,
                out_path=prepared["prepared_jsonl"],
                report_path=prepared["prepared_report_json"],
                seed_override=args.seed,
            )
            report["steps"]["prepare_corpus"] = {
                "status": "ok",
                "prepared_jsonl": str(prepared["prepared_jsonl"]),
                "prepared_report_json": str(prepared["prepared_report_json"]),
            }
            report["prepare_corpus_summary"] = corpus_report

        search_report = search_corpus(
            bundle_path=args.bundle,
            input_jsonl=prepared["prepared_jsonl"],
            active_unit_ids=[unit_id],
            out_jsonl=outputs["detection_jsonl"],
            review_csv=outputs["human_review_csv"],
            report_json=outputs["search_report_json"],
            allow_polyset=args.allow_polyset,
            include_debug=args.include_debug,
        )
        report["steps"]["search_corpus"] = {"status": "ok"}
        report["search_summary"] = {
            "n_input_texts": search_report.get("n_input_texts"),
            "n_input_by_domain": search_report.get("n_input_by_domain"),
            "n_texts_with_hits": search_report.get("n_texts_with_hits"),
            "n_texts_with_hits_by_domain": search_report.get("n_texts_with_hits_by_domain"),
            "n_candidates": search_report.get("n_candidates"),
            "n_candidates_by_domain": search_report.get("n_candidates_by_domain"),
            "n_candidates_by_unit_id": search_report.get("n_candidates_by_unit_id"),
            "span_source_counts": search_report.get("span_source_counts"),
            "component_span_status_counts": search_report.get("component_span_status_counts"),
            "elapsed_sec": search_report.get("elapsed_sec"),
        }

        if int(search_report.get("n_candidates") or 0) == 0:
            report["steps"]["prepare_codex_review"] = {
                "status": "skipped_no_candidates",
                "note": "human_review.csv was created with headers only; there are no candidates to inspect.",
            }
            report["codex_review_summary"] = None
            report["steps"]["first_pass_review"] = {
                "status": "skipped_no_candidates",
                "note": "No candidates, so first-pass review files were not generated.",
            }
            report["first_pass_review_summary"] = None
        else:
            codex_report = prepare_codex_review(
                item_id=unit_id,
                input_path=outputs["human_review_csv"],
                out_csv=outputs["codex_review_csv"],
                out_xlsx=outputs["codex_review_xlsx"],
                report_json=outputs["codex_review_report_json"],
            )
            report["steps"]["prepare_codex_review"] = {"status": "ok"}
            report["codex_review_summary"] = {
                "n_rows": codex_report.get("n_rows"),
                "span_parse_counts": codex_report.get("span_parse_counts"),
                "span_source_counts": codex_report.get("span_source_counts"),
                "component_span_status_counts": codex_report.get("component_span_status_counts"),
                "existing_human_label_counts": codex_report.get("existing_human_label_counts"),
            }
            first_pass_report = apply_first_pass_review(
                item_id=unit_id,
                input_path=outputs["codex_review_csv"],
                out_csv=outputs["first_pass_csv"],
                out_xlsx=outputs["first_pass_xlsx"],
                report_json=outputs["first_pass_report_json"],
            )
            profile_status = str(first_pass_report.get("profile_status") or "")
            if profile_status == "missing":
                report["steps"]["first_pass_review"] = {
                    "status": "skipped_no_profile",
                    "note": (
                        "First-pass files were generated, but no advisory profile exists for this unit. "
                        "Use the first-pass file as a manual review template; human_label/span_status remain final."
                    ),
                }
            else:
                report["steps"]["first_pass_review"] = {"status": "ok"}
            report["first_pass_review_summary"] = {
                "profile_id": first_pass_report.get("profile_id"),
                "profile_status": first_pass_report.get("profile_status"),
                "profile_source": first_pass_report.get("profile_source"),
                "advisory_labels_applied": first_pass_report.get("advisory_labels_applied"),
                "n_rows": first_pass_report.get("n_rows"),
                "codex_review_label_counts": first_pass_report.get("codex_review_label_counts"),
                "codex_review_span_status_counts": first_pass_report.get("codex_review_span_status_counts"),
                "codex_review_reason_counts": first_pass_report.get("codex_review_reason_counts"),
                "column_policy": first_pass_report.get("column_policy"),
                "human_working_file": str(outputs["first_pass_xlsx"]),
                "human_label_columns_modified": (first_pass_report.get("policy") or {}).get(
                    "human_label_columns_modified"
                ),
            }

        report["status"] = "ok"
        report["failure_reason"] = None
        return report
    except Exception as exc:
        report["status"] = "failed"
        report["failure_reason"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_at"] = _now_utc()
        _write_json(outputs["run_report_json"], report)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--unit-id",
        required=True,
        help="Detector runtime unit to search, e.g. df003 or ps_ce002.",
    )
    parser.add_argument(
        "--gold",
        required=True,
        type=Path,
        help="Exported gold JSONL path. Must already exist; run src.export_gold first.",
    )
    parser.add_argument(
        "--bundle",
        required=True,
        type=Path,
        help="Detector bundle path. Must already exist; run src.detector.export_bundle first.",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Corpus manifest JSON, e.g. configs/corpus/example_making_manifest.json.",
    )
    parser.add_argument(
        "--corpus-root",
        required=True,
        type=Path,
        help="Folder containing the prepared source corpus text files referenced by the manifest.",
    )
    parser.add_argument(
        "--prepared-root",
        required=True,
        type=Path,
        help="Folder for shared prepared corpus batches. Existing batch JSONL is reused.",
    )
    parser.add_argument(
        "--artifact-root",
        required=True,
        type=Path,
        help="Artifact root for unit-specific outputs, e.g. /.../HanTalk_arti/example_making.",
    )
    parser.add_argument(
        "--batch-index",
        required=True,
        type=int,
        help="Prepared corpus batch index to search, e.g. 2 for batch_002.",
    )
    parser.add_argument(
        "--allow-polyset",
        action="store_true",
        help="Allow ps_id polyset runtime units. Required for units such as ps_ce002.",
    )
    parser.add_argument(
        "--include-debug",
        action="store_true",
        help="Include detector debug details in underlying search results. Keep off by default.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate unit-specific output files if they already exist.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Override manifest seed when preparing a missing corpus batch.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = run_corpus_review_batch(args)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "unit_id": report["unit_id"],
                "batch_index": report["batch_index"],
                "status": report["status"],
                "failure_reason": report.get("failure_reason"),
                "gold_recall": (report.get("gold_gate") or {}).get("gold_recall"),
                "fn_count": (report.get("gold_gate") or {}).get("fn_count"),
                "n_candidates": (report.get("search_summary") or {}).get("n_candidates"),
                "human_review_csv": report["outputs"]["human_review_csv"],
                "codex_review_xlsx": report["outputs"]["codex_review_xlsx"],
                "first_pass_xlsx": report["outputs"]["first_pass_xlsx"],
                "run_report_json": report["outputs"]["run_report_json"],
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
