"""DEC-004 ablation pilot: single-seed, N=20 products (13 train / 3 val /
4 test from the existing data/product_split.csv), 5 configs.

Full (reference) and 4 single-module-removed ablations:
  - without_feedback: locked-context guidance stays, feedback hint removed
  - without_prob_kb: Conservative Noisy-Or + conflict adjustment replaced
    by deterministic monotonic max-merge
  - structured_only: no LLM calls, structured extraction only
  - unstructured_only: no structured seeding, LLM extraction only

Deferred (not run here — see Decision log.md DEC-004 status): without
Synthetic-Data-Generator and without-LoRA (nothing to ablate against
until DEC-006 exists), without-Provenance (no active provenance filter
exists yet in the pipeline to turn off).

Usage: python -m scripts.dec004_ablation_pilot
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.experiment_runner import ExperimentConfig, run_experiment

N_PRODUCTS = 20
OUTPUT_ROOT = Path("outputs/dec004_ablation_pilot")


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


CONFIGS = [
    dict(config_name="full", experiment_id="DEC004_FULL"),
    dict(config_name="without_feedback", experiment_id="DEC004_NO_FEEDBACK", use_feedback=False),
    dict(config_name="without_prob_kb", experiment_id="DEC004_NO_PROBKB", use_prob_kb=False),
    dict(config_name="structured_only", experiment_id="DEC004_STRUCTURED_ONLY", use_unstructured=False),
    dict(config_name="unstructured_only", experiment_id="DEC004_UNSTRUCTURED_ONLY", use_structured=False),
]


def main():
    api_key = load_api_key()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    total_cost = 0.0
    total_calls = 0

    for overrides in CONFIGS:
        name = overrides["config_name"]
        print(f"\n{'='*60}\n=== Config: {name} ===\n{'='*60}")

        config = ExperimentConfig(
            output_root=str(OUTPUT_ROOT / name),
            n_products=N_PRODUCTS,
            **overrides,
        )
        result = run_experiment(config, api_key=api_key)
        total_cost += result["total_cost_usd"]
        total_calls += result["total_calls"]

        config_dir = OUTPUT_ROOT / name
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(config_dir / "iteration_metrics.csv", "w", newline="", encoding="utf-8") as f:
            if result["iteration_metrics"]:
                writer = csv.DictWriter(f, fieldnames=list(result["iteration_metrics"][0].keys()))
                writer.writeheader()
                writer.writerows(result["iteration_metrics"])

        if result["held_out_metrics"]:
            with open(config_dir / "held_out_metrics.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(result["held_out_metrics"][0].keys()))
                writer.writeheader()
                writer.writerows(result["held_out_metrics"])

        with open(config_dir / "call_log.json", "w", encoding="utf-8") as f:
            json.dump(result["call_log"], f, indent=2)

        with open(config_dir / "run_config.json", "w", encoding="utf-8") as f:
            json.dump({
                **overrides, "n_products": N_PRODUCTS,
                "n_train": result["n_train"], "n_val": result["n_val"], "n_test": result["n_test"],
                "total_calls": result["total_calls"], "total_cost_usd": result["total_cost_usd"],
            }, f, indent=2)

        final_iter = result["iteration_metrics"][-1] if result["iteration_metrics"] else {}
        held_out_test = None
        if result["held_out_metrics"]:
            held_out_test = next(r for r in result["held_out_metrics"] if r["split"] == "test")

        summary_rows.append({
            "config": name,
            "final_iter_precision": final_iter.get("precision"),
            "final_iter_recall": final_iter.get("recall"),
            "final_iter_f1": final_iter.get("f1"),
            "final_kb_size": final_iter.get("kb_size"),
            "held_out_test_precision": held_out_test["precision"] if held_out_test else None,
            "held_out_test_recall": held_out_test["recall"] if held_out_test else None,
            "held_out_test_f1": held_out_test["f1"] if held_out_test else None,
            "n_calls": result["total_calls"],
            "cost_usd": result["total_cost_usd"],
        })

        print(f"  n_calls={result['total_calls']} cost=${result['total_cost_usd']:.6f} "
              f"final_iter_f1={final_iter.get('f1')} held_out_test_f1="
              f"{held_out_test['f1'] if held_out_test else 'N/A'}")

    with open(OUTPUT_ROOT / "ablation_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_calls} calls, ${total_cost:.6f}")
    print(f"Saved to {OUTPUT_ROOT}/ablation_summary.csv")


if __name__ == "__main__":
    main()
