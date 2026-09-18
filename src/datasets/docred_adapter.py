"""DocRED dataset adapter (DEC-020, framework-level public-benchmark
validation). Parses the official DocRED JSON format (human-annotated
dev split, downloaded from the thunlp/docred HuggingFace mirror --
MIT licensed, https://huggingface.co/datasets/thunlp/docred) into the
same (subject, predicate, object) representation used throughout this
project's PKB pipeline.

DocRED's relation vocabulary is closed (96 Wikidata-style relation
types, resolved via rel_info.json) -- same spirit as BioRED's
BIORED_RELATION_TYPES and the product domain's ALLOWED_PREDICATES, and
the reason a schema-guided (not open-phrase) extraction prompt is
needed here, same as BioRED/product, NOT CaRB's open-phrase prompt.

Unlike BioRED (one document, one call, one set of gold triples) and
CaRB (one sentence, no repeated entities), DocRED provides MULTIPLE
evidence sentences per gold (head, relation, tail) triple, and the
same entity is mentioned repeatedly across a document (vertexSet
coreference clusters). That repetition is exactly the structure this
project's PKB/Noisy-Or aggregation is designed to operate on -- each
evidence sentence for a triple becomes one observation, analogous to
each structured/unstructured source-record for a product. This is
what makes DocRED usable for a FRAMEWORK-level test (DEC-020), not
just an extractor-level test like DEC-001 (CaRB) or DEC-021 (TACRED).

Entities are represented by their FIRST surface mention in the
document (same documented simplification as BioRED's adapter) --
entity linking/normalization is out of scope here.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_relation_map(path: str | Path = "data/DocRED/rel_info.json") -> dict[str, str]:
    """Maps Wikidata property IDs (e.g. 'P17') to human-readable names
    (e.g. 'country') -- the closed 96-relation schema."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_docred_split(
    path: str | Path = "data/DocRED/dev.json",
    rel_info_path: str | Path = "data/DocRED/rel_info.json",
) -> list[dict]:
    """Returns a list of document dicts:
    {title, sentences: [str, ...],
     gold_triples: [(subject_text, relation_name, object_text)],
     observations: [
         {subject, relation, object, sentence_id, sentence_text}
     ]}

    `gold_triples` is the deduplicated per-document gold set (for
    computing precision/recall/F1 against DocRED gold). `observations`
    is the flattened, per-evidence-sentence list (one row per
    (triple, evidence sentence) pair) -- feed this into the PKB so
    triples with multiple evidence sentences get multiple observations
    to aggregate over, the whole point of this DEC.
    """
    rel_map = load_relation_map(rel_info_path)

    with open(path, encoding="utf-8") as f:
        raw_docs = json.load(f)

    documents = []
    for doc in raw_docs:
        sentences = [" ".join(tokens) for tokens in doc["sents"]]

        def first_mention(entity_idx: int) -> str:
            return doc["vertexSet"][entity_idx][0]["name"]

        gold_triples = []
        observations = []
        for label in doc["labels"]:
            subject = first_mention(label["h"])
            obj = first_mention(label["t"])
            relation = rel_map.get(label["r"], label["r"])
            gold_triples.append((subject, relation, obj))

            evidence_ids = label.get("evidence", [])
            if not evidence_ids:
                continue
            for sent_id in evidence_ids:
                if sent_id >= len(sentences):
                    continue
                observations.append({
                    "subject": subject,
                    "relation": relation,
                    "object": obj,
                    "sentence_id": sent_id,
                    "sentence_text": sentences[sent_id],
                })

        documents.append({
            "title": doc["title"],
            "sentences": sentences,
            "gold_triples": list(dict.fromkeys(gold_triples)),
            "observations": observations,
        })

    return documents


def closed_predicate_list(rel_info_path: str | Path = "data/DocRED/rel_info.json") -> list[str]:
    """The 96 relation names, for a schema-guided extraction prompt
    (same role as BIORED_RELATION_TYPES / ALLOWED_PREDICATES)."""
    return sorted(load_relation_map(rel_info_path).values())
