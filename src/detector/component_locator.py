"""Component span assembly for detector candidates.

The locator runs only after a detect regex match, and searches within a small
character window around that match. This keeps recall protected by the detect
rule while allowing better educational spans when components can be recovered.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .bridges import BRIDGE_REGISTRY, BridgeMatcher
from .span_utils import DEFAULT_GAP_MARKER, make_span_key, make_span_text, validate_span_segments


@dataclass(frozen=True)
class ComponentCandidate:
    comp_id: str
    span: list[int]
    text: str
    source: str
    bridge_id: str | None = None
    bridge_kind: str | None = None


class ComponentLocator:
    """Assemble component spans for one origin e_id."""

    def __init__(
        self,
        components_by_e_id: dict[str, list[dict[str, Any]]],
        *,
        bridge_registry: dict[str, BridgeMatcher] | None = None,
    ) -> None:
        self.components_by_e_id = components_by_e_id
        self.bridge_registry = bridge_registry or BRIDGE_REGISTRY
        self._surface_patterns: dict[tuple[str, str], re.Pattern[str]] = {}
        self._compile_surface_patterns()

    def _compile_surface_patterns(self) -> None:
        for e_id, components in self.components_by_e_id.items():
            for component in components:
                comp_id = str(component["comp_id"])
                pattern = self._surface_regex(str(component.get("comp_surf") or ""))
                if pattern is not None:
                    self._surface_patterns[(e_id, comp_id)] = pattern

    @staticmethod
    def _surface_regex(comp_surf: str) -> re.Pattern[str] | None:
        parts = [part.strip() for part in comp_surf.split("/") if part.strip()]
        if not parts:
            return None
        escaped = [re.escape(part) for part in sorted(parts, key=len, reverse=True)]
        return re.compile("|".join(escaped))

    def locate(
        self,
        *,
        raw_text: str,
        origin_e_id: str,
        regex_match_span: list[int],
        component_window_chars: int = 20,
        max_candidates_per_component: int = 20,
        max_component_paths: int = 2000,
        include_debug: bool = False,
    ) -> dict[str, Any]:
        """Return component span assembly result for one regex hit."""
        if component_window_chars < 0:
            raise ValueError("component_window_chars must be >= 0")
        if max_candidates_per_component <= 0:
            raise ValueError("max_candidates_per_component must be > 0")
        if max_component_paths <= 0:
            raise ValueError("max_component_paths must be > 0")

        components = [
            component
            for component in self.components_by_e_id.get(origin_e_id, [])
            if bool(component.get("is_required", True))
        ]
        if not components:
            return {"ok": False, "reason": "no_components", "component_span_enabled": False}

        components = sorted(
            components,
            key=lambda component: (
                component.get("comp_order") is None,
                component.get("comp_order") or 0,
                str(component.get("comp_id")),
            ),
        )

        match_start, match_end = int(regex_match_span[0]), int(regex_match_span[1])
        search_start = max(0, match_start - component_window_chars)
        search_end = min(len(raw_text), match_end + component_window_chars)

        candidates_by_comp: dict[str, list[ComponentCandidate]] = {}
        debug: dict[str, Any] = {
            "search_start": search_start,
            "search_end": search_end,
            "candidate_counts": {},
        }
        for component in components:
            comp_id = str(component["comp_id"])
            candidates = self._find_component_candidates(
                raw_text=raw_text,
                origin_e_id=origin_e_id,
                component=component,
                search_start=search_start,
                search_end=search_end,
                regex_match_span=[match_start, match_end],
                max_candidates=max_candidates_per_component,
            )
            candidates_by_comp[comp_id] = candidates
            debug["candidate_counts"][comp_id] = len(candidates)
            if not candidates:
                result = {
                    "ok": False,
                    "reason": "missing_required_component",
                    "failed_required_comp_ids": [comp_id],
                    "component_span_enabled": False,
                }
                if include_debug:
                    result["component_debug"] = debug
                return result

        component_orders = self._component_orders(components)
        debug["component_orders"] = [
            [str(component["comp_id"]) for component in component_order]
            for component_order in component_orders
        ]
        path, paths_considered, truncated = self._select_best_path(
            component_orders,
            candidates_by_comp,
            regex_match_span=[match_start, match_end],
            max_component_paths=max_component_paths,
        )
        debug["paths_considered"] = paths_considered
        debug["paths_truncated"] = truncated
        if path is None:
            result = {
                "ok": False,
                "reason": "no_ordered_component_path",
                "component_span_enabled": False,
            }
            if include_debug:
                result["component_debug"] = debug
            return result

        component_spans = {candidate.comp_id: candidate.span for candidate in path}
        span_segments = self._merge_component_spans(raw_text, [candidate.span for candidate in path])
        span_segments = validate_span_segments(raw_text, span_segments)
        applied_bridge_ids = sorted({candidate.bridge_id for candidate in path if candidate.bridge_id})
        result = {
            "ok": True,
            "span_segments": span_segments,
            "span_key": make_span_key(span_segments),
            "span_text": make_span_text(raw_text, span_segments, gap_marker=DEFAULT_GAP_MARKER),
            "span_source": "component_spans",
            "component_span_enabled": True,
            "component_spans": component_spans,
            "applied_bridge_ids": applied_bridge_ids,
            "component_span_status": "ok",
        }
        if include_debug:
            debug["selected_component_spans"] = component_spans
            result["component_debug"] = debug
        return result

    def _find_component_candidates(
        self,
        *,
        raw_text: str,
        origin_e_id: str,
        component: dict[str, Any],
        search_start: int,
        search_end: int,
        regex_match_span: list[int],
        max_candidates: int,
    ) -> list[ComponentCandidate]:
        comp_id = str(component["comp_id"])
        seen: set[tuple[int, int]] = set()
        candidates: list[ComponentCandidate] = []

        pattern = self._surface_patterns.get((origin_e_id, comp_id))
        if pattern is not None:
            window = raw_text[search_start:search_end]
            for match in pattern.finditer(window):
                start = search_start + match.start()
                end = search_start + match.end()
                key = (start, end)
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(
                    ComponentCandidate(
                        comp_id=comp_id,
                        span=[start, end],
                        text=raw_text[start:end],
                        source="surface",
                    )
                )

        bridge_id = component.get("bridge_id")
        if bridge_id:
            bridge = self.bridge_registry.get(str(bridge_id))
            if bridge is not None:
                for match in bridge.find(
                    raw_text=raw_text,
                    search_start=search_start,
                    search_end=search_end,
                    component=component,
                ):
                    start, end = int(match["span"][0]), int(match["span"][1])
                    key = (start, end)
                    if key in seen:
                        continue
                    seen.add(key)
                    candidates.append(
                        ComponentCandidate(
                            comp_id=comp_id,
                            span=[start, end],
                            text=raw_text[start:end],
                            source="bridge",
                            bridge_id=str(bridge_id),
                            bridge_kind=match.get("bridge_kind"),
                        )
                    )

        candidates.sort(key=lambda candidate: self._candidate_score(candidate, regex_match_span))
        return candidates[:max_candidates]

    @staticmethod
    def _candidate_score(candidate: ComponentCandidate, regex_match_span: list[int]) -> tuple[int, int, int]:
        start, end = candidate.span
        match_start, match_end = regex_match_span
        if start < match_end and end > match_start:
            distance = 0
        elif end <= match_start:
            distance = match_start - end
        else:
            distance = start - match_end
        source_penalty = 0 if candidate.source == "surface" else 1
        return (distance, source_penalty, start)

    @classmethod
    def _component_orders(cls, components: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Return component-order variants allowed by order_policy.

        fx is fixed. fl allows only one adjacent swap with another fl component.
        The anchor component keeps its base comp_order position.
        """
        base = list(components)
        orders: list[list[dict[str, Any]]] = [base]
        anchor_comp_id = cls._anchor_comp_id(base)
        anchor_index = cls._component_index(base, anchor_comp_id)
        seen = {tuple(str(component["comp_id"]) for component in base)}

        for idx in range(len(base) - 1):
            left = base[idx]
            right = base[idx + 1]
            if not cls._can_swap_adjacent(left, right, anchor_comp_id):
                continue
            swapped = list(base)
            swapped[idx], swapped[idx + 1] = swapped[idx + 1], swapped[idx]
            if anchor_index is not None and cls._component_index(swapped, anchor_comp_id) != anchor_index:
                continue
            key = tuple(str(component["comp_id"]) for component in swapped)
            if key in seen:
                continue
            seen.add(key)
            orders.append(swapped)
        return orders

    @staticmethod
    def _order_policy(component: dict[str, Any]) -> str:
        policy = str(component.get("order_policy") or "fx").strip().lower()
        return policy or "fx"

    @staticmethod
    def _anchor_comp_id(components: list[dict[str, Any]]) -> str | None:
        ranked = [
            component
            for component in components
            if component.get("anchor_rank") is not None
        ]
        if not ranked:
            return None
        # Higher anchor_rank means a stronger anchor in the migrated dict.
        anchor = max(
            ranked,
            key=lambda component: (
                int(component.get("anchor_rank") or 0),
                -int(component.get("comp_order") or 0),
                str(component.get("comp_id")),
            ),
        )
        return str(anchor["comp_id"])

    @staticmethod
    def _component_index(components: list[dict[str, Any]], comp_id: str | None) -> int | None:
        if comp_id is None:
            return None
        for idx, component in enumerate(components):
            if str(component["comp_id"]) == comp_id:
                return idx
        return None

    @classmethod
    def _can_swap_adjacent(
        cls,
        left: dict[str, Any],
        right: dict[str, Any],
        anchor_comp_id: str | None,
    ) -> bool:
        if str(left["comp_id"]) == anchor_comp_id or str(right["comp_id"]) == anchor_comp_id:
            return False
        return cls._order_policy(left) == "fl" and cls._order_policy(right) == "fl"

    def _select_best_path(
        self,
        component_orders: list[list[dict[str, Any]]],
        candidates_by_comp: dict[str, list[ComponentCandidate]],
        *,
        regex_match_span: list[int],
        max_component_paths: int,
    ) -> tuple[list[ComponentCandidate] | None, int, bool]:
        best_path: list[ComponentCandidate] | None = None
        best_score: tuple[int, int, int, int] | None = None
        total_paths_considered = 0
        truncated = False

        for component_order in component_orders:
            remaining_paths = max_component_paths - total_paths_considered
            if remaining_paths <= 0:
                truncated = True
                break
            path, paths_considered, order_truncated = self._select_path_for_order(
                component_order,
                candidates_by_comp,
                regex_match_span=regex_match_span,
                max_component_paths=remaining_paths,
            )
            total_paths_considered += paths_considered
            truncated = truncated or order_truncated
            if path is None:
                continue
            score = self._path_score(path, regex_match_span)
            if best_score is None or score < best_score:
                best_score = score
                best_path = path

        return best_path, total_paths_considered, truncated

    def _select_path_for_order(
        self,
        components: list[dict[str, Any]],
        candidates_by_comp: dict[str, list[ComponentCandidate]],
        *,
        regex_match_span: list[int],
        max_component_paths: int,
    ) -> tuple[list[ComponentCandidate] | None, int, bool]:
        best_path: list[ComponentCandidate] | None = None
        best_score: tuple[int, int, int, int] | None = None
        paths_considered = 0
        truncated = False

        def walk(idx: int, path: list[ComponentCandidate]) -> None:
            nonlocal best_path, best_score, paths_considered, truncated
            if paths_considered >= max_component_paths:
                truncated = True
                return
            if idx >= len(components):
                paths_considered += 1
                score = self._path_score(path, regex_match_span)
                if best_score is None or score < best_score:
                    best_score = score
                    best_path = list(path)
                return

            component = components[idx]
            comp_id = str(component["comp_id"])
            previous = path[-1] if path else None
            previous_component = components[idx - 1] if idx > 0 else None

            for candidate in candidates_by_comp.get(comp_id, []):
                if previous is not None and not self._is_valid_next(previous, candidate, previous_component):
                    continue
                path.append(candidate)
                walk(idx + 1, path)
                path.pop()

        walk(0, [])
        return best_path, paths_considered, truncated

    @staticmethod
    def _is_valid_next(
        previous: ComponentCandidate,
        current: ComponentCandidate,
        previous_component: dict[str, Any] | None,
    ) -> bool:
        if previous.span[1] > current.span[0]:
            return False
        if previous_component is None:
            return True
        gap = current.span[0] - previous.span[1]
        min_gap = previous_component.get("min_gap_to_next")
        max_gap = previous_component.get("max_gap_to_next")
        if min_gap is not None and gap < int(min_gap):
            return False
        if max_gap is not None and gap > int(max_gap):
            return False
        return True

    @staticmethod
    def _path_score(path: list[ComponentCandidate], regex_match_span: list[int]) -> tuple[int, int, int, int]:
        distances = [ComponentLocator._candidate_score(candidate, regex_match_span)[0] for candidate in path]
        total_gap = sum(
            max(0, current.span[0] - previous.span[1])
            for previous, current in zip(path, path[1:])
        )
        bridge_count = sum(1 for candidate in path if candidate.source == "bridge")
        start = path[0].span[0] if path else 0
        return (sum(distances), total_gap, bridge_count, start)

    @staticmethod
    def _merge_component_spans(raw_text: str, spans: list[list[int]]) -> list[list[int]]:
        ordered = sorted(([int(start), int(end)] for start, end in spans), key=lambda item: (item[0], item[1]))
        if not ordered:
            return []
        merged: list[list[int]] = []
        current_start, current_end = ordered[0]
        for start, end in ordered[1:]:
            gap_text = raw_text[current_end:start]
            if gap_text.strip() == "":
                current_end = end
                continue
            merged.append([current_start, current_end])
            current_start, current_end = start, end
        merged.append([current_start, current_end])
        return merged
