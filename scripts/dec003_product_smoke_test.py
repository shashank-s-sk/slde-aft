"""DEC-003 product-domain smoke test: 3 real products, structured +
OpenRouter LLM extraction, no PKB/feedback loop yet. Mirrors the
methodology of EVID-002 (CaRB 3-sentence smoke test) before scaling to
the full ~155-call instrumented run.

Usage: python -m scripts.dec003_product_smoke_test
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from src.datasets.product_generator import generate_products
from src.extractors.structured import extract_structured
from src.extractors.openrouter_llm import extract_unstructured_llm

MODEL = "meta-llama/llama-3.1-8b-instruct"
N_SMOKE = 3
OUTPUT_DIR = Path("outputs/dec003_product_smoke_3")


def load_api_key() -> str:
    env_path = Path(".env")
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def main():
    api_key = load_api_key()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    products = generate_products(N_SMOKE, seed=42)

    predictions = []
    gold_unstructured_all = []
    total_cost = 0.0
    total_latency = 0.0

    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in products:
        source_id = f"product_{idx}"

        structured_triples = extract_structured(structured_row, source_id=source_id)

        llm_result = extract_unstructured_llm(
            doc_text=unstructured_row["text"],
            source_id=source_id,
            api_key=api_key,
            model=MODEL,
        )

        cost = llm_result.get("cost_usd") or 0.0
        total_cost += cost
        total_latency += llm_result["latency_s"]

        predictions.append({
            "product_idx": idx,
            "product_name": structured_row["product_name"],
            "unstructured_text": unstructured_row["text"],
            "structured_triples": structured_triples,
            "llm_triples": llm_result["triples"],
            "llm_error": llm_result["error"],
            "http_status": llm_result["http_status"],
            "latency_s": llm_result["latency_s"],
            "cost_usd": cost,
            "prompt_tokens": llm_result["prompt_tokens"],
            "completion_tokens": llm_result["completion_tokens"],
        })

        gold_unstructured_all.extend(
            {"subject": s, "predicate": p, "object": o, "product_idx": idx}
            for s, p, o, _ in gold_unstructured
        )

        print(f"product_{idx}: {structured_row['product_name']} "
              f"| llm_triples={len(llm_result['triples'])} "
              f"| cost=${cost:.8f} | latency={llm_result['latency_s']:.2f}s "
              f"| error={llm_result['error']}")

    with open(OUTPUT_DIR / "predictions.json", "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    with open(OUTPUT_DIR / "gold_unstructured.json", "w", encoding="utf-8") as f:
        json.dump(gold_unstructured_all, f, indent=2)

    config = {
        "experiment_id": "DEC003_PRODUCT_SMOKE_3",
        "model": MODEL,
        "provider": "OpenRouter",
        "temperature": 0.0,
        "n_products": N_SMOKE,
        "generation_seed": 42,
        "total_cost_usd": total_cost,
        "total_latency_s": total_latency,
        "mean_latency_s": total_latency / N_SMOKE,
    }
    with open(OUTPUT_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print()
    print(f"TOTAL cost: ${total_cost:.8f} for {N_SMOKE} products")
    print(f"Mean latency: {total_latency / N_SMOKE:.2f}s")
    print(f"Saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
