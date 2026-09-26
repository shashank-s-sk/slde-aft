"""DEC-033 offline analysis (zero API cost), as pre-registered in Decision
log.md DEC-033. For every arm with extractions on disk, reports:

  - extractor recall (no aggregation, primary evaluator of DEC-031/032);
  - corroboration: G2 raw and G2 verified (see src/dec033_protocol.py),
    as a share of all gold facts, and rho = verified share / annotation
    rate (DocRED: 2+ gold evidence sentences, 50.2%; also against the
    3.4% of facts whose two entities are *named* in 2+ sentences;
    BioRED: 2+ co-mentions, 35.1%);
  - no aggregation, R2 and R3 P/R/F1 (normalised key, tau 0.70, shrinkage 0.5),
    and the aggregation gap = F1(R3) - F1(no aggregation);
  - paired bootstrap over documents (10,000 resamples) of each new arm
    against the Llama sentence-level arm ON THE SAME DOCUMENTS, for the
    verified G2 share and for the gap.

Usage: python -m scripts.dec033_analyze
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from src import dec031_docred as D
from src import dec032_biored as B
from src import dec033_protocol as P

ARMS = {
    ("docred", "llama", "sentence"): Path("outputs/dec031_docred/extractions"),
    ("docred", "deepseek", "sentence"): Path("outputs/dec033_protocol/extractions/docred_deepseek_sentence"),
    ("docred", "llama", "document"): Path("outputs/dec033_protocol/extractions/docred_llama_document"),
    ("docred", "deepseek", "document"): Path("outputs/dec033_protocol/extractions/docred_deepseek_document"),
    ("biored", "llama", "sentence"): Path("outputs/dec032_biored/extractions/llama_sentence"),
    ("biored", "deepseek", "sentence"): Path("outputs/dec032_biored/extractions/deepseek_sentence"),
    ("biored", "llama", "document"): Path("outputs/dec033_protocol/extractions/biored_llama_document"),
    ("biored", "deepseek", "document"): Path("outputs/dec033_protocol/extractions/biored_deepseek_document"),
}
OUT = Path("outputs/dec033_protocol/analysis_result.json")
N_BOOT = 10_000
SEED = 20330926


def load(path: Path) -> dict[int, dict[int, list[dict]]]:
    by = defaultdict(dict)
    for f in sorted(path.glob("shard_*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r["http_status"] is not None:
                by[r["doc_idx"]][r.get("unit_id", r.get("sent_id"))] = r["triples"]
    return by


def evaluate(corpus, doc, items):
    return D.evaluate_doc(doc, items) if corpus == "docred" else B.evaluate_doc(doc, items, "alias")


def doc_counts(corpus, unit, doc, unit_triples):
    obs = P.observations(unit, unit_triples, len(doc["sentences"]))
    raw = list({(o["subject"], o["predicate"], o["object"]) for o in obs})
    out = {"naive": evaluate(corpus, doc, raw), **P.corroboration(corpus, doc, obs),
           "gold": len(doc["gold_facts"])}
    for rule in ("R2", "R3"):
        out[rule] = evaluate(corpus, doc, D.admitted_items(D.aggregate(obs, "norm", rule, {})))
    return out


def citation_validity(corpus, docs, ext):
    """Pre-registered measure for document arms: of the sentences cited for
    triples that match a gold fact, the share that genuinely support it
    (gold evidence on DocRED; co-mention of both concepts on BioRED)."""
    cited = valid = triples = no_citation = 0
    for d in docs:
        ut, n = ext.get(d["doc_idx"], {}), len(d["sentences"])
        for t in ut.get(0, []):
            triples += 1
            no_citation += not any(0 <= e < n for e in t.get("evidence", []))
        match = P.matcher(corpus, d)
        for o in P.observations("document", ut, n):
            g = None if o["sent_id"] == P.DOC_SOURCE else match((o["subject"], o["predicate"], o["object"]))
            if g is not None:
                cited += 1
                valid += o["sent_id"] in P.fact_sentences(corpus, d, g)
    return {"citations_on_correct_triples": cited, "valid": valid,
            "validity": valid / cited if cited else None,
            "triples": triples, "triples_without_valid_citation": no_citation}


def prf(c):
    return D.prf(c["tp"], c["fp"], c["fn"])


def main():
    docs = {"docred": P.load_docred(), "biored": P.load_biored()}
    rates = {"docred": P.annotation_rate("docred", docs["docred"], "evidence"),
             "docred_named": P.annotation_rate("docred", docs["docred"], "comention"),
             "biored": P.annotation_rate("biored", docs["biored"])}
    per_arm, result = {}, {"annotation_rates": rates, "arms": {}, "comparisons": {}}
    for (corpus, model, unit), path in ARMS.items():
        if not path.exists():
            continue
        ext = load(path)
        n_units = (lambda d: len(d["sentences"])) if unit == "sentence" else (lambda d: 1)
        complete = [d for d in docs[corpus] if len(ext.get(d["doc_idx"], {})) == n_units(d)]
        if not complete:
            continue
        counts = {d["doc_idx"]: doc_counts(corpus, unit, d, ext[d["doc_idx"]]) for d in complete}
        per_arm[(corpus, model, unit)] = counts
        tot = lambda k, f: sum(c[k][f] for c in counts.values())
        gold = sum(c["gold"] for c in counts.values())
        s = {"docs": len(complete)}
        for arm in ("naive", "R2", "R3"):
            s[arm] = D.prf(tot(arm, "tp"), tot(arm, "fp"), tot(arm, "fn"))
        for k in ("recovered", "g2_raw", "g2_verified"):
            s[k] = sum(c[k] for c in counts.values())
        s["g2_verified_share"] = s["g2_verified"] / gold
        s["rho"] = s["g2_verified_share"] / rates[corpus]
        if corpus == "docred":
            s["rho_vs_named"] = s["g2_verified_share"] / rates["docred_named"]
        s["gap_R3"] = s["R3"]["f1"] - s["naive"]["f1"]
        if unit == "document":
            s["citation_validity"] = citation_validity(corpus, complete, ext)
            print(f"  citation validity {corpus}/{model}: {s['citation_validity']}")
        result["arms"]["/".join((corpus, model, unit))] = s
        print(f"{corpus:6} {model:8} {unit:8} docs={len(complete):3}  recall={s['naive']['recall']:.4f}  "
              f"G2 raw/ver={s['g2_raw']}/{s['g2_verified']} ({100 * s['g2_verified_share']:.2f}%)  "
              f"rho={s['rho']:.3f}  F1 naive/R2/R3={s['naive']['f1']:.4f}/{s['R2']['f1']:.4f}/{s['R3']['f1']:.4f}  "
              f"gap={s['gap_R3']:+.4f}")

    rng = np.random.default_rng(SEED)
    # Each arm's own gap F1(R3) - F1(no aggregation), with a bootstrap CI
    # (needed by the OVERTURNED and STANDS decision rules).
    for (corpus, model, unit), counts in per_arm.items():
        ids = sorted(counts)
        idx = rng.integers(0, len(ids), size=(N_BOOT, len(ids)))
        f = lambda sel, arm: D.prf(*(sum(counts[i][arm][k] for i in sel) for k in ("tp", "fp", "fn")))["f1"]
        own = lambda sel: f(sel, "R3") - f(sel, "naive")
        boots = np.array([own([ids[j] for j in row]) for row in idx])
        lo, hi = np.percentile(boots, [2.5, 97.5])
        key = "/".join((corpus, model, unit))
        result["arms"][key]["gap_R3_ci"] = [float(own(ids)), float(lo), float(hi)]
        print(f"  own gap {key}: {own(ids):+.4f} [{lo:+.4f}, {hi:+.4f}]")

    for (corpus, model, unit), counts in per_arm.items():
        base_key = (corpus, "llama", "sentence")
        if (model, unit) == ("llama", "sentence") or base_key not in per_arm:
            continue
        ids = sorted(set(counts) & set(per_arm[base_key]))
        base = per_arm[base_key]
        idx = rng.integers(0, len(ids), size=(N_BOOT, len(ids)))

        def stats(sel, cs):
            g = sum(cs[i]["gold"] for i in sel)
            share = sum(cs[i]["g2_verified"] for i in sel) / g
            f = lambda arm: D.prf(*(sum(cs[i][arm][k] for i in sel) for k in ("tp", "fp", "fn")))["f1"]
            return share, f("R3") - f("naive")

        def diff(sel):
            a, b = stats(sel, counts), stats(sel, base)
            return a[0] - b[0], a[1] - b[1]

        point = diff(ids)
        boots = np.array([diff([ids[j] for j in row]) for row in idx])
        lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
        key = f"{corpus}/{model}/{unit} vs {corpus}/llama/sentence"
        result["comparisons"][key] = {
            "docs": len(ids),
            "g2_verified_share_diff": [float(point[0]), float(lo[0]), float(hi[0])],
            "gap_diff": [float(point[1]), float(lo[1]), float(hi[1])]}
        print(f"  {key}: G2 share {point[0]:+.4f} [{lo[0]:+.4f}, {hi[0]:+.4f}]  "
              f"gap {point[1]:+.4f} [{lo[1]:+.4f}, {hi[1]:+.4f}]")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
