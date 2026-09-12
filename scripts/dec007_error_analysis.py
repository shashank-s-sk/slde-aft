"""DEC-007 systematic error analysis. Zero API cost — pure analysis of
predictions/snapshots already saved by earlier runs.

Two sources, each categorized per DEC-007's required labels (correct
extraction / failed extraction (false negative) / hallucinated triple
(false positive) / conflicting triple / ambiguous relation):

  A) CaRB-30 comparison (DEC-001/002, EVID-021): both systems
     (slde_aft_llama, deepseek_baseline). Simple TP/FP/FN categorization
     via the same normalized matching used for their reported F1.

  B) DEC-003's real product-domain PKB run (EVID-013), final iteration
     4 snapshot: has confidence, competitor_count, functional_predicate,
     and gold_label already computed, so conflicting-triple and
     ambiguous-relation categories can be derived directly. False
     negatives (gold facts never observed at all) are computed by
     regenerating the same train-split gold set the run used.

Usage: python -m scripts.dec007_error_analysis
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from src.evaluator import Triple, normalize_triple
from src.experiment_runner import load_products, load_split, normalize_gold
from src.pkb_instrumentation import normalized_object, normalized_slot

OUTPUT_DIR = Path("outputs/dec007_error_analysis")
AMBIGUOUS_BAND = 0.03  # +/- around threshold counts as "ambiguous"


def analyze_carb():
    rows = []
    for system in ["slde_aft_llama", "deepseek_baseline"]:
        pred_path = Path(f"outputs/dec001_002_carb30/{system}/predictions.json")
        records = json.loads(pred_path.read_text(encoding="utf-8"))

        for rec in records:
            gold_set = {normalize_triple(Triple(t["subject"], t["predicate"], t["object"]))
                        for t in rec["gold_triples"]}
            pred_set = {normalize_triple(Triple(t["subject"], t["predicate"], t["object"]))
                        for t in rec["predicted_triples"]}

            for t in pred_set:
                category = "correct_extraction" if t in gold_set else "hallucinated_triple"
                rows.append({
                    "source": "carb30", "system": system, "sentence_id": rec["sentence_id"],
                    "text": rec["sentence"], "subject": t.subject, "predicate": t.predicate,
                    "object": t.object, "category": category, "is_conflicting": None,
                    "is_ambiguous": None, "confidence": None,
                    "competitor_count": None, "provenance": rec["sentence"],
                })
            for t in gold_set - pred_set:
                rows.append({
                    "source": "carb30", "system": system, "sentence_id": rec["sentence_id"],
                    "text": rec["sentence"], "subject": t.subject, "predicate": t.predicate,
                    "object": t.object, "category": "failed_extraction", "is_conflicting": None,
                    "is_ambiguous": None, "confidence": None,
                    "competitor_count": None, "provenance": rec["sentence"],
                })
    return rows


def analyze_product_domain():
    snapshot_path = Path("outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv")
    snapshot_rows = list(csv.DictReader(open(snapshot_path, encoding="utf-8")))

    threshold = float(snapshot_rows[0]["threshold"]) if snapshot_rows else 0.88

    accepted_keys = set()
    rows = []
    for r in snapshot_rows:
        key = (r["subject"].strip().lower(), r["predicate"].strip().lower(), r["object"].strip().lower())
        accepted_keys.add(key)

        confidence = float(r["conflict_adjusted_final_confidence"])
        gold_label = r["gold_label"]
        above = r["above_threshold"] == "True"
        competitor_count = int(r["competitor_count"])

        if gold_label == "1":
            category = "correct_extraction" if above else "correct_but_below_threshold"
        else:
            category = "hallucinated_triple" if above else "hallucinated_but_filtered"

        # Conflicting/ambiguous are independent flags, not a replacement for
        # the correct/hallucinated outcome — a conflicting triple can be
        # either gold-correct or a hallucination, and collapsing that
        # distinction away would hide which one it is.
        is_conflicting = competitor_count > 0
        is_ambiguous = abs(confidence - threshold) <= AMBIGUOUS_BAND

        rows.append({
            "source": "product_domain", "system": "slde_aft_prob_kb", "sentence_id": r["subject"],
            "text": None, "subject": r["subject"], "predicate": r["predicate"], "object": r["object"],
            "category": category, "is_conflicting": is_conflicting, "is_ambiguous": is_ambiguous,
            "confidence": round(confidence, 4),
            "competitor_count": competitor_count, "provenance": r["provenance"][:200],
        })

    # False negatives: train-split gold facts never observed at all.
    split = load_split("data/product_split.csv")
    products = load_products(50, generation_seed=42)
    train_idx = sorted(i for i in products if split.get(i) == "train")

    for idx in train_idx:
        _, _, _, gold_unstructured = products[idx]
        for s, p, o, _ in gold_unstructured:
            s_norm, p_norm = normalized_slot(s, p)
            key = (s_norm, p_norm, normalized_object(o))
            if key not in accepted_keys:
                rows.append({
                    "source": "product_domain", "system": "slde_aft_prob_kb",
                    "sentence_id": s, "text": None, "subject": s, "predicate": p, "object": o,
                    "category": "failed_extraction", "is_conflicting": None, "is_ambiguous": None,
                    "confidence": None, "competitor_count": None, "provenance": None,
                })

    return rows


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    carb_rows = analyze_carb()
    product_rows = analyze_product_domain()
    all_rows = carb_rows + product_rows

    with open(OUTPUT_DIR / "error_analysis_full.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)

    from collections import Counter
    print("=== CaRB-30 category counts (by system) ===")
    for system in ["slde_aft_llama", "deepseek_baseline"]:
        counts = Counter(r["category"] for r in carb_rows if r["system"] == system)
        print(f"  {system}: {dict(counts)}")

    print("\n=== Product-domain category counts ===")
    counts = Counter(r["category"] for r in product_rows)
    print(f"  {dict(counts)}")

    # Save 2 representative examples per category per source for manual review.
    examples = {}
    for r in all_rows:
        k = (r["source"], r["system"], r["category"])
        examples.setdefault(k, []).append(r)

    curated = []
    for k, rows in examples.items():
        curated.extend(rows[:2])

    with open(OUTPUT_DIR / "curated_examples.json", "w", encoding="utf-8") as f:
        json.dump(curated, f, indent=2)

    print(f"\nTotal rows: {len(all_rows)}")
    print(f"Curated examples (2 per source/system/category): {len(curated)}")
    print(f"Saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
