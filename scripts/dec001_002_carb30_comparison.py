"""DEC-001 (scale CaRB pilot from 10 to 30 sentences) + DEC-002 (add a
stronger external baseline, DeepSeek) in one run, since both use the
identical protocol and can be directly compared fairly.

Two systems, same 30 sentences, same prompt (prompts/openie_carb_v1.txt),
same evaluator:
  - "slde_aft_llama": SLDE-AFT's own extractor pinned to
    meta-llama/llama-3.1-8b-instruct (EVID-002/003 used openrouter/auto,
    which DEC-005's own fairness rules say not to do for a reported
    result — fixed here to a pinned model instead).
  - "deepseek_baseline": deepseek/deepseek-v3.2, the stronger external
    SOTA baseline the professor asked for (DEC-002).

Usage: python -m scripts.dec001_002_carb30_comparison
"""

from __future__ import annotations

import json
import csv
from pathlib import Path

from src.extractors.openrouter_openie import extract_openie_triples
from src.evaluator import Triple, compute_precision_recall_f1

DATA_PATH = Path("data/carb_dev_sample.jsonl")
OUTPUT_ROOT = Path("outputs/dec001_002_carb30")

SYSTEMS = {
    "slde_aft_llama": "meta-llama/llama-3.1-8b-instruct",
    "deepseek_baseline": "deepseek/deepseek-v3.2",
}


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def load_sentences():
    records = []
    with open(DATA_PATH, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def main():
    api_key = load_api_key()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    sentences = load_sentences()
    print(f"Loaded {len(sentences)} CaRB sentences")

    summary_rows = []

    for system_name, model in SYSTEMS.items():
        print(f"\n=== {system_name} ({model}) ===")
        sys_dir = OUTPUT_ROOT / system_name
        sys_dir.mkdir(parents=True, exist_ok=True)

        predictions = []
        call_log = []
        all_pred_triples = []
        all_gold_triples = []
        total_cost = 0.0

        for rec in sentences:
            result = extract_openie_triples(rec["sentence"], api_key=api_key, model=model)
            cost = result.get("cost_usd") or 0.0
            total_cost += cost

            predictions.append({
                "sentence_id": rec["sentence_id"], "sentence": rec["sentence"],
                "gold_triples": rec["gold_triples"], "predicted_triples": result["triples"],
                "error": result["error"],
            })
            call_log.append({
                "sentence_id": rec["sentence_id"], "cost_usd": cost,
                "latency_s": result["latency_s"], "http_status": result["http_status"],
                "error": result["error"], "n_triples": len(result["triples"]),
            })

            for t in result["triples"]:
                all_pred_triples.append(Triple(t["subject"], t["predicate"], t["object"]))
            for t in rec["gold_triples"]:
                all_gold_triples.append(Triple(t["subject"], t["predicate"], t["object"]))

            print(f"  {rec['sentence_id']}: {len(result['triples'])} triples, "
                  f"${cost:.6f}, error={result['error']}")

        metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples)

        with open(sys_dir / "predictions.json", "w", encoding="utf-8") as f:
            json.dump(predictions, f, indent=2)
        with open(sys_dir / "call_log.json", "w", encoding="utf-8") as f:
            json.dump(call_log, f, indent=2)
        with open(sys_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump({
                "system": system_name, "model": model, "n_sentences": len(sentences),
                "total_cost_usd": total_cost, "n_errors": len([c for c in call_log if c["error"]]),
                **metrics,
            }, f, indent=2)

        print(f"  {system_name}: P={metrics['precision']:.4f} R={metrics['recall']:.4f} "
              f"F1={metrics['f1']:.4f} | cost=${total_cost:.6f}")

        summary_rows.append({
            "system": system_name, "model": model,
            "precision": metrics["precision"], "recall": metrics["recall"], "f1": metrics["f1"],
            "true_positives": metrics["true_positives"], "false_positives": metrics["false_positives"],
            "false_negatives": metrics["false_negatives"], "n_errors": len([c for c in call_log if c["error"]]),
            "cost_usd": total_cost,
        })

    with open(OUTPUT_ROOT / "comparison_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nSaved comparison to {OUTPUT_ROOT}/comparison_summary.csv")


if __name__ == "__main__":
    main()
