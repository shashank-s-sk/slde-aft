import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object: str


def normalize_text(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+%", "%", text)
    return text


def normalize_triple(triple: Triple) -> Triple:
    return Triple(
        subject=normalize_text(triple.subject),
        predicate=normalize_text(triple.predicate),
        object=normalize_text(triple.object),
    )


def compute_precision_recall_f1(
    gold_triples: Iterable[Triple],
    predicted_triples: Iterable[Triple],
):
    gold_set = {normalize_triple(t) for t in gold_triples}
    pred_set = {normalize_triple(t) for t in predicted_triples}

    true_positives = len(gold_set & pred_set)
    false_positives = len(pred_set - gold_set)
    false_negatives = len(gold_set - pred_set)

    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )

    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "gold_count": len(gold_set),
        "prediction_count": len(pred_set),
    }