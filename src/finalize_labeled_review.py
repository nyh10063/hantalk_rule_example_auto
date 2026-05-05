#!/usr/bin/env python3
"""Finalize human-labeled review files into review summary and encoder examples.

This wrapper does not edit dict/rules/bundles. It only runs the final
human-label summary and encoder-example export steps for already labeled review
files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .export_encoder_examples import export_encoder_examples
    from .summarize_review import summarize_reviews
except ImportError:  # pragma: no cover - supports direct script execution.
    from export_encoder_examples import export_encoder_examples
    from summarize_review import summarize_reviews


SCHEMA_VERSION = "hantalk_finalize_labeled_review_report_v1"
EXPORT_ALLOWED_ACTIONS = {"ready_for_encoder_export", "continue_batch_search", "max_batches_reached"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _ensure_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")


def _default_paths(*, item_id: str, artifact_root: Path) -> dict[str, Path]:
    item_dir = artifact_root / item_id
    return {
        "item_dir": item_dir,
        "review_summary": item_dir / f"{item_id}_review_summary.json",
        "encoder_xlsx": item_dir / f"{item_id}_encoder_examples.xlsx",
        "encoder_jsonl": item_dir / f"{item_id}_encoder_pair_examples.jsonl",
        "encoder_summary": item_dir / f"{item_id}_encoder_examples_summary.json",
        "finalize_report": item_dir / f"{item_id}_finalize_labeled_review_report.json",
    }


def _guard_outputs(paths: dict[str, Path], *, overwrite: bool) -> None:
    output_keys = [
        "review_summary",
        "encoder_xlsx",
        "encoder_jsonl",
        "encoder_summary",
        "finalize_report",
    ]
    existing = [paths[key] for key in output_keys if paths[key].exists()]
    if existing and not overwrite:
        formatted = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(f"Output file(s) already exist. Use --overwrite to regenerate:\n{formatted}")
    if overwrite:
        for path in existing:
            if not path.is_file():
                raise FileExistsError(f"Cannot overwrite non-file output path: {path}")
            path.unlink()


def _next_step_hint(*, export_ran: bool, cleanup_blocked: bool, encoder_summary: dict[str, Any] | None) -> str:
    if cleanup_blocked:
        return "Fix human_label/span_status cleanup issues, then rerun finalize_labeled_review."
    if not export_ran:
        return "Export did not run. Inspect finalize report and rerun when ready."
    if encoder_summary and not encoder_summary.get("ready_for_training"):
        return "Encoder examples exported, but targets are not complete. Add supplemental labeled inputs and rerun export/finalize."
    return "Encoder examples exported and target counts are ready for later aggregate merge/training."


def finalize_labeled_review(
    *,
    item_id: str,
    bundle_path: Path,
    input_paths: list[Path],
    artifact_root: Path,
    target_pos: int,
    target_neg: int,
    max_batches: int,
    fp_tp_ratio_threshold: float,
    seed: int,
    overwrite: bool,
    allow_cleanup_export: bool,
    require_text_id: bool,
) -> dict[str, Any]:
    item_id = item_id.strip()
    if not item_id:
        raise ValueError("--item-id must not be blank")
    _ensure_file(bundle_path, label="bundle")
    if not input_paths:
        raise ValueError("At least one --input is required")
    for input_path in input_paths:
        _ensure_file(input_path, label="labeled review input")
    if target_pos < 0:
        raise ValueError("--target-pos must be >= 0")
    if target_neg < 0:
        raise ValueError("--target-neg must be >= 0")
    if max_batches <= 0:
        raise ValueError("--max-batches must be > 0")
    if fp_tp_ratio_threshold <= 0:
        raise ValueError("--fp-tp-ratio-threshold must be > 0")

    paths = _default_paths(item_id=item_id, artifact_root=artifact_root)
    paths["item_dir"].mkdir(parents=True, exist_ok=True)
    _guard_outputs(paths, overwrite=overwrite)

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "item_id": item_id,
        "created_at": _now_utc(),
        "input_files": [str(path) for path in input_paths],
        "bundle": str(bundle_path),
        "artifact_root": str(artifact_root),
        "outputs": {
            "review_summary": str(paths["review_summary"]),
            "encoder_jsonl": str(paths["encoder_jsonl"]),
            "encoder_xlsx": str(paths["encoder_xlsx"]),
            "encoder_summary": str(paths["encoder_summary"]),
            "finalize_report": str(paths["finalize_report"]),
        },
        "parameters": {
            "target_pos": target_pos,
            "target_neg": target_neg,
            "max_processed_batches": max_batches,
            "fp_tp_ratio_threshold": fp_tp_ratio_threshold,
            "seed": seed,
            "allow_cleanup_export": allow_cleanup_export,
            "require_text_id": require_text_id,
        },
        "summary_next_action": None,
        "cleanup_blocked": False,
        "cleanup_export_overridden": False,
        "export_ran": False,
        "summary": None,
        "encoder_summary": None,
        "status": "running",
        "failure_reason": None,
    }

    try:
        review_summary = summarize_reviews(
            item_id=item_id,
            input_paths=input_paths,
            out_path=paths["review_summary"],
            target_pos=target_pos,
            target_neg=target_neg,
            max_batches=max_batches,
            fp_tp_ratio_threshold=fp_tp_ratio_threshold,
        )
        next_action = str(review_summary.get("next_action") or "")
        cleanup_blocked = next_action == "needs_label_cleanup" and not allow_cleanup_export
        export_allowed = next_action in EXPORT_ALLOWED_ACTIONS or allow_cleanup_export

        report["summary_next_action"] = next_action
        report["cleanup_blocked"] = cleanup_blocked
        report["cleanup_export_overridden"] = next_action == "needs_label_cleanup" and allow_cleanup_export
        report["summary"] = {
            "n_rows": review_summary.get("n_rows"),
            "label_counts": review_summary.get("label_counts"),
            "span_status_counts": review_summary.get("span_status_counts"),
            "target_reached": review_summary.get("target_reached"),
            "collection_status": review_summary.get("collection_status"),
            "rule_refinement_status": review_summary.get("rule_refinement_status"),
            "cleanup_flags": review_summary.get("cleanup_flags"),
            "warnings": review_summary.get("warnings"),
            "n_invalid_rows_total": review_summary.get("n_invalid_rows_total"),
            "invalid_rows_preview": (review_summary.get("invalid_rows") or [])[:20],
        }

        if cleanup_blocked:
            report["status"] = "blocked"
            report["failure_reason"] = "needs_label_cleanup"
            report["next_step_hint"] = _next_step_hint(
                export_ran=False,
                cleanup_blocked=True,
                encoder_summary=None,
            )
            return report

        if not export_allowed:
            report["status"] = "blocked"
            report["failure_reason"] = f"unsupported_summary_next_action:{next_action}"
            report["next_step_hint"] = _next_step_hint(
                export_ran=False,
                cleanup_blocked=False,
                encoder_summary=None,
            )
            return report

        encoder_summary = export_encoder_examples(
            item_id=item_id,
            bundle_path=bundle_path,
            input_paths=input_paths,
            out_xlsx=paths["encoder_xlsx"],
            out_jsonl=paths["encoder_jsonl"],
            out_summary=paths["encoder_summary"],
            min_pos=target_pos,
            min_neg=target_neg,
            max_batches=max_batches,
            seed=seed,
            require_text_id=require_text_id,
        )
        report["export_ran"] = True
        report["encoder_summary"] = {
            "n_rows_read": encoder_summary.get("n_rows_read"),
            "n_rows_exported": encoder_summary.get("n_rows_exported"),
            "label_counts": encoder_summary.get("label_counts"),
            "role_counts": encoder_summary.get("role_counts"),
            "split_counts": encoder_summary.get("split_counts"),
            "target_reached": encoder_summary.get("target_reached"),
            "ready_for_training": encoder_summary.get("ready_for_training"),
            "warnings": encoder_summary.get("warnings"),
            "class_balance": encoder_summary.get("class_balance"),
        }
        report["status"] = "ok"
        report["failure_reason"] = None
        report["next_step_hint"] = _next_step_hint(
            export_ran=True,
            cleanup_blocked=False,
            encoder_summary=encoder_summary,
        )
        return report
    finally:
        report["finished_at"] = _now_utc()
        if report.get("next_step_hint") is None:
            report["next_step_hint"] = _next_step_hint(
                export_ran=bool(report.get("export_ran")),
                cleanup_blocked=bool(report.get("cleanup_blocked")),
                encoder_summary=report.get("encoder_summary"),
            )
        _write_json(paths["finalize_report"], report)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-id", required=True, help="Grammar item or task unit id, e.g. df003 or ps_ce002.")
    parser.add_argument("--bundle", required=True, type=Path, help="Detector bundle JSON used to build encoder text_b.")
    parser.add_argument(
        "--input",
        action="append",
        required=True,
        dest="inputs",
        type=Path,
        help="Human-labeled review .xlsx or .csv file. Can be passed multiple times.",
    )
    parser.add_argument(
        "--artifact-root",
        required=True,
        type=Path,
        help="Base artifact folder. Outputs are written under {artifact_root}/{item_id}/.",
    )
    parser.add_argument("--target-pos", type=int, default=100)
    parser.add_argument("--target-neg", type=int, default=100)
    parser.add_argument("--max-batches", type=int, default=3)
    parser.add_argument("--fp-tp-ratio-threshold", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=20260502)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--require-text-id",
        action="store_true",
        help="Fail encoder export when any exported row has blank text_id. Recommended for normal batch automation.",
    )
    parser.add_argument(
        "--allow-cleanup-export",
        action="store_true",
        help="Export even when summarize_review reports needs_label_cleanup. Not recommended for normal runs.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = finalize_labeled_review(
            item_id=args.item_id,
            bundle_path=args.bundle,
            input_paths=args.inputs,
            artifact_root=args.artifact_root,
            target_pos=args.target_pos,
            target_neg=args.target_neg,
            max_batches=args.max_batches,
            fp_tp_ratio_threshold=args.fp_tp_ratio_threshold,
            seed=args.seed,
            overwrite=args.overwrite,
            allow_cleanup_export=args.allow_cleanup_export,
            require_text_id=args.require_text_id,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should emit a concise fatal message.
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "item_id": report["item_id"],
                "status": report["status"],
                "failure_reason": report.get("failure_reason"),
                "summary_next_action": report.get("summary_next_action"),
                "export_ran": report.get("export_ran"),
                "label_counts": (report.get("summary") or {}).get("label_counts"),
                "ready_for_training": (report.get("encoder_summary") or {}).get("ready_for_training"),
                "outputs": report.get("outputs"),
                "next_step_hint": report.get("next_step_hint"),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0 if report["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
