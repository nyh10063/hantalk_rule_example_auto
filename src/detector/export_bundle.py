#!/usr/bin/env python3
"""Export a runtime detector bundle from the human-managed dict.xlsx."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

try:
    from .bridges import BRIDGE_REGISTRY, bridge_metadata_by_id
except ImportError:  # pragma: no cover - supports direct script execution.
    from src.detector.bridges import BRIDGE_REGISTRY, bridge_metadata_by_id

SCHEMA_VERSION = "hantalk_detector_bundle_v1"

REQUIRED_SHEETS = {"items", "rule_components", "detect_rules"}
REQUIRED_COLUMNS = {
    "items": {
        "e_id",
        "canonical_form",
        "group",
        "polyset_id",
        "disconti_allowed",
        "e_comp_id",
        "detect_ruleset_id",
        "verify_ruleset_id",
        "gloss",
    },
    "rule_components": {
        "e_id",
        "comp_surf",
        "comp_id",
        "is_required",
        "anchor_rank",
        "comp_order",
        "order_policy",
        "min_gap_to_next",
        "max_gap_to_next",
    },
    "detect_rules": {
        "e_id",
        "ruleset_id",
        "rule_id",
        "stage",
        "target",
        "pattern",
        "priority",
        "hard_fail",
    },
}

VALID_GROUPS = {"a", "b", "c"}
VALID_STAGES = {"detect", "verify"}
VALID_TARGETS_BY_STAGE = {
    "detect": {"raw_sentence"},
    "verify": {"raw_sentence", "char_window"},
}
VALID_ORDER_POLICIES = {"fx", "fl"}


class BundleExportError(ValueError):
    """Fatal bundle export error."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _text(value: Any, *, lower: bool = False, none_if_blank: bool = True) -> str | None:
    if _is_blank(value):
        return None if none_if_blank else ""
    out = str(value).strip()
    return out.lower() if lower else out


def _required_text(record: dict[str, Any], key: str, *, sheet: str, row_no: int, lower: bool = False) -> str:
    value = _text(record.get(key), lower=lower)
    if value is None:
        raise BundleExportError(f"{sheet}:{row_no} missing required value: {key}")
    return value


def _int_or_none(value: Any, *, sheet: str, row_no: int, key: str) -> int | None:
    if _is_blank(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise BundleExportError(f"{sheet}:{row_no} {key} must be int-like: {value!r}") from exc


def _bool_value(value: Any, *, sheet: str, row_no: int, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(int(value))
    text = _text(value, lower=True)
    if text is None:
        return False
    if text in {"true", "t", "yes", "y", "1"}:
        return True
    if text in {"false", "f", "no", "n", "0"}:
        return False
    raise BundleExportError(f"{sheet}:{row_no} {key} must be boolean-like: {value!r}")


def _split_ids(value: Any) -> list[str]:
    text = _text(value)
    if text is None:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def _read_sheet(workbook: Any, sheet_name: str) -> tuple[list[str], list[tuple[int, dict[str, Any]]]]:
    worksheet = workbook[sheet_name]
    header_row = next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True))
    last_non_blank_idx = -1
    for idx, cell in enumerate(header_row):
        if not _is_blank(cell):
            last_non_blank_idx = idx
    if last_non_blank_idx < 0:
        raise BundleExportError(f"{sheet_name} has no header row")

    headers: list[str] = []
    seen_headers: set[str] = set()
    for idx, cell in enumerate(header_row[: last_non_blank_idx + 1]):
        if _is_blank(cell):
            raise BundleExportError(f"{sheet_name} has blank header in the middle at column {idx + 1}")
        header = str(cell).strip()
        if header in seen_headers:
            raise BundleExportError(f"{sheet_name} has duplicated header: {header}")
        seen_headers.add(header)
        headers.append(header)

    records: list[tuple[int, dict[str, Any]]] = []
    for row_no, values in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        if not values or all(_is_blank(value) for value in values):
            continue
        record = {headers[idx]: values[idx] if idx < len(values) else None for idx in range(len(headers))}
        if all(_is_blank(record.get(header)) for header in headers):
            continue
        records.append((row_no, record))
    return headers, records


def _check_required_structure(workbook: Any) -> None:
    missing_sheets = sorted(REQUIRED_SHEETS - set(workbook.sheetnames))
    if missing_sheets:
        raise BundleExportError(f"Missing required sheet(s): {', '.join(missing_sheets)}")

    for sheet_name, required_columns in REQUIRED_COLUMNS.items():
        headers, _ = _read_sheet(workbook, sheet_name)
        missing_columns = sorted(required_columns - set(headers))
        if missing_columns:
            raise BundleExportError(f"{sheet_name} missing required column(s): {', '.join(missing_columns)}")


def _looks_like_python_regex_literal(pattern: str) -> bool:
    stripped = pattern.strip()
    if re.match(r"^[rRuUfFbB]*(['\"]).*\1$", stripped):
        return True
    return stripped.startswith(("r\"", "r'", "R\"", "R'"))


def _derive_polyset_form(items: list[dict[str, Any]]) -> str:
    forms = [str(item.get("canonical_form") or item["e_id"]) for item in items]
    stripped = [re.sub(r"\d+$", "", form).strip() for form in forms]
    return stripped[0] if stripped and all(form == stripped[0] for form in stripped) else "/".join(forms)


def build_bundle(dict_xlsx: Path) -> dict[str, Any]:
    workbook = load_workbook(dict_xlsx, read_only=True, data_only=True)
    _check_required_structure(workbook)
    warnings: list[str] = []

    _, item_rows = _read_sheet(workbook, "items")
    _, component_rows = _read_sheet(workbook, "rule_components")
    _, rule_rows = _read_sheet(workbook, "detect_rules")

    items_by_e_id: dict[str, dict[str, Any]] = {}
    for row_no, row in item_rows:
        e_id = _required_text(row, "e_id", sheet="items", row_no=row_no)
        if e_id in items_by_e_id:
            raise BundleExportError(f"items.e_id duplicated: {e_id}")
        group = _required_text(row, "group", sheet="items", row_no=row_no, lower=True)
        if group not in VALID_GROUPS:
            raise BundleExportError(f"items:{row_no} group must be one of a/b/c: {group!r}")
        polyset_id = _text(row.get("polyset_id"))
        if group == "c" and polyset_id is None:
            warnings.append(f"items:{row_no} group=c but polyset_id is empty for e_id={e_id}")
        items_by_e_id[e_id] = {
            "e_id": e_id,
            "canonical_form": _required_text(row, "canonical_form", sheet="items", row_no=row_no),
            "group": group,
            "polyset_id": polyset_id,
            "level": _text(row.get("난이도")),
            "topic": _text(row.get("주제")),
            "disconti_allowed": _bool_value(row.get("disconti_allowed"), sheet="items", row_no=row_no, key="disconti_allowed"),
            "e_comp_ids": _split_ids(row.get("e_comp_id")),
            "detect_ruleset_id": _text(row.get("detect_ruleset_id")),
            "verify_ruleset_id": _text(row.get("verify_ruleset_id")),
            "gloss": _text(row.get("gloss")),
        }

    components_by_e_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    referenced_bridge_ids: set[str] = set()
    for row_no, row in component_rows:
        e_id = _required_text(row, "e_id", sheet="rule_components", row_no=row_no)
        if e_id not in items_by_e_id:
            raise BundleExportError(f"rule_components:{row_no} e_id not found in items: {e_id}")
        bridge_id = _text(row.get("bridge_id"))
        if bridge_id is not None:
            if bridge_id not in BRIDGE_REGISTRY:
                known = ", ".join(sorted(BRIDGE_REGISTRY))
                raise BundleExportError(
                    f"rule_components:{row_no} unknown bridge_id={bridge_id!r}; known bridge_id values: {known}"
                )
            referenced_bridge_ids.add(bridge_id)
        order_policy = _text(row.get("order_policy"), lower=True) or "fx"
        if order_policy not in VALID_ORDER_POLICIES:
            allowed = ", ".join(sorted(VALID_ORDER_POLICIES))
            raise BundleExportError(
                f"rule_components:{row_no} order_policy={order_policy!r} invalid; allowed: {allowed}"
            )
        component = {
            "e_id": e_id,
            "comp_surf": _required_text(row, "comp_surf", sheet="rule_components", row_no=row_no),
            "comp_id": _required_text(row, "comp_id", sheet="rule_components", row_no=row_no),
            "is_required": _bool_value(row.get("is_required"), sheet="rule_components", row_no=row_no, key="is_required"),
            "anchor_rank": _int_or_none(row.get("anchor_rank"), sheet="rule_components", row_no=row_no, key="anchor_rank"),
            "comp_order": _int_or_none(row.get("comp_order"), sheet="rule_components", row_no=row_no, key="comp_order"),
            "order_policy": order_policy,
            "min_gap_to_next": _int_or_none(row.get("min_gap_to_next"), sheet="rule_components", row_no=row_no, key="min_gap_to_next"),
            "max_gap_to_next": _int_or_none(row.get("max_gap_to_next"), sheet="rule_components", row_no=row_no, key="max_gap_to_next"),
            "bridge_id": bridge_id,
        }
        components_by_e_id[e_id].append(component)

    for components in components_by_e_id.values():
        components.sort(key=lambda item: (item.get("comp_order") is None, item.get("comp_order") or 0, item["comp_id"]))

    rules_by_ruleset_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen_rule_ids: set[str] = set()
    for row_no, row in rule_rows:
        e_id = _required_text(row, "e_id", sheet="detect_rules", row_no=row_no)
        if e_id not in items_by_e_id:
            raise BundleExportError(f"detect_rules:{row_no} e_id not found in items: {e_id}")
        ruleset_id = _required_text(row, "ruleset_id", sheet="detect_rules", row_no=row_no)
        rule_id = _required_text(row, "rule_id", sheet="detect_rules", row_no=row_no)
        if rule_id in seen_rule_ids:
            raise BundleExportError(f"detect_rules.rule_id duplicated: {rule_id}")
        seen_rule_ids.add(rule_id)

        stage = _required_text(row, "stage", sheet="detect_rules", row_no=row_no, lower=True)
        if stage not in VALID_STAGES:
            raise BundleExportError(f"detect_rules:{row_no} stage must be detect/verify: {stage!r}")
        target = _required_text(row, "target", sheet="detect_rules", row_no=row_no, lower=True)
        if target not in VALID_TARGETS_BY_STAGE[stage]:
            allowed = ", ".join(sorted(VALID_TARGETS_BY_STAGE[stage]))
            raise BundleExportError(f"detect_rules:{row_no} target={target!r} invalid for stage={stage}; allowed: {allowed}")
        pattern = _required_text(row, "pattern", sheet="detect_rules", row_no=row_no)
        try:
            re.compile(pattern)
        except re.error as exc:
            raise BundleExportError(f"detect_rules:{row_no} regex compile failed for rule_id={rule_id}: {exc}") from exc
        if _looks_like_python_regex_literal(pattern):
            warnings.append(f"detect_rules:{row_no} pattern looks like a Python string literal for rule_id={rule_id}")

        hard_fail = _bool_value(row.get("hard_fail"), sheet="detect_rules", row_no=row_no, key="hard_fail")
        if stage == "verify" and not hard_fail:
            warnings.append(f"detect_rules:{row_no} verify rule has hard_fail=false for rule_id={rule_id}")

        rule = {
            "e_id": e_id,
            "ruleset_id": ruleset_id,
            "rule_id": rule_id,
            "stage": stage,
            "target": target,
            "pattern": pattern,
            "priority": _int_or_none(row.get("priority"), sheet="detect_rules", row_no=row_no, key="priority") or 0,
            "hard_fail": hard_fail,
            "rule_type": "surface_regex",
            "engine": "re",
        }
        rules_by_ruleset_id[ruleset_id].append(rule)

    for rules in rules_by_ruleset_id.values():
        rules.sort(key=lambda item: (item["priority"], item["rule_id"]))

    all_ruleset_ids = set(rules_by_ruleset_id)
    for e_id, item in items_by_e_id.items():
        detect_ruleset_id = item.get("detect_ruleset_id")
        verify_ruleset_id = item.get("verify_ruleset_id")
        if detect_ruleset_id:
            detect_rules = [rule for rule in rules_by_ruleset_id.get(detect_ruleset_id, []) if rule.get("stage") == "detect"]
            if not detect_rules:
                raise BundleExportError(f"items e_id={e_id} detect_ruleset_id has no detect rules: {detect_ruleset_id}")
        if verify_ruleset_id:
            verify_rules = [rule for rule in rules_by_ruleset_id.get(verify_ruleset_id, []) if rule.get("stage") == "verify"]
            if not verify_rules:
                raise BundleExportError(f"items e_id={e_id} verify_ruleset_id has no verify rules: {verify_ruleset_id}")

    for ruleset_id, rules in rules_by_ruleset_id.items():
        stages = {rule["stage"] for rule in rules}
        if len(stages) > 1:
            raise BundleExportError(f"ruleset_id contains mixed stages: {ruleset_id} -> {sorted(stages)}")

    referenced_rulesets = {item.get("detect_ruleset_id") for item in items_by_e_id.values()} | {
        item.get("verify_ruleset_id") for item in items_by_e_id.values()
    }
    referenced_rulesets.discard(None)
    for ruleset_id in sorted(all_ruleset_ids - referenced_rulesets):
        warnings.append(f"ruleset_id not referenced by items: {ruleset_id}")

    polyset_members: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items_by_e_id.values():
        polyset_id = item.get("polyset_id")
        if polyset_id:
            polyset_members[polyset_id].append(item)

    polysets_by_id: dict[str, dict[str, Any]] = {}
    for polyset_id, members in sorted(polyset_members.items()):
        member_e_ids = [member["e_id"] for member in members]
        polysets_by_id[polyset_id] = {
            "polyset_id": polyset_id,
            "member_e_ids": member_e_ids,
            "detect_form": _derive_polyset_form(members),
        }

    runtime_units: dict[str, dict[str, Any]] = {}
    for e_id, item in items_by_e_id.items():
        if item["group"] == "c" and item.get("polyset_id"):
            continue
        detect_ruleset_ids = [item["detect_ruleset_id"]] if item.get("detect_ruleset_id") else []
        verify_ruleset_ids = [item["verify_ruleset_id"]] if item.get("verify_ruleset_id") else []
        runtime_units[e_id] = {
            "unit_id": e_id,
            "unit_type": "item",
            "group": item["group"],
            "member_e_ids": [e_id],
            "canonical_form": item["canonical_form"],
            "detect_ruleset_ids": detect_ruleset_ids,
            "verify_ruleset_ids": verify_ruleset_ids,
        }

    for polyset_id, polyset in polysets_by_id.items():
        members = [items_by_e_id[e_id] for e_id in polyset["member_e_ids"]]
        detect_ruleset_ids = [member["detect_ruleset_id"] for member in members if member.get("detect_ruleset_id")]
        verify_ruleset_ids = [member["verify_ruleset_id"] for member in members if member.get("verify_ruleset_id")]
        runtime_units[polyset_id] = {
            "unit_id": polyset_id,
            "unit_type": "polyset",
            "group": "c",
            "member_e_ids": polyset["member_e_ids"],
            "canonical_form": polyset["detect_form"],
            "detect_ruleset_ids": detect_ruleset_ids,
            "verify_ruleset_ids": verify_ruleset_ids,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "dict_xlsx": str(dict_xlsx),
            "source_sha256": _sha256(dict_xlsx),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "items_by_e_id": dict(sorted(items_by_e_id.items())),
        "components_by_e_id": {e_id: components_by_e_id[e_id] for e_id in sorted(components_by_e_id)},
        "bridges_by_id": {
            bridge_id: bridge_metadata_by_id()[bridge_id]
            for bridge_id in sorted(referenced_bridge_ids)
        },
        "rules_by_ruleset_id": {ruleset_id: rules_by_ruleset_id[ruleset_id] for ruleset_id in sorted(rules_by_ruleset_id)},
        "polysets_by_id": polysets_by_id,
        "runtime_units": dict(sorted(runtime_units.items())),
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export HanTalk detector runtime bundle from dict.xlsx.")
    parser.add_argument("--dict", dest="dict_xlsx", type=Path, default=Path("datasets/dict/dict.xlsx"))
    parser.add_argument("--out", type=Path, default=Path("configs/detector/detector_bundle.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        bundle = build_bundle(args.dict_xlsx)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001 - CLI should give a concise fatal message.
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    print(f"bundle={args.out}")
    print(f"schema_version={bundle['schema_version']}")
    print(f"items={len(bundle['items_by_e_id'])}")
    print(f"runtime_units={len(bundle['runtime_units'])}")
    print(f"warnings={len(bundle['warnings'])}")
    for warning in bundle["warnings"]:
        print(f"[WARNING] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
