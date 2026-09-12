"""Synthetic supervision generator — DEC-006 / SLDE.pdf Module 4.

Converts high-confidence PKB triples (C > threshold) into instruction-
response training pairs for LoRA fine-tuning, per the paper's own
description: 'Each triple is transformed using a combination of fixed
templates... to produce an instruction of the form "Extract the
[predicate] of [subject]" paired with a response of the form "The
[predicate] of [subject] is [object]."' Diversity is controlled via
balanced per-predicate sampling so no single predicate dominates the
training set (paper Section 4.5).

This module does NOT require torch/transformers — it only produces the
JSONL training data. The actual LoRA fine-tuning step (scripts/
dec006_lora_finetune.py) needs those and a GPU; see Decision log.md
DEC-006 for the staged free-then-paid GPU plan.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


def build_instruction_pair(subject: str, predicate: str, object_value: str) -> dict:
    predicate_readable = predicate.replace("_", " ")
    return {
        "instruction": f"Extract the {predicate_readable} of {subject}.",
        "response": f"The {predicate_readable} of {subject} is {object_value}.",
    }


def generate_synthetic_examples(
    accepted: dict[tuple[str, str, str], dict[str, Any]],
    threshold: float = 0.88,
    max_per_predicate: int | None = None,
) -> list[dict]:
    """accepted: the same {(subject_norm, predicate_norm, object_norm): entry}
    dict produced by CandidateBufferAdapter/DeterministicKBAdapter, where
    each entry has 'subject', 'predicate', 'object', 'confidence'.

    Returns a list of instruction/response dicts, balanced across
    predicates (no predicate contributes more than max_per_predicate
    examples, if given) so the fine-tuning set doesn't over-specialize
    toward the most frequently observed relation types (paper 4.5).
    """
    by_predicate: dict[str, list[dict]] = defaultdict(list)

    for entry in accepted.values():
        if entry.get("confidence", 0.0) <= threshold:
            continue
        pair = build_instruction_pair(entry["subject"], entry["predicate"], entry["object"])
        pair.update({
            "subject": entry["subject"], "predicate": entry["predicate"],
            "object": entry["object"], "confidence": entry["confidence"],
            "provenance": (entry.get("provenance") or [None])[0] if isinstance(entry.get("provenance"), list)
                          else entry.get("provenance"),
        })
        by_predicate[entry["predicate"]].append(pair)

    examples = []
    for predicate, pairs in by_predicate.items():
        selected = pairs[:max_per_predicate] if max_per_predicate else pairs
        examples.extend(selected)

    return examples


def save_synthetic_jsonl(examples: list[dict], out_path: str | Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for ex in examples:
            row = {
                "text": (
                    f"### Instruction:\n{ex['instruction']}\n\n"
                    f"### Response:\n{ex['response']}"
                )
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return out_path
