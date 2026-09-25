"""DEC-032 offline analysis (zero API cost), exactly as pre-registered in
Decision log.md DEC-032. Reads outputs/dec032_biored/extractions/.

Reported FIRST, per model, before any aggregation result:
  - extractor recall (no aggregation, sentence level, primary evaluator);
  - extraction-level corroboration: G2 = gold facts the extractions
    recover from 2+ distinct sentences, as a share of all gold facts;
  - annotation-level corroboration, for contrast: gold facts whose two
    concepts are co-mentioned in 2+ sentences (and in 1+, the ceiling
    for sentence-level extraction);
  - rho = G2 share / annotation-level (2+) share;
  - share of extracted triples whose predicate is one of the 8 BioRED
    relation types.

Then, per model (sentence level): arms no aggregation, R2, R3 (key =
DEC-031's normalised key (b); tau 0.70, shrinkage 0.5), each with P/R/F1
under the primary (alias), strict and relaxed evaluators, admitted
count, contested slots (candidates / admitted) and documents admitting
anything. Whole-abstract extraction (the pilot's setting) is reported as
no aggregation only.

Paired bootstrap over documents (10,000 resamples, pooled counts
recomputed per resample, 95% percentile CI).

Usage: python -m scripts.dec032_biored_analyze [--extractions-dir DIR]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.dec031_docred import admitted_items, aggregate, contested_slots, prf
from src.dec032_biored import evaluate_doc, load_docs, matched_fact, valid_relation

EXTRACTIONS_DIR = Path("outputs/dec032_biored/extractions")
OUT_PATH = Path("outputs/dec032_biored/analysis_result.json")
N_BOOTSTRAP = 10_000
BOOT_SEED = 20320924
KEY = "norm"
EVALUATORS = ("alias", "strict", "relaxed")
MODELS = ("llama", "deepseek")
ARMS = ("naive", "R2", "R3")


def load_run(path: Path) -> tuple[dict[int, dict[int, list[dict]]], dict]:
    by_doc: dict[int, dict[int, list[dict]]] = defaultdict(dict)
    stats = {"records": 0, "network_failed": 0, "content_errors": 0, "cost_usd": 0.0}
    for f in sorted(path.glob("shard_*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                stats["truncated_lines"] = stats.get("truncated_lines", 0) + 1
                continue  # cut off when a process was stopped; the call was redone
            if rec["http_status"] is None:
                stats["network_failed"] += 1
                continue
            stats["records"] += 1
            stats["cost_usd"] += rec.get("cost_usd") or 0.0
            stats["content_errors"] += bool(rec["error"])
            by_doc[rec["doc_idx"]][rec["unit_id"]] = rec["triples"]
    return by_doc, stats


def doc_counts(doc: dict, unit_triples: dict[int, list[dict]], sentence_level: bool) -> dict:
    obs = [{"sent_id": u, "subject": t["subject"], "predicate": t["predicate"], "object": t["object"]}
           for u in sorted(unit_triples) for t in unit_triples[u]]
    raw = [(o["subject"], o["predicate"], o["object"]) for o in obs]
    sents = defaultdict(set)
    for o, it in zip(obs, raw):
        g = matched_fact(doc, it)
        if g is not None:
            sents[g].add(o["sent_id"])
    out = {"g2": sum(1 for s in sents.values() if len(s) >= 2),
           "n_triples": len(raw), "n_valid_rel": sum(valid_relation(p) for _, p, _ in raw)}
    arms = {"naive": (raw, None)}
    if sentence_level:
        for rule in ("R2", "R3"):
            cands = aggregate(obs, KEY, rule, {})
            arms[rule] = (admitted_items(cands), cands)
        c2 = aggregate(obs, KEY, "R2", {})
        out["within_sentence_dups"] = sum(c["n_obs"] - c["n_sents"] for c in c2.values())
    for arm, (items, cands) in arms.items():
        out[arm] = {ev: evaluate_doc(doc, items, ev) for ev in EVALUATORS}
        out[arm]["admitted"] = len(set(items))
        out[arm]["any"] = int(bool(items))
        out[arm]["contested_candidates"] = contested_slots(cands, False) if cands else 0
        out[arm]["contested_admitted"] = contested_slots(cands, True) if cands else 0
    return out


def boot(idx, fn):
    point = fn(np.arange(idx.shape[1]))
    vals = np.array([fn(ix) for ix in idx])
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return {"value": float(point), "ci95": [float(lo), float(hi)], "ci_excludes_zero": bool(lo > 0 or hi < 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractions-dir", type=Path, default=EXTRACTIONS_DIR)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    docs = load_docs()
    n_gold = sum(len(d["gold_facts"]) for d in docs)
    ann2 = sum(sum(1 for k in d["fact_sentence_comention"] if k >= 2) for d in docs)
    ann1 = sum(sum(1 for k in d["fact_sentence_comention"] if k >= 1) for d in docs)
    result = {"n_docs": len(docs), "n_sentences": sum(len(d["sentences"]) for d in docs),
              "n_gold_facts": n_gold,
              "annotation_comention_2plus_share": ann2 / n_gold,
              "annotation_comention_1plus_share": ann1 / n_gold, "models": {}}
    print(f"{len(docs)} docs, {result['n_sentences']} sentences, {n_gold} gold facts")
    print(f"annotation level: co-mentioned in 2+ sentences {100 * ann2 / n_gold:.1f}%, "
          f"in 1+ {100 * ann1 / n_gold:.1f}%")

    rng = np.random.default_rng(BOOT_SEED)
    for model in MODELS:
        res = {}
        for unit in ("sentence", "abstract"):
            path = args.extractions_dir / f"{model}_{unit}"
            if not path.exists():
                continue
            by_doc, stats = load_run(path)
            n_units = {d["doc_idx"]: (len(d["sentences"]) if unit == "sentence" else 1) for d in docs}
            complete = [d for d in docs if len(by_doc.get(d["doc_idx"], {})) == n_units[d["doc_idx"]]]
            counts = [doc_counts(d, by_doc[d["doc_idx"]], unit == "sentence") for d in complete]
            idx = rng.integers(0, len(complete), size=(N_BOOTSTRAP, len(complete)))
            gold_c = np.array([len(d["gold_facts"]) for d in complete])

            def arr(arm, ev, f):
                return np.array([c[arm][ev][f] for c in counts])

            def f1(arm, ev="alias", metric="f1"):
                tp, fp, fn = arr(arm, ev, "tp"), arr(arm, ev, "fp"), arr(arm, ev, "fn")
                return lambda ix: prf(tp[ix].sum(), fp[ix].sum(), fn[ix].sum())[metric]

            arms_here = ARMS if unit == "sentence" else ("naive",)
            summary = {}
            for arm in arms_here:
                summary[arm] = {ev: prf(*(int(arr(arm, ev, f).sum()) for f in ("tp", "fp", "fn")))
                                for ev in EVALUATORS}
                for k in ("admitted", "any", "contested_candidates", "contested_admitted"):
                    summary[arm][k] = sum(c[arm][k] for c in counts)
            g2 = np.array([c["g2"] for c in counts])
            first = {
                "extractor_recall": summary["naive"]["alias"]["recall"],
                "g2_facts": int(g2.sum()),
                "g2_share": boot(idx, lambda ix: g2[ix].sum() / gold_c[ix].sum()),
                "valid_relation_share": sum(c["n_valid_rel"] for c in counts) / max(1, sum(c["n_triples"] for c in counts)),
            }
            first["rho_g2_over_annotation"] = first["g2_share"]["value"] / result["annotation_comention_2plus_share"]
            comps = {}
            if unit == "sentence":
                first["within_sentence_duplicate_observations"] = sum(c["within_sentence_dups"] for c in counts)
                comps["R2_vs_naive_F1"] = boot(idx, lambda ix: f1("R2")(ix) - f1("naive")(ix))
                comps["R3_vs_naive_F1"] = boot(idx, lambda ix: f1("R3")(ix) - f1("naive")(ix))
                comps["R3_vs_R2_F1 (PRIMARY R3)"] = boot(idx, lambda ix: f1("R3")(ix) - f1("R2")(ix))
                comps["R3_vs_R2_precision (secondary)"] = boot(
                    idx, lambda ix: f1("R3", metric="precision")(ix) - f1("R2", metric="precision")(ix))
            res[unit] = {"docs_complete": len(complete), "extraction": stats,
                         "measured_first": first, "arms": summary, "comparisons": comps}

            print(f"\n===== {model} / {unit}: {len(complete)}/{len(docs)} docs complete, "
                  f"{stats['records']} calls, {stats['content_errors']} unparsable, ${stats['cost_usd']:.4f}")
            print(f"  FIRST: extractor recall {first['extractor_recall']:.4f} | G2 {first['g2_facts']} "
                  f"= {100 * first['g2_share']['value']:.2f}% {first['g2_share']['ci95']} | rho "
                  f"{first['rho_g2_over_annotation']:.3f} | valid relation {100 * first['valid_relation_share']:.1f}%"
                  + (f" | within-sentence dups {first['within_sentence_duplicate_observations']}"
                     if unit == "sentence" else ""))
            for arm in arms_here:
                s = summary[arm]
                print(f"  {arm:>5}: " + " | ".join(
                    f"{ev} P={s[ev]['precision']:.4f} R={s[ev]['recall']:.4f} F1={s[ev]['f1']:.4f}"
                    for ev in EVALUATORS)
                    + f" | adm={s['admitted']} docs_any={s['any']} contested={s['contested_candidates']}/{s['contested_admitted']}")
            for k, v in comps.items():
                print(f"  {k}: {v['value']:+.4f} [{v['ci95'][0]:+.4f}, {v['ci95'][1]:+.4f}]")
        result["models"][model] = res

    if all(m in result["models"] and "sentence" in result["models"][m] for m in MODELS):
        result["baseline_note"] = "DeepSeek vs Llama comparisons are descriptive (same prompt, same sentences)."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nSaved {args.out}")


if __name__ == "__main__":
    main()
