from src.leakage_split import build_product_split


def test_split_covers_every_index_exactly_once():
    split = build_product_split(n_products=50, seed=7)
    assert sorted(split.keys()) == list(range(1, 51))


def test_split_ratios_match_70_10_20():
    split = build_product_split(n_products=50, seed=7)
    counts = {"train": 0, "val": 0, "test": 0}
    for v in split.values():
        counts[v] += 1
    assert counts == {"train": 35, "val": 5, "test": 10}


def test_split_is_deterministic_given_same_seed():
    split_a = build_product_split(n_products=50, seed=7)
    split_b = build_product_split(n_products=50, seed=7)
    assert split_a == split_b


def test_different_seeds_can_produce_different_split():
    split_a = build_product_split(n_products=50, seed=7)
    split_b = build_product_split(n_products=50, seed=99)
    assert split_a != split_b


def test_invalid_ratios_raise_error():
    try:
        build_product_split(n_products=50, seed=7, train_ratio=0.5, val_ratio=0.4, test_ratio=0.4)
    except ValueError:
        return
    raise AssertionError("expected ValueError for ratios that do not sum to 1.0")
