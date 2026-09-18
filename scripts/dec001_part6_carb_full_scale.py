"""DEC-001 Part 6: full 641-sentence-scale CaRB run (actually 548 of
641 test.txt lines that have an exact-string gold match in
data/CaRB/data/gold/test.tsv -- same exact-match selection method used
for the original 30-sentence pilot, just not truncated; the ~93-line
gap is pre-existing whitespace/quoting mismatch between test.txt and
test.tsv, not a new methodology change).

Same protocol as EVID-021's 30-sentence run
(scripts/dec001_002_carb30_comparison.py): same prompt
(prompts/openie_carb_v1.txt via extract_openie_triples's default),
same two systems (SLDE-AFT's own pinned Llama-3.1-8B extractor +
DeepSeek-V3.2 external baseline) -- GPT-4o/Claude/Gemini deliberately
excluded from this full-scale run per the cost analysis in Decision
log.md DEC-001 Part 6 (their full-scale cost, ~$12.66 combined, was
deferred; their 30-sentence pilot numbers remain the reported SOTA
comparison points).

INCREMENTAL/RESUMABLE (added after the first attempt at this was
killed by a system-wide low-memory event with zero progress saved,
since the original version only wrote output at the very end): each
sentence's result is appended to `predictions.jsonl` immediately and
the file handle is flushed after every line, so a kill mid-run loses
at most the single in-flight call. Re-running the same command skips
any sentence_id already present in that file and continues from where
it left off.

Usage (run ONE system at a time -- sequential, not parallel, to keep
peak memory low after the earlier kill):
    python -m scripts.dec001_part6_carb_full_scale slde_aft_llama
    python -m scripts.dec001_part6_carb_full_scale deepseek_baseline
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from src.extractors.openrouter_openie import extract_openie_triples
from src.evaluator import Triple, compute_precision_recall_f1

DATA_PATH = Path("data/carb_full_sample.jsonl")
OUTPUT_ROOT = Path("outputs/dec001_part6_carb_full")

SYSTEMS = {
    "slde_aft_llama": "meta-llama/llama-3.1-8b-instruct",
    "deepseek_baseline": "deepseek/deepseek-v3.2",
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


def load_done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(json.loads(line)["sentence_id"])
            except (json.JSONDecodeError, KeyError):
                continue  # last line may be a partial write from a kill
    return done


def main(system_name: str):
    if system_name not in SYSTEMS:
        raise SystemExit(f"Unknown system {system_name!r}, expected one of {list(SYSTEMS)}")
    model = SYSTEMS[system_name]

    api_key = load_api_key()
    sys_dir = OUTPUT_ROOT / system_name
    sys_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = sys_dir / "predictions.jsonl"

    sentences = load_sentences()
    done_ids = load_done_ids(predictions_path)
    remaining = [rec for rec in sentences if rec["sentence_id"] not in done_ids]
    print(f"{system_name}: {len(sentences)} total sentences, "
          f"{len(done_ids)} already done, {len(remaining)} remaining", flush=True)

    with open(predictions_path, "a", encoding="utf-8") as f:
        for i, rec in enumerate(remaining):
            result = extract_openie_triples(rec["sentence"], api_key=api_key, model=model)
            row = {
                "sentence_id": rec["sentence_id"], "sentence": rec["sentence"],
                "gold_triples": rec["gold_triples"], "predicted_triples": result["triples"],
                "error": result["error"], "cost_usd": result.get("cost_usd") or 0.0,
                "latency_s": result["latency_s"], "http_status": result["http_status"],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()

            if (i + 1) % 25 == 0 or i == len(remaining) - 1:
                print(f"  [{i + 1}/{len(remaining)}] {rec['sentence_id']}: "
                      f"{len(result['triples'])} triples", flush=True)

    # Rebuild full metrics from the complete predictions.jsonl (covers
    # both this run and any earlier resumed portion).
    all_pred_triples, all_gold_triples = [], []
    total_cost, n_errors = 0.0, 0
    with open(predictions_path, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            total_cost += row["cost_usd"]
            if row["error"]:
                n_errors += 1
            for t in row["predicted_triples"]:
                all_pred_triples.append(Triple(t["subject"], t["predicate"], t["object"]))
            for t in row["gold_triples"]:
                all_gold_triples.append(Triple(t["subject"], t["predicate"], t["object"]))

    metrics = compute_precision_recall_f1(all_gold_triples, all_pred_triples)
    with open(sys_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "system": system_name, "model": model, "n_sentences": len(sentences),
            "total_cost_usd": total_cost, "n_errors": n_errors, **metrics,
        }, f, indent=2)

    print(f"\n{system_name}: P={metrics['precision']:.4f} R={metrics['recall']:.4f} "
          f"F1={metrics['f1']:.4f} | cost=${total_cost:.6f} | errors={n_errors}", flush=True)
    print(f"Saved -> {sys_dir}/", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m scripts.dec001_part6_carb_full_scale <system_name>")
    main(sys.argv[1])
