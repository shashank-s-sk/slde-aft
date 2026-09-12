from src.deterministic_kb_adapter import DeterministicKBAdapter


def _make_adapter(tmp_path):
    return DeterministicKBAdapter(
        experiment_id="TEST_EXP",
        run_id="run_1",
        output_dir=str(tmp_path / "out"),
        threshold=0.88,
        gold_keys={("widget", "has_color", "black")},
        min_conf=0.80,
    )


def test_confidence_is_max_merge_not_noisy_or(tmp_path):
    adapter = _make_adapter(tmp_path)
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.85, source_id="doc_1", source_type="unstructured", provenance="p1",
    )
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.90, source_id="doc_2", source_type="unstructured", provenance="p2",
    )
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.70, source_id="doc_3", source_type="unstructured", provenance="p3",
    )
    entry = adapter.accepted[("widget", "has_color", "black")]
    assert entry["confidence"] == 0.90  # max, not aggregated


def test_below_min_conf_first_observation_is_rejected(tmp_path):
    adapter = _make_adapter(tmp_path)
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.5, source_id="doc_1", source_type="unstructured", provenance="p1",
    )
    assert ("widget", "has_color", "black") not in adapter.accepted


def test_no_conflict_penalty_ever_applied(tmp_path):
    adapter = _make_adapter(tmp_path)
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.9, source_id="doc_1", source_type="unstructured", provenance="p1",
    )
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="white",
        confidence=0.9, source_id="doc_2", source_type="unstructured", provenance="p2",
    )
    black = adapter.accepted[("widget", "has_color", "black")]
    white = adapter.accepted[("widget", "has_color", "white")]
    assert black["confidence"] == 0.9
    assert white["confidence"] == 0.9
    assert black["competitor_count"] == 0  # deterministic KB never computes this


def test_end_iteration_writes_artifacts(tmp_path):
    adapter = _make_adapter(tmp_path)
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.9, source_id="doc_1", source_type="unstructured", provenance="p1",
    )
    adapter.end_iteration()
    out_dir = tmp_path / "out"
    assert (out_dir / "observations_iteration_1.csv").exists()
    assert (out_dir / "pkb_snapshot_iteration_1.csv").exists()
    assert adapter.pending_observations == []
