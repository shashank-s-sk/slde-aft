"""DEC-019 closed-loop test utility: reconstruct a CandidateBufferAdapter's
exact state at the end of a given iteration by replaying its saved
observations_iteration_N.csv files through fresh accept_candidate() calls.

Verified exact (see dec019_closedloop_control.py's own sanity check, and
manual verification during development): replaying
outputs/dec006_scaleup_probkb/train_kb/observations_iteration_{1,2,3,4}.csv
reproduces exactly the same 475/475 above-threshold triples as the
originally-saved pkb_snapshot_iteration_4.csv, with all 2241 accepted
keys matching exactly. This is safe to build the closed-loop comparison
on top of.

Used because CandidateBufferAdapter doesn't natively support loading a
snapshot CSV back into a resumable object -- the accepted-triple dict's
derived fields (support, competitor_count, etc.) are only correctly
computed by replaying the actual accept_candidate() call sequence, not
by copying snapshot columns directly.
"""

from __future__ import annotations

import pandas as pd

from src.probkb_v2_adapter import CandidateBufferAdapter


def replay_iterations(
    adapter: CandidateBufferAdapter,
    observations_dir: str,
    iterations: list[int],
) -> None:
    """Replay observations_iteration_N.csv for each N in `iterations`, in
    order, into `adapter` (mutated in place) via accept_candidate() +
    end_iteration(), reconstructing exactly the state as of the last
    iteration replayed."""
    for it in iterations:
        obs = pd.read_csv(f"{observations_dir}/observations_iteration_{it}.csv")
        for _, row in obs.iterrows():
            adapter.accept_candidate(
                subject=row["subject"], predicate=row["predicate"], object_value=row["object"],
                confidence=row["observation_confidence"], source_id=row["source_id"],
                source_type=row["source_type"], provenance=row["provenance"],
            )
        adapter.end_iteration(it)


def build_replayed_adapter(
    observations_dir: str,
    iterations: list[int],
    experiment_id: str,
    run_id: str,
    functional_predicates_path: str,
    output_dir: str,
    threshold: float = 0.88,
    shrinkage: float = 0.75,
    gold_keys: set | None = None,
) -> CandidateBufferAdapter:
    """Construct a fresh adapter and replay `iterations` into it. Returns
    the adapter, ready to have accept_candidate() called for a NEW
    iteration on top of the replayed state."""
    adapter = CandidateBufferAdapter(
        experiment_id=experiment_id, run_id=run_id,
        prob_kb_version="conservative_noisy_or_conflict_adjusted",
        functional_predicates_path=functional_predicates_path,
        output_dir=output_dir, threshold=threshold, shrinkage=shrinkage,
        gold_keys=gold_keys or set(),
    )
    replay_iterations(adapter, observations_dir, iterations)
    return adapter
