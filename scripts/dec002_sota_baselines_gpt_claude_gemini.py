"""DEC-002 extension: GPT-4o, Claude Sonnet 5, and Gemini 2.5 Pro as
additional external SOTA baselines on the same 30-sentence CaRB pilot
(professor_feedback.md point #2 explicitly names "GPT-4 extraction,"
"Claude," and "Gemini" among the expected comparisons).

Reuses the identical protocol as EVID-021's DeepSeek baseline: same 30
sentences (data/carb_dev_sample.jsonl), same prompt
(prompts/openie_carb_v1.txt via src/extractors/openrouter_openie.py),
same evaluator -- and additionally scored with the OFFICIAL CaRB
scorer (data/CaRB/carb.py, per EVID-031), not just the internal
evaluator, since EVID-031 already showed the internal evaluator
undercounts real performance by 4-8x.

Model picks and why:
  - openai/gpt-4o: matches "GPT-4 extraction" literally as named in
    the feedback, rather than a newer unnamed generation.
  - anthropic/claude-sonnet-5: current-generation Claude, comparable
    tier to DeepSeek-V3.2 (not the priciest Opus tier, matching
    DEC-002's own "a strong baseline, not necessarily the most
    expensive one" precedent).
  - google/gemini-2.5-pro: stable, non-preview Gemini (preview models
    can be deprecated/rate-limited without notice, which would hurt
    reproducibility).

Usage (real API calls, ~90 total across 3 models x 30 sentences,
expected cost in the same cents-to-low-dollars range as EVID-021's
DeepSeek run):
    python scripts/dec002_sota_baselines_gpt_claude_gemini.py
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from src.extractors.openrouter_openie import extract_openie_triples
from src.evaluator import Triple, compute_precision_recall_f1

# Retry/pacing: the first real run hit OpenRouter's in-flight credit
# budget exhaustion (402, transient -- clears once earlier requests
# settle) and Claude Sonnet 5's new-account rate limit (429, 20 req/min
# cap) firing 3 models back-to-back with no delay. Fixed with a
# per-call floor delay (keeps every model comfortably under 20 rpm) and
# retry-with-backoff on 402/429.
MIN_SECONDS_BETWEEN_CALLS = 3.5
MAX_RETRIES = 4
RETRY_BACKOFF_SECONDS = 20


def extract_with_retry(sentence: str, api_key: str, model: str, max_tokens: int = 512) -> dict:
    for attempt in range(MAX_RETRIES + 1):
        result = extract_openie_triples(sentence, api_key=api_key, model=model, max_tokens=max_tokens)
        if result["http_status"] not in (402, 429):
            return result
        if attempt < MAX_RETRIES:
            print(f"    retrying after {RETRY_BACKOFF_SECONDS}s (http_status={result['http_status']})")
            time.sleep(RETRY_BACKOFF_SECONDS)
    return result

DATA_PATH = Path("data/carb_dev_sample.jsonl")
OUTPUT_ROOT = Path("outputs/dec002_sota_baselines")

SYSTEMS = {
    "gpt4o_baseline": "openai/gpt-4o",
    "claude_sonnet5_baseline": "anthropic/claude-sonnet-5",
    "gemini25pro_baseline": "google/gemini-2.5-pro",
}

# Gemini 2.5 Pro's response (markdown-fenced JSON) got truncated mid-array
# at the default 512 max_tokens -- confirmed via a direct diagnostic call
# (raw output cut off after ```json\n[\n  {\n    "subject": "3). Bumped for
# Gemini specifically; other models already succeed at the default.
MAX_TOKENS_BY_SYSTEM = {
    "gemini25pro_baseline": 3072,
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", nargs="+", choices=list(SYSTEMS.keys()), default=None,
                         help="Run only these systems (default: all)")
    args = parser.parse_args()
    systems = {k: v for k, v in SYSTEMS.items() if args.only is None or k in args.only}

    api_key = load_api_key()
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    sentences = load_sentences()
    print(f"Loaded {len(sentences)} CaRB sentences")

    summary_rows = []

    for system_name, model in systems.items():
        print(f"\n=== {system_name} ({model}) ===")
        sys_dir = OUTPUT_ROOT / system_name
        sys_dir.mkdir(parents=True, exist_ok=True)

        predictions = []
        call_log = []
        all_pred_triples = []
        all_gold_triples = []
        total_cost = 0.0

        for rec in sentences:
            t0 = time.perf_counter()
            result = extract_with_retry(rec["sentence"], api_key=api_key, model=model,
                                         max_tokens=MAX_TOKENS_BY_SYSTEM.get(system_name, 512))
            cost = result.get("cost_usd") or 0.0
            total_cost += cost

            elapsed = time.perf_counter() - t0
            if elapsed < MIN_SECONDS_BETWEEN_CALLS:
                time.sleep(MIN_SECONDS_BETWEEN_CALLS - elapsed)

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

    # Rebuild the full summary from every system's saved metrics.json (not
    # just the ones run this invocation), so --only doesn't clobber rows
    # for systems completed in an earlier run.
    all_rows = []
    for system_name, model in SYSTEMS.items():
        metrics_path = OUTPUT_ROOT / system_name / "metrics.json"
        if not metrics_path.exists():
            continue
        with open(metrics_path, encoding="utf-8") as f:
            m = json.load(f)
        all_rows.append({
            "system": system_name, "model": model,
            "precision": m["precision"], "recall": m["recall"], "f1": m["f1"],
            "true_positives": m["true_positives"], "false_positives": m["false_positives"],
            "false_negatives": m["false_negatives"], "n_errors": m["n_errors"],
            "cost_usd": m["total_cost_usd"],
        })

    if all_rows:
        with open(OUTPUT_ROOT / "comparison_summary.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)

    print(f"\nSaved comparison to {OUTPUT_ROOT}/comparison_summary.csv")


if __name__ == "__main__":
    main()
