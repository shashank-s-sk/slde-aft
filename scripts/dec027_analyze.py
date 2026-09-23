"""DEC-027 local analysis -- run this AFTER scripts/dec027_pod_run.py
has finished on the GPU pod and its outputs/ directories have been
copied/committed back. Zero cost, pure Python, no GPU needed.

Computes exactly the statistics pre-registered in Decision log.md
DEC-027: the primary paired bootstrap over the 40 test products (mean
per-product F1 difference, fine-tuned minus base, averaged across the
5 confirmatory seeds), the secondary one-sample t-test/Wilcoxon of the
5 seeds' whole-test-set F1 against the fresh base F1, and
training-seed vs. test-product variance reported separately.

Usage: python -m scripts.dec027_analyze
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats

from src.datasets.product_generator import generate_products
from src.evaluator import Triple, normalize_triple

SUMMARY_PATH = Path("outputs/dec027_leakage_free_finetuning/run_summary.json")
N_PRODUCTS = 200
GENERATION_SEED = 42
N_BOOTSTRAP = 10_000
BOOT_SEED = 20270927
MIN_EFFECT_OF_INTEREST = 0.03


def load_test_gold() -> dict[int, set]:
    """product_idx -> normalized gold_unstructured triple set, test-split products only."""
    import csv
    split = {}
    with open("data/product_split_200.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]

    gold = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        N_PRODUCTS, seed=GENERATION_SEED
    ):
        if split.get(idx) == "test":
            gold[idx] = {normalize_triple(Triple(s, p, o)) for s, p, o, _ in gold_unstructured}
    return gold


def per_product_f1(predictions_path: Path, gold: dict[int, set]) -> dict[int, float]:
    preds = json.loads(predictions_path.read_text(encoding="utf-8"))
    by_product = {}
    for row in preds:
        idx = row["product_idx"]
        if idx not in gold:
            continue
        pred_set = {
            normalize_triple(Triple(t["subject"], t["predicate"], t["object"]))
            for t in row["predicted_triples"]
        }
        gold_set = gold[idx]
        tp = len(pred_set & gold_set)
        fp = len(pred_set - gold_set)
        fn = len(gold_set - pred_set)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        by_product[idx] = f1
    return by_product


def main():
    if not SUMMARY_PATH.exists():
        print(f"ERROR: {SUMMARY_PATH} not found -- run scripts/dec027_pod_run.py on a GPU pod "
              "and copy its outputs/ back before running this analysis.")
        return

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    gold = load_test_gold()
    test_products = sorted(gold.keys())
    print(f"Test products: {len(test_products)}, total gold triples: {sum(len(g) for g in gold.values())}")

    base_pred_path = Path("outputs/dec006_eval/base_model/predictions.json")
    base_per_product = per_product_f1(base_pred_path, gold)
    base_whole_f1 = summary["base_test"]["f1"]
    print(f"Base model: whole-set F1={base_whole_f1:.4f}")

    seed_whole_f1 = []
    seed_per_product = []
    for seed_key, entry in summary["confirmatory"].items():
        adapter_dir = Path(entry["adapter_dir"])
        pred_path = Path("outputs/dec006_eval") / adapter_dir.name / "predictions.json"
        pp = per_product_f1(pred_path, gold)
        seed_per_product.append(pp)
        seed_whole_f1.append(entry["test_metrics"]["f1"])
        print(f"Seed {seed_key}: whole-set F1={entry['test_metrics']['f1']:.4f}")

    seed_whole_f1 = np.array(seed_whole_f1)

    # --- Secondary: one-sample t-test / Wilcoxon of whole-set F1 vs base ---
    diffs_whole = seed_whole_f1 - base_whole_f1
    t_stat, t_p = stats.ttest_1samp(seed_whole_f1, popmean=base_whole_f1)
    try:
        w_stat, w_p = stats.wilcoxon(diffs_whole)
    except ValueError as e:
        w_stat, w_p = None, None
        print(f"Wilcoxon not computable: {e}")

    training_seed_sd = float(seed_whole_f1.std(ddof=1))
    print(f"\nSecondary (descriptive): mean whole-set F1={seed_whole_f1.mean():.4f} "
          f"(sample SD={training_seed_sd:.4f}), diff vs base mean={diffs_whole.mean():.4f}, "
          f"one-sample t={t_stat:.3f} p={t_p:.4f}, Wilcoxon p={w_p}")

    # --- Primary: paired bootstrap over the 40 test products ---
    per_product_diff = []
    for idx in test_products:
        seed_f1s = [pp.get(idx, 0.0) for pp in seed_per_product]
        mean_finetuned = float(np.mean(seed_f1s))
        per_product_diff.append(mean_finetuned - base_per_product.get(idx, 0.0))
    per_product_diff = np.array(per_product_diff)
    test_product_sd = float(per_product_diff.std(ddof=1))

    rng = np.random.default_rng(BOOT_SEED)
    n = len(test_products)
    idx_resample = rng.integers(0, n, size=(N_BOOTSTRAP, n))
    boot_means = per_product_diff[idx_resample].mean(axis=1)
    ci_lo, ci_hi = float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))
    point_estimate = float(per_product_diff.mean())
    excludes_zero = bool(ci_lo > 0 or ci_hi < 0)
    is_positive = excludes_zero and point_estimate >= MIN_EFFECT_OF_INTEREST

    print(f"\nPrimary (pre-registered): paired bootstrap over {n} test products, "
          f"{N_BOOTSTRAP} resamples")
    print(f"  Mean per-product F1 diff (fine-tuned - base): {point_estimate:.4f}")
    print(f"  95% CI: [{ci_lo:.4f}, {ci_hi:.4f}]  (excludes zero: {excludes_zero})")
    print(f"  Test-product SD: {test_product_sd:.4f}  |  Training-seed SD (whole-set F1): {training_seed_sd:.4f}")
    print(f"  Minimum effect of interest: {MIN_EFFECT_OF_INTEREST}")
    print(f"\n  ==> RESULT: {'POSITIVE' if is_positive else 'NULL'} "
          f"(CI excludes 0: {excludes_zero}, point estimate >= {MIN_EFFECT_OF_INTEREST}: "
          f"{point_estimate >= MIN_EFFECT_OF_INTEREST})")
    if not is_positive:
        print("  This is a NULL result per the pre-registration. Report it as such -- "
              "per Decision log.md DEC-027, a null here supersedes EVID-040's exploratory "
              "positive result as the manuscript's headline fine-tuning claim.")

    out = {
        "n_test_products": n,
        "n_gold_triples_total": sum(len(g) for g in gold.values()),
        "base_whole_f1": base_whole_f1,
        "seed_whole_f1": seed_whole_f1.tolist(),
        "training_seed_sample_sd": training_seed_sd,
        "one_sample_ttest": {"t": float(t_stat), "p": float(t_p)},
        "wilcoxon": {"stat": w_stat, "p": w_p},
        "primary_bootstrap": {
            "point_estimate": point_estimate, "ci_lower": ci_lo, "ci_upper": ci_hi,
            "excludes_zero": excludes_zero, "test_product_sample_sd": test_product_sd,
            "min_effect_of_interest": MIN_EFFECT_OF_INTEREST, "is_positive": is_positive,
            "n_bootstrap": N_BOOTSTRAP,
        },
    }
    out_path = Path("outputs/dec027_leakage_free_finetuning/analysis_result.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved -> {out_path}")


if __name__ == "__main__":
    main()
