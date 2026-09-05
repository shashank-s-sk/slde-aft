import csv
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True)
class Triple:
    subject: str
    predicate: str
    object: str

@dataclass
class SentenceRecord:
    sentence_id: str
    text: str
    gold_triples: List[Triple]

def load_carb_gold_tsv(path: Path) -> Dict[str, SentenceRecord]:
    """
    Load CaRB gold TSV and group by sentence.
    Returns: {sentence_text: SentenceRecord}
    """
    sentences = {}
    idx = 0

    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 4:
                continue
            sentence = row[0].strip()
            relation = row[1].strip()
            arg1 = row[2].strip()
            arg2 = row[3].strip()

            if sentence not in sentences:
                idx += 1
                sentences[sentence] = SentenceRecord(
                    sentence_id=f"carb_test_{idx:04d}",
                    text=sentence,
                    gold_triples=[],
                )

            triple = Triple(subject=arg1, predicate=relation, object=arg2)
            sentences[sentence].gold_triples.append(triple)

    return sentences