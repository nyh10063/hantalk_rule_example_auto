"""Minimal runtime DetectorEngine for HanTalk.

This first implementation intentionally uses regex match spans only. It does
not yet assemble educational component spans such as "본 적 ... 있".
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .span_utils import make_char_window, make_span_key, make_span_text, validate_span_segments

RESULT_SCHEMA_VERSION = "hantalk_detector_result_v1"


class DetectorEngine:
    """Detector runtime backed by an exported detector bundle."""

    def __init__(self, bundle: dict[str, Any], *, bundle_path: str | None = None) -> None:
        self.bundle = bundle
        self.bundle_path = bundle_path
        self.runtime_units: dict[str, dict[str, Any]] = bundle.get("runtime_units") or {}
        self.rules_by_ruleset_id: dict[str, list[dict[str, Any]]] = bundle.get("rules_by_ruleset_id") or {}
        self._compiled_rules: dict[str, re.Pattern[str]] = {}
        self._rule_by_id: dict[str, dict[str, Any]] = {}
        self._compile_rules()

    @classmethod
    def from_bundle(cls, bundle_path: str | Path) -> "DetectorEngine":
        path = Path(bundle_path)
        with path.open("r", encoding="utf-8") as f:
            bundle = json.load(f)
        return cls(bundle, bundle_path=str(path))

    def _compile_rules(self) -> None:
        for rules in self.rules_by_ruleset_id.values():
            for rule in rules:
                rule_id = str(rule["rule_id"])
                self._rule_by_id[rule_id] = rule
                self._compiled_rules[rule_id] = re.compile(str(rule["pattern"]))

    def detect(
        self,
        raw_text: str,
        *,
        active_unit_ids: list[str] | None = None,
        text_id: str | None = None,
        profile_id: str | None = None,
        window_chars: int = 20,
    ) -> dict[str, Any]:
        """Detect grammar candidates in raw_text.

        active_unit_ids controls which runtime units are executed. In Phase 1,
        df003 item-unit detection is the supported/tested path.
        """
        units = self._select_units(active_unit_ids)
        raw_candidates: list[dict[str, Any]] = []
        detect_match_count = 0

        for unit in units:
            for ruleset_id in unit.get("detect_ruleset_ids") or []:
                for rule in self._rules_for_ruleset(ruleset_id, stage="detect"):
                    pattern = self._compiled_rules[rule["rule_id"]]
                    for match in pattern.finditer(raw_text):
                        start, end = match.span()
                        if start == end:
                            continue
                        detect_match_count += 1
                        span_segments = validate_span_segments(raw_text, [[start, end]])
                        raw_candidates.append(
                            self._candidate_from_match(
                                raw_text=raw_text,
                                unit=unit,
                                span_segments=span_segments,
                                detect_rule=rule,
                            )
                        )

        merged_candidates = self._merge_candidates(raw_candidates)
        kept_candidates: list[dict[str, Any]] = []
        rejected_candidates: list[dict[str, Any]] = []
        hard_fail_count = 0

        for candidate in merged_candidates:
            hard_fail_rule_ids = self._hard_fail_rule_ids(
                raw_text=raw_text,
                candidate=candidate,
                window_chars=window_chars,
            )
            if hard_fail_rule_ids:
                rejected = dict(candidate)
                rejected["hard_fail_rule_ids"] = hard_fail_rule_ids
                rejected_candidates.append(rejected)
                hard_fail_count += 1
                continue
            kept_candidates.append(candidate)

        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "text_id": text_id,
            "raw_text": raw_text,
            "profile_id": profile_id,
            "active_unit_ids": [unit["unit_id"] for unit in units],
            "candidates": kept_candidates,
            "rejected_candidates": rejected_candidates,
            "summary": {
                "n_detect_matches": detect_match_count,
                "n_candidates_before_verify": len(merged_candidates),
                "n_candidates_after_verify": len(kept_candidates),
                "n_candidates_hard_failed": hard_fail_count,
            },
        }

    def _select_units(self, active_unit_ids: list[str] | None) -> list[dict[str, Any]]:
        if active_unit_ids is None:
            return [self.runtime_units[unit_id] for unit_id in sorted(self.runtime_units)]
        units: list[dict[str, Any]] = []
        for unit_id in active_unit_ids:
            if unit_id not in self.runtime_units:
                raise ValueError(f"Unknown active_unit_id: {unit_id}")
            units.append(self.runtime_units[unit_id])
        return units

    def _rules_for_ruleset(self, ruleset_id: str, *, stage: str) -> list[dict[str, Any]]:
        return [rule for rule in self.rules_by_ruleset_id.get(ruleset_id, []) if rule.get("stage") == stage]

    def _candidate_from_match(
        self,
        *,
        raw_text: str,
        unit: dict[str, Any],
        span_segments: list[list[int]],
        detect_rule: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "unit_id": unit["unit_id"],
            "unit_type": unit["unit_type"],
            "member_e_ids": list(unit.get("member_e_ids") or []),
            "group": unit.get("group"),
            "canonical_form": unit.get("canonical_form"),
            "span_segments": span_segments,
            "span_key": make_span_key(span_segments),
            "span_text": make_span_text(raw_text, span_segments),
            "span_source": "regex_match",
            "component_span_enabled": False,
            "detect_ruleset_ids": list(unit.get("detect_ruleset_ids") or []),
            "verify_ruleset_ids": list(unit.get("verify_ruleset_ids") or []),
            "detect_rule_ids": [detect_rule["rule_id"]],
            "hard_fail_rule_ids": [],
        }

    def _merge_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for candidate in candidates:
            key = (candidate["unit_id"], candidate["span_key"])
            if key not in merged:
                merged[key] = candidate
                continue
            existing = merged[key]
            existing["detect_rule_ids"] = sorted(set(existing["detect_rule_ids"]) | set(candidate["detect_rule_ids"]))
        return list(merged.values())

    def _hard_fail_rule_ids(
        self,
        *,
        raw_text: str,
        candidate: dict[str, Any],
        window_chars: int,
    ) -> list[str]:
        hard_fail_rule_ids: list[str] = []
        for ruleset_id in candidate.get("verify_ruleset_ids") or []:
            for rule in self._rules_for_ruleset(ruleset_id, stage="verify"):
                if not rule.get("hard_fail"):
                    continue
                haystack = raw_text
                if rule.get("target") == "char_window":
                    haystack = str(make_char_window(raw_text, candidate["span_segments"], window_chars=window_chars)["text"])
                pattern = self._compiled_rules[rule["rule_id"]]
                if pattern.search(haystack):
                    hard_fail_rule_ids.append(rule["rule_id"])
        return hard_fail_rule_ids
