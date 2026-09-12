"""DEC-003 full instrumented product-domain Prob-KB run.

Design (documented here since it makes methodological choices beyond what
any single notebook cell specifies):

- Train-split products (from data/product_split.csv) go through the
  original SLDE-AFT Full 4-iteration loop (see
  SLDE_AFT_DualSource_Final_(20).ipynb cell 24), but the deterministic
  LockedKnowledgeStore is replaced with the instrumented
  CandidateBufferAdapter (src/probkb_v2_adapter.py) so every observation
  and per-iteration snapshot is logged, per DEC-003 / EVID-007's request.
- Structured facts seed the KB at iteration 1 only (not re-observed every
  iteration). Unlike the original LockedKnowledgeStore's max-merge (where
  re-observing an identical 0.98 confidence is a no-op), the Prob-KB's
  Noisy-Or aggregation would treat repeated identical structured
  observations as new evidence and inflate support artificially. Iteration
  1 seeding is judged the more defensible choice for this KB variant.
- Val + test-split products get exactly one unstructured-only extraction
  pass, guided by the *train* KB's locked context and feedback hint only
  (never by their own structured facts), per slde_aft_next_steps.md item 2
  and 3 (leakage-safe held-out evaluation, cumulative-PKB vs unstructured
  quality kept separate).

Usage: python -m scripts.dec003_product_probkb_run
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from src.datasets.product_generator import ALLOWED_PREDICATES, generate_products
from src.extractors.structured import extract_structured
from src.extractors.openrouter_llm import extract_unstructured_llm
from src.feedback_builder import build_feedback_hint
from src.pkb_instrumentation import normalized_object, normalized_slot
from src.probkb_v2_adapter import CandidateBufferAdapter

MODEL = "meta-llama/llama-3.1-8b-instruct"
EXPERIMENT_ID = "DEC003_PRODUCT_V2"
N_PRODUCTS = 50
GENERATION_SEED = 42
THRESHOLD = 0.88
SHRINKAGE = 0.75
FUNCTIONAL_PREDICATES_PATH = "configs/functional_predicates_product_domain.json"
SPLIT_PATH = Path("data/product_split.csv")
OUTPUT_ROOT = Path("outputs/dec003_product_probkb_v2")


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def load_split() -> dict[int, str]:
    split = {}
    with open(SPLIT_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]
    return split


def normalize_gold(gold_list) -> set[tuple[str, str, str]]:
    keys = set()
    for s, p, o, _ in gold_list:
        s_norm, p_norm = normalized_slot(s, p)
        keys.add((s_norm, p_norm, normalized_object(o)))
    return keys


def normalize_llm_triples(triples) -> set[tuple[str, str, str]]:
    keys = set()
    for t in triples:
        s_norm, p_norm = normalized_slot(t["subject"], t["predicate"])
        keys.add((s_norm, p_norm, normalized_object(t["object"])))
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
        products[idx] = (structured_row, unstructured_row, gold_structured, gold_unstructured)

    train_idx = sorted(i for i, s in split.items() if s == "train")
    val_idx = sorted(i for i, s in split.items() if s == "val")
    test_idx = sorted(i for i, s in split.items() if s == "test")

    train_gold_keys = set()
    for idx in train_idx:
        train_gold_keys |= normalize_gold(products[idx][3])

    all_gold_keys = set()
    for idx in products:
        all_gold_keys |= normalize_gold(products[idx][3])

    total_cost = 0.0
    total_calls = 0
    call_log = []

    def do_llm_call(idx, text, locked_context, feedback_hint):
        nonlocal total_cost, total_calls
        result = extract_unstructured_llm(
            doc_text=text, source_id=f"product_{idx}", api_key=api_key,
            model=MODEL, locked_context=locked_context, feedback_hint=feedback_hint,
        )
        cost = result.get("cost_usd") or 0.0
        total_cost += cost
        total_calls += 1
        call_log.append({
            "product_idx": idx, "cost_usd": cost, "latency_s": result["latency_s"],
            "http_status": result["http_status"], "error": result["error"],
            "n_triples": len(result["triples"]),
        })
        print(f"  [{total_calls}] product_{idx}: {len(result['triples'])} triples, "
              f"${cost:.8f}, {result['latency_s']:.1f}s, error={result['error']}")
        return result

    # ---- Train KB build: 4 iterations over train-split products ----
    train_out = OUTPUT_ROOT / "train_kb"
    adapter_train = CandidateBufferAdapter(
        experiment_id=EXPERIMENT_ID, run_id="train_kb",
        prob_kb_version="conservative_noisy_or_conflict_adjusted",
        functional_predicates_path=FUNCTIONAL_PREDICATES_PATH,
        output_dir=str(train_out), threshold=THRESHOLD,
        gold_keys=train_gold_keys, shrinkage=SHRINKAGE,
    )

    iteration_metrics = []

    print(f"\n=== Iteration 1: structured seed + unguided LLM ({len(train_idx)} train products) ===")
    iter1_llm_keys = set()
    t0 = time.perf_counter()
    for idx in train_idx:
        structured_row, unstructured_row, _, _ = products[idx]
        for triple in extract_structured(structured_row, source_id=f"product_{idx}"):
            adapter_train.accept_candidate(
                subject=triple["subject"], predicate=triple["predicate"],
                object_value=triple["object"], confidence=triple["confidence"],
                source_id=triple["source_id"], source_type=triple["source_type"],
                provenance=triple["provenance"],
            )
        result = do_llm_call(idx, unstructured_row["text"], locked_context=None, feedback_hint=None)
        for triple in result["triples"]:
            adapter_train.accept_candidate(
                subject=triple["subject"], predicate=triple["predicate"],
                object_value=triple["object"], confidence=triple["confidence"],
                source_id=triple["source_id"], source_type=triple["source_type"],
                provenance=triple["provenance"],
            )
        iter1_llm_keys |= normalize_llm_triples(result["triples"])

    metrics = prf(iter1_llm_keys, train_gold_keys)
    metrics.update({"iteration": 1, "runtime_s": time.perf_counter() - t0,
                     "kb_size": len(adapter_train.accepted)})
    iteration_metrics.append(metrics)
    adapter_train.end_iteration(1)
    print(f"  Iter 1 LLM-only eval: P={metrics['precision']:.4f} R={metrics['recall']:.4f} F1={metrics['f1']:.4f}")

    for it in range(2, 5):
        print(f"\n=== Iteration {it}: locked-context + feedback-guided LLM ===")
        locked_context = adapter_train.get_locked_context_strings(n=12)
        feedback_hint = build_feedback_hint(
            adapter_train.as_key_set(), train_gold_keys, ALLOWED_PREDICATES,
        )
        iter_llm_keys = set()
        t0 = time.perf_counter()
        for idx in train_idx:
            _, unstructured_row, _, _ = products[idx]
            result = do_llm_call(idx, unstructured_row["text"], locked_context, feedback_hint)
            for triple in result["triples"]:
                adapter_train.accept_candidate(
                    subject=triple["subject"], predicate=triple["predicate"],
                    object_value=triple["object"], confidence=triple["confidence"],
                    source_id=triple["source_id"], source_type=triple["source_type"],
                    provenance=triple["provenance"],
                )
            iter_llm_keys |= normalize_llm_triples(result["triples"])

        metrics = prf(iter_llm_keys, train_gold_keys)
        metrics.update({"iteration": it, "runtime_s": time.perf_counter() - t0,
                         "kb_size": len(adapter_train.accepted)})
        iteration_metrics.append(metrics)
        adapter_train.end_iteration(it)
        print(f"  Iter {it} LLM-only eval: P={metrics['precision']:.4f} R={metrics['recall']:.4f} F1={metrics['f1']:.4f}")

    train_out.mkdir(parents=True, exist_ok=True)
    with open(train_out / "iteration_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(iteration_metrics[0].keys()))
        writer.writeheader()
        writer.writerows(iteration_metrics)

    # ---- Held-out evaluation: val + test, single pass, train-KB guidance only ----
    print(f"\n=== Held-out pass: {len(val_idx)} val + {len(test_idx)} test products ===")
    held_out_out = OUTPUT_ROOT / "held_out_eval"
    final_locked_context = adapter_train.get_locked_context_strings(n=12)
    final_feedback_hint = build_feedback_hint(
        adapter_train.as_key_set(), train_gold_keys, ALLOWED_PREDICATES,
    )

    held_out_gold_keys = set()
    for idx in val_idx + test_idx:
        held_out_gold_keys |= normalize_gold(products[idx][3])

    adapter_eval = CandidateBufferAdapter(
        experiment_id=EXPERIMENT_ID, run_id="held_out_eval",
        prob_kb_version="conservative_noisy_or_conflict_adjusted",
        functional_predicates_path=FUNCTIONAL_PREDICATES_PATH,
        output_dir=str(held_out_out), threshold=THRESHOLD,
        gold_keys=held_out_gold_keys, shrinkage=SHRINKAGE,
    )

    val_pred_keys, test_pred_keys = set(), set()
    for idx in val_idx + test_idx:
        _, unstructured_row, _, _ = products[idx]
        result = do_llm_call(idx, unstructured_row["text"], final_locked_context, final_feedback_hint)
        for triple in result["triples"]:
            adapter_eval.accept_candidate(
                subject=triple["subject"], predicate=triple["predicate"],
                object_value=triple["object"], confidence=triple["confidence"],
                source_id=triple["source_id"], source_type=triple["source_type"],
                provenance=triple["provenance"],
            )
        keys = normalize_llm_triples(result["triples"])
        if idx in val_idx:
            val_pred_keys |= keys
        else:
            test_pred_keys |= keys

    adapter_eval.end_iteration(1)

    val_gold_keys = set()
    for idx in val_idx:
        val_gold_keys |= normalize_gold(products[idx][3])
    test_gold_keys = set()
    for idx in test_idx:
        test_gold_keys |= normalize_gold(products[idx][3])

    held_out_metrics = [
        {"split": "val", **prf(val_pred_keys, val_gold_keys)},
        {"split": "test", **prf(test_pred_keys, test_gold_keys)},
    ]
    held_out_out.mkdir(parents=True, exist_ok=True)
    with open(held_out_out / "held_out_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(held_out_metrics[0].keys()))
        writer.writeheader()
        writer.writerows(held_out_metrics)

    for row in held_out_metrics:
        print(f"  {row['split']}: P={row['precision']:.4f} R={row['recall']:.4f} F1={row['f1']:.4f} "
              f"(TP={row['true_positives']} FP={row['false_positives']} FN={row['false_negatives']})")

    # ---- Config / run manifest ----
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    config = {
        "experiment_id": EXPERIMENT_ID,
        "model": MODEL,
        "provider": "OpenRouter",
        "temperature": 0.0,
        "generation_seed": GENERATION_SEED,
        "split_seed": 7,
        "n_train": len(train_idx), "n_val": len(val_idx), "n_test": len(test_idx),
        "threshold": THRESHOLD, "shrinkage": SHRINKAGE,
        "functional_predicates_path": FUNCTIONAL_PREDICATES_PATH,
        "total_api_calls": total_calls,
        "total_cost_usd": total_cost,
    }
    with open(OUTPUT_ROOT / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    with open(OUTPUT_ROOT / "call_log.json", "w", encoding="utf-8") as f:
        json.dump(call_log, f, indent=2)

    print(f"\nTOTAL: {total_calls} API calls, ${total_cost:.6f}")
    print(f"Saved to {OUTPUT_ROOT}/")


if __name__ == "__main__":
    main()
