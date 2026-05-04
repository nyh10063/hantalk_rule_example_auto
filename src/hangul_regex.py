#!/usr/bin/env python3
"""Small Hangul regex helpers.

This module intentionally generates only mechanical regex parts, such as a
character class for Hangul syllables with a specific jongseong. It must not
decide a grammar item's full detect regex.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

HANGUL_SYLLABLE_BASE = 0xAC00
HANGUL_SYLLABLE_COUNT = 11172
N_JUNGSEONG = 21
N_JONGSEONG = 28

JONGSEONG_INDEX_BY_JAMO = {
    "": 0,
    "ㄱ": 1,
    "ㄲ": 2,
    "ㄳ": 3,
    "ㄴ": 4,
    "ㄵ": 5,
    "ㄶ": 6,
    "ㄷ": 7,
    "ㄹ": 8,
    "ㄺ": 9,
    "ㄻ": 10,
    "ㄼ": 11,
    "ㄽ": 12,
    "ㄾ": 13,
    "ㄿ": 14,
    "ㅀ": 15,
    "ㅁ": 16,
    "ㅂ": 17,
    "ㅄ": 18,
    "ㅅ": 19,
    "ㅆ": 20,
    "ㅇ": 21,
    "ㅈ": 22,
    "ㅊ": 23,
    "ㅋ": 24,
    "ㅌ": 25,
    "ㅍ": 26,
    "ㅎ": 27,
}


def jongseong_index(jongseong: str) -> int:
    """Return the Unicode Hangul jongseong index for a compatibility jamo."""
    try:
        return JONGSEONG_INDEX_BY_JAMO[jongseong]
    except KeyError as exc:
        allowed = ", ".join(repr(key) for key in JONGSEONG_INDEX_BY_JAMO if key)
        raise ValueError(f"Unsupported jongseong {jongseong!r}. Allowed values: {allowed}") from exc


def has_jongseong(ch: str, jongseong: str) -> bool:
    """Return True if one Hangul syllable has the requested jongseong."""
    if len(ch) != 1:
        return False
    code = ord(ch) - HANGUL_SYLLABLE_BASE
    if code < 0 or code >= HANGUL_SYLLABLE_COUNT:
        return False
    return code % N_JONGSEONG == jongseong_index(jongseong)


def syllables_with_jongseong(jongseong: str) -> str:
    """Return all modern Hangul syllables with the requested jongseong."""
    index = jongseong_index(jongseong)
    if index == 0:
        raise ValueError("Empty jongseong cannot be represented as a useful regex character class")
    return "".join(
        chr(HANGUL_SYLLABLE_BASE + ((lead * N_JUNGSEONG + vowel) * N_JONGSEONG + index))
        for lead in range(19)
        for vowel in range(N_JUNGSEONG)
    )


def jongseong_char_class(jongseong: str) -> str:
    """Return a regex character class for syllables with the requested jongseong."""
    return f"[{syllables_with_jongseong(jongseong)}]"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jongseong", required=True, help="Compatibility jamo, e.g. ㄴ or ㄹ")
    parser.add_argument("--suffix", default="", help="Optional literal suffix appended after the char class")
    parser.add_argument("--json", action="store_true", help="Print metadata and regex as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        char_class = jongseong_char_class(args.jongseong)
        regex_part = f"{char_class}{args.suffix}"
        re.compile(regex_part)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "jongseong": args.jongseong,
                    "n_syllables": len(syllables_with_jongseong(args.jongseong)),
                    "regex": regex_part,
                    "note": "Mechanical regex part only. Full detect regex remains human/Codex-reviewed.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(regex_part)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
