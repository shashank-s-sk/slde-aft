from src.synthetic_data_generator import (
    build_instruction_pair,
    generate_synthetic_examples,
    save_synthetic_jsonl,
)


def test_instruction_pair_format():
    pair = build_instruction_pair("Widget Pro 1", "has_color", "black")
    assert pair["instruction"] == "Extract the has color of Widget Pro 1."
    assert pair["response"] == "The has color of Widget Pro 1 is black."


def _accepted_fixture():
    return {
        ("widget 1", "has_color", "black"): {
            "subject": "Widget 1", "predicate": "has_color", "object": "black",
            "confidence": 0.95, "provenance": ["evidence text"],
        },
        ("widget 1", "has_price_usd", "199"): {
            "subject": "Widget 1", "predicate": "has_price_usd", "object": "199",
            "confidence": 0.70,  # below threshold, must be excluded
        },
        ("widget 2", "has_color", "white"): {
            "subject": "Widget 2", "predicate": "has_color", "object": "white",
            "confidence": 0.92,
        },
    }


def test_filters_below_threshold():
    examples = generate_synthetic_examples(_accepted_fixture(), threshold=0.88)
    predicates = [e["predicate"] for e in examples]
    assert "has_price_usd" not in predicates
    assert len(examples) == 2


def test_balanced_sampling_caps_per_predicate():
    accepted = {}
    for i in range(10):
        accepted[(f"widget {i}", "has_color", "black")] = {
            "subject": f"Widget {i}", "predicate": "has_color", "object": "black",
            "confidence": 0.95,
        }
    examples = generate_synthetic_examples(accepted, threshold=0.88, max_per_predicate=3)
    assert len(examples) == 3


def test_save_jsonl_roundtrip(tmp_path):
    examples = generate_synthetic_examples(_accepted_fixture(), threshold=0.88)
    out_path = save_synthetic_jsonl(examples, tmp_path / "synth.jsonl")
    lines = out_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    import json
    row = json.loads(lines[0])
    assert "### Instruction:" in row["text"]
    assert "### Response:" in row["text"]
