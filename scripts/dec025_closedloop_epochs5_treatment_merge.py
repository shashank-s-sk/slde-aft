"""DEC-025 closed-loop retest — TREATMENT arm, merge step (local, no cost).

Same replay/merge logic as scripts/dec019_closedloop_treatment_merge.py,
pointed at the epochs=5 adapter's iteration-5 triples instead of the
epochs=3 seed-43 adapter's. Replays iterations 1-4 fresh from the SAME
outputs/dec006_scaleup_probkb/train_kb snapshot DEC-019 used (identical
starting point to both DEC-019's control arm and this run), merges the
epochs=5 model's triples in as iteration 5, and computes the same two
metrics as DEC-019: (a) this iteration's own extraction quality vs.
gold, and (b) the accumulated KB's above-threshold quality vs. gold
after this iteration.

Usage:
    python scripts/dec025_closedloop_epochs5_treatment_merge.py
"""

from __future__ import annotations

import json
from pathlib import Path

from src.datasets.product_generator import generate_products
from src.pkb_instrumentation import normalized_object, normalized_slot
from src.pkb_replay import build_replayed_adapter

SCALEUP_ROOT = "outputs/dec006_scaleup_probkb"
SPLIT_PATH = "data/product_split_200.csv"
N_PRODUCTS = 200
GENERATION_SEED = 42
FUNCTIONAL_PREDICATES_PATH = "configs/functional_predicates_product_domain.json"
TRIPLES_PATH = "outputs/dec025_closedloop/treatment/iteration5_triples.json"
OUTPUT_DIR = "outputs/dec025_closedloop/treatment"
ADAPTER_LABEL = "outputs/dec025_adapters/mistral7b_qlora_epochs5_seed43"


def load_split() -> dict[int, str]:
    import csv
    split = {}
    with open(SPLIT_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]
    return split


def normalize_gold(gold_list) -> set[tuple[str, str, str]]:
    keys = set()
    for s, p, o, _ in gold_list:
        sn, pn = normalized_slot(s, p)
        keys.add((sn, pn, normalized_object(o)))
    return keys


def normalize_triples(triples) -> set[tuple[str, str, str]]:
    keys = set()
    for t in triples:
        sn, pn = normalized_slot(t["subject"], t["predicate"])
        keys.add((sn, pn, normalized_object(t["object"])))
    return keys


def prf(pred_keys: set, gold_keys: set) -> dict:
    tp = len(pred_keys & gold_keys)
    fp = len(pred_keys - gold_keys)
    fn = len(gold_keys - pred_keys)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1,
            "true_positives": tp, "false_positives": fp, "false_negatives": fn}


def main():
    split = load_split()
    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        N_PRODUCTS, seed=GENERATION_SEED
    ):
        products[idx] = gold_structured

    train_idx = sorted(i for i, s in split.items() if s == "train")
    train_gold_keys = set()
    for idx in train_idx:
        train_gold_keys |= normalize_gold(products[idx])

    adapter = build_replayed_adapter(
        observations_dir=f"{SCALEUP_ROOT}/train_kb",
        iterations=[1, 2, 3, 4],
        experiment_id="DEC025_CLOSEDLOOP_EPOCHS5", run_id="treatment",
        functional_predicates_path=FUNCTIONAL_PREDICATES_PATH,
        output_dir=OUTPUT_DIR, threshold=0.88, shrinkage=0.75,
        gold_keys=train_gold_keys,
    )
    print(f"Replayed iterations 1-4: {len(adapter.accepted)} accepted keys, "
          f"{sum(1 for e in adapter.accepted.values() if e['confidence'] > 0.88)} above threshold")

    with open(TRIPLES_PATH, encoding="utf-8") as f:
        triples = json.load(f)
    print(f"Loaded {len(triples)} fine-tuned-model triples from {TRIPLES_PATH}")

    for t in triples:
        adapter.accept_candidate(
            subject=t["subject"], predicate=t["predicate"], object_value=t["object"],
            confidence=t["confidence"], source_id=t["source_id"],
            source_type=t["source_type"], provenance=t["provenance"],
        )
    adapter.end_iteration(5)

    iter5_pred_keys = normalize_triples(triples)
    iter5_metrics = prf(iter5_pred_keys, train_gold_keys)

    above_threshold_keys = [
        {"subject": e["subject"], "predicate": e["predicate"], "object": e["object"]}
        for e in adapter.accepted.values() if e["confidence"] > 0.88
    ]
    above_threshold_norm_keys = normalize_triples(above_threshold_keys)
    kb_metrics = prf(above_threshold_norm_keys, train_gold_keys)

    out = Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "arm": "treatment", "adapter": ADAPTER_LABEL, "epochs": 5, "seed": 43,
        "n_triples_extracted": len(triples),
        "iteration5_extraction_only": iter5_metrics,
        "accumulated_kb_after_iteration5": kb_metrics,
        "accumulated_kb_size": len(above_threshold_norm_keys),
    }
    with open(out / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nIteration 5 (this pass only): P={iter5_metrics['precision']:.4f} R={iter5_metrics['recall']:.4f} F1={iter5_metrics['f1']:.4f}")
    print(f"Accumulated KB after iteration 5: P={kb_metrics['precision']:.4f} R={kb_metrics['recall']:.4f} F1={kb_metrics['f1']:.4f} (n={len(above_threshold_norm_keys)})")
    print(f"Saved to {out}/summary.json")


if __name__ == "__main__":
    main()
