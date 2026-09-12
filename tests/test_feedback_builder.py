from src.feedback_builder import build_feedback_hint


def test_reports_missed_gold_facts():
    hint = build_feedback_hint(
        accepted_keys=set(),
        gold_keys={("widget", "has_color", "black")},
        allowed_predicates=["has_color"],
    )
    assert "widget | has_color | black" in hint


def test_reports_false_patterns_not_in_gold():
    hint = build_feedback_hint(
        accepted_keys={("widget", "has_color", "purple")},
        gold_keys={("widget", "has_color", "black")},
        allowed_predicates=["has_color"],
    )
    assert "widget | has_color | purple" in hint


def test_empty_when_fully_covered_and_no_gaps():
    key = ("widget", "has_color", "black")
    hint = build_feedback_hint(
        accepted_keys={key, key},
        gold_keys={key},
        allowed_predicates=["has_color"],
    )
    assert "Missing facts" not in hint
    assert "Avoid unsupported" not in hint
