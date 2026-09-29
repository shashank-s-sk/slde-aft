"""DEC-036 -- rerun the DEC-003 (dataset A, product657) and DEC-006 scale-up
(dataset B, product200) pipelines unchanged, with a chosen extractor and
per-token logprobs requested on every LLM call.

Each LLM observation carries both confidences: the verbalized one goes into
the KB as before (so the run itself is the pre-registered pipeline), and the
DEC-036 logprob confidences are prefixed to its provenance string as
"LP=<primary>;LPO=<object-only>|". Provenance is stored per observation but
never read by the pipeline, so both variants score identical observations.
`scripts/dec036_replay.py` swaps them in afterwards.

Usage: python -m scripts.dec036_run {A|B} <openrouter model id>
Pre-registration: Decision log.md, DEC-036 (commit 2f3a731).
"""

from __future__ import annotations

import importlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.extractors import openrouter_llm

MODULES = {"A": "scripts.dec003_product_probkb_run", "B": "scripts.dec006_scaleup_probkb_run"}
OUT_ROOT = Path("outputs/dec036")


def lp_tag(value) -> str:
    return "NA" if value is None else f"{value:.6f}"


def main() -> None:
    dataset, model = sys.argv[1], sys.argv[2]
    slug = model.split("/")[-1]
    mod = importlib.import_module(MODULES[dataset])
    out = OUT_ROOT / f"{dataset}_{slug}"
    mod.MODEL = model
    mod.OUTPUT_ROOT = out
    mod.EXPERIMENT_ID = f"DEC036_{dataset}_{slug}"

    side_log, raw_log = [], []

    # Within an iteration the locked context and feedback hint are fixed at
    # its start, so its calls are independent: prefetch them in parallel and
    # hand results back in the pipeline's own order (identical semantics).
    # A call whose key was not prefetched simply runs synchronously.
    split = mod.load_split()
    texts = {idx: row[1]["text"] for idx, *row in
             mod.generate_products(mod.N_PRODUCTS, seed=mod.GENERATION_SEED)}
    groups = [sorted(i for i, s in split.items() if s == "train"),
              sorted(i for i, s in split.items() if s == "val") + sorted(i for i, s in split.items() if s == "test")]
    pool = ThreadPoolExecutor(16)
    futures = {}

    def call(kw):
        # Retry transient provider failures (timeouts, 429, 5xx, 422 routing
        # refusals) so an observation is never silently dropped by the API;
        # a model-output failure ("no JSON array") is kept, as in the original runs.
        for attempt in range(6):
            result = openrouter_llm.extract_unstructured_llm(**kw, logprobs=True)
            err = str(result.get("error") or "")
            if not err or "no JSON array" in err or "JSON parse" in err or "402" in err:
                return result
            time.sleep(5 * 2 ** attempt)
        return result

    def key_of(kw):
        return (kw["source_id"], kw["doc_text"], tuple(kw.get("locked_context") or ()), kw.get("feedback_hint"))

    def extract_with_logprobs(**kwargs):
        k = key_of(kwargs)
        if k not in futures:
            idx = int(str(kwargs["source_id"]).split("_")[-1])
            for group in groups:
                if idx in group:
                    for j in group:
                        kw = dict(kwargs, source_id=f"product_{j}", doc_text=texts[j])
                        futures.setdefault(key_of(kw), pool.submit(call, kw))
            futures.setdefault(k, pool.submit(call, kwargs))
        result = futures.pop(k).result()
        if result.get("error") and ("402" in str(result["error"]) or "credits" in str(result["error"])):
            raise SystemExit(f"OpenRouter credit error, stopping so no partial run is scored: {result['error']}")
        raw_log.append({"source_id": kwargs.get("source_id"), "provider": result.get("provider"),
                        "content": result.get("content"), "token_logprobs": result.get("token_logprobs")})
        for t in result["triples"]:
            lp, lpo = t.pop("confidence_logprob", None), t.pop("confidence_logprob_object", None)
            t["provenance"] = f"LP={lp_tag(lp)};LPO={lp_tag(lpo)}|" + t["provenance"]
            side_log.append({
                "source_id": t["source_id"], "subject": t["subject"], "predicate": t["predicate"],
                "object": t["object"], "confidence_verbalized": t["confidence"],
                "confidence_logprob": lp, "confidence_logprob_object": lpo,
                "provider": result.get("provider"), "error": result.get("error"),
            })
        return result

    mod.extract_unstructured_llm = extract_with_logprobs
    mod.main()
    with open(out / "logprob_side_log.json", "w", encoding="utf-8") as f:
        json.dump(side_log, f, indent=1)
    with open(out / "logprob_raw_calls.json", "w", encoding="utf-8") as f:
        json.dump(raw_log, f)
    n_na = sum(r["confidence_logprob"] is None for r in side_log)
    providers = sorted({str(r["provider"]) for r in side_log})
    print(f"side log: {len(side_log)} LLM triples, {n_na} without a logprob confidence; providers {providers}")


if __name__ == "__main__":
    main()
