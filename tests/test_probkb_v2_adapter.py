import json

from src.probkb_v2_adapter import CandidateBufferAdapter


def _make_adapter(tmp_path):
    policy_path = tmp_path / "functional_predicates.json"
    policy_path.write_text(
        json.dumps({"functional_predicates": ["has_color"]}),
        encoding="utf-8",
    )
    return CandidateBufferAdapter(
        experiment_id="TEST_EXP",
        run_id="run_1",
        prob_kb_version="v2",
        functional_predicates_path=str(policy_path),
        output_dir=str(tmp_path / "out"),
        threshold=0.88,
        gold_keys={("widget", "has_color", "black")},
        shrinkage=0.75,
    )


def test_end_iteration_writes_both_artifacts_without_crashing(tmp_path):
    adapter = _make_adapter(tmp_path)

    adapter.accept_candidate(
        subject="Widget",
        predicate="has_color",
        object_value="black",
        confidence=0.9,
        source_id="doc_1",
        source_type="unstructured",
        provenance="the widget is black",
    )

    adapter.end_iteration()

    out_dir = tmp_path / "out"
    obs_path = out_dir / "observations_iteration_1.csv"
    snap_path = out_dir / "pkb_snapshot_iteration_1.csv"
    assert obs_path.exists()
    assert snap_path.exists()

    obs_text = obs_path.read_text(encoding="utf-8")
    assert "widget|has_color|black" in obs_text

    snap_text = snap_path.read_text(encoding="utf-8")
    assert "widget|has_color|black" in snap_text


def test_pending_observations_reset_between_iterations(tmp_path):
    adapter = _make_adapter(tmp_path)

    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.9, source_id="doc_1", source_type="unstructured",
        provenance="p1",
    )
    adapter.end_iteration()
    assert adapter.pending_observations == []

    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.85, source_id="doc_2", source_type="unstructured",
        provenance="p2",
    )
    adapter.end_iteration()

    iter2_obs = (tmp_path / "out" / "observations_iteration_2.csv").read_text(encoding="utf-8")
    # Only the second observation should appear in iteration 2's file.
    assert iter2_obs.count("widget|has_color|black") == 1


def test_conflict_adjustment_applies_to_functional_predicate(tmp_path):
    adapter = _make_adapter(tmp_path)

    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="black",
        confidence=0.9, source_id="doc_1", source_type="unstructured",
        provenance="p1",
    )
    adapter.accept_candidate(
        subject="Widget", predicate="has_color", object_value="white",
        confidence=0.9, source_id="doc_2", source_type="unstructured",
        provenance="p2",
    )

    black_entry = adapter.accepted[("widget", "has_color", "black")]
    white_entry = adapter.accepted[("widget", "has_color", "white")]

    assert black_entry["competitor_count"] == 1
    assert white_entry["competitor_count"] == 1
    # conflict adjustment divides support by (competitors + 1)
    assert black_entry["confidence"] < black_entry["support"]
