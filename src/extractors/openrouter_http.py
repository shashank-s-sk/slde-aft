"""Shared OpenRouter POST with retries for transient network failures.

Before this module, both extractors called requests.post directly, so a
single timeout or dropped connection raised out of the extractor and
killed the whole experiment process -- twice during DEC-029 (EVID-045).
Only network-level failures are retried here. An HTTP response of any
status, including an unparsable model answer, is returned as-is,
because it is a real outcome of the call.
"""

from __future__ import annotations

import time

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NETWORK_RETRIES = 3  # extra attempts after the first, network errors only
NETWORK_BACKOFF_S = 2.0  # waits 2s, 4s, 8s between attempts


def post_with_network_retry(
    headers: dict,
    payload: dict,
    timeout: int,
    retries: int = NETWORK_RETRIES,
    backoff_s: float = NETWORK_BACKOFF_S,
) -> tuple[requests.Response | None, int, str | None]:
    """Returns (response, retries_used, error). `response` is None only if
    every attempt failed at the network level; `error` then describes the
    last failure."""
    last_error = None
    for attempt in range(retries + 1):
        try:
            return requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout), attempt, None
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff_s * 2 ** attempt)
    return None, retries, (f"network error after {retries + 1} attempts: "
                           f"{type(last_error).__name__}: {last_error}")
