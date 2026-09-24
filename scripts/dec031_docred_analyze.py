"""DEC-031 offline analysis (zero API cost). Reads every
outputs/dec031_docred/extractions/shard_*.jsonl and computes, exactly as
pre-registered in Decision log.md DEC-031:

Settings: "all" (every sentence; PRIMARY) and "evidence" (only gold
evidence sentences -- DEC-020's oracle setting, for comparability with
the pilot only).

Methods per setting: naive (no aggregation: every extracted item) and
PKB with key in {exact, norm, alias(ORACLE)} x rule in {R2, R3}.

Per method: P/R/F1 under the primary (alias-aware) evaluator and the
secondary DEC-020 first-mention evaluator; admitted item count;
contested slots among all candidates and among admitted; number of
documents where anything was admitted.

Diagnostics: G2 = gold facts that the raw extractions recover from 2+
distinct sentences (what aggregation could corroborate); pooled rate =
share of G2 facts recovered by an admitted item; within-sentence
duplicate observations per key (if 0, R3 == R2 by construction).

Paired bootstrap over documents (10,000 resamples, pooled counts
recomputed per resample, [2.5, 97.5] percentile CI) for the
pre-registered comparisons.

Usage: python -m scripts.dec031_docred_analyze [--extractions-dir DIR]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.dec031_docred import (KEYS, RULES, admitted_items, aggregate, alias_index,
                               contested_slots, evaluate_doc, evaluate_doc_first_mention,
                               gold_matcher, load_docs, prf)

EXTRACTIONS_DIR = Path("outputs/dec031_docred/extractions")
OUT_PATH = Path("outputs/dec031_docred/analysis_result.json")
N_BOOTSTRAP = 10_000
BOOT_SEED = 20310924
SETTINGS = ("all", "evidence")
METHODS = ["naive"] + [f"{k}_{r}" for k in KEYS for r in RULES]

# (label, method_a, method_b, metric): the difference reported is b - a.
COMPARISONS = [
    ("PRIMARY matching key: norm vs exact (R2), F1", "exact_R2", "norm_R2", "f1"),
    ("norm vs exact (R2), recall", "exact_R2", "norm_R2", "recall"),
    ("norm vs exact (R2), pooled rate on G2", "exact_R2", "norm_R2", "pooled"),
    ("ORACLE alias vs exact (R2), F1", "exact_R2", "alias_R2", "f1"),
    ("ORACLE alias vs exact (R2), pooled rate on G2", "exact_R2", "alias_R2", "pooled"),
    ("exact (R2) vs naive, F1", "naive", "exact_R2", "f1"),
    ("norm (R2) vs naive, F1", "naive", "norm_R2", "f1"),
    ("ORACLE alias (R2) vs naive, F1", "naive", "alias_R2", "f1"),
    ("PRIMARY R3 vs R2 (norm key), F1", "norm_R2", "norm_R3", "f1"),
    ("R3 vs R2 (exact key), F1", "exact_R2", "exact_R3", "f1"),
    ("R3 vs R2 (ORACLE alias key), F1", "alias_R2", "alias_R3", "f1"),
]


def load_extractions(ext_dir: Path) -> tuple[dict[int, dict[int, list[dict]]], dict]:
    by_doc: dict[int, dict[int, list[dict]]] = defaultdict(dict)
    stats = {"records": 0, "network_failed": 0, "content_errors": 0, "cost_usd": 0.0}
    for path in sorted(ext_dir.glob("shard_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["http_status"] is None:
                stats["network_failed"] += 1
                continue
            stats["records"] += 1
            stats["cost_usd"] += rec.get("cost_usd") or 0.0
            if rec["error"]:
                stats["content_errors"] += 1
            by_doc[rec["doc_idx"]][rec["sent_id"]] = rec["triples"]
    return by_doc, stats


def per_doc_counts(doc: dict, sent_triples: dict[int, list[dict]], setting: str) -> dict:
    sent_ids = sorted(sent_triples) if setting == "all" else [
        s for s in doc["evidence_sent_ids"] if s in sent_triples]
    obs = [{"sent_id": s, "subject": t["subject"], "predicate": t["predicate"], "object": t["object"]}
           for s in sent_ids for t in sent_triples[s]]
    aliases = alias_index(doc)
    match = gold_matcher(doc)

    # G2: gold facts recovered by raw extractions from 2+ distinct sentences
    sents_per_fact = defaultdict(set)
    for o in obs:
        g = match((o["subject"], o["predicate"], o["object"]))
        if g is not None:
            sents_per_fact[g].add(o["sent_id"])
    g2 = {g for g, s in sents_per_fact.items() if len(s) >= 2}

    out = {}
    raw_items = [(o["subject"], o["predicate"], o["object"]) for o in obs]
    out["naive"] = {**evaluate_doc(doc, raw_items),
                    "sec": evaluate_doc_first_mention(doc, raw_items),
                    "admitted": len(set(raw_items)), "any": int(bool(raw_items)),
                    "contested_all": 0, "contested_admitted": 0,
                    "g2": len(g2), "pooled": len(g2 & {match(i) for i in raw_items})}
    for key in KEYS:
        dup = 0
        for rule in RULES:
            cands = aggregate(obs, key, rule, aliases)
            items = admitted_items(cands)
            matched = {match(i) for i in items}
            out[f"{key}_{rule}"] = {
                **evaluate_doc(doc, items),
                "sec": evaluate_doc_first_mention(doc, items),
                "admitted": len(items), "any": int(bool(items)),
                "contested_all": contested_slots(cands, admitted_only=False),
                "contested_admitted": contested_slots(cands, admitted_only=True),
                "g2": len(g2), "pooled": len(g2 & matched),
            }
            if rule == "R2":
                dup = sum(c["n_obs"] - c["n_sents"] for c in cands.values())
        out[f"{key}_R2"]["within_sentence_dups"] = dup
    return out


def metric_from_sums(s: dict, metric: str) -> float:
    if metric == "pooled":
        return s["pooled"] / s["g2"] if s["g2"] else 0.0
    return prf(s["tp"], s["fp"], s["fn"])[metric]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extractions-dir", type=Path, default=EXTRACTIONS_DIR)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    docs = load_docs()
    by_doc, stats = load_extractions(args.extractions_dir)
    complete = [d for d in docs if len(by_doc.get(d["doc_idx"], {})) == len(d["sentences"])]
    print(f"extraction records: {stats['records']} (content errors {stats['content_errors']}, "
          f"network-failed {stats['network_failed']}), cost ${stats['cost_usd']:.4f}")
    print(f"documents with every sentence extracted: {len(complete)}/{len(docs)}")
    result = {"n_docs_total": len(docs), "n_docs_complete": len(complete), "extraction": stats,
              "settings": {}}

    rng = np.random.default_rng(BOOT_SEED)
    idx = rng.integers(0, len(complete), size=(N_BOOTSTRAP, len(complete)))

    for setting in SETTINGS:
        counts = [per_doc_counts(d, by_doc[d["doc_idx"]], setting) for d in complete]
        arr = {m: {f: np.array([c[m][f] for c in counts]) for f in ("tp", "fp", "fn", "g2", "pooled")}
               for m in METHODS}
        summary = {}
        for m in METHODS:
            sums = {f: int(v.sum()) for f, v in arr[m].items()}
            sec = {f: sum(c[m]["sec"][f] for c in counts) for f in ("tp", "fp", "fn")}
            summary[m] = {
                "primary": prf(sums["tp"], sums["fp"], sums["fn"]),
                "secondary_first_mention": prf(sec["tp"], sec["fp"], sec["fn"]),
                "admitted": sum(c[m]["admitted"] for c in counts),
                "docs_with_any_admitted": sum(c[m]["any"] for c in counts),
                "contested_slots_candidates": sum(c[m]["contested_all"] for c in counts),
                "contested_slots_admitted": sum(c[m]["contested_admitted"] for c in counts),
                "g2_facts": sums["g2"], "g2_pooled": sums["pooled"],
                "pooled_rate": metric_from_sums(sums, "pooled"),
            }
            if "within_sentence_dups" in counts[0][m]:
                summary[m]["within_sentence_duplicate_observations"] = sum(
                    c[m]["within_sentence_dups"] for c in counts)

        comps = []
        for label, a, b, metric in COMPARISONS:
            def stat(ix):
                sa = {f: arr[a][f][ix].sum() for f in arr[a]}
                sb = {f: arr[b][f][ix].sum() for f in arr[b]}
                return metric_from_sums(sb, metric) - metric_from_sums(sa, metric)
            point = stat(np.arange(len(complete)))
            boots = np.array([stat(ix) for ix in idx])
            lo, hi = np.percentile(boots, [2.5, 97.5])
            comps.append({"comparison": label, "a": a, "b": b, "metric": metric,
                          "diff": float(point), "ci95": [float(lo), float(hi)],
                          "ci_excludes_zero": bool(lo > 0 or hi < 0)})

        f1 = {m: summary[m]["primary"]["f1"] for m in METHODS}
        gap = f1["naive"] - f1["exact_R2"]
        gap_closed = {k: ((f1[f"{k}_R2"] - f1["exact_R2"]) / gap if gap > 0 else None)
                      for k in ("norm", "alias")}
        result["settings"][setting] = {"methods": summary, "comparisons": comps,
                                       "share_of_naive_gap_closed_R2": gap_closed}

        print(f"\n===== setting: {setting} =====")
        for m in METHODS:
            s = summary[m]
            print(f"{m:>9}: P={s['primary']['precision']:.4f} R={s['primary']['recall']:.4f} "
                  f"F1={s['primary']['f1']:.4f} | adm={s['admitted']} docs_any={s['docs_with_any_admitted']} "
                  f"contested cand/adm={s['contested_slots_candidates']}/{s['contested_slots_admitted']} "
                  f"pooled={s['g2_pooled']}/{s['g2_facts']} | 1st-mention F1={s['secondary_first_mention']['f1']:.4f}")
        for c in comps:
            print(f"  {c['comparison']}: {c['diff']:+.4f} [{c['ci95'][0]:+.4f}, {c['ci95'][1]:+.4f}]")
        print(f"  share of naive-vs-exact F1 gap closed (R2): {gap_closed}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\nSaved {args.out}")


if __name__ == "__main__":
    main()
