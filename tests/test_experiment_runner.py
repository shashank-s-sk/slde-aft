import pytest

import src.experiment_runner as runner
from src.experiment_runner import ExperimentConfig, run_experiment
from src.deterministic_kb_adapter import DeterministicKBAdapter
from src.probkb_v2_adapter import CandidateBufferAdapter

N_PRODUCTS = 8  # gives 3 train / 2 val / 3 test with the real split file


@pytest.fixture
def mock_llm(monkeypatch):
    captured_calls = []

    def fake_extract(doc_text, source_id, api_key, model, locked_context=None,
                      feedback_hint=None, extractor_tag="openrouter"):
        captured_calls.append({"feedback_hint": feedback_hint, "locked_context": locked_context})
        return {
            "triples": [{
                "subject": "FakeProduct", "predicate": "has_color", "object": "black",
                "confidence": 0.9, "source_id": source_id, "provenance": doc_text[:50],
                "source_type": "unstructured", "extractor_version": extractor_tag,
            }],
            "error": None, "http_status": 200, "latency_s": 0.0,
            "cost_usd": 0.0, "prompt_tokens": 1, "completion_tokens": 1,
        }

    monkeypatch.setattr(runner, "extract_unstructured_llm", fake_extract)
    return captured_calls


def _base_config(tmp_path, **overrides):
    defaults = dict(
        config_name="test", experiment_id="TEST_ABLATION",
        output_root=str(tmp_path / "out"), n_products=N_PRODUCTS,
        n_iterations=2,
    )
    defaults.update(overrides)
    return ExperimentConfig(**defaults)


def test_full_config_runs_all_iterations_and_held_out(tmp_path, mock_llm):
    config = _base_config(tmp_path)
    result = run_experiment(config, api_key="fake")
    assert len(result["iteration_metrics"]) == 2
    assert result["held_out_metrics"] is not None
    assert {row["split"] for row in result["held_out_metrics"]} == {"val", "test"}
    assert isinstance(result["kb"], CandidateBufferAdapter)


def test_without_prob_kb_uses_deterministic_adapter(tmp_path, mock_llm):
    config = _base_config(tmp_path, use_prob_kb=False)
    result = run_experiment(config, api_key="fake")
    assert isinstance(result["kb"], DeterministicKBAdapter)


def test_without_feedback_never_passes_a_hint(tmp_path, mock_llm):
    config = _base_config(tmp_path, use_feedback=False, n_iterations=2)
    run_experiment(config, api_key="fake")
    assert all(call["feedback_hint"] is None for call in mock_llm)


def test_with_feedback_passes_a_hint_after_iteration_1(tmp_path, mock_llm):
    config = _base_config(tmp_path, use_feedback=True, n_iterations=2)
    result = run_experiment(config, api_key="fake")
    n_train = result["n_train"]
    # First n_train calls are iteration 1 (no feedback yet); later calls
    # (iteration 2 train + held-out) should carry a feedback hint since
    # the mocked LLM always returns a triple that won't match train gold.
    later_calls = mock_llm[n_train:]
    assert any(call["feedback_hint"] is not None for call in later_calls)


def test_structured_only_skips_llm_and_held_out(tmp_path, mock_llm):
    config = _base_config(tmp_path, use_unstructured=False, use_structured=True)
    result = run_experiment(config, api_key="fake")
    assert len(mock_llm) == 0  # no LLM calls at all
    assert len(result["iteration_metrics"]) == 1  # forced to 1 iteration
    assert result["iteration_metrics"][0]["precision"] is None
    assert result["held_out_metrics"] is None
    assert result["kb"].get_accepted()  # structured triples still populate the KB


def test_unstructured_only_skips_structured_seeding(tmp_path, mock_llm):
    config = _base_config(tmp_path, use_structured=False, use_unstructured=True, n_iterations=1)
    result = run_experiment(config, api_key="fake")
    accepted = result["kb"].get_accepted()
    # Every accepted triple must come from the mocked LLM (confidence 0.9),
    # never from the structured extractor (confidence 0.98).
    assert all(abs(v["confidence"] - 0.9) < 1e-9 or "all_confidences" in v for v in accepted.values())
    confidences = [c for v in accepted.values() for c in v["all_confidences"]]
    assert 0.98 not in confidences
