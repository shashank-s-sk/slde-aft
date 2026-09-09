from __future__ import annotations

from math import prod
from typing import Iterable


DEFAULT_SHRINKAGE = 0.75


def validate_confidence(value: float) -> float:
    """Validate one observation confidence in the closed interval [0, 1]."""
    value = float(value)

    if not 0.0 <= value <= 1.0:
        raise ValueError(f"Confidence must be in [0, 1], got {value}")

    return value


def validate_shrinkage(value: float) -> float:
    """Validate lambda in the interval (0, 1]."""
    value = float(value)

    if not 0.0 < value <= 1.0:
        raise ValueError(f"Shrinkage must be in (0, 1], got {value}")

    return value


def conservative_noisy_or(
    confidences: Iterable[float],
    shrinkage: float = DEFAULT_SHRINKAGE,
) -> float:
    """
    Compute A_t = 1 - product_i(1 - lambda * c_i).

    This returns the conservative Noisy-Or support score before any
    functionally single-valued predicate conflict adjustment.
    """
    shrinkage = validate_shrinkage(shrinkage)
    values = [validate_confidence(confidence) for confidence in confidences]

    if not values:
        return 0.0

    residual_support = prod(
        1.0 - shrinkage * confidence
        for confidence in values
    )

    return 1.0 - residual_support


def conflict_adjusted_confidence(
    support: float,
    competitor_count: int,
) -> float:
    """
    Compute C_t = A_t / (m_t + 1).

    Call this only for predicates explicitly designated as functionally
    single-valued in the experiment configuration.
    """
    support = validate_confidence(support)

    if not isinstance(competitor_count, int) or competitor_count < 0:
        raise ValueError(
            "competitor_count must be a non-negative integer"
        )

    return support / (competitor_count + 1)


def final_confidence(
    confidences: Iterable[float],
    competitor_count: int = 0,
    shrinkage: float = DEFAULT_SHRINKAGE,
    functional_predicate: bool = False,
) -> float:
    """
    Return the final PKB score.

    For non-functional predicates, return A_t.
    For functionally single-valued predicates, return A_t / (m_t + 1).
    """
    support = conservative_noisy_or(
        confidences=confidences,
        shrinkage=shrinkage,
    )

    if functional_predicate:
        return conflict_adjusted_confidence(
            support=support,
            competitor_count=competitor_count,
        )

    return support


def max_merge(confidences: Iterable[float]) -> float:
    """Compute max_i(c_i)."""
    values = [validate_confidence(confidence) for confidence in confidences]
    return max(values, default=0.0)


def mean_aggregation(confidences: Iterable[float]) -> float:
    """Compute the arithmetic mean of observation confidences."""
    values = [validate_confidence(confidence) for confidence in confidences]

    if not values:
        return 0.0

    return sum(values) / len(values)


def standard_noisy_or(confidences: Iterable[float]) -> float:
    """Compute 1 - product_i(1 - c_i)."""
    values = [validate_confidence(confidence) for confidence in confidences]

    if not values:
        return 0.0

    residual_support = prod(
        1.0 - confidence
        for confidence in values
    )

    return 1.0 - residual_support