"""DEC-019 closed-loop test — CONTROL arm.

Tests claim #1 (does closing the loop with a fine-tuned model actually
improve the system): reconstructs the exact iteration-4 KB state from
the DEC-006 200-product scale-up run (EVID-027/028's source data, via
src/pkb_replay.py -- verified to exactly reproduce the original
475-triple above-threshold snapshot), then runs ONE more iteration
(iteration 5) over the same 140 train products using the SAME
un-fine-tuned base API model as iterations 1-4.

Uses the plain src/prompts.py prompt format (no locked-context/
feedback-hint) rather than the usual iterative-loop prompt
(src/extractors/openrouter_llm.py's build_prompt with locked context),
specifically so this is a fair, apples-to-apples comparison against the
TREATMENT arm (scripts/dec019_closedloop_treatment_extract.py), which
runs a fine-tuned model that was only ever trained on the plain format
-- giving it the locked-context/feedback-hint format it never saw
would reproduce EVID-026's train/eval format-mismatch bug. DEC-005
already found locked-context/feedback has no significant effect
anyway, so dropping it here isolates the fine-tuning question cleanly
without meaningfully changing what's being tested.

This is the CONTROL: "what would iteration 5 look like if we just kept
using the un-fine-tuned model?" Compare against
scripts/dec019_closedloop_treatment_merge.py's result.

Usage (real API calls, ~140 calls, ~$0.003 based on prior runs):
    python scripts/dec019_closedloop_control.py
"""

from __future__ import annotations

import json
from pathlib import Path

from src.datasets.product_generator import ALLOWED_PREDICATES, generate_products
from src.extractors.openrouter_llm import extract_unstructured_llm
from src.pkb_instrumentation import normalized_object, normalized_slot
from src.pkb_replay import build_replayed_adapter
from src.prompts import build_extraction_prompt

MODEL = "meta-llama/llama-3.1-8b-instruct"
SCALEUP_ROOT = "outputs/dec006_scaleup_probkb"
SPLIT_PATH = "data/product_split_200.csv"
N_PRODUCTS = 200
GENERATION_SEED = 42
FUNCTIONAL_PREDICATES_PATH = "configs/functional_predicates_product_domain.json"
OUTPUT_DIR = "outputs/dec019_closedloop/control"


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def load_split() -> dict[int, str]:
    import csv
    split = {}
    with open(SPLIT_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]
    return split


def normalize_gold(gold_list) -> set[tuple[str, str, str]]:
    keys = set()
    for s, p, o, _ in gold_list:
        sn, pn = normalized_slot(s, p)
        keys.add((sn, pn, normalized_object(o)))
    return keys


def normalize_triples(triples) -> set[tuple[str, str, str]]:
    keys = set()
    for t in triples:
        sn, pn = normalized_slot(t["subject"], t["predicate"])
        keys.add((sn, pn, normalized_object(t["object"])))
    return keys


def prf(pred_keys: set, gold_keys: set) -> dict:
    tp = len(pred_keys & gold_keys)
    fp = len(pred_keys - gold_keys)
    fn = len(gold_keys - pred_keys)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1,
            "true_positives": tp, "false_positives": fp, "false_negatives": fn}


def main():
    api_key = load_api_key()
    split = load_split()

    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        N_PRODUCTS, seed=GENERATION_SEED
    ):
        products[idx] = (unstructured_row, gold_structured)

    train_idx = sorted(i for i, s in split.items() if s == "train")
    train_gold_keys = set()
    for idx in train_idx:
        train_gold_keys |= normalize_gold(products[idx][1])

    adapter = build_replayed_adapter(
        observations_dir=f"{SCALEUP_ROOT}/train_kb",
        iterations=[1, 2, 3, 4],
        experiment_id="DEC019_CLOSEDLOOP", run_id="control",
        functional_predicates_path=FUNCTIONAL_PREDICATES_PATH,
        output_dir=OUTPUT_DIR, threshold=0.88, shrinkage=0.75,
        gold_keys=train_gold_keys,
    )
    print(f"Replayed iterations 1-4: {len(adapter.accepted)} accepted keys, "
          f"{sum(1 for e in adapter.accepted.values() if e['confidence'] > 0.88)} above threshold")

    total_cost, total_calls = 0.0, 0
    call_log = []
    iter5_pred_keys = set()

    for idx in train_idx:
        unstructured_row, _ = products[idx]
        text = unstructured_row["text"][:700]
        prompt = build_extraction_prompt(text, ALLOWED_PREDICATES)
        result = extract_unstructured_llm(
            doc_text=text, source_id=f"product_{idx}", api_key=api_key, model=MODEL,
            prompt_override=prompt,
        )
        cost = result.get("cost_usd") or 0.0
        total_cost += cost
        total_calls += 1
        call_log.append({"product_idx": idx, "cost_usd": cost, "n_triples": len(result["triples"]),
                          "error": result["error"]})
        print(f"  [{total_calls}] product_{idx}: {len(result['triples'])} triples, error={result['error']}")

        for triple in result["triples"]:
            adapter.accept_candidate(
                subject=triple["subject"], predicate=triple["predicate"],
                object_value=triple["object"], confidence=triple["confidence"],
                source_id=triple["source_id"], source_type=triple["source_type"],
                provenance=triple["provenance"],
            )
        iter5_pred_keys |= normalize_triples(result["triples"])

    adapter.end_iteration(5)

    iter5_metrics = prf(iter5_pred_keys, train_gold_keys)
    above_threshold_keys = set(
        (e["subject"], e["predicate"], str(e["object"]))
        for e in adapter.accepted.values() if e["confidence"] > 0.88
    )
    above_threshold_norm_keys = normalize_triples(
        [{"subject": s, "predicate": p, "object": o} for s, p, o in above_threshold_keys]
    )
    kb_metrics = prf(above_threshold_norm_keys, train_gold_keys)

    out = Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    summary = {
        "arm": "control", "model": MODEL, "total_calls": total_calls, "total_cost_usd": total_cost,
        "iteration5_extraction_only": iter5_metrics,
        "accumulated_kb_after_iteration5": kb_metrics,
        "accumulated_kb_size": len(above_threshold_norm_keys),
    }
    with open(out / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    with open(out / "call_log.json", "w", encoding="utf-8") as f:
        json.dump(call_log, f, indent=2)

    print(f"\nIteration 5 (this pass only): P={iter5_metrics['precision']:.4f} R={iter5_metrics['recall']:.4f} F1={iter5_metrics['f1']:.4f}")
    print(f"Accumulated KB after iteration 5: P={kb_metrics['precision']:.4f} R={kb_metrics['recall']:.4f} F1={kb_metrics['f1']:.4f} (n={len(above_threshold_norm_keys)})")
    print(f"Total: {total_calls} calls, ${total_cost:.6f}")
    print(f"Saved to {out}/")


if __name__ == "__main__":
    main()
