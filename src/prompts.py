"""Shared product-domain JSON-triple extraction prompt template.

Used by both scripts/dec006_evaluate_adapter.py (evaluation) and
scripts/dec006_regenerate_synth_data.py (DEC-006 fine-tuning data), so
the fine-tuned model is trained on the exact task shape it is
evaluated on. Splitting this out fixed a real bug: the original
per-relation "### Instruction / ### Response" training format (matching
SLDE.pdf's Module 4 description literally) taught a different task
than this JSON-array extraction prompt, and the fine-tuned model
scored F1=0.0000 at eval time as a result -- not a fine-tuning
failure, a train/eval format mismatch.
"""

from __future__ import annotations


def build_extraction_prompt(text: str, allowed_predicates: list[str]) -> str:
    return f"""You extract factual product knowledge triples.

Return ONLY a valid JSON array.
Each item must contain: subject, predicate, object, confidence

Allowed predicates:
{", ".join(allowed_predicates)}

Rules:
- Extract only facts explicitly supported by text.
- confidence must be between 0.85 and 0.99.
- Do not invent facts.

Text:
{text}

Example output:
[
  {{"subject":"TechNova Smartphone Max 1","predicate":"manufactured_by","object":"TechNova","confidence":0.95}}
]""".strip()
