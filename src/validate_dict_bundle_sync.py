#!/usr/bin/env python3
"""Validate that a detector bundle is still in sync with the dict Excel SSOT.

This script never edits the dict or bundle. It rebuilds an in-memory bundle
from the dict Excel and compares only the requested runtime unit slice against
the already-exported runtime bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .detector.export_bundle import build_bundle
except ImportError:  # pragma: no cover - supports direct script execution.
    from detector.export_bundle import build_bundle


SCHEMA_VERSION = "hantalk_dict_bundle_sync_report_v1"
COMPARISON_BASIS = "dict_exported_temp_bundle_vs_runtime_bundle"
PATTERN_COMPARISON = "exported_bundle_pattern"


MISSING = object()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def _blank_to_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _str_value(value: Any) -> str | None:
    return _blank_to_none(value)


def _str_list(value: Any) -> list[str]:
    if not value:
        return []
    if not isinstance(value, list):
        value = [value]
    out = []
    for item in value:
        text = _blank_to_none(item)
        if text is not None:
            out.append(text)
    return sorted(set(out))


def _int_value(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(int(value))
    text = str(value).strip().lower()
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0", ""}:
        return False
    raise ValueError(f"Cannot normalize boolean value: {value!r}")


def _normalize_rule(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "ruleset_id": _str_value(rule.get("ruleset_id")),
        "rule_id": _str_value(rule.get("rule_id")),
        "stage": _str_value(rule.get("stage")),
        "target": _str_value(rule.get("target")),
        "component_id": _blank_to_none(rule.get("component_id")),
        "pattern": _str_value(rule.get("pattern")),
        "priority": _int_value(rule.get("priority")),
        "hard_fail": _bool_value(rule.get("hard_fail")),
    }


def _normalize_component(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "unit_id": _str_value(component.get("unit_id")),
        "source_e_id": _str_value(component.get("source_e_id")),
        "ps_id": _str_value(component.get("ps_id")),
        "comp_id": _str_value(component.get("comp_id")),
        "comp_surf": _str_value(component.get("comp_surf")),
        "is_required": _bool_value(component.get("is_required")),
        "anchor_rank": _int_or_none(component.get("anchor_rank")),
        "comp_order": _int_or_none(component.get("comp_order")),
        "order_policy": _str_value(component.get("order_policy")),
        "min_gap_to_next": _int_or_none(component.get("min_gap_to_next")),
        "max_gap_to_next": _int_or_none(component.get("max_gap_to_next")),
        "bridge_id": _str_value(component.get("bridge_id")),
    }


def normalize_bundle_unit_slice(bundle: dict[str, Any], unit_id: str) -> dict[str, Any]:
    """Return the comparable unit slice for one runtime unit.

    The comparison intentionally ignores generated timestamps, source hashes,
    bridge metadata, item metadata, and gloss text. Patterns are compared after
    dict export because both sides are bundle-shaped values.
    """

    runtime_units = bundle.get("runtime_units") or {}
    rules_by_ruleset_id = bundle.get("rules_by_ruleset_id") or {}
    components_by_e_id = bundle.get("components_by_e_id") or {}
    unit = runtime_units.get(unit_id)
    if not isinstance(unit, dict):
        return {
            "runtime_unit": None,
            "components": [],
            "rules": [],
        }

    detect_ruleset_ids = _str_list(unit.get("detect_ruleset_ids"))
    verify_ruleset_ids = _str_list(unit.get("verify_ruleset_ids"))
    ruleset_ids = sorted(set(detect_ruleset_ids + verify_ruleset_ids))
    rules: list[dict[str, Any]] = []
    for ruleset_id in ruleset_ids:
        for rule in rules_by_ruleset_id.get(ruleset_id, []):
            if not isinstance(rule, dict):
                continue
            rules.append(_normalize_rule(rule))
    rules.sort(
        key=lambda item: (
            item.get("ruleset_id") or "",
            item.get("priority") or 0,
            item.get("rule_id") or "",
        )
    )
    components = [
        _normalize_component(component)
        for component in components_by_e_id.get(unit_id, [])
        if isinstance(component, dict)
    ]
    components.sort(
        key=lambda item: (
            item.get("comp_order") is None,
            item.get("comp_order") or 0,
            item.get("comp_id") or "",
        )
    )

    return {
        "runtime_unit": {
            "unit_id": _str_value(unit.get("unit_id")),
            "unit_type": _str_value(unit.get("unit_type")),
            "member_e_ids": _str_list(unit.get("member_e_ids")),
            "canonical_form": _str_value(unit.get("canonical_form")),
            "detect_ruleset_ids": detect_ruleset_ids,
            "verify_ruleset_ids": verify_ruleset_ids,
        },
        "components": components,
        "rules": rules,
    }


def _jsonable(value: Any) -> Any:
    if value is MISSING:
        return "__missing__"
    return value


def _diff_values(expected: Any, actual: Any, *, path: str = "$") -> list[dict[str, Any]]:
    if isinstance(expected, dict) and isinstance(actual, dict):
        diffs: list[dict[str, Any]] = []
        for key in sorted(set(expected) | set(actual)):
            next_expected = expected.get(key, MISSING)
            next_actual = actual.get(key, MISSING)
            diffs.extend(_diff_values(next_expected, next_actual, path=f"{path}.{key}"))
        return diffs

    if isinstance(expected, list) and isinstance(actual, list):
        diffs = []
        max_len = max(len(expected), len(actual))
        for idx in range(max_len):
            next_expected = expected[idx] if idx < len(expected) else MISSING
            next_actual = actual[idx] if idx < len(actual) else MISSING
            diffs.extend(_diff_values(next_expected, next_actual, path=f"{path}[{idx}]"))
        return diffs

    if expected != actual:
        return [
            {
                "path": path,
                "dict_value": _jsonable(expected),
                "bundle_value": _jsonable(actual),
            }
        ]
    return []


def build_sync_report(*, dict_xlsx: Path, bundle_path: Path, unit_id: str) -> dict[str, Any]:
    if not dict_xlsx.exists():
        raise FileNotFoundError(f"dict Excel not found: {dict_xlsx}")
    if not bundle_path.exists():
        raise FileNotFoundError(f"detector bundle not found: {bundle_path}")

    dict_bundle = build_bundle(dict_xlsx)
    runtime_bundle = _load_json(bundle_path)
    dict_slice = normalize_bundle_unit_slice(dict_bundle, unit_id)
    bundle_slice = normalize_bundle_unit_slice(runtime_bundle, unit_id)
    diffs = _diff_values(dict_slice, bundle_slice)

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_utc(),
        "unit_id": unit_id,
        "dict_xlsx": str(dict_xlsx),
        "dict_xlsx_sha256": _sha256(dict_xlsx),
        "bundle": str(bundle_path),
        "bundle_sha256": _sha256(bundle_path),
        "comparison_basis": COMPARISON_BASIS,
        "pattern_comparison": PATTERN_COMPARISON,
        "normalization": {
            "component_id_blank_equals_null": True,
            "string_lists_are_compared_as_sorted_sets": True,
        },
        "ignored_fields": [
            "source.generated_at",
            "source.source_sha256",
            "source.dict_xlsx",
            "items_by_e_id",
            "polysets_by_id",
            "bridges_by_id",
            "runtime_units.*.gloss",
            "warnings",
        ],
        "compared_fields": {
            "runtime_unit": [
                "unit_id",
                "unit_type",
                "member_e_ids",
                "canonical_form",
                "detect_ruleset_ids",
                "verify_ruleset_ids",
            ],
            "components": [
                "unit_id",
                "source_e_id",
                "ps_id",
                "comp_id",
                "comp_surf",
                "is_required",
                "anchor_rank",
                "comp_order",
                "order_policy",
                "min_gap_to_next",
                "max_gap_to_next",
                "bridge_id",
            ],
            "rules": [
                "ruleset_id",
                "rule_id",
                "stage",
                "target",
                "component_id",
                "pattern",
                "priority",
                "hard_fail",
            ],
        },
        "dict_export_warning_count": len(dict_bundle.get("warnings") or []),
        "dict_export_warnings": list(dict_bundle.get("warnings") or []),
        "dict_unit_exists": dict_slice["runtime_unit"] is not None,
        "bundle_unit_exists": bundle_slice["runtime_unit"] is not None,
        "in_sync": not diffs,
        "diff_count": len(diffs),
        "diffs": diffs,
    }


def validate_dict_bundle_sync(
    *,
    dict_xlsx: Path,
    bundle_path: Path,
    unit_id: str,
    report_json: Path | None = None,
) -> dict[str, Any]:
    report = build_sync_report(dict_xlsx=dict_xlsx, bundle_path=bundle_path, unit_id=unit_id)
    if report_json is not None:
        _write_json(report_json, report)
    return report


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dict",
        dest="dict_xlsx",
        type=Path,
        required=True,
        help="Human-managed dict Excel SSOT to compare by re-exporting in memory.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        required=True,
        help="Existing detector bundle JSON that will be used by runtime/search.",
    )
    parser.add_argument(
        "--unit-id",
        required=True,
        help="Runtime unit id to compare, e.g. df003 or ps_ce002.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        required=True,
        help="Path for the dict/bundle sync report JSON.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = validate_dict_bundle_sync(
            dict_xlsx=args.dict_xlsx,
            bundle_path=args.bundle,
            unit_id=str(args.unit_id),
            report_json=args.report_json,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should give a concise fatal message.
        error_report = {
            "schema_version": SCHEMA_VERSION,
            "created_at": _now_utc(),
            "unit_id": str(args.unit_id),
            "dict_xlsx": str(args.dict_xlsx),
            "bundle": str(args.bundle),
            "comparison_basis": COMPARISON_BASIS,
            "pattern_comparison": PATTERN_COMPARISON,
            "in_sync": False,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        _write_json(args.report_json, error_report)
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "unit_id": report["unit_id"],
                "in_sync": report["in_sync"],
                "diff_count": report["diff_count"],
                "report_json": str(args.report_json),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0 if report["in_sync"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
