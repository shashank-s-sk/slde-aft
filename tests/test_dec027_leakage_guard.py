import json

import pytest

from src.dec027_leakage_guard import assert_no_leakage, held_out_product_names

TRAINING_DATA_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl"


def test_committed_training_set_has_no_leakage():
    """The actual training data DEC-027 uses must contain no validation-
    or test-split product from the 200-product split."""
    assert_no_leakage(TRAINING_DATA_PATH)


def test_guard_detects_a_planted_violation(tmp_path):
    """Prove the guard actually catches leakage, not just that it passes
    on already-clean data: inject one held-out product's own training
    example into a scratch copy of the real training file, and assert
    the guard raises with that product named in the message."""
    held_out = sorted(held_out_product_names())
    assert held_out, "no held-out products found -- split/generation broken, cannot run this test"
    planted_product = held_out[0]

    scratch_path = tmp_path / "planted_leakage.jsonl"
    original_lines = [
        line for line in open(TRAINING_DATA_PATH, encoding="utf-8") if line.strip()
    ]

    planted_example = {
        "text": (
            "You extract factual product knowledge triples.\n\nText:\n"
            f"{planted_product} is manufactured by TestBrand.\n\n"
            f'[{{"subject": "{planted_product}", "predicate": "manufactured_by", '
            f'"object": "TestBrand", "confidence": 0.95}}]'
        )
    }

    with open(scratch_path, "w", encoding="utf-8") as f:
        for line in original_lines:
            f.write(line if line.endswith("\n") else line + "\n")
        f.write(json.dumps(planted_example) + "\n")

    with pytest.raises(AssertionError) as exc_info:
        assert_no_leakage(str(scratch_path))

    assert planted_product in str(exc_info.value)
