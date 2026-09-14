"""Regenerate DEC-006's synthetic fine-tuning data in the SAME
task-shape as the evaluation harness (dec006_evaluate_adapter.py /
src/prompts.py): a paragraph of product text in, a JSON array of
triples out.

The original version (src/synthetic_data_generator.py's per-relation
"### Instruction / ### Response" template, matching SLDE.pdf's Module 4
description literally: "Extract the [predicate] of [subject]" -> "The
[predicate] of [subject] is [object].") taught a different task shape
than what dec006_evaluate_adapter.py tests. The fine-tuned model
scored F1=0.0000 on the first real RunPod run as a direct result of
this mismatch -- not a fine-tuning failure. This script fixes it by
deriving training examples from the same real per-product
high-confidence PKB triples used before (outputs/dec003_product_probkb_v2/
train_kb/pkb_snapshot_iteration_4.csv, above_threshold rows only --
127 rows / 33 products, same source as the original file per EVID-025),
grouped per product, using the exact same prompt template as eval.

Pure Python + pandas, no GPU needed.

Usage:
    python scripts/dec006_regenerate_synth_data.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.datasets.product_generator import ALLOWED_PREDICATES
from src.prompts import build_extraction_prompt

SNAPSHOT_PATH = "outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv"
OUT_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train.jsonl"


def main():
    df = pd.read_csv(SNAPSHOT_PATH)
    accepted = df[df["above_threshold"] == True]  # noqa: E712

    triples_by_subject: dict[str, list[dict]] = defaultdict(list)
    text_by_subject: dict[str, str] = {}

    for _, row in accepted.iterrows():
        subject = row["subject"]
        triples_by_subject[subject].append({
            "subject": subject,
            "predicate": row["predicate"],
            "object": row["object"],
            "confidence": round(float(row["conflict_adjusted_final_confidence"]), 2),
        })
        if subject not in text_by_subject:
            provenance = json.loads(row["provenance"])
            real_text = next((p for p in provenance if not p.startswith("structured_row:")), None)
            if real_text:
                text_by_subject[subject] = real_text

    examples = []
    for subject, triples in triples_by_subject.items():
        text = text_by_subject.get(subject)
        if not text:
            continue
        prompt = build_extraction_prompt(text[:700], ALLOWED_PREDICATES)
        target = json.dumps(triples, ensure_ascii=False)
        examples.append({"text": f"{prompt}\n{target}"})

    out_path = Path(OUT_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    n_triples = sum(len(v) for v in triples_by_subject.values())
    print(f"Wrote {len(examples)} product-level examples ({n_triples} total triples) -> {out_path}")


if __name__ == "__main__":
    main()
