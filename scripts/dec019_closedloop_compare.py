"""DEC-019 closed-loop test — final comparison.

Loads the iteration-4 baseline (pre-closure, from the original
EVID-027 scale-up snapshot), the CONTROL arm's iteration-5 result
(continuing with the un-fine-tuned model), and the TREATMENT arm's
iteration-5 result (closing the loop with the fine-tuned model), and
prints/saves the three-way comparison that actually answers claim #1:
does closing the loop improve the system?

Usage (after both control and treatment-merge have been run):
    python scripts/dec019_closedloop_compare.py
"""

from __future__ import annotations

import json
from pathlib import Path

from src.datasets.product_generator import generate_products
from src.pkb_instrumentation import normalized_object, normalized_slot

SCALEUP_SNAPSHOT = "outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv"
SPLIT_PATH = "data/product_split_200.csv"
N_PRODUCTS = 200
GENERATION_SEED = 42


def normalize_gold(gold_list) -> set[tuple[str, str, str]]:
    keys = set()
    for s, p, o, _ in gold_list:
        sn, pn = normalized_slot(s, p)
        keys.add((sn, pn, normalized_object(o)))
    return keys


def normalize_row_keys(rows) -> set[tuple[str, str, str]]:
    keys = set()
    for s, p, o in rows:
        sn, pn = normalized_slot(s, p)
        keys.add((sn, pn, normalized_object(str(o))))
    return keys


def prf(pred_keys: set, gold_keys: set) -> dict:
    tp = len(pred_keys & gold_keys)
    fp = len(pred_keys - gold_keys)
    fn = len(gold_keys - pred_keys)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    import csv
    import pandas as pd

    split = {}
    with open(SPLIT_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]

    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        N_PRODUCTS, seed=GENERATION_SEED
    ):
        products[idx] = gold_structured

    train_idx = sorted(i for i, s in split.items() if s == "train")
    train_gold_keys = set()
    for idx in train_idx:
        train_gold_keys |= normalize_gold(products[idx])

    baseline_df = pd.read_csv(SCALEUP_SNAPSHOT)
    baseline_above = baseline_df[baseline_df["above_threshold"] == True]  # noqa: E712
    baseline_keys = normalize_row_keys(
        (r["subject"], r["predicate"], r["object"]) for _, r in baseline_above.iterrows()
    )
    baseline_metrics = prf(baseline_keys, train_gold_keys)
    baseline_n = len(baseline_keys)

    with open("outputs/dec019_closedloop/control/summary.json") as f:
        control = json.load(f)
    with open("outputs/dec019_closedloop/treatment/summary.json") as f:
        treatment = json.load(f)

    rows = [
        ("Iteration 4 (pre-closure baseline)", baseline_n, baseline_metrics),
        ("Iteration 5, CONTROL (base model continues)", control["accumulated_kb_size"], control["accumulated_kb_after_iteration5"]),
        ("Iteration 5, TREATMENT (fine-tuned model closes the loop)", treatment["accumulated_kb_size"], treatment["accumulated_kb_after_iteration5"]),
    ]

    print(f"{'Arm':<55} {'KB size':>8} {'P':>8} {'R':>8} {'F1':>8}")
    for name, n, m in rows:
        print(f"{name:<55} {n:>8} {m['precision']:>8.4f} {m['recall']:>8.4f} {m['f1']:>8.4f}")

    result = {
        "iteration4_baseline": {"kb_size": baseline_n, **baseline_metrics},
        "control_iteration5": {"kb_size": control["accumulated_kb_size"], **control["accumulated_kb_after_iteration5"]},
        "treatment_iteration5": {"kb_size": treatment["accumulated_kb_size"], **treatment["accumulated_kb_after_iteration5"]},
    }
    out = Path("outputs/dec019_closedloop")
    with open(out / "final_comparison.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved -> {out}/final_comparison.json")


if __name__ == "__main__":
    main()
