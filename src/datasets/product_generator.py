"""Deterministic consumer-product record generator.

Faithful port of the `generate_product_record` cell shared by the
SLDE_AFT_DualSource_Final_(20/30/40/50).ipynb notebooks: same attribute
lists, same ALLOWED_PREDICATES schema, same random-draw order. Calling
this with the global `random` module seeded to 42 (as the notebooks do)
reproduces the exact same products for index 1..N regardless of N — see
`src/leakage_split.py` for why that matters.
"""

from __future__ import annotations

import random

ALLOWED_PREDICATES = [
    "manufactured_by", "belongs_to_category", "has_price_usd",
    "has_screen_size_inch", "has_ram_gb", "has_storage_gb",
    "has_battery_life_hours", "has_weight_kg", "has_color",
    "made_of_material", "target_market_region",
    "supports_fast_charging", "has_noise_cancellation",
]

brands = ["Auralex", "PixelWare", "NeoTech", "VoltEdge", "Zenbyte", "TechNova"]
categories = ["smartphone", "laptop", "headphones", "tablet", "smartwatch"]
colors = ["black", "silver", "blue", "white", "green"]
materials = ["aluminum", "plastic", "carbon fiber"]
regions = ["EU", "US", "APAC", "Global"]


def generate_product_record(idx: int):
    category = random.choice(categories)
    brand = random.choice(brands)
    color = random.choice(colors)
    material = random.choice(materials)
    region = random.choice(regions)
    name = f"{brand} {category.title()} {random.choice(['Pro', 'Max', 'Lite', 'Air', 'Plus'])} {idx}"

    price = random.choice([199, 249, 299, 349, 499, 699, 899, 1099, 1299])
    screen = random.choice([6.1, 6.7, 10.9, 11.0, 13.3, 14.0, 15.6])
    ram = random.choice([4, 6, 8, 12, 16, 32])
    storage = random.choice([64, 128, 256, 512, 1024])
    battery = random.choice([8, 10, 12, 14, 18, 20, 24])
    weight = random.choice([0.18, 0.23, 0.42, 0.55, 1.2, 1.45, 1.8])
    fast = random.choice(["yes", "no"])
    noise = random.choice(["yes", "no"]) if category == "headphones" else "no"

    structured = {
        "product_name": name, "brand": brand, "category": category,
        "price_usd": price, "screen_size_inch": screen, "ram_gb": ram,
        "storage_gb": storage, "battery_life_hours": battery, "weight_kg": weight,
        "color": color, "material": material, "market_region": region,
        "fast_charging": fast, "noise_cancellation": noise,
    }

    all_fact_sentences = {
        "manufactured_by": f"{name} is manufactured by {brand}.",
        "belongs_to_category": f"It is a {category} device.",
        "has_price_usd": f"Priced at {price} USD.",
        "has_screen_size_inch": f"The display measures {screen} inches.",
        "has_ram_gb": f"Comes with {ram}GB of RAM.",
        "has_storage_gb": f"Offers {storage}GB of internal storage.",
        "has_battery_life_hours": f"Battery lasts up to {battery} hours.",
        "has_weight_kg": f"Weighs approximately {weight}kg.",
        "has_color": f"Available in {color}.",
        "made_of_material": f"Built with {material} construction.",
        "target_market_region": f"Targeted at the {region} market.",
        "supports_fast_charging": f"Fast charging is {fast}.",
        "has_noise_cancellation": f"Noise cancellation: {noise}.",
    }

    all_preds = list(all_fact_sentences.keys())
    visible_preds = set(random.sample(all_preds, 7))

    unstructured_text = " ".join(
        all_fact_sentences[p] for p in all_preds if p in visible_preds
    )

    gold_structured = [
        (name, "manufactured_by", str(brand), "structured"),
        (name, "belongs_to_category", str(category), "structured"),
        (name, "has_price_usd", str(price), "structured"),
        (name, "has_screen_size_inch", str(screen), "structured"),
        (name, "has_ram_gb", str(ram), "structured"),
        (name, "has_storage_gb", str(storage), "structured"),
        (name, "has_battery_life_hours", str(battery), "structured"),
        (name, "has_weight_kg", str(weight), "structured"),
        (name, "has_color", str(color), "structured"),
        (name, "made_of_material", str(material), "structured"),
        (name, "target_market_region", str(region), "structured"),
        (name, "supports_fast_charging", str(fast), "structured"),
        (name, "has_noise_cancellation", str(noise), "structured"),
    ]

    gold_unstructured = [
        (s, p, o, "unstructured")
        for s, p, o, _ in gold_structured
        if p in visible_preds
    ]

    return structured, {"product_name": name, "text": unstructured_text}, gold_structured, gold_unstructured


def generate_products(n: int, seed: int = 42):
    """Reset the global RNG to `seed` and generate products 1..n in order.

    Matches the notebooks' own `random.seed(42)` call so that product
    index 1..n here is identical to index 1..n inside any of the
    20/30/40/50-product notebooks.
    """
    random.seed(seed)
    records = []
    for idx in range(1, n + 1):
        records.append((idx, *generate_product_record(idx)))
    return records
