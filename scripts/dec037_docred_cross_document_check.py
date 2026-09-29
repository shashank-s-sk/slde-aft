"""DEC-037 (free data check, no API cost): how much cross-document
redundancy does the DocRED data already on disk contain?

Counts (a) entities and (b) gold facts that appear in more than one
document, in dev (998 docs), train_annotated (3,053) and both pooled.
Names are normalised (NFKC, lowercase, punctuation and whitespace
collapsed). Two matching modes:
- primary-name: an entity is its first mention's name;
- alias: an entity is the set of its mention names, and two occurrences
  match if they share any normalised name. For facts, a (head, relation,
  tail) matches if the relation is the same and the head and tail each
  share an alias.

Usage: python -m scripts.dec037_docred_cross_document_check
"""

from __future__ import annotations

import collections
import json
import re
import unicodedata
from pathlib import Path

OUT = Path("outputs/dec037_docred_redundancy_check")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load(path: str, tag: str) -> list[dict]:
    return [dict(ex, _doc=f"{tag}_{i}") for i, ex in enumerate(json.load(open(path, encoding="utf-8")))]


def analyse(docs: list[dict], rel_map: dict) -> dict:
    ent_docs = collections.defaultdict(set)      # primary name -> docs
    alias_docs = collections.defaultdict(set)    # any alias -> docs
    fact_docs = collections.defaultdict(set)     # (h primary, r, t primary) -> docs
    fact_alias_docs = collections.defaultdict(set)
    n_entities = n_facts = 0
    for ex in docs:
        names = []
        for v in ex["vertexSet"]:
            aliases = {norm(m["name"]) for m in v if norm(m["name"])}
            prim = norm(v[0]["name"])
            names.append((prim, aliases))
            n_entities += 1
            ent_docs[prim].add(ex["_doc"])
            for a in aliases:
                alias_docs[a].add(ex["_doc"])
        for lab in ex.get("labels", []):
            n_facts += 1
            (hp, ha), (tp, ta), r = names[lab["h"]], names[lab["t"]], rel_map.get(lab["r"], lab["r"])
            fact_docs[(hp, r, tp)].add(ex["_doc"])
            for h in ha:
                for t in ta:
                    fact_alias_docs[(h, r, t)].add(ex["_doc"])

    # alias-mode fact redundancy, counted per gold fact instance
    facts_multi_alias = 0
    for ex in docs:
        names = [{norm(m["name"]) for m in v if norm(m["name"])} for v in ex["vertexSet"]]
        for lab in ex.get("labels", []):
            r = rel_map.get(lab["r"], lab["r"])
            others = set()
            for h in names[lab["h"]]:
                for t in names[lab["t"]]:
                    others |= fact_alias_docs[(h, r, t)]
            if len(others - {ex["_doc"]}) > 0:
                facts_multi_alias += 1

    def dist(d):
        c = collections.Counter(min(len(v), 5) for v in d.values())
        return {("5+" if k == 5 else str(k)): c[k] for k in sorted(c)}

    multi_fact_keys = {k for k, v in fact_docs.items() if len(v) > 1}
    rel_counter = collections.Counter(k[1] for k in multi_fact_keys)
    instances_multi = sum(len(fact_docs[k]) for k in multi_fact_keys)
    return {
        "documents": len(docs),
        "entity_mentions_clusters": n_entities,
        "distinct_entities_primary_name": len(ent_docs),
        "entities_in_2plus_docs_primary_name": sum(len(v) > 1 for v in ent_docs.values()),
        "distinct_alias_strings": len(alias_docs),
        "alias_strings_in_2plus_docs": sum(len(v) > 1 for v in alias_docs.values()),
        "entity_doc_count_distribution_primary": dist(ent_docs),
        "gold_fact_instances": n_facts,
        "distinct_facts_primary_name": len(fact_docs),
        "distinct_facts_in_2plus_docs_primary_name": len(multi_fact_keys),
        "fact_instances_whose_fact_recurs_in_another_doc_primary": instances_multi,
        "fact_instances_whose_fact_recurs_in_another_doc_alias": facts_multi_alias,
        "fact_doc_count_distribution_primary": dist(fact_docs),
        "top_relations_among_recurring_facts": rel_counter.most_common(10),
        "example_recurring_facts": [
            {"fact": list(k), "n_docs": len(fact_docs[k])}
            for k in sorted(multi_fact_keys, key=lambda k: -len(fact_docs[k]))[:10]
        ],
    }


def main() -> None:
    rel_map = json.load(open("data/DocRED/rel_info.json", encoding="utf-8"))
    dev = load("data/DocRED/dev.json", "dev")
    train = load("data/DocRED/train_annotated.json", "train")
    result = {"dev": analyse(dev, rel_map), "train_annotated": analyse(train, rel_map),
              "dev+train_annotated": analyse(dev + train, rel_map)}
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "summary.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    for name, r in result.items():
        print(f"\n== {name}: {r['documents']} docs")
        for k, v in r.items():
            if k not in ("documents", "example_recurring_facts"):
                print(f"  {k}: {v}")
        print("  examples:", [(e['fact'], e['n_docs']) for e in r["example_recurring_facts"][:6]])


if __name__ == "__main__":
    main()
