from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.pkb_instrumentation import (
    build_snapshot_dataframe,
    refresh_slot_scores,
    save_iteration_artifacts,
)


def load_functional_predicates(path: str) -> set[str]:
    with open(path, "r", encoding="utf-8") as f:
        policy = json.load(f)

    return set(policy.get("functional_predicates", []))


class CandidateBufferAdapter:
    """
    Wraps a Probabilistic KB run to:
      - maintain an 'accepted' dict compatible with pkb_instrumentation,
      - call refresh_slot_scores after each accepted candidate,
      - save observation and snapshot artifacts at each iteration.
    """

    def __init__(
        self,
        experiment_id: str,
        run_id: str,
        prob_kb_version: str,
        functional_predicates_path: str,
        output_dir: str,
        threshold: float = 0.88,
        gold_keys: Optional[set[Tuple[str, str, str]]] = None,
        shrinkage: float = 0.5,
    ):
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.prob_kb_version = prob_kb_version
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.gold_keys = gold_keys or set()
        self.shrinkage = shrinkage

        self.functional_predicates = load_functional_predicates(
            functional_predicates_path
        )

        # accepted[(subject_norm, predicate, object_norm)] -> entry dict
        self.accepted: Dict[
            Tuple[str, str, str],
            Dict[str, Any],
        ] = {}

        self.iteration = 0

    def accept_candidate(
        self,
        subject: str,
        predicate: str,
        object_value: str,
        confidence: float,
        source_id: str,
        source_type: str,
        provenance: str,
    ) -> None:
        """
        Record a newly accepted candidate and refresh scores for its slot.

        This method is called by your existing PKB loop whenever a candidate
        is accepted (e.g., after passing consistency checks and being merged
        into the KB).
        """
        from src.pkb_instrumentation import (
            normalized_object,
            normalized_slot,
        )

        subject_norm, predicate_norm = normalized_slot(
            subject,
            predicate,
        )
        object_norm = normalized_object(object_value)

        key = (subject_norm, predicate_norm, object_norm)

        if key not in self.accepted:
            self.accepted[key] = {
                "subject": subject,
                "predicate": predicate,
                "object": object_value,
                "confidence": confidence,
                "all_confidences": [confidence],
                "source_ids": [source_id],
                "source_types": [source_type],
                "provenance": [provenance],
                "status": "candidate",
            }
        else:
            entry = self.accepted[key]
            entry["all_confidences"].append(confidence)
            entry["source_ids"].append(source_id)
            entry["source_types"].append(source_type)
            entry["provenance"].append(provenance)
            # Keep the latest confidence as the running value
            entry["confidence"] = confidence

        # Recompute support and final_confidence for this slot
        refresh_slot_scores(
            accepted=self.accepted,
            subject=subject,
            predicate=predicate,
            functional_predicates=self.functional_predicates,
            shrinkage=self.shrinkage,
        )

    def end_iteration(
        self,
        iteration: Optional[int] = None,
    ) -> None:
        """
        Call this at the end of each PKB iteration to:
          - increment iteration counter,
          - build the snapshot DataFrame,
          - save observations and snapshot CSVs.
        """
        if iteration is not None:
            self.iteration = iteration
        else:
            self.iteration += 1

        snapshot_df = build_snapshot_dataframe(
            accepted=self.accepted,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            prob_kb_version=self.prob_kb_version,
            iteration=self.iteration,
            threshold=self.threshold,
            gold_keys=self.gold_keys,
        )

        save_iteration_artifacts(
            observations=[],  # see note below
            snapshot_df=snapshot_df,
            output_dir=self.output_dir,
            iteration=self.iteration,
        )

    def get_accepted(self) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
        return self.accepted