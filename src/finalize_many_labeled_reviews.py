#!/usr/bin/env python3
"""Finalize labeled reviews for many units, then rebuild the encoder aggregate.

This orchestrator is intentionally thin. It delegates unit-level work to
finalize_labeled_review.py and aggregate rebuilding to merge_encoder_examples.py.
It does not edit dict files, detector rules, or detector bundles.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .finalize_labeled_review import finalize_labeled_review
    from .merge_encoder_examples import merge_encoder_examples
except ImportError:  # pragma: no cover - supports direct script execution.
    from finalize_labeled_review import finalize_labeled_review
    from merge_encoder_examples import merge_encoder_examples


SCHEMA_VERSION = "hantalk_finalize_many_labeled_reviews_report_v1"
MANIFEST_SCHEMA_VERSION = "hantalk_finalize_many_labeled_reviews_manifest_v1"
PATH_KEYS = {"artifact_root", "bundle", "merge_out_dir", "out_dir"}
INPUT_EXT_PRIORITY = {".xlsx": 0, ".csv": 1}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _resolve_path(value: Any, *, cwd: Path) -> Path | None:
    if _is_blank(value):
        return None
    path = Path(str(value)).expanduser()
    return path if path.is_absolute() else cwd / path


def _jsonable_config(config: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in sorted(config.items()):
        if isinstance(value, Path):
            out[key] = str(value)
        elif isinstance(value, list):
            out[key] = [str(item) if isinstance(item, Path) else item for item in value]
        else:
            out[key] = value
    return out


def _merge_defaults(defaults: dict[str, Any], unit: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    merged.update(unit)
    return merged


def _unit_id(unit: dict[str, Any]) -> str:
    unit_id = str(unit.get("unit_id") or "").strip()
    if not unit_id:
        raise ValueError(f"unit entry is missing unit_id: {unit}")
    return unit_id


def _selected_unit_entries(
    units: list[dict[str, Any]],
    *,
    only_units: set[str] | None,
    start_at_unit: str | None,
) -> list[dict[str, Any]]:
    if start_at_unit is not None and start_at_unit not in {_unit_id(unit) for unit in units}:
        raise ValueError(f"--start-at-unit not found in manifest units: {start_at_unit}")

    entries: list[dict[str, Any]] = []
    start_reached = start_at_unit is None
    for index, unit in enumerate(units):
        unit_id = _unit_id(unit)
        if only_units is not None and unit_id not in only_units:
            entries.append({"index": index, "unit": unit, "selected": False, "skip_reason": "skipped_by_only_unit_filter"})
            continue
        if not start_reached:
            if unit_id == start_at_unit:
                start_reached = True
            else:
                entries.append({"index": index, "unit": unit, "selected": False, "skip_reason": "skipped_before_start_at_unit"})
                continue
        entries.append({"index": index, "unit": unit, "selected": True, "skip_reason": None})
    return entries


def _normalize_config(config: dict[str, Any], *, cwd: Path) -> dict[str, Any]:
    normalized = dict(config)
    for key in PATH_KEYS:
        if key in normalized:
            normalized[key] = _resolve_path(normalized.get(key), cwd=cwd)
    normalized["inputs"] = _dedupe_unit_inputs(_raw_inputs(normalized), cwd=cwd)
    return normalized


def _raw_inputs(config: dict[str, Any]) -> list[Any]:
    if "inputs" in config and "input" in config:
        raise ValueError(f"unit_id={config.get('unit_id')}: use either inputs or input, not both")
    if "inputs" in config:
        inputs = config.get("inputs")
        if not isinstance(inputs, list):
            raise ValueError(f"unit_id={config.get('unit_id')}: inputs must be a list")
        return inputs
    if "input" in config:
        return [config.get("input")]
    return []


def _dedupe_unit_inputs(values: list[Any], *, cwd: Path) -> list[Path]:
    """Deduplicate CSV/XLSX copies per unit, preferring XLSX for the same stem."""
    resolved = [_resolve_path(value, cwd=cwd) for value in values]
    paths = [path for path in resolved if path is not None]
    if not paths:
        return []

    grouped: dict[tuple[Path, str], list[Path]] = {}
    for path in paths:
        grouped.setdefault((path.parent, path.stem), []).append(path)

    deduped: list[Path] = []
    for _, group in sorted(grouped.items(), key=lambda item: (str(item[0][0]), item[0][1])):
        sorted_group = sorted(
            group,
            key=lambda path: (INPUT_EXT_PRIORITY.get(path.suffix.lower(), 99), path.suffix.lower(), str(path)),
        )
        deduped.append(sorted_group[0])
    return deduped


def _require(config: dict[str, Any], key: str) -> Any:
    value = config.get(key)
    if _is_blank(value):
        raise ValueError(f"unit_id={config.get('unit_id')}: missing required config key: {key}")
    return value


def _path_config(config: dict[str, Any], key: str) -> Path:
    value = _require(config, key)
    if not isinstance(value, Path):
        raise ValueError(f"unit_id={config.get('unit_id')}: {key} did not resolve to Path: {value!r}")
    return value


def _bool_config(config: dict[str, Any], key: str, default: bool = False) -> bool:
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(int(value))
    text = str(value).strip().lower()
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0", ""}:
        return False
    raise ValueError(f"unit_id={config.get('unit_id')}: {key} must be boolean-like: {value!r}")


def _int_config(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get(key, default))


def _float_config(config: dict[str, Any], key: str, default: float) -> float:
    return float(config.get(key, default))


def _validate_unit_config(config: dict[str, Any]) -> None:
    _require(config, "unit_id")
    _path_config(config, "bundle")
    _path_config(config, "artifact_root")
    if not config.get("inputs"):
        raise ValueError(f"unit_id={config.get('unit_id')}: at least one labeled input is required")


def _encoder_jsonl_path(*, unit_id: str, artifact_root: Path) -> Path:
    return artifact_root / unit_id / f"{unit_id}_encoder_pair_examples.jsonl"


def _unit_bucket(status: str | None) -> str:
    if status == "ok":
        return "ok"
    if status == "blocked":
        return "blocked"
    if status == "dry_run":
        return "dry_run"
    if status == "skipped":
        return "skipped"
    return "failed"


def _summarize_finalize_report(report: dict[str, Any], *, unit_id: str, artifact_root: Path) -> dict[str, Any]:
    outputs = report.get("outputs") or {}
    encoder_summary = report.get("encoder_summary") or {}
    summary = report.get("summary") or {}
    encoder_jsonl = outputs.get("encoder_jsonl") or str(_encoder_jsonl_path(unit_id=unit_id, artifact_root=artifact_root))
    return {
        "unit_id": unit_id,
        "status": report.get("status"),
        "failure_reason": report.get("failure_reason"),
        "summary_next_action": report.get("summary_next_action"),
        "export_ran": bool(report.get("export_ran")),
        "ready_for_training": encoder_summary.get("ready_for_training"),
        "label_counts": summary.get("label_counts"),
        "encoder_label_counts": encoder_summary.get("label_counts"),
        "encoder_n_rows_exported": encoder_summary.get("n_rows_exported"),
        "encoder_jsonl": encoder_jsonl,
        "encoder_xlsx": outputs.get("encoder_xlsx"),
        "encoder_summary": outputs.get("encoder_summary"),
        "review_summary": outputs.get("review_summary"),
        "finalize_report": outputs.get("finalize_report"),
        "next_step_hint": report.get("next_step_hint"),
    }


def _run_one_unit(config: dict[str, Any], *, overwrite: bool, dry_run: bool) -> dict[str, Any]:
    _validate_unit_config(config)
    unit_id = str(config["unit_id"]).strip()
    artifact_root = _path_config(config, "artifact_root")
    if dry_run:
        return {
            "unit_id": unit_id,
            "status": "dry_run",
            "selected": True,
            "export_ran": False,
            "config": _jsonable_config(config),
            "planned_encoder_jsonl": str(_encoder_jsonl_path(unit_id=unit_id, artifact_root=artifact_root)),
        }

    report = finalize_labeled_review(
        item_id=unit_id,
        bundle_path=_path_config(config, "bundle"),
        input_paths=list(config["inputs"]),
        artifact_root=artifact_root,
        target_pos=_int_config(config, "target_pos", 100),
        target_neg=_int_config(config, "target_neg", 100),
        max_batches=_int_config(config, "max_batches", 3),
        min_tp_for_batch_mode=_int_config(config, "min_tp_for_batch_mode", 30),
        fp_tp_ratio_threshold=_float_config(config, "fp_tp_ratio_threshold", 2.0),
        seed=_int_config(config, "seed", 20260502),
        overwrite=overwrite or _bool_config(config, "overwrite", False),
        allow_cleanup_export=_bool_config(config, "allow_cleanup_export", False),
        require_text_id=_bool_config(config, "require_text_id", True),
    )
    summary = _summarize_finalize_report(report, unit_id=unit_id, artifact_root=artifact_root)
    summary["selected"] = True
    return summary


def _merge_config(manifest_data: dict[str, Any], *, args: argparse.Namespace, cwd: Path) -> dict[str, Any]:
    merge_data = manifest_data.get("merge") or {}
    if not isinstance(merge_data, dict):
        raise ValueError("manifest merge must be an object when present")

    enabled = bool(merge_data.get("enabled", True)) and not args.skip_merge
    out_dir = args.merge_out_dir
    if out_dir is None:
        out_dir = _resolve_path(merge_data.get("out_dir"), cwd=cwd)
    return {
        "enabled": enabled,
        "out_dir": out_dir,
    }


def _run_merge(
    *,
    successful_jsonl_paths: list[Path],
    merge_config: dict[str, Any],
    includes_only_this_run_units: bool,
    dry_run: bool,
) -> dict[str, Any]:
    if not merge_config["enabled"]:
        return {
            "enabled": False,
            "status": "skipped_disabled",
            "includes_only_this_run_units": includes_only_this_run_units,
            "n_input_files": len(successful_jsonl_paths),
        }
    out_dir = merge_config.get("out_dir")
    if out_dir is None:
        raise ValueError("merge is enabled but merge.out_dir or --merge-out-dir was not provided")
    if not successful_jsonl_paths:
        return {
            "enabled": True,
            "status": "skipped_no_successful_exports",
            "includes_only_this_run_units": includes_only_this_run_units,
            "n_input_files": 0,
            "out_dir": str(out_dir),
        }
    if dry_run:
        return {
            "enabled": True,
            "status": "dry_run",
            "includes_only_this_run_units": includes_only_this_run_units,
            "n_input_files": len(successful_jsonl_paths),
            "input_files": [str(path) for path in successful_jsonl_paths],
            "out_dir": str(out_dir),
        }

    summary = merge_encoder_examples(input_paths=successful_jsonl_paths, out_dir=out_dir)
    return {
        "enabled": True,
        "status": "ok",
        "includes_only_this_run_units": includes_only_this_run_units,
        "n_input_files": summary.get("n_input_files"),
        "n_examples": summary.get("n_examples"),
        "item_counts": summary.get("item_counts"),
        "label_counts": summary.get("label_counts"),
        "split_counts": summary.get("split_counts"),
        "out_jsonl": summary.get("out_jsonl"),
        "out_xlsx": summary.get("out_xlsx"),
        "out_summary": summary.get("out_summary"),
    }


def _new_report(
    args: argparse.Namespace,
    manifest_data: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    cwd: Path,
    merge_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_utc(),
        "manifest": str(args.manifest),
        "out_report": str(args.out_report),
        "cwd": str(cwd),
        "path_resolution_base": "cwd",
        "dry_run": bool(args.dry_run),
        "stop_on_failure": bool(args.stop_on_failure),
        "skip_merge": bool(args.skip_merge),
        "only_unit": args.only_unit or [],
        "start_at_unit": args.start_at_unit,
        "manifest_schema_version": manifest_data.get("schema_version"),
        "n_units_total": len(manifest_data.get("units") or []),
        "n_units_selected": sum(1 for entry in entries if entry["selected"]),
        "n_ok": 0,
        "n_blocked": 0,
        "n_failed": 0,
        "n_skipped": 0,
        "n_dry_run": 0,
        "n_exported": 0,
        "successful_encoder_jsonl_paths": [],
        "merge": {
            "enabled": bool(merge_config["enabled"]),
            "status": "pending",
            "out_dir": str(merge_config["out_dir"]) if merge_config.get("out_dir") else None,
        },
        "units": [],
        "status": "running",
        "failure_reason": None,
    }


def _recount(report: dict[str, Any]) -> None:
    counts = {"ok": 0, "blocked": 0, "failed": 0, "skipped": 0, "dry_run": 0}
    exported = 0
    successful_paths: list[str] = []
    for unit in report["units"]:
        bucket = _unit_bucket(unit.get("status"))
        counts[bucket] += 1
        if unit.get("status") == "ok" and unit.get("export_ran") and unit.get("encoder_jsonl"):
            exported += 1
            successful_paths.append(str(unit["encoder_jsonl"]))
    report["n_ok"] = counts["ok"]
    report["n_blocked"] = counts["blocked"]
    report["n_failed"] = counts["failed"]
    report["n_skipped"] = counts["skipped"]
    report["n_dry_run"] = counts["dry_run"]
    report["n_exported"] = exported
    report["successful_encoder_jsonl_paths"] = successful_paths


def run_finalize_many_labeled_reviews(args: argparse.Namespace) -> dict[str, Any]:
    cwd = Path.cwd()
    manifest_data = _load_json(args.manifest)
    if manifest_data.get("schema_version") not in {None, MANIFEST_SCHEMA_VERSION}:
        raise ValueError(
            f"{args.manifest}: unsupported schema_version={manifest_data.get('schema_version')!r}; "
            f"expected {MANIFEST_SCHEMA_VERSION!r}"
        )
    units = manifest_data.get("units") or []
    if not isinstance(units, list) or not units:
        raise ValueError(f"{args.manifest}: units must be a non-empty list")
    defaults = manifest_data.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError(f"{args.manifest}: defaults must be an object when present")

    only_units = set(args.only_unit) if args.only_unit else None
    entries = _selected_unit_entries(units, only_units=only_units, start_at_unit=args.start_at_unit)
    merge_config = _merge_config(manifest_data, args=args, cwd=cwd)
    includes_only_this_run_units = bool(args.only_unit or args.start_at_unit or sum(1 for entry in entries if entry["selected"]) < len(units))
    report = _new_report(args, manifest_data, entries, cwd=cwd, merge_config=merge_config)

    try:
        for entry in entries:
            unit = entry["unit"]
            unit_id = _unit_id(unit)
            if not entry["selected"]:
                report["units"].append(
                    {
                        "unit_id": unit_id,
                        "status": "skipped",
                        "selected": False,
                        "skip_reason": entry["skip_reason"],
                    }
                )
                _recount(report)
                _write_json(args.out_report, report)
                continue

            try:
                config = _normalize_config(_merge_defaults(defaults, unit), cwd=cwd)
                result = _run_one_unit(config, overwrite=args.overwrite, dry_run=args.dry_run)
            except Exception as exc:  # noqa: BLE001 - continue to next unit by default.
                result = {
                    "unit_id": unit_id,
                    "status": "failed",
                    "selected": True,
                    "export_ran": False,
                    "failure_reason": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(limit=20),
                }
            report["units"].append(result)
            _recount(report)
            _write_json(args.out_report, report)

            if args.stop_on_failure and _unit_bucket(result.get("status")) in {"blocked", "failed"}:
                report["status"] = "stopped_on_failure"
                report["failure_reason"] = result.get("failure_reason") or result.get("summary_next_action")
                break

        successful_jsonl_paths = [Path(path) for path in report["successful_encoder_jsonl_paths"]]
        try:
            report["merge"] = _run_merge(
                successful_jsonl_paths=successful_jsonl_paths,
                merge_config=merge_config,
                includes_only_this_run_units=includes_only_this_run_units,
                dry_run=args.dry_run,
            )
        except Exception as exc:  # noqa: BLE001 - merge failure should be visible in final report.
            report["merge"] = {
                "enabled": bool(merge_config["enabled"]),
                "status": "failed",
                "failure_reason": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(limit=20),
                "includes_only_this_run_units": includes_only_this_run_units,
                "n_input_files": len(successful_jsonl_paths),
            }
            if report["status"] == "running":
                report["status"] = "failed"
                report["failure_reason"] = "merge_failed"

        if report["status"] == "running":
            report["status"] = "ok"
            report["failure_reason"] = None
        return report
    finally:
        report["finished_at"] = _now_utc()
        _recount(report)
        _write_json(args.out_report, report)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="Many-unit finalize manifest JSON.")
    parser.add_argument("--out-report", required=True, type=Path, help="Path to write the aggregate finalize report JSON.")
    parser.add_argument("--only-unit", action="append", default=None, help="Run only this unit_id. May be repeated.")
    parser.add_argument("--start-at-unit", default=None, help="Skip manifest units before this unit_id.")
    parser.add_argument("--merge-out-dir", type=Path, default=None, help="Override manifest merge.out_dir.")
    parser.add_argument("--skip-merge", action="store_true", help="Finalize item-level outputs but skip all_encoder_* merge.")
    parser.add_argument("--overwrite", action="store_true", help="Forward overwrite behavior to unit-level finalize.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and record planned unit configs without running finalize/merge.")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop after the first blocked/failed selected unit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = run_finalize_many_labeled_reviews(args)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": report.get("status"),
                "failure_reason": report.get("failure_reason"),
                "n_units_total": report.get("n_units_total"),
                "n_units_selected": report.get("n_units_selected"),
                "n_ok": report.get("n_ok"),
                "n_blocked": report.get("n_blocked"),
                "n_failed": report.get("n_failed"),
                "n_skipped": report.get("n_skipped"),
                "n_dry_run": report.get("n_dry_run"),
                "n_exported": report.get("n_exported"),
                "merge_status": (report.get("merge") or {}).get("status"),
                "out_report": str(args.out_report),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0 if report.get("status") in {"ok", "stopped_on_failure"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
