"""DEC-025 closed-loop retest — final comparison.

Reuses DEC-019's iteration-4 baseline and CONTROL arm as-is (identical
starting point and identical "keep using the un-fine-tuned model"
question -- neither depends on which fine-tuned adapter is being
tested, so re-running them would just re-spend money for the same
answer). Adds the DEC-019 epochs=3 TREATMENT result (if present) and
this DEC's epochs=5 TREATMENT result side by side, so the epoch-count
effect on closing the loop is visible directly, not just asserted.

Usage (after scripts/dec025_closedloop_epochs5_treatment_merge.py has
been run):
    python scripts/dec025_closedloop_compare.py
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

    rows = [
        ("Iteration 4 (pre-closure baseline)", baseline_n, baseline_metrics),
        ("Iteration 5, CONTROL (base model continues)", control["accumulated_kb_size"], control["accumulated_kb_after_iteration5"]),
    ]

    old_treatment_path = Path("outputs/dec019_closedloop/treatment/summary.json")
    if old_treatment_path.exists():
        with open(old_treatment_path) as f:
            old_treatment = json.load(f)
        rows.append((
            "Iteration 5, TREATMENT epochs=3 seed43 (DEC-019, superseded adapter)",
            old_treatment["accumulated_kb_size"], old_treatment["accumulated_kb_after_iteration5"],
        ))

    with open("outputs/dec025_closedloop/treatment/summary.json") as f:
        new_treatment = json.load(f)
    rows.append((
        "Iteration 5, TREATMENT epochs=5 seed43 (DEC-025, headline adapter)",
        new_treatment["accumulated_kb_size"], new_treatment["accumulated_kb_after_iteration5"],
    ))

    print(f"{'Arm':<62} {'KB size':>8} {'P':>8} {'R':>8} {'F1':>8}")
    for name, n, m in rows:
        print(f"{name:<62} {n:>8} {m['precision']:>8.4f} {m['recall']:>8.4f} {m['f1']:>8.4f}")

    result = {name: {"kb_size": n, **m} for name, n, m in rows}
    out = Path("outputs/dec025_closedloop")
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "final_comparison.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved -> {out}/final_comparison.json")


if __name__ == "__main__":
    main()
