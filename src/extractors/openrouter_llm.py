"""OpenRouter LLM extractor. Ported from the SLDE-AFT notebooks'
`call_openrouter_for_triples` / `extract_unstructured_llm` cells, with the
API key read from the environment (never hard-coded) and per-call
latency/cost returned so callers can log them.
"""

from __future__ import annotations

import json
import re
import time

import requests

from src.datasets.product_generator import ALLOWED_PREDICATES

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_prompt(text: str, locked_context=None, feedback_hint: str | None = None) -> str:
    locked_block = "\n".join(locked_context) if locked_context else "None"
    feedback_block = feedback_hint if feedback_hint else "None"

    return f"""You extract factual product knowledge triples.

Return ONLY a valid JSON array.
Each object must contain: subject, predicate, object, confidence

Allowed predicates:
{", ".join(ALLOWED_PREDICATES)}

Rules:
- Extract only facts explicitly stated in the input text.
- Do not hallucinate.
- Output confidence between 0.80 and 0.96.

Locked knowledge (guidance only, do not repeat blindly):
{locked_block}

Feedback hint (guidance only):
{feedback_block}

Input text:
{text}

Example output:
[
  {{"subject":"TechNova Smartphone Pro 1","predicate":"has_ram_gb","object":"8","confidence":0.91}}
]""".strip()


def call_openrouter_for_triples(
    text: str,
    api_key: str,
    model: str,
    locked_context=None,
    feedback_hint: str | None = None,
    temperature: float = 0.0,
    timeout: int = 90,
    max_tokens: int = 512,
) -> dict:
    """Returns a dict with: items (parsed triples), raw_response, latency_s,
    cost_usd, prompt_tokens, completion_tokens, http_status, error.

    max_tokens is capped explicitly (default 512) because every real
    extraction call observed so far has used well under 300 completion
    tokens (a handful of JSON triples) — without this cap, OpenRouter
    pre-authorizes credits against the model's full context window
    (100K+ tokens) rather than what the call will actually use, which
    can trigger a spurious HTTP 402 "insufficient credits" on a low but
    genuinely sufficient balance. See Evidence log.md EVID-018.
    """

    prompt = build_prompt(text, locked_context=locked_context, feedback_hint=feedback_hint)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "SLDE-AFT-DEC003-Smoke-Test",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    t0 = time.perf_counter()
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
    latency_s = time.perf_counter() - t0

    result = {
        "items": [],
        "raw_response": None,
        "latency_s": latency_s,
        "cost_usd": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "http_status": r.status_code,
        "error": None,
    }

    try:
        response_json = r.json()
    except Exception as e:
        result["error"] = f"non-JSON response: {e}"
        return result

    result["raw_response"] = response_json

    if "error" in response_json or "choices" not in response_json:
        result["error"] = str(response_json.get("error", "no choices"))
        return result

    usage = response_json.get("usage", {})
    result["cost_usd"] = usage.get("cost")
    result["prompt_tokens"] = usage.get("prompt_tokens")
    result["completion_tokens"] = usage.get("completion_tokens")

    content = response_json["choices"][0]["message"]["content"]
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        result["error"] = "no JSON array found in model output"
        return result

    try:
        arr = json.loads(match.group(0))
        result["items"] = arr if isinstance(arr, list) else []
    except Exception as e:
        result["error"] = f"JSON parse error: {e}"

    return result


def extract_unstructured_llm(
    doc_text: str,
    source_id: str,
    api_key: str,
    model: str,
    locked_context=None,
    feedback_hint: str | None = None,
    extractor_tag: str = "openrouter",
) -> dict:
    """Returns dict with: triples (list of common-schema dicts) plus the
    same latency/cost/error fields as call_openrouter_for_triples."""

    call_result = call_openrouter_for_triples(
        doc_text,
        api_key=api_key,
        model=model,
        locked_context=locked_context,
        feedback_hint=feedback_hint,
    )

    triples = []
    for item in call_result["items"]:
        if all(k in item for k in ("subject", "predicate", "object", "confidence")):
            pred = str(item["predicate"]).strip()
            if pred in ALLOWED_PREDICATES:
                triples.append({
                    "subject": str(item["subject"]).strip(),
                    "predicate": pred,
                    "object": str(item["object"]).strip(),
                    "confidence": float(item["confidence"]),
                    "source_id": source_id,
                    "provenance": doc_text[:1000],
                    "source_type": "unstructured",
                    "extractor_version": extractor_tag,
                })

    call_result["triples"] = triples
    return call_result
