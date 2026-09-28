"""DEC-035: audit DySECT's released knowledge base (zero API cost).

Reads the demo KB shipped in megagonlabs/dysect
(kbs/demo_acl_2026_run_dec_25_2025.tar.gz, commit 8d6c680) and measures:

1. whether stored overall confidences equal DySECT's conservative Noisy-OR
   over every (confidence, frequency) leaf, i.e. repeat counting with no
   source deduplication (basicLib.findAllConfidenceScores_noLoop);
2. how often the mutual-exclusion division C_agg/(k+1) fired
   (basicLib.overallConfidenceAupdate);
3. for generalization edges, the only KB confidences DySECT's DocRED
   extractor reads (extract_with_kb_fireworks.py, threshold 0.5), how many
   are admitted only because the same (source, document) was counted more
   than once.

Usage: python scripts/dec035_dysect_kb_audit.py <path to extracted kb/> [out.json]
"""
import collections
import json
import os
import sys

import numpy as np

LAMBDA = 0.75  # DySECT default shrinkage (conservativeNoisyOr penaltyTerm)
ADMIT = 0.5    # threshold in extract_with_kb_fireworks.py for generalizations
EXTRACTOR = "Extractor_gpt-4o"  # source name of DySECT's DocRED extractions


def cnor(confs):
    return 1 - np.prod([1 - float(c) * LAMBDA for c in confs])


def leaf_paths(node, trail, out):
    """(path keys, confidence, frequency) for every confidence leaf."""
    for k, v in node.items():
        if not isinstance(v, dict):
            continue
        if k == "confidence":
            for c, sub in v.items():
                f = next(iter(sub.get("frequency", {"1": {}})), "1")
                out.append((tuple(trail), c, int(f)))
        elif k != "overall confidence":
            leaf_paths(v, trail + [k], out)
    return out


def source_doc(trail):
    """Dedup key: the source, plus the DocRED document for extractor leaves."""
    src = trail[trail.index("source") + 1] if "source" in trail else None
    doc = trail[trail.index("instances file") + 1] if "instances file" in trail else None
    return src, doc


def main(root, out_path=None):
    s = collections.Counter()
    conf_obs = collections.Counter()
    src_obs = collections.Counter()
    concepts_rep, concepts_dedup = set(), set()
    for d, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(d, fn), encoding="utf-8") as fh:
                ent = json.load(fh)
            for pred, objs in ent.items():
                if not isinstance(objs, dict):
                    continue
                for obj, node in objs.items():
                    if not isinstance(node, dict) or "iteration" not in node:
                        continue
                    leaves = leaf_paths(node, [], [])
                    if not leaves:
                        continue
                    s["triples"] += 1
                    obs = [c for _, c, f in leaves for _ in range(f)]
                    for t, c, f in leaves:
                        conf_obs[c] += f
                        src_obs[source_doc(t)[0]] += f
                    keys = {source_doc(t)[0] for t, _, _ in leaves}
                    if len(obs) > 1:
                        s["triples_n_obs>1"] += 1
                        if len(keys) == 1:
                            s["triples_n_obs>1_single_source"] += 1
                    a = cnor(obs)
                    oc = node.get("overall confidence")
                    if isinstance(oc, dict) and oc:
                        try:
                            stored = float(next(iter(oc)))
                        except ValueError:
                            stored = None
                        if stored is not None:
                            s["has_stored"] += 1
                            if abs(stored - a) < 1e-6:
                                s["stored_eq_repeat_counted_cnor"] += 1
                            elif stored == 1.0:
                                s["stored_eq_1_trusted_or_seed"] += 1
                            elif stored > 0 and abs(a / stored - 1 - round(a / stored - 1)) < 1e-3 \
                                    and round(a / stored - 1) >= 1:
                                s["mutex_division_fired"] += 1
                            else:
                                s["stored_differs_nonintegral_k(stale)"] += 1
                    if pred == "generalizations" and obj != "Everything":
                        best = {}
                        for t, c, _ in leaves:
                            key = source_doc(t)
                            best[key] = max(best.get(key, 0.0), float(c))
                        dd = cnor(best.values())
                        s["gen_edges"] += 1
                        if a >= ADMIT:
                            s["gen_admitted@0.5_repeat_counting"] += 1
                            concepts_rep.add(obj)
                        if dd >= ADMIT:
                            s["gen_admitted@0.5_dedup_source_doc"] += 1
                            concepts_dedup.add(obj)
                        if a >= ADMIT > dd:
                            s["gen_admitted_only_via_repeats"] += 1
                    ex = [(t, c, f) for t, c, f in leaves if EXTRACTOR in t]
                    if ex:
                        s["docred_extractor_triples"] += 1
                        docs = collections.Counter()
                        for t, _, f in ex:
                            docs[source_doc(t)[1]] += f
                        if sum(docs.values()) > len(docs):
                            s["docred_extractor_repeat_within_one_doc"] += 1
                        if len(docs) > 1:
                            s["docred_extractor_>1_doc"] += 1
    result = {
        "counts": dict(sorted(s.items())),
        "confidence_values_obs_weighted": dict(conf_obs.most_common()),
        "sources_obs_weighted": dict(src_obs.most_common()),
        "distinct_concepts_admitted@0.5": {"repeat_counting": len(concepts_rep),
                                           "dedup_source_doc": len(concepts_dedup)},
    }
    print(json.dumps(result, indent=2))
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
