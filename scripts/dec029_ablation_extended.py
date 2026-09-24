"""DEC-029: higher-powered module ablation, extending DEC-023/EVID-039.

Identical to scripts/dec023_ablation_n50.py in every respect (same N=50
product superset and data/product_split.csv split, same per-call
caching and resume logic, same held-out test metric) except:
  - SEEDS: 25 new seeds (47-71), giving 30 total with DEC-023's 42-46.
  - CONFIGS: only the 3 pre-registered configs (full, without_feedback,
    without_prob_kb); structured_only/unstructured_only are out of scope.
  - OUTPUT_ROOT: outputs/dec029_ablation_extended/, so EVID-039's saved
    5-seed results are never overwritten (README ground rule 2).
The combined 30-seed analysis is a separate step
(scripts/dec029_analyze.py), which reads DEC-023's files without
modifying them.

Usage: python -u -m scripts.dec029_ablation_extended
   or, to run shards in parallel (each (config, seed) run is independent
   and has its own cache, so sharding changes wall-clock time only):
       python -u -m scripts.dec029_ablation_extended --config full --seeds 47-59
   Each shard writes all_runs_summary__<config>_<start>-<end>.csv;
   scripts/dec029_analyze.py reads every all_runs_summary*.csv here.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from src.experiment_runner import ExperimentConfig, run_experiment

N_PRODUCTS = 50
SEEDS = list(range(47, 72))
OUTPUT_ROOT = Path("outputs/dec029_ablation_extended")

CONFIGS = [
    dict(config_name="full", experiment_id="DEC029_FULL"),
    dict(config_name="without_feedback", experiment_id="DEC029_NO_FEEDBACK", use_feedback=False),
    dict(config_name="without_prob_kb", experiment_id="DEC029_NO_PROBKB", use_prob_kb=False),
]


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


ERROR_RATE_SKIP_THRESHOLD = 0.20


def _already_clean(run_dir: Path) -> bool:
    call_log_path = run_dir / "call_log.json"
    if not call_log_path.exists():
        return False
    calls = json.loads(call_log_path.read_text(encoding="utf-8"))
    if not calls:
        return True
    error_rate = len([c for c in calls if c["error"]]) / len(calls)
    return error_rate < ERROR_RATE_SKIP_THRESHOLD


SUMMARY_NAME = "all_runs_summary.csv"


def _load_existing_summary() -> dict[tuple[str, int], dict]:
    summary_path = OUTPUT_ROOT / SUMMARY_NAME
    rows = {}
    if summary_path.exists():
        with open(summary_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[(row["config"], int(row["seed"]))] = row
    return rows


def _write_summary(rows_by_key: dict[tuple[str, int], dict]) -> None:
    ordered = [rows_by_key[k] for k in rows_by_key]
    with open(OUTPUT_ROOT / SUMMARY_NAME, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ordered[0].keys()))
        writer.writeheader()
        writer.writerows(ordered)


def main():
    global SUMMARY_NAME
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", choices=[c["config_name"] for c in CONFIGS])
    parser.add_argument("--seeds", help="inclusive range, e.g. 47-59")
    args = parser.parse_args()
    configs = [c for c in CONFIGS if args.config in (None, c["config_name"])]
    seeds = SEEDS
    if args.seeds:
        lo, hi = (int(x) for x in args.seeds.split("-"))
        seeds = [s for s in SEEDS if lo <= s <= hi]
    if args.config or args.seeds:
        SUMMARY_NAME = f"all_runs_summary__{args.config or 'all'}_{args.seeds or 'all'}.csv"

    api_key = load_api_key()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    rows_by_key = _load_existing_summary()
    total_cost = 0.0
    total_calls = 0

    for overrides in configs:
        name = overrides["config_name"]
        for seed in seeds:
            run_dir = OUTPUT_ROOT / name / f"seed_{seed}"

            if _already_clean(run_dir):
                print(f"\n=== {name} / seed {seed}: SKIPPED (already clean) ===", flush=True)
                continue

            print(f"\n=== {name} / seed {seed} ===", flush=True)
            run_dir.mkdir(parents=True, exist_ok=True)

            config = ExperimentConfig(
                output_root=str(run_dir), n_products=N_PRODUCTS,
                generation_seed=seed, seed_label=f"seed{seed}",
                cache_path=str(run_dir / "call_cache.jsonl"),
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

            _write_summary(rows_by_key)

    print(f"\nTOTAL: {total_calls} calls, ${total_cost:.6f}", flush=True)
    print(f"Saved to {OUTPUT_ROOT}/{SUMMARY_NAME}", flush=True)


if __name__ == "__main__":
    main()
