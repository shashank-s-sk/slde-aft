"""DEC-001 part 5 — run the OFFICIAL CaRB scorer (data/CaRB/carb.py),
not this project's internal normalized exact-match evaluator.

Every CaRB number reported so far (EVID-003/004/021) used an internal
evaluator. This script converts the already-collected predictions
(outputs/dec001_002_carb30/{slde_aft_llama,deepseek_baseline}/
predictions.json, from EVID-021's pinned-model N=30 run) into CaRB's
tab-separated format and runs data/CaRB/carb.py's real scorer against
it, using CaRB's own default matching function
(Matcher.binary_linient_tuple_match -- the standard "CaRB score"
reported in the literature when no matching flag is specified).

Correction made while building this: the 30 sentences are labeled
"carb_dev_sample.jsonl" in this project, but were verified (by exact
sentence-text lookup) to all be present in CaRB's official TEST split
gold file (data/CaRB/data/gold/test.tsv), not dev.tsv. This is a
naming/labeling correction, not a leakage concern -- CaRB is an
extraction-quality-only benchmark in this project, never used to train
or tune anything.

No per-triple confidence scores were captured during the original
extraction (prompts/openie_carb_v1.txt doesn't ask for one), so every
extracted triple gets a uniform confidence of 1.0 -- this collapses
CaRB's usual precision-recall CURVE to a single point, which is normal
for systems that don't emit calibrated per-triple confidence and does
not affect the resulting precision/recall/F1 values themselves.

Usage (pure Python, no API/GPU cost):
    python scripts/dec001_run_official_carb_scorer.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DEV_SAMPLE_PATH = "data/carb_dev_sample.jsonl"
GOLD_TEST_TSV = "data/CaRB/data/gold/test.tsv"
OUT_DIR = Path("outputs/dec001_official_carb")
SYSTEMS = {
    "slde_aft_llama": "outputs/dec001_002_carb30/slde_aft_llama/predictions.json",
    "deepseek_baseline": "outputs/dec001_002_carb30/deepseek_baseline/predictions.json",
}


def load_sample_sentences() -> list[str]:
    sentences = []
    with open(DEV_SAMPLE_PATH, encoding="utf-8") as f:
        for line in f:
            sentences.append(json.loads(line)["sentence"])
    return sentences


def write_gold_subset(sentences: list[str], out_path: Path) -> None:
    wanted = set(sentences)
    kept = []
    with open(GOLD_TEST_TSV, encoding="utf-8") as f:
        for line in f:
            sent = line.split("\t", 1)[0]
            if sent in wanted:
                kept.append(line.rstrip("\n"))
    found_sentences = set(line.split("\t", 1)[0] for line in kept)
    missing = wanted - found_sentences
    if missing:
        print(f"WARNING: {len(missing)}/{len(wanted)} sample sentences not found in {GOLD_TEST_TSV}")
    out_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"Wrote gold subset: {len(found_sentences)}/{len(wanted)} sentences, {len(kept)} gold triples -> {out_path}")


def write_tabbed_predictions(predictions_path: str, out_path: Path) -> None:
    with open(predictions_path, encoding="utf-8") as f:
        predictions = json.load(f)
    lines = []
    for item in predictions:
        sent = item["sentence"]
        for t in item.get("predicted_triples", []):
            fields = [sent, "1.0", t["predicate"], t["subject"], t["object"]]
            lines.append("\t".join(fields))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} predicted triples ({len(predictions)} sentences) -> {out_path}")


def run_carb_scorer(gold_path: Path, tabbed_path: Path, dat_out_path: Path) -> str:
    result = subprocess.run(
        [sys.executable, "carb.py",
         f"--gold={gold_path.resolve()}",
         f"--out={dat_out_path.resolve()}",
         f"--tabbed={tabbed_path.resolve()}"],
        cwd="data/CaRB", capture_output=True, text=True,
    )
    return result.stdout + result.stderr


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sentences = load_sample_sentences()
    print(f"Loaded {len(sentences)} sentences from {DEV_SAMPLE_PATH}")

    gold_subset_path = OUT_DIR / "gold_subset_30.tsv"
    write_gold_subset(sentences, gold_subset_path)

    results = {}
    for system_name, predictions_path in SYSTEMS.items():
        print(f"\n=== {system_name} ===")
        tabbed_path = OUT_DIR / f"{system_name}_tabbed.tsv"
        write_tabbed_predictions(predictions_path, tabbed_path)
        dat_out_path = OUT_DIR / f"{system_name}_pr_curve.dat"
        output = run_carb_scorer(gold_subset_path, tabbed_path, dat_out_path)
        print(output)
        results[system_name] = output

    with open(OUT_DIR / "official_carb_scorer_raw_output.txt", "w", encoding="utf-8") as f:
        for name, output in results.items():
            f.write(f"=== {name} ===\n{output}\n\n")
    print(f"\nSaved raw scorer output -> {OUT_DIR}/official_carb_scorer_raw_output.txt")


if __name__ == "__main__":
    main()
