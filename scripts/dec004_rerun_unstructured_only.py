"""Re-run of the DEC-004 unstructured_only ablation config only, after
fixing the call_log persistence gap found in EVID-016. Investigates the
iteration-4 F1=0.0 anomaly from the first pilot run.

Usage: python -m scripts.dec004_rerun_unstructured_only
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


def main():
    api_key = load_api_key()
    name = "unstructured_only"
    config_dir = OUTPUT_ROOT / name
    config_dir.mkdir(parents=True, exist_ok=True)

    config = ExperimentConfig(
        config_name=name, experiment_id="DEC004_UNSTRUCTURED_ONLY_RERUN",
        output_root=str(config_dir), n_products=N_PRODUCTS,
        use_structured=False, use_unstructured=True,
    )
    result = run_experiment(config, api_key=api_key)

    with open(config_dir / "iteration_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(result["iteration_metrics"][0].keys()))
        writer.writeheader()
        writer.writerows(result["iteration_metrics"])

    with open(config_dir / "call_log.json", "w", encoding="utf-8") as f:
        json.dump(result["call_log"], f, indent=2)

    with open(config_dir / "run_config.json", "w", encoding="utf-8") as f:
        json.dump({
            "config_name": name, "use_structured": False, "use_unstructured": True,
            "n_products": N_PRODUCTS,
            "n_train": result["n_train"], "n_val": result["n_val"], "n_test": result["n_test"],
            "total_calls": result["total_calls"], "total_cost_usd": result["total_cost_usd"],
        }, f, indent=2)

    print("Iteration metrics:")
    for row in result["iteration_metrics"]:
        print(f"  iter {row['iteration']}: P={row['precision']:.4f} R={row['recall']:.4f} "
              f"F1={row['f1']:.4f} KB={row['kb_size']}")

    errors = [c for c in result["call_log"] if c["error"]]
    print(f"\nTotal calls: {result['total_calls']}, cost: ${result['total_cost_usd']:.6f}")
    print(f"Calls with error: {len(errors)}")
    for it in sorted(set(c["iteration"] for c in result["call_log"])):
        iter_calls = [c for c in result["call_log"] if c["iteration"] == it]
        iter_errors = [c for c in iter_calls if c["error"]]
        iter_zero = [c for c in iter_calls if c["n_triples"] == 0]
        print(f"  iteration {it}: {len(iter_calls)} calls, {len(iter_errors)} errors, "
              f"{len(iter_zero)} zero-triple")


if __name__ == "__main__":
    main()
