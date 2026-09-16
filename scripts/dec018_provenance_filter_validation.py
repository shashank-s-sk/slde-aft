"""DEC-018 — validate the provenance filter against known gold triples.

Because the product domain is synthetically generated, we know the TRUE
gold triples for every product (src/datasets/product_generator.py).
This script directly measures whether requiring structured corroboration
(src/provenance_filter.py) actually improves synthetic-training-data
precision, rather than just asserting it does -- answering
professor_feedback.md point #7's "provenance filtering examples" ask
with a real, quantitative before/after comparison.

Pure Python + pandas, no API/GPU cost -- reprocesses an already-collected
PKB snapshot.

Usage:
    python scripts/dec018_provenance_filter_validation.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.datasets.product_generator import generate_products
from src.pkb_instrumentation import normalized_object, normalized_slot
from src.provenance_filter import has_structured_corroboration

SNAPSHOT_PATH = "outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv"
N_PRODUCTS = 200
GENERATION_SEED = 42
OUT_DIR = Path("outputs/dec018_provenance_filter")


def main():
    df = pd.read_csv(SNAPSHOT_PATH)
    accepted = df[df["above_threshold"] == True].copy()  # noqa: E712
    accepted["source_types_list"] = accepted["source_types"].apply(json.loads)
    accepted["has_structured"] = accepted["source_types_list"].apply(has_structured_corroboration)

    gold_keys = set()
    for idx, structured, unstructured, gold_structured, gold_unstructured in generate_products(
        N_PRODUCTS, seed=GENERATION_SEED
    ):
        for s, p, o, _ in gold_structured:
            sn, pn = normalized_slot(s, p)
            gold_keys.add((sn, pn, normalized_object(o)))

    def is_gold(row) -> bool:
        sn, pn = normalized_slot(row["subject"], row["predicate"])
        return (sn, pn, normalized_object(str(row["object"]))) in gold_keys

    accepted["is_correct"] = accepted.apply(is_gold, axis=1)

    with_struct = accepted[accepted["has_structured"]]
    without_struct = accepted[~accepted["has_structured"]]

    summary = {
        "snapshot_path": SNAPSHOT_PATH,
        "n_total_above_threshold": len(accepted),
        "unfiltered_precision": float(accepted["is_correct"].mean()),
        "n_with_structured_corroboration": len(with_struct),
        "precision_with_structured_corroboration": float(with_struct["is_correct"].mean()) if len(with_struct) else None,
        "n_unstructured_only": len(without_struct),
        "precision_unstructured_only": float(without_struct["is_correct"].mean()) if len(without_struct) else None,
        "n_dropped_by_filter": len(without_struct),
        "pct_dropped_by_filter": len(without_struct) / len(accepted) if len(accepted) else 0.0,
    }

    print(json.dumps(summary, indent=2))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    without_struct[["subject", "predicate", "object", "observation_count", "is_correct"]].to_csv(
        OUT_DIR / "dropped_triples.csv", index=False
    )
    print(f"\nSaved summary.json and dropped_triples.csv -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
