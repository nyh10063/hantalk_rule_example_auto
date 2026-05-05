#!/usr/bin/env python3
"""Run review automation for many detector units in sequence.

This orchestrator is intentionally thin. It delegates actual unit work to
run_corpus_review_batch.py or run_full_corpus_review.py, records each unit
result, and continues to the next unit unless --stop-on-failure is set.
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
    from .run_corpus_review_batch import run_corpus_review_batch
    from .run_full_corpus_review import (
        DEFAULT_BACKFILL_DOMAIN,
        DEFAULT_MAX_FIRST_PASS_FP,
        DEFAULT_MAX_FIRST_PASS_UNCLEAR,
        DEFAULT_MAX_SHARDS,
        DEFAULT_TARGET_FIRST_PASS_TP,
        run_full_corpus_review,
    )
except ImportError:  # pragma: no cover - supports direct script execution.
    from run_corpus_review_batch import run_corpus_review_batch
    from run_full_corpus_review import (
        DEFAULT_BACKFILL_DOMAIN,
        DEFAULT_MAX_FIRST_PASS_FP,
        DEFAULT_MAX_FIRST_PASS_UNCLEAR,
        DEFAULT_MAX_SHARDS,
        DEFAULT_TARGET_FIRST_PASS_TP,
        run_full_corpus_review,
    )


SCHEMA_VERSION = "hantalk_many_review_units_run_report_v1"
MANIFEST_SCHEMA_VERSION = "hantalk_many_review_units_manifest_v1"
VALID_MODES = {"sampled_batch", "full_corpus"}
PATH_KEYS = {"gold", "bundle", "dict", "manifest", "corpus_root", "prepared_root", "artifact_root"}


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
    path = Path(str(value))
    return path if path.is_absolute() else cwd / path


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
    mode = str(normalized.get("mode") or "full_corpus").strip()
    if mode not in VALID_MODES:
        raise ValueError(f"mode must be one of {sorted(VALID_MODES)}: {mode!r}")
    normalized["mode"] = mode
    for key in PATH_KEYS:
        if key in normalized:
            normalized[key] = _resolve_path(normalized.get(key), cwd=cwd)
    return normalized


def _require(config: dict[str, Any], key: str) -> Any:
    value = config.get(key)
    if _is_blank(value):
        raise ValueError(f"unit_id={config.get('unit_id')}: missing required config key: {key}")
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


def _int_config(config: dict[str, Any], key: str, default: int | None = None) -> int | None:
    value = config.get(key, default)
    if value is None:
        return None
    return int(value)


def _path_config(config: dict[str, Any], key: str) -> Path:
    value = _require(config, key)
    if not isinstance(value, Path):
        raise ValueError(f"unit_id={config.get('unit_id')}: {key} did not resolve to Path: {value!r}")
    return value


def _validate_common_config(config: dict[str, Any]) -> None:
    _require(config, "unit_id")
    for key in ["gold", "bundle", "manifest", "corpus_root", "prepared_root", "artifact_root"]:
        _path_config(config, key)
    if config["mode"] == "sampled_batch":
        _require(config, "batch_index")


def _build_full_corpus_namespace(config: dict[str, Any], *, overwrite: bool) -> argparse.Namespace:
    _validate_common_config(config)
    return argparse.Namespace(
        unit_id=str(config["unit_id"]).strip(),
        gold=_path_config(config, "gold"),
        bundle=_path_config(config, "bundle"),
        dict_xlsx=_resolve_path(config.get("dict"), cwd=Path.cwd()) if not isinstance(config.get("dict"), Path) else config.get("dict"),
        manifest=_path_config(config, "manifest"),
        corpus_root=_path_config(config, "corpus_root"),
        prepared_root=_path_config(config, "prepared_root"),
        artifact_root=_path_config(config, "artifact_root"),
        start_shard_index=int(config.get("start_shard_index", 0)),
        target_first_pass_tp=int(config.get("target_first_pass_tp", DEFAULT_TARGET_FIRST_PASS_TP)),
        max_first_pass_fp=int(config.get("max_first_pass_fp", DEFAULT_MAX_FIRST_PASS_FP)),
        max_first_pass_unclear=int(config.get("max_first_pass_unclear", DEFAULT_MAX_FIRST_PASS_UNCLEAR)),
        max_shards=int(config.get("max_shards", DEFAULT_MAX_SHARDS)),
        backfill_domain=str(config.get("backfill_domain") or DEFAULT_BACKFILL_DOMAIN),
        allow_polyset=_bool_config(config, "allow_polyset", False),
        include_debug=_bool_config(config, "include_debug", False),
        overwrite_shards=overwrite or _bool_config(config, "overwrite_shards", False),
        skip_dict_bundle_sync=_bool_config(config, "skip_dict_bundle_sync", False),
        seed=_int_config(config, "seed", None),
    )


def _build_sampled_batch_namespace(config: dict[str, Any], *, overwrite: bool) -> argparse.Namespace:
    _validate_common_config(config)
    return argparse.Namespace(
        unit_id=str(config["unit_id"]).strip(),
        gold=_path_config(config, "gold"),
        bundle=_path_config(config, "bundle"),
        dict_xlsx=_resolve_path(config.get("dict"), cwd=Path.cwd()) if not isinstance(config.get("dict"), Path) else config.get("dict"),
        manifest=_path_config(config, "manifest"),
        corpus_root=_path_config(config, "corpus_root"),
        prepared_root=_path_config(config, "prepared_root"),
        artifact_root=_path_config(config, "artifact_root"),
        batch_index=int(config.get("batch_index")),
        allow_polyset=_bool_config(config, "allow_polyset", False),
        include_debug=_bool_config(config, "include_debug", False),
        overwrite=overwrite or _bool_config(config, "overwrite", False),
        skip_dict_bundle_sync=_bool_config(config, "skip_dict_bundle_sync", False),
        seed=_int_config(config, "seed", None),
    )


def _summarize_full_corpus_report(report: dict[str, Any]) -> dict[str, Any]:
    outputs = report.get("outputs") or {}
    return {
        "status": report.get("status"),
        "failure_reason": report.get("failure_reason"),
        "stop_reason": report.get("stop_reason"),
        "target_reached": report.get("target_reached"),
        "cumulative": report.get("cumulative"),
        "shards_processed": report.get("shards_processed"),
        "shards_reused": report.get("shards_reused"),
        "human_working_file": outputs.get("merged_first_pass_xlsx"),
        "run_report_json": outputs.get("run_report_json"),
    }


def _summarize_sampled_batch_report(report: dict[str, Any]) -> dict[str, Any]:
    outputs = report.get("outputs") or {}
    return {
        "status": report.get("status"),
        "failure_reason": report.get("failure_reason"),
        "stop_reason": report.get("stop_reason"),
        "target_reached": None,
        "gold_recall": (report.get("gold_gate") or {}).get("gold_recall"),
        "fn_count": (report.get("gold_gate") or {}).get("fn_count"),
        "n_candidates": (report.get("search_summary") or {}).get("n_candidates"),
        "first_pass_review_summary": report.get("first_pass_review_summary"),
        "human_working_file": outputs.get("first_pass_xlsx"),
        "run_report_json": outputs.get("run_report_json"),
    }


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


def _run_one_unit(config: dict[str, Any], *, overwrite: bool, dry_run: bool) -> dict[str, Any]:
    unit_id = str(config["unit_id"]).strip()
    mode = str(config["mode"])
    if dry_run:
        return {
            "unit_id": unit_id,
            "mode": mode,
            "status": "dry_run",
            "selected": True,
            "config": _jsonable_config(config),
        }

    if mode == "full_corpus":
        report = run_full_corpus_review(_build_full_corpus_namespace(config, overwrite=overwrite))
        summary = _summarize_full_corpus_report(report)
    elif mode == "sampled_batch":
        report = run_corpus_review_batch(_build_sampled_batch_namespace(config, overwrite=overwrite))
        summary = _summarize_sampled_batch_report(report)
    else:  # pragma: no cover - validated earlier.
        raise ValueError(f"unsupported mode: {mode}")

    summary.update(
        {
            "unit_id": unit_id,
            "mode": mode,
            "selected": True,
        }
    )
    return summary


def _jsonable_config(config: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in sorted(config.items()):
        if isinstance(value, Path):
            out[key] = str(value)
        else:
            out[key] = value
    return out


def _new_report(args: argparse.Namespace, manifest_data: dict[str, Any], entries: list[dict[str, Any]], *, cwd: Path) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_utc(),
        "manifest": str(args.manifest),
        "out_report": str(args.out_report),
        "cwd": str(cwd),
        "path_resolution_base": "cwd",
        "dry_run": bool(args.dry_run),
        "stop_on_failure": bool(args.stop_on_failure),
        "manifest_schema_version": manifest_data.get("schema_version"),
        "n_units_total": len(manifest_data.get("units") or []),
        "n_units_selected": sum(1 for entry in entries if entry["selected"]),
        "n_ok": 0,
        "n_blocked": 0,
        "n_failed": 0,
        "n_skipped": 0,
        "n_dry_run": 0,
        "units": [],
        "status": "running",
        "failure_reason": None,
    }


def _recount(report: dict[str, Any]) -> None:
    counts = {"ok": 0, "blocked": 0, "failed": 0, "skipped": 0, "dry_run": 0}
    for unit in report["units"]:
        bucket = _unit_bucket(unit.get("status"))
        counts[bucket] += 1
    report["n_ok"] = counts["ok"]
    report["n_blocked"] = counts["blocked"]
    report["n_failed"] = counts["failed"]
    report["n_skipped"] = counts["skipped"]
    report["n_dry_run"] = counts["dry_run"]


def run_many_review_units(args: argparse.Namespace) -> dict[str, Any]:
    cwd = Path.cwd()
    manifest_data = _load_json(args.manifest)
    units = manifest_data.get("units") or []
    if not isinstance(units, list) or not units:
        raise ValueError(f"{args.manifest}: units must be a non-empty list")
    if manifest_data.get("schema_version") not in {None, MANIFEST_SCHEMA_VERSION}:
        raise ValueError(
            f"{args.manifest}: unsupported schema_version={manifest_data.get('schema_version')!r}; "
            f"expected {MANIFEST_SCHEMA_VERSION!r}"
        )

    only_units = set(args.only_unit) if args.only_unit else None
    entries = _selected_unit_entries(units, only_units=only_units, start_at_unit=args.start_at_unit)
    report = _new_report(args, manifest_data, entries, cwd=cwd)
    defaults = manifest_data.get("defaults") or {}
    if not isinstance(defaults, dict):
        raise ValueError(f"{args.manifest}: defaults must be an object when present")

    try:
        for entry in entries:
            unit = entry["unit"]
            unit_id = _unit_id(unit)
            if not entry["selected"]:
                report["units"].append(
                    {
                        "unit_id": unit_id,
                        "mode": str((_merge_defaults(defaults, unit)).get("mode") or "full_corpus"),
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
                    "mode": str((_merge_defaults(defaults, unit)).get("mode") or "full_corpus"),
                    "status": "failed",
                    "selected": True,
                    "failure_reason": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(limit=20),
                }
            report["units"].append(result)
            _recount(report)
            _write_json(args.out_report, report)

            if args.stop_on_failure and _unit_bucket(result.get("status")) in {"blocked", "failed"}:
                report["status"] = "stopped_on_failure"
                report["failure_reason"] = result.get("failure_reason") or result.get("stop_reason")
                break

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
    parser.add_argument("--manifest", required=True, type=Path, help="Many-unit review manifest JSON.")
    parser.add_argument("--out-report", required=True, type=Path, help="Path to write the aggregate run report JSON.")
    parser.add_argument("--only-unit", action="append", default=None, help="Run only this unit_id. May be repeated.")
    parser.add_argument("--start-at-unit", default=None, help="Skip manifest units before this unit_id.")
    parser.add_argument("--overwrite", action="store_true", help="Forward overwrite behavior to the underlying unit runner.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and record planned unit configs without running them.")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop after the first blocked/failed selected unit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = run_many_review_units(args)
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
