"""DEC-009 biomedical domain pilot: BioRED, dev split, first N abstracts.
Same architecture as the rest of the project — same triple schema, same
evaluator, same pinned model (meta-llama/llama-3.1-8b-instruct) as the
core pipeline (per the provider plan in memory: DeepSeek is reserved for
DEC-002's baseline comparison only, not the core pipeline).

Per DEC-009's own rules: only Dev-split data used (never Test), and no
BioRED labels are used for prompt design beyond what's already fixed in
prompts/openie_biored_v1.txt (the six relation types are BioRED's own
public schema, not tuned against these specific gold labels).

Usage: python -m scripts.dec009_biored_pilot
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.datasets.biored_adapter import load_biored_split
from src.evaluator import Triple, compute_precision_recall_f1
from src.extractors.openrouter_openie import extract_openie_triples

N_DOCS = 15
MODEL = "meta-llama/llama-3.1-8b-instruct"
OUTPUT_DIR = Path("outputs/dec009_biored_pilot")


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def main():
    api_key = load_api_key()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    docs = load_biored_split("Dev")[:N_DOCS]
    prompt_template = Path("prompts/openie_biored_v1.txt").read_text(encoding="utf-8")

    predictions = []
    call_log = []
    all_pred_triples = []
    all_gold_triples = []
    total_cost = 0.0

    for doc in docs:
        result = extract_openie_triples(
            doc["text"], api_key=api_key, model=MODEL,
            prompt_template=prompt_template, max_tokens=1024,
        )
        cost = result.get("cost_usd") or 0.0
        total_cost += cost

        gold = [(s, p, o) for s, p, o, _ in doc["gold_triples"]]
        predictions.append({
            "pmid": doc["pmid"], "text": doc["text"],
            "gold_triples": gold, "predicted_triples": result["triples"],
            "error": result["error"],
        })
        call_log.append({
            "pmid": doc["pmid"], "cost_usd": cost, "latency_s": result["latency_s"],
            "http_status": result["http_status"], "error": result["error"],
            "n_triples": len(result["triples"]), "n_gold": len(gold),
        })

        for t in result["triples"]:
            all_pred_triples.append(Triple(t["subject"], t["predicate"], t["object"]))
        for s, p, o in gold:
            all_gold_triples.append(Triple(s, p, o))

        print(f"  {doc['pmid']}: {len(result['triples'])} pred / {len(gold)} gold, "
              f"${cost:.6f}, error={result['error']}")

    metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples)

    with open(OUTPUT_DIR / "predictions.json", "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)
    with open(OUTPUT_DIR / "call_log.json", "w", encoding="utf-8") as f:
        json.dump(call_log, f, indent=2)
    with open(OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "model": MODEL, "n_docs": N_DOCS, "split": "Dev",
            "total_cost_usd": total_cost, "n_errors": len([c for c in call_log if c["error"]]),
            **metrics,
        }, f, indent=2)

    print(f"\nP={metrics['precision']:.4f} R={metrics['recall']:.4f} F1={metrics['f1']:.4f}")
    print(f"TP={metrics['true_positives']} FP={metrics['false_positives']} FN={metrics['false_negatives']}")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
