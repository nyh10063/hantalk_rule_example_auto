#!/usr/bin/env python3
"""Prepare a shared example-making corpus batch.

Input files are lightweight `text;source` style TSV/CSV-like text files.
The script keeps memory bounded by stable-hash streaming sampling per domain.
"""

from __future__ import annotations

import argparse
import heapq
import hashlib
import json
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_HEADER_CANDIDATES = {"sentence", "form", "text", "raw_text"}
SOURCE_HEADER_CANDIDATES = {"source"}
HASH_METHOD = "sha256(seed|domain|source_file|source_line_no|raw_text)"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def _resolve_file(root: Path, manifest_name: str) -> Path:
    direct = root / manifest_name
    if direct.exists():
        return direct

    wanted = {
        unicodedata.normalize("NFC", manifest_name),
        unicodedata.normalize("NFD", manifest_name),
    }
    for candidate in root.iterdir():
        if not candidate.is_file():
            continue
        names = {
            unicodedata.normalize("NFC", candidate.name),
            unicodedata.normalize("NFD", candidate.name),
        }
        if wanted & names:
            return candidate
    raise FileNotFoundError(f"Corpus file not found under {root}: {manifest_name}")


def _looks_like_header(line: str, delimiter: str) -> bool:
    parts = [part.strip().lower() for part in line.rstrip("\n").split(delimiter)]
    return bool(set(parts) & (TEXT_HEADER_CANDIDATES | SOURCE_HEADER_CANDIDATES))


def _header_info(line: str, delimiter: str) -> dict[str, Any]:
    columns = [part.strip() for part in line.rstrip("\n").split(delimiter)]
    lowered = [part.lower() for part in columns]
    text_column = next((col for col in lowered if col in TEXT_HEADER_CANDIDATES), None)
    source_column = next((col for col in lowered if col in SOURCE_HEADER_CANDIDATES), None)
    return {
        "columns": columns,
        "text_column": text_column,
        "source_column": source_column,
        "mode": "header" if text_column or source_column else "fallback_first_last",
    }


def _parse_data_line(line: str, delimiter: str) -> tuple[str | None, str | None]:
    stripped = line.rstrip("\n")
    if not stripped:
        return None, None
    if delimiter not in stripped:
        return None, None
    text, source = stripped.rsplit(delimiter, 1)
    text = text.strip()
    source = source.strip()
    if not text:
        return "", source
    return text, source


def _hash_record(*, seed: int, domain: str, source_file: str, source_line_no: int, raw_text: str) -> tuple[int, str]:
    payload = f"{seed}\t{domain}\t{source_file}\t{source_line_no}\t{raw_text}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest, 16), digest


def _candidate_record(
    *,
    seed: int,
    batch_id: str,
    batch_index: int,
    domain: str,
    source_file: str,
    source_row_index: int,
    source_line_no: int,
    raw_text: str,
    source: str,
) -> tuple[int, str, dict[str, Any]]:
    hash_int, hash_hex = _hash_record(
        seed=seed,
        domain=domain,
        source_file=source_file,
        source_line_no=source_line_no,
        raw_text=raw_text,
    )
    record = {
        "text_id": None,
        "batch_id": batch_id,
        "batch_index": batch_index,
        "corpus_domain": domain,
        "source": source,
        "source_file": source_file,
        "source_row_index": source_row_index,
        "source_line_no": source_line_no,
        "sample_hash": hash_hex,
        "raw_text": raw_text,
    }
    return hash_int, hash_hex, record


def _sample_domain(
    *,
    domain: str,
    file_path: Path,
    requested: int,
    rank_start: int,
    batch_id: str,
    batch_index: int,
    seed: int,
    delimiter: str,
    encoding: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if requested <= 0:
        raise ValueError(f"sampling size must be positive for domain={domain}: {requested}")
    if rank_start < 0:
        raise ValueError(f"rank_start must be >= 0 for domain={domain}: {rank_start}")
    start = rank_start
    end = start + requested
    keep_count = end
    if keep_count <= 0:
        raise ValueError(f"keep_count must be positive for domain={domain}: {keep_count}")

    heap: list[tuple[int, str, dict[str, Any]]] = []
    n_seen = 0
    n_valid = 0
    n_empty = 0
    n_parse_error = 0
    header: dict[str, Any] | None = None
    has_header = False
    data_row_index = -1

    with file_path.open("r", encoding=encoding, errors="replace") as f:
        first_line = f.readline()
        if first_line:
            has_header = _looks_like_header(first_line, delimiter)
            header = _header_info(first_line, delimiter) if has_header else None
            if not has_header:
                f.seek(0)
        for source_line_no, line in enumerate(f, start=2 if has_header else 1):
            n_seen += 1
            data_row_index += 1
            raw_text, source = _parse_data_line(line, delimiter)
            if raw_text is None:
                n_parse_error += 1
                continue
            if not raw_text:
                n_empty += 1
                continue
            n_valid += 1
            hash_int, hash_hex, record = _candidate_record(
                seed=seed,
                batch_id=batch_id,
                batch_index=batch_index,
                domain=domain,
                source_file=file_path.name,
                source_row_index=data_row_index,
                source_line_no=source_line_no,
                raw_text=raw_text,
                source=source or "",
            )
            # Max-heap simulated with negative hash. Keep the smallest hashes.
            item = (-hash_int, f"{source_line_no:012d}:{hash_hex}", record)
            if len(heap) < keep_count:
                heapq.heappush(heap, item)
            elif hash_int < -heap[0][0]:
                heapq.heapreplace(heap, item)

    candidates = sorted(((-neg_hash, tie, record) for neg_hash, tie, record in heap), key=lambda item: (item[0], item[1]))
    selected = [record for _, _, record in candidates[start:end]]
    for idx, record in enumerate(selected, start=1):
        record["text_id"] = f"{domain}_b{batch_index:03d}_{idx:06d}"

    selected_hashes = [record["sample_hash"] for record in selected]
    report = {
        "domain": domain,
        "source_file": str(file_path),
        "requested": requested,
        "batch_index": batch_index,
        "rank_start": start,
        "rank_end_exclusive": end,
        "keep_count": keep_count,
        "header_detected": has_header,
        "header": header,
        "n_rows_seen": n_seen,
        "n_rows_valid": n_valid,
        "n_rows_selected": len(selected),
        "n_rows_skipped_empty": n_empty,
        "n_rows_skipped_parse_error": n_parse_error,
        "selected_hash_min": min(selected_hashes) if selected_hashes else None,
        "selected_hash_max": max(selected_hashes) if selected_hashes else None,
        "warning": None if len(selected) == requested else f"selected {len(selected)} rows, requested {requested}",
    }
    return selected, report


def _select_sampling_schedule(manifest: dict[str, Any], batch_index: int) -> dict[str, Any]:
    schedules = manifest.get("sampling_schedules") or []
    if not schedules:
        return {
            "schedule_id": "default",
            "start_batch_index": 0,
            "sampling": manifest.get("sampling") or {},
            "rank_start_offsets": {},
        }

    matched: dict[str, Any] | None = None
    for schedule in schedules:
        start_batch_index = int(schedule.get("start_batch_index", 0))
        end_batch_index = schedule.get("end_batch_index")
        if batch_index < start_batch_index:
            continue
        if end_batch_index is not None and batch_index > int(end_batch_index):
            continue
        if matched is None or start_batch_index >= int(matched.get("start_batch_index", 0)):
            matched = schedule

    if matched is None:
        raise ValueError(f"No sampling schedule matches batch_index={batch_index}")
    if not matched.get("sampling"):
        raise ValueError(f"Sampling schedule is missing sampling: {matched}")
    return matched


def prepare_corpus(
    *,
    manifest_path: Path,
    corpus_root: Path,
    batch_index: int,
    out_path: Path,
    report_path: Path,
    seed_override: int | None = None,
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    seed = int(seed_override if seed_override is not None else manifest.get("seed", 0))
    delimiter = str(manifest.get("delimiter", ";"))
    encoding = str(manifest.get("encoding", "utf-8-sig"))
    batch_id_prefix = str(manifest.get("batch_id_prefix", "example_making"))
    batch_id = f"{batch_id_prefix}_batch_{batch_index:03d}"
    corpora = manifest.get("corpora") or {}
    schedule = _select_sampling_schedule(manifest, batch_index)
    sampling = schedule.get("sampling") or {}
    schedule_id = str(schedule.get("schedule_id", "default"))
    schedule_start_batch_index = int(schedule.get("start_batch_index", 0))
    rank_start_offsets = {
        domain: int(offset) for domain, offset in (schedule.get("rank_start_offsets") or {}).items()
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    all_records: list[dict[str, Any]] = []
    domain_reports: dict[str, Any] = {}

    for domain in sampling:
        if domain not in corpora:
            raise KeyError(f"manifest sampling domain is missing from corpora: {domain}")
        requested = int(sampling[domain])
        rank_start = rank_start_offsets.get(domain, 0) + (batch_index - schedule_start_batch_index) * requested
        file_name = str(corpora[domain]["file"])
        file_path = _resolve_file(corpus_root, file_name)
        selected, domain_report = _sample_domain(
            domain=domain,
            file_path=file_path,
            requested=requested,
            rank_start=rank_start,
            batch_id=batch_id,
            batch_index=batch_index,
            seed=seed,
            delimiter=delimiter,
            encoding=encoding,
        )
        all_records.extend(selected)
        domain_reports[domain] = domain_report

    with out_path.open("w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")

    report = {
        "schema_version": "hantalk_prepared_example_corpus_report_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_path),
        "corpus_root": str(corpus_root),
        "output_path": str(out_path),
        "batch_id": batch_id,
        "batch_index": batch_index,
        "sampling_schedule_id": schedule_id,
        "sampling_schedule_start_batch_index": schedule_start_batch_index,
        "sampling_rank_start_offsets": rank_start_offsets,
        "seed": seed,
        "hash_method": HASH_METHOD,
        "delimiter": delimiter,
        "encoding": encoding,
        "sampling_requested_by_domain": {domain: int(size) for domain, size in sampling.items()},
        "n_rows_selected_total": len(all_records),
        "n_rows_selected_by_domain": {
            domain: int(domain_report["n_rows_selected"]) for domain, domain_report in domain_reports.items()
        },
        "n_rows_seen_by_domain": {
            domain: int(domain_report["n_rows_seen"]) for domain, domain_report in domain_reports.items()
        },
        "n_rows_valid_by_domain": {
            domain: int(domain_report["n_rows_valid"]) for domain, domain_report in domain_reports.items()
        },
        "n_rows_skipped_empty_by_domain": {
            domain: int(domain_report["n_rows_skipped_empty"]) for domain, domain_report in domain_reports.items()
        },
        "n_rows_skipped_parse_error_by_domain": {
            domain: int(domain_report["n_rows_skipped_parse_error"]) for domain, domain_report in domain_reports.items()
        },
        "domain_reports": domain_reports,
    }
    _write_json(report_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--corpus-root", required=True, type=Path)
    parser.add_argument("--batch-index", required=True, type=int)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=None, help="Override manifest seed.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = prepare_corpus(
        manifest_path=args.manifest,
        corpus_root=args.corpus_root,
        batch_index=args.batch_index,
        out_path=args.out,
        report_path=args.report,
        seed_override=args.seed,
    )
    print(
        json.dumps(
            {
                "batch_id": report["batch_id"],
                "n_rows_selected_total": report["n_rows_selected_total"],
                "n_rows_selected_by_domain": report["n_rows_selected_by_domain"],
                "report": str(args.report),
                "out": str(args.out),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
