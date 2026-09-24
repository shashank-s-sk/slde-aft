"""DEC-032: BioRED at scale. Shared logic for
scripts/dec032_biored_extract.py (paid extraction) and
scripts/dec032_biored_analyze.py (offline arms). Every definition here
is pre-registered in Decision log.md DEC-032.

Corpus: the 400 Train + 100 Dev abstracts (Test is never used, per
DEC-009's rule). Sources for aggregation are sentences: the title is
sentence 0 and the abstract is split by SENTENCE_SPLIT below.

Gold: BioRED relations are between concept IDs and are UNORDERED
(entity pairs), so every evaluator here matches either argument order.

Evaluators (all per document, predictions deduplicated per gold fact):
  - "alias" (PRIMARY): predicate equals the relation type, and subject
    and object equal, after dec031 normalize_b(), any annotated mention
    of the two gold concept IDs (either order).
  - "strict" (pilot continuity): exact match after
    src.evaluator.normalize_text against each concept's FIRST mention.
  - "relaxed" (pilot continuity, EVID-024's heuristic): predicate exact;
    subject/object match a concept's first mention if either normalised
    string contains the other.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from src.dec031_docred import normalize_b
from src.evaluator import normalize_text

ROOT = Path("data/BioRED/BioRED")
SPLITS = ("Train", "Dev")
RELATION_TYPES = ["Association", "Positive_Correlation", "Negative_Correlation", "Bind",
                  "Cotreatment", "Comparison", "Drug_Interaction", "Conversion"]

SENTENCE_SPLIT = re.compile(
    r"(?<!\be\.g)(?<!\bi\.e)(?<!\bet al)(?<!\bvs)(?<!\bFig)(?<!\bapprox)(?<!\bca)"
    r"(?<=[.!?])\s+(?=[A-Z0-9(\[])")
ID_SEP = re.compile(r"[,;|]")


def _parse(path: Path) -> list[dict]:
    docs, cur = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            if cur:
                docs.append(cur)
            cur = None
            continue
        if "|t|" in line:
            pmid, _, title = line.split("|", 2)
            cur = {"pmid": pmid, "title": title, "abstract": "", "mentions": [], "relations": []}
        elif "|a|" in line:
            cur["abstract"] = line.split("|", 2)[2]
        else:
            f = line.split("\t")
            if len(f) == 6:
                cur["mentions"].append((int(f[1]), int(f[2]), f[3], f[5]))
            elif len(f) == 5:
                cur["relations"].append((f[1], f[2], f[3]))
    if cur:
        docs.append(cur)
    return docs


def sentence_spans(title: str, abstract: str) -> list[tuple[int, int]]:
    """Character spans in the PubTator text "title + ' ' + abstract"."""
    spans = [(0, len(title))]
    off, pos = len(title) + 1, 0
    for m in SENTENCE_SPLIT.finditer(abstract):
        spans.append((off + pos, off + m.start()))
        pos = m.end()
    spans.append((off + pos, off + len(abstract)))
    return [(a, b) for a, b in spans if b > a]


def load_docs(root: Path = ROOT) -> list[dict]:
    docs = []
    for split in SPLITS:
        for d in _parse(root / f"{split}.PubTator"):
            text = f"{d['title']} {d['abstract']}"
            spans = sentence_spans(d["title"], d["abstract"])
            mentions, first, sent_of = defaultdict(set), {}, defaultdict(set)
            for start, end, surface, ids in d["mentions"]:
                si = next((i for i, (a, b) in enumerate(spans) if a <= start < b), None)
                for cid in ID_SEP.split(ids):
                    mentions[cid].add(surface)
                    first.setdefault(cid, surface)
                    if si is not None:
                        sent_of[cid].add(si)
            facts = sorted({(r, *sorted((a, b))) for r, a, b in d["relations"]
                            if a in mentions and b in mentions})
            docs.append({
                "doc_idx": len(docs), "pmid": d["pmid"], "split": split, "text": text,
                "sentences": [text[a:b] for a, b in spans],
                "mentions": {k: sorted(v) for k, v in mentions.items()},
                "first_mention": first,
                "gold_facts": facts,  # (relation_type, concept_id_a, concept_id_b), a < b
                "fact_sentence_comention": [len(sent_of[a] & sent_of[b]) for _, a, b in facts],
            })
    return docs


def _match_fact(doc: dict, item: tuple[str, str, str], evaluator: str):
    s, p, o = item
    if normalize_text(p) not in {normalize_text(r) for r in RELATION_TYPES}:
        return None
    for i, (r, a, b) in enumerate(doc["gold_facts"]):
        if normalize_text(r) != normalize_text(p):
            continue
        for x, y in ((a, b), (b, a)):
            if evaluator == "alias":
                forms_x = {normalize_b(m) for m in doc["mentions"][x]}
                forms_y = {normalize_b(m) for m in doc["mentions"][y]}
                if normalize_b(s) in forms_x and normalize_b(o) in forms_y:
                    return i
            else:
                gx, gy = normalize_text(doc["first_mention"][x]), normalize_text(doc["first_mention"][y])
                ps, po = normalize_text(s), normalize_text(o)
                if evaluator == "strict" and ps == gx and po == gy:
                    return i
                if evaluator == "relaxed" and ps and po and (ps in gx or gx in ps) and (po in gy or gy in po):
                    return i
    return None


def evaluate_doc(doc: dict, items: list[tuple[str, str, str]], evaluator: str = "alias") -> dict:
    keys = set()
    for it in items:
        g = _match_fact(doc, it, evaluator)
        keys.add(("gold", g) if g is not None else
                 ("pred", normalize_b(it[0]), normalize_text(it[1]), normalize_b(it[2])))
    tp = sum(1 for k in keys if k[0] == "gold")
    return {"tp": tp, "fp": len(keys) - tp, "fn": len(doc["gold_facts"]) - tp}


def matched_fact(doc: dict, item: tuple[str, str, str]):
    """Gold fact index under the primary evaluator, or None."""
    return _match_fact(doc, item, "alias")


def valid_relation(predicate: str) -> bool:
    return normalize_text(predicate) in {normalize_text(r) for r in RELATION_TYPES}
