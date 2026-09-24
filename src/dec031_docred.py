"""DEC-031: DocRED at scale with a normalised matching key.

Shared logic for scripts/dec031_docred_extract.py (paid extraction, run
once) and scripts/dec031_docred_analyze.py (offline, every arm computed
from the same saved extractions). Everything here is pre-registered in
Decision log.md DEC-031; change it only with a logged deviation.

Matching keys (how an extracted subject/object string is keyed when
observations are pooled into PKB candidates):
  (a) "exact":  the PKB adapter's existing key -- strip + lowercase
                (src/pkb_instrumentation.normalized_slot/object).
  (b) "norm":   pure string normalisation, no gold resources -- see
                normalize_b(). The deployable arm.
  (c) "alias":  ORACLE. A string whose normalize_b() form equals the
                normalize_b() form of exactly one gold entity's mention
                in this document is keyed to that entity; anything else
                falls back to its (b) key. Uses DocRED gold entity
                mentions, so it is an upper bound, not a deployable
                result.

Aggregation (conflict penalty off: configs/docred_functional_predicates.json
is empty, as in DEC-020, so the rival ceiling does not apply here):
  R2: conservative Noisy-Or over every observation of a key,
      confidence 1.0 per observation, shrinkage 0.5 -> 1 - 0.5**k.
  R3: the same over distinct source sentences only (DEC-026's
      distinct-source rule, source = sentence).
  Admit when score >= TAU = 0.70, i.e. >= 2 observations (R2) or >= 2
  distinct sentences (R3). Fixed from DEC-020; not tuned.

Evaluation (primary, identical for every arm): per document, an item
(subject, predicate, object) matches gold fact (h, r, t) when the
predicate equals r's name and the subject's and object's normalize_b()
forms equal the normalize_b() form of any mention of h and t
respectively. Each item is mapped to an evaluation key -- the gold fact
it matches, else its own (b)-normalised triple -- and keys are
deduplicated per document before counting, so no arm gains or loses
from how it spells or groups the same fact.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from src.evaluator import normalize_text
from src.pkb_instrumentation import normalized_object, normalized_slot

DEV_PATH = Path("data/DocRED/dev.json")
REL_INFO_PATH = Path("data/DocRED/rel_info.json")
SHRINKAGE = 0.5
TAU = 0.70
KEYS = ("exact", "norm", "alias")
RULES = ("R2", "R3")

_ARTICLES = ("the ", "a ", "an ")


def normalize_b(text: str) -> str:
    """Arm (b), exactly as pre-registered: Unicode NFKC, casefold, drop a
    possessive 's, delete periods and apostrophes ("U.S." -> "us"),
    replace every other Unicode punctuation character with a space
    ("Jean-Paul" -> "jean paul"), collapse whitespace, strip, then drop
    one leading English article ("the", "a", "an")."""
    s = unicodedata.normalize("NFKC", str(text)).casefold()
    s = re.sub(r"['’]s\b", "", s)
    s = re.sub(r"[.'’]", "", s)
    s = "".join(" " if unicodedata.category(ch).startswith("P") else ch for ch in s)
    s = re.sub(r"\s+", " ", s).strip()
    for article in _ARTICLES:
        if s.startswith(article) and len(s) > len(article):
            s = s[len(article):]
            break
    return s


def load_docs(dev_path: Path = DEV_PATH, rel_info_path: Path = REL_INFO_PATH) -> list[dict]:
    """The DEC-031 document set: every DocRED dev document with at least
    one gold (head, relation, tail) triple supported by 2+ evidence
    sentences -- the same eligibility rule as DEC-020's pilot build
    (845 of 998 documents). doc_idx is the position in this list."""
    rel_map = json.loads(Path(rel_info_path).read_text(encoding="utf-8"))
    raw = json.loads(Path(dev_path).read_text(encoding="utf-8"))
    docs = []
    for d in raw:
        sentences = [" ".join(tokens) for tokens in d["sents"]]
        mentions = [sorted({m["name"] for m in ent}) for ent in d["vertexSet"]]
        first_mention = [ent[0]["name"] for ent in d["vertexSet"]]
        facts, evidence = [], []
        ev_counter = Counter()
        for lab in d["labels"]:
            rel = rel_map.get(lab["r"], lab["r"])
            ev = [e for e in lab.get("evidence", []) if e < len(sentences)]
            ev_counter[(first_mention[lab["h"]], rel, first_mention[lab["t"]])] += len(ev)
            facts.append((lab["h"], rel, lab["t"]))
            evidence.extend(ev)
        if not any(v > 1 for v in ev_counter.values()):
            continue
        docs.append({
            "doc_idx": len(docs),
            "title": d["title"],
            "sentences": sentences,
            "mentions": mentions,
            "first_mention": first_mention,
            "gold_facts": sorted(set(facts)),
            "evidence_sent_ids": sorted(set(evidence)),
        })
    return docs


def alias_index(doc: dict) -> dict[str, int]:
    """normalize_b(mention) -> entity index, for mentions that resolve to
    exactly one entity in this document. Ambiguous forms are left out."""
    owners: dict[str, set[int]] = defaultdict(set)
    for ent_idx, names in enumerate(doc["mentions"]):
        for name in names:
            owners[normalize_b(name)].add(ent_idx)
    return {form: next(iter(ids)) for form, ids in owners.items() if len(ids) == 1}


def entity_key(text: str, key: str, aliases: dict[str, int]) -> str:
    if key == "exact":
        return normalized_object(text)
    b = normalize_b(text)
    if key == "norm":
        return b
    if key == "alias":
        return f"<E{aliases[b]}>" if b in aliases else b
    raise ValueError(key)


def predicate_key(predicate: str, key: str) -> str:
    if key == "exact":
        return normalized_slot("", predicate)[1]
    return normalize_text(predicate)


def aggregate(observations: list[dict], key: str, rule: str, aliases: dict[str, int]) -> dict[tuple, dict]:
    """observations: [{sent_id, subject, predicate, object}] for one
    document. Returns candidate key -> {score, n_obs, n_sents, forms},
    where forms counts the raw (subject, predicate, object) spellings
    pooled into the candidate."""
    cands: dict[tuple, dict] = {}
    for o in observations:
        k = (entity_key(o["subject"], key, aliases), predicate_key(o["predicate"], key),
             entity_key(o["object"], key, aliases))
        c = cands.setdefault(k, {"n_obs": 0, "sents": set(), "forms": Counter()})
        c["n_obs"] += 1
        c["sents"].add(o["sent_id"])
        c["forms"][(o["subject"], o["predicate"], o["object"])] += 1
    for c in cands.values():
        n = c["n_obs"] if rule == "R2" else len(c["sents"])
        c["score"] = 1.0 - (1.0 - SHRINKAGE) ** n
        c["n_sents"] = len(c["sents"])
        del c["sents"]
    return cands


def admitted_items(cands: dict[tuple, dict]) -> list[tuple[str, str, str]]:
    """One representative raw spelling per admitted candidate: its most
    frequent form (ties: lexicographically smallest, for determinism)."""
    out = []
    for c in cands.values():
        if c["score"] >= TAU - 1e-12:
            top = max(c["forms"].values())
            out.append(min(f for f, n in c["forms"].items() if n == top))
    return out


def contested_slots(cands: dict[tuple, dict], admitted_only: bool) -> int:
    """(subject key, predicate key) slots with 2+ distinct object keys."""
    objs: dict[tuple, set] = defaultdict(set)
    for (s, p, o), c in cands.items():
        if not admitted_only or c["score"] >= TAU - 1e-12:
            objs[(s, p)].add(o)
    return sum(1 for v in objs.values() if len(v) > 1)


def gold_matcher(doc: dict):
    """Returns match(item) -> gold fact index or None (primary evaluator)."""
    forms = [{normalize_b(n) for n in names} for names in doc["mentions"]]
    by_rel: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for i, (h, r, t) in enumerate(doc["gold_facts"]):
        by_rel[normalize_text(r)].append((i, h, t))

    def match(item: tuple[str, str, str]):
        s, p, o = normalize_b(item[0]), normalize_text(item[1]), normalize_b(item[2])
        for i, h, t in by_rel.get(p, ()):
            if s in forms[h] and o in forms[t]:
                return i
        return None

    return match


def evaluate_doc(doc: dict, items: list[tuple[str, str, str]]) -> dict:
    """Primary evaluator: counts for one document (see module docstring)."""
    match = gold_matcher(doc)
    keys = set()
    for it in items:
        g = match(it)
        keys.add(("gold", g) if g is not None else ("pred", normalize_b(it[0]),
                                                    normalize_text(it[1]), normalize_b(it[2])))
    tp = sum(1 for k in keys if k[0] == "gold")
    return {"tp": tp, "fp": len(keys) - tp, "fn": len(doc["gold_facts"]) - tp}


def evaluate_doc_first_mention(doc: dict, items: list[tuple[str, str, str]]) -> dict:
    """Secondary evaluator, for continuity with DEC-020: exact match (after
    src.evaluator.normalize_text) against gold triples written with each
    entity's first vertexSet mention, per document."""
    gold = {(normalize_text(doc["first_mention"][h]), normalize_text(r), normalize_text(doc["first_mention"][t]))
            for h, r, t in doc["gold_facts"]}
    pred = {tuple(normalize_text(x) for x in it) for it in items}
    tp = len(gold & pred)
    return {"tp": tp, "fp": len(pred) - tp, "fn": len(gold) - tp}


def prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return {"precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "tp": tp, "fp": fp, "fn": fn}
