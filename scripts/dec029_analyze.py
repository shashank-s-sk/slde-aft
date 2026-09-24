"""DEC-029 analysis -- run AFTER scripts/dec029_ablation_extended.py.
Zero cost, pure Python.

Combines DEC-023's 5 seeds (42-46, read from
outputs/dec023_ablation_n50/all_runs_summary.csv, never modified) with
DEC-029's 25 new seeds (47-71) and computes exactly the statistics
pre-registered in Decision log.md DEC-029, for `without_feedback` and
`without_prob_kb` each against `full`, on held-out test F1:

  - paired t-test and Wilcoxon signed-rank (EVID-020/039's method);
  - 95% CI of the mean paired difference: paired bootstrap over seeds,
    10,000 resamples, [2.5, 97.5] percentile interval;
  - achieved minimum detectable effect (MDE), paired t-test,
    alpha=0.05 two-sided, 80% power. The required Cohen's d is solved
    from the noncentral t distribution (reproduces AUDIT.md's d=1.682
    at n=5). Two versions are reported:
      * pre-registered / AUDIT.md method: d x the ablated condition's
        own observed sample SD;
      * d x the sample SD of the paired differences, which is the SD a
        paired t-test actually uses.

Usage: python -m scripts.dec029_analyze
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
from scipy import optimize, stats

DEC023_SUMMARY = Path("outputs/dec023_ablation_n50/all_runs_summary.csv")
DEC029_SUMMARY = Path("outputs/dec029_ablation_extended/all_runs_summary.csv")
OUT_PATH = Path("outputs/dec029_ablation_extended/analysis_result.json")
CONFIGS = ["full", "without_feedback", "without_prob_kb"]
N_BOOTSTRAP = 10_000
BOOT_SEED = 20290923
ALPHA = 0.05
POWER = 0.80


def load_rows(path: Path) -> dict[tuple[str, int], float]:
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["config"] in CONFIGS and row["held_out_test_f1"] not in ("", "None"):
                out[(row["config"], int(row["seed"]))] = float(row["held_out_test_f1"])
    return out


def required_d(n: int) -> float:
    """Cohen's d giving `POWER` for a two-sided one-sample/paired t-test at n."""
    df = n - 1
    t_crit = stats.t.ppf(1 - ALPHA / 2, df)

    def power(d):
        nc = d * np.sqrt(n)
        # scipy's nct.cdf returns NaN far into the tails; the lower-tail
        # term is negligible there, so treat NaN as 0.
        upper = stats.nct.sf(t_crit, df, nc)
        lower = np.nan_to_num(stats.nct.cdf(-t_crit, df, nc))
        return upper + lower - POWER

    return optimize.brentq(power, 0.05, 3.0)


def paired_bootstrap_ci(diffs: np.ndarray) -> tuple[float, float]:
    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(diffs), size=(N_BOOTSTRAP, len(diffs)))
    means = diffs[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main():
    scores = load_rows(DEC023_SUMMARY)
    for path in sorted(DEC029_SUMMARY.parent.glob("all_runs_summary*.csv")):
        scores.update(load_rows(path))

    seeds = sorted({s for (c, s) in scores if all((cfg, s) in scores for cfg in CONFIGS)})
    dropped = sorted({s for (c, s) in scores} - set(seeds))
    print(f"Seeds with held-out test F1 for all 3 configs: {len(seeds)} "
          f"({seeds[0]}-{seeds[-1]}); dropped (incomplete): {dropped}")

    n = len(seeds)
    d_req = required_d(n)
    result = {"n_seeds": n, "seeds": seeds, "dropped_seeds": dropped,
              "required_cohens_d_80pct_power": d_req,
              "required_cohens_d_at_n5_check": required_d(5), "configs": {}, "comparisons": {}}

    per_config = {}
    for cfg in CONFIGS:
        v = np.array([scores[(cfg, s)] for s in seeds])
        per_config[cfg] = v
        result["configs"][cfg] = {"mean": float(v.mean()), "sample_sd": float(v.std(ddof=1))}
        print(f"{cfg:>17}: mean={v.mean():.4f} sample SD={v.std(ddof=1):.4f}")
    print(f"Required Cohen's d at n={n} (80% power, alpha=0.05 two-sided): {d_req:.3f} "
          f"(n=5 check: {required_d(5):.3f})")

    for cfg in ["without_feedback", "without_prob_kb"]:
        diffs = per_config[cfg] - per_config["full"]
        t = stats.ttest_rel(per_config[cfg], per_config["full"])
        w = stats.wilcoxon(diffs)
        lo, hi = paired_bootstrap_ci(diffs)
        sd_cond = float(per_config[cfg].std(ddof=1))
        sd_diff = float(diffs.std(ddof=1))
        comp = {
            "mean_diff_vs_full": float(diffs.mean()),
            "bootstrap_95ci": [lo, hi],
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
            "paired_t": {"t": float(t.statistic), "p": float(t.pvalue)},
            "wilcoxon": {"stat": float(w.statistic), "p": float(w.pvalue)},
            "sd_condition": sd_cond,
            "sd_paired_diff": sd_diff,
            "mde_preregistered_condition_sd": d_req * sd_cond,
            "mde_paired_diff_sd": d_req * sd_diff,
            "n_seeds_condition_beats_full": int((diffs > 0).sum()),
        }
        result["comparisons"][f"{cfg}_vs_full"] = comp
        print(f"\n{cfg} vs full: diff={diffs.mean():+.4f} 95% CI [{lo:+.4f}, {hi:+.4f}] "
              f"paired t={t.statistic:.3f} p={t.pvalue:.4f} Wilcoxon p={w.pvalue:.4f} "
              f"({comp['n_seeds_condition_beats_full']}/{n} seeds above full)")
        print(f"  MDE: {comp['mde_preregistered_condition_sd']:.4f} (pre-registered, condition SD "
              f"{sd_cond:.4f}); {comp['mde_paired_diff_sd']:.4f} (paired-difference SD {sd_diff:.4f})")

    OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nSaved {OUT_PATH}")


if __name__ == "__main__":
    main()
