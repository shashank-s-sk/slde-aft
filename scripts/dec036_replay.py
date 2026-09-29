"""DEC-036 -- replay the DEC-026 aggregation-rule comparison (R1-R6,
unchanged code) on the DEC-036 reruns, under three observation-confidence
variants of the SAME observations:

- verbalized:      the extractor's stated confidence (as in DEC-026);
- logprob:         primary logprob confidence, exp(mean token logprob) over
                   the subject/predicate/object value tokens;
- logprob_object:  secondary, joint probability of the object-value tokens.

Logprob values are read from the "LP=..;LPO=..|" provenance prefix written by
scripts/dec036_run.py. Structured observations, and LLM observations whose
tokens could not be aligned ("NA"), keep their verbalized confidence; both
are counted. The stored R2 columns are recomputed from the substituted
confidences with src.pkb_math (verified to reproduce the stored values
exactly on the verbalized snapshot).

Also reports how count-driven each score is: Spearman rho between the
Noisy-OR support A(t) and the observation count (descriptive, per DEC-036).

Usage: python -m scripts.dec036_replay
Pre-registration: Decision log.md, DEC-036 (commit 2f3a731).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

from scripts import dec026_aggregation_rules_replay as replay
from src.pkb_math import conservative_noisy_or, final_confidence

SHRINKAGE = 0.75
ROOT = Path("outputs/dec036")
RUNS = {
    "A": "scripts.dec003_product_probkb_run",
    "B": "scripts.dec006_scaleup_probkb_run",
}
MODELS = ["llama-3.1-8b-instruct", "deepseek-v3.2"]
VARIANTS = {"verbalized": None, "logprob": "LP", "logprob_object": "LPO"}
_TAG = re.compile(r"^LP=([^;]+);LPO=([^|]+)\|")


def substitute(df: pd.DataFrame, field: str | None) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    counts = {"llm_obs": 0, "llm_obs_no_logprob": 0, "structured_obs": 0}
    new_confs, supports, finals = [], [], []
    for _, r in df.iterrows():
        confs = json.loads(r["observation_confidences"])
        provs = json.loads(r["provenance"])
        stypes = json.loads(r["source_types"])
        out = []
        for c, p, st in zip(confs, provs, stypes):
            m = _TAG.match(str(p)) if st == "unstructured" else None
            if st != "unstructured":
                counts["structured_obs"] += 1
                out.append(c)
                continue
            counts["llm_obs"] += 1
            val = None
            if m and field is not None:
                raw = m.group(1) if field == "LP" else m.group(2)
                val = None if raw == "NA" else float(raw)
            if field is not None and val is None:
                counts["llm_obs_no_logprob"] += 1
            out.append(c if val is None else val)
        new_confs.append(json.dumps(out))
        supports.append(conservative_noisy_or(out, SHRINKAGE))
        finals.append(final_confidence(out, int(r["competitor_count"]), SHRINKAGE,
                                       bool(r["functional_predicate"])))
    df["observation_confidences"] = new_confs
    df["conservative_noisy_or_support"] = supports
    df["conflict_adjusted_final_confidence"] = finals
    return df, counts


def main() -> None:
    inputs = ROOT / "replay_inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    replay.OUT_DIR = ROOT / "replay"
    summary = {}
    for ds, gold_module in RUNS.items():
        for model in MODELS:
            snap = ROOT / f"{ds}_{model}" / "train_kb" / "pkb_snapshot_iteration_4.csv"
            if not snap.exists():
                print(f"missing {snap}, skipping")
                continue
            raw = pd.read_csv(snap)
            for variant, field in VARIANTS.items():
                name = f"{ds}_{model}_{variant}"
                df, counts = substitute(raw, field)
                path = inputs / f"{name}.csv"
                df.to_csv(path, index=False)
                rho = spearmanr(df["conservative_noisy_or_support"], df["observation_count"])
                llm_confs = [c for cs, st in zip(df["observation_confidences"], raw["source_types"])
                             for c, s in zip(json.loads(cs), json.loads(st)) if s == "unstructured"]
                replay.run_dataset(name, {"snapshot": str(path), "gold_module": gold_module})
                summary[name] = {
                    **counts,
                    "triples": len(df),
                    "spearman_support_vs_obs_count": {"rho": float(rho.statistic), "p": float(rho.pvalue)},
                    "llm_conf_min_median_max": [float(pd.Series(llm_confs).min()),
                                                float(pd.Series(llm_confs).median()),
                                                float(pd.Series(llm_confs).max())] if llm_confs else None,
                }
    with open(ROOT / "dec036_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
