"""DEC-034: official-style DocRED scores (F1, Ign F1, evidence F1) for the
already-collected DocRED extractions (DEC-031 and DEC-033). Zero API cost.
See src/docred_official.py for the conversion and the two variants.

Outputs scored per arm: no aggregation (every extracted triple) and R3
(triples admitted by distinct-source aggregation, normalised key,
tau 0.70), over the documents each arm covers.

Usage: python -m scripts.docred_official_score
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts import dec033_analyze as A
from src import dec031_docred as D
from src import dec033_protocol as P
from src import docred_official as O

OUT = Path("outputs/docred_official/official_scores.json")


def outputs_for(doc, unit, unit_triples):
    obs = P.observations(unit, unit_triples, len(doc["sentences"]))
    cands = D.aggregate(obs, "norm", "R3", {})
    admitted = {k for k, c in cands.items() if c["score"] >= D.TAU - 1e-12}
    key = lambda o: (D.normalize_b(o["subject"]), D.normalize_text(o["predicate"]),
                     D.normalize_b(o["object"]))
    return {"naive": obs, "R3": [o for o in obs if key(o) in admitted]}


def main():
    docs = P.load_docred()
    raw = {d["title"]: d for d in json.loads(Path(D.DEV_PATH).read_text(encoding="utf-8"))}
    train_facts = O.load_train_facts()
    rel_ids = O.relation_ids()
    result = {}
    for (corpus, model, unit), path in A.ARMS.items():
        if corpus != "docred" or not path.exists():
            continue
        ext = A.load(path)
        n_units = (lambda d: len(d["sentences"])) if unit == "sentence" else (lambda d: 1)
        complete = [d for d in docs if len(ext.get(d["doc_idx"], {})) == n_units(d)]
        for output in ("naive", "R3"):
            preds, uns = {}, {}
            for d in complete:
                obs = outputs_for(d, unit, ext[d["doc_idx"]])[output]
                preds[d["title"]], uns[d["title"]] = O.convert(d, obs, rel_ids)
            s = O.score([raw[d["title"]] for d in complete], preds, uns, train_facts)
            s["docs"] = len(complete)
            name = f"{model}/{unit}/{output}"
            result[name] = s
            st, pe, ev = s["strict"], s["penalised"], s["evidence"]
            print(f"{name:26} docs={len(complete)} scorable={s['scorable_predictions']:6} "
                  f"unscorable={s['unscorable_predictions']:6} correct={s['correct']:5} | "
                  f"strict P/R/F1 {st['precision']:.3f}/{st['recall']:.4f}/{st['f1']:.4f} IgnF1 {st['ign_f1']:.4f} | "
                  f"penalised F1 {pe['f1']:.4f} IgnF1 {pe['ign_f1']:.4f} | EviF1 {ev['f1']:.4f}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("saved", OUT)


if __name__ == "__main__":
    main()
