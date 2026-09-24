"""DEC-031 extraction (the only paid step): one API call per sentence,
for EVERY sentence of the 845 eligible DocRED dev documents
(src/dec031_docred.load_docs), with the same model, prompt, temperature
and max_tokens as DEC-020's pilot. Every matching-key arm, R2/R3, and
the evidence-only comparison arm are then computed offline from these
same extractions by scripts/dec031_docred_analyze.py.

Crash-safe and shardable:
  - Each finished call is appended to
    outputs/dec031_docred/extractions/shard_<i>of<n>.jsonl immediately,
    so a crash or kill loses at most the call in flight.
  - A restarted shard skips every (doc_idx, sent_id) already recorded
    with an HTTP response. Calls that failed at the network level
    (http_status null, after openrouter_http's own retries) are
    requested again. Calls that returned unparsable output are NOT
    re-requested: that is a real outcome, kept as-is for every
    sentence alike (DEC-029's retry rule was applied unevenly across
    configs; this avoids that).
  - Documents are split across shards by doc_idx % n_shards.

Usage:
    python -u -m scripts.dec031_docred_extract --shard 0 --n-shards 3
    python -u -m scripts.dec031_docred_extract --dry-run --limit-docs 3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.dec031_docred import load_docs

PROMPT_PATH = Path("prompts/openie_docred_v1.txt")
MODEL = "meta-llama/llama-3.1-8b-instruct"
MAX_TOKENS = 1024
OUTPUT_DIR = Path("outputs/dec031_docred/extractions")


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def done_calls(path: Path) -> set[tuple[int, int]]:
    done = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec["http_status"] is not None:
                    done.add((rec["doc_idx"], rec["sent_id"]))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--n-shards", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-docs", type=int, default=None)
    args = ap.parse_args()

    if args.dry_run:
        def extract(sentence, **kw):
            return {"triples": [], "error": None, "http_status": 200, "latency_s": 0.0,
                    "cost_usd": 0.0, "network_retries": 0}
        out_dir = OUTPUT_DIR.parent / "dry_run"
        api_key = ""
    else:
        from src.extractors.openrouter_openie import extract_openie_triples as extract
        out_dir = OUTPUT_DIR
        api_key = load_api_key()

    docs = load_docs()
    if args.limit_docs:
        docs = docs[:args.limit_docs]
    mine = [d for d in docs if d["doc_idx"] % args.n_shards == args.shard]
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"shard_{args.shard}of{args.n_shards}.jsonl"
    done = done_calls(out_path)
    todo = [(d, i) for d in mine for i in range(len(d["sentences"])) if (d["doc_idx"], i) not in done]
    print(f"shard {args.shard}/{args.n_shards}: {len(mine)} docs, "
          f"{sum(len(d['sentences']) for d in mine)} sentences, {len(done)} already done, "
          f"{len(todo)} to run", flush=True)

    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    cost = 0.0
    with open(out_path, "a", encoding="utf-8") as f:
        for n, (doc, sent_id) in enumerate(todo, 1):
            r = extract(doc["sentences"][sent_id], api_key=api_key, model=MODEL,
                        prompt_template=prompt_template, max_tokens=MAX_TOKENS)
            rec = {"doc_idx": doc["doc_idx"], "title": doc["title"], "sent_id": sent_id,
                   "triples": r["triples"], "error": r["error"], "http_status": r["http_status"],
                   "cost_usd": r.get("cost_usd"), "latency_s": r.get("latency_s"),
                   "network_retries": r.get("network_retries", 0)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            cost += r.get("cost_usd") or 0.0
            if n % 50 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} calls, ${cost:.4f} this session", flush=True)
    print(f"DONE shard {args.shard}: ${cost:.6f} this session", flush=True)


if __name__ == "__main__":
    main()
