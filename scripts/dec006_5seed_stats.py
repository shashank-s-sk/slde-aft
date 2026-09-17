"""DEC-006 5-seed statistical test (EVID-034), matching DEC-005's
5-seed convention. Base model's F1 is deterministic (greedy decoding),
so this is a one-sample test: are the 5 fine-tuned seeds' F1 values
significantly different from the fixed base F1?

Usage (pure Python + scipy, no API/GPU cost):
    python scripts/dec006_5seed_stats.py
"""

from __future__ import annotations

import json

import numpy as np
from scipy import stats

SEEDS = {
    42: "outputs/dec006_eval/mistral7b_qlora/metrics.json",
    43: "outputs/dec006_eval/mistral7b_qlora_seed43/metrics.json",
    44: "outputs/dec006_eval/mistral7b_qlora_seed44/metrics.json",
    45: "outputs/dec006_eval/mistral7b_qlora_seed45/metrics.json",
    46: "outputs/dec006_eval/mistral7b_qlora_seed46/metrics.json",
}
BASE_PATH = "outputs/dec006_eval/base_model/metrics.json"


def main():
    with open(BASE_PATH) as f:
        base_f1 = json.load(f)["f1"]

    seed_f1 = {}
    for seed, path in SEEDS.items():
        with open(path) as f:
            seed_f1[seed] = json.load(f)["f1"]

    vals = np.array(list(seed_f1.values()))
    diffs = vals - base_f1

    t_stat, t_p = stats.ttest_1samp(vals, popmean=base_f1)
    w_stat, w_p = stats.wilcoxon(diffs)

    result = {
        "base_f1": base_f1,
        "seed_f1": seed_f1,
        "mean_f1": float(vals.mean()),
        "std_f1": float(vals.std(ddof=1)),
        "mean_diff_vs_base": float(diffs.mean()),
        "n_positive": int((diffs > 0).sum()),
        "n_negative": int((diffs < 0).sum()),
        "ttest_1samp": {"t": float(t_stat), "p": float(t_p)},
        "wilcoxon_signed_rank": {"W": float(w_stat), "p": float(w_p)},
    }
    print(json.dumps(result, indent=2))

    with open("outputs/dec006_eval/five_seed_stats.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved -> outputs/dec006_eval/five_seed_stats.json")


if __name__ == "__main__":
    main()
