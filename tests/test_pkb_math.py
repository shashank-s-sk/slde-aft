import pytest

from src.pkb_math import (
    DEFAULT_SHRINKAGE,
    conflict_adjusted_confidence,
    conservative_noisy_or,
    final_confidence,
    max_merge,
    mean_aggregation,
    standard_noisy_or,
)


def test_empty_observation_list_has_zero_support():
    assert conservative_noisy_or([]) == 0.0


def test_single_observation_uses_shrinkage():
    result = conservative_noisy_or(
        [0.80],
        shrinkage=DEFAULT_SHRINKAGE,
    )

    assert result == pytest.approx(0.60)


def test_support_is_bounded():
    result = conservative_noisy_or([0.20, 0.70, 0.95])

    assert 0.0 <= result <= 1.0


def test_evidence_monotonicity_for_fixed_conflict_set():
    before = conservative_noisy_or([0.60], shrinkage=0.75)
    after = conservative_noisy_or([0.60, 0.40], shrinkage=0.75)

    assert after >= before


def test_conflict_adjustment_divides_by_competitors_plus_one():
    support = conservative_noisy_or([0.80], shrinkage=0.75)

    result = conflict_adjusted_confidence(
        support=support,
        competitor_count=2,
    )

    assert result == pytest.approx(support / 3.0)


def test_nonfunctional_predicate_does_not_get_conflict_penalty():
    support = conservative_noisy_or([0.80], shrinkage=0.75)

    result = final_confidence(
        confidences=[0.80],
        competitor_count=3,
        shrinkage=0.75,
        functional_predicate=False,
    )

    assert result == pytest.approx(support)


def test_functional_predicate_gets_conflict_penalty():
    support = conservative_noisy_or([0.80], shrinkage=0.75)

    result = final_confidence(
        confidences=[0.80],
        competitor_count=3,
        shrinkage=0.75,
        functional_predicate=True,
    )

    assert result == pytest.approx(support / 4.0)


def test_aggregation_rules_are_bounded():
    confidences = [0.30, 0.70]

    scores = [
        max_merge(confidences),
        mean_aggregation(confidences),
        standard_noisy_or(confidences),
        conservative_noisy_or(confidences),
    ]

    assert all(0.0 <= score <= 1.0 for score in scores)


def test_invalid_confidence_raises_error():
    with pytest.raises(ValueError):
        conservative_noisy_or([1.01])


def test_invalid_shrinkage_raises_error():
    with pytest.raises(ValueError):
        conservative_noisy_or([0.50], shrinkage=0.0)

def test_dynamic_conflict_can_reduce_final_confidence():
    support_before = conservative_noisy_or(
        [0.90],
        shrinkage=0.75,
    )

    support_after = conservative_noisy_or(
        [0.90, 0.10],
        shrinkage=0.75,
    )

    confidence_before = final_confidence(
        confidences=[0.90],
        competitor_count=0,
        shrinkage=0.75,
        functional_predicate=True,
    )

    confidence_after = final_confidence(
        confidences=[0.90, 0.10],
        competitor_count=1,
        shrinkage=0.75,
        functional_predicate=True,
    )

    assert support_after >= support_before
    assert confidence_after < confidence_before