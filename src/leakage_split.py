"""Leakage-safe product-level train/val/test split for the SLDE-AFT
consumer-product dataset (DEC-003 leakage-safe split; slde_aft_next_steps.md
item #2).

The 20/30/40/50-product notebooks all call ``random.seed(42)`` and then
draw product attributes in the same order for the same list definitions
(brands/categories/colors/materials/regions and ALLOWED_PREDICATES are
identical across the four notebook variants). Under a fixed seed, product
index 1..N in the N-product run is therefore bit-identical to product
index 1..N in any larger run. This lets a single split, computed over the
50-product superset, apply consistently to the 20-, 30-, and 40-product
subsets: for any dataset size N, keep only rows with product_idx <= N.

This module does not regenerate product content. It only assigns each
product index to train/val/test so that no dataset size accidentally puts
a "test" product's structured facts into a training/KB-seed/prompt-example
role at another size.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

N_PRODUCTS_SUPERSET = 50
SPLIT_SEED = 7  # deliberately distinct from the generation seed (42)
TRAIN_RATIO = 0.70
VAL_RATIO = 0.10
TEST_RATIO = 0.20


def build_product_split(
    n_products: int = N_PRODUCTS_SUPERSET,
    seed: int = SPLIT_SEED,
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
    test_ratio: float = TEST_RATIO,
) -> dict[int, str]:
    """Return {product_idx (1-based): "train" | "val" | "test"}."""

    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-9:
        raise ValueError("train/val/test ratios must sum to 1.0")

    n_train = round(n_products * train_ratio)
    n_val = round(n_products * val_ratio)
    n_test = n_products - n_train - n_val
    if n_test < 0:
        raise ValueError("train_ratio + val_ratio exceeds 1.0")

    indices = list(range(1, n_products + 1))
    rng = random.Random(seed)
    rng.shuffle(indices)

    split: dict[int, str] = {}
    for idx in indices[:n_train]:
        split[idx] = "train"
    for idx in indices[n_train : n_train + n_val]:
        split[idx] = "val"
    for idx in indices[n_train + n_val :]:
        split[idx] = "test"
    return split


def save_product_split(
    output_dir: str | Path = "data",
    n_products: int = N_PRODUCTS_SUPERSET,
    seed: int = SPLIT_SEED,
) -> tuple[Path, Path]:
    """Compute the split and write data/product_split.csv +
    data/product_split_manifest.json. Returns (csv_path, manifest_path)."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    split = build_product_split(n_products=n_products, seed=seed)

    csv_path = output_dir / "product_split.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_idx", "split"])
        for idx in sorted(split):
            writer.writerow([idx, split[idx]])

    counts = {"train": 0, "val": 0, "test": 0}
    for v in split.values():
        counts[v] += 1

    manifest = {
        "n_products_superset": n_products,
        "split_seed": seed,
        "generation_seed": 42,
        "ratios": {
            "train": TRAIN_RATIO,
            "val": VAL_RATIO,
            "test": TEST_RATIO,
        },
        "counts": counts,
        "usage": (
            "For a dataset of size N (20/30/40/50), keep only rows with "
            "product_idx <= N, then join structured_products.csv / "
            "gold_triples_*.csv on product_idx (loop position, 1-based) "
            "to get each product's split assignment."
        ),
        "leakage_rules": [
            "Test-split products must be evaluated on unstructured-text "
            "extraction only.",
            "Do not seed the KB with a test-split product's structured "
            "target triples before evaluating that product.",
            "Do not use test-split products in synthetic training data, "
            "LoRA fine-tuning data, few-shot prompt examples, feedback- "
            "controller exemplars, or threshold selection.",
            "Val-split products may be used for threshold selection and "
            "hyperparameter tuning; train-split products may seed the KB "
            "and generate synthetic supervision.",
        ],
        "assumption": (
            "Assumes the 20/30/40/50 notebooks are run with random.seed(42) "
            "and unmodified brands/categories/colors/materials/regions "
            "lists, so product_idx 1..N is identical across dataset sizes. "
            "If any notebook's generation cell is edited, this assumption "
            "must be re-verified before reusing this split."
        ),
    }

    manifest_path = output_dir / "product_split_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return csv_path, manifest_path


if __name__ == "__main__":
    csv_path, manifest_path = save_product_split()
    print(f"Wrote {csv_path}")
    print(f"Wrote {manifest_path}")
