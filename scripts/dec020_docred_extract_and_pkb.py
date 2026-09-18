"""DEC-020 steps 3-5: run extraction + PKB aggregation on the 15-doc
DocRED pilot (outputs/dec020_docred_pilot/pilot_docs.jsonl), and
compare against a naive no-aggregation baseline -- the actual test of
whether the FRAMEWORK (not just the extractor) adds value on public
data.

Per document:
  1. Extract triples from each unique evidence sentence (one API call
     per unique sentence, schema-guided prompt over DocRED's 96 closed
     relation types -- prompts/openie_docred_v1.txt).
  2. NAIVE baseline: union of all extracted triples across the
     document's sentences, no confidence filtering, no aggregation
     across repeated observations of the same fact.
  3. PKB pipeline: feed every extracted triple into a fresh
     CandidateBufferAdapter as one observation (confidence=1.0 per
     observation, same convention as CaRB/BioRED, which don't capture
     per-triple calibrated confidence either) -- so a triple recovered
     from 2+ different evidence sentences accumulates multiple
     observations and gets a higher conservative-Noisy-Or confidence
     than a triple seen only once. Keep only accepted triples at or
     above the accept threshold.

Threshold note: DocRED naturally provides far fewer repeated
observations per fact (median ~1-2 evidence sentences) than the
product-domain pipeline's multi-iteration setting (which calibrated
the default 0.88 threshold). With shrinkage=0.5 and confidence=1.0
observations, conservative-Noisy-Or support after k observations is
1-0.5^k: 0.50 (k=1), 0.75 (k=2), 0.875 (k=3), 0.9375 (k=4). Using 0.88
here would reject nearly everything (most triples never reach 4
evidence sentences), producing a degenerate, uninformative comparison.
**Threshold is recalibrated to 0.70 for this experiment** so that
triples with >=2 corroborating observations pass and single-observation
ones don't -- a documented, domain-specific parameter choice, not a
silent change to the project's core-pipeline default.

No functional-predicate policy is applied (configs/
docred_functional_predicates.json is empty) -- unlike the product
domain, DocRED's Wikidata-style relations don't have an established
single-valued-per-subject policy in this project, so only plain
Noisy-Or corroboration is tested here, not the conflict-adjustment
penalty. Documented simplification, not a hidden one.

Usage:
    python -m scripts.dec020_docred_extract_and_pkb           # real run
    python -m scripts.dec020_docred_extract_and_pkb --dry-run  # no API calls, mocked extractor
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.evaluator import Triple, compute_precision_recall_f1
from src.probkb_v2_adapter import CandidateBufferAdapter

PILOT_PATH = Path("outputs/dec020_docred_pilot/pilot_docs.jsonl")
PROMPT_PATH = Path("prompts/openie_docred_v1.txt")
FUNCTIONAL_PREDICATES_PATH = "configs/docred_functional_predicates.json"
OUTPUT_DIR = Path("outputs/dec020_docred_extract_and_pkb")
MODEL = "meta-llama/llama-3.1-8b-instruct"
THRESHOLD = 0.70
SHRINKAGE = 0.5


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def load_pilot_docs() -> list[dict]:
    docs = []
    with open(PILOT_PATH, encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs


def unique_evidence_sentences(doc: dict) -> dict[int, str]:
    """sentence_id -> sentence_text, for every sentence referenced as
    evidence by at least one gold triple in this document."""
    out: dict[int, str] = {}
    for obs in doc["observations"]:
        out[obs["sentence_id"]] = obs["sentence_text"]
    return out


def make_extractor(dry_run: bool):
    if dry_run:
        def fake_extract(sentence, api_key, model, prompt_template=None, max_tokens=1024):
            return {"triples": [], "error": None, "http_status": 200,
                     "latency_s": 0.0, "cost_usd": 0.0}
        return fake_extract

    from src.extractors.openrouter_openie import extract_openie_triples
    return extract_openie_triples


def main(dry_run: bool = False):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_pilot_docs()
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    extract = make_extractor(dry_run)
    api_key = "" if dry_run else load_api_key()

    all_gold_triples: list[Triple] = []
    all_pred_triples_naive: list[Triple] = []
    all_pred_triples_pkb: list[Triple] = []
    per_doc_results = []
    total_cost = 0.0
    n_calls = 0
    n_errors = 0

    for doc_idx, doc in enumerate(docs):
        title = doc["title"]
        sent_map = unique_evidence_sentences(doc)
        print(f"\n=== [{doc_idx + 1}/{len(docs)}] {title} "
              f"({len(sent_map)} unique evidence sentences, "
              f"{len(doc['gold_triples'])} gold triples) ===")

        predicted_by_sentence: dict[int, list[dict]] = {}
        for sent_id, sent_text in sent_map.items():
            result = extract(sent_text, api_key=api_key, model=MODEL,
                              prompt_template=prompt_template, max_tokens=1024)
            n_calls += 1
            cost = result.get("cost_usd") or 0.0
            total_cost += cost
            if result["error"]:
                n_errors += 1
            predicted_by_sentence[sent_id] = result["triples"]
            print(f"  sent {sent_id}: {len(result['triples'])} triples, "
                  f"${cost:.6f}, error={result['error']}")

        # --- naive baseline: dedup union across the document's sentences ---
        seen_naive = set()
        doc_naive_triples = []
        for triples in predicted_by_sentence.values():
            for t in triples:
                key = (t["subject"].strip().lower(), t["predicate"].strip().lower(),
                       t["object"].strip().lower())
                if key not in seen_naive:
                    seen_naive.add(key)
                    doc_naive_triples.append(t)
                    all_pred_triples_naive.append(Triple(t["subject"], t["predicate"], t["object"]))

        # --- PKB: one fresh adapter per document ---
        adapter = CandidateBufferAdapter(
            experiment_id="dec020_docred_pilot",
            run_id=f"doc_{doc_idx:02d}",
            prob_kb_version="v2",
            functional_predicates_path=FUNCTIONAL_PREDICATES_PATH,
            output_dir=str(OUTPUT_DIR / "pkb_artifacts" / f"doc_{doc_idx:02d}"),
            threshold=THRESHOLD,
            shrinkage=SHRINKAGE,
        )
        for sent_id, triples in predicted_by_sentence.items():
            for t in triples:
                adapter.accept_candidate(
                    subject=t["subject"], predicate=t["predicate"], object_value=t["object"],
                    confidence=1.0, source_id=f"{title}::sent{sent_id}",
                    source_type="docred_unstructured",
                    provenance=sent_map[sent_id][:300],
                )
        adapter.end_iteration(iteration=1)

        accepted = adapter.get_accepted()
        doc_pkb_triples = []
        for entry in accepted.values():
            if entry["confidence"] >= THRESHOLD:
                doc_pkb_triples.append(entry)
                all_pred_triples_pkb.append(Triple(entry["subject"], entry["predicate"], entry["object"]))

        for s, p, o in doc["gold_triples"]:
            all_gold_triples.append(Triple(s, p, o))

        per_doc_results.append({
            "title": title, "n_sentences": len(sent_map), "n_gold": len(doc["gold_triples"]),
            "n_naive_pred": len(doc_naive_triples), "n_pkb_accepted": len(doc_pkb_triples),
            "n_candidates_total": len(accepted),
        })
        print(f"  -> naive: {len(doc_naive_triples)} triples | "
              f"PKB accepted (>= {THRESHOLD}): {len(doc_pkb_triples)}/{len(accepted)} candidates")

    naive_metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples_naive)
    pkb_metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples_pkb)

    summary = {
        "model": MODEL, "n_docs": len(docs), "threshold": THRESHOLD, "shrinkage": SHRINKAGE,
        "total_cost_usd": total_cost, "n_api_calls": n_calls, "n_errors": n_errors,
        "naive_baseline": naive_metrics, "pkb_aggregated": pkb_metrics,
        "per_doc": per_doc_results,
    }
    with open(OUTPUT_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=== FINAL ===")
    print(f"NAIVE baseline:   P={naive_metrics['precision']:.4f} R={naive_metrics['recall']:.4f} F1={naive_metrics['f1']:.4f}")
    print(f"PKB aggregated:   P={pkb_metrics['precision']:.4f} R={pkb_metrics['recall']:.4f} F1={pkb_metrics['f1']:.4f}")
    print(f"API calls: {n_calls}, errors: {n_errors}, total cost: ${total_cost:.6f}")
    print(f"Saved -> {OUTPUT_DIR}/summary.json")


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
