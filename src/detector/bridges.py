"""Shared component bridge matchers for HanTalk detector.

Bridges recover component spans that are not always present as independent
surface strings. They return component-span candidates only; DetectorEngine
still owns candidate creation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class BridgeMetadata:
    bridge_id: str
    version: str
    requires_morph: bool
    description: str


class BridgeMatcher(Protocol):
    metadata: BridgeMetadata

    def find(
        self,
        *,
        raw_text: str,
        search_start: int,
        search_end: int,
        component: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return possible spans for one component inside [search_start, search_end)."""


def _has_final_n_syllable(ch: str) -> bool:
    """Return True if a Hangul syllable has jongseong ㄴ."""
    if len(ch) != 1:
        return False
    code = ord(ch) - 0xAC00
    if code < 0 or code >= 11172:
        return False
    return code % 28 == 4


class AdnominalNBridge:
    """Find ㄴ/은 adnominal component spans with lightweight character logic."""

    metadata = BridgeMetadata(
        bridge_id="adnominal_n",
        version="v1",
        requires_morph=False,
        description="Recover ㄴ/은 adnominal component spans, including final-ㄴ syllables such as 본/간/한.",
    )

    _explicit_pattern = re.compile(r"[ㄴᆫ]|은")

    def find(
        self,
        *,
        raw_text: str,
        search_start: int,
        search_end: int,
        component: dict[str, Any],
    ) -> list[dict[str, Any]]:
        del component
        matches: list[dict[str, Any]] = []
        window = raw_text[search_start:search_end]
        seen: set[tuple[int, int]] = set()

        for match in self._explicit_pattern.finditer(window):
            start = search_start + match.start()
            end = search_start + match.end()
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                {
                    "span": [start, end],
                    "text": raw_text[start:end],
                    "source": "bridge",
                    "bridge_id": self.metadata.bridge_id,
                    "bridge_kind": "explicit",
                }
            )

        for offset, ch in enumerate(window):
            if not _has_final_n_syllable(ch):
                continue
            start = search_start + offset
            end = start + 1
            key = (start, end)
            if key in seen:
                continue
            seen.add(key)
            matches.append(
                {
                    "span": [start, end],
                    "text": raw_text[start:end],
                    "source": "bridge",
                    "bridge_id": self.metadata.bridge_id,
                    "bridge_kind": "final_n_syllable",
                }
            )

        return matches


class ThingBridge:
    """Find common 것 variants as one component span."""

    metadata = BridgeMetadata(
        bridge_id="thing",
        version="v1",
        requires_morph=False,
        description="Find 것/거/게/건/걸 variants for future dependent-noun component rules.",
    )

    _pattern = re.compile(r"것|거|게|건|걸")

    def find(
        self,
        *,
        raw_text: str,
        search_start: int,
        search_end: int,
        component: dict[str, Any],
    ) -> list[dict[str, Any]]:
        del component
        window = raw_text[search_start:search_end]
        return [
            {
                "span": [search_start + match.start(), search_start + match.end()],
                "text": match.group(0),
                "source": "bridge",
                "bridge_id": self.metadata.bridge_id,
                "bridge_kind": "thing_variant",
            }
            for match in self._pattern.finditer(window)
        ]


BRIDGE_REGISTRY: dict[str, BridgeMatcher] = {
    "adnominal_n": AdnominalNBridge(),
    "thing": ThingBridge(),
}


def bridge_metadata_by_id() -> dict[str, dict[str, Any]]:
    """Return JSON-serializable bridge metadata."""
    return {
        bridge_id: {
            "bridge_id": matcher.metadata.bridge_id,
            "version": matcher.metadata.version,
            "requires_morph": matcher.metadata.requires_morph,
            "description": matcher.metadata.description,
        }
        for bridge_id, matcher in sorted(BRIDGE_REGISTRY.items())
    }
