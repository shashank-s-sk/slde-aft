"""DEC-038 offline analysis (zero API cost), exactly as pre-registered in
Decision log.md DEC-038 (commit f87e91a).

Corpus-level KB over the 2,010-document DocRED redundancy subset; source =
document. Methods: naive, R2 (all observations), R3-doc (distinct
documents, primary), R3-unit (distinct (document, sentence) units). DEC-031
score 1 - 0.5^n admitted at tau = 0.70, `norm` matching key. Observations
follow DEC-033: a document-level triple yields one observation per cited
valid sentence (or one document-level observation if it cites none).

Every metric is computed per stratum (GEO / OTHER), never pooled.

Usage: python -m scripts.dec038_analyze
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from src.dec031_docred import SHRINKAGE, TAU, normalize_b, predicate_key

ROOT = Path("outputs/dec038_crossdoc")
ARMS = ["deepseek_document", "llama_sentence"]
GEO = {"country", "located in the administrative territorial entity", "contains administrative territorial entity"}
METHODS = ["naive", "R2", "R3_doc", "R3_unit"]
N_BOOT, SEED = 10_000, 20380929
N_HALF = 1_000
DOC_SOURCE = -1


def stratum(rel: str) -> str:
    return "GEO" if rel in GEO else "OTHER"


def admitted(n: int) -> bool:
    return 1.0 - (1.0 - SHRINKAGE) ** n >= TAU - 1e-12


def wilson(k: int, n: int) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p, z = k / n, 1.96
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [c - h, c + h]


def load_gold():
    ids = json.loads((ROOT / "doc_list.json").read_text(encoding="utf-8"))["doc_ids"]
    rel_map = json.loads(Path("data/DocRED/rel_info.json").read_text(encoding="utf-8"))
    raw = {"dev": json.loads(Path("data/DocRED/dev.json").read_text(encoding="utf-8")),
           "train": json.loads(Path("data/DocRED/train_annotated.json").read_text(encoding="utf-8"))}
    alias = defaultdict(set)          # normalised mention -> first-mention names H
    fact_docs = defaultdict(set)      # (H, r, T) -> doc ids
    n_sent = {}
    for doc_id in ids:
        split, i = doc_id.split("_")
        d = raw[split][int(i)]
        n_sent[doc_id] = len(d["sents"])
        first = [normalize_b(ent[0]["name"]) for ent in d["vertexSet"]]
        for ent, h in zip(d["vertexSet"], first):
            for m in ent:
                alias[normalize_b(m["name"])].add(h)
        for lab in d["labels"]:
            fact_docs[(first[lab["h"]], rel_map.get(lab["r"], lab["r"]), first[lab["t"]])].add(doc_id)
    return ids, alias, fact_docs, n_sent


def load_observations(arm: str, n_sent: dict) -> tuple[list[tuple], dict]:
    """[(key, doc_id, unit)], plus call statistics."""
    obs, stats = [], defaultdict(int)
    seen = {}
    for line in (ROOT / "extractions" / f"{arm}.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            seen[(rec["doc_id"], rec["unit_id"])] = rec   # last record per unit wins (re-requests)
    for (doc_id, uid), rec in seen.items():
        stats["calls"] += 1
        stats["errors"] += bool(rec["error"])
        stats["cost_usd"] += rec.get("cost_usd") or 0.0
        for t in rec["triples"] or []:
            key = (normalize_b(t["subject"]), predicate_key(t["predicate"], "norm"), normalize_b(t["object"]))
            if arm.endswith("sentence"):
                obs.append((key, doc_id, uid))
            else:
                cited = [e for e in (t.get("evidence") or []) if isinstance(e, int) and 0 <= e < n_sent[doc_id]]
                for e in (cited or [DOC_SOURCE]):
                    obs.append((key, doc_id, e))
    return obs, dict(stats)


def analyse_arm(arm, ids, alias, fact_docs, n_sent):
    obs, stats = load_observations(arm, n_sent)
    gold = list(fact_docs)
    gold_idx = {g: i for i, g in enumerate(gold)}
    by_rel_pair = defaultdict(list)
    for g in gold:
        by_rel_pair[g[1]].append(g)
    gold_by_ht = defaultdict(list)
    for g in gold:
        gold_by_ht[(g[0], g[1], g[2])].append(gold_idx[g])

    def matches(key):
        s, p, o = key
        return sorted({gold_idx[(h, p, t)] for h in alias.get(s, ()) for t in alias.get(o, ())
                       if (h, p, t) in gold_idx})

    cands = {}
    for key, doc_id, unit in obs:
        c = cands.setdefault(key, {"n_obs": 0, "docs": set(), "units": set()})
        c["n_obs"] += 1
        c["docs"].add(doc_id)
        c["units"].add((doc_id, unit))
    keys = list(cands)
    match = [matches(k) for k in keys]
    adm = {"naive": np.ones(len(keys), bool),
           "R2": np.array([admitted(cands[k]["n_obs"]) for k in keys]),
           "R3_doc": np.array([admitted(len(cands[k]["docs"])) for k in keys]),
           "R3_unit": np.array([admitted(len(cands[k]["units"])) for k in keys])}
    cstrat = np.array([stratum(k[1]) for k in keys])
    gstrat = np.array([stratum(g[1]) for g in gold])
    gdocs = np.array([len(fact_docs[g]) for g in gold])

    # P1: realised cross-document corroboration of G_rec, from raw extractions
    docs_per_gold = defaultdict(set)
    for k, m in zip(keys, match):
        for gi in m:
            docs_per_gold[gi] |= cands[k]["docs"]
    result = {"calls": stats, "n_observations": len(obs), "n_candidate_keys": len(keys), "strata": {}}

    # units for the paired bootstrap: one per gold fact (with its matching
    # candidates) + one per candidate matching no gold fact
    owner = {}
    for ci, m in enumerate(match):
        if m:
            owner[ci] = m[0]
    gold_cands = defaultdict(list)
    for ci, gi in owner.items():
        gold_cands[gi].append(ci)

    for S in ("GEO", "OTHER"):
        gmask = gstrat == S
        n_gold = int(gmask.sum())
        rec_ids = [gi for gi in np.flatnonzero(gmask) if gdocs[gi] >= 2]
        k2 = sum(len(docs_per_gold[gi]) >= 2 for gi in rec_ids)
        k1 = sum(len(docs_per_gold[gi]) >= 1 for gi in rec_ids)
        out = {"gold_facts": n_gold, "G_rec": len(rec_ids),
               "P1_G_rec_recovered_from_2plus_docs": {"k": k2, "rate": k2 / len(rec_ids) if rec_ids else 0.0,
                                                      "wilson95": wilson(k2, len(rec_ids))},
               "G_rec_recovered_from_1plus_docs": {"k": k1, "rate": k1 / len(rec_ids) if rec_ids else 0.0},
               "methods": {}, "recall_on_G_rec_by_n_docs": {}}
        # unit arrays
        units_adm = {m: [] for m in METHODS}
        units_tpc = {m: [] for m in METHODS}
        units_tpg = {m: [] for m in METHODS}
        for gi in np.flatnonzero(gmask):
            cl = gold_cands.get(gi, [])
            for m in METHODS:
                a = [ci for ci in cl if adm[m][ci]]
                units_adm[m].append(len(a))
                units_tpc[m].append(len(a))
                units_tpg[m].append(1 if a else 0)
        fp_c = [ci for ci in range(len(keys)) if ci not in owner and cstrat[ci] == S]
        for ci in fp_c:
            for m in METHODS:
                units_adm[m].append(int(adm[m][ci]))
                units_tpc[m].append(0)
                units_tpg[m].append(0)
        isg = np.array([1] * n_gold + [0] * len(fp_c))
        A = {m: np.array(units_adm[m], float) for m in METHODS}
        TC = {m: np.array(units_tpc[m], float) for m in METHODS}
        TG = {m: np.array(units_tpg[m], float) for m in METHODS}

        def prf(w):
            res = {}
            ng = (w * isg).sum()
            for m in METHODS:
                a, tc, tg = (w * A[m]).sum(), (w * TC[m]).sum(), (w * TG[m]).sum()
                p = tc / a if a else 0.0
                r = tg / ng if ng else 0.0
                res[m] = (p, r, 2 * p * r / (p + r) if p + r else 0.0)
            return res

        full = prf(np.ones(len(isg)))
        # multi-matching candidates are counted once as TP under their owner;
        # admitted-key precision recomputed exactly for the headline numbers
        for m in METHODS:
            sel = [ci for ci in range(len(keys)) if cstrat[ci] == S and adm[m][ci]]
            tp = sum(1 for ci in sel if match[ci] and stratum(gold[match[ci][0]][1]) == S)
            p = tp / len(sel) if sel else 0.0
            r = full[m][1]
            out["methods"][m] = {"admitted_keys": len(sel), "tp_keys": tp, "precision": p, "recall": r,
                                 "f1": 2 * p * r / (p + r) if p + r else 0.0}
        rng = np.random.default_rng(SEED)
        comps = [("P2_F1_R3doc_minus_naive", "R3_doc", "naive", 2), ("P3_precision_R3doc_minus_naive", "R3_doc", "naive", 0),
                 ("precision_R3doc_minus_R2", "R3_doc", "R2", 0), ("F1_R3doc_minus_R2", "R3_doc", "R2", 2),
                 ("F1_R3unit_minus_naive", "R3_unit", "naive", 2), ("precision_R3doc_minus_R3unit", "R3_doc", "R3_unit", 0)]
        boots = {c[0]: [] for c in comps}
        N = len(isg)
        for _ in range(N_BOOT):
            w = np.bincount(rng.integers(0, N, N), minlength=N).astype(float)
            r_ = prf(w)
            for name, a, b, j in comps:
                boots[name].append(r_[a][j] - r_[b][j])
        out["bootstrap_fact_keys"] = {}
        for name, a, b, j in comps:
            arr = np.array(boots[name])
            out["bootstrap_fact_keys"][name] = {
                "diff_full_sample": full[a][j] - full[b][j],
                "ci95": [float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))],
                "excludes_zero": bool(np.percentile(arr, 2.5) > 0 or np.percentile(arr, 97.5) < 0)}
        for label, lo, hi in (("2", 2, 2), ("3", 3, 3), ("4", 4, 4), ("5+", 5, 10 ** 9)):
            sel = [gi for gi in rec_ids if lo <= gdocs[gi] <= hi]
            row = {"n": len(sel)}
            for m in METHODS:
                hit = sum(1 for gi in sel if any(adm[m][ci] for ci in gold_cands.get(gi, [])))
                row[m] = hit / len(sel) if sel else 0.0
            out["recall_on_G_rec_by_n_docs"][label] = row
        result["strata"][S] = out
    result["_internal"] = (keys, cands, match, adm, cstrat, gold, gstrat, fact_docs)
    return result


def half_sampling(res, ids):
    """Secondary robustness: 1,000 draws of 50% of documents, full
    re-aggregation per draw. Reported both as pre-registered (deviations
    scaled by 1/sqrt(2)) and unscaled (a half-sample without replacement
    already has roughly the full-sample variance), labelled."""
    keys, cands, match, adm, cstrat, gold, gstrat, fact_docs = res["_internal"]
    doc_pos = {d: i for i, d in enumerate(ids)}
    cand_docs = [np.array(sorted(doc_pos[d] for d in cands[k]["docs"])) for k in keys]
    cand_units = [[(doc_pos[d], u) for d, u in cands[k]["units"]] for k in keys]
    gold_docs = [np.array(sorted(doc_pos[d] for d in fact_docs[g])) for g in gold]
    rng = np.random.default_rng(SEED + 1)
    out = {}
    for S in ("GEO", "OTHER"):
        ci_s = [i for i in range(len(keys)) if cstrat[i] == S]
        gi_s = [i for i in range(len(gold)) if gstrat[i] == S]
        diffs = defaultdict(list)
        for _ in range(N_HALF):
            keep = np.zeros(len(ids), bool)
            keep[rng.choice(len(ids), len(ids) // 2, replace=False)] = True
            gold_in = {gi for gi in gi_s if keep[gold_docs[gi]].any()}
            m_stats = {}
            for m in ("naive", "R3_doc"):
                admitted_c, tp, hit = 0, 0, set()
                for ci in ci_s:
                    nd = int(keep[cand_docs[ci]].sum())
                    if nd == 0:
                        continue
                    ok = True if m == "naive" else admitted(nd)
                    if ok:
                        admitted_c += 1
                        g = [gi for gi in match[ci] if gi in gold_in]
                        if g:
                            tp += 1
                            hit.add(g[0])
                p = tp / admitted_c if admitted_c else 0.0
                r = len(hit) / len(gold_in) if gold_in else 0.0
                m_stats[m] = (p, r, 2 * p * r / (p + r) if p + r else 0.0)
            diffs["F1"].append(m_stats["R3_doc"][2] - m_stats["naive"][2])
            diffs["precision"].append(m_stats["R3_doc"][0] - m_stats["naive"][0])
        o = {}
        for k, v in diffs.items():
            v = np.array(v)
            dev = v - v.mean()
            o[k] = {"half_sample_mean": float(v.mean()),
                    "dev_ci95_unscaled": [float(np.percentile(dev, 2.5)), float(np.percentile(dev, 97.5))],
                    "dev_ci95_scaled_prereg": [float(np.percentile(dev, 2.5) / math.sqrt(2)),
                                               float(np.percentile(dev, 97.5) / math.sqrt(2))]}
        out[S] = o
    return out


def main() -> None:
    ids, alias, fact_docs, n_sent = load_gold()
    report = {"n_docs": len(ids), "distinct_gold_facts": len(fact_docs),
              "G_rec_total_normalize_b": sum(len(v) >= 2 for v in fact_docs.values()),
              "G_rec_EVID053_primary_key": 2179, "arms": {}}
    for arm in ARMS:
        if not (ROOT / "extractions" / f"{arm}.jsonl").exists():
            continue
        res = analyse_arm(arm, ids, alias, fact_docs, n_sent)
        res["half_sampling_secondary"] = half_sampling(res, ids)
        res.pop("_internal")
        report["arms"][arm] = res
    with open(ROOT / "analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
