"""DEC-027 pod orchestration -- run this ON a rented RunPod GPU pod
(RTX 4090, 3090 fallback), NOT locally. See scripts/dec027_pod_runbook.sh
for the full pod setup sequence this script assumes has already run
(git clone, pip install, PYTHONPATH).

Implements the DEC-027 pre-registration (Decision log.md) end to end in
one pod session:
  0. Strict leakage guard (src/dec027_leakage_guard.py) -- aborts before
     any GPU time is spent if it fails.
  1. Epoch grid {2,3,5,8}, seed 42, evaluated on the 20-product
     VALIDATION split only.
  2. LoRA grid (rank in {8,32}, lr in {1e-4,3e-4}) at the winning epoch
     count, seed 42, evaluated on VALIDATION only; the epoch grid's own
     rank=16/alpha=32/lr=2e-4 run at the winning epoch is reused as the
     grid's fifth (default) point, not retrained.
  3. Confirmatory run: the single winning configuration, trained at
     seeds 43-46 (seed 42 reused from the grid), evaluated ONCE per
     seed on the untouched 40-product TEST split.
  4. Fresh base-model evaluation on the same 40-product test split.

Every step's raw metrics.json is left exactly where
scripts/dec006_evaluate_adapter.py already saves it
(outputs/dec006_eval/<name>[_val]/metrics.json); this script additionally
writes a single consolidated outputs/dec027_leakage_free_finetuning/
run_summary.json indexing all of them, so the after-the-fact bootstrap
analysis (scripts/dec027_analyze.py, run locally, zero cost) doesn't
need to re-discover file paths.

Usage: python scripts/dec027_pod_run.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

DATA_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl"
OUT_ROOT = Path("outputs/dec027_leakage_free_finetuning")
EPOCHS_GRID = [2, 3, 5, 8]
LORA_GRID = [
    ("rank8", ["--lora-rank", "8", "--lora-alpha", "16"]),
    ("rank32", ["--lora-rank", "32", "--lora-alpha", "64"]),
    ("lr1e-4", ["--learning-rate", "1e-4"]),
    ("lr3e-4", ["--learning-rate", "3e-4"]),
]
CONFIRM_SEEDS = [43, 44, 45, 46]  # seed 42 reused from the epoch/LoRA grid


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def eval_metrics_path(adapter_dir: Path | None, eval_split: str) -> Path:
    name = adapter_dir.name if adapter_dir else "base_model"
    if eval_split != "test":
        name = f"{name}_{eval_split}"
    return Path("outputs/dec006_eval") / name / "metrics.json"


def train_and_eval(adapter_dir: Path, seed: int, epochs: int, eval_split: str, extra_train_args: list[str] | None = None) -> dict:
    if not (adapter_dir / "adapter_model.safetensors").exists():
        run(["python", "scripts/dec006_lora_finetune.py", "--seed", str(seed), "--epochs", str(epochs),
             "--data-path", DATA_PATH, "--output-dir", str(adapter_dir)] + (extra_train_args or []))
    else:
        print(f"Adapter already exists at {adapter_dir}, skipping training (resume-safe).")

    run(["python", "scripts/dec006_evaluate_adapter.py", "--adapter", str(adapter_dir),
         "--n-products", "200", "--eval-split", eval_split,
         "--training-data-path", DATA_PATH, "--strict-leakage-guard"])

    return json.loads(eval_metrics_path(adapter_dir, eval_split).read_text(encoding="utf-8"))


def main():
    from src.dec027_leakage_guard import assert_no_leakage
    assert_no_leakage(DATA_PATH, n_products=200)
    print("DEC-027 strict leakage guard PASSED at pod-run start -- proceeding.\n")

    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary = {"epoch_grid": {}, "lora_grid": {}, "confirmatory": {}, "base_test": None,
               "data_path": DATA_PATH}

    print("=== Step 1: epoch grid (seed 42, validation split) ===")
    for epochs in EPOCHS_GRID:
        adapter_dir = OUT_ROOT / f"epoch_grid/epochs{epochs}_seed42"
        m = train_and_eval(adapter_dir, seed=42, epochs=epochs, eval_split="val")
        summary["epoch_grid"][str(epochs)] = {"adapter_dir": str(adapter_dir), "val_metrics": m}
        print(f"epochs={epochs}: val F1={m['f1']:.4f} (P={m['precision']:.4f} R={m['recall']:.4f})")

    best_epochs = max(summary["epoch_grid"], key=lambda k: summary["epoch_grid"][k]["val_metrics"]["f1"])
    best_epochs = int(best_epochs)
    print(f"\nWinning epoch count (by validation F1): {best_epochs}\n")
    summary["winning_epochs"] = best_epochs

    print("=== Step 2: LoRA grid at winning epoch count (seed 42, validation split) ===")
    default_dir = OUT_ROOT / f"epoch_grid/epochs{best_epochs}_seed42"
    summary["lora_grid"]["default_rank16_alpha32_lr2e-4"] = {
        "adapter_dir": str(default_dir),
        "val_metrics": summary["epoch_grid"][str(best_epochs)]["val_metrics"],
    }
    print(f"default_rank16_alpha32_lr2e-4 (reused from epoch grid): "
          f"val F1={summary['lora_grid']['default_rank16_alpha32_lr2e-4']['val_metrics']['f1']:.4f}")

    for name, extra_args in LORA_GRID:
        adapter_dir = OUT_ROOT / f"lora_grid/{name}_epochs{best_epochs}_seed42"
        m = train_and_eval(adapter_dir, seed=42, epochs=best_epochs, eval_split="val", extra_train_args=extra_args)
        summary["lora_grid"][name] = {"adapter_dir": str(adapter_dir), "val_metrics": m}
        print(f"{name}: val F1={m['f1']:.4f} (P={m['precision']:.4f} R={m['recall']:.4f})")

    def lora_key_rank(name: str) -> int:
        # tie-break toward the simpler (lower rank) / default config, per
        # the pre-registered selection rule (ties within 0.01 -> simpler).
        return {"default_rank16_alpha32_lr2e-4": 16, "rank8": 8, "rank32": 32,
                "lr1e-4": 16, "lr3e-4": 16}[name]

    best_f1 = max(v["val_metrics"]["f1"] for v in summary["lora_grid"].values())
    tied = [k for k, v in summary["lora_grid"].items() if abs(v["val_metrics"]["f1"] - best_f1) <= 0.01]
    best_lora = min(tied, key=lora_key_rank)
    print(f"\nWinning LoRA config (by validation F1, ties -> simpler config): {best_lora}\n")
    summary["winning_lora_config"] = best_lora
    summary["winning_adapter_dir_seed42"] = summary["lora_grid"][best_lora]["adapter_dir"]

    lora_extra_by_name = {name: args for name, args in LORA_GRID}
    winning_extra_args = lora_extra_by_name.get(best_lora, [])

    print("=== Step 3: confirmatory run (winning config, seeds 42 + 43-46, test split) ===")
    winning_adapter_seed42 = Path(summary["winning_adapter_dir_seed42"])
    m42_test = train_and_eval(winning_adapter_seed42, seed=42, epochs=best_epochs, eval_split="test",
                               extra_train_args=winning_extra_args)
    summary["confirmatory"]["42"] = {"adapter_dir": str(winning_adapter_seed42), "test_metrics": m42_test}
    print(f"seed=42 (reused): test F1={m42_test['f1']:.4f}")

    for seed in CONFIRM_SEEDS:
        adapter_dir = OUT_ROOT / f"confirmatory/{best_lora}_epochs{best_epochs}_seed{seed}"
        m = train_and_eval(adapter_dir, seed=seed, epochs=best_epochs, eval_split="test",
                            extra_train_args=winning_extra_args)
        summary["confirmatory"][str(seed)] = {"adapter_dir": str(adapter_dir), "test_metrics": m}
        print(f"seed={seed}: test F1={m['f1']:.4f}")

    print("\n=== Step 4: fresh base-model evaluation (test split) ===")
    run(["python", "scripts/dec006_evaluate_adapter.py", "--n-products", "200", "--eval-split", "test",
         "--training-data-path", DATA_PATH, "--strict-leakage-guard"])
    base_metrics = json.loads(eval_metrics_path(None, "test").read_text(encoding="utf-8"))
    summary["base_test"] = base_metrics
    print(f"base model: test F1={base_metrics['f1']:.4f}")

    with open(OUT_ROOT / "run_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSaved -> {OUT_ROOT}/run_summary.json")
    print("\n=== DONE. Copy/commit outputs/dec027_leakage_free_finetuning/ and "
          "outputs/dec006_eval/ back, then STOP THE POD. ===")


if __name__ == "__main__":
    main()
