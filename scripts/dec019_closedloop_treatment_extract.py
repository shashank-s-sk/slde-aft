"""DEC-019 closed-loop test — TREATMENT arm, extraction step.

Runs on a rented GPU (same setup as DEC-006). Uses the best-performing
fine-tuned adapter (seed 43, EVID-028: F1=0.2090, the single best of
the 3 seeds tested) to extract triples from the SAME 140 train-split
product texts the CONTROL arm (dec019_closedloop_control.py) uses,
with the SAME plain prompt format (src/prompts.py) the adapter was
actually trained on.

Only extraction happens here (GPU-only step); merging these triples
into the replayed iteration-4 KB state happens locally afterward via
dec019_closedloop_treatment_merge.py, once this script's output file
is pulled back down (git push from the pod, same flow as DEC-006).

Usage, after the usual pod setup (clone, checkout, pip install,
export PYTHONPATH=$(pwd)):
    python scripts/dec019_closedloop_treatment_extract.py
"""

from __future__ import annotations

import json
from pathlib import Path

from src.datasets.product_generator import ALLOWED_PREDICATES, generate_products
from src.leakage_split import build_product_split  # noqa: F401 (not used; split loaded from CSV directly)
from src.prompts import build_extraction_prompt

BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"
ADAPTER_PATH = "outputs/dec006_adapters/mistral7b_qlora_seed43"
SPLIT_PATH = "data/product_split_200.csv"
N_PRODUCTS = 200
GENERATION_SEED = 42
OUT_PATH = "outputs/dec019_closedloop/treatment/iteration5_triples.json"


def load_split() -> dict[int, str]:
    import csv
    split = {}
    with open(SPLIT_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            split[int(row["product_idx"])] = row["split"]
    return split


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
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto")
    model = PeftModel.from_pretrained(model, ADAPTER_PATH)
    model.eval()

    split = load_split()
    products = {}
    for idx, structured_row, unstructured_row, gold_structured, gold_unstructured in generate_products(
        N_PRODUCTS, seed=GENERATION_SEED
    ):
        products[idx] = unstructured_row

    train_idx = sorted(i for i in products if split.get(i) == "train")
    print(f"Extracting on {len(train_idx)} train products with {ADAPTER_PATH}")

    all_triples = []
    for i, idx in enumerate(train_idx):
        text = products[idx]["text"][:700]
        prompt = build_extraction_prompt(text, ALLOWED_PREDICATES)
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

        n_kept = 0
        for item in items:
            try:
                subj = str(item.get("subject", "")).strip()
                pred = str(item.get("predicate", "")).strip()
                obj = str(item.get("object", "")).strip()
                conf = float(item.get("confidence", 0.9))
                if subj and pred and obj and pred in ALLOWED_PREDICATES:
                    all_triples.append({
                        "product_idx": idx, "subject": subj, "predicate": pred, "object": obj,
                        "confidence": conf, "source_id": f"product_{idx}",
                        "source_type": "unstructured", "provenance": text,
                    })
                    n_kept += 1
            except Exception:
                continue
        print(f"  [{i+1}/{len(train_idx)}] product_{idx}: {n_kept} triples")

    out_path = Path(OUT_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_triples, f, indent=2)
    print(f"\nWrote {len(all_triples)} triples across {len(train_idx)} products -> {out_path}")


if __name__ == "__main__":
    main()
