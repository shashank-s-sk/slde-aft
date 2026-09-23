"""DEC-026 -- offline replay comparing confidence-aggregation rules
(R1 max-merge, R2 published, R3 source-count, R4 evidence-share,
R5 = R3+R4, and the post-hoc exploratory R6 unsquared evidence-share)
over already-saved gold-labeled PKB snapshots. Zero new API/GPU cost --
reuses outputs/dec003_product_probkb_v2 and outputs/dec006_scaleup_probkb's
already-collected snapshots. Implements Decision log.md's DEC-026
pre-registration (plus its follow-up addendum, which added R6 and the
fixed-tau=0.88 secondary analysis after seeing R4's null) exactly; see
that entry for the full rationale behind every design choice made here.

Usage: python -m scripts.dec026_aggregation_rules_replay
"""

from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from src.pkb_instrumentation import normalized_object, normalized_slot
from src.pkb_math import conflict_adjusted_confidence, conservative_noisy_or

SHRINKAGE = 0.75
SPLIT_SEED = 42
BOOT_SEED = 12345
N_BOOTSTRAP = 10_000
N_BINS = 10
FIXED_TAU = 0.88  # the pipeline's actual operating threshold everywhere else in this project
RULES = [
    "R1_max_merge", "R2_published", "R3_source_count", "R4_evidence_share", "R5_combined",
    "R6_evidence_share_unsquared",
]
EXPLORATORY_RULES = {"R6_evidence_share_unsquared"}  # added post-hoc after seeing R4's null; not part of the original DEC-026 pre-registration
BASELINE_RULE = "R2_published"

OUT_DIR = Path("outputs/dec026_aggregation_rules")

DATASETS = {
    "product657": dict(
        snapshot="outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv",
        gold_module="scripts.dec003_product_probkb_run",
    ),
    "product200": dict(
        snapshot="outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv",
        gold_module="scripts.dec006_scaleup_probkb_run",
    ),
}


# ---------------------------------------------------------------- gold ----

def load_gold_by_product(gold_module_name: str) -> dict[str, set[tuple[str, str, str]]]:
    """Reuses the exact gold-reconstruction logic from the original DEC-003/
    DEC-006 run scripts (imported, not re-derived) to build {raw product
    name: normalized gold-key set} for the train-split products."""
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


# ---------------------------------------------------------------- rules ----

def r1_max_merge(confs: list[float]) -> float:
    return max(confs)


def r3_support(confs: list[float], source_types: list[str], source_ids: list[str]) -> float:
    rep: dict[tuple[str, str], float] = {}
    for stype, sid, c in zip(source_types, source_ids, confs):
        key = (stype, sid)
        if key not in rep or c > rep[key]:
            rep[key] = c
    return conservative_noisy_or(list(rep.values()), shrinkage=SHRINKAGE)


def compute_rule_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["observation_confidences"] = df["observation_confidences"].apply(json.loads)
    df["source_ids"] = df["source_ids"].apply(json.loads)
    df["source_types"] = df["source_types"].apply(json.loads)

    norm = df.apply(lambda r: normalized_slot(r["subject"], r["predicate"]), axis=1)
    df["subject_norm"] = norm.apply(lambda t: t[0])
    df["predicate_norm"] = norm.apply(lambda t: t[1])
    df["object_norm"] = df["object"].apply(normalized_object)

    df["R1_max_merge"] = df["observation_confidences"].apply(r1_max_merge)

    # R2: published rule -- already computed and stored by the original run.
    df["R2_published"] = df["conflict_adjusted_final_confidence"]
    df["_R2_support"] = df["conservative_noisy_or_support"]

    # R3: distinct-(source_type, source_id) Noisy-Or, same conflict gating as R2.
    df["_R3_support"] = df.apply(
        lambda r: r3_support(r["observation_confidences"], r["source_types"], r["source_ids"]),
        axis=1,
    )
    df["R3_source_count"] = df.apply(
        lambda r: conflict_adjusted_confidence(r["_R3_support"], int(r["competitor_count"]))
        if r["functional_predicate"] else r["_R3_support"],
        axis=1,
    )

    # R4: evidence-share on top of R2's original (repeat-counted) support.
    slot_sum_r2 = df.groupby(["subject_norm", "predicate_norm"])["_R2_support"].transform("sum")
    df["R4_evidence_share"] = np.where(
        df["functional_predicate"],
        np.where(slot_sum_r2 > 0, (df["_R2_support"] ** 2) / slot_sum_r2, 0.0),
        df["_R2_support"],
    )

    # R5: R3 + R4 combined -- evidence-share on top of R3's distinct-source support.
    slot_sum_r3 = df.groupby(["subject_norm", "predicate_norm"])["_R3_support"].transform("sum")
    df["R5_combined"] = np.where(
        df["functional_predicate"],
        np.where(slot_sum_r3 > 0, (df["_R3_support"] ** 2) / slot_sum_r3, 0.0),
        df["_R3_support"],
    )

    # R6 (exploratory, post-hoc): unsquared evidence share on R2's original
    # support, same scope/input as R4 -- added after R4's null to check
    # whether squaring, not the ceiling-removal idea itself, was the reason
    # R4 never moved any contested slot past threshold.
    df["R6_evidence_share_unsquared"] = np.where(
        df["functional_predicate"],
        np.where(slot_sum_r2 > 0, df["_R2_support"] / slot_sum_r2, 0.0),
        df["_R2_support"],
    )

    return df


# ------------------------------------------------------------- metrics ----

def prf_from_counts(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "tp": tp, "fp": fp, "fn": fn}


def per_subject_counts(
    sub_df: pd.DataFrame, score_col: str, tau: float, gold_by_product: dict[str, set]
) -> dict[str, tuple[int, int, int]]:
    out = {}
    for subj, g in sub_df.groupby("subject"):
        pred = set(g.loc[g[score_col] >= tau, "triple_key"])
        gold_strs = keys_to_strs(gold_by_product.get(subj, set()))
        tp = len(pred & gold_strs)
        fp = len(pred - gold_strs)
        fn = len(gold_strs - pred)
        out[subj] = (tp, fp, fn)
    return out


def prf_at_threshold(
    sub_df: pd.DataFrame, score_col: str, tau: float, gold_by_product: dict[str, set]
) -> dict:
    counts = per_subject_counts(sub_df, score_col, tau, gold_by_product)
    tp = sum(c[0] for c in counts.values())
    fp = sum(c[1] for c in counts.values())
    fn = sum(c[2] for c in counts.values())
    return prf_from_counts(tp, fp, fn)


def select_threshold(val_df: pd.DataFrame, score_col: str, gold_by_product: dict[str, set]) -> tuple[float, pd.DataFrame]:
    grid_rows = []
    best_tau, best_f1 = 0.0, -1.0
    for i in range(101):
        tau = i / 100
        m = prf_at_threshold(val_df, score_col, tau, gold_by_product)
        grid_rows.append({"tau": tau, **m})
        if m["f1"] >= best_f1:
            best_f1, best_tau = m["f1"], tau
    return best_tau, pd.DataFrame(grid_rows)


def compute_ece_brier(sub_df: pd.DataFrame, score_col: str, label_col: str = "gold_label") -> tuple[float, float, pd.DataFrame]:
    d = sub_df.dropna(subset=[label_col])
    n_total = len(d)
    edges = [i / N_BINS for i in range(N_BINS + 1)]
    rows = []
    ece = 0.0
    for i in range(N_BINS):
        lo, hi = edges[i], edges[i + 1]
        if i == N_BINS - 1:
            in_bin = d[(d[score_col] >= lo) & (d[score_col] <= hi)]
        else:
            in_bin = d[(d[score_col] >= lo) & (d[score_col] < hi)]
        n = len(in_bin)
        if n == 0:
            rows.append({"bin_lower": lo, "bin_upper": hi, "n": 0, "mean_score": None, "empirical_positive_rate": None, "abs_gap": None})
            continue
        mean_score = in_bin[score_col].mean()
        pos_rate = in_bin[label_col].mean()
        gap = abs(pos_rate - mean_score)
        ece += (n / n_total) * gap
        rows.append({"bin_lower": lo, "bin_upper": hi, "n": n, "mean_score": mean_score, "empirical_positive_rate": pos_rate, "abs_gap": gap})
    brier = ((d[score_col] - d[label_col]) ** 2).mean() if n_total else None
    return ece, brier, pd.DataFrame(rows)


def contested_admitted_count(sub_df: pd.DataFrame, score_col: str, tau: float) -> int:
    func_df = sub_df[sub_df["functional_predicate"]]
    slot_nobj = func_df.groupby(["subject_norm", "predicate_norm"])["object_norm"].nunique()
    contested_slots = set(slot_nobj[slot_nobj >= 2].index)
    if not contested_slots:
        return 0
    admitted_any = 0
    for slot, g in func_df.groupby(["subject_norm", "predicate_norm"]):
        if slot in contested_slots and (g[score_col] >= tau).any():
            admitted_any += 1
    return admitted_any


def bootstrap_f1_diff(
    subjects: list[str],
    counts_rule: dict[str, tuple[int, int, int]],
    counts_base: dict[str, tuple[int, int, int]],
    seed: int,
    n_boot: int,
) -> dict:
    """F1-only bootstrap CI (original DEC-026 pre-registration).
    Kept as-is for the F1-selected-threshold comparison; see
    bootstrap_prf_diff for the fixed-tau precision/recall/F1 triple
    added in the follow-up round."""
    full = bootstrap_prf_diff(subjects, counts_rule, counts_base, seed, n_boot)
    return {
        "mean_diff": full["f1"]["mean_diff"],
        "ci_lower_2.5pct": full["f1"]["ci_lower_2.5pct"],
        "ci_upper_97.5pct": full["f1"]["ci_upper_97.5pct"],
        "excludes_zero": full["f1"]["excludes_zero"],
        "n_bootstrap": n_boot,
    }


def bootstrap_prf_diff(
    subjects: list[str],
    counts_rule: dict[str, tuple[int, int, int]],
    counts_base: dict[str, tuple[int, int, int]],
    seed: int,
    n_boot: int,
) -> dict:
    """Subject-level cluster bootstrap CI for precision, recall, AND F1
    differences (rule - base), reported separately. Used both for the
    original F1-selected comparison and (follow-up round) for the
    fixed-tau=0.88 comparison, which needs all three metrics, not just F1."""
    n = len(subjects)
    tp_r = np.array([counts_rule[s][0] for s in subjects])
    fp_r = np.array([counts_rule[s][1] for s in subjects])
    fn_r = np.array([counts_rule[s][2] for s in subjects])
    tp_b = np.array([counts_base[s][0] for s in subjects])
    fp_b = np.array([counts_base[s][1] for s in subjects])
    fn_b = np.array([counts_base[s][2] for s in subjects])

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))

    tp_r_s = tp_r[idx].sum(axis=1)
    fp_r_s = fp_r[idx].sum(axis=1)
    fn_r_s = fn_r[idx].sum(axis=1)
    tp_b_s = tp_b[idx].sum(axis=1)
    fp_b_s = fp_b[idx].sum(axis=1)
    fn_b_s = fn_b[idx].sum(axis=1)

    def prec_vec(tp, fp):
        return np.where((tp + fp) > 0, tp / np.maximum(tp + fp, 1), 0.0)

    def rec_vec(tp, fn):
        return np.where((tp + fn) > 0, tp / np.maximum(tp + fn, 1), 0.0)

    def f1_vec(prec, rec):
        denom = prec + rec
        return np.where(denom > 0, 2 * prec * rec / np.where(denom > 0, denom, 1), 0.0)

    prec_r, rec_r = prec_vec(tp_r_s, fp_r_s), rec_vec(tp_r_s, fn_r_s)
    prec_b, rec_b = prec_vec(tp_b_s, fp_b_s), rec_vec(tp_b_s, fn_b_s)
    f1_r, f1_b = f1_vec(prec_r, rec_r), f1_vec(prec_b, rec_b)

    def summarize(diffs: np.ndarray) -> dict:
        diffs = np.sort(diffs)
        lo = float(np.percentile(diffs, 2.5))
        hi = float(np.percentile(diffs, 97.5))
        return {
            "mean_diff": float(diffs.mean()),
            "ci_lower_2.5pct": lo,
            "ci_upper_97.5pct": hi,
            "excludes_zero": bool(lo > 0 or hi < 0),
            "n_bootstrap": n_boot,
        }

    return {
        "precision": summarize(prec_r - prec_b),
        "recall": summarize(rec_r - rec_b),
        "f1": summarize(f1_r - f1_b),
    }


# ---------------------------------------------------------------- main ----

def run_dataset(name: str, spec: dict) -> None:
    print(f"\n=== Dataset {name} ===")
    raw = pd.read_csv(spec["snapshot"])
    df = compute_rule_scores(raw)

    gold_by_product = load_gold_by_product(spec["gold_module"])

    full_gold_strs = set()
    for g in gold_by_product.values():
        full_gold_strs |= keys_to_strs(g)
    labeled = df.dropna(subset=["gold_label"])
    mismatch = (labeled["triple_key"].isin(full_gold_strs)) != (labeled["gold_label"] == 1)
    n_mismatch = int(mismatch.sum())
    if n_mismatch:
        raise RuntimeError(
            f"{name}: {n_mismatch} rows where reconstructed gold membership "
            "disagrees with the snapshot's own gold_label column -- gold "
            "reconstruction is not trustworthy, stopping rather than reporting."
        )
    print(f"Gold reconstruction sanity check: 0/{len(labeled)} mismatches against stored gold_label.")

    subjects = sorted(df["subject"].unique())
    rng = random.Random(SPLIT_SEED)
    rng.shuffle(subjects)
    half = len(subjects) // 2
    val_subjects = set(subjects[:half])
    test_subjects = set(subjects[half:])
    df["split"] = df["subject"].apply(lambda s: "val" if s in val_subjects else "test")

    missing = [p for p in gold_by_product if p not in val_subjects and p not in test_subjects]
    if missing:
        raise RuntimeError(f"{name}: {len(missing)} gold products never appear as a candidate subject: {missing}")

    val_df = df[df["split"] == "val"]
    test_df = df[df["split"] == "test"]
    print(f"Subjects: {len(subjects)} total ({len(val_subjects)} val / {len(test_subjects)} test); "
          f"triples: {len(df)} total ({len(val_df)} val / {len(test_df)} test)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Follow-up #3: state the recall denominator explicitly and save it.
    # gold_by_product is built from `gold_unstructured` (imported from the
    # original DEC-003/DEC-006 run scripts' own normalize_gold), the SAME
    # gold definition those scripts used for their own train_gold_keys and
    # for the snapshot's own gold_label column (verified equal above, 0
    # mismatches). It is NOT the same gold definition used elsewhere in
    # this project: DEC-019/EVID-030's closed-loop recall uses
    # `gold_structured` (all structured-column facts per product, a
    # larger/stricter set), and EVID-013's held-out val/test recall is
    # measured on different (non-train) products from a single raw
    # extraction pass with no threshold admission at all. See EVID-041 for
    # the full comparability statement.
    val_gold_keys = set()
    test_gold_keys = set()
    for pname, gk in gold_by_product.items():
        if pname in val_subjects:
            val_gold_keys |= gk
        else:
            test_gold_keys |= gk
    full_gold_keys = val_gold_keys | test_gold_keys
    n_gold_positive_candidates = int((df["gold_label"] == 1).sum())

    with open(OUT_DIR / f"{name}_val_test_split.json", "w", encoding="utf-8") as f:
        json.dump({
            "split_seed": SPLIT_SEED,
            "n_subjects_total": len(subjects),
            "val_subjects": sorted(val_subjects),
            "test_subjects": sorted(test_subjects),
            "recall_denominator": {
                "definition": "gold_unstructured facts for train-split products, imported "
                               "from the original run script's own normalize_gold() -- same "
                               "gold set the snapshot's own gold_label column was built from.",
                "n_gold_keys_total": len(full_gold_keys),
                "n_gold_keys_val": len(val_gold_keys),
                "n_gold_keys_test": len(test_gold_keys),
                "n_gold_positive_candidate_rows_in_snapshot": n_gold_positive_candidates,
                "every_gold_key_was_extracted_at_least_once": len(full_gold_keys) == n_gold_positive_candidates,
            },
        }, f, indent=2)
    print(f"Recall denominator: {len(full_gold_keys)} total gold_unstructured keys "
          f"({len(val_gold_keys)} val / {len(test_gold_keys)} test); "
          f"{n_gold_positive_candidates} gold-positive candidate rows already in the snapshot "
          f"(equal: {len(full_gold_keys) == n_gold_positive_candidates}).")

    thresholds = {}
    grid_frames = []
    metrics_summary = {}
    bootstrap_summary = {}
    per_subject_test_counts = {}
    per_subject_test_counts_fixed = {}

    for rule in RULES:
        tau, grid_df = select_threshold(val_df, rule, gold_by_product)
        thresholds[rule] = tau
        grid_df.insert(0, "rule", rule)
        grid_frames.append(grid_df)

        test_metrics = prf_at_threshold(test_df, rule, tau, gold_by_product)
        ece, brier, _bins = compute_ece_brier(test_df, rule)
        n_admitted = int((test_df[rule] >= tau).sum())
        n_contested_admitted = contested_admitted_count(test_df, rule, tau)

        # Secondary analysis (follow-up #1): same test split, same rule,
        # but the threshold fixed at the pipeline's actual operating point
        # (tau=0.88) instead of validation-selected -- reported alongside,
        # not instead of, the F1-selected numbers above.
        fixed_metrics = prf_at_threshold(test_df, rule, FIXED_TAU, gold_by_product)
        fixed_n_admitted = int((test_df[rule] >= FIXED_TAU).sum())
        fixed_n_contested_admitted = contested_admitted_count(test_df, rule, FIXED_TAU)

        metrics_summary[rule] = {
            "exploratory_posthoc": rule in EXPLORATORY_RULES,
            "f1_selected": {
                "selected_tau": tau,
                "precision": test_metrics["precision"],
                "recall": test_metrics["recall"],
                "f1": test_metrics["f1"],
                "tp": test_metrics["tp"],
                "fp": test_metrics["fp"],
                "fn": test_metrics["fn"],
                "n_admitted_test": n_admitted,
                "n_contested_slots_with_admission_test": n_contested_admitted,
            },
            "fixed_tau_0.88": {
                "tau": FIXED_TAU,
                "precision": fixed_metrics["precision"],
                "recall": fixed_metrics["recall"],
                "f1": fixed_metrics["f1"],
                "tp": fixed_metrics["tp"],
                "fp": fixed_metrics["fp"],
                "fn": fixed_metrics["fn"],
                "n_admitted_test": fixed_n_admitted,
                "n_contested_slots_with_admission_test": fixed_n_contested_admitted,
            },
            "ece": ece,
            "brier": brier,
        }

        per_subject_test_counts[rule] = per_subject_counts(test_df, rule, tau, gold_by_product)
        per_subject_test_counts_fixed[rule] = per_subject_counts(test_df, rule, FIXED_TAU, gold_by_product)

        print(f"  {rule}: [F1-selected] tau={tau:.2f} P={test_metrics['precision']:.4f} "
              f"R={test_metrics['recall']:.4f} F1={test_metrics['f1']:.4f} "
              f"admitted={n_admitted} contested_admitted={n_contested_admitted} | "
              f"[tau=0.88] P={fixed_metrics['precision']:.4f} R={fixed_metrics['recall']:.4f} "
              f"F1={fixed_metrics['f1']:.4f} admitted={fixed_n_admitted} "
              f"contested_admitted={fixed_n_contested_admitted} | ECE={ece:.4f} Brier={brier:.4f}")

    base_counts = per_subject_test_counts[BASELINE_RULE]
    test_subjects_sorted = sorted(test_subjects)
    for rule in RULES:
        if rule == BASELINE_RULE:
            continue
        boot = bootstrap_f1_diff(
            test_subjects_sorted, per_subject_test_counts[rule], base_counts, BOOT_SEED, N_BOOTSTRAP
        )
        bootstrap_summary[rule] = boot
        print(f"  bootstrap F1({rule}) - F1({BASELINE_RULE}): mean={boot['mean_diff']:.4f} "
              f"95% CI=[{boot['ci_lower_2.5pct']:.4f}, {boot['ci_upper_97.5pct']:.4f}] "
              f"excludes_zero={boot['excludes_zero']}")

    # Follow-up #1 (round 2): bootstrap CIs at the FIXED tau=0.88 operating
    # point too, precision/recall/F1 reported separately -- this is the
    # threshold that goes in the paper, so it needs its own CIs, not just
    # the F1-selected ones above. Requested specifically for R1 vs R2 and
    # R3 vs R2 (the two rules that actually differ from R2 in outcome).
    fixed_tau_bootstrap_summary = {}
    base_counts_fixed = per_subject_test_counts_fixed[BASELINE_RULE]
    for rule in ["R1_max_merge", "R3_source_count"]:
        boot_prf = bootstrap_prf_diff(
            test_subjects_sorted, per_subject_test_counts_fixed[rule], base_counts_fixed, BOOT_SEED, N_BOOTSTRAP
        )
        fixed_tau_bootstrap_summary[rule] = boot_prf
        print(f"  [tau=0.88] bootstrap {rule} - {BASELINE_RULE}: "
              f"P diff mean={boot_prf['precision']['mean_diff']:.4f} "
              f"CI=[{boot_prf['precision']['ci_lower_2.5pct']:.4f}, {boot_prf['precision']['ci_upper_97.5pct']:.4f}] "
              f"excl0={boot_prf['precision']['excludes_zero']} | "
              f"R diff mean={boot_prf['recall']['mean_diff']:.4f} "
              f"CI=[{boot_prf['recall']['ci_lower_2.5pct']:.4f}, {boot_prf['recall']['ci_upper_97.5pct']:.4f}] "
              f"excl0={boot_prf['recall']['excludes_zero']} | "
              f"F1 diff mean={boot_prf['f1']['mean_diff']:.4f} "
              f"CI=[{boot_prf['f1']['ci_lower_2.5pct']:.4f}, {boot_prf['f1']['ci_upper_97.5pct']:.4f}] "
              f"excl0={boot_prf['f1']['excludes_zero']}")

    pd.concat(grid_frames, ignore_index=True).to_csv(OUT_DIR / f"{name}_threshold_selection.csv", index=False)

    with open(OUT_DIR / f"{name}_metrics_summary.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    with open(OUT_DIR / f"{name}_bootstrap_ci.json", "w", encoding="utf-8") as f:
        json.dump(bootstrap_summary, f, indent=2)

    with open(OUT_DIR / f"{name}_bootstrap_ci_fixed_tau.json", "w", encoding="utf-8") as f:
        json.dump(fixed_tau_bootstrap_summary, f, indent=2)

    score_cols = RULES
    admitted_cols = {}
    for rule in RULES:
        admitted_cols[f"{rule}_admitted_at_test_tau"] = df[rule] >= thresholds[rule]
    out_df = df[["triple_key", "subject", "predicate", "object", "split", "functional_predicate",
                 "competitor_count", "gold_label"] + score_cols].copy()
    for col, vals in admitted_cols.items():
        out_df[col] = vals
    out_df.to_csv(OUT_DIR / f"{name}_per_triple_scores.csv", index=False)

    print(f"Saved -> {OUT_DIR}/{name}_*")


def main():
    for name, spec in DATASETS.items():
        run_dataset(name, spec)


if __name__ == "__main__":
    main()
