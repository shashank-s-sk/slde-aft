from src import dec033_protocol as P
from src.extractors import openrouter_openie as O


def test_observations_document_unit_uses_cited_sentences():
    trips = {0: [{"subject": "A", "predicate": "p", "object": "B", "evidence": [0, 2, 9]},
                 {"subject": "C", "predicate": "p", "object": "D", "evidence": []}]}
    obs = P.observations("document", trips, n_sentences=3)
    ab = sorted(o["sent_id"] for o in obs if o["subject"] == "A")
    cd = [o["sent_id"] for o in obs if o["subject"] == "C"]
    assert ab == [0, 2]            # out-of-range citation 9 dropped
    assert cd == [P.DOC_SOURCE]    # no citation: one document-level source


def test_observations_sentence_unit():
    trips = {0: [{"subject": "A", "predicate": "p", "object": "B"}],
             3: [{"subject": "A", "predicate": "p", "object": "B"}]}
    assert sorted(o["sent_id"] for o in P.observations("sentence", trips, 5)) == [0, 3]


def test_corroboration_raw_vs_verified():
    doc = {"gold_facts": [("Association", "C1", "C2")],
           "mentions": {"C1": ["aspirin"], "C2": ["headache"]},
           "first_mention": {"C1": "aspirin", "C2": "headache"},
           "concept_sentences": {"C1": [0, 1], "C2": [0, 1]}}
    obs = [{"sent_id": s, "subject": "aspirin", "predicate": "Association", "object": "headache"}
           for s in (0, 1, 4)]
    c = P.corroboration("biored", doc, obs)
    assert c == {"recovered": 1, "g2_raw": 1, "g2_verified": 1}
    c2 = P.corroboration("biored", doc, [dict(o, sent_id=s) for o, s in zip(obs, (0, 4, 5))])
    assert c2["g2_raw"] == 1 and c2["g2_verified"] == 0  # only one cited sentence co-mentions both


def test_numbered_document():
    assert P.numbered({"sentences": ["First.", "Second."]}) == "[0] First.\n[1] Second."


def test_extractor_keeps_evidence(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content":
                    '[{"subject":"A","predicate":"p","object":"B","evidence":[2,"1","x",2]}]'}}],
                    "usage": {"cost": 0.0}}
    monkeypatch.setattr(O, "post_with_network_retry", lambda *a, **k: (R(), 0, None))
    out = O.extract_openie_triples("t", api_key="k", model="m", keep_evidence=True)
    assert out["triples"][0]["evidence"] == [1, 2]
    out2 = O.extract_openie_triples("t", api_key="k", model="m")
    assert "evidence" not in out2["triples"][0]
