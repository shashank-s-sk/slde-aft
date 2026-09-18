"""DEC-003 step 5: computational complexity analysis (prototype vs.
optimized) of the PKB's candidate-acceptance path -- the other
undone DEC-003 deliverable alongside real-data calibration.

Zero API/GPU cost -- pure Python micro-benchmark against the ACTUAL
production code (src/probkb_v2_adapter.CandidateBufferAdapter,
unmodified), plus a standalone illustrative comparison against an
indexed alternative (NOT wired into production -- this project's real
PKB math/acceptance logic is not touched here; DEC-019's replay
pipeline depends on its exact current behavior, so changing it is out
of scope for a complexity write-up).

## Why the current implementation is O(N) per call / O(N^2) cumulative

`CandidateBufferAdapter.accept_candidate` calls
`src.pkb_instrumentation.refresh_slot_scores`, which calls
`accepted_slot_keys(accepted, subject, predicate)`:

    return [key for key in accepted if key[0]==subject_norm and key[1]==predicate_norm]

This is a LINEAR SCAN over every key ever accepted so far, on every
single `accept_candidate` call, regardless of how many of those keys
actually share the (subject, predicate) slot being updated. If N total
observations are accepted over a run, the i-th call costs O(i), so the
cumulative cost is O(1+2+...+N) = O(N^2/2) = O(N^2).

## The proposed optimization (illustrative here, not implemented in
## production)

Index `accepted` by (subject_norm, predicate_norm) -> the small set of
competing objects for that slot: `slot_index[key_prefix] -> set[object_norm]`.
Then the slot lookup a single call needs is O(m) where m is the number
of competing values for THAT slot (bounded by real-world attribute
fan-out -- typically a handful, not the whole KB), not O(N). Cumulative
cost over N observations becomes O(N * m_avg) ~= O(N) for bounded m_avg.

This script empirically demonstrates both curves rather than just
asserting them.

Usage: python -m scripts.dec003_complexity_benchmark
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

from src.probkb_v2_adapter import CandidateBufferAdapter

OUT_DIR = Path("outputs/dec003_complexity_benchmark")
FUNCTIONAL_PREDICATES_PATH = "configs/docred_functional_predicates.json"  # empty policy, reused
CHECKPOINT_SIZES = [100, 500, 1000, 2000, 4000, 8000]


def make_candidate_stream(n: int, seed: int = 42):
    """Generates n (subject, predicate, object, confidence) observations,
    each for a DISTINCT (subject, predicate) slot (occasionally revisited
    with a competing object, mirroring real fan-out) -- critically, the
    number of distinct slots scales WITH n, so `accepted` actually grows
    to size ~n instead of saturating at a small fixed key space. This is
    what's needed to observe accepted_slot_keys' true O(len(accepted))
    linear-scan cost as the KB grows large, not an artifact of a capped
    slot space."""
    rng = random.Random(seed)
    n_slots = max(1, n // 3)  # ~3 observations per slot on average, unbounded growth
    slots = [(f"entity_{i}", f"attr_{i % 20}") for i in range(n_slots)]
    for _ in range(n):
        subject, predicate = rng.choice(slots)
        obj = f"value_{rng.randint(0, 4)}"  # small fan-out per slot
        confidence = rng.uniform(0.5, 1.0)
        yield subject, predicate, obj, confidence


def benchmark_production_adapter(n: int) -> list[dict]:
    """Times the REAL, unmodified CandidateBufferAdapter.accept_candidate
    at increasing KB sizes, recording per-call latency at checkpoints."""
    adapter = CandidateBufferAdapter(
        experiment_id="dec003_complexity", run_id="prototype",
        prob_kb_version="v2", functional_predicates_path=FUNCTIONAL_PREDICATES_PATH,
        output_dir=str(OUT_DIR / "prototype_artifacts"), threshold=0.88, shrinkage=0.5,
    )
    rows = []
    checkpoints = set(CHECKPOINT_SIZES)
    for i, (s, p, o, c) in enumerate(make_candidate_stream(n), start=1):
        t0 = time.perf_counter()
        adapter.accept_candidate(s, p, o, c, source_id=f"call_{i}",
                                  source_type="benchmark", provenance="synthetic")
        elapsed = time.perf_counter() - t0
        if i in checkpoints:
            rows.append({"kb_size": i, "single_call_seconds": elapsed,
                         "accepted_dict_size": len(adapter.accepted)})
    return rows


class IndexedSlotStore:
    """Standalone, illustrative indexed alternative to
    src.pkb_instrumentation.accepted_slot_keys's linear scan -- NOT the
    production PKB, just a same-shape simulation to measure the
    achievable optimized complexity for comparison. Uses the identical
    conservative-Noisy-Or math (src.pkb_math) so the comparison is
    complexity-only, not a different formula."""

    def __init__(self):
        from src.pkb_math import conservative_noisy_or
        self._noisy_or = conservative_noisy_or
        self.slot_index: dict[tuple[str, str], dict[str, list[float]]] = {}

    def accept(self, subject: str, predicate: str, obj: str, confidence: float, shrinkage: float = 0.5):
        key_prefix = (subject.strip().lower(), predicate.strip().lower())
        obj_norm = obj.strip().lower()
        slot = self.slot_index.setdefault(key_prefix, {})
        slot.setdefault(obj_norm, []).append(confidence)
        # O(m) over this slot's own competing objects only, not the whole KB
        for confidences in slot.values():
            self._noisy_or(confidences, shrinkage=shrinkage)


def benchmark_indexed_alternative(n: int) -> list[dict]:
    store = IndexedSlotStore()
    rows = []
    checkpoints = set(CHECKPOINT_SIZES)
    total_accepted = 0
    for i, (s, p, o, c) in enumerate(make_candidate_stream(n), start=1):
        t0 = time.perf_counter()
        store.accept(s, p, o, c)
        elapsed = time.perf_counter() - t0
        total_accepted = sum(len(v) for slot in store.slot_index.values() for v in [slot])
        if i in checkpoints:
            rows.append({"kb_size": i, "single_call_seconds": elapsed,
                         "accepted_dict_size": i})
    return rows


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    max_n = max(CHECKPOINT_SIZES)

    print(f"Benchmarking PRODUCTION CandidateBufferAdapter up to N={max_n} observations...")
    prototype_rows = benchmark_production_adapter(max_n)

    print(f"Benchmarking illustrative indexed alternative up to N={max_n} observations...")
    indexed_rows = benchmark_indexed_alternative(max_n)

    with open(OUT_DIR / "prototype_timings.json", "w", encoding="utf-8") as f:
        json.dump(prototype_rows, f, indent=2)
    with open(OUT_DIR / "indexed_alternative_timings.json", "w", encoding="utf-8") as f:
        json.dump(indexed_rows, f, indent=2)

    print("\n=== Prototype (production, unmodified) -- per-call latency at KB size N ===")
    for row in prototype_rows:
        print(f"  N={row['kb_size']:>5}  single_call={row['single_call_seconds']*1000:.4f} ms")

    print("\n=== Indexed alternative (illustrative, not production) ===")
    for row in indexed_rows:
        print(f"  N={row['kb_size']:>5}  single_call={row['single_call_seconds']*1000:.4f} ms")

    # Quick growth-ratio check: for O(N) per-call, latency at 8x N should be ~8x;
    # for O(1)-ish per-call, latency should stay roughly flat.
    proto_first, proto_last = prototype_rows[0], prototype_rows[-1]
    idx_first, idx_last = indexed_rows[0], indexed_rows[-1]
    n_ratio = proto_last["kb_size"] / proto_first["kb_size"]
    proto_ratio = proto_last["single_call_seconds"] / max(proto_first["single_call_seconds"], 1e-9)
    idx_ratio = idx_last["single_call_seconds"] / max(idx_first["single_call_seconds"], 1e-9)
    print(f"\nKB size grew {n_ratio:.1f}x ({proto_first['kb_size']} -> {proto_last['kb_size']})")
    print(f"Prototype per-call latency grew {proto_ratio:.1f}x  (expect ~{n_ratio:.1f}x for O(N) per call)")
    print(f"Indexed alt.  per-call latency grew {idx_ratio:.1f}x  (expect ~flat for O(1)-ish per call)")

    print(f"\nSaved -> {OUT_DIR}/")


if __name__ == "__main__":
    main()
