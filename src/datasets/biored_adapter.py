"""BioRED dataset adapter (DEC-009, second-domain evaluation). Parses
the official PubTator-format files (data/BioRED/BioRED/*.PubTator) into
the same (subject, predicate, object) triple representation used
throughout this project.

BioRED's gold relations are between normalized entity IDs, not surface
text — e.g. relation (D003409, Positive_Correlation, 6528) where D003409
and 6528 are concept IDs, each of which may have multiple surface
mentions in the document ("sodium/iodide symporter" and "NIS" both map
to gene ID 6528). Since the LLM extractor produces surface text, not
normalized concept IDs (entity linking is out of scope here), each
entity is represented by its FIRST surface mention in the document —
a documented simplification/limitation, not a hidden one. See
Decision log.md DEC-009 and Evidence log.md for the corresponding EVID
entry.

BioRED's relation vocabulary is closed (6 types), which fits this
project's existing schema-constrained extraction design (same spirit as
the product domain's ALLOWED_PREDICATES).
"""

from __future__ import annotations

from pathlib import Path

BIORED_RELATION_TYPES = [
    "Positive_Correlation",
    "Negative_Correlation",
    "Association",
    "Bind",
    "Cotreatment",
    "Comparison",
]


def parse_pubtator(path: str | Path) -> list[dict]:
    """Returns a list of document dicts:
    {pmid, title, abstract, text, entities: {id: {type, first_mention}},
     gold_triples: [(subject_text, relation_type, object_text, novelty)]}
    """
    documents = []
    pmid = None
    title = None
    abstract = None
    entities: dict[str, dict] = {}
    relations: list[tuple] = []

    def flush():
        if pmid is None:
            return
        text = f"{title} {abstract}".strip()
        gold_triples = []
        for rel_type, ent1_id, ent2_id, novelty in relations:
            e1 = entities.get(ent1_id)
            e2 = entities.get(ent2_id)
            if e1 is None or e2 is None:
                continue
            gold_triples.append((e1["first_mention"], rel_type, e2["first_mention"], novelty))
        documents.append({
            "pmid": pmid, "title": title, "abstract": abstract, "text": text,
            "entities": entities, "gold_triples": gold_triples,
        })

    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            if not line:
                flush()
                pmid, title, abstract = None, None, None
                entities = {}
                relations = []
                continue

            if "|t|" in line:
                pmid, _, title = line.split("|", 2)
                continue
            if "|a|" in line:
                _, _, abstract = line.split("|", 2)
                continue

            parts = line.split("\t")
            if len(parts) == 6:
                _, start, end, mention_text, entity_type, entity_id = parts
                if entity_id not in entities:
                    entities[entity_id] = {"type": entity_type, "first_mention": mention_text}
            elif len(parts) == 5:
                _, rel_type, ent1_id, ent2_id, novelty = parts
                relations.append((rel_type, ent1_id, ent2_id, novelty))

    flush()  # in case file doesn't end with a blank line
    return documents


def load_biored_split(split: str, root: str = "data/BioRED/BioRED") -> list[dict]:
    """split: 'Train', 'Dev', or 'Test'."""
    path = Path(root) / f"{split}.PubTator"
    return parse_pubtator(path)
