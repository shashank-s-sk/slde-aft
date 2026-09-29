"""DEC-035b Step A -- internal go/no-go (NOT for the paper): does counting
repeated observations change DySECT's own KB-guided DocRED recall?

Reproduces DySECT's released protocol (megagonlabs/dysect @ 8d6c680,
extract_with_kb_fireworks.py + llm-extractor/scripts/eval_dysect.py), with
Llama-3.3-70B as the extractor and gpt-4.1-mini as the judge, both via
OpenRouter:

  arm a  base:      add_triples, iteration 0 (no added info)
  arm b  kb_orig:   add_kb_info (Positive), the table's "Iter-1": concepts
                    whose stored overall confidence >= 0.5 in DySECT's
                    released KB (repeat counting, as published)
  arm c  kb_dedup:  identical, but each generalization edge rescored with one
                    observation per (source, document)

Documents: DySECT's 500 "dev" docs (data_prep.py: train_annotated.json,
random.seed(1), first 500). The judge scores base+arm triples per document
(their cumulative evaluation). Gold = DocRED labels as (head, relation, tail).

Pre-registered outcome (Decision log.md, DEC-035b, commit 2f3a731):
|recall_b - recall_c| >= 2.0 pp is "meaningful"; paired per-document
bootstrap 95% CI. Primary recall = mean per-document recall (their
`average_recall`); macro recall reported alongside.

Usage: python -m scripts.dec035b_dysect_stepA <dysect repo dir> <extracted kb dir>
"""

from __future__ import annotations

import json
import random
import re
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dec035_dysect_kb_audit import cnor, leaf_paths, source_doc  # noqa: E402

EXTRACTOR = "meta-llama/llama-3.3-70b-instruct"
JUDGE = "openai/gpt-4.1-mini"
N_DOCS = 500
ADMIT = 0.5
BUDGET_USD = 6.0
N_BOOT = 10_000
OUT = Path("outputs/dec035b_stepA")

SYSTEM_PROMPT = """
You are an information extraction agent designed to improve across iterations.

Your goal is to progressively increase recall while maintaining strict precision.

At each iteration:
- You are given:
  (a) the document text
  (b) previously extracted triples
  (c) optional additional guidance from earlier iterations
- You MUST treat previously extracted triples as already known facts.
- You MUST NOT repeat previously extracted triples.
- You SHOULD look for:
    • relations that were missed earlier
    • entities that were previously unseen
    • new relations involving known entities
    • implicit but explicitly stated facts that can be expressed independently

You must NOT hallucinate, infer unstated facts, or relax schema constraints.
You must obey the allowed concept types, relations, and output format exactly.

Your objective is to extract ONLY new, valid triples that increase coverage of the document.
"""  # verbatim from extract_with_kb_fireworks.py

_cost = 0.0
_lock = threading.Lock()


def api_key() -> str:
    for line in open(".env", encoding="utf-8"):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("OPENROUTER_API_KEY not set")


def chat(model: str, messages: list, key: str) -> str:
    global _cost
    for attempt in range(5):
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "temperature": 0.0,
                      "max_tokens": 6000, "usage": {"include": True}},
                timeout=300,
            ).json()
            if "choices" not in r and (r.get("error") or {}).get("code") == 402:
                raise SystemExit(f"OpenRouter 402 (credits): {r['error'].get('message')}")
            out = r["choices"][0]["message"]["content"] or ""
            with _lock:
                _cost += float(r.get("usage", {}).get("cost") or 0.0)
                if _cost > BUDGET_USD:
                    raise SystemExit(f"budget guard: spent ${_cost:.2f} > ${BUDGET_USD}")
            return out
        except SystemExit:
            raise
        except Exception as e:  # retry like DySECT's generate_text
            print(f"  retry {attempt + 1}: {e}")
    return "Error"


# ---------------------------------------------------------------- data ---

def load_docs(rel_map: dict) -> list[dict]:
    data = json.load(open("data/DocRED/train_annotated.json", encoding="utf-8"))
    random.seed(1)
    random.shuffle(data)
    docs = []
    for i, ex in enumerate(data[:N_DOCS]):
        text = " ".join(" ".join(s) for s in ex["sents"])
        vs = ex["vertexSet"]
        gold = [[vs[lab["h"]][0]["name"], rel_map.get(lab["r"], lab["r"]), vs[lab["t"]][0]["name"]]
                for lab in ex.get("labels", [])]
        docs.append({"doc_id": f"doc_{i}", "text": text, "gold": gold})
    return docs


def parse_rows(out: str) -> list:
    try:
        rows = json.loads(out.strip("`").strip())
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def triples(rows: list) -> set:
    t = set()
    for line in rows:
        if isinstance(line, list) and len(line) == 5:
            t.add((str(line[0]), str(line[2]), str(line[3])))
        elif isinstance(line, list) and len(line) == 3:
            t.add(tuple(str(x) for x in line))
    return t


# ------------------------------------------------------------------ KB ---

def canonical(s: str) -> str:
    c = unicodedata.normalize("NFKC", s)[:200]
    c = re.sub(r"[^\w\s-]", "", c.lower())
    return re.sub(r"[-\s]+", "_", c).strip("-_").replace("\t", "").replace("\n", "")


def kb_generalizations(kb: Path, entity: str):
    c = canonical(entity.split("||")[0])[:200]
    if not c:
        return None
    path = kb.joinpath(*list(c[:5])) / f"{c}.json"
    if not path.is_file():
        return None
    return json.load(open(path, encoding="utf-8")).get("generalizations")


def concept_conf(node: dict, dedup: bool) -> float:
    oc = node.get("overall confidence", {"0": 0})
    stored = float(next(iter(oc)))
    if not dedup or stored == 1.0:
        return stored
    best = {}
    for t, c, _ in leaf_paths(node, [], []):
        key = source_doc(t)
        best[key] = max(best.get(key, 0.0), float(c))
    return float(cnor(best.values())) if best else stored


def kb_concepts(kb: Path, base_rows: list, dedup: bool) -> set:
    ents = {str(r[0]) for r in base_rows if isinstance(r, list) and len(r) >= 4} | \
           {str(r[3]) for r in base_rows if isinstance(r, list) and len(r) >= 4}
    out = set()
    for e in ents:
        gens = kb_generalizations(kb, e)
        if not gens:
            continue
        for concept, node in gens.items():
            if concept == "Everything" or not isinstance(node, dict):
                continue
            if concept_conf(node, dedup) >= ADMIT:
                out.add(concept)
    return out


# ---------------------------------------------------------------- judge --

def judge_prompt(extracted: list, gold: list) -> str:  # verbatim from eval_dysect.llm_judge
    return (
        "You are required to annotate the response generated by an AI model for information extraction task. "
        "You are given the human annotated gold triples and the AI model extracted triples. "
        "Identify which one of the AI predicted triples are correct in comparison to the gold triples. "
        "Generate the response in JSON format using the keys below, and provide each key's output as a list of triples: "
        "1. true_pos: correctly_predicted_triples "
        "2. false_pos: incorrectly_predicted_triples "
        "3. false_neg: missed_triples "
        "Rules **MUST FOLLOW**:"
        "* If the entities are partially matching consider them a match"
        "* If the entity types mentioned in the relation section does not match, consider them a correct match"
        "* Consider reverse relations as match e.g. A->is_father_of->B then B->is_son_of->A"
        f"GOLD TRIPLES: {json.dumps(gold, ensure_ascii=False)} "
        f"AI PREDICTED Triples: {json.dumps(extracted, ensure_ascii=False)} "
        "Output only the JSON."
    )


def judge(extracted: set, gold: list, key: str) -> dict:
    out = chat(JUDGE, [{"role": "user", "content": judge_prompt([list(t) for t in extracted], gold)}], key)
    out = re.sub(r"^```[a-zA-Z0-9]*\s*", "", out)
    out = re.sub(r"```$", "", out).strip()
    try:
        res = json.loads(out)
    except Exception:
        res = {}
    tp, fp, fn = (len(res.get(k, [])) for k in ("true_pos", "false_pos", "false_neg"))
    return {"TP": tp, "FP": fp, "FN": fn, "recall": tp / (tp + fn) if tp + fn else 0.0,
            "n_extracted": len(extracted), "judge_parse_ok": bool(res)}


# ----------------------------------------------------------------- main --

def main() -> None:
    repo, kb = Path(sys.argv[1]), Path(sys.argv[2])
    key = api_key()
    prompt_tmpl = (repo / "llm-extractor/configs/domains/docred/prompt_base_v1_5_positive.txt").read_text(encoding="utf-8")
    rel_map = json.load(open("data/DocRED/rel_info.json", encoding="utf-8"))
    docs = load_docs(rel_map)
    OUT.mkdir(parents=True, exist_ok=True)

    def extract(doc, added_info):
        p = prompt_tmpl.format(document=doc["text"], example="", added_info=added_info)
        return chat(EXTRACTOR, [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": p}], key)

    def per_doc(doc):
        cache = OUT / f"{doc['doc_id']}.json"
        if cache.exists():
            return json.load(open(cache, encoding="utf-8"))
        base_out = extract(doc, "")
        base_rows = parse_rows(base_out)
        rec = {"doc_id": doc["doc_id"], "base_raw": base_out}
        base_t = triples(base_rows)
        rec["base"] = judge(base_t, doc["gold"], key)
        for arm, dedup in (("kb_orig", False), ("kb_dedup", True)):
            concepts = sorted(kb_concepts(kb, base_rows, dedup))
            rec[f"{arm}_concepts"] = concepts
            added = f"### Previously Extracted General Concepts:\n{', '.join(concepts)}\n" if concepts else ""
            if arm == "kb_dedup" and concepts == rec["kb_orig_concepts"]:
                rec[arm] = dict(rec["kb_orig"], identical_prompt=True)  # same prompt, temperature 0: reuse
                rec[f"{arm}_raw"] = rec["kb_orig_raw"]
                continue
            out = extract(doc, added)
            rec[f"{arm}_raw"] = out
            rec[arm] = judge(base_t | triples(parse_rows(out)), doc["gold"], key)
        json.dump(rec, open(cache, "w", encoding="utf-8"), indent=1)
        print(f"{doc['doc_id']}: base R={rec['base']['recall']:.3f} orig R={rec['kb_orig']['recall']:.3f} "
              f"dedup R={rec['kb_dedup']['recall']:.3f} | spent ${_cost:.3f}")
        return rec

    with ThreadPoolExecutor(24) as ex:
        recs = list(ex.map(per_doc, docs))

    arms = ("base", "kb_orig", "kb_dedup")
    summary = {"n_docs": len(recs), "extractor": EXTRACTOR, "judge": JUDGE, "cost_usd_this_session": _cost}
    for a in arms:
        tp = sum(r[a]["TP"] for r in recs)
        fn = sum(r[a]["FN"] for r in recs)
        summary[a] = {"mean_doc_recall": float(np.mean([r[a]["recall"] for r in recs])),
                      "macro_recall": tp / (tp + fn) if tp + fn else 0.0,
                      "avg_extracted": float(np.mean([r[a]["n_extracted"] for r in recs])),
                      "judge_parse_failures": sum(not r[a]["judge_parse_ok"] for r in recs)}
    d = np.array([r["kb_orig"]["recall"] - r["kb_dedup"]["recall"] for r in recs])
    rng = np.random.default_rng(12345)
    boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(N_BOOT)]
    summary["orig_minus_dedup_pp"] = {"mean": float(d.mean() * 100),
                                      "ci95": [float(np.percentile(boots, 2.5) * 100), float(np.percentile(boots, 97.5) * 100)]}
    summary["docs_with_identical_prompt"] = sum(bool(r["kb_dedup"].get("identical_prompt")) for r in recs)
    summary["meaningful_ge_2pp"] = bool(abs(d.mean() * 100) >= 2.0)
    json.dump(summary, open(OUT / "summary.json", "w", encoding="utf-8"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
