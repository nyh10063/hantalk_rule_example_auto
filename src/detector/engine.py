"""Runtime DetectorEngine for HanTalk."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .component_locator import ComponentLocator
from .span_utils import DEFAULT_GAP_MARKER, make_char_window, make_span_key, make_span_text, validate_span_segments

RESULT_SCHEMA_VERSION = "hantalk_detector_result_v1"


class DetectorEngine:
    """Detector runtime backed by an exported detector bundle."""

    def __init__(self, bundle: dict[str, Any], *, bundle_path: str | None = None) -> None:
        self.bundle = bundle
        self.bundle_path = bundle_path
        self.runtime_units: dict[str, dict[str, Any]] = bundle.get("runtime_units") or {}
        self.rules_by_ruleset_id: dict[str, list[dict[str, Any]]] = bundle.get("rules_by_ruleset_id") or {}
        self.components_by_e_id: dict[str, list[dict[str, Any]]] = bundle.get("components_by_e_id") or {}
        self.component_locator = ComponentLocator(self.components_by_e_id)
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
        allow_all: bool = False,
        allow_polyset: bool = False,
        allow_experimental_polyset: bool = False,
        max_matches_per_rule: int = 50,
        max_candidates_per_component: int = 20,
        max_component_paths: int = 2000,
        text_id: str | None = None,
        profile_id: str | None = None,
        window_chars: int = 20,
        component_window_chars: int = 20,
        include_debug: bool = False,
        realtime: bool = False,
    ) -> dict[str, Any]:
        """Detect grammar candidates in raw_text.

        active_unit_ids controls which runtime task units are executed. A task
        unit may be a legacy e_id item unit, a single-member ps_id wrapper, or
        a multi-member ps_id polyset.
        """
        if realtime:
            include_debug = False
        units = self._select_units(
            active_unit_ids,
            allow_all=allow_all,
            allow_polyset=allow_polyset,
            allow_experimental_polyset=allow_experimental_polyset,
        )
        raw_candidates: list[dict[str, Any]] = []
        detect_match_count = 0
        truncated_match_count = 0
        truncated_rules: list[dict[str, Any]] = []

        for unit in units:
            for ruleset_id in unit.get("detect_ruleset_ids") or []:
                for rule in self._rules_for_ruleset(ruleset_id, stage="detect"):
                    pattern = self._compiled_rules[rule["rule_id"]]
                    rule_match_count = 0
                    for match in pattern.finditer(raw_text):
                        if rule_match_count >= max_matches_per_rule:
                            truncated_match_count += 1
                            truncated_rules.append(
                                {
                                    "unit_id": unit["unit_id"],
                                    "rule_id": rule["rule_id"],
                                    "max_matches_per_rule": max_matches_per_rule,
                                }
                            )
                            break
                        start, end = match.span()
                        if start == end:
                            continue
                        rule_match_count += 1
                        detect_match_count += 1
                        raw_candidates.append(
                            self._candidate_from_match(
                                raw_text=raw_text,
                                unit=unit,
                                regex_match_span=[start, end],
                                detect_rule=rule,
                                component_window_chars=component_window_chars,
                                max_candidates_per_component=max_candidates_per_component,
                                max_component_paths=max_component_paths,
                                include_debug=include_debug,
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

        hidden_realtime_count = 0
        if realtime:
            visible_candidates: list[dict[str, Any]] = []
            for candidate in kept_candidates:
                if candidate.get("span_source") == "regex_match_fallback":
                    hidden_realtime_count += 1
                    continue
                visible_candidates.append(self._strip_realtime_fields(candidate))
            kept_candidates = visible_candidates
            rejected_candidates = []

        component_summary = self._component_span_summary(kept_candidates)
        component_summary_before_verify = self._component_span_summary(merged_candidates)

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
                "n_matches_truncated": truncated_match_count,
                "truncated_rules": truncated_rules,
                "n_candidates_hidden_realtime": hidden_realtime_count,
                "realtime": realtime,
                "n_component_span_success": component_summary["component_spans"],
                "n_component_span_fallback": component_summary["regex_match_fallback"],
                "n_component_span_regex_only": component_summary["regex_match"],
                "span_source_counts": component_summary,
                "span_source_counts_before_verify": component_summary_before_verify,
            },
        }

    def _select_units(
        self,
        active_unit_ids: list[str] | None,
        *,
        allow_all: bool,
        allow_polyset: bool,
        allow_experimental_polyset: bool,
    ) -> list[dict[str, Any]]:
        if active_unit_ids is None:
            if not allow_all:
                raise ValueError("active_unit_ids is required unless allow_all=True")
            active_unit_ids = sorted(self.runtime_units)
        units: list[dict[str, Any]] = []
        for unit_id in active_unit_ids:
            if unit_id not in self.runtime_units:
                raise ValueError(f"Unknown active_unit_id: {unit_id}")
            unit = self.runtime_units[unit_id]
            if unit.get("unit_type") == "polyset" and not (allow_polyset or allow_experimental_polyset):
                raise ValueError(
                    f"Polyset runtime unit is disabled unless explicitly allowed: {unit_id}. "
                    "Pass allow_polyset=True for multi-member ps_id task units."
                )
            units.append(unit)
        return units

    def _rules_for_ruleset(self, ruleset_id: str, *, stage: str) -> list[dict[str, Any]]:
        return [rule for rule in self.rules_by_ruleset_id.get(ruleset_id, []) if rule.get("stage") == stage]

    def _candidate_from_match(
        self,
        *,
        raw_text: str,
        unit: dict[str, Any],
        regex_match_span: list[int],
        detect_rule: dict[str, Any],
        component_window_chars: int,
        max_candidates_per_component: int,
        max_component_paths: int,
        include_debug: bool,
    ) -> dict[str, Any]:
        regex_span_segments = validate_span_segments(raw_text, [regex_match_span])
        origin_e_id = str(detect_rule["e_id"])
        component_result = self.component_locator.locate(
            raw_text=raw_text,
            origin_e_id=origin_e_id,
            regex_match_span=regex_match_span,
            component_window_chars=component_window_chars,
            max_candidates_per_component=max_candidates_per_component,
            max_component_paths=max_component_paths,
            include_debug=include_debug,
        )

        if component_result.get("ok"):
            span_segments = component_result["span_segments"]
            span_source = "component_spans"
            component_span_enabled = True
            component_span_status = "ok"
            component_spans = component_result.get("component_spans") or {}
            partial_component_spans = {}
            partial_span_segments: list[list[int]] = []
            partial_span_text = ""
            matched_component_ids = sorted(component_spans)
            missing_required_component_ids: list[str] = []
            applied_bridge_ids = component_result.get("applied_bridge_ids") or []
        else:
            span_segments = regex_span_segments
            reason = str(component_result.get("reason") or "component_span_not_available")
            span_source = "regex_match" if reason == "no_components" else "regex_match_fallback"
            component_span_enabled = False
            component_span_status = str(component_result.get("component_span_status") or reason)
            component_spans = {}
            partial_component_spans = component_result.get("partial_component_spans") or {}
            partial_span_segments = component_result.get("partial_span_segments") or []
            partial_span_text = str(component_result.get("partial_span_text") or "")
            matched_component_ids = list(component_result.get("matched_component_ids") or [])
            missing_required_component_ids = list(component_result.get("missing_required_component_ids") or [])
            applied_bridge_ids = []

        candidate = {
            "origin_e_id": origin_e_id,
            "unit_id": unit["unit_id"],
            "unit_type": unit["unit_type"],
            "member_e_ids": list(unit.get("member_e_ids") or []),
            "group": unit.get("group"),
            "canonical_form": unit.get("canonical_form"),
            "regex_match_span": regex_match_span,
            "regex_match_text": raw_text[int(regex_match_span[0]) : int(regex_match_span[1])],
            "span_segments": span_segments,
            "span_key": make_span_key(span_segments),
            "span_text": make_span_text(raw_text, span_segments, gap_marker=DEFAULT_GAP_MARKER),
            "span_source": span_source,
            "component_span_enabled": component_span_enabled,
            "component_span_status": component_span_status,
            "component_spans": component_spans,
            "partial_component_spans": partial_component_spans,
            "partial_span_segments": partial_span_segments,
            "partial_span_key": str(component_result.get("partial_span_key") or ""),
            "partial_span_text": partial_span_text,
            "matched_component_ids": matched_component_ids,
            "missing_required_component_ids": missing_required_component_ids,
            "applied_bridge_ids": applied_bridge_ids,
            "detect_ruleset_ids": list(unit.get("detect_ruleset_ids") or []),
            "verify_ruleset_ids": list(unit.get("verify_ruleset_ids") or []),
            "detect_rule_ids": [detect_rule["rule_id"]],
            "hard_fail_rule_ids": [],
        }
        if include_debug and component_result.get("component_debug"):
            candidate["component_debug"] = component_result["component_debug"]
        return candidate

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
                elif rule.get("target") == "component_right_context":
                    haystack = self._component_right_context(
                        raw_text=raw_text,
                        candidate=candidate,
                        rule=rule,
                    )
                    if haystack is None:
                        continue
                elif rule.get("target") == "component_left_context":
                    haystack = self._component_left_context(
                        raw_text=raw_text,
                        candidate=candidate,
                        rule=rule,
                    )
                    if haystack is None:
                        continue
                elif rule.get("target") == "component_text":
                    haystack = self._component_text(
                        raw_text=raw_text,
                        candidate=candidate,
                        rule=rule,
                    )
                    if haystack is None:
                        continue
                elif rule.get("target") == "left_plus_component_text":
                    haystack = self._left_plus_component_text(
                        raw_text=raw_text,
                        candidate=candidate,
                        rule=rule,
                    )
                    if haystack is None:
                        continue
                pattern = self._compiled_rules[rule["rule_id"]]
                if pattern.search(haystack):
                    hard_fail_rule_ids.append(rule["rule_id"])
        return hard_fail_rule_ids

    @classmethod
    def _component_right_context(
        cls,
        *,
        raw_text: str,
        candidate: dict[str, Any],
        rule: dict[str, Any],
    ) -> str | None:
        """Return the first non-space character to the right of a component span.

        If the candidate has no component span for the requested component_id,
        the verify rule is skipped to protect recall.
        """
        span = cls._component_span(candidate=candidate, rule=rule)
        if span is None:
            return None
        component_end = int(span[1])
        for idx in range(component_end, len(raw_text)):
            ch = raw_text[idx]
            if not ch.isspace():
                return ch
        return ""

    @classmethod
    def _component_left_context(
        cls,
        *,
        raw_text: str,
        candidate: dict[str, Any],
        rule: dict[str, Any],
    ) -> str | None:
        """Return the first non-space character to the left of a component span."""
        span = cls._component_span(candidate=candidate, rule=rule)
        if span is None:
            return None
        component_start = int(span[0])
        for idx in range(component_start - 1, -1, -1):
            ch = raw_text[idx]
            if not ch.isspace():
                return ch
        return ""

    @classmethod
    def _component_text(
        cls,
        *,
        raw_text: str,
        candidate: dict[str, Any],
        rule: dict[str, Any],
    ) -> str | None:
        """Return the selected component span text."""
        span = cls._component_span(candidate=candidate, rule=rule)
        if span is None:
            return None
        return raw_text[int(span[0]) : int(span[1])]

    @classmethod
    def _left_plus_component_text(
        cls,
        *,
        raw_text: str,
        candidate: dict[str, Any],
        rule: dict[str, Any],
    ) -> str | None:
        """Return left one-character context concatenated with component text."""
        left = cls._component_left_context(raw_text=raw_text, candidate=candidate, rule=rule)
        text = cls._component_text(raw_text=raw_text, candidate=candidate, rule=rule)
        if left is None or text is None:
            return None
        return f"{left}{text}"

    @staticmethod
    def _component_span(
        *,
        candidate: dict[str, Any],
        rule: dict[str, Any],
    ) -> list[int] | None:
        """Return full or partial component span for a component-scoped verify rule."""
        component_id = rule.get("component_id")
        if not component_id:
            return None
        component_spans = candidate.get("component_spans") or {}
        span = component_spans.get(str(component_id))
        if not span:
            partial_component_spans = candidate.get("partial_component_spans") or {}
            span = partial_component_spans.get(str(component_id))
        if not span or len(span) != 2:
            return None
        return [int(span[0]), int(span[1])]

    @staticmethod
    def _strip_realtime_fields(candidate: dict[str, Any]) -> dict[str, Any]:
        """Hide offline-only analysis fields from realtime output."""
        stripped = dict(candidate)
        for key in [
            "partial_component_spans",
            "partial_span_segments",
            "partial_span_key",
            "partial_span_text",
            "matched_component_ids",
            "missing_required_component_ids",
            "component_debug",
        ]:
            stripped.pop(key, None)
        return stripped

    @staticmethod
    def _component_span_summary(candidates: list[dict[str, Any]]) -> dict[str, int]:
        summary = {
            "component_spans": 0,
            "regex_match_fallback": 0,
            "regex_match": 0,
            "other": 0,
        }
        for candidate in candidates:
            span_source = str(candidate.get("span_source") or "")
            if span_source in summary:
                summary[span_source] += 1
            else:
                summary["other"] += 1
        return summary
