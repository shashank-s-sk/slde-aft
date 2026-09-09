from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import json
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from src.pkb_math import (
    conservative_noisy_or,
    conflict_adjusted_confidence,
)

DEFAULT_SHRINKAGE: float = 0.5

def final_confidence(
    confidences: Iterable[float],
    competitor_count: int,
    shrinkage: float = DEFAULT_SHRINKAGE,
    functional_predicate: bool = True,
) -> float:
    support = conservative_noisy_or(
        confidences,
        shrinkage=shrinkage,
    )

    if not functional_predicate:
        return support

    return conflict_adjusted_confidence(
        support=support,
        competitor_count=competitor_count,
    )

def normalized_slot(
    subject: str,
    predicate: str,
) -> tuple[str, str]:
    return (
        str(subject).strip().lower(),
        str(predicate).strip().lower(),
    )


def normalized_object(value: str) -> str:
    return str(value).strip().lower()


def is_functional_predicate(
    predicate: str,
    functional_predicates: set[str],
) -> bool:
    return str(predicate).strip().lower() in functional_predicates


def accepted_slot_keys(
    accepted: dict[tuple[str, str, str], dict[str, Any]],
    subject: str,
    predicate: str,
) -> list[tuple[str, str, str]]:
    subject_norm, predicate_norm = normalized_slot(
        subject,
        predicate,
    )

    return [
        key
        for key in accepted
        if key[0] == subject_norm and key[1] == predicate_norm
    ]


def competitor_count(
    accepted: dict[tuple[str, str, str], dict[str, Any]],
    subject: str,
    predicate: str,
    object_value: str,
) -> int:
    object_norm = normalized_object(object_value)

    objects = {
        key[2]
        for key in accepted_slot_keys(
            accepted,
            subject,
            predicate,
        )
    }

    return len(objects - {object_norm})


def refresh_slot_scores(
    accepted: dict[tuple[str, str, str], dict[str, Any]],
    subject: str,
    predicate: str,
    functional_predicates: set[str],
    shrinkage: float = DEFAULT_SHRINKAGE,
) -> None:
    for key in accepted_slot_keys(
        accepted,
        subject,
        predicate,
    ):
        entry = accepted[key]

        confidences = entry.get(
            "all_confidences",
            [],
        )

        if not confidences:
            continue

        is_functional = is_functional_predicate(
            entry["predicate"],
            functional_predicates,
        )

        competitors = competitor_count(
            accepted=accepted,
            subject=entry["subject"],
            predicate=entry["predicate"],
            object_value=entry["object"],
        )

        support = conservative_noisy_or(
            confidences,
            shrinkage=shrinkage,
        )

        confidence = final_confidence(
            confidences=confidences,
            competitor_count=competitors,
            shrinkage=shrinkage,
            functional_predicate=is_functional,
        )

        entry["support"] = float(support)
        entry["confidence"] = float(confidence)
        entry["competitor_count"] = int(competitors)
        entry["functional_predicate"] = bool(is_functional)


def make_observation_row(
    triple: Any,
    experiment_id: str,
    run_id: str,
    iteration: int,
    prob_kb_version: str,
) -> dict[str, Any]:
    key = triple.key()

    return {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "prob_kb_version": prob_kb_version,
        "iteration": iteration,
        "subject": triple.subject,
        "predicate": triple.predicate,
        "object": triple.object,
        "triple_key": "|".join(key),
        "observation_confidence": float(triple.confidence),
        "source_id": triple.source_id,
        "source_type": triple.source_type,
        "provenance": triple.provenance[:300],
        "extractor_version": getattr(
            triple,
            "extractor_version",
            None,
        ),
    }


def build_snapshot_dataframe(
    accepted: dict[tuple[str, str, str], dict[str, Any]],
    experiment_id: str,
    run_id: str,
    iteration: int,
    prob_kb_version: str,
    threshold: float,
    gold_keys: set[tuple[str, str, str]] | None = None,
) -> pd.DataFrame:
    rows = []

    for key, entry in accepted.items():
        confidence = float(entry["confidence"])
        previous_confidence = entry.get(
            "previous_snapshot_confidence"
        )

        if previous_confidence is None:
            crossed_up = confidence >= threshold
            crossed_down = False
        else:
            crossed_up = (
                previous_confidence < threshold
                and confidence >= threshold
            )

            crossed_down = (
                previous_confidence >= threshold
                and confidence < threshold
            )

        rows.append({
            "experiment_id": experiment_id,
            "run_id": run_id,
            "prob_kb_version": prob_kb_version,
            "iteration": iteration,
            "subject": entry["subject"],
            "predicate": entry["predicate"],
            "object": entry["object"],
            "triple_key": "|".join(key),
            "observation_count": len(
                entry.get("all_confidences", [])
            ),
            "observation_confidences": json.dumps(
                entry.get("all_confidences", [])
            ),
            "functional_predicate": entry.get(
                "functional_predicate",
                False,
            ),
            "competitor_count": entry.get(
                "competitor_count",
                0,
            ),
            "conservative_noisy_or_support": entry.get(
                "support",
                confidence,
            ),
            "conflict_adjusted_final_confidence": confidence,
            "threshold": threshold,
            "above_threshold": confidence >= threshold,
            "previous_final_confidence": previous_confidence,
            "crossed_threshold_up": crossed_up,
            "crossed_threshold_down": crossed_down,
            "source_ids": json.dumps(
                entry.get("source_ids", [])
            ),
            "source_types": json.dumps(
                entry.get("source_types", [])
            ),
            "provenance": json.dumps(
                entry.get("provenance", [])
            ),
            "gold_label": (
                int(key in gold_keys)
                if gold_keys is not None
                else None
            ),
            "kb_size": len(accepted),
            "status": entry.get("status", "unknown"),
        })

        entry["previous_snapshot_confidence"] = confidence

    return pd.DataFrame(rows)


def save_iteration_artifacts(
    observation_rows: Iterable[dict[str, Any]],
    accepted: dict[tuple[str, str, str], dict[str, Any]],
    output_dir: str | Path,
    experiment_id: str,
    run_id: str,
    iteration: int,
    prob_kb_version: str,
    threshold: float,
    gold_keys: set[tuple[str, str, str]] | None = None,
) -> tuple[Path, Path, pd.DataFrame]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    observations_df = pd.DataFrame(list(observation_rows))

    observations_path = output_path / (
        f"observations_iteration_{iteration}.csv"
    )

    observations_df.to_csv(
        observations_path,
        index=False,
        encoding="utf-8",
    )

    snapshot_df = build_snapshot_dataframe(
        accepted=accepted,
        experiment_id=experiment_id,
        run_id=run_id,
        iteration=iteration,
        prob_kb_version=prob_kb_version,
        threshold=threshold,
        gold_keys=gold_keys,
    )

    snapshot_path = output_path / (
        f"pkb_snapshot_iteration_{iteration}.csv"
    )

    snapshot_df.to_csv(
        snapshot_path,
        index=False,
        encoding="utf-8",
    )

    return observations_path, snapshot_path, snapshot_df