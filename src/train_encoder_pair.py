#!/usr/bin/env python3
"""Train a HanTalk pair-mode binary encoder.

This is the canonical HanTalk encoder training entrypoint for pair examples
exported by ``src.export_encoder_examples``. It never reads Excel files.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .detector.span_utils import parse_span_segments
except ImportError:  # pragma: no cover - supports direct script execution.
    from detector.span_utils import parse_span_segments

SCHEMA_VERSION = "hantalk_train_encoder_pair_report_v1"
RUNTIME_CONFIG_SCHEMA_VERSION = "hantalk_runtime_encoder_config_v1"
EXPECTED_INPUT_CONSTRUCTION_VERSION = "hantalk_binary_pair_v1"
EXPECTED_SPAN_MARKER_STYLE = "[SPAN]...[/SPAN]"
ALLOWED_SPLITS = {"train", "dev", "test"}
ALLOWED_ROLES = {"pos_conti", "pos_disconti", "neg_target_absent"}
MODEL_INPUT_KEYS = {"input_ids", "attention_mask", "token_type_ids", "position_ids"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            f.write("")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_cell(row.get(key)) for key in fieldnames})


def _csv_cell(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    if value is None:
        return ""
    return value


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + "\n")


def _sha256_file(path: Path) -> str:
    digest = __import__("hashlib").sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _safe_prepare_out_dir(out_dir: Path, *, overwrite: bool) -> None:
    resolved = out_dir.expanduser().resolve()
    cwd = Path.cwd().resolve()
    dangerous = {Path("/").resolve(), Path.home().resolve(), cwd}
    if resolved in dangerous or cwd in resolved.parents:
        raise ValueError(f"Refusing to use dangerous --out-dir path: {resolved}")
    if resolved.exists():
        if not overwrite:
            raise FileExistsError(f"--out-dir already exists. Pass --overwrite to replace it: {resolved}")
        if resolved.is_file():
            resolved.unlink()
        else:
            shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def _set_global_seed(torch: Any, np: Any, *, seed: int, deterministic: bool) -> dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    cudnn_deterministic = None
    cudnn_benchmark = None
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.deterministic = bool(deterministic)
        torch.backends.cudnn.benchmark = not bool(deterministic)
        cudnn_deterministic = bool(torch.backends.cudnn.deterministic)
        cudnn_benchmark = bool(torch.backends.cudnn.benchmark)
    return {
        "seed": seed,
        "deterministic": deterministic,
        "torch_cudnn_deterministic": cudnn_deterministic,
        "torch_cudnn_benchmark": cudnn_benchmark,
    }


def _import_training_deps() -> dict[str, Any]:
    try:
        import numpy as np
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, Dataset
        from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup
    except ImportError as exc:  # pragma: no cover - depends on local env.
        raise RuntimeError(
            "Training requires numpy, torch, and transformers. "
            "Install dependencies before running without --validate-only."
        ) from exc
    return {
        "np": np,
        "torch": torch,
        "nn": nn,
        "DataLoader": DataLoader,
        "Dataset": Dataset,
        "AutoModel": AutoModel,
        "AutoTokenizer": AutoTokenizer,
        "get_linear_schedule_with_warmup": get_linear_schedule_with_warmup,
    }


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "torch": None,
        "transformers": None,
        "tokenizers": None,
        "numpy": None,
    }
    for package_name in ["torch", "transformers", "tokenizers", "numpy"]:
        try:
            module = __import__(package_name)
            versions[package_name] = str(getattr(module, "__version__", None))
        except Exception:
            versions[package_name] = None
    return versions


def _read_examples_jsonl(path: Path) -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no} invalid JSONL") from exc
            row["_line_no"] = line_no
            examples.append(row)
    if not examples:
        raise ValueError(f"{path}: no examples found")
    return examples


def _normalize_example(row: dict[str, Any]) -> dict[str, Any]:
    required = [
        "schema_version",
        "input_construction_version",
        "item_id",
        "example_id",
        "label",
        "split",
        "text_a",
        "text_b",
        "raw_text",
        "span_segments",
        "span_key",
        "span_text",
        "example_role",
    ]
    missing = [key for key in required if key not in row]
    if missing:
        raise ValueError(f"line {row.get('_line_no')}: missing required key(s): {missing}")
    input_construction_version = str(row["input_construction_version"]).strip()
    if input_construction_version != EXPECTED_INPUT_CONSTRUCTION_VERSION:
        raise ValueError(
            f"line {row.get('_line_no')}: invalid input_construction_version "
            f"{input_construction_version!r}; expected {EXPECTED_INPUT_CONSTRUCTION_VERSION!r}"
        )
    if row.get("span_marker_style") not in {None, "", EXPECTED_SPAN_MARKER_STYLE}:
        raise ValueError(
            f"line {row.get('_line_no')}: invalid span_marker_style "
            f"{row.get('span_marker_style')!r}; expected {EXPECTED_SPAN_MARKER_STYLE!r}"
        )

    example_id = str(row["example_id"]).strip()
    item_id = str(row["item_id"]).strip()
    split = str(row["split"]).strip()
    example_role = str(row["example_role"]).strip()
    text_a = str(row["text_a"]).strip()
    text_b = str(row["text_b"]).strip()
    raw_text = str(row["raw_text"])
    if not example_id:
        raise ValueError(f"line {row.get('_line_no')}: blank example_id")
    if not item_id:
        raise ValueError(f"{example_id}: blank item_id")
    if split not in ALLOWED_SPLITS:
        raise ValueError(f"{example_id}: invalid split {split!r}")
    if example_role not in ALLOWED_ROLES:
        raise ValueError(f"{example_id}: invalid example_role {example_role!r}")
    if not text_a:
        raise ValueError(f"{example_id}: blank text_a")
    if not text_b:
        raise ValueError(f"{example_id}: blank text_b")

    try:
        label = int(row["label"])
    except Exception as exc:
        raise ValueError(f"{example_id}: label must be 0 or 1") from exc
    if label not in {0, 1}:
        raise ValueError(f"{example_id}: label must be 0 or 1, got {label!r}")

    try:
        span_segments = parse_span_segments(row["span_segments"])
    except Exception as exc:
        raise ValueError(f"{example_id}: invalid span_segments") from exc

    normalized = dict(row)
    normalized["example_id"] = example_id
    normalized["item_id"] = item_id
    normalized["label"] = label
    normalized["split"] = split
    normalized["example_role"] = example_role
    normalized["text_a"] = text_a
    normalized["text_b"] = text_b
    normalized["raw_text"] = raw_text
    normalized["span_segments"] = span_segments
    normalized["corpus_domain"] = str(row.get("corpus_domain") or "unknown").strip() or "unknown"
    normalized["span_marker_style"] = str(row.get("span_marker_style") or EXPECTED_SPAN_MARKER_STYLE)
    return normalized


def _validate_and_summarize_examples(
    examples: list[dict[str, Any]],
    *,
    strict_splits: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    warnings: list[str] = []
    for row in examples:
        item = _normalize_example(row)
        if item["example_id"] in seen_ids:
            raise ValueError(f"duplicate example_id: {item['example_id']}")
        seen_ids.add(item["example_id"])
        normalized.append(item)

    by_split: dict[str, list[dict[str, Any]]] = {
        split: [row for row in normalized if row["split"] == split] for split in sorted(ALLOWED_SPLITS)
    }
    if not by_split["train"]:
        raise ValueError("train split is empty")
    if not by_split["dev"]:
        raise ValueError("dev split is empty. Formal training requires dev for best checkpoint selection.")
    if not by_split["test"]:
        message = "test split is empty"
        if strict_splits:
            raise ValueError(message)
        warnings.append(message)

    for split_name in ["train", "dev"]:
        labels = {row["label"] for row in by_split[split_name]}
        if labels != {0, 1}:
            raise ValueError(f"{split_name} split must contain both label 0 and 1; got {sorted(labels)}")
    test_labels = {row["label"] for row in by_split["test"]}
    if by_split["test"] and test_labels != {0, 1}:
        message = f"test split should contain both label 0 and 1; got {sorted(test_labels)}"
        if strict_splits:
            raise ValueError(message)
        warnings.append(message)

    summary = {
        "schema_version": "hantalk_encoder_pair_data_summary_v1",
        "created_at": _now_utc(),
        "n_examples": len(normalized),
        "split_counts": _count_by(normalized, "split", keys=["train", "dev", "test"]),
        "label_counts": _count_by_label(normalized),
        "label_counts_by_split": {
            split: _count_by_label(rows) for split, rows in by_split.items()
        },
        "role_counts_by_split": {
            split: _count_by(rows, "example_role", keys=sorted(ALLOWED_ROLES)) for split, rows in by_split.items()
        },
        "domain_counts_by_split": {
            split: _count_by(rows, "corpus_domain") for split, rows in by_split.items()
        },
        "item_counts": _count_by(normalized, "item_id"),
        "warnings": warnings,
    }
    return normalized, summary


def _count_by(rows: list[dict[str, Any]], key: str, *, keys: list[str] | None = None) -> dict[str, int]:
    counter = Counter(str(row.get(key) or "unknown") for row in rows)
    if keys is not None:
        return {key_value: int(counter.get(key_value, 0)) for key_value in keys}
    return dict(sorted((key_value, int(value)) for key_value, value in counter.items()))


def _count_by_label(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(int(row["label"]) for row in rows)
    return {
        "positive": int(counter.get(1, 0)),
        "negative": int(counter.get(0, 0)),
    }


def _split_examples(examples: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {split: [row for row in examples if row["split"] == split] for split in ["train", "dev", "test"]}


def _compute_tokenization_stats(
    tokenizer: Any,
    examples: list[dict[str, Any]],
    *,
    max_length: int,
    sample_limit: int = 20,
) -> dict[str, Any]:
    stats_by_split: dict[str, dict[str, Any]] = {}
    total_truncated = 0
    total_examples = 0
    max_observed = 0
    truncated_samples: list[dict[str, Any]] = []
    for split in ["train", "dev", "test"]:
        rows = [row for row in examples if row["split"] == split]
        n_truncated = 0
        split_max = 0
        for row in rows:
            encoded = tokenizer(
                row["text_a"],
                row["text_b"],
                add_special_tokens=True,
                truncation=False,
            )
            token_len = len(encoded["input_ids"])
            split_max = max(split_max, token_len)
            max_observed = max(max_observed, token_len)
            is_truncated = token_len > max_length
            if is_truncated:
                n_truncated += 1
                if len(truncated_samples) < sample_limit:
                    truncated_samples.append(
                        {
                            "example_id": row["example_id"],
                            "split": split,
                            "tokenized_length": token_len,
                            "max_length": max_length,
                            "text_a": row["text_a"],
                            "text_b": row["text_b"],
                        }
                    )
        total_truncated += n_truncated
        total_examples += len(rows)
        stats_by_split[split] = {
            "n_examples": len(rows),
            "n_truncated": n_truncated,
            "truncation_rate": _safe_div(n_truncated, len(rows)),
            "max_tokenized_length_observed": split_max,
        }
    return {
        "max_length": max_length,
        "n_examples": total_examples,
        "n_truncated_total": total_truncated,
        "truncation_rate": _safe_div(total_truncated, total_examples),
        "max_tokenized_length_observed": max_observed,
        "by_split": stats_by_split,
        "truncated_examples_sample": truncated_samples,
    }


def _safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def _resolve_device(torch: Any, device_arg: str) -> Any:
    if device_arg == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device(device_arg)


def _device_name(torch: Any, device: Any) -> str:
    try:
        if device.type == "cuda":
            return str(torch.cuda.get_device_name(device))
        if device.type == "mps":
            return "mps"
    except Exception:
        pass
    return str(device)


def _parameter_counts(model: Any) -> dict[str, int]:
    total = sum(int(p.numel()) for p in model.parameters())
    trainable = sum(int(p.numel()) for p in model.parameters() if p.requires_grad)
    return {"n_parameters": total, "n_trainable_parameters": trainable}


def _build_training_objects(deps: dict[str, Any]) -> dict[str, Any]:
    torch = deps["torch"]
    nn = deps["nn"]
    Dataset = deps["Dataset"]

    class EncoderPairDataset(Dataset):  # type: ignore[misc, valid-type]
        def __init__(self, rows: list[dict[str, Any]]):
            self.rows = rows

        def __len__(self) -> int:
            return len(self.rows)

        def __getitem__(self, idx: int) -> dict[str, Any]:
            return self.rows[idx]

    class PairCollator:
        def __init__(self, tokenizer: Any, *, max_length: int):
            self.tokenizer = tokenizer
            self.max_length = max_length

        def __call__(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
            encoded = self.tokenizer(
                [row["text_a"] for row in rows],
                [row["text_b"] for row in rows],
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            encoded["labels"] = torch.tensor([float(row["label"]) for row in rows], dtype=torch.float32)
            encoded["meta"] = rows
            return encoded

    class PairBinaryEncoder(nn.Module):  # type: ignore[misc, valid-type]
        def __init__(self, encoder: Any, *, pooling: str, head_dropout: float):
            super().__init__()
            if pooling not in {"masked_mean", "cls"}:
                raise ValueError(f"Unsupported pooling: {pooling}")
            self.encoder = encoder
            self.pooling = pooling
            hidden_size = int(getattr(encoder.config, "hidden_size"))
            self.dropout = nn.Dropout(float(head_dropout)) if head_dropout > 0 else nn.Identity()
            self.head = nn.Linear(hidden_size, 1)
            self._accepted_input_keys = self._get_accepted_input_keys()

        def _get_accepted_input_keys(self) -> set[str]:
            try:
                signature = inspect.signature(self.encoder.forward)
                params = signature.parameters
                if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
                    return set(MODEL_INPUT_KEYS)
                return set(MODEL_INPUT_KEYS).intersection(params)
            except Exception:
                return set(MODEL_INPUT_KEYS)

        def _pool(self, last_hidden_state: Any, attention_mask: Any) -> Any:
            if self.pooling == "cls":
                return last_hidden_state[:, 0]
            mask = attention_mask.unsqueeze(-1).float()
            summed = (last_hidden_state * mask).sum(dim=1)
            denom = mask.sum(dim=1).clamp(min=1e-6)
            return summed / denom

        def forward(self, batch: dict[str, Any]) -> Any:
            model_inputs = {
                key: value for key, value in batch.items() if key in self._accepted_input_keys
            }
            outputs = self.encoder(**model_inputs)
            pooled = self._pool(outputs.last_hidden_state, batch["attention_mask"])
            pooled = self.dropout(pooled)
            return self.head(pooled).squeeze(-1)

    return {
        "EncoderPairDataset": EncoderPairDataset,
        "PairCollator": PairCollator,
        "PairBinaryEncoder": PairBinaryEncoder,
    }


def _make_loss_fn(torch: Any, nn: Any, train_rows: list[dict[str, Any]], *, loss_pos_weight: str, device: Any) -> Any:
    pos_weight = None
    value = str(loss_pos_weight).strip().lower()
    if value == "none":
        pos_weight = None
    elif value == "auto":
        n_pos = sum(1 for row in train_rows if int(row["label"]) == 1)
        n_neg = sum(1 for row in train_rows if int(row["label"]) == 0)
        if n_pos <= 0:
            raise ValueError("Cannot use --loss-pos-weight auto when train has no positive examples")
        pos_weight = torch.tensor([float(n_neg / n_pos)], dtype=torch.float32, device=device)
    else:
        try:
            pos_weight = torch.tensor([float(value)], dtype=torch.float32, device=device)
        except ValueError as exc:
            raise ValueError("--loss-pos-weight must be none, auto, or a float") from exc
    return nn.BCEWithLogitsLoss(pos_weight=pos_weight, reduction="none")


def _move_batch_to_device(batch: dict[str, Any], *, device: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in batch.items():
        if key == "meta":
            out[key] = value
        elif hasattr(value, "to"):
            out[key] = value.to(device)
        else:
            out[key] = value
    return out


def _prediction_rows_from_batch(
    *,
    batch_meta: list[dict[str, Any]],
    logits: Any,
    labels: Any,
    losses: Any,
    threshold: float,
) -> list[dict[str, Any]]:
    probs = logits.sigmoid().detach().cpu().tolist()
    logits_list = logits.detach().cpu().tolist()
    labels_list = labels.detach().cpu().tolist()
    losses_list = losses.detach().cpu().tolist()
    rows: list[dict[str, Any]] = []
    for meta, logit, prob, label, loss in zip(batch_meta, logits_list, probs, labels_list, losses_list):
        pred = 1 if float(prob) >= threshold else 0
        gold = int(round(float(label)))
        rows.append(
            {
                "example_id": meta.get("example_id"),
                "item_id": meta.get("item_id"),
                "split": meta.get("split"),
                "gold_label": gold,
                "pred_label": pred,
                "prob": float(prob),
                "logit": float(logit),
                "loss": float(loss),
                "example_role": meta.get("example_role"),
                "corpus_domain": meta.get("corpus_domain"),
                "text_a": meta.get("text_a"),
                "text_b": meta.get("text_b"),
                "raw_text": meta.get("raw_text"),
                "span_segments": meta.get("span_segments"),
                "span_text": meta.get("span_text"),
                "source_hit_id": meta.get("source_hit_id"),
            }
        )
    return rows


def _limit_prediction_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return rows
    return rows[:limit]


def _metrics_from_predictions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return _empty_metrics()
    tp = sum(1 for row in rows if row["gold_label"] == 1 and row["pred_label"] == 1)
    fp = sum(1 for row in rows if row["gold_label"] == 0 and row["pred_label"] == 1)
    tn = sum(1 for row in rows if row["gold_label"] == 0 and row["pred_label"] == 0)
    fn = sum(1 for row in rows if row["gold_label"] == 1 and row["pred_label"] == 0)
    n = len(rows)
    n_pos = tp + fn
    n_neg = tn + fp
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    pos_acc = _safe_div(tp, n_pos)
    neg_acc = _safe_div(tn, n_neg)
    return {
        "n_examples": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "loss_mean": sum(float(row["loss"]) for row in rows) / n,
        "accuracy": _safe_div(tp + tn, n),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "balanced_acc": (pos_acc + neg_acc) / 2.0,
        "pos_acc": pos_acc,
        "neg_acc": neg_acc,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "prob_pos_mean": _mean([row["prob"] for row in rows if row["gold_label"] == 1]),
        "prob_neg_mean": _mean([row["prob"] for row in rows if row["gold_label"] == 0]),
        "logit_pos_mean": _mean([row["logit"] for row in rows if row["gold_label"] == 1]),
        "logit_neg_mean": _mean([row["logit"] for row in rows if row["gold_label"] == 0]),
    }


def _empty_metrics() -> dict[str, Any]:
    return {
        "n_examples": 0,
        "n_pos": 0,
        "n_neg": 0,
        "loss_mean": 0.0,
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
        "balanced_acc": 0.0,
        "pos_acc": 0.0,
        "neg_acc": 0.0,
        "tp": 0,
        "fp": 0,
        "tn": 0,
        "fn": 0,
        "prob_pos_mean": 0.0,
        "prob_neg_mean": 0.0,
        "logit_pos_mean": 0.0,
        "logit_neg_mean": 0.0,
    }


def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _group_metrics(rows: list[dict[str, Any]], group_key: str) -> dict[str, dict[str, Any]]:
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key) or "unknown")].append(row)
    return {key: _metrics_from_predictions(value) for key, value in sorted(grouped.items())}


def train_one_epoch(
    *,
    deps: dict[str, Any],
    model: Any,
    loader: Any,
    optimizer: Any,
    scheduler: Any,
    loss_fn: Any,
    device: Any,
    grad_clip_norm: float,
    use_amp: bool,
    epoch: int,
    global_step_start: int,
    log_every_steps: int,
    step_log_path: Path | None,
    wandb_run: Any | None,
) -> dict[str, Any]:
    torch = deps["torch"]
    model.train()
    start = time.perf_counter()
    losses: list[float] = []
    n_examples = 0
    n_steps = 0
    global_step = int(global_step_start)
    scaler = torch.cuda.amp.GradScaler(enabled=bool(use_amp and device.type == "cuda"))
    for batch in loader:
        batch = _move_batch_to_device(batch, device=device)
        optimizer.zero_grad(set_to_none=True)
        with torch.cuda.amp.autocast(enabled=bool(use_amp and device.type == "cuda")):
            logits = model(batch)
            per_example_loss = loss_fn(logits, batch["labels"])
            loss = per_example_loss.mean()
        if not torch.isfinite(loss):
            raise ValueError(f"Non-finite train loss at epoch={epoch}, step={n_steps + 1}: {loss}")
        scaler.scale(loss).backward()
        if grad_clip_norm > 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip_norm)
        scaler.step(optimizer)
        scaler.update()
        if scheduler is not None:
            scheduler.step()
        batch_size = int(batch["labels"].shape[0])
        losses.append(float(loss.detach().cpu()) * batch_size)
        n_examples += batch_size
        n_steps += 1
        global_step += 1
        if log_every_steps > 0 and global_step % log_every_steps == 0:
            step_record = {
                "epoch": epoch,
                "global_step": global_step,
                "train_loss_step": float(loss.detach().cpu()),
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
            }
            if step_log_path is not None:
                _append_jsonl(step_log_path, step_record)
            if wandb_run is not None:
                wandb_run.log(
                    {
                        "train/loss_step": step_record["train_loss_step"],
                        "train/global_step": global_step,
                        "lr": step_record["learning_rate"],
                        "epoch": epoch,
                    },
                    step=global_step,
                )
    elapsed = time.perf_counter() - start
    return {
        "epoch": epoch,
        "global_step_end": global_step,
        "loss_mean": _safe_div(sum(losses), n_examples),
        "n_examples": n_examples,
        "n_steps": n_steps,
        "elapsed_sec": elapsed,
        "avg_train_step_sec": _safe_div(elapsed, n_steps),
        "train_examples_per_sec": _safe_div(n_examples, elapsed),
        "learning_rate": float(optimizer.param_groups[0]["lr"]),
    }


def evaluate(
    *,
    deps: dict[str, Any],
    model: Any,
    loader: Any,
    loss_fn: Any,
    device: Any,
    threshold: float,
    split: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    torch = deps["torch"]
    model.eval()
    rows: list[dict[str, Any]] = []
    n_batches = 0
    n_examples = 0
    start = time.perf_counter()
    with torch.no_grad():
        for batch in loader:
            batch = _move_batch_to_device(batch, device=device)
            logits = model(batch)
            per_example_loss = loss_fn(logits, batch["labels"])
            rows.extend(
                _prediction_rows_from_batch(
                    batch_meta=batch["meta"],
                    logits=logits,
                    labels=batch["labels"],
                    losses=per_example_loss,
                    threshold=threshold,
                )
            )
            n_batches += 1
            n_examples += int(batch["labels"].shape[0])
    elapsed = time.perf_counter() - start
    metrics = _metrics_from_predictions(rows)
    metrics["metrics_by_example_role"] = _group_metrics(rows, "example_role")
    metrics["metrics_by_corpus_domain"] = _group_metrics(rows, "corpus_domain")
    metrics["split"] = split
    speed = {
        "elapsed_sec": elapsed,
        "n_batches": n_batches,
        "n_examples": n_examples,
        "avg_eval_batch_sec": _safe_div(elapsed, n_batches),
        "avg_inference_example_sec": _safe_div(elapsed, n_examples),
        "eval_examples_per_sec": _safe_div(n_examples, elapsed),
        "includes_tokenization": True,
        "includes_dataloader_overhead": True,
        "note": "Measured during eval loop with tokenizer/collator and DataLoader overhead included.",
    }
    return metrics, rows, speed


def _is_better(current: dict[str, Any], best: dict[str, Any] | None, *, min_delta: float) -> bool:
    if best is None:
        return True
    current_loss = float(current["loss_mean"])
    best_loss = float(best["loss_mean"])
    if current_loss < best_loss - min_delta:
        return True
    if abs(current_loss - best_loss) <= min_delta:
        return float(current["balanced_acc"]) > float(best["balanced_acc"]) + min_delta
    return False


def _save_checkpoint(
    *,
    checkpoint_dir: Path,
    model: Any,
    tokenizer: Any,
    epoch: int,
    metrics: dict[str, Any],
    args: argparse.Namespace,
    model_name_or_path: str,
    tokenizer_name_or_path: str,
    best_epoch: int | None,
) -> None:
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    encoder_dir = checkpoint_dir / "encoder"
    tokenizer_dir = checkpoint_dir / "tokenizer"
    model.encoder.save_pretrained(encoder_dir)
    tokenizer.save_pretrained(tokenizer_dir)
    deps = _import_training_deps()
    deps["torch"].save(model.head.state_dict(), checkpoint_dir / "head.pt")
    runtime_config = {
        "schema_version": RUNTIME_CONFIG_SCHEMA_VERSION,
        "input_construction_version": EXPECTED_INPUT_CONSTRUCTION_VERSION,
        "span_marker_style": EXPECTED_SPAN_MARKER_STYLE,
        "model_type": "pair_binary_encoder",
        "pooling": args.pooling,
        "threshold": args.threshold,
        "max_length": args.max_length,
        "encoder_path": "encoder",
        "tokenizer_path": "tokenizer",
        "head_path": "head.pt",
        "model_name_or_path": model_name_or_path,
        "tokenizer_name_or_path": tokenizer_name_or_path,
        "text_b_source": "encoder_pair_examples.jsonl generated from detector_bundle.items_by_e_id[item_id].canonical_form + gloss",
    }
    _write_json(checkpoint_dir / "runtime_encoder_config.json", runtime_config)
    _write_json(
        checkpoint_dir / "checkpoint_meta.json",
        {
            "schema_version": "hantalk_encoder_checkpoint_meta_v1",
            "created_at": _now_utc(),
            "epoch": epoch,
            "best_epoch": best_epoch,
            "metrics": metrics,
            "threshold": args.threshold,
            "pooling": args.pooling,
            "input_construction_version": EXPECTED_INPUT_CONSTRUCTION_VERSION,
            "span_marker_style": EXPECTED_SPAN_MARKER_STYLE,
        },
    )


def _wandb_init(args: argparse.Namespace, config: dict[str, Any]) -> Any | None:
    if args.wandb_mode == "disabled":
        return None
    try:
        import wandb
    except ImportError as exc:  # pragma: no cover - optional dependency.
        raise RuntimeError("wandb is required when --wandb-mode is online/offline") from exc
    return wandb.init(
        project=args.wandb_project,
        name=args.wandb_run_name,
        mode=args.wandb_mode,
        tags=[tag for tag in args.wandb_tags.split(",") if tag.strip()] if args.wandb_tags else None,
        config=config,
    )


def _wandb_log_prediction_table(run: Any, rows: list[dict[str, Any]], *, name: str, limit: int) -> None:
    if run is None or limit <= 0:
        return
    import wandb  # type: ignore

    columns = [
        "example_id",
        "gold_label",
        "pred_label",
        "prob",
        "logit",
        "loss",
        "example_role",
        "corpus_domain",
        "text_a",
        "text_b",
        "raw_text",
        "span_segments",
    ]
    table = wandb.Table(columns=columns)
    for row in rows[:limit]:
        table.add_data(*[_csv_cell(row.get(column)) for column in columns])
    run.log({name: table})


def _make_dataloaders(
    *,
    deps: dict[str, Any],
    examples_by_split: dict[str, list[dict[str, Any]]],
    tokenizer: Any,
    max_length: int,
    batch_size: int,
    eval_batch_size: int,
    shuffle_seed: int,
) -> dict[str, Any]:
    torch = deps["torch"]
    DataLoader = deps["DataLoader"]
    objects = _build_training_objects(deps)
    DatasetClass = objects["EncoderPairDataset"]
    CollatorClass = objects["PairCollator"]
    collator = CollatorClass(tokenizer, max_length=max_length)
    generator = torch.Generator()
    generator.manual_seed(shuffle_seed)
    loaders = {
        "train": DataLoader(
            DatasetClass(examples_by_split["train"]),
            batch_size=batch_size,
            shuffle=True,
            generator=generator,
            collate_fn=collator,
        ),
        "dev": DataLoader(
            DatasetClass(examples_by_split["dev"]),
            batch_size=eval_batch_size,
            shuffle=False,
            collate_fn=collator,
        ),
        "test": DataLoader(
            DatasetClass(examples_by_split["test"]),
            batch_size=eval_batch_size,
            shuffle=False,
            collate_fn=collator,
        ),
    }
    return loaders


def _train(args: argparse.Namespace, examples: list[dict[str, Any]], data_summary: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    deps = _import_training_deps()
    np = deps["np"]
    torch = deps["torch"]
    AutoTokenizer = deps["AutoTokenizer"]
    AutoModel = deps["AutoModel"]
    get_linear_schedule_with_warmup = deps["get_linear_schedule_with_warmup"]

    seed_state = _set_global_seed(torch, np, seed=args.seed, deterministic=args.deterministic)
    device = _resolve_device(torch, args.device)
    tokenizer_name = args.tokenizer_name_or_path or args.model_name_or_path
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_name,
        revision=args.revision,
        cache_dir=args.cache_dir,
        trust_remote_code=args.trust_remote_code,
    )
    encoder = AutoModel.from_pretrained(
        args.model_name_or_path,
        revision=args.revision,
        cache_dir=args.cache_dir,
        trust_remote_code=args.trust_remote_code,
    )
    objects = _build_training_objects(deps)
    model = objects["PairBinaryEncoder"](encoder, pooling=args.pooling, head_dropout=args.head_dropout)
    model.to(device)

    examples_by_split = _split_examples(examples)
    loaders = _make_dataloaders(
        deps=deps,
        examples_by_split=examples_by_split,
        tokenizer=tokenizer,
        max_length=args.max_length,
        batch_size=args.batch_size,
        eval_batch_size=args.eval_batch_size,
        shuffle_seed=args.shuffle_seed,
    )
    loss_fn = _make_loss_fn(
        torch,
        deps["nn"],
        examples_by_split["train"],
        loss_pos_weight=args.loss_pos_weight,
        device=device,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    total_steps = max(1, len(loaders["train"]) * args.epochs)
    warmup_steps = int(total_steps * args.warmup_ratio)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps,
    )
    param_counts = _parameter_counts(model)
    truncation_stats = _compute_tokenization_stats(tokenizer, examples, max_length=args.max_length)
    _write_json(out_dir / "data_summary.json", {**data_summary, "tokenization": truncation_stats})

    config = _train_config(
        args,
        out_dir=out_dir,
        extra={
            "seed_state": seed_state,
            "tokenization": truncation_stats,
            "device": {
                "device": str(device),
                "device_name": _device_name(torch, device),
            },
            "model_info": {
                "model_name_or_path": args.model_name_or_path,
                "tokenizer_name_or_path": tokenizer_name,
                **param_counts,
            },
            "optimizer": {
                "total_steps": total_steps,
                "warmup_steps": warmup_steps,
                "warmup_ratio": args.warmup_ratio,
            },
        },
    )
    _write_json(out_dir / "train_config.json", config)
    run = _wandb_init(args, config)

    best_metrics: dict[str, Any] | None = None
    best_epoch: int | None = None
    epochs_without_improvement = 0
    global_step = 0
    all_epoch_reports: list[dict[str, Any]] = []
    predictions_dir = out_dir / "predictions"
    debug_dir = out_dir / "debug"

    for epoch in range(1, args.epochs + 1):
        train_metrics = train_one_epoch(
            deps=deps,
            model=model,
            loader=loaders["train"],
            optimizer=optimizer,
            scheduler=scheduler,
            loss_fn=loss_fn,
            device=device,
            grad_clip_norm=args.grad_clip_norm,
            use_amp=args.amp,
            epoch=epoch,
            global_step_start=global_step,
            log_every_steps=args.log_every_steps,
            step_log_path=out_dir / "train_step_log.jsonl",
            wandb_run=run,
        )
        global_step = int(train_metrics["global_step_end"])
        dev_metrics, dev_predictions, dev_speed = evaluate(
            deps=deps,
            model=model,
            loader=loaders["dev"],
            loss_fn=loss_fn,
            device=device,
            threshold=args.threshold,
            split="dev",
        )
        improved = _is_better(dev_metrics, best_metrics, min_delta=args.min_delta)
        if improved:
            best_metrics = dev_metrics
            best_epoch = epoch
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        _save_checkpoint(
            checkpoint_dir=out_dir / "checkpoints" / "last",
            model=model,
            tokenizer=tokenizer,
            epoch=epoch,
            metrics=dev_metrics,
            args=args,
            model_name_or_path=args.model_name_or_path,
            tokenizer_name_or_path=tokenizer_name,
            best_epoch=best_epoch,
        )
        if improved:
            _save_checkpoint(
                checkpoint_dir=out_dir / "checkpoints" / "best",
                model=model,
                tokenizer=tokenizer,
                epoch=epoch,
                metrics=dev_metrics,
                args=args,
                model_name_or_path=args.model_name_or_path,
                tokenizer_name_or_path=tokenizer_name,
                best_epoch=best_epoch,
            )

        if args.save_dev_predictions_every > 0 and epoch % args.save_dev_predictions_every == 0:
            _write_jsonl(
                predictions_dir / f"dev_predictions_epoch_{epoch:03d}.jsonl",
                _limit_prediction_rows(dev_predictions, args.max_saved_prediction_rows),
            )
        _write_jsonl(
            debug_dir / "debug_predictions_latest.jsonl",
            _limit_prediction_rows(dev_predictions, args.max_saved_prediction_rows),
        )
        _write_csv(
            debug_dir / "debug_predictions_latest.csv",
            _limit_prediction_rows(dev_predictions, args.max_saved_prediction_rows),
        )

        epoch_report = {
            "epoch": epoch,
            "train": train_metrics,
            "dev": dev_metrics,
            "dev_speed": dev_speed,
            "best_epoch": best_epoch,
            "best_dev_loss_mean": best_metrics["loss_mean"] if best_metrics else None,
            "best_dev_balanced_acc": best_metrics["balanced_acc"] if best_metrics else None,
            "improved": improved,
            "epochs_without_improvement": epochs_without_improvement,
        }
        _append_jsonl(out_dir / "metrics_by_epoch.jsonl", epoch_report)
        _append_jsonl(out_dir / "train_log.jsonl", epoch_report)
        all_epoch_reports.append(epoch_report)
        if run is not None:
            run.log(
                {
                    "epoch": epoch,
                    "train/loss_epoch": train_metrics["loss_mean"],
                    "train/examples_per_sec": train_metrics["train_examples_per_sec"],
                    "dev/loss_mean": dev_metrics["loss_mean"],
                    "dev/accuracy": dev_metrics["accuracy"],
                    "dev/precision": dev_metrics["precision"],
                    "dev/recall": dev_metrics["recall"],
                    "dev/f1": dev_metrics["f1"],
                    "dev/balanced_acc": dev_metrics["balanced_acc"],
                    "dev/pos_acc": dev_metrics["pos_acc"],
                    "dev/neg_acc": dev_metrics["neg_acc"],
                    "speed/avg_train_step_sec": train_metrics["avg_train_step_sec"],
                    "speed/avg_eval_example_sec": dev_speed["avg_inference_example_sec"],
                    "best/epoch": best_epoch,
                    "best/dev_loss_mean": best_metrics["loss_mean"] if best_metrics else None,
                    "best/dev_balanced_acc": best_metrics["balanced_acc"] if best_metrics else None,
                    "lr": train_metrics["learning_rate"],
                }
            )
            _wandb_log_prediction_table(
                run,
                dev_predictions,
                name=f"dev_predictions_epoch_{epoch:03d}",
                limit=args.wandb_log_prediction_samples,
            )
        if args.early_stop_patience >= 0 and epochs_without_improvement >= args.early_stop_patience:
            break

    best_checkpoint = out_dir / "checkpoints" / "best"
    if not best_checkpoint.exists():
        shutil.copytree(out_dir / "checkpoints" / "last", best_checkpoint)
    # Evaluate with the in-memory best only if the best epoch is the last improved state.
    # For exact final test reproducibility, reload from the saved best checkpoint.
    best_encoder = AutoModel.from_pretrained(best_checkpoint / "encoder")
    best_model = objects["PairBinaryEncoder"](best_encoder, pooling=args.pooling, head_dropout=args.head_dropout)
    best_model.head.load_state_dict(torch.load(best_checkpoint / "head.pt", map_location="cpu"))
    best_model.to(device)
    test_metrics, test_predictions, test_speed = evaluate(
        deps=deps,
        model=best_model,
        loader=loaders["test"],
        loss_fn=loss_fn,
        device=device,
        threshold=args.threshold,
        split="test",
    )
    test_errors = [row for row in test_predictions if row["gold_label"] != row["pred_label"]]
    _write_jsonl(
        predictions_dir / "test_predictions_best.jsonl",
        _limit_prediction_rows(test_predictions, args.max_saved_prediction_rows),
    )
    _write_jsonl(
        predictions_dir / "test_errors_best.jsonl",
        _limit_prediction_rows(test_errors, args.max_saved_prediction_rows),
    )
    _write_csv(
        debug_dir / "debug_predictions_latest.csv",
        _limit_prediction_rows(test_predictions, args.max_saved_prediction_rows),
    )
    _write_jsonl(
        debug_dir / "debug_predictions_latest.jsonl",
        _limit_prediction_rows(test_predictions, args.max_saved_prediction_rows),
    )
    if run is not None:
        run.log(
            {
                "test/loss_mean": test_metrics["loss_mean"],
                "test/accuracy": test_metrics["accuracy"],
                "test/precision": test_metrics["precision"],
                "test/recall": test_metrics["recall"],
                "test/f1": test_metrics["f1"],
                "test/balanced_acc": test_metrics["balanced_acc"],
                "speed/test_avg_inference_example_sec": test_speed["avg_inference_example_sec"],
            }
        )
        _wandb_log_prediction_table(
            run,
            test_predictions,
            name="test_predictions_best",
            limit=args.wandb_log_prediction_samples,
        )
        run.finish()

    report = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now_utc(),
        "examples_jsonl": str(args.examples_jsonl),
        "examples_jsonl_sha256": _sha256_file(args.examples_jsonl),
        "model_name_or_path": args.model_name_or_path,
        "tokenizer_name_or_path": tokenizer_name,
        "input_construction_version": EXPECTED_INPUT_CONSTRUCTION_VERSION,
        "span_marker_style": EXPECTED_SPAN_MARKER_STYLE,
        "seed": args.seed,
        "shuffle_seed": args.shuffle_seed,
        "deterministic": args.deterministic,
        "threshold": args.threshold,
        "max_length": args.max_length,
        "pooling": args.pooling,
        "best_selection": {
            "primary": "dev_loss_mean",
            "secondary": "dev_balanced_acc",
            "tie_breaker": "earlier_epoch",
        },
        "best_epoch": best_epoch,
        "best_dev_metrics": best_metrics,
        "test_metrics_best": test_metrics,
        "data_summary": data_summary,
        "tokenization": truncation_stats,
        "speed": {
            **param_counts,
            "device": str(device),
            "device_name": _device_name(torch, device),
            "batch_size": args.batch_size,
            "eval_batch_size": args.eval_batch_size,
            "max_length": args.max_length,
            "avg_train_step_sec": _mean([entry["train"]["avg_train_step_sec"] for entry in all_epoch_reports]),
            "avg_eval_batch_sec": test_speed["avg_eval_batch_sec"],
            "avg_inference_example_sec": test_speed["avg_inference_example_sec"],
            "train_examples_per_sec": _mean([entry["train"]["train_examples_per_sec"] for entry in all_epoch_reports]),
            "eval_examples_per_sec": test_speed["eval_examples_per_sec"],
            "speed_measurement": {
                "avg_inference_example_sec": test_speed["avg_inference_example_sec"],
                "includes_tokenization": True,
                "includes_dataloader_overhead": True,
                "note": "Measured during eval loop with tokenizer/collator and DataLoader overhead included.",
            },
        },
        "prediction_saving": {
            "max_saved_prediction_rows": args.max_saved_prediction_rows,
            "note": "0 means no row limit. Metrics are always computed on full prediction rows before saving limits are applied.",
        },
        "artifacts": {
            "best_checkpoint": "checkpoints/best",
            "last_checkpoint": "checkpoints/last",
            "test_predictions_best": "predictions/test_predictions_best.jsonl",
            "test_errors_best": "predictions/test_errors_best.jsonl",
            "runtime_encoder_config": "checkpoints/best/runtime_encoder_config.json",
        },
        "warnings": data_summary.get("warnings", []),
    }
    _write_json(out_dir / "train_encoder_pair_report.json", report)
    return report


def _validate_only(
    args: argparse.Namespace,
    examples: list[dict[str, Any]],
    data_summary: dict[str, Any],
    out_dir: Path,
) -> dict[str, Any]:
    tokenization_stats = None
    if not args.skip_tokenization_stats:
        deps = _import_training_deps()
        tokenizer_name = args.tokenizer_name_or_path or args.model_name_or_path
        tokenizer = deps["AutoTokenizer"].from_pretrained(
            tokenizer_name,
            revision=args.revision,
            cache_dir=args.cache_dir,
            trust_remote_code=args.trust_remote_code,
        )
        tokenization_stats = _compute_tokenization_stats(tokenizer, examples, max_length=args.max_length)
    config = _train_config(
        args,
        out_dir=out_dir,
        extra={
            "validate_only": True,
            "tokenization": tokenization_stats,
            "model_info": {
                "model_name_or_path": args.model_name_or_path,
                "tokenizer_name_or_path": args.tokenizer_name_or_path or args.model_name_or_path,
            },
        },
    )
    _write_json(out_dir / "train_config.json", config)
    validate_report = {
        "schema_version": "hantalk_train_encoder_pair_validate_report_v1",
        "created_at": _now_utc(),
        "examples_jsonl": str(args.examples_jsonl),
        "examples_jsonl_sha256": _sha256_file(args.examples_jsonl),
        "model_name_or_path": args.model_name_or_path,
        "tokenizer_name_or_path": args.tokenizer_name_or_path or args.model_name_or_path,
        "data_summary": data_summary,
        "tokenization": tokenization_stats,
        "validate_only": True,
    }
    _write_json(out_dir / "train_encoder_pair_report.json", validate_report)
    _write_json(out_dir / "data_summary.json", {**data_summary, "tokenization": tokenization_stats})
    return validate_report


def _train_config(args: argparse.Namespace, *, out_dir: Path, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    config = {
        "schema_version": "hantalk_train_encoder_pair_config_v1",
        "created_at": _now_utc(),
        "args": {key: _jsonable(value) for key, value in vars(args).items()},
        "command": " ".join(sys.argv),
        "cwd": str(Path.cwd()),
        "out_dir": str(out_dir),
        "examples_jsonl_sha256": _sha256_file(args.examples_jsonl),
        "git_commit": _git_commit(Path.cwd()),
        "environment": _package_versions(),
    }
    if extra:
        config.update(extra)
    return config


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return str(value)


def _validate_args(args: argparse.Namespace) -> None:
    if not args.examples_jsonl.exists():
        raise FileNotFoundError(f"--examples-jsonl does not exist: {args.examples_jsonl}")
    checks = [
        (args.batch_size > 0, "--batch-size must be > 0"),
        (args.eval_batch_size > 0, "--eval-batch-size must be > 0"),
        (args.epochs > 0, "--epochs must be > 0"),
        (args.lr > 0, "--lr must be > 0"),
        (args.weight_decay >= 0, "--weight-decay must be >= 0"),
        (0 <= args.warmup_ratio <= 1, "--warmup-ratio must be between 0 and 1"),
        (args.max_length > 0, "--max-length must be > 0"),
        (0 <= args.threshold <= 1, "--threshold must be between 0 and 1"),
        (args.grad_clip_norm >= 0, "--grad-clip-norm must be >= 0"),
        (args.early_stop_patience >= -1, "--early-stop-patience must be >= -1"),
        (args.min_delta >= 0, "--min-delta must be >= 0"),
        (0 <= args.head_dropout < 1, "--head-dropout must be >= 0 and < 1"),
        (args.wandb_log_prediction_samples >= 0, "--wandb-log-prediction-samples must be >= 0"),
        (args.save_dev_predictions_every >= 0, "--save-dev-predictions-every must be >= 0"),
        (args.max_saved_prediction_rows >= 0, "--max-saved-prediction-rows must be >= 0"),
        (args.log_every_steps >= 0, "--log-every-steps must be >= 0"),
    ]
    failed = [message for ok, message in checks if not ok]
    if failed:
        raise ValueError("; ".join(failed))
    loss_pos_weight = str(args.loss_pos_weight).strip().lower()
    if loss_pos_weight not in {"none", "auto"}:
        try:
            if float(loss_pos_weight) <= 0:
                raise ValueError
        except ValueError as exc:
            raise ValueError("--loss-pos-weight must be none, auto, or a positive float") from exc


def run(args: argparse.Namespace) -> dict[str, Any]:
    _validate_args(args)
    out_dir = args.out_dir.expanduser().resolve()
    _safe_prepare_out_dir(out_dir, overwrite=args.overwrite)
    examples_raw = _read_examples_jsonl(args.examples_jsonl)
    examples, data_summary = _validate_and_summarize_examples(
        examples_raw,
        strict_splits=args.strict_splits,
    )
    config = _train_config(args, out_dir=out_dir)
    _write_json(out_dir / "train_config.json", config)
    _write_json(out_dir / "data_summary.json", data_summary)
    if args.validate_only:
        return _validate_only(args, examples, data_summary, out_dir)
    return _train(args, examples, data_summary, out_dir)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--examples-jsonl", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--tokenizer-name-or-path")
    parser.add_argument("--revision")
    parser.add_argument("--cache-dir")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--shuffle-seed", required=True, type=int)
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--eval-batch-size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument("--warmup-ratio", type=float, default=0.0)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--early-stop-patience", type=int, default=4)
    parser.add_argument("--min-delta", type=float, default=0.0)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    parser.add_argument("--pooling", default="masked_mean", choices=["masked_mean", "cls"])
    parser.add_argument("--head-dropout", type=float, default=0.0)
    parser.add_argument("--loss-pos-weight", default="none")
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--wandb-project", default="hantalk")
    parser.add_argument("--wandb-run-name")
    parser.add_argument("--wandb-mode", default="disabled", choices=["disabled", "offline", "online"])
    parser.add_argument("--wandb-tags", default="")
    parser.add_argument("--wandb-log-prediction-samples", type=int, default=50)
    parser.add_argument("--save-dev-predictions-every", type=int, default=1)
    parser.add_argument(
        "--max-saved-prediction-rows",
        type=int,
        default=0,
        help="Limit rows saved in prediction/debug files. 0 means unlimited.",
    )
    parser.add_argument(
        "--log-every-steps",
        type=int,
        default=0,
        help="Log train step loss every N optimizer steps to train_step_log.jsonl and W&B. 0 disables step logging.",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--skip-tokenization-stats", action="store_true")
    parser.add_argument("--strict-splits", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "report": str(args.out_dir.expanduser().resolve() / "train_encoder_pair_report.json"),
                "validate_only": bool(args.validate_only),
                "model_name_or_path": args.model_name_or_path,
                "n_examples": report.get("data_summary", {}).get("n_examples"),
                "best_epoch": report.get("best_epoch"),
                "test_f1": (report.get("test_metrics_best") or {}).get("f1"),
            },
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
