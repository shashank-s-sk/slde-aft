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

DEC-018 provenance filter (see src/provenance_filter.py): by default,
also drops any triple whose corroboration is unstructured-only (no
structured source in its observation history). Validated on the
200-product scale-up snapshot (EVID-029): this raises training-data
precision against gold from 93.5% to 100%, by removing exactly the
triples that are hallucinations -- despite crossing the confidence
threshold and being observed 2-21 times each, every one of the
unstructured-only triples in that snapshot was wrong (mostly generic
device-category nouns like "laptop device" standing in for the real
product name). Pass --no-provenance-filter to reproduce the older,
unfiltered behavior (e.g. to exactly match EVID-026/027/028's data).

Pure Python + pandas, no GPU needed.

Usage:
    python scripts/dec006_regenerate_synth_data.py
    python scripts/dec006_regenerate_synth_data.py --no-provenance-filter
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.datasets.product_generator import ALLOWED_PREDICATES
from src.prompts import build_extraction_prompt
from src.provenance_filter import has_structured_corroboration

SNAPSHOT_PATH = "outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv"
OUT_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train.jsonl"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-path", default=SNAPSHOT_PATH,
                         help="PKB snapshot CSV to derive training data from (default: the original 50-product DEC-003 run)")
    parser.add_argument("--out-path", default=OUT_PATH)
    parser.add_argument("--no-provenance-filter", action="store_true",
                         help="Disable the DEC-018 provenance filter (reproduces pre-DEC-018 behavior)")
    args = parser.parse_args()
    use_provenance_filter = not args.no_provenance_filter

    df = pd.read_csv(args.snapshot_path)
    accepted = df[df["above_threshold"] == True].copy()  # noqa: E712

    if use_provenance_filter:
        n_before = len(accepted)
        accepted = accepted[accepted["source_types"].apply(lambda s: has_structured_corroboration(json.loads(s)))]
        print(f"Provenance filter: kept {len(accepted)}/{n_before} triples "
              f"(dropped {n_before - len(accepted)} with unstructured-only corroboration)")

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

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    n_triples = sum(len(v) for v in triples_by_subject.values())
    print(f"Wrote {len(examples)} product-level examples ({n_triples} total triples) -> {out_path}")


if __name__ == "__main__":
    main()
