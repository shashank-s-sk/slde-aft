"""Deterministic (monotonic max-merge) KB adapter — the DEC-004 "without
Probabilistic KB" ablation target. Mirrors the notebooks'
LockedKnowledgeStore (confidence = max over observations, KB only grows),
but exposes the same interface as CandidateBufferAdapter
(accept_candidate/end_iteration/as_key_set/get_locked_context_strings) so
src/experiment_runner.py can swap between the two KB variants without any
branching logic, and reuses pkb_instrumentation's snapshot/save functions
so both KB variants produce directly comparable output artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.pkb_instrumentation import (
    normalized_object,
    normalized_slot,
    save_iteration_artifacts,
)


class DeterministicKBAdapter:
    def __init__(
        self,
        experiment_id: str,
        run_id: str,
        output_dir: str,
        threshold: float = 0.88,
        gold_keys: Optional[set[Tuple[str, str, str]]] = None,
        min_conf: float = 0.80,
    ):
        self.experiment_id = experiment_id
        self.run_id = run_id
        self.prob_kb_version = "deterministic_max_merge"
        self.output_dir = Path(output_dir)
        self.threshold = threshold
        self.gold_keys = gold_keys or set()
        self.min_conf = min_conf

        self.accepted: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        self.pending_observations: List[Dict[str, Any]] = []
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
        subject_norm, predicate_norm = normalized_slot(subject, predicate)
        object_norm = normalized_object(object_value)
        key = (subject_norm, predicate_norm, object_norm)

        self.pending_observations.append({
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "prob_kb_version": self.prob_kb_version,
            "subject": subject,
            "predicate": predicate,
            "object": object_value,
            "triple_key": "|".join(key),
            "observation_confidence": float(confidence),
            "source_id": source_id,
            "source_type": source_type,
            "provenance": str(provenance)[:300],
            "extractor_version": source_type,
        })

        if key in self.accepted:
            entry = self.accepted[key]
            entry["confidence"] = max(entry["confidence"], float(confidence))
            entry["support"] = entry["confidence"]
            entry["all_confidences"].append(float(confidence))
            entry["source_ids"].append(source_id)
            entry["source_types"].append(source_type)
            entry["provenance"].append(provenance)
        elif float(confidence) >= self.min_conf:
            self.accepted[key] = {
                "subject": subject,
                "predicate": predicate,
                "object": object_value,
                "confidence": float(confidence),
                "support": float(confidence),
                "all_confidences": [float(confidence)],
                "source_ids": [source_id],
                "source_types": [source_type],
                "provenance": [provenance],
                "status": "locked",
                "competitor_count": 0,
                "functional_predicate": False,
            }

    def end_iteration(self, iteration: Optional[int] = None) -> None:
        if iteration is not None:
            self.iteration = iteration
        else:
            self.iteration += 1

        for row in self.pending_observations:
            row["iteration"] = self.iteration

        save_iteration_artifacts(
            observation_rows=self.pending_observations,
            accepted=self.accepted,
            output_dir=self.output_dir,
            experiment_id=self.experiment_id,
            run_id=self.run_id,
            iteration=self.iteration,
            prob_kb_version=self.prob_kb_version,
            threshold=self.threshold,
            gold_keys=self.gold_keys,
        )
        self.pending_observations = []

    def get_accepted(self) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
        return self.accepted

    def as_key_set(self) -> set[Tuple[str, str, str]]:
        return set(self.accepted.keys())

    def get_locked_context_strings(self, n: int = 12) -> List[str]:
        items = sorted(
            self.accepted.values(),
            key=lambda x: (-x.get("confidence", 0.0), x["predicate"], x["subject"]),
        )
        return [
            f'{x["subject"]} | {x["predicate"]} | {x["object"]} | conf={round(x.get("confidence", 0.0), 3)}'
            for x in items[:n]
        ]
