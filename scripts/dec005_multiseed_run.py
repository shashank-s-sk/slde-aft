"""DEC-005 multi-seed statistical validation. Reuses the exact same
src/experiment_runner.py as DEC-004 — same 5 configs, same N=20 scale,
just repeated across 5 generation seeds instead of 1. Writes results
incrementally (per config x seed) so partial progress survives an
interruption, then aggregates mean +/- std and paired significance
tests (paired t-test, Wilcoxon signed-rank) comparing each ablation
against the full-reference config.

Usage: python -u -m scripts.dec005_multiseed_run
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.experiment_runner import ExperimentConfig, run_experiment

N_PRODUCTS = 20
SEEDS = [42, 43, 44, 45, 46]
OUTPUT_ROOT = Path("outputs/dec005_multiseed")

CONFIGS = [
    dict(config_name="full", experiment_id="DEC005_FULL"),
    dict(config_name="without_feedback", experiment_id="DEC005_NO_FEEDBACK", use_feedback=False),
    dict(config_name="without_prob_kb", experiment_id="DEC005_NO_PROBKB", use_prob_kb=False),
    dict(config_name="structured_only", experiment_id="DEC005_STRUCTURED_ONLY", use_unstructured=False),
    dict(config_name="unstructured_only", experiment_id="DEC005_UNSTRUCTURED_ONLY", use_structured=False),
]


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


ERROR_RATE_SKIP_THRESHOLD = 0.20  # skip a (config, seed) if its saved call_log
                                   # already has an error rate below this


def _already_clean(run_dir: Path) -> bool:
    call_log_path = run_dir / "call_log.json"
    if not call_log_path.exists():
        return False
    calls = json.loads(call_log_path.read_text(encoding="utf-8"))
    if not calls:
        return True  # e.g. structured_only, which makes 0 calls
    error_rate = len([c for c in calls if c["error"]]) / len(calls)
    return error_rate < ERROR_RATE_SKIP_THRESHOLD


def _load_existing_summary() -> dict[tuple[str, int], dict]:
    summary_path = OUTPUT_ROOT / "all_runs_summary.csv"
    rows = {}
    if summary_path.exists():
        with open(summary_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[(row["config"], int(row["seed"]))] = row
    return rows


def _write_summary(rows_by_key: dict[tuple[str, int], dict]) -> None:
    ordered = [rows_by_key[k] for k in rows_by_key]
    with open(OUTPUT_ROOT / "all_runs_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ordered[0].keys()))
        writer.writeheader()
        writer.writerows(ordered)


def main():
    api_key = load_api_key()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    rows_by_key = _load_existing_summary()
    total_cost = 0.0
    total_calls = 0

    for overrides in CONFIGS:
        name = overrides["config_name"]
        for seed in SEEDS:
            run_dir = OUTPUT_ROOT / name / f"seed_{seed}"

            if _already_clean(run_dir):
                print(f"\n=== {name} / seed {seed}: SKIPPED (already clean) ===", flush=True)
                continue

            print(f"\n=== {name} / seed {seed} ===", flush=True)
            run_dir.mkdir(parents=True, exist_ok=True)

            config = ExperimentConfig(
                output_root=str(run_dir), n_products=N_PRODUCTS,
                generation_seed=seed, seed_label=f"seed{seed}",
                **overrides,
            )
            result = run_experiment(config, api_key=api_key)
            total_cost += result["total_cost_usd"]
            total_calls += result["total_calls"]

            if result["iteration_metrics"]:
                with open(run_dir / "iteration_metrics.csv", "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(result["iteration_metrics"][0].keys()))
                    writer.writeheader()
                    writer.writerows(result["iteration_metrics"])

            if result["held_out_metrics"]:
                with open(run_dir / "held_out_metrics.csv", "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=list(result["held_out_metrics"][0].keys()))
                    writer.writeheader()
                    writer.writerows(result["held_out_metrics"])

            with open(run_dir / "call_log.json", "w", encoding="utf-8") as f:
                json.dump(result["call_log"], f, indent=2)

            final_iter = result["iteration_metrics"][-1] if result["iteration_metrics"] else {}
            held_out_test = None
            if result["held_out_metrics"]:
                held_out_test = next(r for r in result["held_out_metrics"] if r["split"] == "test")

            row = {
                "config": name, "seed": seed,
                "final_iter_f1": final_iter.get("f1"),
                "held_out_test_f1": held_out_test["f1"] if held_out_test else None,
                "n_calls": result["total_calls"], "n_errors": len([c for c in result["call_log"] if c["error"]]),
                "cost_usd": result["total_cost_usd"],
            }
            rows_by_key[(name, seed)] = row
            print(f"  final_iter_f1={row['final_iter_f1']} held_out_test_f1={row['held_out_test_f1']} "
                  f"n_calls={row['n_calls']} n_errors={row['n_errors']}", flush=True)

            # Write running summary after every run so partial progress is never lost,
            # merged with any pre-existing (skipped, already-clean) rows.
            _write_summary(rows_by_key)

    print(f"\nTOTAL: {total_calls} calls, ${total_cost:.6f}", flush=True)
    print(f"Saved to {OUTPUT_ROOT}/all_runs_summary.csv", flush=True)


if __name__ == "__main__":
    main()
