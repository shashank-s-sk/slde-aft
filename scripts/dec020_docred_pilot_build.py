"""DEC-020 step 1-2: build the DocRED pilot subset (data prep only,
zero API cost). Selects N_DOCS documents from the human-annotated dev
split (data/DocRED/dev.json, downloaded from the thunlp/docred
HuggingFace mirror -- MIT licensed) using a fixed seed for
reproducibility, and writes:

- outputs/dec020_docred_pilot/pilot_docs.jsonl -- one selected
  document per line (title, sentences, gold_triples, observations)
- outputs/dec020_docred_pilot/closed_predicates.json -- the 96-relation
  schema-guided predicate list, for building the extraction prompt

Deliberately biases the sample toward documents that have at least one
multi-evidence-sentence gold triple (845/998 dev docs qualify), since
those are the ones that actually exercise PKB aggregation -- the whole
point of DEC-020 versus DEC-001/DEC-021's extractor-only benchmarks.

No LLM calls here -- this is pure data preparation. Extraction (which
costs a small amount) is a separate, later step, run only after this
pilot selection is reviewed.

Usage: python -m scripts.dec020_docred_pilot_build
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from src.datasets.docred_adapter import closed_predicate_list, load_docred_split

N_DOCS = 15
SEED = 42
OUTPUT_DIR = Path("outputs/dec020_docred_pilot")


def has_multi_evidence_triple(doc: dict) -> bool:
    counts = Counter((o["subject"], o["relation"], o["object"]) for o in doc["observations"])
    return any(v > 1 for v in counts.values())


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    docs = load_docred_split()
    eligible = [d for d in docs if has_multi_evidence_triple(d)]
    print(f"Loaded {len(docs)} dev-annotated documents "
          f"({len(eligible)} have >=1 multi-evidence gold triple)")

    rng = random.Random(SEED)
    pilot = rng.sample(eligible, N_DOCS)

    with open(OUTPUT_DIR / "pilot_docs.jsonl", "w", encoding="utf-8") as f:
        for doc in pilot:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    predicates = closed_predicate_list()
    with open(OUTPUT_DIR / "closed_predicates.json", "w", encoding="utf-8") as f:
        json.dump(predicates, f, indent=2)

    total_gold = sum(len(d["gold_triples"]) for d in pilot)
    total_obs = sum(len(d["observations"]) for d in pilot)
    multi_ev_triples = sum(
        1 for d in pilot
        for count in Counter((o["subject"], o["relation"], o["object"])
                              for o in d["observations"]).values()
        if count > 1
    )

    print(f"Selected {len(pilot)} pilot documents (seed={SEED})")
    print(f"  total gold triples: {total_gold}")
    print(f"  total observations (triple x evidence-sentence): {total_obs}")
    print(f"  gold triples with >=2 evidence sentences: {multi_ev_triples}")
    print(f"  closed predicate schema size: {len(predicates)}")
    print(f"Saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
