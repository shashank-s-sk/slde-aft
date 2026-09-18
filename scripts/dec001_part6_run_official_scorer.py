"""DEC-001 Part 6 — run the OFFICIAL CaRB scorer (data/CaRB/carb.py) on
the full 548-sentence scale-up, same method as EVID-031's 30-sentence
pilot (see scripts/dec001_run_official_carb_scorer.py), adapted for:
- predictions.jsonl (one JSON object per line, incremental/resumable
  format) instead of predictions.json (a single JSON array)
- the full 548-sentence gold set (data/carb_full_sample.jsonl) instead
  of the 30-sentence sample

Usage (pure Python, no API/GPU cost):
    python -m scripts.dec001_part6_run_official_scorer
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

FULL_SAMPLE_PATH = "data/carb_full_sample.jsonl"
GOLD_TEST_TSV = "data/CaRB/data/gold/test.tsv"
OUT_DIR = Path("outputs/dec001_part6_official_carb")
SYSTEMS = {
    "slde_aft_llama": "outputs/dec001_part6_carb_full/slde_aft_llama/predictions.jsonl",
    "deepseek_baseline": "outputs/dec001_part6_carb_full/deepseek_baseline/predictions.jsonl",
}


def load_sample_sentences() -> list[str]:
    sentences = []
    with open(FULL_SAMPLE_PATH, encoding="utf-8") as f:
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


def write_tabbed_predictions(predictions_jsonl_path: str, out_path: Path) -> None:
    lines = []
    n_sentences = 0
    with open(predictions_jsonl_path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            item = json.loads(raw)
            n_sentences += 1
            sent = item["sentence"]
            for t in item.get("predicted_triples", []):
                fields = [sent, "1.0", t["predicate"], t["subject"], t["object"]]
                lines.append("\t".join(fields))
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} predicted triples ({n_sentences} sentences) -> {out_path}")


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
    print(f"Loaded {len(sentences)} sentences from {FULL_SAMPLE_PATH}")

    gold_subset_path = OUT_DIR / "gold_subset_full.tsv"
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
