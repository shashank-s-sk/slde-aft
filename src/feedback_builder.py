"""Feedback-hint builder. Ported from the notebooks' `FeedbackBuilder` cell
as a standalone function so DEC-004's "without Feedback Controller"
ablation can toggle this call on/off around the same implementation
instead of duplicating the logic.
"""

from __future__ import annotations

from collections import Counter


def build_feedback_hint(
    accepted_keys: set[tuple[str, str, str]],
    gold_keys: set[tuple[str, str, str]],
    allowed_predicates: list[str],
    max_missed: int = 8,
    max_false_patterns: int = 6,
    max_coverage_gaps: int = 8,
) -> str:
    false_patterns = list(accepted_keys - gold_keys)[:max_false_patterns]
    missed = list(gold_keys - accepted_keys)[:max_missed]

    pred_counts = Counter(k[1] for k in accepted_keys)
    coverage_gaps = [
        p for p in allowed_predicates if pred_counts.get(p, 0) < 2
    ][:max_coverage_gaps]

    blocks = []
    if missed:
        blocks.append(
            "Missing facts to recover when explicitly supported:\n"
            + "\n".join(f"- {s} | {p} | {o}" for s, p, o in missed)
        )
    if false_patterns:
        blocks.append(
            "Avoid unsupported patterns like:\n"
            + "\n".join(f"- {s} | {p} | {o}" for s, p, o in false_patterns)
        )
    if coverage_gaps:
        blocks.append(
            "Undercovered predicates — try to extract these:\n"
            + "\n".join(f"- {p}" for p in coverage_gaps)
        )
    return "\n\n".join(blocks).strip()
