"""DEC-032 extraction (the only paid step). Same crash-safe, shardable
design as scripts/dec031_docred_extract.py:
  - every finished call is appended to
    outputs/dec032_biored/extractions/<model>_<unit>/shard_<i>of<n>.jsonl
    immediately, so a crash loses at most the call in flight;
  - a restarted shard skips every call already recorded with an HTTP
    response and re-requests only network-level failures;
  - unparsable model output is never re-requested (DEC-029 lesson);
  - documents are split across shards by doc_idx % n_shards.

--model llama     meta-llama/llama-3.1-8b-instruct (the pipeline's extractor)
--model deepseek  deepseek/deepseek-v3.2 (external baseline, DEC-002's)
--unit sentence   one call per sentence, prompts/openie_biored_sent_v1.txt
                  (the primary setting; sources for aggregation)
--unit abstract   one call per whole title+abstract, prompts/openie_biored_v1.txt
                  unchanged (the DEC-009 pilot's setting, for continuity)

Usage:
    python -u -m scripts.dec032_biored_extract --model llama --unit sentence --shard 0 --n-shards 3
    python -u -m scripts.dec032_biored_extract --model llama --unit sentence --dry-run --limit-docs 3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.dec032_biored import load_docs

MODELS = {"llama": "meta-llama/llama-3.1-8b-instruct", "deepseek": "deepseek/deepseek-v3.2"}
PROMPTS = {"sentence": Path("prompts/openie_biored_sent_v1.txt"),
           "abstract": Path("prompts/openie_biored_v1.txt")}
MAX_TOKENS = 1024
OUTPUT_DIR = Path("outputs/dec032_biored/extractions")


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def units(doc: dict, unit: str) -> list[tuple[int, str]]:
    """(unit_id, text) pairs; unit_id is the sentence index, or 0 for the abstract."""
    return list(enumerate(doc["sentences"])) if unit == "sentence" else [(0, doc["text"])]


def done_calls(path: Path) -> set[tuple[int, int]]:
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue  # a line cut off when the process was stopped; redo that call
                if rec["http_status"] is not None:
                    done.add((rec["doc_idx"], rec["unit_id"]))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=sorted(MODELS), required=True)
    ap.add_argument("--unit", choices=sorted(PROMPTS), required=True)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--n-shards", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-docs", type=int, default=None)
    args = ap.parse_args()

    if args.dry_run:
        def extract(text, **kw):
            return {"triples": [], "error": None, "http_status": 200, "latency_s": 0.0,
                    "cost_usd": 0.0, "network_retries": 0}
        out_dir = OUTPUT_DIR.parent / "dry_run" / f"{args.model}_{args.unit}"
        api_key = ""
    else:
        from src.extractors.openrouter_openie import extract_openie_triples as extract
        out_dir = OUTPUT_DIR / f"{args.model}_{args.unit}"
        api_key = load_api_key()

    docs = load_docs()
    if args.limit_docs:
        docs = docs[:args.limit_docs]
    mine = [d for d in docs if d["doc_idx"] % args.n_shards == args.shard]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"shard_{args.shard}of{args.n_shards}.jsonl"
    done = done_calls(out_path)
    todo = [(d, uid, text) for d in mine for uid, text in units(d, args.unit)
            if (d["doc_idx"], uid) not in done]
    print(f"{args.model}/{args.unit} shard {args.shard}/{args.n_shards}: {len(mine)} docs, "
          f"{len(done)} calls already done, {len(todo)} to run", flush=True)

    prompt_template = PROMPTS[args.unit].read_text(encoding="utf-8")
    cost = 0.0
    with open(out_path, "a", encoding="utf-8") as f:
        for n, (doc, uid, text) in enumerate(todo, 1):
            r = extract(text, api_key=api_key, model=MODELS[args.model],
                        prompt_template=prompt_template, max_tokens=MAX_TOKENS)
            rec = {"doc_idx": doc["doc_idx"], "pmid": doc["pmid"], "unit_id": uid,
                   "triples": r["triples"], "error": r["error"], "http_status": r["http_status"],
                   "cost_usd": r.get("cost_usd"), "latency_s": r.get("latency_s"),
                   "network_retries": r.get("network_retries", 0)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            cost += r.get("cost_usd") or 0.0
            if n % 50 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} calls, ${cost:.4f} this session", flush=True)
    print(f"DONE {args.model}/{args.unit} shard {args.shard}: ${cost:.6f} this session", flush=True)


if __name__ == "__main__":
    main()
