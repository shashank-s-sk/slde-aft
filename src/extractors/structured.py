"""Deterministic structured (CSV-column) extractor. Ported from the
SLDE-AFT notebooks' `extract_structured` cell: no API calls, confidence
fixed at 0.98 per DEC's deterministic structured-source policy.
"""

from __future__ import annotations

_COLUMN_TO_PREDICATE = {
    "brand": "manufactured_by",
    "category": "belongs_to_category",
    "price_usd": "has_price_usd",
    "screen_size_inch": "has_screen_size_inch",
    "ram_gb": "has_ram_gb",
    "storage_gb": "has_storage_gb",
    "battery_life_hours": "has_battery_life_hours",
    "weight_kg": "has_weight_kg",
    "color": "has_color",
    "material": "made_of_material",
    "market_region": "target_market_region",
    "fast_charging": "supports_fast_charging",
    "noise_cancellation": "has_noise_cancellation",
}


def extract_structured(structured_row: dict, source_id: str) -> list[dict]:
    product_name = str(structured_row["product_name"]).strip()
    triples = []
    for col, pred in _COLUMN_TO_PREDICATE.items():
        if col in structured_row and structured_row[col] is not None:
            triples.append({
                "subject": product_name,
                "predicate": pred,
                "object": str(structured_row[col]).strip(),
                "confidence": 0.98,
                "source_id": source_id,
                "provenance": f"structured_row:{product_name}",
                "source_type": "structured",
                "extractor_version": "schema-v1",
            })
    return triples
