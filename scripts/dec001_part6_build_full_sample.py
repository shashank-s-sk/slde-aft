"""DEC-001 Part 6: build the full-scale CaRB sample (all test-split
sentences that have >=1 gold triple), replicating the exact selection
logic used to build the original 30-sentence `carb_dev_sample.jsonl`
(iterate data/CaRB/data/test.txt in file order, keep sentences that
appear in data/CaRB/data/gold/test.tsv, attach their gold triples) --
just without truncating to 30.

Zero cost, pure data prep.

Usage: python -m scripts.dec001_part6_build_full_sample
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

TEST_TXT = Path("data/CaRB/data/test.txt")
GOLD_TSV = Path("data/CaRB/data/gold/test.tsv")
OUT_PATH = Path("data/carb_full_sample.jsonl")


def load_gold() -> dict[str, list[dict]]:
    gold_by_sentence: dict[str, list[dict]] = defaultdict(list)
    with open(GOLD_TSV, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 4:
                continue
            sentence, predicate, subject, obj = parts
            gold_by_sentence[sentence].append({
                "subject": subject, "predicate": predicate, "object": obj,
            })
    return gold_by_sentence


def main():
    gold_by_sentence = load_gold()
    sentences = [l.rstrip("\n") for l in open(TEST_TXT, encoding="utf-8")]

    records = []
    for sentence in sentences:
        if sentence in gold_by_sentence:
            records.append({
                "sentence_id": f"carb_test_{len(records) + 1:04d}",
                "sentence": sentence,
                "gold_triples": gold_by_sentence[sentence],
            })

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Total sentences in test.txt: {len(sentences)}")
    print(f"Sentences with gold triples: {len(records)}")
    print(f"Saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()
