"""DEC-003 step 6 (real-data half): confidence calibration on REAL
product-domain data, closing the gap flagged in EVID-014's Limitations
("this checks admission quality... not calibration (ECE) on real
data -- EVID-005/009's ECE results are still synthetic-only; a
real-data calibration table remains undone").

Zero new API/GPU cost -- uses the already-collected, gold-labeled
snapshot from EVID-013's real 155-call instrumented run:
outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv
(657 candidate triples, each with a `gold_label` column (1=matches
known gold, 0=doesn't) and `conflict_adjusted_final_confidence`, the
same conservative-Noisy-Or + conflict-adjustment score already used
throughout this project -- see src/pkb_math.py).

Methodology (standard ECE / reliability-diagram convention, matching
the spirit of EVID-005/009's synthetic calibration but applied to real
data for the first time):
- 10 equal-width confidence bins: [0.0,0.1), [0.1,0.2), ..., [0.9,1.0]
- Per bin: n (count), mean predicted confidence, empirical positive
  rate (fraction of gold_label==1 in that bin -- this IS "accuracy"
  for a probabilistic binary calibration curve)
- ECE = sum_bins (n_bin / N) * |empirical_positive_rate - mean_confidence|
- Brier score = mean((confidence - gold_label)^2) over all triples

Usage: python -m scripts.dec003_real_data_calibration
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

SNAPSHOT_PATH = Path("outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv")
CONFIDENCE_COL = "conflict_adjusted_final_confidence"
LABEL_COL = "gold_label"
OUT_DIR = Path("outputs/dec003_real_calibration")
N_BINS = 10


def compute_ece_and_bins(df: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    edges = [i / N_BINS for i in range(N_BINS + 1)]
    rows = []
    n_total = len(df)
    ece = 0.0

    for i in range(N_BINS):
        lo, hi = edges[i], edges[i + 1]
        if i == N_BINS - 1:
            in_bin = df[(df[CONFIDENCE_COL] >= lo) & (df[CONFIDENCE_COL] <= hi)]
        else:
            in_bin = df[(df[CONFIDENCE_COL] >= lo) & (df[CONFIDENCE_COL] < hi)]

        n = len(in_bin)
        if n == 0:
            rows.append({"bin_lower": lo, "bin_upper": hi, "n": 0,
                         "mean_confidence": None, "empirical_positive_rate": None,
                         "abs_gap": None})
            continue

        mean_conf = in_bin[CONFIDENCE_COL].mean()
        pos_rate = in_bin[LABEL_COL].mean()
        gap = abs(pos_rate - mean_conf)
        ece += (n / n_total) * gap

        rows.append({"bin_lower": lo, "bin_upper": hi, "n": n,
                     "mean_confidence": mean_conf, "empirical_positive_rate": pos_rate,
                     "abs_gap": gap})

    return ece, pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SNAPSHOT_PATH)
    df = df.dropna(subset=[CONFIDENCE_COL, LABEL_COL])
    n = len(df)
    print(f"Loaded {n} real (subject, predicate, object) candidates from {SNAPSHOT_PATH}")
    print(f"Gold-positive: {int(df[LABEL_COL].sum())} ({df[LABEL_COL].mean():.1%}), "
          f"Gold-negative: {int((1 - df[LABEL_COL]).sum())}")

    ece, bins_df = compute_ece_and_bins(df)
    brier = ((df[CONFIDENCE_COL] - df[LABEL_COL]) ** 2).mean()

    bins_df.to_csv(OUT_DIR / "calibration_bins_real.csv", index=False)
    reliability_points = bins_df.dropna(subset=["mean_confidence"])[
        ["mean_confidence", "empirical_positive_rate", "n"]
    ]
    reliability_points.to_csv(OUT_DIR / "reliability_diagram_points_real.csv", index=False)

    summary = {
        "source_snapshot": str(SNAPSHOT_PATH), "n_triples": n,
        "n_bins": N_BINS, "ece": ece, "brier_score": brier,
        "n_gold_positive": int(df[LABEL_COL].sum()),
        "n_gold_negative": int((1 - df[LABEL_COL]).sum()),
    }
    with open(OUT_DIR / "ece_real.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nECE (real data, {N_BINS} bins): {ece:.4f}")
    print(f"Brier score (real data): {brier:.4f}")
    print("\nPer-bin detail:")
    print(bins_df.to_string(index=False))
    print(f"\nSaved -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
