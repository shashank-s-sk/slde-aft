from src import docred_official as O

REL = {"country": "P17", "member of": "P463"}


def _doc():
    return {"mentions": [["Paris"], ["France"], ["NATO"]]}


def test_convert_links_unique_mentions_and_known_relations():
    obs = [{"sent_id": 0, "subject": "Paris", "predicate": "country", "object": "France"},
           {"sent_id": 2, "subject": "Paris", "predicate": "country", "object": "France"},
           {"sent_id": -1, "subject": "France", "predicate": "member of", "object": "NATO"},
           {"sent_id": 1, "subject": "Paris", "predicate": "capital city", "object": "France"},
           {"sent_id": 1, "subject": "Lyon", "predicate": "country", "object": "France"}]
    preds, uns = O.convert(_doc(), obs, REL)
    assert preds == {(0, 1, "P17"): {0, 2}, (1, 2, "P463"): set()}
    assert len(uns) == 2  # off-schema relation; unlinked entity


def test_score_matches_official_arithmetic():
    vs = [[{"name": "Paris"}], [{"name": "France"}], [{"name": "NATO"}]]
    raw = [{"title": "T", "vertexSet": vs,
            "labels": [{"h": 0, "t": 1, "r": "P17", "evidence": [0, 1]},
                       {"h": 1, "t": 2, "r": "P463", "evidence": [3]}]}]
    preds = {"T": {(0, 1, "P17"): {0, 2}, (2, 1, "P17"): {4}}}
    s = O.score(raw, preds, {"T": {("x", "y", "z")}}, {("Paris", "France", "P17")})
    assert s["correct"] == 1 and s["correct_in_train"] == 1
    assert s["strict"]["precision"] == 0.5 and s["strict"]["recall"] == 0.5
    assert s["penalised"]["precision"] == 1 / 3
    assert s["strict"]["ign_precision"] == 0.0   # the only correct fact is in train
    assert s["evidence"]["precision"] == 1 / 3   # 1 correct of 3 predicted evidence sentences
    assert s["evidence"]["recall"] == 1 / 3      # 1 of 3 gold evidence sentences
