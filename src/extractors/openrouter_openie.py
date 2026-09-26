"""Generic OpenIE extractor — model- and prompt-parameterized so the
same protocol can be run against any OpenRouter model (SLDE-AFT's own
pinned model, or an external baseline like DeepSeek) and any prompt
template (CaRB's open-relation prompt by default, or a schema-
constrained one like BioRED's — DEC-009), satisfying DEC-002's fairness
rule: same input, same prompt, same evaluator, only the model differs.

Unlike src/extractors/openrouter_llm.py (product-domain, ALLOWED_PREDICATES
baked into that module's own prompt), this module takes its prompt
template as data, so it works for any {SENTENCE}-templated prompt file.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from src.extractors.openrouter_http import post_with_network_retry

DEFAULT_PROMPT_TEMPLATE = Path("prompts/openie_carb_v1.txt").read_text(encoding="utf-8")


def extract_openie_triples(
    sentence: str,
    api_key: str,
    model: str,
    prompt_template: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
    timeout: int = 90,
    keep_evidence: bool = False,
) -> dict:
    """Returns dict with: triples (list of {subject,predicate,object}),
    error, http_status, latency_s, cost_usd, raw_content_on_error.

    keep_evidence (DEC-033 document-level prompts): also keep each item's
    "evidence" field, normalised to a sorted list of distinct integer
    sentence indices (non-integer entries are dropped)."""

    template = prompt_template if prompt_template is not None else DEFAULT_PROMPT_TEMPLATE
    prompt = template.replace("{SENTENCE}", sentence)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "SLDE-AFT-DEC001-002-CaRB30",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    t0 = time.perf_counter()
    r, network_retries, network_error = post_with_network_retry(headers, payload, timeout)
    latency_s = time.perf_counter() - t0

    result = {
        "triples": [], "error": None, "http_status": r.status_code if r is not None else None,
        "latency_s": latency_s, "cost_usd": None, "network_retries": network_retries,
    }

    if r is None:
        result["error"] = network_error
        return result

    try:
        response_json = r.json()
    except Exception as e:
        result["error"] = f"non-JSON response: {e}"
        return result

    if "error" in response_json or "choices" not in response_json:
        result["error"] = str(response_json.get("error", "no choices"))
        return result

    usage = response_json.get("usage", {})
    result["cost_usd"] = usage.get("cost")

    content = response_json["choices"][0]["message"]["content"]
    if content is None:
        # Some providers (observed with google/gemini-2.5-pro via
        # OpenRouter) can return a null content field -- e.g. the model
        # spent its whole token budget on internal reasoning and never
        # produced a final answer. Treat as a normal extraction failure,
        # not a crash.
        result["error"] = "model returned null content"
        result["raw_content_on_error"] = None
        return result
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        result["error"] = "no JSON array found in model output"
        result["raw_content_on_error"] = content
        return result

    try:
        arr = json.loads(match.group(0))
    except Exception as e:
        result["error"] = f"JSON parse error: {e}"
        result["raw_content_on_error"] = content
        return result

    triples = []
    for item in arr if isinstance(arr, list) else []:
        if all(k in item for k in ("subject", "predicate", "object")):
            triple = {
                "subject": str(item["subject"]).strip(),
                "predicate": str(item["predicate"]).strip(),
                "object": str(item["object"]).strip(),
            }
            if keep_evidence:
                ev = item.get("evidence", [])
                ev = ev if isinstance(ev, list) else [ev]
                idx = set()
                for e in ev:
                    try:
                        idx.add(int(e))
                    except (TypeError, ValueError):
                        continue
                triple["evidence"] = sorted(idx)
            triples.append(triple)
    result["triples"] = triples
    return result
