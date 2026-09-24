import json

from scripts import dec032_biored_analyze as analyze
from src.dec032_biored import evaluate_doc, load_docs, sentence_spans, valid_relation

DOC = {
    "gold_facts": [("Association", "D1", "G2")],
    "mentions": {"D1": ["type II diabetes", "T2D"], "G2": ["HNF-6", "hepatocyte nuclear factor-6"]},
    "first_mention": {"D1": "type II diabetes", "G2": "HNF-6"},
}


def test_sentence_spans_respect_abbreviations():
    title = "A title"
    abstract = "First sentence, e.g. with an abbreviation. Second one (n=3). 3 mice died."
    text = f"{title} {abstract}"
    sents = [text[a:b] for a, b in sentence_spans(title, abstract)]
    assert sents == ["A title", "First sentence, e.g. with an abbreviation.",
                     "Second one (n=3).", "3 mice died."]


def test_evaluators_unordered_and_alias_aware():
    item = ("hepatocyte nuclear factor-6", "Association", "T2D")  # reversed order, non-first mentions
    assert evaluate_doc(DOC, [item], "alias") == {"tp": 1, "fp": 0, "fn": 0}
    assert evaluate_doc(DOC, [item], "strict")["tp"] == 0
    assert evaluate_doc(DOC, [("HNF-6", "Association", "type II diabetes")], "strict")["tp"] == 1
    assert evaluate_doc(DOC, [("HNF-6 gene", "Association", "diabetes")], "relaxed")["tp"] == 1


def test_valid_relation_uses_all_eight_types():
    assert valid_relation("Drug_Interaction") and valid_relation("conversion")
    assert not valid_relation("causes")


def test_real_corpus_loads():
    docs = load_docs()
    assert len(docs) == 500 and sum(len(d["sentences"]) for d in docs) == 5462
    assert all(len(d["fact_sentence_comention"]) == len(d["gold_facts"]) for d in docs)


def test_end_to_end_on_synthetic_extractions(tmp_path, monkeypatch):
    docs = [dict(DOC, doc_idx=i, pmid=str(i), sentences=["s0", "s1", "s2"],
                 fact_sentence_comention=[2]) for i in range(3)]
    monkeypatch.setattr(analyze, "load_docs", lambda: docs)
    run = tmp_path / "llama_sentence"; run.mkdir()
    recs = []
    for d in docs:
        for s, trip in enumerate([("HNF-6", "Association", "T2D"), ("HNF-6", "Association", "T2D"),
                                  ("X", "causes", "Y")]):
            recs.append({"doc_idx": d["doc_idx"], "unit_id": s, "http_status": 200, "error": None,
                         "cost_usd": 0.0, "triples": [dict(zip(("subject", "predicate", "object"), trip))] * (2 if s == 2 else 1)})
    (run / "shard_0of1.jsonl").write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    out = tmp_path / "res.json"
    monkeypatch.setattr("sys.argv", ["x", "--extractions-dir", str(tmp_path), "--out", str(out)])
    analyze.main()
    r = json.loads(out.read_text())["models"]["llama"]["sentence"]
    first = r["measured_first"]
    assert first["g2_facts"] == 3 and first["valid_relation_share"] == 0.5
    assert first["within_sentence_duplicate_observations"] == 3  # the doubled "X causes Y"
    assert r["arms"]["R2"]["admitted"] == 6 and r["arms"]["R3"]["admitted"] == 3
    assert r["arms"]["R3"]["alias"]["precision"] == 1.0
