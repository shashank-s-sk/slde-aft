"""DEC-018 provenance filter — SLDE.pdf claim #5 ("provenance actively
filters synthetic training data quality").

Validated on the DEC-006 200-product PKB run (EVID-029): among the 475
triples that already cross the confidence threshold, the 444 with at
least one STRUCTURED source alongside their unstructured observations
are 100% correct against gold; the 31 with unstructured-only
corroboration (despite being observed 2-21 times each) are 0% correct
-- all are hallucinations, mostly generic device-category nouns
("laptop device", "tablet device") or copied sentence fragments
standing in for the real product name, repeated by the LLM across
extractions and mistaken by Noisy-Or aggregation for corroborating
evidence.

This is therefore a real, evidence-based filter, not a token gesture:
requiring structured corroboration for synthetic-training-data
inclusion is validated to raise precision from 93.5% to 100% on this
dataset, at the cost of dropping 31/475 triples (6.5%).
"""

from __future__ import annotations

from typing import Any


def has_structured_corroboration(source_types: list[str]) -> bool:
    """True if at least one of this triple's observations came from a
    structured source, alongside (or instead of) unstructured ones."""
    return "structured" in source_types


def passes_provenance_filter(entry: dict[str, Any]) -> bool:
    """entry: a dict with a 'source_types' key (list[str]), as produced
    by CandidateBufferAdapter/DeterministicKBAdapter accepted-triple
    entries or a PKB snapshot row (already json.loads'd)."""
    return has_structured_corroboration(entry.get("source_types", []))
