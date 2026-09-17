"""DEC-002 extension: REBEL (Babelscape/rebel-large) as an external
OpenIE baseline -- the first-named, most standard system in
professor_feedback.md point #2's list, and the most tractable of the
remaining ones (a downloadable HF model, CPU-feasible for 30 short
sentences, no API cost).

Same 30 CaRB sentences (data/carb_dev_sample.jsonl) as every other
baseline in this project. REBEL's output uses special delimiter tokens
(<triplet>, <subj>, <obj>) rather than natural-language JSON, so this
script has its own dedicated parser instead of reusing
src/extractors/openrouter_openie.py's JSON-array parser.

Runs entirely locally, no API key needed. First run downloads the
~500MB model from Hugging Face.

Usage:
    python scripts/dec002_rebel_baseline.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.evaluator import Triple, compute_precision_recall_f1

DATA_PATH = Path("data/carb_dev_sample.jsonl")
OUTPUT_DIR = Path("outputs/dec002_rebel_baseline")
MODEL_NAME = "Babelscape/rebel-large"


def load_sentences():
    records = []
    with open(DATA_PATH, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records


def extract_triplets(text: str) -> list[dict]:
    """Parse REBEL's <triplet>/<subj>/<obj> delimited output format into
    a list of {"subject", "predicate", "object"} dicts. Adapted from the
    parsing logic on the Babelscape/rebel-large model card."""
    triplets = []
    relation, subject, relation_type, object_ = "", "", "", ""
    text = text.strip()
    current = "x"
    for token in text.replace("<s>", "").replace("<pad>", "").replace("</s>", "").split():
        if token == "<triplet>":
            current = "t"
            if relation != "":
                triplets.append({"subject": subject.strip(), "predicate": relation.strip(), "object": object_.strip()})
                relation = ""
            subject = ""
        elif token == "<subj>":
            current = "s"
            if relation != "":
                triplets.append({"subject": subject.strip(), "predicate": relation.strip(), "object": object_.strip()})
            object_ = ""
        elif token == "<obj>":
            current = "o"
            relation = ""
        else:
            if current == "t":
                subject += " " + token
            elif current == "s":
                object_ += " " + token
            elif current == "o":
                relation += " " + token
    if subject != "" and relation != "" and object_ != "":
        triplets.append({"subject": subject.strip(), "predicate": relation.strip(), "object": object_.strip()})
    return triplets


def main():
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sentences = load_sentences()
    print(f"Loaded {len(sentences)} CaRB sentences")

    print(f"Loading {MODEL_NAME} (CPU)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model.eval()

    gen_kwargs = {
        "max_length": 256,
        "length_penalty": 0,
        "num_beams": 3,
        "num_return_sequences": 1,
    }

    predictions = []
    all_pred_triples, all_gold_triples = [], []
    t_start = time.perf_counter()

    for i, rec in enumerate(sentences):
        inputs = tokenizer(rec["sentence"], max_length=256, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = model.generate(inputs["input_ids"], attention_mask=inputs["attention_mask"], **gen_kwargs)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=False)
        triples = extract_triplets(decoded)

        predictions.append({
            "sentence_id": rec["sentence_id"], "sentence": rec["sentence"],
            "gold_triples": rec["gold_triples"], "predicted_triples": triples, "error": None,
        })
        for t in triples:
            all_pred_triples.append(Triple(t["subject"], t["predicate"], t["object"]))
        for t in rec["gold_triples"]:
            all_gold_triples.append(Triple(t["subject"], t["predicate"], t["object"]))

        print(f"  [{i+1}/{len(sentences)}] {rec['sentence_id']}: {len(triples)} triples")

    runtime_s = time.perf_counter() - t_start
    metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples)

    with open(OUTPUT_DIR / "predictions.json", "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)
    with open(OUTPUT_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "system": "rebel_baseline", "model": MODEL_NAME, "n_sentences": len(sentences),
            "runtime_s": runtime_s, "n_errors": 0, **metrics,
        }, f, indent=2)

    print(f"\nrebel_baseline: P={metrics['precision']:.4f} R={metrics['recall']:.4f} "
          f"F1={metrics['f1']:.4f} | runtime={runtime_s:.1f}s")
    print(f"Saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
