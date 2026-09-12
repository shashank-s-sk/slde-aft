"""DEC-006 local-adapter evaluation — run on the same rented GPU
alongside dec006_lora_finetune.py, NOT locally. Loads a base model
(optionally with a LoRA adapter), runs local inference on the held-out
test split (data/product_split.csv, respecting the same leakage-safe
boundaries as every other experiment in this project), and evaluates
with the exact same normalized-triple protocol used everywhere else
(src/evaluator.py) so results are directly comparable to the API-based
runs (EVID-013 etc).

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

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"


def build_prompt(text: str) -> str:
    return f"""You extract factual product knowledge triples.

Return ONLY a valid JSON array.
Each item must contain: subject, predicate, object, confidence

Allowed predicates:
{", ".join(ALLOWED_PREDICATES)}

Rules:
- Extract only facts explicitly supported by text.
- confidence must be between 0.85 and 0.99.
- Do not invent facts.

Text:
{text}

Example output:
[
  {{"subject":"TechNova Smartphone Max 1","predicate":"manufactured_by","object":"TechNova","confidence":0.95}}
]""".strip()


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
    args = parser.parse_args()

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

    test_idx = sorted(i for i in products if split.get(i) == "test")

    all_pred_triples, all_gold_triples = [], []
    predictions = []

    for idx in test_idx:
        unstructured_row, gold_unstructured = products[idx]
        prompt = build_prompt(unstructured_row["text"][:700])

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=768).to(model.device)
        input_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = model.generate(
                **inputs, max_new_tokens=400, do_sample=False,
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

    out_dir = Path("outputs/dec006_eval") / (Path(args.adapter).name if args.adapter else "base_model")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "predictions.json", "w") as f:
        json.dump(predictions, f, indent=2)
    with open(out_dir / "metrics.json", "w") as f:
        json.dump({"adapter": args.adapter, "base_model": args.base_model, **metrics}, f, indent=2)
    print(f"Saved to {out_dir}/")


if __name__ == "__main__":
    main()
