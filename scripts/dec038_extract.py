"""DEC-038 extraction (paid): fresh extraction of the 2,010-document DocRED
cross-document redundancy subset (outputs/dec038_crossdoc/doc_list.json).

Arms (pre-registered, Decision log DEC-038, commit f87e91a):
  --arm deepseek_document : DeepSeek-V3.2, one call per document, numbered
                            sentences, cited evidence (DEC-033 prompt/settings)
  --arm llama_sentence    : Llama-3.1-8B, one call per sentence (DEC-031)

Crash-safe per-call cache (outputs/dec038_crossdoc/extractions/<arm>.jsonl),
parallel workers. Transient API failures (network, HTTP 408/429/5xx) are
re-requested on the next pass; unparsable model output is kept and never
re-requested (DEC-031 rule). HTTP 402 stops the run at once. Hard cost cap.

Usage: python -u -m scripts.dec038_extract --arm deepseek_document --max-cost 1.20
"""

from __future__ import annotations

import argparse
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.dec033_protocol import numbered
from src.extractors.openrouter_openie import extract_openie_triples

ARMS = {
    "deepseek_document": dict(model="deepseek/deepseek-v3.2", prompt="prompts/openie_docred_doc_v1.txt",
                              max_tokens=2048, unit="document"),
    "llama_sentence": dict(model="meta-llama/llama-3.1-8b-instruct", prompt="prompts/openie_docred_v1.txt",
                           max_tokens=1024, unit="sentence"),
}
ROOT = Path("outputs/dec038_crossdoc")
TRANSIENT = {408, 429, 500, 502, 503, 504, 520, 522, 524, 529}


def load_api_key() -> str:
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("OPENROUTER_API_KEY not set in .env")


def load_subset() -> list[dict]:
    ids = json.loads((ROOT / "doc_list.json").read_text(encoding="utf-8"))["doc_ids"]
    raw = {"dev": json.loads(Path("data/DocRED/dev.json").read_text(encoding="utf-8")),
           "train": json.loads(Path("data/DocRED/train_annotated.json").read_text(encoding="utf-8"))}
    docs = []
    for doc_id in ids:
        split, i = doc_id.split("_")
        d = raw[split][int(i)]
        docs.append({"doc_id": doc_id, "title": d["title"], "sentences": [" ".join(t) for t in d["sents"]]})
    return docs


def is_transient(rec: dict) -> bool:
    return rec.get("http_status") is None or rec.get("http_status") in TRANSIENT


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    ap.add_argument("--max-cost", type=float, required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--limit-docs", type=int, default=None)
    args = ap.parse_args()
    cfg = ARMS[args.arm]

    out = ROOT / "extractions" / f"{args.arm}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done, spent = set(), 0.0
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                spent += rec.get("cost_usd") or 0.0
                if not is_transient(rec):
                    done.add((rec["doc_id"], rec["unit_id"]))

    docs = load_subset()[: args.limit_docs]
    if cfg["unit"] == "document":
        units = [(d, 0, numbered(d)) for d in docs]
    else:
        units = [(d, i, s) for d in docs for i, s in enumerate(d["sentences"])]
    todo = [(d, u, t) for d, u, t in units if (d["doc_id"], u) not in done]
    print(f"{args.arm}: {len(units)} calls total, {len(done)} done (${spent:.4f} spent), "
          f"{len(todo)} to run, cap ${args.max_cost:.2f}", flush=True)

    template = Path(cfg["prompt"]).read_text(encoding="utf-8")
    api_key = load_api_key()
    lock = threading.Lock()
    state = {"spent": spent, "n": 0, "stop": None}

    def run(item):
        d, u, text = item
        with lock:
            if state["stop"]:
                return
            if state["spent"] >= args.max_cost:
                state["stop"] = f"cost cap ${args.max_cost:.2f} reached"
                return
        r = extract_openie_triples(text, api_key=api_key, model=cfg["model"], prompt_template=template,
                                   max_tokens=cfg["max_tokens"], keep_evidence=(cfg["unit"] == "document"))
        rec = {"doc_id": d["doc_id"], "unit_id": u, "triples": r["triples"], "error": r["error"],
               "http_status": r["http_status"], "cost_usd": r.get("cost_usd"),
               "latency_s": r.get("latency_s"), "network_retries": r.get("network_retries", 0)}
        with lock:
            if r["http_status"] == 402:
                state["stop"] = f"HTTP 402 (credits): {r['error']}"
                return
            with open(out, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            state["spent"] += r.get("cost_usd") or 0.0
            state["n"] += 1
            if state["n"] % 100 == 0:
                print(f"  {state['n']}/{len(todo)} calls, ${state['spent']:.4f} total", flush=True)

    with ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(run, todo))
    print(f"STOPPED: {state['stop']}" if state["stop"] else "DONE", f"{state['n']} calls this pass, "
          f"${state['spent']:.4f} total for {args.arm}", flush=True)


if __name__ == "__main__":
    main()
