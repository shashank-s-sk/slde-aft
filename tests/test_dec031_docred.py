import json

import pytest

from scripts import dec031_docred_analyze as analyze
from src.dec031_docred import (admitted_items, aggregate, alias_index, contested_slots,
                               evaluate_doc, evaluate_doc_first_mention, normalize_b)

DOC = {
    "doc_idx": 0, "title": "T",
    "sentences": ["s0", "s1", "s2"],
    "mentions": [["Barack Obama", "Obama"], ["United States", "U.S."], ["Hawaii"]],
    "first_mention": ["Barack Obama", "United States", "Hawaii"],
    "gold_facts": [(0, "country of citizenship", 1), (0, "place of birth", 2)],
    "evidence_sent_ids": [0, 1],
}


def obs(sent, s, p, o):
    return {"sent_id": sent, "subject": s, "predicate": p, "object": o}


@pytest.mark.parametrize("raw,expected", [
    ("The United States", "united states"),
    ("U.S.", "us"),
    ("Obama's", "obama"),
    ("  A  Tale of Two Cities ", "tale of two cities"),
    ("Jean-Paul", "jean paul"),
    ("an", "an"),
])
def test_normalize_b(raw, expected):
    assert normalize_b(raw) == expected


def test_alias_index_drops_ambiguous_forms():
    doc = {**DOC, "mentions": [["Paris"], ["Paris", "Paris, Texas"]]}
    idx = alias_index(doc)
    assert "paris" not in idx and idx["paris texas"] == 1


def test_keys_pool_variants_differently():
    o = [obs(0, "Obama", "country of citizenship", "U.S."),
         obs(1, "Barack Obama", "country of citizenship", "United States")]
    aliases = alias_index(DOC)
    for key, expect_admitted in (("exact", 0), ("norm", 0), ("alias", 1)):
        cands = aggregate(o, key, "R2", aliases)
        assert len(admitted_items(cands)) == expect_admitted, key
    o2 = [obs(0, "the U.S.", "capital", "x"), obs(1, "US", "capital", "x")]
    assert len(admitted_items(aggregate(o2, "exact", "R2", {}))) == 0
    assert len(admitted_items(aggregate(o2, "norm", "R2", {}))) == 1


def test_r3_counts_distinct_sentences_only():
    o = [obs(0, "Obama", "place of birth", "Hawaii"), obs(0, "Obama", "place of birth", "Hawaii")]
    assert len(admitted_items(aggregate(o, "exact", "R2", {}))) == 1
    assert len(admitted_items(aggregate(o, "exact", "R3", {}))) == 0


def test_contested_slots():
    o = [obs(0, "Obama", "place of birth", "Hawaii"), obs(1, "Obama", "place of birth", "Kenya"),
         obs(2, "Obama", "place of birth", "Hawaii")]
    cands = aggregate(o, "exact", "R2", {})
    assert contested_slots(cands, admitted_only=False) == 1
    assert contested_slots(cands, admitted_only=True) == 0


def test_evaluator_is_alias_aware_and_deduplicates_by_gold_fact():
    items = [("Obama", "country of citizenship", "U.S."),
             ("Barack Obama", "country of citizenship", "United States"),
             ("Obama", "place of birth", "Kenya")]
    assert evaluate_doc(DOC, items) == {"tp": 1, "fp": 1, "fn": 1}
    assert evaluate_doc_first_mention(DOC, items) == {"tp": 1, "fp": 2, "fn": 1}


def test_end_to_end_on_synthetic_extractions(tmp_path, monkeypatch):
    """Extractions built from gold with varied mention spellings: the
    normalised and alias keys must pool more gold facts than the exact
    key, and the evidence-only setting must use a subset of sentences."""
    docs = [dict(DOC, doc_idx=i) for i in range(4)]
    monkeypatch.setattr(analyze, "load_docs", lambda: docs)
    recs = []
    for d in docs:
        spell = {0: ["Obama", "Barack Obama", "obama"], 1: ["U.S.", "United States", "US"]}
        for s in range(3):
            t = [{"subject": spell[0][s], "predicate": "country of citizenship", "object": spell[1][s]}]
            recs.append({"doc_idx": d["doc_idx"], "sent_id": s, "triples": t, "error": None,
                         "http_status": 200, "cost_usd": 0.0})
    (tmp_path / "shard_0of1.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    out = tmp_path / "res.json"
    monkeypatch.setattr("sys.argv", ["x", "--extractions-dir", str(tmp_path), "--out", str(out)])
    analyze.main()
    settings = json.loads(out.read_text())["settings"]
    res = settings["all"]["methods"]
    # sentence spellings: ("Obama","U.S."), ("Barack Obama","United States"), ("obama","US")
    assert res["exact_R2"]["g2_pooled"] == 0  # "u.s." != "us": exact key pools nothing
    assert res["norm_R2"]["g2_pooled"] == 4   # sentences 0 and 2 both key to ("obama", "us")
    assert res["alias_R2"]["g2_pooled"] == 4  # all three resolve to the same gold entities
    assert res["naive"]["primary"]["tp"] == 4
    ev = settings["evidence"]["methods"]      # evidence sentences 0 and 1 only
    assert ev["norm_R2"]["g2_pooled"] == 0 and ev["alias_R2"]["g2_pooled"] == 4
