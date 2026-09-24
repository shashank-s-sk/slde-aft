import pytest
import requests

import src.extractors.openrouter_http as http
from src.extractors.openrouter_llm import call_openrouter_for_triples
from src.extractors.openrouter_openie import extract_openie_triples


class FakeResponse:
    status_code = 200

    def json(self):
        return {
            "choices": [{"message": {"content": '[{"subject": "A", "predicate": "p", "object": "B"}]'}}],
            "usage": {"cost": 0.00001},
        }


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(http.time, "sleep", lambda s: None)


def fail_then_succeed(monkeypatch, n_failures, exc):
    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] <= n_failures:
            raise exc
        return FakeResponse()

    monkeypatch.setattr(http.requests, "post", fake_post)
    return calls


@pytest.mark.parametrize("exc", [
    requests.exceptions.ReadTimeout("read timed out"),
    requests.exceptions.ChunkedEncodingError("Response ended prematurely"),
    requests.exceptions.ConnectionError("connection reset"),
])
def test_transient_network_error_is_retried(monkeypatch, exc):
    calls = fail_then_succeed(monkeypatch, 2, exc)
    r, retries, error = http.post_with_network_retry({}, {}, timeout=1)
    assert r is not None and retries == 2 and error is None
    assert calls["n"] == 3


def test_persistent_network_error_is_returned_not_raised(monkeypatch):
    calls = fail_then_succeed(monkeypatch, 99, requests.exceptions.ReadTimeout("read timed out"))
    r, retries, error = http.post_with_network_retry({}, {}, timeout=1)
    assert r is None
    assert calls["n"] == http.NETWORK_RETRIES + 1
    assert "ReadTimeout" in error


def test_llm_extractor_records_network_failure_as_failed_call(monkeypatch):
    fail_then_succeed(monkeypatch, 99, requests.exceptions.ChunkedEncodingError("cut off"))
    result = call_openrouter_for_triples("text", api_key="k", model="m")
    assert result["http_status"] is None
    assert result["items"] == []
    assert "ChunkedEncodingError" in result["error"]


def test_openie_extractor_records_network_failure_as_failed_call(monkeypatch):
    fail_then_succeed(monkeypatch, 99, requests.exceptions.ConnectionError("down"))
    result = extract_openie_triples("A sentence.", api_key="k", model="m")
    assert result["http_status"] is None
    assert result["triples"] == []
    assert "ConnectionError" in result["error"]


def test_extractors_unchanged_on_success_after_retry(monkeypatch):
    fail_then_succeed(monkeypatch, 1, requests.exceptions.ReadTimeout("slow"))
    result = extract_openie_triples("A sentence.", api_key="k", model="m")
    assert result["error"] is None
    assert result["triples"] == [{"subject": "A", "predicate": "p", "object": "B"}]
    assert result["network_retries"] == 1
