"""DEC-006 local-adapter evaluation — run on the same rented GPU
alongside dec006_lora_finetune.py, NOT locally. Loads a base model
(optionally with a LoRA adapter), runs local inference on the held-out
test split (data/product_split.csv, respecting the same leakage-safe
boundaries as every other experiment in this project), and evaluates
with the exact same normalized-triple protocol used everywhere else
(src/evaluator.py) so results are directly comparable to the API-based
runs (EVID-013 etc).

Cross-split leakage guard: the fine-tuning training data
(outputs/dec006_synthetic_data/product_domain_synth_train.jsonl) may
have been built from a DIFFERENT, independently-shuffled product split
than this script's evaluation split (e.g. EVID-027's 200-product
scale-up split vs. this script's default 50-product split) -- found in
practice to overlap: 2 of 10 original test products were also used to
build EVID-027's fine-tuning examples, real train/test leakage. This
script now reads that training file and automatically excludes any
would-be test product whose name was actually used in training,
printing exactly what got excluded and why, rather than silently
evaluating on a partially-contaminated set.

Usage:
    python scripts/dec006_evaluate_adapter.py   # no --adapter => base model only (the "before" number)
    python scripts/dec006_evaluate_adapter.py --adapter outputs/dec006_adapters/mistral7b_qlora
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src.datasets.product_generator import ALLOWED_PREDICATES, generate_products
from src.evaluator import Triple, compute_precision_recall_f1
from src.leakage_split import build_product_split
from src.prompts import build_extraction_prompt

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
SYNTHETIC_TRAIN_PATH = "outputs/dec006_synthetic_data/product_domain_synth_train.jsonl"


def build_prompt(text: str) -> str:
    return build_extraction_prompt(text, ALLOWED_PREDICATES)


def load_trained_subjects(path: str) -> set[str]:
    """Extract every product/subject name actually used in the fine-tuning
    training data, by parsing the trailing target JSON array of each
    training example's text field (the LAST '[' in the string -- the
    prompt's own fixed "Example output" block also contains one, so the
    first bracket is not it)."""
    trained = set()
    p = Path(path)
    if not p.exists():
        return trained
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                text = json.loads(line)["text"]
            except Exception:
                continue
            start = text.rfind("[")
            if start == -1:
                continue
            try:
                items = json.loads(text[start:])
            except Exception:
                continue
            for item in items:
                subj = item.get("subject")
                if subj:
                    trained.add(subj)
    return trained


def parse_json_array(text: str) -> list[dict]:
    text = text.strip()
    if "[" not in text:
        return []
    text = text[text.find("["):]
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else []
    except Exception:
        pass
    last_obj_end = text.rfind("}")
    if last_obj_end != -1:
        repaired = text[:last_obj_end + 1] + "]"
        try:
            data = json.loads(repaired)
            return data if isinstance(data, list) else []
        except Exception:
            pass
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", default=None, help="Path to a saved LoRA adapter, or omit for base model only")
    parser.add_argument("--base-model", default=BASE_MODEL)
    parser.add_argument("--n-products", type=int, default=50)
    parser.add_argument("--training-data-path", default=SYNTHETIC_TRAIN_PATH,
                         help="Used only for the leakage guard -- excludes any test product also present here")
    parser.add_argument("--eval-split", choices=["val", "test"], default="test",
                         help="DEC-027: evaluate on the validation split (hyperparameter selection) "
                              "or the test split (confirmatory run). Defaults to test so existing "
                              "usage (N=50, no --eval-split) is unaffected.")
    parser.add_argument("--strict-leakage-guard", action="store_true",
                         help="DEC-027: abort with a non-zero exit if any held-out product leaks "
                              "into the training data, instead of silently excluding it. Uses "
                              "src/dec027_leakage_guard.py; only meaningful with --n-products 200.")
    args = parser.parse_args()

    if args.strict_leakage_guard:
        from src.dec027_leakage_guard import assert_no_leakage
        assert_no_leakage(args.training_data_path, n_products=args.n_products)
        print("DEC-027 strict leakage guard: PASSED (no held-out product in the training data).")

    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.float16, device_map="auto",
    )
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()

    split = build_product_split(n_products=args.n_products)
    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        args.n_products, seed=42
    ):
        products[idx] = (unstructured_row, gold_unstructured)

    test_idx = sorted(i for i in products if split.get(i) == args.eval_split)

    trained_subjects = load_trained_subjects(args.training_data_path)
    leaked_idx = [i for i in test_idx if products[i][0]["product_name"] in trained_subjects]
    if leaked_idx:
        leaked_names = [products[i][0]["product_name"] for i in leaked_idx]
        print(f"!!! LEAKAGE GUARD: excluding {len(leaked_idx)}/{len(test_idx)} test products "
              f"also present in the fine-tuning training data: {leaked_names}")
        test_idx = [i for i in test_idx if i not in leaked_idx]
    print(f"Evaluating on {len(test_idx)} leakage-safe test products.")

    all_pred_triples, all_gold_triples = [], []
    predictions = []

    for idx in test_idx:
        unstructured_row, gold_unstructured = products[idx]
        prompt = build_prompt(unstructured_row["text"][:700])

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=768).to(model.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = model.generate(
                **inputs, max_new_tokens=400, min_new_tokens=100, do_sample=False,
                pad_token_id=tokenizer.eos_token_id, eos_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )
        completion = tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        items = parse_json_array(completion)

        pred_triples = []
        for item in items:
            try:
                subj, pred, obj = str(item.get("subject", "")).strip(), str(item.get("predicate", "")).strip(), str(item.get("object", "")).strip()
                if subj and pred and obj and pred in ALLOWED_PREDICATES:
                    pred_triples.append({"subject": subj, "predicate": pred, "object": obj})
            except Exception:
                continue

        predictions.append({"product_idx": idx, "predicted_triples": pred_triples,
                             "gold_triples": [{"subject": s, "predicate": p, "object": o} for s, p, o, _ in gold_unstructured]})

        for t in pred_triples:
            all_pred_triples.append(Triple(t["subject"], t["predicate"], t["object"]))
        for s, p, o, _ in gold_unstructured:
            all_gold_triples.append(Triple(s, p, o))

    metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples)
    print(f"Adapter: {args.adapter or '(base model only)'}")
    print(f"P={metrics['precision']:.4f} R={metrics['recall']:.4f} F1={metrics['f1']:.4f}")

    adapter_name = Path(args.adapter).name if args.adapter else "base_model"
    # DEC-027: suffix with the eval split whenever it's non-default (val),
    # so a val-split grid-search evaluation never overwrites the same
    # adapter's later test-split confirmatory evaluation.
    out_dir = Path("outputs/dec006_eval") / (
        adapter_name if args.eval_split == "test" else f"{adapter_name}_{args.eval_split}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    with open(out_dir / "metrics.json", "w") as f:
        json.dump({
            "adapter": args.adapter, "base_model": args.base_model,
            "n_test_products_evaluated": len(test_idx),
            "n_test_products_excluded_for_leakage": len(leaked_idx),
            "leaked_product_names_excluded": [products[i][0]["product_name"] for i in leaked_idx],
            **metrics,
        }, f, indent=2)
    print(f"Saved to {out_dir}/")


if __name__ == "__main__":
    main()
