"""DEC-028 -- provenance filter under a noisy structured source.

Corrupts a controlled fraction of the 200-product run's STRUCTURED
observation rows (iteration 1 only -- structured facts seed the KB at
iteration 1 only, per this project's design) with a different,
plausible value from that predicate's own fixed value pool
(src/datasets/product_generator.py), then replays the (partially
corrupted) full observation set through the real, unmodified PKB
acceptance/aggregation code (src/pkb_replay.py -> CandidateBufferAdapter)
to reconstruct what the accepted-candidate state would have been under
a noisy structured source. Gold labels are never touched and never
re-derived from the corrupted data.

Two scoring arms are read from the SAME replayed `accepted` dict (no
second replay needed): the conflict-adjusted arm uses each entry's
`confidence` field (C(t) = A(t)/(m(t)+1) for functional predicates,
already computed by refresh_slot_scores); the support-only arm uses
each entry's `support` field (A(t), no conflict-adjustment divisor,
computed identically for every predicate) -- both fields already exist
in the accepted dict, unmodified, per pkb_instrumentation.py.

Usage: python -m scripts.dec028_provenance_corruption
"""

from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from src.pkb_replay import replay_iterations
from src.probkb_v2_adapter import CandidateBufferAdapter
from src.provenance_filter import has_structured_corroboration

OBS_DIR = Path("outputs/dec006_scaleup_probkb/train_kb")
OUT_DIR = Path("outputs/dec028_provenance_corruption")
FUNC_PRED_PATH = "configs/functional_predicates_product_domain.json"
THRESHOLD = 0.88
SHRINKAGE = 0.75
RATES = [0.0, 0.05, 0.10, 0.20]
N_SEEDS = 5
N_BOOTSTRAP = 10_000
BOOT_SEED = 20260923

GOLD_MODULE = "scripts.dec006_scaleup_probkb_run"

# Predicate -> fixed value pool, transcribed directly from
# src/datasets/product_generator.py (brands/categories/colors/materials/
# regions/numeric pools) via structured.py's column->predicate mapping.
VALUE_POOLS: dict[str, list] = {
    "manufactured_by": ["Auralex", "PixelWare", "NeoTech", "VoltEdge", "Zenbyte", "TechNova"],
    "belongs_to_category": ["smartphone", "laptop", "headphones", "tablet", "smartwatch"],
    "has_price_usd": [199, 249, 299, 349, 499, 699, 899, 1099, 1299],
    "has_screen_size_inch": [6.1, 6.7, 10.9, 11.0, 13.3, 14.0, 15.6],
    "has_ram_gb": [4, 6, 8, 12, 16, 32],
    "has_storage_gb": [64, 128, 256, 512, 1024],
    "has_battery_life_hours": [8, 10, 12, 14, 18, 20, 24],
    "has_weight_kg": [0.18, 0.23, 0.42, 0.55, 1.2, 1.45, 1.8],
    "has_color": ["black", "silver", "blue", "white", "green"],
    "made_of_material": ["aluminum", "plastic", "carbon fiber"],
    "target_market_region": ["EU", "US", "APAC", "Global"],
    "supports_fast_charging": ["yes", "no"],
    "has_noise_cancellation": ["yes", "no"],
}


def load_gold_by_product(gold_module_name: str) -> dict[str, set[tuple[str, str, str]]]:
    mod = importlib.import_module(gold_module_name)
    split = mod.load_split()
    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in mod.generate_products(
        mod.N_PRODUCTS, seed=mod.GENERATION_SEED
    ):
        products[idx] = (structured_row, unstructured_row, gold_structured, gold_unstructured)
    train_idx = sorted(i for i, s in split.items() if s == "train")
    gold_by_product = {}
    for idx in train_idx:
        pname = products[idx][0]["product_name"]
        gold_by_product[pname] = mod.normalize_gold(products[idx][3])
    return gold_by_product


def keys_to_strs(keys: set[tuple[str, str, str]]) -> set[str]:
    return {"|".join(k) for k in keys}


def corrupt_iteration1(rate: float, seed: int) -> pd.DataFrame:
    """Return a corrupted copy of observations_iteration_1.csv: for each
    structured row, with probability `rate`, replace `object` with a
    different value drawn uniformly from that predicate's own value pool."""
    df = pd.read_csv(OBS_DIR / "observations_iteration_1.csv")
    rng = random.Random(seed)
    is_structured = df["source_type"] == "structured"
    new_objects = df["object"].astype(str).tolist()

    for i in df.index[is_structured]:
        if rng.random() >= rate:
            continue
        pred = df.at[i, "predicate"]
        pool = VALUE_POOLS.get(pred)
        if not pool:
            continue
        true_val = str(df.at[i, "object"])
        candidates = [v for v in pool if str(v) != true_val]
        if not candidates:
            continue
        new_objects[i] = str(rng.choice(candidates))

    df["object"] = new_objects
    # triple_key must reflect the (possibly corrupted) object for replay
    # to treat it as a distinct candidate -- recomputed the same way
    # accept_candidate() does internally, but triple_key in this CSV is
    # informational only (not consumed by replay_iterations); left as-is
    # except for the object column, which is what replay actually reads.
    return df


def build_corrupted_dir(rate: float, seed: int) -> Path:
    tag = f"rate{int(rate*100)}_seed{seed}"
    d = OUT_DIR / "corrupted_obs" / tag
    d.mkdir(parents=True, exist_ok=True)
    corrupted_iter1 = corrupt_iteration1(rate, seed)
    corrupted_iter1.to_csv(d / "observations_iteration_1.csv", index=False)
    for it in (2, 3, 4):
        src = OBS_DIR / f"observations_iteration_{it}.csv"
        dst = d / f"observations_iteration_{it}.csv"
        if not dst.exists():
            pd.read_csv(src).to_csv(dst, index=False)
    return d


def replay_to_accepted(obs_dir: Path, gold_keys: set[tuple[str, str, str]]) -> dict:
    adapter = CandidateBufferAdapter(
        experiment_id="DEC028_CORRUPTION",
        run_id=f"replay_{obs_dir.name}",
        prob_kb_version="conservative_noisy_or_conflict_adjusted",
        functional_predicates_path=FUNC_PRED_PATH,
        output_dir=str(OUT_DIR / "replay_artifacts" / obs_dir.name),
        threshold=THRESHOLD,
        shrinkage=SHRINKAGE,
        gold_keys=gold_keys,
    )
    replay_iterations(adapter, str(obs_dir), [1, 2, 3, 4])
    return adapter.accepted


def slot_key(subject: str, predicate: str) -> tuple[str, str]:
    return (str(subject).strip().lower(), str(predicate).strip().lower())


def analyze_arm(
    accepted: dict, score_field: str, gold_key_strs: set[str], baseline_slot_object_counts: dict | None
) -> dict:
    rows = []
    for key, entry in accepted.items():
        subj_norm, pred_norm, obj_norm = key
        rows.append({
            "subject_norm": subj_norm,
            "predicate_norm": pred_norm,
            "object_norm": obj_norm,
            "triple_key": "|".join(key),
            "score": entry[score_field],
            "functional_predicate": entry.get("functional_predicate", False),
            "source_types": entry.get("source_types", []),
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return {"admitted": 0, "contested_created": 0, "contested_with_admission": 0,
                "passing_precision": None, "removed_precision": None,
                "n_true_correct_removed": 0, "n_incorrect_passed": 0,
                "n_pass": 0, "n_removed": 0, "admitted_keys": set(),
                "slot_object_counts": {}, "pass_gold_flags": [], "removed_gold_flags": [],
                "pass_subjects": [], "removed_subjects": []}

    admitted = df[df["score"] >= THRESHOLD]
    admitted_keys = set(admitted["triple_key"])

    # slot -> set of distinct objects among ALL accepted candidates (structural, score-independent)
    slot_object_counts = df.groupby(["subject_norm", "predicate_norm"])["object_norm"].nunique().to_dict()

    contested_created = 0
    contested_with_admission = 0
    if baseline_slot_object_counts is not None:
        func_slots = df[df["functional_predicate"]].groupby(["subject_norm", "predicate_norm"])
        for slot, group in func_slots:
            n_now = group["object_norm"].nunique()
            n_before = baseline_slot_object_counts.get(slot, 0)
            if n_now >= 2 and n_before < 2:
                contested_created += 1
                if (group["score"] >= THRESHOLD).any():
                    contested_with_admission += 1

    admitted = admitted.copy()
    admitted["is_gold"] = admitted["triple_key"].isin(gold_key_strs)
    admitted["passes_filter"] = admitted["source_types"].apply(has_structured_corroboration)

    passing = admitted[admitted["passes_filter"]]
    removed = admitted[~admitted["passes_filter"]]

    passing_precision = float(passing["is_gold"].mean()) if len(passing) else None
    removed_precision = float(removed["is_gold"].mean()) if len(removed) else None
    n_true_correct_removed = int((removed["is_gold"]).sum())
    n_incorrect_passed = int((~passing["is_gold"]).sum())

    return {
        "admitted": int(len(admitted)),
        "contested_created": contested_created,
        "contested_with_admission": contested_with_admission,
        "passing_precision": passing_precision,
        "removed_precision": removed_precision,
        "n_true_correct_removed": n_true_correct_removed,
        "n_incorrect_passed": n_incorrect_passed,
        "n_pass": int(len(passing)),
        "n_removed": int(len(removed)),
        "admitted_keys": admitted_keys,
        "slot_object_counts": slot_object_counts,
        "pass_gold_flags": passing["is_gold"].tolist(),
        "removed_gold_flags": removed["is_gold"].tolist(),
        "pass_subjects": passing["subject_norm"].tolist(),
        "removed_subjects": removed["subject_norm"].tolist(),
    }


def product_clustered_bootstrap(
    pass_subjects: list, pass_gold: list, removed_subjects: list, removed_gold: list,
    seed: int, n_boot: int,
) -> dict:
    """Cluster bootstrap over unique subject strings, matching DEC-026's
    ACTUAL convention exactly (scripts/dec026_aggregation_rules_replay.py's
    per_subject_counts/bootstrap_prf_diff): resampling is over every unique
    subject present in the pooled admitted data, including hallucinated/
    fragment "subjects" (e.g. "laptop device") that are not among the 140
    real train products -- these are not dropped, they contribute 0 TP but
    a real (nonzero) N, exactly as DEC-026 treats them. Restricting the
    resample population to only the 140 real products (an earlier version
    of this script did this) silently discarded most of the removed-set
    triples, which are disproportionately fragment-subject hallucinations
    per EVID-029, and produced a materially wrong estimate -- fixed here to
    match DEC-026's real behavior, not the pre-registration's shorthand
    description of it."""
    all_subjects = sorted(set(pass_subjects) | set(removed_subjects))
    n_products = len(all_subjects)
    idx_map = {p: i for i, p in enumerate(all_subjects)}

    tp_pass = np.zeros(n_products)
    n_pass = np.zeros(n_products)
    for subj, gold in zip(pass_subjects, pass_gold):
        i = idx_map.get(subj)
        if i is None:
            continue
        n_pass[i] += 1
        tp_pass[i] += float(gold)

    tp_rem = np.zeros(n_products)
    n_rem = np.zeros(n_products)
    for subj, gold in zip(removed_subjects, removed_gold):
        i = idx_map.get(subj)
        if i is None:
            continue
        n_rem[i] += 1
        tp_rem[i] += float(gold)

    rng = np.random.default_rng(seed)
    resample_idx = rng.integers(0, n_products, size=(n_boot, n_products))

    tp_pass_s = tp_pass[resample_idx].sum(axis=1)
    n_pass_s = n_pass[resample_idx].sum(axis=1)
    tp_rem_s = tp_rem[resample_idx].sum(axis=1)
    n_rem_s = n_rem[resample_idx].sum(axis=1)

    prec_pass = np.where(n_pass_s > 0, tp_pass_s / np.maximum(n_pass_s, 1), np.nan)
    prec_rem = np.where(n_rem_s > 0, tp_rem_s / np.maximum(n_rem_s, 1), np.nan)
    diffs = prec_pass - prec_rem
    diffs = diffs[~np.isnan(diffs)]

    if len(diffs) == 0:
        return {"mean_diff": None, "ci_lower": None, "ci_upper": None, "excludes_zero": None, "n_valid_resamples": 0}

    lo, hi = float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
    return {"mean_diff": float(diffs.mean()), "ci_lower": lo, "ci_upper": hi,
            "excludes_zero": bool(lo > 0 or hi < 0), "n_valid_resamples": int(len(diffs))}


def mean_sample_sd(values: list) -> dict:
    arr = np.array([v for v in values if v is not None], dtype=float)
    if len(arr) == 0:
        return {"mean": None, "sample_sd": None, "n": 0}
    return {"mean": float(arr.mean()), "sample_sd": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0, "n": int(len(arr))}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gold_by_product = load_gold_by_product(GOLD_MODULE)
    full_gold = set()
    for g in gold_by_product.values():
        full_gold |= g
    gold_key_strs = keys_to_strs(full_gold)

    # --- r=0 baseline (both arms), and the mandatory sanity check ---
    print("=== r=0% baseline (sanity check against EVID-029) ===")
    baseline_dir = build_corrupted_dir(0.0, seed=0)
    baseline_accepted = replay_to_accepted(baseline_dir, full_gold)

    baseline_conflict = analyze_arm(baseline_accepted, "confidence", gold_key_strs, baseline_slot_object_counts=None)
    baseline_support = analyze_arm(baseline_accepted, "support", gold_key_strs, baseline_slot_object_counts=None)

    print(f"conflict-adjusted arm @ r=0: admitted={baseline_conflict['admitted']} "
          f"pass={baseline_conflict['n_pass']} removed={baseline_conflict['n_removed']}")

    expected = (475, 444, 31)
    actual = (baseline_conflict["admitted"], baseline_conflict["n_pass"], baseline_conflict["n_removed"])
    if actual != expected:
        print(f"\n!!! SANITY CHECK FAILED !!!\nExpected (admitted, pass, removed) = {expected}\n"
              f"Got {actual}\nSTOPPING -- do not trust any corrupted-rate result until this is fixed.")
        with open(OUT_DIR / "SANITY_CHECK_FAILED.json", "w", encoding="utf-8") as f:
            json.dump({"expected": expected, "actual": actual}, f, indent=2)
        return
    print(f"Sanity check PASSED: {actual} matches EVID-029 exactly.\n")

    baseline_slots_conflict = baseline_conflict["slot_object_counts"]
    baseline_slots_support = baseline_support["slot_object_counts"]

    def strip(d):
        return {k: v for k, v in d.items()
                if k not in ("admitted_keys", "slot_object_counts", "pass_gold_flags",
                             "removed_gold_flags", "pass_subjects", "removed_subjects")}

    per_seed_results = {"conflict_adjusted": {}, "support_only": {}}
    rate_aggregates = {"conflict_adjusted": {}, "support_only": {}}

    for rate in RATES:
        seeds = [0] if rate == 0.0 else list(range(1, N_SEEDS + 1))
        rate_key = f"{int(rate*100)}%"
        per_seed_results["conflict_adjusted"][rate_key] = []
        per_seed_results["support_only"][rate_key] = []

        pooled = {
            "conflict_adjusted": {"pass_subj": [], "pass_gold": [], "rem_subj": [], "rem_gold": []},
            "support_only": {"pass_subj": [], "pass_gold": [], "rem_subj": [], "rem_gold": []},
        }

        for seed in seeds:
            if rate == 0.0 and seed == 0:
                accepted = baseline_accepted
            else:
                d = build_corrupted_dir(rate, seed)
                accepted = replay_to_accepted(d, full_gold)

            conflict = analyze_arm(accepted, "confidence", gold_key_strs, baseline_slots_conflict)
            support = analyze_arm(accepted, "support", gold_key_strs, baseline_slots_support)

            per_seed_results["conflict_adjusted"][rate_key].append({"seed": seed, **strip(conflict)})
            per_seed_results["support_only"][rate_key].append({"seed": seed, **strip(support)})

            for arm_name, arm in (("conflict_adjusted", conflict), ("support_only", support)):
                pooled[arm_name]["pass_subj"].extend(arm["pass_subjects"])
                pooled[arm_name]["pass_gold"].extend(arm["pass_gold_flags"])
                pooled[arm_name]["rem_subj"].extend(arm["removed_subjects"])
                pooled[arm_name]["rem_gold"].extend(arm["removed_gold_flags"])

            print(f"rate={rate_key} seed={seed} | conflict-adj: admitted={conflict['admitted']} "
                  f"contested_created={conflict['contested_created']} contested_admitted={conflict['contested_with_admission']} "
                  f"pass_prec={conflict['passing_precision']} removed_prec={conflict['removed_precision']} | "
                  f"support-only: admitted={support['admitted']} contested_created={support['contested_created']} "
                  f"contested_admitted={support['contested_with_admission']} "
                  f"pass_prec={support['passing_precision']} removed_prec={support['removed_precision']}")

        for arm_name in ("conflict_adjusted", "support_only"):
            seed_rows = per_seed_results[arm_name][rate_key]
            boot = product_clustered_bootstrap(
                pooled[arm_name]["pass_subj"], pooled[arm_name]["pass_gold"],
                pooled[arm_name]["rem_subj"], pooled[arm_name]["rem_gold"],
                BOOT_SEED, N_BOOTSTRAP,
            )
            rate_aggregates[arm_name][rate_key] = {
                "n_seeds": len(seed_rows),
                "admitted_mean_sd": mean_sample_sd([r["admitted"] for r in seed_rows]),
                "contested_created_mean_sd": mean_sample_sd([r["contested_created"] for r in seed_rows]),
                "contested_with_admission_mean_sd": mean_sample_sd([r["contested_with_admission"] for r in seed_rows]),
                "passing_precision_mean_sd": mean_sample_sd([r["passing_precision"] for r in seed_rows]),
                "removed_precision_mean_sd": mean_sample_sd([r["removed_precision"] for r in seed_rows]),
                "product_clustered_bootstrap_pass_minus_removed": boot,
            }
            print(f"[AGGREGATE] rate={rate_key} arm={arm_name}: "
                  f"passing_precision={rate_aggregates[arm_name][rate_key]['passing_precision_mean_sd']} "
                  f"removed_precision={rate_aggregates[arm_name][rate_key]['removed_precision_mean_sd']} "
                  f"bootstrap(pass-removed)={boot}")

    output = {"per_seed": per_seed_results, "rate_aggregates": rate_aggregates}
    with open(OUT_DIR / "dec028_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved -> {OUT_DIR}/dec028_results.json")


if __name__ == "__main__":
    main()
