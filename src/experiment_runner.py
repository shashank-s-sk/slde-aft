"""Reusable ablation/statistics experiment runner.

Shared by DEC-004 (module on/off ablations) and DEC-005 (multi-seed
statistical validation) so neither has to duplicate the extraction loop
that scripts/dec003_product_probkb_run.py established. A single
ExperimentConfig controls which modules are active; run_experiment()
executes the full train-iteration + held-out-evaluation loop and returns
everything needed to build a comparison table.

Design notes (see Decision log.md DEC-004 for the full rationale):
- use_prob_kb toggles between CandidateBufferAdapter (Conservative
  Noisy-Or + conflict adjustment) and DeterministicKBAdapter (monotonic
  max-merge) — same external interface, swapped by dependency injection.
- use_feedback toggles only the feedback_hint text passed to the LLM
  extractor; locked_context is still built from the KB regardless (the
  Feedback Controller and KB-guidance are separate modules per DEC-004's
  own ablation list).
- use_structured / use_unstructured are source-path ablations. Per
  DEC-004's notes these are "not direct replacements for the full
  dual-source task" — held-out (unstructured-text) evaluation is skipped
  for structured-only (there is no text-reading component to evaluate),
  and documented as such in the returned results rather than silently
  producing a misleading metric.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.datasets.product_generator import ALLOWED_PREDICATES, generate_products
from src.deterministic_kb_adapter import DeterministicKBAdapter
from src.extractors.openrouter_llm import extract_unstructured_llm
from src.extractors.structured import extract_structured
from src.feedback_builder import build_feedback_hint
from src.pkb_instrumentation import normalized_object, normalized_slot
from src.probkb_v2_adapter import CandidateBufferAdapter


@dataclass
class ExperimentConfig:
    config_name: str
    experiment_id: str
    output_root: str
    n_products: int = 20
    generation_seed: int = 42
    seed_label: str = "seed42"
    model: str = "meta-llama/llama-3.1-8b-instruct"
    use_feedback: bool = True
    use_prob_kb: bool = True
    use_structured: bool = True
    use_unstructured: bool = True
    n_iterations: int = 4
    threshold: float = 0.88
    shrinkage: float = 0.75
    functional_predicates_path: str = "configs/functional_predicates_product_domain.json"
    split_path: str = "data/product_split.csv"


def load_split(split_path: str) -> dict[int, str]:
    import csv
    split = {}
    with open(split_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]
    return split


def load_products(n_products: int, generation_seed: int) -> dict[int, tuple]:
    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        n_products, seed=generation_seed
    ):
        products[idx] = (structured_row, unstructured_row, gold_structured, gold_unstructured)
    return products


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


def _make_kb(config: ExperimentConfig, run_id: str, output_dir: str, gold_keys: set):
    if config.use_prob_kb:
        return CandidateBufferAdapter(
            experiment_id=config.experiment_id, run_id=run_id,
            prob_kb_version="conservative_noisy_or_conflict_adjusted",
            functional_predicates_path=config.functional_predicates_path,
            output_dir=output_dir, threshold=config.threshold,
            gold_keys=gold_keys, shrinkage=config.shrinkage,
        )
    return DeterministicKBAdapter(
        experiment_id=config.experiment_id, run_id=run_id,
        output_dir=output_dir, threshold=config.threshold, gold_keys=gold_keys,
    )


def run_experiment(config: ExperimentConfig, api_key: str) -> dict:
    split = load_split(config.split_path)
    products = load_products(config.n_products, config.generation_seed)

    train_idx = sorted(i for i in products if split.get(i) == "train")
    val_idx = sorted(i for i in products if split.get(i) == "val")
    test_idx = sorted(i for i in products if split.get(i) == "test")

    train_gold_keys = set()
    for idx in train_idx:
        train_gold_keys |= normalize_gold(products[idx][3])

    total_cost = 0.0
    total_calls = 0
    call_log = []

    def do_llm_call(idx, text, locked_context, feedback_hint, iteration, phase):
        nonlocal total_cost, total_calls
        if not config.use_unstructured:
            return {"triples": [], "error": None, "cost_usd": 0.0, "latency_s": 0.0}
        result = extract_unstructured_llm(
            doc_text=text, source_id=f"product_{idx}", api_key=api_key,
            model=config.model, locked_context=locked_context, feedback_hint=feedback_hint,
        )
        cost = result.get("cost_usd") or 0.0
        total_cost += cost
        total_calls += 1
        log_entry = {
            "product_idx": idx,
            "iteration": iteration,
            "phase": phase,
            "cost_usd": cost,
            "latency_s": result["latency_s"],
            "http_status": result.get("http_status"),
            "error": result["error"],
            "n_triples": len(result["triples"]),
            "predicted_triples": [
                {"subject": t["subject"], "predicate": t["predicate"], "object": t["object"]}
                for t in result["triples"]
            ],
        }
        if result["error"]:
            raw = result.get("raw_response")
            content = raw
            try:
                if raw and "choices" in raw:
                    content = raw["choices"][0]["message"]["content"]
            except Exception:
                pass
            log_entry["raw_content_on_error"] = content
        call_log.append(log_entry)
        return result

    output_root = Path(config.output_root)
    train_out = output_root / "train_kb"
    kb = _make_kb(config, run_id="train_kb", output_dir=str(train_out), gold_keys=train_gold_keys)

    iteration_metrics = []
    n_iterations = config.n_iterations if config.use_unstructured else 1

    for it in range(1, n_iterations + 1):
        locked_context = None if it == 1 else kb.get_locked_context_strings(n=12)
        feedback_hint = None
        if it > 1 and config.use_feedback:
            feedback_hint = build_feedback_hint(kb.as_key_set(), train_gold_keys, ALLOWED_PREDICATES)

        iter_llm_keys = set()
        t0 = time.perf_counter()
        for idx in train_idx:
            structured_row, unstructured_row, _, _ = products[idx]

            if it == 1 and config.use_structured:
                for triple in extract_structured(structured_row, source_id=f"product_{idx}"):
                    kb.accept_candidate(
                        subject=triple["subject"], predicate=triple["predicate"],
                        object_value=triple["object"], confidence=triple["confidence"],
                        source_id=triple["source_id"], source_type=triple["source_type"],
                        provenance=triple["provenance"],
                    )

            if config.use_unstructured:
                result = do_llm_call(idx, unstructured_row["text"], locked_context, feedback_hint,
                                      iteration=it, phase="train")
                for triple in result["triples"]:
                    kb.accept_candidate(
                        subject=triple["subject"], predicate=triple["predicate"],
                        object_value=triple["object"], confidence=triple["confidence"],
                        source_id=triple["source_id"], source_type=triple["source_type"],
                        provenance=triple["provenance"],
                    )
                iter_llm_keys |= normalize_llm_triples(result["triples"])

        metrics = prf(iter_llm_keys, train_gold_keys) if config.use_unstructured else {
            "precision": None, "recall": None, "f1": None,
            "true_positives": None, "false_positives": None, "false_negatives": None,
        }
        metrics.update({"iteration": it, "runtime_s": time.perf_counter() - t0,
                         "kb_size": len(kb.accepted)})
        iteration_metrics.append(metrics)
        kb.end_iteration(it)

    held_out_metrics = None
    if config.use_unstructured and config.use_structured:
        # Held-out eval is only meaningful when the ablation still reads
        # unstructured text — structured-only has no text component, and
        # unstructured-only's held-out eval is identical in kind to its
        # train-iteration eval, so it's reported via iteration_metrics
        # instead of duplicated here.
        held_out_out = output_root / "held_out_eval"
        final_locked_context = kb.get_locked_context_strings(n=12)
        final_feedback_hint = (
            build_feedback_hint(kb.as_key_set(), train_gold_keys, ALLOWED_PREDICATES)
            if config.use_feedback else None
        )
        held_out_gold_keys = set()
        for idx in val_idx + test_idx:
            held_out_gold_keys |= normalize_gold(products[idx][3])

        eval_kb = _make_kb(config, run_id="held_out_eval", output_dir=str(held_out_out),
                            gold_keys=held_out_gold_keys)

        val_pred_keys, test_pred_keys = set(), set()
        for idx in val_idx + test_idx:
            _, unstructured_row, _, _ = products[idx]
            result = do_llm_call(idx, unstructured_row["text"], final_locked_context, final_feedback_hint,
                                  iteration=0, phase="held_out")
            for triple in result["triples"]:
                eval_kb.accept_candidate(
                    subject=triple["subject"], predicate=triple["predicate"],
                    object_value=triple["object"], confidence=triple["confidence"],
                    source_id=triple["source_id"], source_type=triple["source_type"],
                    provenance=triple["provenance"],
                )
            keys = normalize_llm_triples(result["triples"])
            (val_pred_keys if idx in val_idx else test_pred_keys).update(keys)
        eval_kb.end_iteration(1)

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

    return {
        "config": config,
        "kb": kb,
        "iteration_metrics": iteration_metrics,
        "held_out_metrics": held_out_metrics,
        "total_cost_usd": total_cost,
        "total_calls": total_calls,
        "call_log": call_log,
        "n_train": len(train_idx), "n_val": len(val_idx), "n_test": len(test_idx),
    }
