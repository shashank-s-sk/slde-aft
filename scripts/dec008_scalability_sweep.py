"""DEC-008 scalability sweep — scoped version (per user decision:
sizes 20/50/100/200, single-pass extraction rather than the full
4-iteration closed loop, ~45-50 min instead of 6+ hours). Measures how
runtime, per-document latency, memory, KB size, and conflict count
scale with dataset size — the actual question DEC-008 asks — without
re-testing extraction quality (already covered by DEC-003/004/005).

Usage: python -m scripts.dec008_scalability_sweep
"""

from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path

import psutil

from src.datasets.product_generator import generate_products
from src.extractors.structured import extract_structured
from src.extractors.openrouter_llm import extract_unstructured_llm
from src.probkb_v2_adapter import CandidateBufferAdapter

SIZES = [20, 50, 100, 200]
MODEL = "meta-llama/llama-3.1-8b-instruct"
OUTPUT_ROOT = Path("outputs/dec008_scalability")
PROCESS = psutil.Process(os.getpid())


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def mem_mb() -> float:
    return PROCESS.memory_info().rss / (1024 * 1024)


def run_one_size(n_products: int, api_key: str) -> dict:
    print(f"\n=== N={n_products} ===", flush=True)
    out_dir = OUTPUT_ROOT / f"n_{n_products}"

    mem_before = mem_mb()
    t0 = time.perf_counter()

    products = generate_products(n_products, seed=42)

    adapter = CandidateBufferAdapter(
        experiment_id="DEC008_SCALABILITY", run_id=f"n_{n_products}",
        prob_kb_version="conservative_noisy_or_conflict_adjusted",
        functional_predicates_path="configs/functional_predicates_product_domain.json",
        output_dir=str(out_dir), threshold=0.88, shrinkage=0.75,
    )

    total_cost = 0.0
    n_errors = 0
    latencies = []

    for idx, structured_row, unstructured_row, _, _ in products:
        for triple in extract_structured(structured_row, source_id=f"product_{idx}"):
            adapter.accept_candidate(
                subject=triple["subject"], predicate=triple["predicate"],
                object_value=triple["object"], confidence=triple["confidence"],
                source_id=triple["source_id"], source_type=triple["source_type"],
                provenance=triple["provenance"],
            )

        result = extract_unstructured_llm(
            doc_text=unstructured_row["text"], source_id=f"product_{idx}",
            api_key=api_key, model=MODEL,
        )
        total_cost += result.get("cost_usd") or 0.0
        latencies.append(result["latency_s"])
        if result["error"]:
            n_errors += 1
        for triple in result["triples"]:
            adapter.accept_candidate(
                subject=triple["subject"], predicate=triple["predicate"],
                object_value=triple["object"], confidence=triple["confidence"],
                source_id=triple["source_id"], source_type=triple["source_type"],
                provenance=triple["provenance"],
            )

    adapter.end_iteration(1)

    total_runtime_s = time.perf_counter() - t0
    mem_after = mem_mb()

    accepted = adapter.get_accepted()
    n_conflicts = sum(1 for v in accepted.values() if v.get("competitor_count", 0) > 0)
    n_above_threshold = sum(1 for v in accepted.values() if v.get("confidence", 0) >= 0.88)

    row = {
        "n_products": n_products,
        "total_runtime_s": round(total_runtime_s, 3),
        "n_llm_calls": len(products),
        "mean_latency_s_per_doc": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "max_latency_s": round(max(latencies), 3) if latencies else None,
        "mem_before_mb": round(mem_before, 2),
        "mem_after_mb": round(mem_after, 2),
        "mem_delta_mb": round(mem_after - mem_before, 2),
        "kb_size": len(accepted),
        "n_conflicts": n_conflicts,
        "n_above_threshold": n_above_threshold,
        "n_errors": n_errors,
        "cost_usd": round(total_cost, 6),
    }
    print(f"  runtime={row['total_runtime_s']}s  mean_latency={row['mean_latency_s_per_doc']}s  "
          f"mem_delta={row['mem_delta_mb']}MB  kb_size={row['kb_size']}  "
          f"conflicts={row['n_conflicts']}  errors={row['n_errors']}  cost=${row['cost_usd']}", flush=True)
    return row


def main():
    api_key = load_api_key()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for n in SIZES:
        row = run_one_size(n, api_key)
        summary_rows.append(row)
        with open(OUTPUT_ROOT / "scalability_summary.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    total_cost = sum(r["cost_usd"] for r in summary_rows)
    total_calls = sum(r["n_llm_calls"] for r in summary_rows)
    print(f"\nTOTAL: {total_calls} calls, ${total_cost:.6f}")
    print(f"Saved to {OUTPUT_ROOT}/scalability_summary.csv")


if __name__ == "__main__":
    main()
