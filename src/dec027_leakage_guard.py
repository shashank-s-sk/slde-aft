"""DEC-027 leakage guard: assert that no validation- or test-split
product name (from data/product_split_200.csv) appears as a training
example's subject in a fine-tuning training JSONL file.

Reuses scripts/dec006_evaluate_adapter.py's existing
load_trained_subjects() (parses the trailing target JSON array of each
training example, the same way that script already does for its own
leakage exclusion) rather than reimplementing subject extraction, so
both mechanisms agree by construction.
"""

from __future__ import annotations

import csv
from pathlib import Path

from scripts.dec006_evaluate_adapter import load_trained_subjects
from src.datasets.product_generator import generate_products

SPLIT_PATH_200 = "data/product_split_200.csv"
N_PRODUCTS_200 = 200
GENERATION_SEED = 42


def load_split(path: str) -> dict[int, str]:
    split = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]
    return split


def held_out_product_names(
    split_path: str = SPLIT_PATH_200,
    n_products: int = N_PRODUCTS_200,
    generation_seed: int = GENERATION_SEED,
) -> set[str]:
    """Every product name assigned to the validation or test split."""
    split = load_split(split_path)
    names = set()
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        n_products, seed=generation_seed
    ):
        if split.get(idx) in ("val", "test"):
            names.add(structured_row["product_name"])
    return names


def assert_no_leakage(
    training_data_path: str,
    split_path: str = SPLIT_PATH_200,
    n_products: int = N_PRODUCTS_200,
    generation_seed: int = GENERATION_SEED,
) -> None:
    """Raise AssertionError, naming every leaked product, if any
    validation- or test-split product name appears as a subject in the
    training data at `training_data_path`."""
    held_out = held_out_product_names(split_path, n_products, generation_seed)
    trained = load_trained_subjects(training_data_path)
    leaked = sorted(held_out & trained)
    if leaked:
        raise AssertionError(
            f"DEC-027 leakage guard FAILED: {len(leaked)} validation/test product(s) "
            f"found as a training-example subject in {training_data_path!r}: {leaked}"
        )
