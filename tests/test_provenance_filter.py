from src.provenance_filter import has_structured_corroboration, passes_provenance_filter


def test_structured_and_unstructured_passes():
    assert has_structured_corroboration(["structured", "unstructured", "unstructured"]) is True


def test_structured_only_passes():
    assert has_structured_corroboration(["structured"]) is True


def test_unstructured_only_fails():
    assert has_structured_corroboration(["unstructured", "unstructured", "unstructured"]) is False


def test_empty_fails():
    assert has_structured_corroboration([]) is False


def test_passes_provenance_filter_entry_dict():
    assert passes_provenance_filter({"source_types": ["structured", "unstructured"]}) is True
    assert passes_provenance_filter({"source_types": ["unstructured", "unstructured"]}) is False
    assert passes_provenance_filter({}) is False
