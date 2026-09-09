import json

from src.pkb_instrumentation import (
    build_snapshot_dataframe,
    competitor_count,
    is_functional_predicate,
    normalized_object,
    normalized_slot,
    refresh_slot_scores,
    save_iteration_artifacts,
)


def test_normalized_slot():
    assert normalized_slot(
        " Product-A ",
        " has_color ",
    ) == ("product-a", "has_color")


def test_normalized_object():
    assert normalized_object(" Black ") == "black"


def test_functional_predicate_policy():
    functional_predicates = {
        "has_color",
        "has_noise_cancellation",
    }

    assert is_functional_predicate(
        "has_color",
        functional_predicates,
    ) is True

    assert is_functional_predicate(
        "made_of_material",
        functional_predicates,
    ) is False


def test_competitor_count():
    accepted = {
        ("product-a", "has_color", "black"): {
            "subject": "Product-A",
            "predicate": "has_color",
            "object": "black",
        },
        ("product-a", "has_color", "white"): {
            "subject": "Product-A",
            "predicate": "has_color",
            "object": "white",
        },
    }

    assert competitor_count(
        accepted=accepted,
        subject="Product-A",
        predicate="has_color",
        object_value="black",
    ) == 1

    assert competitor_count(
        accepted=accepted,
        subject="Product-A",
        predicate="has_color",
        object_value="white",
    ) == 1


def test_refresh_slot_scores_applies_functional_penalty():
    accepted = {
        ("product-a", "has_noise_cancellation", "yes"): {
            "subject": "Product-A",
            "predicate": "has_noise_cancellation",
            "object": "yes",
            "confidence": 0.90,
            "all_confidences": [0.90, 0.92],
            "source_ids": ["source-1", "source-2"],
            "source_types": ["unstructured", "unstructured"],
            "provenance": ["evidence-1", "evidence-2"],
            "status": "candidate",
        },
        ("product-a", "has_noise_cancellation", "no"): {
            "subject": "Product-A",
            "predicate": "has_noise_cancellation",
            "object": "no",
            "confidence": 0.70,
            "all_confidences": [0.70],
            "source_ids": ["source-3"],
            "source_types": ["unstructured"],
            "provenance": ["conflicting evidence"],
            "status": "candidate",
        },
    }

    refresh_slot_scores(
        accepted=accepted,
        subject="Product-A",
        predicate="has_noise_cancellation",
        functional_predicates={"has_noise_cancellation"},
    )

    yes_entry = accepted[
        ("product-a", "has_noise_cancellation", "yes")
    ]

    no_entry = accepted[
        ("product-a", "has_noise_cancellation", "no")
    ]

    assert yes_entry["functional_predicate"] is True
    assert no_entry["functional_predicate"] is True
    assert yes_entry["competitor_count"] == 1
    assert no_entry["competitor_count"] == 1
    assert yes_entry["confidence"] == (
        yes_entry["support"] / 2.0
    )
    assert no_entry["confidence"] == (
        no_entry["support"] / 2.0
    )


def test_refresh_slot_scores_keeps_nonfunctional_score_equal_support():
    accepted = {
        ("product-b", "made_of_material", "aluminum"): {
            "subject": "Product-B",
            "predicate": "made_of_material",
            "object": "aluminum",
            "confidence": 0.85,
            "all_confidences": [0.85],
            "source_ids": ["source-4"],
            "source_types": ["structured"],
            "provenance": ["material evidence"],
            "status": "candidate",
        },
    }

    refresh_slot_scores(
        accepted=accepted,
        subject="Product-B",
        predicate="made_of_material",
        functional_predicates={"has_noise_cancellation"},
    )

    entry = accepted[
        ("product-b", "made_of_material", "aluminum")
    ]

    assert entry["functional_predicate"] is False
    assert entry["competitor_count"] == 0
    assert entry["confidence"] == entry["support"]


def test_snapshot_contains_required_columns():
    accepted = {
        ("product-a", "has_color", "black"): {
            "subject": "Product-A",
            "predicate": "has_color",
            "object": "black",
            "confidence": 0.40,
            "support": 0.80,
            "all_confidences": [0.80],
            "source_ids": ["source-1"],
            "source_types": ["unstructured"],
            "provenance": ["Product-A is black."],
            "functional_predicate": True,
            "competitor_count": 1,
            "status": "candidate",
        }
    }

    snapshot_df = build_snapshot_dataframe(
        accepted=accepted,
        experiment_id="DEC003_TEST",
        run_id="run_001",
        iteration=1,
        prob_kb_version="prob_kb_v2",
        threshold=0.88,
        gold_keys=None,
    )

    required_columns = {
        "experiment_id",
        "run_id",
        "prob_kb_version",
        "iteration",
        "triple_key",
        "observation_count",
        "observation_confidences",
        "functional_predicate",
        "competitor_count",
        "conservative_noisy_or_support",
        "conflict_adjusted_final_confidence",
        "threshold",
        "above_threshold",
        "previous_final_confidence",
        "crossed_threshold_up",
        "crossed_threshold_down",
        "source_ids",
        "source_types",
        "provenance",
        "kb_size",
        "status",
    }

    assert required_columns.issubset(snapshot_df.columns)
    assert len(snapshot_df) == 1


def test_snapshot_marks_initial_threshold_crossing():
    accepted = {
        ("product-a", "has_color", "black"): {
            "subject": "Product-A",
            "predicate": "has_color",
            "object": "black",
            "confidence": 0.90,
            "support": 0.90,
            "all_confidences": [0.90],
            "source_ids": ["source-1"],
            "source_types": ["unstructured"],
            "provenance": ["Product-A is black."],
            "functional_predicate": True,
            "competitor_count": 0,
            "status": "locked",
        }
    }

    snapshot_df = build_snapshot_dataframe(
        accepted=accepted,
        experiment_id="DEC003_TEST",
        run_id="run_001",
        iteration=1,
        prob_kb_version="prob_kb_v2",
        threshold=0.88,
        gold_keys=None,
    )

    row = snapshot_df.iloc[0]

    assert bool(row["above_threshold"]) is True
    assert bool(row["crossed_threshold_up"]) is True
    assert bool(row["crossed_threshold_down"]) is False