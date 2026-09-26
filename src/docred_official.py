"""Official-style DocRED scoring (DEC-034; descriptive, zero API cost).

Re-scores already-collected extractions with the metrics of DocRED's
official evaluation script (thunlp/DocRED code/evaluation.py): relation
F1, Ign F1 (precision ignoring correct facts whose mention-name triple
also appears in train_annotated.json), and evidence F1.

Our extractor produces open (subject, predicate, object) strings, not
(head index, tail index, relation id), so each triple is converted:
  - entity: normalize_b(string) must equal the normalize_b() form of a
    mention of exactly one entity in the document (the DEC-031 alias
    index; ambiguous forms are not linked);
  - relation: normalize_text(predicate) must equal a DocRED relation name
    (rel_info.json), mapped to its P-id.
A triple failing either step cannot be expressed in the official format
("unscorable"). Two variants are reported:
  strict    -- unscorable triples are dropped (the official script only
               ever sees convertible predictions; this flatters precision);
  penalised -- each distinct unscorable triple is added to the
               prediction count as a false positive.
Evidence for a prediction = the union of its source sentences (the
sentence it was extracted from, or the sentences the document-level
extractor cited).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src import dec031_docred as D
from src.evaluator import normalize_text

TRAIN_PATH = Path("data/DocRED/train_annotated.json")


def load_train_facts(path: Path = TRAIN_PATH) -> set[tuple[str, str, str]]:
    """(head mention name, tail mention name, relation id) for every
    mention pair of every train_annotated fact, as in the official script."""
    facts = set()
    for d in json.loads(Path(path).read_text(encoding="utf-8")):
        vs = d["vertexSet"]
        for lab in d["labels"]:
            for n1 in vs[lab["h"]]:
                for n2 in vs[lab["t"]]:
                    facts.add((n1["name"], n2["name"], lab["r"]))
    return facts


def relation_ids(rel_info_path: Path = D.REL_INFO_PATH) -> dict[str, str]:
    """normalize_text(relation name) -> relation id."""
    rel = json.loads(Path(rel_info_path).read_text(encoding="utf-8"))
    return {normalize_text(name): rid for rid, name in rel.items()}


def convert(doc: dict, obs: list[dict], rel_ids: dict[str, str]):
    """obs: [{sent_id, subject, predicate, object}] for the output being
    scored. Returns ({(h, t, r): evidence sentence set}, set of distinct
    unscorable triples)."""
    aliases = D.alias_index(doc)
    preds: dict[tuple, set] = defaultdict(set)
    unscorable = set()
    for o in obs:
        h = aliases.get(D.normalize_b(o["subject"]))
        t = aliases.get(D.normalize_b(o["object"]))
        r = rel_ids.get(normalize_text(o["predicate"]))
        if h is None or t is None or r is None:
            unscorable.add((D.normalize_b(o["subject"]), normalize_text(o["predicate"]),
                            D.normalize_b(o["object"])))
            continue
        ev = preds[(h, t, r)]  # a document-level source cites no sentence
        if o["sent_id"] >= 0:
            ev.add(o["sent_id"])
    return preds, unscorable


def score(raw_docs: list[dict], preds_by_title: dict, unscorable_by_title: dict,
          train_facts: set) -> dict:
    """The official evaluation.py arithmetic, over the given documents only."""
    tot_relations = tot_evidences = 0
    truth = {}
    for d in raw_docs:
        for lab in d["labels"]:
            ev = set(lab.get("evidence", []))
            truth[(d["title"], lab["h"], lab["t"], lab["r"])] = ev
            tot_relations += 1
            tot_evidences += len(ev)
    vs_by_title = {d["title"]: d["vertexSet"] for d in raw_docs}
    n_pred = correct = correct_in_train = correct_ev = pred_ev = 0
    for title, preds in preds_by_title.items():
        vs = vs_by_title[title]
        for (h, t, r), ev in preds.items():
            n_pred += 1
            pred_ev += len(ev)
            key = (title, h, t, r)
            if key in truth:
                correct += 1
                correct_ev += len(ev & truth[key])
                if any((n1["name"], n2["name"], r) in train_facts for n1 in vs[h] for n2 in vs[t]):
                    correct_in_train += 1
    n_uns = sum(len(u) for u in unscorable_by_title.values())

    def f1(p, r):
        return 2 * p * r / (p + r) if p + r else 0.0

    out = {"gold_relations": tot_relations, "scorable_predictions": n_pred,
           "unscorable_predictions": n_uns, "correct": correct,
           "correct_in_train": correct_in_train}
    rec = correct / tot_relations if tot_relations else 0.0
    evi_r = correct_ev / tot_evidences if tot_evidences else 0.0
    evi_p = correct_ev / pred_ev if pred_ev else 0.0
    for variant, denom in (("strict", n_pred), ("penalised", n_pred + n_uns)):
        p = correct / denom if denom else 0.0
        ign_denom = denom - correct_in_train
        p_ign = (correct - correct_in_train) / ign_denom if ign_denom > 0 else 0.0
        out[variant] = {"precision": p, "recall": rec, "f1": f1(p, rec),
                        "ign_precision": p_ign, "ign_f1": f1(p_ign, rec)}
    out["evidence"] = {"precision": evi_p, "recall": evi_r, "f1": f1(evi_p, evi_r)}
    return out
