"""DEC-033: does the extraction protocol create the corroboration
bottleneck? Shared logic for scripts/dec033_extract.py (paid) and
scripts/dec033_analyze.py (offline). Pre-registered in Decision log.md
DEC-033.

Arms (corpus x extractor x unit):
  unit "sentence": one call per sentence; a sentence is one source.
  unit "document": one call per document, sentences numbered [0], [1], ...;
      the model cites the sentence numbers that support each triple, and
      each cited sentence is one source. A triple citing no valid sentence
      gets a single document-level source (it can never be corroborated).

Corroboration of a gold fact (the G2 measure of DEC-031/032):
  raw      -- a matching extracted triple has 2+ distinct sources;
  verified -- counting only sources in which both gold entities are
              mentioned (DocRED vertexSet sentence ids; BioRED annotated
              concept mentions). Guards against a model inflating
              corroboration by citing arbitrary sentences.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from src import dec031_docred as D
from src import dec032_biored as B

DOC_SOURCE = -1  # source id for a document-level triple that cites no valid sentence


def load_docred() -> list[dict]:
    raw = {d["title"]: d for d in json.loads(Path(D.DEV_PATH).read_text(encoding="utf-8"))}
    rel = json.loads(Path(D.REL_INFO_PATH).read_text(encoding="utf-8"))
    docs = D.load_docs()
    for d in docs:
        rd = raw[d["title"]]
        d["entity_sentences"] = [sorted({m["sent_id"] for m in ent}) for ent in rd["vertexSet"]]
        ev = defaultdict(set)
        for lab in rd["labels"]:
            ev[(lab["h"], rel.get(lab["r"], lab["r"]), lab["t"])] |= {
                e for e in lab.get("evidence", []) if e < len(d["sentences"])}
        d["fact_evidence"] = [sorted(ev.get(f, set())) for f in d["gold_facts"]]
    return docs


def load_biored() -> list[dict]:
    docs = B.load_docs()
    parsed = {}
    for split in B.SPLITS:
        for d in B._parse(B.ROOT / f"{split}.PubTator"):
            parsed[d["pmid"]] = d
    for d in docs:
        pd = parsed[d["pmid"]]
        spans = B.sentence_spans(pd["title"], pd["abstract"])
        sent_of = defaultdict(set)
        for start, end, surface, ids in pd["mentions"]:
            si = next((i for i, (a, b) in enumerate(spans) if a <= start < b), None)
            if si is not None:
                for cid in B.ID_SEP.split(ids):
                    sent_of[cid].add(si)
        d["concept_sentences"] = {k: sorted(v) for k, v in sent_of.items()}
    return docs


def numbered(doc: dict) -> str:
    return "\n".join(f"[{i}] {s}" for i, s in enumerate(doc["sentences"]))


def observations(unit: str, unit_triples: dict[int, list[dict]], n_sentences: int) -> list[dict]:
    """(sent_id, subject, predicate, object) observations for aggregation."""
    obs = []
    for uid in sorted(unit_triples):
        for t in unit_triples[uid]:
            base = {"subject": t["subject"], "predicate": t["predicate"], "object": t["object"]}
            if unit == "sentence":
                obs.append({**base, "sent_id": uid})
            else:
                cited = [e for e in t.get("evidence", []) if 0 <= e < n_sentences]
                for e in (cited or [DOC_SOURCE]):
                    obs.append({**base, "sent_id": e})
    return obs


def fact_sentences(corpus: str, doc: dict, fact_idx: int, basis: str = "evidence") -> set[int]:
    """Sentences that support a gold fact.
    DocRED, basis "evidence" (default): the gold evidence sentences, which
        include sentences that refer to an entity only by pronoun or other
        coreference.
    DocRED, basis "comention": sentences naming both entities.
    BioRED: co-mention of both annotated concepts (no evidence annotations)."""
    if corpus == "docred":
        if basis == "evidence":
            return set(doc["fact_evidence"][fact_idx])
        h, _, t = doc["gold_facts"][fact_idx]
        return set(doc["entity_sentences"][h]) & set(doc["entity_sentences"][t])
    _, a, b = doc["gold_facts"][fact_idx]
    return set(doc["concept_sentences"].get(a, [])) & set(doc["concept_sentences"].get(b, []))


def matcher(corpus: str, doc: dict):
    if corpus == "docred":
        return D.gold_matcher(doc)
    return lambda item: B.matched_fact(doc, item)


def corroboration(corpus: str, doc: dict, obs: list[dict]) -> dict:
    """Gold facts recovered at all, and from 2+ sources (raw / verified)."""
    match = matcher(corpus, doc)
    srcs = defaultdict(set)
    for o in obs:
        g = match((o["subject"], o["predicate"], o["object"]))
        if g is not None:
            srcs[g].add(o["sent_id"])
    raw = {g for g, s in srcs.items() if len({x for x in s if x != DOC_SOURCE}) >= 2}
    ver = {g for g, s in srcs.items() if len(s & fact_sentences(corpus, doc, g)) >= 2}
    return {"recovered": len(srcs), "g2_raw": len(raw), "g2_verified": len(ver)}


def annotation_rate(corpus: str, docs: list[dict], basis: str = "evidence") -> float:
    """Share of gold facts supported by 2+ sentences, on the given basis
    (see fact_sentences)."""
    tot = hit = 0
    for d in docs:
        for g in range(len(d["gold_facts"])):
            tot += 1
            hit += len(fact_sentences(corpus, d, g, basis)) >= 2
    return hit / tot if tot else 0.0
