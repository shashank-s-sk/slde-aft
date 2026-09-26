"""DEC-033 extraction (paid). Same crash-safe, shardable design as
DEC-031/032 (per-call cache, network failures re-requested, unparsable
output never re-requested), plus a hard per-process spending cap and an
optional pre-registered random document subset.

Arms written here (outputs/dec033_protocol/extractions/<corpus>_<model>_<unit>/):
  --unit document : one call per document, numbered sentences, cited evidence
  --unit sentence : one call per sentence (used for DocRED x DeepSeek)
Arms reused from earlier runs (never re-extracted):
  DocRED Llama sentence  -> outputs/dec031_docred/extractions
  BioRED Llama/DeepSeek sentence -> outputs/dec032_biored/extractions/<model>_sentence

Usage:
  python -u -m scripts.dec033_extract --corpus docred --model deepseek --unit document \
      --shard 0 --n-shards 3 --max-cost 0.20
  python -u -m scripts.dec033_extract --corpus docred --model deepseek --unit sentence \
      --doc-sample 400 --shard 0 --n-shards 3 --max-cost 0.20
  ... --dry-run --limit-docs 3
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src import dec033_protocol as P

MODELS = {"llama": "meta-llama/llama-3.1-8b-instruct", "deepseek": "deepseek/deepseek-v3.2"}
PROMPTS = {("docred", "document"): "prompts/openie_docred_doc_v1.txt",
           ("docred", "sentence"): "prompts/openie_docred_v1.txt",
           ("biored", "document"): "prompts/openie_biored_doc_v1.txt",
           ("biored", "sentence"): "prompts/openie_biored_sent_v1.txt"}
MAX_TOKENS = {"document": 2048, "sentence": 1024}
OUT = Path("outputs/dec033_protocol/extractions")
SAMPLE_SEED = 20330926


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                return key
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def sample_ids(n_docs: int, k: int) -> set[int]:
    """The pre-registered random document subset (fixed seed)."""
    return set(random.Random(SAMPLE_SEED).sample(range(n_docs), k))


def read_cache(path: Path) -> tuple[set, float]:
    done, cost = set(), 0.0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            cost += rec.get("cost_usd") or 0.0
            if rec["http_status"] is not None:
                done.add((rec["doc_idx"], rec["unit_id"]))
    return done, cost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["docred", "biored"], required=True)
    ap.add_argument("--model", choices=sorted(MODELS), required=True)
    ap.add_argument("--unit", choices=["document", "sentence"], required=True)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--n-shards", type=int, default=1)
    ap.add_argument("--max-cost", type=float, required=True, help="USD cap for THIS process")
    ap.add_argument("--doc-sample", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit-docs", type=int, default=None)
    args = ap.parse_args()

    docs = P.load_docred() if args.corpus == "docred" else P.load_biored()
    if args.doc_sample:
        keep = sample_ids(len(docs), args.doc_sample)
        docs = [d for d in docs if d["doc_idx"] in keep]
    if args.limit_docs:
        docs = docs[:args.limit_docs]
    mine = [d for d in docs if d["doc_idx"] % args.n_shards == args.shard]

    if args.dry_run:
        def extract(text, **kw):
            return {"triples": [], "error": None, "http_status": 200, "latency_s": 0.0,
                    "cost_usd": 0.0, "network_retries": 0}
        out_dir = OUT.parent / "dry_run" / f"{args.corpus}_{args.model}_{args.unit}"
        api_key = ""
    else:
        from src.extractors.openrouter_openie import extract_openie_triples as extract
        out_dir = OUT / f"{args.corpus}_{args.model}_{args.unit}"
        api_key = load_api_key()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"shard_{args.shard}of{args.n_shards}.jsonl"
    done, spent = read_cache(path)

    def units(d):
        return [(0, P.numbered(d))] if args.unit == "document" else list(enumerate(d["sentences"]))

    todo = [(d, u, text) for d in mine for u, text in units(d) if (d["doc_idx"], u) not in done]
    print(f"{args.corpus}/{args.model}/{args.unit} shard {args.shard}/{args.n_shards}: "
          f"{len(mine)} docs, {len(done)} calls done (${spent:.4f}), {len(todo)} to run, "
          f"cap ${args.max_cost:.4f}", flush=True)
    template = Path(PROMPTS[(args.corpus, args.unit)]).read_text(encoding="utf-8")
    with open(path, "a", encoding="utf-8") as f:
        for n, (d, u, text) in enumerate(todo, 1):
            if spent >= args.max_cost:
                print(f"COST CAP REACHED at ${spent:.4f} after {n - 1} calls; stopping", flush=True)
                break
            r = extract(text, api_key=api_key, model=MODELS[args.model], prompt_template=template,
                        max_tokens=MAX_TOKENS[args.unit], keep_evidence=(args.unit == "document"))
            rec = {"doc_idx": d["doc_idx"], "unit_id": u, "triples": r["triples"], "error": r["error"],
                   "http_status": r["http_status"], "cost_usd": r.get("cost_usd"),
                   "latency_s": r.get("latency_s"), "network_retries": r.get("network_retries", 0)}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            spent += r.get("cost_usd") or 0.0
            if n % 50 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} calls, ${spent:.4f} total in this shard", flush=True)
    print(f"DONE {args.corpus}/{args.model}/{args.unit} shard {args.shard}: ${spent:.6f}", flush=True)


if __name__ == "__main__":
    main()
