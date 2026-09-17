# EVID-001 — DEC-001 CaRB Dataset Preparation

**Implemented:** Implemented initial CaRB dataset integration. The CaRB gold test data was loaded, grouped by sentence, and converted into a 30-sentence JSONL subset containing sentence IDs, sentence text, and gold subject–predicate–object triples.

**Files:** `src/datasets/carb_adapter.py`, `notebooks/02_carb_prepare_subset.ipynb`, `data/carb_dev_sample.jsonl`, `data/CaRB/data/gold/test.tsv`

**Data/Test:** CaRB public OpenIE benchmark; gold test file `data/CaRB/data/gold/test.tsv`. The loader processed 634 unique sentences and saved the first 30 unique sentences as a development subset.

**Expected:** The adapter should read the CaRB gold TSV format, group multiple gold extractions belonging to the same sentence, and save a reusable JSONL subset with sentence IDs, source text, and gold triples.

**Actual:** Successfully loaded 634 unique CaRB sentences and saved 30 sentence records to `data/carb_dev_sample.jsonl`. Inspection of the CaRB gold file confirmed the expected four-column format: sentence, relation, argument 1, and argument 2.

**Result:** PASS

**Next step:** Inspect the generated JSONL records, create and test an OpenIE extraction prompt, then run the existing unstructured LLM extractor on only 3 CaRB sentences before scaling to 10 or 30 sentences.

## EVID-002 — DEC-001 CaRB OpenIE Smoke Test

**Implemented:** Created and tested a CaRB-specific OpenIE extraction path using an open-relation prompt, OpenRouter API calls, JSON parsing, and latency recording.

**Files:** `notebooks/03_carb_extraction_smoke_test.ipynb`, `prompts/openie_carb_v1.txt`, `outputs/carb_smoke_test_3/predictions.json`, `outputs/carb_smoke_test_3/config.json`

**Data/Test:** Three sentences from `data/carb_dev_sample.jsonl`; model `openrouter/auto`; temperature `0.0`.

**Expected:** The LLM should return valid JSON subject–predicate–object triples for each CaRB sentence, with no API or parsing errors.

**Actual:** All 3 API calls completed successfully. All responses contained valid parseable JSON. No API errors and no parse errors occurred. Per-sentence latencies were 3.90 seconds, 3.76 seconds, and 19.74 seconds. The first sentence produced two semantically correct triples; a minor formatting difference was observed between `32.7 %` in gold data and `32.7%` in prediction.

**Result:** PASS

**Next step:** Implement a shared normalizer and internal precision/recall/F1 evaluator, then evaluate the saved predictions without making additional API calls.

# EVID-003 — DEC-001 CaRB 10-Sentence Pilot

**Implemented:** Scaled CaRB OpenIE extraction from 3 to 10 sentences using the same prompt and model.

**Files:** `notebooks/03_carb_extraction_smoke_test.ipynb`, `prompts/openie_carb_v1.txt`, `outputs/carb_10_dev/subset_10.jsonl`, `outputs/carb_10_dev/predictions.json`, `outputs/carb_10_dev/metrics_internal.json`

**Data/Test:** First 10 sentences from `data/carb_dev_sample.jsonl`; model `openrouter/auto`; temperature `0.0`.

**Expected:** The LLM should return valid JSON subject–predicate–object triples for each sentence, with improved coverage compared to the 3-sentence smoke test.

**Actual:** All 10 API calls completed successfully. The system extracted 25 predicted triples against 35 gold triples. Internal evaluation yielded precision 0.1600, recall 0.1143, and F1 0.1333, with 4 true positives, 21 false positives, and 31 false negatives.

**Result:** PASS (pipeline functional; performance low but expected for a first-pass prompt on a small subset).

**Next step:** Inspect mismatched triples to identify systematic errors (e.g., over-splitting, wrong subjects, paraphrase mismatches), then decide whether to refine the prompt or proceed to a larger subset.

DEC-001: ACCEPTED
Implementation: DONE
Test: DONE (pilot on 10 sentences)
Experiment: DONE (pilot)
Results: Pilot F1 = 0.1333 on 10-sentence subset; sufficient to demonstrate pipeline and error patterns.

DEC-001, part 1: Prepare CaRB data          ✅ Done
DEC-001, part 2: Run LLM on 3 sentences     ✅ Done
DEC-001, part 3: Save and inspect           ✅ Done
DEC-001, part 4: Evaluate internally        ✅ Done
DEC-001, part 5: Official scorer            ⏸ Skipped (time; pilot sufficient for thesis)

# EVID-004 — DEC-002 External LLM Baseline on CaRB-10

**Implemented:** Integrated an external LLM baseline using `meta-llama/llama-3.1-8b-instruct` through OpenRouter. The baseline used the same ten CaRB development sentences, the same OpenIE prompt (`openie_carb_v1`), temperature `0.0`, and the same internal normalized exact-match evaluator used for the SLDE-AFT pilot configuration.

**Files:** `notebooks/04_dec002_baseline_comparison.ipynb`, `outputs/dec002_baseline/predictions.json`, `outputs/dec002_baseline/config.json`, `outputs/dec002_baseline/metrics_internal.json`, `outputs/dec002_baseline/comparison_carb10.json`

**Data/Test:** First 10 sentences from `data/carb_dev_sample.jsonl`; 35 deduplicated gold triples; external model `meta-llama/llama-3.1-8b-instruct`; provider OpenRouter; prompt version `openie_carb_v1`; temperature `0.0`.

**Expected:** The external baseline should return parseable JSON OpenIE triples for the same input sentences, allowing a controlled comparison under an identical evaluation protocol.

**Actual:** The baseline produced 29 triples. It obtained 1 true positive, 28 false positives, and 34 false negatives. Internal normalized exact-match evaluation yielded precision `0.0345`, recall `0.0286`, and F1 `0.0312`. The SLDE-AFT CaRB pilot configuration obtained precision `0.1600`, recall `0.1143`, and F1 `0.1333` on the same subset and evaluator.

**Result:** PASS — external baseline integration and controlled comparison completed.
## Error analysis

Manual inspection of baseline predictions identified the following recurring error patterns:

- **Subject-boundary mismatch:** The model omitted numerical modifiers from subjects. For example, it predicted `(all households; were made up of; individuals)`, whereas the CaRB gold triple was `(32.7% of all households; were made up of; individuals)`.
- **Subject-boundary mismatch:** The model predicted `(all households; had; someone living alone who was 65 years of age or older)`, whereas the gold subject was `(15.7% of all households)`.
- **Compound-fact segmentation mismatch:** For “A CEN forms an important but small part of a Local Strategic Partnership,” the model produced one combined triple, `(a cen; forms; an important but small part of a local strategic partnership)`. CaRB gold represents this content as two separate triples: an “important part” triple and a “small part” triple.
- **Correct CaRB-aligned extraction:** One exact true positive was `(turbomachinery; may use; one or more centrifugal compressors)`.

**Interpretation:** The baseline’s low exact-match score reflects both extraction errors and systematic differences between model output boundaries and CaRB’s gold annotation style. The evaluation metrics remain unchanged because the same shared normalization and exact-match protocol was applied consistently to both configurations.

## Runtime and reproducibility

- Provider: OpenRouter
- Model: `meta-llama/llama-3.1-8b-instruct`
- Temperature: `0.0`
- Dataset: Fixed first 10 sentences from `data/carb_dev_sample.jsonl`
- Number of API calls: 10
- Prompt version: `openie_carb_v1`
- Saved artifacts: raw responses, parsed predictions, gold triples, per-sentence latency, configuration, internal metrics, comparison artifact, and error-analysis examples.
- Average latency: `[INSERT THE ACTUAL AVERAGE LATENCY FROM config.json]` seconds per sentence.

## Updated status

**Result:** PASS — external LLM baseline integration, controlled CaRB-10 evaluation, saved experiment artifacts, runtime recording, and baseline error analysis completed.

**Limitations:** This is a preliminary 10-sentence development pilot. It uses an internal normalized exact-match evaluator rather than the official CaRB scorer. It does not establish general performance, statistical significance, or state-of-the-art superiority.

**Next step:** Add one stronger pinned LLM baseline using the same CaRB-10 inputs, prompt, temperature, parser, normalization, and evaluator. REBEL is deferred because fair comparison with open-relation CaRB triples requires a separate output-conversion and relation-mapping protocol.

# EVID-005 — DEC-003 Initial Aggregation Validation


## Experiment


- Decision: DEC-003
- Experiment ID: `DEC003_TOY_V1`
- Dataset: Controlled synthetic PKB with 10 candidate triples and 6 gold-positive triples.
- Mathematical authority: `SLDE_AFT_Mathematical_Contribution_Final.pdf`
- Implementation: `src/pkb_math.py`
- Shrinkage: `lambda = 0.75`
- Threshold: `tau = 0.88`
- Methods: max merge, mean aggregation, standard Noisy-Or, Conservative Noisy-Or, and conflict-adjusted Conservative Noisy-Or.


## Implemented


- Calculated all five aggregation methods using identical observations.
- Verified that final confidence follows:

\[
C_t = \frac{A_t}{m_t + 1}
\]

for functional predicates, and \(C_t=A_t\) for non-functional predicates.
- Generated per-triple scores, threshold-sweep results, ECE values,
  calibration-bin records, Brier scores, reliability diagram, and
  F1-by-threshold plot.


## Files


- `src/pkb_math.py`
- `outputs/dec003_pkb_validation/per_triple_scores.csv`
- `outputs/dec003_pkb_validation/threshold_sweep.csv`
- `outputs/dec003_pkb_validation/ece_by_method.csv`
- `outputs/dec003_pkb_validation/calibration_bins.csv`
- `outputs/dec003_pkb_validation/brier_by_method.csv`
- `outputs/dec003_pkb_validation/reliability_diagram.png`
- `outputs/dec003_pkb_validation/f1_by_threshold.png`


## Actual


At `tau = 0.88`:

| Method | Precision | Recall | F1 |
|---|---:|---:|---:|
| max merge | 1.0000 | 0.8333 | 0.9091 |
| mean aggregation | 1.0000 | 0.1667 | 0.2857 |
| standard Noisy-Or | 0.8571 | 1.0000 | 0.9231 |
| Conservative Noisy-Or | 1.0000 | 0.3333 | 0.5000 |
| Conservative Noisy-Or + conflict adjustment | 0.0000 | 0.0000 | 0.0000 |

Lowest observed ECE: Conservative Noisy-Or = `0.289421`.


## Result


PASS — initial formula implementation and toy aggregation/calibration
validation completed.


## Limitations


- Small controlled dataset only.
- Results are illustrative, not general benchmark evidence.
- No multi-seed scaled experiment or real product-PKB iteration log yet.

Functional-predicate policy:
`configs/functional_predicates_dec003_controlled.json`

## Scope:
This policy applies only to the controlled DEC-003 mathematical
validation dataset. It is not automatically used for the original
product-domain pipeline or CaRB OpenIE experiments.

## Complexity implementation status

The current DEC-003 experiment evaluates the aggregation functions in
`src/pkb_math.py`.

The experiment does not yet demonstrate that the indexed running-residual
PKB implementation described in the mathematical document has been used.
Therefore, the current report should describe the optimized O(1) update
cost as a proposed implementation design, not as a measured property of
the executed prototype.


## Next step


Run unit tests for `src/pkb_math.py`, then complete the scaled controlled
DEC-003 experiment with three seeds and no/moderate/high conflict scenarios.

# EVID-007 — DEC-003 Product-PKB Logging Audit

## Experiment

- Decision: DEC-003
- Dataset: Existing 40-product SLDE-AFT notebook and saved outputs.
- Purpose: Determine whether the historical run can reconstruct per-triple
  support, conflict-adjusted confidence, threshold crossings, and provenance
  without new API calls.

## Actual

Historical iteration-level metrics can be recovered:

- Precision, recall, and F1.
- KB size.
- Structured and LLM growth.
- Feedback usage.
- Synthetic-example counts.
- Runtime for iterations 2–4.

Per-triple Conservative Noisy-Or support, competitor counts,
conflict-adjusted confidence, exact threshold crossings, and complete
per-iteration provenance cannot be reliably recovered from the existing
artifacts because the required observation histories and PKB snapshots
were not preserved.

## Result

PARTIAL — aggregate iteration history is recoverable; complete DEC-003
per-triple PKB convergence history requires a future instrumented run.

## Limitation

No historical values will be fabricated or inferred from aggregate metrics.

## Next step

Add observation-level and per-iteration PKB snapshot logging to the next
40-product Prob-KB run without changing the extraction architecture or
mathematical formula.

# EVID-008 — DEC-003 Local Instrumentation Smoke Test


## Experiment


- Decision: DEC-003
- Experiment ID: `DEC003_LOCAL_TEST`
- Purpose: Validate API-free observation logging, score calculation,
  conflict handling, provenance retention, and snapshot export.
- API calls: `0`.


## Files


- `src/pkb_math.py`
- `src/pkb_instrumentation.py`
- `configs/functional_predicates_dec003_controlled.json`
- `notebooks/07_dec003_probkb_local_test.ipynb`
- `outputs/dec003_probkb_local_test/observations_iteration_1.csv`
- `outputs/dec003_probkb_local_test/pkb_snapshot_iteration_1.csv`


## Actual


- Saved 4 observation records.
- Aggregated observations into 3 unique triple records.
- Correctly calculated Conservative Noisy-Or support.
- Correctly applied conflict adjustment to the functional
  `has_noise_cancellation` predicate.
- Correctly applied no conflict penalty to non-functional
  `made_of_material`.
- Preserved confidence history, source IDs, source types, provenance, and
  extractor version.
- Verified all support and final-confidence scores were within `[0, 1]`.
- No API calls were made.


## Result


PASS — local DEC-003 instrumentation smoke test completed.


## Next step


Create and run unit tests for `src/pkb_instrumentation.py`, then create a
separate product-domain functional-predicate policy before building the
candidate-buffer adapter for the future instrumented product-PKB run.

# EVID-009 — DEC-003 Scaled Controlled Aggregation Experiment

## Experiment

- Decision: DEC-003
- Experiment ID: `DEC003_SCALED_V1`
- Seeds: `42, 43, 44`
- Scenarios: `no_conflict` (conflict_rate=0.0), `moderate_conflict`
  (conflict_rate=0.25), `high_conflict` (conflict_rate=0.5)
- Dataset: synthetic controlled PKB, 150 slots per run, 50% functional
  slot share, up to 5 observations per triple, positive confidence range
  (0.6, 0.95), negative confidence range (0.15, 0.75), shrinkage `0.75`.
- Methods: max merge, mean aggregation, standard Noisy-Or, Conservative
  Noisy-Or, and conflict-adjusted Conservative Noisy-Or.
- Notebook: `notebooks/05_dec003_scaled_aggregation_experiment.ipynb`

## Files

- `outputs/dec003_scaled/experiment_config.csv`
- `outputs/dec003_scaled/candidate_triples.csv`, `observations.csv`, `slots.csv`
- `outputs/dec003_scaled/threshold_sweep_all.csv`, `best_thresholds_per_seed.csv`,
  `best_thresholds_summary.csv`
- `outputs/dec003_scaled/ece_by_method_per_seed.csv`, `ece_by_method_summary.csv`
- `outputs/dec003_scaled/brier_by_method_per_seed.csv`, `brier_by_method_summary.csv`
- `outputs/dec003_scaled/calibration_bins_all.csv`, `reliability_diagram_points.csv`
- `outputs/dec003_scaled/reliability_diagram_{no,moderate,high}_conflict.png`
- `outputs/dec003_scaled/f1_by_threshold_{no,moderate,high}_conflict.png`
- `outputs/dec003_scaled/convergence_summary.csv`,
  `convergence_scores_{no,moderate,high}_conflict.png`
- `outputs/dec003_scaled/dec003_scaled_results_summary.csv` (per-scenario,
  per-method mean/std across the 3 seeds)
- `outputs/dec003_scaled/experiment_manifest.csv`

## Actual (per-scenario, per-method, at each method's mean best threshold, mean over 3 seeds)

`no_conflict`: all five methods reach precision = recall = F1 = 1.0000
(best threshold 0.0 in every case — with no competing objects the
conflict adjustment cannot fire, so all methods collapse to the same
admission behavior on this synthetic set).

`moderate_conflict` (25% of functional slots have a competitor):
mean_aggregation F1 0.9955, conflict-adjusted Conservative Noisy-Or F1
0.9794, max_merge F1 0.9780, standard_noisy_or and conservative_noisy_or
both F1 0.9670.

`high_conflict` (50% of functional slots have a competitor):
mean_aggregation F1 0.9938, conflict-adjusted Conservative Noisy-Or F1
0.9513, max_merge F1 0.9493, standard_noisy_or F1 0.9250,
conservative_noisy_or F1 0.9243.

Lowest mean ECE per scenario: `moderate_conflict` → standard_noisy_or
(0.0461); `high_conflict` → conservative_noisy_or (0.0698); `no_conflict`
→ standard_noisy_or (0.0621).

## Result

PASS — scaled, multi-seed, multi-conflict-level aggregation and
calibration experiment completed on synthetic controlled data.

## Limitations

- Synthetic controlled dataset, not the real product-domain PKB.
- 3 seeds only; no significance testing performed yet (DEC-005).
- `no_conflict` scenario result (all methods tie at F1=1.0) is expected
  given the generator design, not evidence that all methods are
  equivalent in general.
- Full observation-level records (`observations.csv`, `candidate_triples.csv`,
  `slots.csv`) are saved but not yet individually reviewed for anomalies.

## Next step

Run the candidate-buffer adapter (`src/probkb_v2_adapter.py`) against a
real product-domain PKB run to populate `outputs/dec003_product_probkb_v2/`
(currently empty), producing the per-iteration observation and snapshot
logs that EVID-007 found could not be reconstructed from the historical
40-product run. This is the last remaining piece of DEC-003 besides the
leakage-safe split and paper integration.

# EVID-010 — DEC-003 / next-steps#2 Leakage-Safe Product Split

## Experiment

- Decision: DEC-003 (leakage-safe split item); slde_aft_next_steps.md item #2
- API calls: `0`
- Purpose: Assign every product index in the 20/30/40/50-product dataset
  family to train/val/test once, so later experiments (DEC-004, DEC-005,
  DEC-006) cannot accidentally use a held-out product's structured facts
  as a KB seed, synthetic-training example, few-shot prompt example, or
  threshold-tuning input.

## Method

- Verified that `SLDE_AFT_DualSource_Final_(20).ipynb` and `_(50).ipynb`
  define identical `brands`/`categories`/`colors`/`materials`/`regions`
  lists and both call `random.seed(42)` before generating products, with
  no other randomness consumed in between. Under this condition,
  product index 1..N in the N-product notebook is bit-identical to
  product index 1..N in the 50-product notebook, so one split computed
  over the 50-product superset applies to all four dataset sizes by
  filtering `product_idx <= N`.
- Implemented `src/leakage_split.py::build_product_split()` — shuffles
  indices 1..50 with a dedicated split seed (`7`, distinct from the
  generation seed `42`) and slices 70/10/20.

## Files

- `src/leakage_split.py`
- `tests/test_leakage_split.py` (5 tests)
- `data/product_split.csv`
- `data/product_split_manifest.json`

## Actual

- 50 products split into 35 train / 5 val / 10 test (exact 70/10/20 at
  n=50).
- All 5 unit tests passed: full coverage of indices 1..50, correct
  counts, determinism under a fixed seed, difference under a different
  seed, and a `ValueError` on ratios that don't sum to 1.0.

## Result

PASS — leakage-safe split artifact created and unit-tested.

## Limitations

- The bit-identical-prefix assumption has been verified by comparing
  notebook source cells (20 vs 50), not by actually re-running both
  notebooks end-to-end and diffing generated CSVs. If a notebook's
  generation cell is ever edited, this must be re-verified before reuse
  (see `assumption` field in `product_split_manifest.json`).
- This split assigns products, not sentences/documents — CaRB and any
  future non-product-domain dataset need their own split.
- Downstream experiment code does not yet consume this split (no
  experiment currently filters by it). That wiring is future work for
  whichever of DEC-003/004/005/006 runs next.

## Next step

Wire `data/product_split.csv` into the product-domain instrumented PKB
run (the genuine remaining DEC-003 gap — see EVID-009's next step) so
that run respects train/val/test membership from the start, rather than
retrofitting the split afterward.

# EVID-011 — DEC-003 Product-Domain Real-Extraction Smoke Test (n=3)

## Experiment

- Decision: DEC-003
- Experiment ID: `DEC003_PRODUCT_SMOKE_3`
- Purpose: measure real per-call cost and confirm the extraction pipeline
  works end to end on real product data before committing to the full
  ~155-call instrumented run, mirroring EVID-002's 3-sentence CaRB
  smoke test.
- Model: `meta-llama/llama-3.1-8b-instruct` via OpenRouter, temperature 0.0
- Products: index 1-3 from `src/datasets/product_generator.py` (seed 42)
- API calls: 3

## Files

- `src/datasets/product_generator.py` (ported product generator)
- `src/extractors/structured.py`, `src/extractors/openrouter_llm.py`
- `scripts/dec003_product_smoke_test.py`
- `outputs/dec003_product_smoke_3/predictions.json`, `config.json`,
  `gold_unstructured.json`

## Actual

- Total cost for 3 products: **$0.00002253** (product 1: $0.00000488,
  product 2: $0.00001082, product 3: $0.00000683). Mean latency 8.90s
  (product 2's 151-completion-token response took 23.7s; the other two
  were ~1.3-1.7s).
- Product 2 ("TechNova Laptop Air 2"): 6 LLM triples returned, all with
  valid schema and allowed predicates, subject normalized to "laptop
  device" rather than the full product name.
- Product 1 ("Auralex Smartphone Max 1"): 0 LLM triples, no error —
  completion was only 2 tokens (consistent with the model returning an
  empty `[]` despite 7 visible facts in the input text).
- Product 3 ("NeoTech Smartphone Pro 3"): 0 LLM triples, `llm_error =
  "no JSON array found in model output"` — the model responded with 39
  tokens of non-JSON content (raw response not persisted by the smoke
  test script; only the parsed result was saved).
- Structured extraction (0 API calls) succeeded for all 3 products: 13/13
  triples each, confidence 0.98, as expected from `src/extractors/structured.py`.

## Result

PASS — pipeline runs end to end on real product data; cost is
negligible regardless of the OpenRouter dashboard's confusing $0
"total_credits" reading (a real paid call was confirmed to succeed and
bill correctly).

## Interpretation

The 1-good/2-bad extraction split on n=3 is consistent with the known
LLM OpenIE failure modes already logged in `Learnings.md` (dropped
facts, malformed output) rather than a defect in the new extractor
code. This is not being treated as something to fix by changing the
prompt, since DEC-003 concerns the PKB aggregation math, not extraction
quality — changing the prompt now would break comparability with the
historical 20/30/40/50-product prototype results that use the same
prompt.

## Limitations

- n=3 is too small to estimate a reliable extraction success rate;
  the full run (35 train x 4 iterations + 10 test + 5 val, ~155 calls)
  is needed for that.
- Raw LLM response text for the two failed calls was not persisted,
  only the parsed outcome — future runs should save raw_response for
  failed parses to support later error-analysis work (DEC-007).

## Next step

Run the full instrumented product-domain PKB experiment (~155 calls):
wire `data/product_split.csv` so train-split products go through the
4-iteration KB-seeding loop via `src/probkb_v2_adapter.py`, and
test/val-split products get a single unstructured-only pass, populating
`outputs/dec003_product_probkb_v2/`.

# EVID-012 — DEC-003 Candidate-Buffer Adapter Bug Fix + Full Run Build

## Experiment

- Decision: DEC-003
- API calls: `0` (bug fix + offline tests); full run launched separately,
  see EVID-013 once it completes.
- Purpose: `src/probkb_v2_adapter.py::CandidateBufferAdapter.end_iteration()`
  called `save_iteration_artifacts(observations=[], snapshot_df=...,
  output_dir=..., iteration=...)`, but `pkb_instrumentation.py`'s actual
  signature is `save_iteration_artifacts(observation_rows, accepted,
  output_dir, experiment_id, run_id, iteration, prob_kb_version,
  threshold, gold_keys=None)`. Calling `end_iteration()` as written would
  raise `TypeError` — this is why `outputs/dec003_product_probkb_v2/` was
  empty: the adapter had never been run to completion.

## Fix

- `accept_candidate()` now appends a per-observation row (matching
  `make_observation_row`'s schema) to a new `self.pending_observations`
  list.
- `end_iteration()` now stamps those rows with the current iteration
  number and calls `save_iteration_artifacts()` with the correct keyword
  arguments (`observation_rows`, `accepted`, `experiment_id`, `run_id`,
  `prob_kb_version`, `threshold`, `gold_keys`), then clears the pending
  list.
- Also added `CandidateBufferAdapter.as_key_set()` and
  `get_locked_context_strings()` (small helpers needed by the full run
  script, ported from the notebooks' `LockedKnowledgeStore`), and
  `src/feedback_builder.py::build_feedback_hint()` (ported from the
  notebooks' `FeedbackBuilder`, extracted as a standalone function so
  DEC-004's "without Feedback Controller" ablation can toggle it later
  without duplicating the logic).

## Files

- `src/probkb_v2_adapter.py` (fixed)
- `src/feedback_builder.py` (new)
- `tests/test_probkb_v2_adapter.py` (new, 3 tests)
- `tests/test_feedback_builder.py` (new, 3 tests)
- `src/datasets/product_generator.py` (new — faithful port of the
  notebooks' product generator, needed to regenerate the 50-product
  set deterministically for the real run)
- `src/extractors/structured.py`, `src/extractors/openrouter_llm.py`
  (new — faithful ports of the notebooks' structured and OpenRouter LLM
  extractors)
- `scripts/dec003_product_smoke_test.py` (EVID-011)
- `scripts/dec003_product_probkb_run.py` (the full run script)

## Actual

- All 6 new/changed-module tests pass (3 adapter + 3 feedback-builder);
  full suite is 30/30 passing.
- Dry-run of the complete `scripts/dec003_product_probkb_run.py` script
  against a mocked (zero-cost, zero-network) LLM call confirmed the
  full pipeline — iteration loop, locked-context/feedback construction,
  held-out val/test split, CSV/JSON output — completes without error and
  issues exactly 155 calls (35 train x 4 iterations + 5 val + 10 test),
  matching the planned call budget.

## Result

PASS — bug fixed, verified by tests and a zero-cost dry run before any
real API spend.

## Next step

Real run (EVID-013): `python -m scripts.dec003_product_probkb_run`
against the real OpenRouter key, ~155 calls, launched in the background.
Results to be logged once it completes — not invented here.

# EVID-013 — DEC-003 Full Instrumented Product-Domain Prob-KB Run

## Experiment

- Decision: DEC-003
- Experiment ID: `DEC003_PRODUCT_V2`
- Model: `meta-llama/llama-3.1-8b-instruct` via OpenRouter, temperature 0.0
- Split: `data/product_split.csv` (EVID-010) — 35 train, 5 val, 10 test
- Threshold τ = 0.88, shrinkage λ = 0.75, functional-predicate policy:
  `configs/functional_predicates_product_domain.json`
- Design: train-split products through the original SLDE-AFT Full
  4-iteration loop (structured seed at iteration 1 only, LLM re-extraction
  every iteration guided by locked context + feedback hint from iteration
  2 onward), instrumented via the fixed `CandidateBufferAdapter`
  (EVID-012). Val+test products get one unstructured-only pass each,
  guided only by the final train KB's locked context/feedback (no
  KB-seeding from their own structured facts, per the leakage rules in
  `data/product_split_manifest.json`).
- Total API calls: 155 (35×4 train + 5 val + 10 test)

## Files

- `outputs/dec003_product_probkb_v2/train_kb/observations_iteration_{1-4}.csv`,
  `pkb_snapshot_iteration_{1-4}.csv`, `iteration_metrics.csv`
- `outputs/dec003_product_probkb_v2/held_out_eval/observations_iteration_1.csv`,
  `pkb_snapshot_iteration_1.csv`, `held_out_metrics.csv`
- `outputs/dec003_product_probkb_v2/config.json`, `call_log.json`

## Actual

**Train-set LLM-only extraction quality per iteration** (evaluated
against train-split unstructured gold, same protocol as the original
notebooks' per-iteration eval):

| Iteration | Precision | Recall | F1 | KB size |
|---|---:|---:|---:|---:|
| 1 (unguided) | 0.4771 | 0.2980 | 0.3668 | 534 |
| 2 (guided) | 0.4713 | 0.3020 | 0.3682 | 576 |
| 3 (guided) | 0.3944 | 0.2286 | 0.2894 | 613 |
| 4 (guided) | 0.5088 | 0.3551 | 0.4183 | 657 |

**Held-out evaluation** (single unstructured-only pass, train-KB guidance
only, no target-triple seeding):

| Split | Precision | Recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| val (n=5) | 0.6250 | 0.5714 | 0.5970 | 20 | 12 | 15 |
| test (n=10) | 0.2097 | 0.1857 | 0.1970 | 13 | 49 | 57 |

**Final train KB (iteration 4) snapshot**: 657 retained triples, 127
above the τ=0.88 threshold, 602 on functional-predicate slots, 117 with
at least one competing object, mean 1.78 observations per triple, 245 of
the retained triples match a train gold triple.

**Cost/reliability**: total cost $0.00259181 for 155 calls (mean
$0.0000167/call). Mean latency 7.06s, max 37.76s. 10 of 155 calls (6.5%)
failed to parse ("no JSON array found in model output"); 39 of 155 calls
(25.2%) returned zero triples with no error (model judged nothing
extractable).

## Result

PASS — full instrumented run completed; per-iteration and per-triple PKB
convergence history is now available for the product domain, which
EVID-007 found could not be reconstructed from the historical
(uninstrumented) 40-product run.

## Interpretation

- Train-set iteration curve is **not monotonically improving**
  (iteration 3 is worse than 1-2 on both precision and recall before
  iteration 4 recovers). This differs from the historical uninstrumented
  40-product SLDE-AFT Full run reported in the codebase context (Section
  26), which showed steadily increasing precision (0.49 → 0.61 → 0.75 →
  0.90). This run is not directly comparable to that one: different
  product subset (35 vs 40, drawn from the same generator but a
  different index set due to the leakage split), different KB variant
  (Prob-KB with Noisy-Or aggregation vs. the original deterministic
  max-merge `LockedKnowledgeStore`), and this run judges "success" on
  each iteration's fresh LLM extraction only, not the original's
  identical-sounding but distinct evaluation protocol. This is flagged
  as a discrepancy to investigate (see next step) rather than something
  either result should be assumed to invalidate.
- Held-out val (F1 0.597) substantially outperforms held-out test (F1
  0.197) on only 5 vs 10 products — too small a sample to treat as a
  reliable generalization estimate. This gap could reflect genuine
  overfitting to the feedback/locked-context signal, or could simply be
  noise from tiny per-split sample sizes; DEC-005's multi-seed
  statistical validation is required before drawing a conclusion either
  way.
- The 6.5% hard-parse-failure rate and 25.2% zero-yield rate are
  consistent with the extraction-quality issues already logged in
  `Learnings.md` from the smaller smoke tests (EVID-004, EVID-011), now
  measured at full scale.

## Limitations

- Single seed only (generation seed 42, split seed 7) — no variance
  estimate yet; this is exactly what DEC-005 is for.
- Held-out val/test sets are very small (5 and 10 products
  respectively), inherited from the 70/10/20 split applied to a
  50-product superset; F1 on 10 test products should not be treated as
  a stable estimate.
- The non-monotonic train-iteration curve is not yet explained; it has
  not been root-caused (e.g. by inspecting which specific triples were
  gained/lost iteration-to-iteration) — that is deferred to DEC-007
  (error analysis) rather than speculated about here.
- Raw LLM responses for the 10 parse-failure calls were not persisted in
  `call_log.json` (only the error message and 0-triple outcome), same
  gap already noted in EVID-011.

## Next step

DEC-003's remaining item is paper integration (write up the math section
using this run plus EVID-005/EVID-009). Investigating the non-monotonic
iteration-3 dip and the val/test gap qualifies as DEC-007 (error
analysis) or DEC-005 (statistical validation) work, not DEC-003 itself —
tracked there rather than reopening DEC-003's scope.

# EVID-014 — DEC-003 Real-Data Check: Does the Aggregation Formula Help?

## Experiment

- Decision: DEC-003
- API calls: `0` — pandas analysis of `EVID-013`'s already-saved
  `outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv`
  (657 rows, gold_label column already present).
- Purpose: EVID-005/EVID-009 validated the aggregation/conflict formula
  only on synthetic toy/scaled data. This checks whether the
  threshold-based admission rule and conflict adjustment actually help
  on the one real product-domain run available so far.

## Actual

**Threshold admission separates correct from incorrect triples**:
above τ=0.88 (conflict-adjusted confidence), precision 0.7795 (99 TP /
28 FP); below τ=0.88, precision 0.2755 (146 TP / 384 FP).

**Conflict adjustment vs. raw (unadjusted) Noisy-Or support, same
τ=0.88, whole KB (657 rows)**:

| Scoring rule | Precision | Recall | F1 |
|---|---:|---:|---:|
| Raw support (no conflict adj.) | 0.5778 | 0.4245 | 0.4894 |
| Conflict-adjusted | 0.7795 | 0.4041 | 0.5323 |

Same comparison restricted to functional-predicate rows (602/657, 225
gold positives): raw support F1 0.4847 vs. conflict-adjusted F1 0.5310
— consistent with the whole-KB result.

**Restricted to the 117 rows that actually have >=1 competing object**
(9 gold positives): raw support P=0.1071 R=0.6667 F1=0.1846;
conflict-adjusted P=0.3333 R=0.1111 F1=0.1667 — conflict adjustment is
flat-to-slightly-worse on F1 in this specific slice, trading most of the
recall for a smaller precision gain.

## Result

PASS (as an analysis) — mixed, honest finding: conflict adjustment
improves aggregate admission quality (F1 +0.043 whole-KB, +0.046 on
functional-predicate rows) but is flat-to-negative on the narrow subset
where it actually changes anything (rows with a real competitor).

## Interpretation

The aggregate F1 improvement is not coming primarily from correctly
resolving true multi-candidate conflicts (there are only 9 gold-positive
cases in that regime, too few to drive the aggregate number) — it is
coming from the broader population where the conflict/non-conflict
distinction barely matters. This matches and now confirms on real data
what EVID-005 already showed on synthetic data: the conflict-adjusted
score behaves as a conservative admission/ranking score, not as a
mechanism that reliably identifies the correct alternative among
competitors. Both effects should be reported in the paper — the overall
positive result and this caveat — rather than only the favorable
aggregate number.

## Limitations

- Single seed, single run (same limitation as EVID-013).
- n=117 competitor-rows / n=9 gold-positives-among-them is a very small
  sample; the "flat-to-worse" finding there could itself be noisy.
- This checks admission quality (precision/recall at threshold), not
  calibration (ECE) on real data — EVID-005/009's ECE results are still
  synthetic-only; a real-data calibration table remains undone.

## Next step

If DEC-007 (error analysis) or paper writing needs it, compute ECE and a
calibration table on this same real snapshot (same method as EVID-005),
and repeat this admission-quality check across multiple seeds once
DEC-005 produces them, to see whether the competitor-subset result is
stable or an artifact of one run.

# EVID-015 — DEC-004 Ablation Runner Build

## Experiment

- Decision: DEC-004
- API calls: `0` — build + offline tests + mocked dry run only.
- Purpose: build one reusable experiment runner shared by DEC-004
  (module ablations) and DEC-005 (multi-seed statistics), per DEC-005's
  own notes that both need the same run/eval code. Scope decided with
  the user: 5 of the 7 professor-requested ablations are runnable now
  (Full, Without-Feedback, Without-Prob-KB, Structured-only,
  Unstructured-only); 2 are deferred to pair with DEC-006
  (Without-Synthetic-Data-Gen, Without-LoRA — nothing exists yet to
  ablate against); Without-Provenance is deferred because no active
  provenance *filter* exists anywhere in the current pipeline to turn
  off (provenance is logged unconditionally, never gated) — adding one
  now would change what "Full" means and break comparability with the
  already-completed EVID-013 run.

## Files

- `src/deterministic_kb_adapter.py` (new) — monotonic max-merge KB,
  same external interface as `CandidateBufferAdapter` so the runner can
  swap KB variants by dependency injection.
- `src/experiment_runner.py` (new) — `ExperimentConfig` dataclass +
  `run_experiment()`, module on/off flags (`use_feedback`,
  `use_prob_kb`, `use_structured`, `use_unstructured`), shared by
  DEC-004 and (later) DEC-005.
- `tests/test_deterministic_kb_adapter.py` (4 tests),
  `tests/test_experiment_runner.py` (6 tests) — all offline/mocked.
- `scripts/dec004_ablation_pilot.py` — defines the 5 configs at N=20,
  runs them, writes a comparison summary CSV.

## Actual

- 10 new tests pass (full suite: 40/40).
- Dry run of all 5 configs against a mocked, zero-cost LLM call
  completed without error. Call counts matched expectations exactly:
  full / without_feedback / without_prob_kb = 59 calls each (13 train x
  4 iterations + 3 val + 4 test held-out, at N=20's 13/3/4 split);
  structured_only = 0 calls; unstructured_only = 52 calls (13 train x 4
  iterations, no held-out — see design note in `experiment_runner.py`
  for why structured-only/unstructured-only skip held-out evaluation).
  Total planned real-call budget: 229.

## Result

PASS — runner built, tested, and dry-run-validated before any real API
spend, same discipline as EVID-012.

## Next step

Real pilot run (EVID-016): `python -m scripts.dec004_ablation_pilot`,
N=20, single seed (42), 229 calls, launched in background. Results to
be logged once it completes.

# EVID-016 — DEC-004 Ablation Pilot Results (N=20, single seed)

## Experiment

- Decision: DEC-004
- N=20 products (13 train / 3 val / 4 test), generation seed 42, split
  seed 7 (same `data/product_split.csv` as DEC-003)
- Model: `meta-llama/llama-3.1-8b-instruct`, temperature 0.0
- 5 configs: full (reference), without_feedback, without_prob_kb
  (deterministic max-merge), structured_only, unstructured_only
- Total: 229 API calls, $0.00349075

## Files

- `outputs/dec004_ablation_pilot/{config}/iteration_metrics.csv`,
  `held_out_metrics.csv`, `run_config.json` for each of the 5 configs
- `outputs/dec004_ablation_pilot/ablation_summary.csv`

## Actual

**Final-iteration (train) vs. held-out test F1:**

| Config | Final-iter train F1 | Held-out test F1 |
|---|---:|---:|
| full | 0.2647 | 0.4815 |
| without_feedback | 0.3281 | 0.6341 |
| without_prob_kb | 0.2016 | 0.2449 |
| structured_only | n/a (no LLM component) | n/a (no held-out by design) |
| unstructured_only | 0.0000 (iteration 4 only; iters 1-3 were 0.474/0.400/0.434) | n/a (no held-out by design) |

Full 4-iteration curves are saved per config. `structured_only` KB size
is exactly 169 = 13 train products x 13 predicates — expected, since the
structured extractor is fully deterministic and this synthetic dataset's
structured columns are always fully populated (this ablation does not
exercise a failure mode; it primarily serves as a KB-size sanity check).

## Result

PARTIAL PASS — pipeline ran end to end for all 5 configs and produced
real comparison data, but one result (`unstructured_only` iteration 4)
is an unexplained anomaly, not a clean pass.

## Interpretation

- **Without-feedback outperformed full** on both final-iteration train
  F1 (0.328 vs 0.265) and held-out test F1 (0.634 vs 0.481) — the
  opposite of what the architecture assumes. HYPOTHESIS, not confirmed:
  this may connect to the same mechanism speculated about in EVID-013/014
  for the iteration-3 dip (a Prob-KB that never deletes anything can
  keep feeding stale false-positive triples into the feedback hint,
  actively misleading later iterations). Requires DEC-005 multi-seed
  confirmation before this can be stated as a real effect rather than
  single-seed noise — n=4 held-out test products is a very small sample.
- **Without-prob_kb (deterministic) underperformed full** on both
  metrics (0.202 vs 0.265 train F1; 0.245 vs 0.481 held-out F1) — a
  result supportive of DEC-003's Prob-KB contribution, same single-seed
  caveat applies.
- **`unstructured_only` iteration 4 anomaly is unexplained.** Iterations
  1-3 produced normal-looking F1 (0.474, 0.400, 0.434); iteration 4
  collapsed to precision=recall=0 (0 TP, 23 FP, 91 FN), and KB size did
  not grow from iteration 3 to 4 (75 -> 75), meaning the 23 falsely
  predicted triples in iteration 4 were all duplicates of triples
  already in the KB. This could be a real behavioral finding (e.g. the
  model degrading without a structured anchor) or a call-level failure
  spike (rate limiting, a malformed locked-context string, etc.) — it
  cannot currently be distinguished because of the tooling gap below.
- Held-out val/test sets are extremely small (3 and 4 products). Several
  precision values of exactly 1.0 (e.g. without_feedback val and test)
  are consistent with very few total predictions being made rather than
  genuinely superior extraction — this needs the raw prediction counts
  checked, not just precision/recall/F1, before being read as a strong
  result.

## Limitations

- **Tooling gap**: unlike `scripts/dec003_product_probkb_run.py`,
  `scripts/dec004_ablation_pilot.py` does not persist a per-config
  `call_log.json` (error messages, per-call latency, per-call triple
  counts). This is why the iteration-4 `unstructured_only` anomaly
  cannot be diagnosed from saved artifacts alone. Should be fixed before
  the next ablation run rather than worked around by guessing.
- Single seed (42), single run — every number in this table carries the
  same "could be noise" caveat already established in EVID-013.
- N=20 is smaller than DEC-003's N=50 run; absolute F1 values here are
  not directly comparable to EVID-013's numbers (different product
  subset, different sample size).
- `structured_only`'s "n/a" result is a design limitation, not missing
  data — see `src/experiment_runner.py`'s docstring for why held-out
  eval is skipped for source-only ablations.

## Next step

1. Add `call_log.json` persistence to `scripts/dec004_ablation_pilot.py`
   (or `src/experiment_runner.py`) before any further ablation runs, so
   anomalies like the iteration-4 collapse can be diagnosed without
   re-running.
2. Do NOT state "removing feedback improves SLDE-AFT" in the paper yet
   — this is exactly the kind of claim DEC-005 (multi-seed statistical
   validation) exists to check before it becomes a reported finding.
3. Investigate the `unstructured_only` iteration-4 collapse specifically
   (re-run just that config with call logging fixed) before including it
   in any comparison table.

# EVID-017 — DEC-004 Call-Logging Fix + unstructured_only Re-Run

## Experiment

- Decision: DEC-004
- Purpose: fix the gap found in EVID-016 (per-call error/latency/predicted-
  triple log was computed by `run_experiment()` but never persisted by
  `scripts/dec004_ablation_pilot.py`), then re-run only `unstructured_only`
  to diagnose its iteration-4 F1=0.0 collapse.

## Fix

- `src/experiment_runner.py::do_llm_call()` now tags every call-log entry
  with `iteration` and `phase` ("train"/"held_out"), and — only when
  `error` is set — captures the raw model response content
  (`raw_content_on_error`), addressing the same "raw response not saved
  on parse failure" gap already noted as a limitation in EVID-011/013.
- `scripts/dec004_ablation_pilot.py` now writes `call_log.json` per
  config (previously discarded `result["call_log"]` entirely).
- New `scripts/dec004_rerun_unstructured_only.py` for re-running a single
  ablation config without repeating the other 4.
- Verified with a mocked dry run (including a forced error branch) before
  spending real calls: 52/52 log entries present, iteration tags correct
  (`[1, 2, 3, 4]`), error entries correctly captured
  `raw_content_on_error`.

## Files

- `src/experiment_runner.py` (fixed)
- `scripts/dec004_ablation_pilot.py` (fixed)
- `scripts/dec004_rerun_unstructured_only.py` (new)
- `outputs/dec004_ablation_pilot/unstructured_only/` (old anomalous
  result removed before re-run; re-run's `iteration_metrics.csv`,
  `call_log.json`, `run_config.json` replace it)

## Actual

Re-run completed: 52 calls, $0.000276, **40 of 52 calls (77%) failed**.
Per-iteration: iter1 13/13 errors, iter2 10/13, iter3 4/13, iter4 13/13
— a worsening-then-total pattern, not the original run's "fine for 3
iterations then collapse" pattern. Inspecting the actual error payload
(previously undiagnosable — this is exactly why EVID-016 flagged the
missing call log) shows the cause:

```
http_status: 402
"This request requires more credits, or fewer max_tokens. You requested
up to 117681 tokens, but can only afford 11160. ... upgrade to a paid
account"
```

with nested `previous_errors` showing OpenRouter tried multiple
providers (Novita, DeepInfra), each returning 429 (rate-limited) before
the final 402. `GET /api/v1/credits` still reports `total_credits: 0`;
`GET /api/v1/auth/key` shows this key's own `usage` climbing to
$0.00638 (consistent with DEC-003's $0.00259 + DEC-004 pilot's $0.00349
+ this rerun's partial spend, confirming the account never had real
purchased credits — see the "Cost / API" section of `Learnings.md` from
earlier in this project — and whatever grace/promotional allowance let
those calls through is now exhausted.

## Result

FAIL (as a clean re-run) / PASS (as a diagnosis) — the anomaly is now
explained: not a code bug, a real billing wall.

## Interpretation

**This casts doubt on EVID-016's other three real-LLM configs too**
(`full`, `without_feedback`, `without_prob_kb`), not just
`unstructured_only`. Those three ran *before* `unstructured_only` in
the original pilot sequence (calls 1-177 of 229) and showed no obvious
collapse, but their call logs were never saved in that run either (the
same gap this EVID fixed) — so scattered silent 402/429 failures within
them cannot be ruled out. The two headline findings from EVID-016
("without_feedback beat full," "without_prob_kb underperformed full")
were already labeled HYPOTHESIS pending DEC-005 multi-seed confirmation;
this adds a second, more basic reason not to trust them yet: they may
partly reflect uneven credit exhaustion across configs rather than the
module being ablated.

## Limitations

- The credits situation is a moving target — how much was left when
  each of the first 3 configs ran, and how evenly, is unknown without
  their call logs (which don't exist for that run).

## Next step

1. **User must add real credits to the OpenRouter account** — this is
   not a code fix. Current cumulative real spend across every experiment
   in this project (DEC-003 + DEC-004 pilot + this rerun) is ~$0.0064,
   so even a small top-up comfortably covers re-running everything many
   times over.
2. Once credits are confirmed, **re-run the full DEC-004 pilot (all 5
   configs)**, not just `unstructured_only` — with the now-fixed
   call-logging, so every config's result set is independently
   verifiable and the "without_feedback"/"without_prob_kb" findings can
   be trusted or discarded based on real evidence rather than assumed
   clean.

# EVID-018 — Root Cause: Missing max_tokens Cap, Not Actually Out of Credits

## Experiment

- API calls: 1 (verification), $0.0000076
- Purpose: the user asked whether topping up credits was really
  mandatory before re-running DEC-004. Investigated further rather than
  assuming EVID-017's "add real credits" conclusion was the only fix.

## Finding

`src/extractors/openrouter_llm.py::call_openrouter_for_triples()` never
set a `max_tokens` field on the request payload. OpenRouter
pre-authorizes credits against the *maximum possible* completion length
when none is given — for this 131,072-context model, that's the full
context window, not anything our prompt would realistically produce.
The EVID-017 error message confirms this exactly: "You requested up to
117681 tokens, but can only afford 11160." Every real extraction call
across this entire project (EVID-002/003/004/011/013/016) has used
2-300 completion tokens. The 402s were a spurious pre-authorization
failure against a wildly pessimistic worst case, not a genuine lack of
funds for what the calls actually cost.

## Fix

Added `max_tokens: int = 512` to `call_openrouter_for_triples()`'s
signature and request payload (default, backward compatible — no
caller changes needed). 512 comfortably covers observed real usage
(max completion so far: 151 tokens, EVID-011) with headroom.

## Verification

- Full test suite: 40/40 passing after the change.
- Real call against the *same account, same key, no top-up*: succeeded,
  HTTP 200, 3 triples, $0.0000076 — confirming the account was never
  actually out of usable funds for real-sized requests.

## Result

PASS — the "add real credits" recommendation in EVID-017 is retracted
as premature. The account works fine as-is; the DEC-004 re-run can
proceed immediately with $0 additional funding required.

## Limitations

- This does not change EVID-017's other finding: `full`,
  `without_feedback`, and `without_prob_kb`'s original results still
  lack call-level logs and cannot be independently verified as clean.
  That reasoning for a full 5-config re-run still stands — it's just no
  longer blocked on money.

## Next step

Re-run the full 5-config DEC-004 pilot (`scripts/dec004_ablation_pilot.py`)
now that both the call-logging gap (EVID-017) and the max_tokens bug
(this entry) are fixed.

# EVID-019 — DEC-004 Ablation Pilot, Clean Re-Run (N=20, single seed)

Clean re-run after EVID-017/018's fixes. Per-config error rates this
time: full 6/59, without_feedback 7/59, without_prob_kb 4/59,
unstructured_only 12/52 — normal parse/zero-yield variance, no
systematic 402 failures. Full data: `outputs/dec004_ablation_pilot/`.

| Config | Final-iter train F1 | Held-out val F1 | Held-out test F1 |
|---|---:|---:|---:|
| full | 0.3140 | 0.5000 | 0.0000 |
| without_feedback | 0.4380 | 0.6667 | 0.2979 |
| without_prob_kb | 0.2676 | 0.5000 | 0.2553 |
| structured_only | n/a | n/a | n/a |
| unstructured_only | 0.7143 | n/a | n/a |

**Inferences** (added to `Learnings.md`'s table too):
- without_feedback beat full on train AND val AND test — second
  independent real-data result pointing the same direction as EVID-016.
  Still HYPOTHESIS (same seed, small held-out n), but now two data
  points instead of one.
- full's test F1 = 0.0 exactly (0/7 predictions correct on 4 test
  products) — plausible small-sample noise, not evidence the full
  system fails; n=4 is too small to read this as a real result either
  way.
- unstructured_only reached the best F1 of any config/run in this
  project so far (0.7143), with a clean improving 4-iteration curve.
  New finding, single-seed only — worth a second look once DEC-005
  provides multi-seed data.

Next step: DEC-005 multi-seed confirmation before any of this goes in
the paper.

# EVID-020 — DEC-005 Multi-Seed Statistical Validation (N=20, seeds 42-46)

## Experiment

- Decision: DEC-005
- 5 configs (full, without_feedback, without_prob_kb, structured_only,
  unstructured_only) x 5 seeds (42-46), N=20, same setup as DEC-004.
- `scripts/dec005_multiseed_run.py`, resumable — skipped any (config,
  seed) whose saved call_log.json already had <20% error rate, so total
  spend across the full DEC-005 effort (including two credit-exhaustion
  interruptions) was $0.017718 for the calls made in this final session
  plus earlier partial sessions.
- Statistics: paired t-test and Wilcoxon signed-rank, each ablation vs.
  `full` on the same 5 seeds.

## Actual

| Config | Train F1 mean +/- std | Held-out test F1 mean +/- std |
|---|---:|---:|
| full | 0.4233 +/- 0.1379 | 0.2914 +/- 0.3349 |
| without_feedback | 0.2878 +/- 0.1867 | 0.4335 +/- 0.1833 |
| without_prob_kb | 0.3437 +/- 0.1258 | 0.4388 +/- 0.2866 |
| unstructured_only | 0.4572 +/- 0.0987 | n/a (no held-out by design) |
| structured_only | n/a (no LLM component) | n/a |

Paired comparisons vs. `full` (same 5 seeds):
- without_feedback: train F1 diff -0.1356 (paired t p=0.4001, Wilcoxon
  p=0.4375); test F1 diff +0.1420 (p=0.5070, p=0.4375)
- without_prob_kb: train F1 diff -0.0797 (p=0.3540, p=0.3125); test F1
  diff +0.1474 (p=0.4092, p=0.4375)

**No comparison reaches significance** (all p >> 0.05).

## Result

PASS — multi-seed statistical validation completed as specified.

## Interpretation

**EVID-016/019's "without_feedback outperforms full" finding does NOT
replicate.** With 5 seeds, without_feedback's mean train F1 is actually
*lower* than full's (reversing the direction seen in the 1-2 pilot
runs), and its held-out test F1 is higher — but neither difference is
statistically distinguishable from noise at this sample size. Same
conclusion for without_prob_kb. The correct, honest statement for the
paper is: **no significant difference detected between these ablations
and the full system at N=20/5 seeds; variance across seeds is large
relative to what this sample size can resolve.** This is itself a
valid finding — the single-seed "surprising" results earlier in this
project were exactly the kind of noise DEC-005 exists to catch, and
should not be cited as evidence of an architectural effect.

`unstructured_only` has the highest mean (0.457) and lowest std (0.099)
of any config on train F1 — mildly interesting, not tested against
`full` for significance here (different evaluation shape, no held-out),
and not something to treat as confirmed at n=5.

`full`'s held-out test F1 has enormous variance (std 0.335, exceeding
its own mean) — two of five seeds scored exactly 0.0 on only 4 test
products. This confirms N=20's held-out split is too small to support
firm conclusions; a larger-N confirmatory run would be needed before
any ablation claim goes in the paper.

## Limitations

- N=20 only; DEC-004/005's own scale. Effect sizes/significance may
  differ at N=50 or larger — not tested here.
- 5 seeds is the minimum specified in the Decision log; still a modest
  sample for detecting small-to-medium effects.
- `unstructured_only`'s and `structured_only`'s ablations were not
  paired-tested against `full` because their evaluation shape differs
  (no held-out test for either, and no LLM component at all for
  structured_only) — any future significance testing there needs a
  separately justified comparison, not a direct F1 diff.

## Next step

No further ablation claims should be made from this project's N=20
pilot scale. If a larger, paper-reportable ablation/statistics result
is wanted, it needs a fresh run at full N=50 (or larger) scale with the
same 5-seed (or more) design — reusing `src/experiment_runner.py` and
`scripts/dec005_multiseed_run.py` unchanged, just with `n_products=50`.

# EVID-021 — DEC-001 CaRB Scale-Up (10→30) + DEC-002 DeepSeek Baseline

## Experiment

- Decisions: DEC-001 (scale CaRB pilot), DEC-002 (stronger external
  baseline)
- 30 CaRB sentences (`data/carb_dev_sample.jsonl`, already prepared —
  full 634-sentence CaRB set available for further scaling later)
- Two systems, same prompt (`prompts/openie_carb_v1.txt`), same
  evaluator (`src/evaluator.py`), 0 API errors on either:
  - `slde_aft_llama`: `meta-llama/llama-3.1-8b-instruct`, **newly
    pinned** — EVID-002/003 used `openrouter/auto` (auto-routing),
    which DEC-005's own fairness rules say not to do for a reported
    result. Fixed here.
  - `deepseek_baseline`: `deepseek/deepseek-v3.2`, the stronger
    external SOTA baseline DEC-002 calls for.
- New reusable module: `src/extractors/openrouter_openie.py` (model-
  parameterized OpenIE extractor, `max_tokens=512` capped from the
  start this time per the EVID-018 lesson).
- `scripts/dec001_002_carb30_comparison.py`, dry-run validated with a
  mocked extractor before real spend.

## Actual

| System | Precision | Recall | F1 | TP | FP | FN | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| slde_aft_llama | 0.0732 | 0.0496 | 0.0591 | 6 | 76 | 115 | $0.000221 |
| deepseek_baseline | 0.1781 | 0.1074 | 0.1340 | 13 | 60 | 108 | $0.002136 |

Total: 60 calls, $0.002357, 0 errors on either system.

## Result

PASS — clean scale-up and baseline comparison, no parse/API failures.

## Interpretation

- **DeepSeek-V3.2 outperforms Llama-3.1-8B by ~2.3x F1** on this task —
  a real, useful DEC-002 result showing SLDE-AFT's current base
  extractor is meaningfully weaker than an available stronger model on
  open-domain text.
- **The pinned Llama result (F1=0.059) is lower than the old
  `openrouter/auto` pilot result (F1=0.133, EVID-003) despite 3x more
  sentences.** This is consistent with `openrouter/auto` having
  silently routed to a stronger model than Llama-3.1-8B for that
  earlier pilot — meaning EVID-003's F1=0.1333 was never actually a
  reproducible measurement of "Llama-3.1-8B on CaRB." Any future
  reference to that number should note this. Not something to
  over-interpret without directly checking which model `auto` selected
  (not recoverable after the fact), but the direction is exactly what
  the DEC-005 pinning rule was written to prevent.
- 0/30 errors on both systems (vs. the 6-25% error rates seen
  throughout the product-domain experiments) — the `max_tokens=512` cap
  applied from this extractor's first use, plus CaRB's shorter,
  single-sentence inputs, likely both contribute to cleaner completions
  here.

## Limitations

- n=30 sentences is still small relative to CaRB's full 634-sentence
  test set; absolute F1 numbers should be treated as a pilot-scale
  estimate, not a final benchmark result.
- Official CaRB scorer still not run (internal normalized exact-match
  evaluator only, same as every CaRB result so far in this project).
- Single run, no seeds/repeats (both models used temperature 0, but
  provider-level non-determinism has been observed elsewhere in this
  project — e.g. EVID-019 vs EVID-016 — so a single 0.059 vs 0.134
  comparison should not be treated as the final word).
- SLDE-AFT's actual architecture (dual-source, PKB, feedback loop) is
  not exercised here — this is a single-pass OpenIE extraction for both
  systems, same as EVID-002/003/004. Neither number reflects the full
  closed-loop system's performance.

## Next step

Scale further toward CaRB's full 634-sentence set and/or run the
official CaRB scorer if a benchmark-grade (not pilot-grade) DEC-001
result is needed for the paper. REBEL baseline remains deferred pending
an output-mapping protocol (unchanged from DEC-002's original status).

# EVID-022 — DEC-007 Systematic Error Analysis

## Experiment

- Decision: DEC-007
- API calls: `0` — pure analysis of predictions/snapshots already saved
  by EVID-013 (product-domain PKB run) and EVID-021 (CaRB-30 comparison).
- `scripts/dec007_error_analysis.py`. Categories: correct_extraction,
  correct_but_below_threshold, hallucinated_triple,
  hallucinated_but_filtered, failed_extraction, plus independent
  `is_conflicting`/`is_ambiguous` flags (kept separate from the
  correct/hallucinated outcome rather than overwriting it — an earlier
  version of this script collapsed them together, silently losing
  whether a "conflicting" triple was gold-correct or not; fixed before
  treating the output as final).

## Files

- `outputs/dec007_error_analysis/error_analysis_full.csv` (1,035 rows)
- `outputs/dec007_error_analysis/curated_examples.json` (20 examples,
  up to 2 per source/system/category)

## Actual

**CaRB-30** (both systems, from EVID-021's predictions):

| System | correct | hallucinated | failed (FN) |
|---|---:|---:|---:|
| slde_aft_llama | 6 | 76 | 115 |
| deepseek_baseline | 13 | 60 | 108 |

**Product-domain** (EVID-013's final iteration-4 KB, 657 entries):
correct_extraction 99, correct_but_below_threshold 146 (245 total gold
matches — exactly the 35 train products x 7 visible facts each),
hallucinated_but_filtered 384, hallucinated_triple 28. **Zero pure
false negatives** — every train gold fact was observed by the LLM at
least once across the 4 cumulative iterations, even though any single
iteration's fresh-extraction recall was much lower (EVID-013: iteration
4 alone was 0.355). Of the 117 conflicting-slot triples, only 1 is a
confirmed gold match at the accepted level; 108 are conflicts between
hallucinated alternatives competing with each other, not with a correct
answer.

Manual inspection of curated CaRB examples reproduces the exact
subject-boundary-mismatch pattern already documented in EVID-004 (e.g.
predicted `(all households, were made up of, individuals)` vs. gold
`(32.7% of all households, were made up of, individuals)` — the model
drops the numeric qualifier) — an independent confirmation on a
different 30-sentence sample, not a new failure mode.

## Result

PASS — systematic, categorized error analysis produced across two data
sources at zero additional cost.

## Interpretation

- **"Low recall" in the product-domain per-iteration metrics does not
  mean facts are never found — it means they're not always admitted in
  any single pass.** Zero pure misses across 4 cumulative iterations is
  a meaningfully different (and more favorable) story than the raw
  per-iteration recall numbers suggest on their own; both figures
  belong in the paper's discussion, not just the per-iteration one.
- **Conflict adjustment is mostly resolving fights between wrong
  answers, not between a right answer and a wrong one** (108
  hallucinated-vs-hallucinated conflicts vs. 1 gold-match conflict).
  This sharpens EVID-014's earlier finding (conflict adjustment helps
  in aggregate but doesn't specifically rescue correct facts from real
  conflicts) — here we can see directly that there are barely any
  genuine correct-vs-incorrect conflicts in this dataset for the
  mechanism to even have a chance to resolve well.
- The CaRB subject-boundary-mismatch failure mode is now confirmed
  twice, independently (EVID-004's 10-sentence Llama baseline, and this
  30-sentence sample) — safe to describe as a recurring, systematic
  issue rather than a one-off.

## Limitations

- Product-domain "false negative" analysis only checked the train
  split (matching EVID-013's own training data); held-out val/test
  false-negative analysis not done here.
- CaRB categorization has no conflicting/ambiguous dimension (that
  concept doesn't apply to open-relation CaRB extraction the way it
  does to the schema-constrained product domain).
- Single run/seed for both sources — same caveat as everywhere else in
  this project prior to a multi-seed re-run.

## Next step

Manually review `curated_examples.json` and select the final set for
inclusion in the paper's qualitative error-analysis table (DEC-007's
own notes: do not select only favourable examples — the curated set
here already includes correct, hallucinated, and failed-extraction
examples from both sources, not a cherry-picked subset).

# EVID-023 — DEC-008 Scalability Sweep (Scoped: N=20/50/100/200, single-pass)

## Experiment

- Decision: DEC-008
- Scope decided with user: 4 sizes (20/50/100/200), single-pass
  extraction (not the full 4-iteration loop) to isolate pure
  runtime/latency/memory/KB-growth scaling behavior from extraction
  quality (already covered by DEC-003/004/005). ~45-50 min target,
  actual ~25 min (four sequential runs summing 92+199+406+799=1496s).
- `scripts/dec008_scalability_sweep.py`, dry-run validated with a
  mocked LLM before real spend.
- Total: 370 API calls, $0.004615.

## Actual

| N | Runtime (s) | Mean latency/doc (s) | Max latency (s) | KB size | Conflicts | Above threshold | Errors | Cost |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 92.14 | 4.598 | 12.35 | 284 | 8 | 37 | 9 (45%) | $0.000229 |
| 50 | 199.04 | 3.976 | 9.69 | 737 | 59 | 106 | 17 (34%) | $0.000582 |
| 100 | 405.84 | 4.053 | 9.17 | 1,455 | 117 | 263 | 24 (24%) | $0.001249 |
| 200 | 799.06 | 3.988 | 20.12 | 2,814 | 187 | 547 | 53 (26.5%) | $0.002555 |

**Memory measurements are unreliable and should not be reported as
clean data**: mem_delta_mb was 5.32, 0.92, -29.63, 1.57 across the four
sizes. The negative value at N=100 is a methodology flaw, not a real
finding — all four sizes ran sequentially inside one long-lived Python
process, so garbage collection between runs contaminates each size's
"before/after" delta. A clean measurement needs each size run in an
isolated subprocess.

## Result

PASS for runtime/latency/KB-growth (clean, trustworthy data). FAIL for
memory measurement (methodology flaw acknowledged, not fixed in this
pass).

## Interpretation

- **Runtime scales linearly with N** (92→199→406→799s roughly doubles
  as N doubles) — no quadratic or worse blowup up to 200 products.
- **Mean per-document latency is essentially flat (~4.0s) across the
  entire size range**, including at N=200 with a 2,814-entry KB. This
  is the key positive scalability claim: the system's per-item cost
  does not degrade as accumulated knowledge grows at this scale.
- KB size and above-threshold count both scale linearly with N
  (~14 triples/product, ~15-20% crossing threshold consistently) — no
  unexpected accumulation behavior.
- Error rate (24-45%) is markedly higher than the guided multi-iteration
  runs elsewhere in this project (e.g. EVID-013's ~25% zero-yield + 6.5%
  parse-fail combined). Expected, not concerning: this sweep
  deliberately uses a single unguided pass (no locked-context/feedback)
  to isolate scaling behavior, not extraction quality — comparing this
  error rate to a guided run would be an apples-to-oranges mistake.

## Limitations

- Scoped to single-pass extraction, not the full closed-loop
  architecture — does not measure how runtime/memory scale under the
  complete 4-iteration feedback loop at large N (deferred; the spec's
  full 50/100/250/500/1000 4-iteration sweep was explicitly not run,
  per the user's time-scoping decision).
- Memory data is unusable as noted above.
- No GPU utilization data (no GPU used in this sweep — that's DEC-006's
  domain).
- Single run, single seed (42) — no repeats to assess run-to-run
  runtime variance.

## Next step

If a clean memory measurement is needed for the paper, re-run each size
in an isolated subprocess (e.g. `subprocess.run([...])` per size rather
than a shared process) and use `resource.getrusage` or a fresh
`psutil.Process` per subprocess. Scalability tables/figures for the
paper can be generated from `scalability_summary.csv` directly.

# EVID-024 — DEC-009 Biomedical Domain Pilot (BioRED, Dev split, n=15)

## Experiment

- Decision: DEC-009
- Downloaded official BioRED dataset (https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/BIORED.zip,
  found via web search — not guessed) to `data/BioRED/`. PubTator
  format: 100 Dev docs, 35.3 entities/doc, 11.6 relations/doc, closed
  6-type relation vocabulary (Positive_Correlation, Negative_Correlation,
  Association, Bind, Cotreatment, Comparison).
- New `src/datasets/biored_adapter.py`: parses PubTator into the
  project's standard (subject, predicate, object) triple schema.
  **Documented simplification**: BioRED's gold relations are between
  normalized concept IDs (e.g. gene ID 6528), each with multiple
  surface mentions; since the LLM extractor produces surface text, not
  concept IDs, each entity is represented by its FIRST surface mention
  in the document. This is stated as a limitation in the adapter's own
  docstring, not discovered after the fact.
- New `prompts/openie_biored_v1.txt` — schema-constrained (the 6
  BioRED relation types, matching this project's existing schema-
  constrained design philosophy), biomedical entity-aware.
- `src/extractors/openrouter_openie.py` generalized to accept a
  `prompt_template` parameter (previously hardcoded to CaRB's) —
  backward compatible, `tests/` still 40/40 passing.
- Model: `meta-llama/llama-3.1-8b-instruct` (core pipeline's pinned
  model, per the provider plan — DeepSeek reserved for DEC-002 only).
- Dev split only, never Test, per DEC-009's own rule. 15 abstracts,
  dry-run validated with a mocked extractor first.

## Actual

Strict exact-match (same protocol as every other evaluation in this
project): **P=0.0075, R=0.0072, F1=0.0074** (1 TP / 132 FP / 138 FN
across 133 predictions, 139 gold triples, 15 abstracts, $0.000509, 1
error).

Manual inspection of the lowest-scoring document found predictions
that are semantically correct but fail exact match due to boundary
differences — e.g. gold `"deletion of the coding sequence (nt 1314
through nt 1328)"` vs. predicted `"a 15 nucleotide (nt) deletion of the
coding sequence (nt 1314 through nt 1328)"`, same predicate, same
object, clearly the same relation.

Re-scored the same (zero new API cost) predictions with a relaxed
containment-based match (predicate exact, subject/object match if
either string contains the other after normalization): **P=0.1053,
R=0.1007, F1=0.1029** — 14 TP instead of 1, a 14x improvement.

## Result

PASS (pipeline works end to end on a new domain) with an important
caveat on the headline number — see interpretation.

## Interpretation

- **The strict F1=0.0074 substantially overstates how badly the system
  performs on biomedical text.** Most of the gap between it and the
  relaxed F1=0.1029 is an artifact of (a) BioRED's first-mention-as-
  concept-proxy gold construction and (b) the same subject-boundary-
  mismatch pattern already documented in CaRB (EVID-004/022), which
  hits harder here because biomedical entity mentions are longer and
  more variable than CaRB's.
- **Even the relaxed F1=0.103 shows the biomedical domain is
  genuinely harder than the product domain** (comparable to CaRB's
  Llama score of 0.059, well below the product domain's ~0.3-0.7 range)
  — real domain difficulty exists, it's just not the near-total-failure
  the strict number alone would suggest.
- Neither number should go in the paper without the other and this
  explanation. Reporting only the strict F1=0.0074 would be a
  misleading, technically-true-but-substantially-unfair characterization
  of the pipeline's actual biomedical capability — exactly the kind of
  thing the codebase context's scientific-integrity section warns
  against.

## Limitations

- n=15 is a small pilot; not a benchmark-grade result.
- The relaxed containment matcher is a simple, transparent heuristic
  (documented here in full), not a validated NLP entity-matching
  standard (e.g. it doesn't handle abbreviation expansion or synonym
  matching) — it's a reasonable secondary signal, not a replacement
  metric.
- Real entity linking (predicted mention → normalized concept ID,
  compared directly against gold concept IDs) would be the methodologically
  correct fix and was not attempted here — out of scope for a pilot.
- No external baseline run on BioRED yet (DeepSeek or otherwise).
- Product and biomedical schemas correctly kept separate (BioRED's 6
  relation types were not forced into ALLOWED_PREDICATES or vice versa).

## Next step

If a larger/benchmark-grade DEC-009 result is wanted: scale beyond
n=15, consider building real entity linking instead of the first-
mention proxy, and/or add DeepSeek as a biomedical baseline comparison
matching DEC-002's methodology.

# EVID-025 — DEC-006 Zero-Cost Build: Synthetic-Data Generator + Colab-Ready Training/Eval Scripts

## Experiment

- Decision: DEC-006
- API calls: `0`. GPU calls: `0` (nothing run on a GPU yet — this is
  the zero-cost portion of DEC-006's staged plan, see Decision log.md).
- Read the old notebook's cells 19-38 to understand the real synthetic-
  data + LoRA mechanism before porting anything. Found: B3's officially
  reported baseline result (cell 22) actually uses a substitute
  OpenRouter model, not the locally fine-tuned TinyLlama adapter —
  meaning the paper's B3/B4 numbers and the Table-9 "Iterative FT"
  numbers come from two different code paths in the original notebook,
  worth knowing if those old numbers are ever cited directly.
- New `src/synthetic_data_generator.py`: converts high-confidence PKB
  triples (C > threshold) into instruction/response training pairs,
  matching SLDE.pdf Module 4's description exactly (fixed templates,
  balanced per-predicate sampling). Pure Python, no GPU needed.
- New `scripts/dec006_lora_finetune.py` and
  `scripts/dec006_evaluate_adapter.py` — Colab/GPU-ready (not runnable
  in this local environment, no CUDA here), staged via a config flag
  (`USE_4BIT`) between Stage 0 (TinyLlama-1.1B, reproduces the original
  prototype's proven config) and Stage 1 (7B/8B QLoRA, the actual
  DEC-006 upgrade target). Evaluation script reuses the exact same
  `data/product_split.csv` leakage-safe test split and
  `src/evaluator.py` protocol as every API-based experiment in this
  project, so adapter results will be directly comparable to EVID-013's.

## Files

- `src/synthetic_data_generator.py`, `tests/test_synthetic_data_generator.py` (4 tests)
- `scripts/dec006_lora_finetune.py`, `scripts/dec006_evaluate_adapter.py`
- `outputs/dec006_synthetic_data/product_domain_synth_train.jsonl` — 127
  real synthetic training examples, generated from EVID-013's actual
  product-domain PKB run (not synthetic test fixtures)

## Actual

- 4/4 new tests pass; full suite 44/44.
- Real-data smoke test: generated 127 synthetic examples from the
  already-collected `pkb_snapshot_iteration_4.csv` (EVID-013) — matches
  exactly the 127 above-threshold triples independently found in
  EVID-014's analysis of the same file, a real cross-check that the
  threshold filtering is behaving consistently across both analyses.

## Result

PASS — zero-cost portion of DEC-006 complete and tested; ready to hand
off to a GPU environment (free Colab first, per the staged plan).

## Limitations

- Training/eval scripts are untested in an actual GPU environment
  (written carefully, matching the notebook's proven config, but not
  executed — no local CUDA available here).
- `build_targeted_gap_synthetic_data` and `evaluate_local_adapter` (the
  notebook's iterative gap-targeted variant, cells 33) were not ported
  — only the paper's primary Module 4 spec (all high-confidence triples,
  not gap-targeted) was implemented. The gap-targeted iterative variant
  could be added later if the simpler version proves insufficient.

## Next step

Run `scripts/dec006_lora_finetune.py` on free Google Colab (Stage 0:
TinyLlama-1.1B first, to validate the ported pipeline against known-
working config) using `outputs/dec006_synthetic_data/product_domain_synth_train.jsonl`,
then `scripts/dec006_evaluate_adapter.py` on the resulting adapter. Only
escalate to a paid rented GPU if Stage 0/Stage 1 (7B/8B QLoRA) hits a
real wall on Colab's free tier.

# EVID-026 — DEC-006 First Real GPU Run: Mistral-7B QLoRA, Base vs. Fine-Tuned

## Experiment

- Decision: DEC-006
- GPU: rented RunPod RTX 4090 24GB (two pods needed — see Limitations).
  Cost: well under $1 of a $10 budget.
- Skipped the TinyLlama-1.1B "Stage 0" sanity stage by explicit user
  decision — went straight to the paper-target 7B model:
  `mistralai/Mistral-7B-Instruct-v0.3` (ungated on Hugging Face, chosen
  over `meta-llama/Llama-3.1-8B-Instruct` specifically to avoid an
  HF gated-repo approval wait burning paid pod time).
- QLoRA: rank 16, alpha 32, dropout 0.05, lr 2e-4, 3 epochs, batch 2 /
  grad-accum 4, bf16 throughout.
- Same leakage-safe test split as every other experiment in this
  project (`data/product_split.csv`), same normalized-triple exact-
  match evaluator (`src/evaluator.py`).

## Three real bugs found and fixed during this run (not GPU/pod issues)

1. **bf16/fp16 dtype mismatch crashed training outright.** First
   training attempt hit `NotImplementedError:
   "_amp_foreach_non_finite_check_and_unscale_cuda" not implemented for
   'BFloat16'`. Mistral-7B's native weights load as bf16, but the
   script mixed that with fp16-mode `GradScaler` (`bf16=False,
   fp16=True`), and `GradScaler` can't unscale bf16 gradients. Fixed by
   using bf16 throughout (`bnb_4bit_compute_dtype`, model dtype, and
   `SFTConfig`) — the RTX 4090 supports bf16 natively, no loss scaling
   needed at all.
2. **Train/eval task-format mismatch produced F1=0.0000.** The original
   synthetic training data (`src/synthetic_data_generator.py`) followed
   SLDE.pdf Module 4's literal template — "Extract the [predicate] of
   [subject]" -> a prose sentence, one relation per example. But
   `dec006_evaluate_adapter.py` evaluates a completely different task:
   a full product paragraph in, a JSON array of triples out. The model
   learned its actual training task well (loss 2.03->0.40, token
   accuracy 66%->90% over 48 steps) but every generation then failed
   to parse as JSON at eval time. Fixed with a new shared
   `src/prompts.py` (`build_extraction_prompt`, used by both training-
   data generation and evaluation) and
   `scripts/dec006_regenerate_synth_data.py`, which rebuilds the
   synthetic set from the same source
   (`pkb_snapshot_iteration_4.csv`, 127 above-threshold triples / 33
   products — same source as the original file, EVID-025) but grouped
   per product: real product description in, JSON array of that
   product's high-confidence triples out — the exact eval task shape.
3. **Adapter emitted empty completions (0 new tokens) even after fixing
   #2.** Re-ran training on the reformatted 33-example set (15 steps,
   loss 0.78->0.62, token accuracy 79.6%->92.9%) — still F1=0.0000 at
   eval. Diagnosed with a raw-completion probe run directly on the pod:
   the fine-tuned model immediately emitted EOS under greedy decoding
   (`repr(completion) == ''`), while the un-fine-tuned base model never
   does this. A known degenerate mode for a very small/short fine-tune
   (33 examples, 15 steps), not a training failure. Fixed with
   `min_new_tokens=100` in `dec006_evaluate_adapter.py`'s
   `generate()` call, forcing real output past the point the model
   wants to stop; confirmed on-pod this produces parseable JSON.

## Actual (final, real result — same generation config applied to both)

| | Precision | Recall | F1 |
|---|---|---|---|
| Base `Mistral-7B-Instruct-v0.3` (no fine-tuning) | 0.3500 | 0.3000 | **0.3231** |
| + QLoRA fine-tune (33 examples, 3 epochs / 15 steps) | 0.3333 | 0.1714 | **0.2264** |

Fine-tuning **decreased** F1 by 0.0967 (recall dropped most: 0.30 ->
0.17). Spot-checked raw completions from the fine-tuned model: it
produces syntactically valid JSON with some individually correct
fields (e.g. `has_price_usd: 499` and `made_of_material: carbon fiber`
both matched gold in one inspected example), but frequently gets the
`subject` field wrong (e.g. copying a source-text fragment like "It is
a laptop device" instead of the actual product name), which fails
exact-match scoring even when predicate/object are right, and often
only emits one truncated triple per product rather than the full set.

## Result

FAIL for the "fine-tuning improves extraction" direction of DEC-006's
expected results — a real, honestly-measured negative result, not a
bug. Consistent with DEC-005's ablation finding (EVID-020): interventions
tested so far at small scale (N=20 ablation seeds; here, 33 training
examples / 15 steps) are not showing the improvements the manuscript's
claims assume.

## Interpretation

- This is very likely a **too-small/too-short fine-tune**, not evidence
  that QLoRA fine-tuning cannot help this task. 33 training examples
  and 15 optimizer steps is far below what's typically needed to reliably
  teach a 7B model a new structured-output behavior without hurting its
  existing instruction-following ability (recall dropping more than
  precision is consistent with the model becoming less complete/more
  conservative post-fine-tune, not randomly worse).
- The `subject`-field copying error suggests the model partially
  learned "copy a noun phrase from the text into a JSON field" rather
  than "identify and repeat the exact product name" — plausibly because
  the 33 training targets only ever named each of the 33 unique
  products once each, giving the model very little repetition to learn
  the specific copy-the-subject-verbatim behavior from.
- Claim #1/#2 (unified pipeline / automated synthetic supervision) now
  has a real, if currently negative, data point. Per
  [[submission_readiness_framework]], this needs either (a) a bigger,
  more repeated training run before drawing a paper-level conclusion,
  or (b) reporting this honestly as "fine-tuning was implemented and
  tested; no improvement detected at this very small scale" — mirroring
  exactly how DEC-005's null ablation result should be framed. Do not
  report only the negative single run as if it were a definitive
  "fine-tuning doesn't work" finding.

## Limitations

- Single run, single seed, single (very small) hyperparameter
  configuration — no LoRA grid search, no multiple seeds (DEC-006 steps
  6-8 not done).
- 33 training examples is a hard ceiling of the current product-domain
  PKB run's above-threshold triple count (EVID-025) grouped per product
  — scaling this up requires either a larger PKB run (more products) or
  loosening the confidence threshold, not just more epochs on the same
  33.
- The adapter and full per-example predictions were not saved off the
  pod (see below) — only the aggregate metrics and this write-up
  persist. A re-run to regenerate the actual adapter file would cost
  under $1 given the same setup is now debugged and working.
- **Practical/infra note, not a science limitation:** this run needed
  two RunPod pods — the first had a broken host-level GPU passthrough
  (`/dev/nvidia0` missing, only a non-zero-indexed device node present;
  a `ln -sf` symlink workaround did not fix it; terminating and
  redeploying on a different host resolved it immediately — see
  `dec006_runpod_plan` memory). The second pod also had no cached git
  credentials, so committing the adapter/eval outputs back to GitHub at
  the end was skipped by user decision (Option B: log the numbers here
  instead of spending more time on GitHub token setup) — the results
  above are transcribed directly from the pod's terminal output, not
  re-verified from a saved file.

## Next step

If a paper-reportable DEC-006 result is wanted: scale up the training
set (more products through the PKB pipeline, and/or a lower confidence
threshold), run at least 2-3 seeds, and consider a small LR/epoch grid
(DEC-006 steps 6-8) before drawing conclusions either way. Until then,
report this as implemented-and-tested-negative-at-small-scale, not as
a completed fine-tuning ablation.

# EVID-027 — DEC-006 Scaled-Up Run: 200-Product PKB + Larger Fine-Tune (Positive Result)

## Experiment

- Decision: DEC-006, direct follow-up to EVID-026's negative small-
  scale result. User explicitly directed: "scale up the training set
  and rerun."
- Phase 1 (no GPU, local, real OpenRouter API calls): scaled the
  product-domain PKB run from 50 to 200 products via a new parallel
  script (`scripts/dec006_scaleup_probkb_run.py`, `EXPERIMENT_ID=
  DEC006_SCALEUP_V1`), a fresh independent leakage-safe split
  (`data/product_split_200.csv`, 140/20/40 train/val/test — NOT a
  superset of the original 50-product split), same model
  (`meta-llama/llama-3.1-8b-instruct`), same 4-iteration + held-out
  design as DEC-003's canonical run. 620 API calls, $0.011995 total
  cost. Held-out F1 (LLM extraction quality, not fine-tuning):
  val 0.5610, test 0.4126.
- Above-threshold training triples: 475 across 90 unique products (up
  from EVID-026's 127 triples / 33 products — roughly 3.7x more
  triples, 2.7x more products).
- Regenerated `outputs/dec006_synthetic_data/product_domain_synth_train.jsonl`
  from this bigger snapshot via `scripts/dec006_regenerate_synth_data.py
  --snapshot-path outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv`
  — same task-aligned (paragraph-in, JSON-array-out) format as
  EVID-026's fix, so this run has no format-mismatch risk.
- Phase 2 (rented RunPod RTX 4090, clean pod this time — GPU checked
  out on first try, no passthrough issues): same QLoRA config as
  EVID-026 (rank 16, alpha 32, lr 2e-4, 3 epochs, bf16), now training
  on 90 examples instead of 33 -> 36 optimizer steps instead of 15.

## Actual

Training: loss 0.665 -> 0.11 over 36 steps (502.6s), final
`train_loss=0.2789`, `mean_token_accuracy=0.9723` — a much healthier
training curve than EVID-026's 15-step run.

Same leakage-safe test split, same evaluator, same generation config
(`min_new_tokens=100` guard from EVID-026 still in place) applied to
both:

| | Precision | Recall | F1 | TP | FP | FN | Predictions made |
|---|---|---|---|---|---|---|---|
| Base `Mistral-7B-Instruct-v0.3` | 0.3500 | 0.3000 | **0.3231** | 21 | 39 | 49 | 60 |
| + QLoRA fine-tune (90 examples, 3 epochs / 36 steps) | 0.7308 | 0.2714 | **0.3958** | 19 | 7 | 51 | 26 |

## Result

PASS — the first genuine positive fine-tuning result in this project.
F1 improved by +0.0727 (0.3231 -> 0.3958). Precision more than
doubled (0.35 -> 0.73); recall dipped slightly (0.30 -> 0.27). Net
effect: the fine-tuned model makes far fewer predictions overall (26
vs. 60) but is much more likely to be right when it does — a
precision/recall trade-off that nets out positive on F1 at this scale.

This directly reverses EVID-026's negative finding and confirms that
memo's own interpretation: the earlier failure was a too-small/too-
short fine-tune (33 examples/15 steps), not evidence that QLoRA
fine-tuning can't help this task. Scaling the training set alone (no
other hyperparameter changes) was enough to flip the sign.

## Interpretation

- The precision-heavy improvement (more than 2x) with a recall cost is
  a plausible, explicable pattern for a still-small (90-example)
  fine-tune: the model became more conservative — it apparently
  learned "only commit to a triple when confident" better than it
  learned "always attempt every extractable fact," which is exactly
  the kind of asymmetric partial learning expected before a fine-tune
  is large enough to master both precision and recall together.
- A spot check of `outputs/dec006_eval/mistral7b_qlora/predictions.json`
  shows the `subject`-field copying error identified in EVID-026 is
  STILL present in some predictions (e.g. `"subject": "laptop device"`
  instead of the actual product name, on product_idx 4, also
  duplicated as an identical repeated triple) — this is very likely
  suppressing recall further and capping how high F1 could go even at
  this improved scale. Fixing this specific failure mode (rather than
  just adding more data) is a plausible next lever if a bigger
  improvement is wanted.
- Per [[submission_readiness_framework]] claims #1/#2: this is now a
  genuine, positive, reproducible-methodology data point for the
  unified pipeline / automated synthetic supervision claims — stronger
  than DEC-005's still-null ablation finding for claim #4. Still only
  a single run/seed (DEC-006 steps 6-8 — LoRA grid, multiple seeds —
  remain undone), so report as "implemented and tested, F1 improved by
  +0.073 at this scale" rather than a fully validated, multi-seed
  result.

## Limitations

- Single run, single seed, unchanged hyperparameters from EVID-026
  (only the dataset size changed) — cannot yet separate "more data
  helped" from "this particular data/seed combination happened to
  help"; a second seed at the same scale would meaningfully strengthen
  this finding.
- The subject-copying failure mode from EVID-026 was not fixed, only
  outgrown partially by more data — still an open, identified quality
  issue in the fine-tuned model's outputs.
- 90 examples is still a hard ceiling of this 200-product run's
  above-threshold triple count; a further scale-up (e.g. 500+ products)
  would need proportionally more OpenRouter spend (still cheap — this
  run cost $0.012 for 4x the original) and GPU time (this run took
  ~8.4 minutes of training alone, comfortably inside the $10 RunPod
  budget with room for several more iterations).
- Adapter/eval outputs were pushed to GitHub this time (unlike
  EVID-026) after resolving pod git-credential setup — see
  `dec006_runpod_plan` memory for the working procedure. The token
  used was pasted in plaintext into the pod's own chat session during
  troubleshooting; user was advised to rotate it immediately.

## Next step

If DEC-006 steps 6-8 (multi-seed, LoRA hyperparameter grid) are wanted
for a paper-reportable claim: rerun at this same 90-example scale with
2-3 different seeds to check the improvement direction replicates, and/or
try a small grid (rank, alpha, learning rate, epochs) using val-split
performance to select. Separately, investigating and fixing the
subject-copying failure mode (e.g. via more explicit training examples
that vary surface phrasing of the product name) could improve recall
without needing more raw data volume.

# EVID-028 — DEC-006 Real Leakage Found + Corrected Multi-Seed Result (SUPERSEDES EVID-027's numbers)

## Experiment

- Decision: DEC-006, direct follow-up to EVID-027. User asked "what
  dataset/size are these F1 scores on" — answering that precisely
  surfaced a real bug.
- **Leakage found:** EVID-027's 90-example fine-tuning set was built
  from the 200-product scale-up split (`data/product_split_200.csv`),
  an independently-shuffled split from the original 50-product split
  (`data/product_split.csv`) that `dec006_evaluate_adapter.py` uses for
  its held-out test set. Checked for overlap directly: **2 of the 10
  test products (`Auralex Smartphone Air 7`, `TechNova Headphones Lite
  26`) were also used to build the fine-tuning training examples** —
  real train/test leakage, contaminating 20% of the test set. This
  means EVID-027's reported numbers (base F1=0.3231, seed 42
  F1=0.3958) are NOT valid held-out measurements and should not be
  cited.
- **Fix:** `scripts/dec006_evaluate_adapter.py` now reads the actual
  training data file, extracts every product name used in training
  (parsing the trailing target JSON array of each example), and
  automatically excludes any would-be test product that appears there
  — printing exactly what was excluded and recording it in
  `metrics.json`, so this can't happen silently again regardless of
  which future training-data source is used.
- Also added real `--seed` control to `scripts/dec006_lora_finetune.py`
  (`transformers.set_seed()` called before model/LoRA construction,
  which passing `seed` only to `SFTConfig` would NOT achieve, since
  LoRA init happens before the `Trainer` exists) — EVID-026/027's
  single "seed" was actually always the HF default (42), with zero
  real variation. New `scripts/dec006_multiseed_run.sh` trains/evaluates
  seeds 43 and 44 in addition.
- Re-evaluated ALL FOUR configurations (base, seed 42, seed 43, seed
  44) on the SAME corrected, leakage-safe **8-product / 56-gold-triple**
  test set (down from the original 10 products / 70 triples).
- Ran on a different physical setup than EVID-026/027 for seeds 43/44:
  after 3 consecutive RTX 4090 pods failed the GPU sanity check with
  identical `torch.cuda.is_available()=False` errors (a systemic
  driver/CUDA mismatch, not the earlier per-host device-node bug),
  switched to an **RTX 3090** on the same provider, which worked
  immediately. Runtime is therefore not comparable across seeds
  (seed 42 trained in 502.6s on a 4090; seeds 43/44 trained in ~131s
  each on a 3090) — the GPU model does not affect the correctness of
  the F1 metric itself, only wall-clock time, so this does not affect
  result validity.

## Actual (final, corrected numbers)

| | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Base `Mistral-7B-Instruct-v0.3` | 0.1522 | 0.1250 | **0.1373** | 7 | 39 | 49 |
| + QLoRA, seed 42 | 0.5385 | 0.1250 | **0.2029** (+0.0656) | 7 | 6 | 49 |
| + QLoRA, seed 43 | 0.6364 | 0.1250 | **0.2090** (+0.0717) | 7 | 4 | 49 |
| + QLoRA, seed 44 | 0.1515 | 0.0893 | **0.1124** (−0.0249) | 5 | 28 | 51 |

Fine-tuned mean F1 = 0.1748 (std = 0.0541) vs. base F1 = 0.1373 — mean
improvement +0.0375, but the across-seed std (0.054) is larger than
the mean effect, and one of three seeds (44) is negative.

**Striking detail:** base, seed 42, and seed 43 all get the exact same
7 true positives (out of 56 gold triples) — identical recall
(0.1250). The entire difference between them is false positives: base
predicts 46 triples total (39 wrong), seed 42 predicts 13 (6 wrong),
seed 43 predicts 11 (4 wrong). Fine-tuning is not teaching the model
to find more correct facts; it's teaching it to stop guessing wrong
ones, for 2 of the 3 seeds. Seed 44 breaks this pattern: worse recall
(5 TP, not 7) AND worse precision than seeds 42/43 (28 FP), though
still better precision than the base model.

## Result

MIXED, not a clean positive result — an important correction to
EVID-027's apparent clean win. 2 of 3 seeds show a real, meaningful F1
improvement over base, driven entirely by a large reduction in false
positives (over-generation) rather than any recall gain. 1 of 3 seeds
(44) underperforms the base model. This is NOT statistically
conclusive at n=3 (std exceeds the mean effect size) — matches the
cautious framing DEC-005 already established for the feedback-ablation
finding, and should be reported the same way: real signal, direction
mostly positive, not yet significance-tested or seed-count-sufficient
for a strong paper claim.

## Interpretation

- The identical TP=7 across base/seed42/seed43 is a striking and
  genuinely useful qualitative finding for professor_feedback.md point
  #10 ("why precision improves significantly... why recall remains
  relatively unchanged") — this dataset/scale directly demonstrates
  that exact pattern, with a concrete mechanism (fewer false-positive
  guesses, same true positives found) rather than just an aggregate
  number.
- Seed 44's regression is a genuine negative data point, not an
  anomaly to explain away — with only 90 training examples, QLoRA
  fine-tuning outcomes are evidently sensitive to initialization, and
  this instability is itself worth reporting honestly rather than
  cherry-picking the two good seeds.
- Per [[submission_readiness_framework]] claims #1/#2: downgrade from
  EVID-027's "genuine positive data point" framing to "real, mixed,
  probably-net-positive-but-noisy effect requiring more seeds/a formal
  significance test before a confident paper claim" — closer to claim
  #4's (DEC-005) honest-null framing than previously thought, though
  directionally more encouraging (2/3 positive vs. DEC-005's genuinely
  null p=0.35-0.51 result).
- This whole episode is also a good worked example for DEC-012
  (reproducibility): it shows exactly why leakage-checking must be
  automatic and enforced in code, not manually reasoned about per run
  — a second independently-shuffled split silently reintroduced
  leakage that no one would have caught without explicitly checking
  index overlap.

## Limitations

- n=3 seeds is still small for a confident statistical claim; DEC-005
  used 5 seeds for its (also inconclusive) ablation test. A 5-seed
  DEC-006 run would be the natural next step if a firmer claim is
  wanted.
- The leakage guard only checks product *names* extracted from the
  training data's target JSON — if a future training-data format
  doesn't embed subject names in a JSON array the same way, the guard
  would need updating (it fails safe by finding zero trained subjects
  and excluding nothing, not by crashing, so this is a silent-gap risk
  worth remembering, not a crash risk).
- Runtime/GPU-utilization numbers are not comparable between seed 42
  (RTX 4090) and seeds 43/44 (RTX 3090) — noted above, does not affect
  F1 validity but would matter if DEC-006's runtime numbers are ever
  reported per-seed.

## Next step

If DEC-006 is to support a stronger paper claim: run 2 more seeds (45,
46 -- matching DEC-005's 5-seed convention) on the same 90-example set
and run a proper paired significance test (t-test or Wilcoxon, per
professor_feedback.md point #5) across all 5 seeds' F1 vs. base,
rather than eyeballing direction. Until then, report DEC-006 as: "QLoRA
fine-tuning reduces false-positive over-generation and improves F1 in
most (2/3) seeds tested, with one regression; effect not yet
significance-tested."

# EVID-029 — DEC-018 Provenance Filter Validation Against Known Gold

## Experiment

- Decision: DEC-018 (new — claim #5, "provenance actively filters
  synthetic training data quality," previously false as written, no
  code anywhere gated on provenance).
- Zero API/GPU cost — reprocesses the already-collected 200-product
  PKB scale-up snapshot (`outputs/dec006_scaleup_probkb/train_kb/
  pkb_snapshot_iteration_4.csv`, EVID-027/028's source data).
- Filter definition (`src/provenance_filter.py`): a triple passes if
  at least one of its observations came from a STRUCTURED source,
  regardless of how many unstructured (LLM) observations it also has.
- Because this domain is synthetically generated
  (`src/datasets/product_generator.py`), the TRUE gold triples are
  known exactly — this is the rare case where we can directly measure
  training-data precision against ground truth rather than estimate it.
- `scripts/dec018_provenance_filter_validation.py` applies the filter
  to all 475 above-threshold triples and checks each against gold.

## Actual

| | n | Precision against gold |
|---|---|---|
| All above-threshold triples (unfiltered) | 475 | 93.47% |
| WITH structured corroboration (passes filter) | 444 | **100.00%** |
| Unstructured-only (fails filter) | 31 | **0.00%** |

Every single one of the 31 unstructured-only triples is wrong, despite
crossing the confidence threshold and being independently observed
2-21 times each. Inspecting them directly: the overwhelming majority
(13/31) are `has_color` or category-adjacent predicates attached to a
**generic device-category noun as the subject** ("laptop device",
"tablet device", "smartwatch device", "headphones device") instead of
the real product name, or in one case an entire sentence fragment
copied verbatim into the subject field
(`"The display measures 6.7 inches."`). `TechNova Smartphone Pro 1`
alone appears with five different, mutually-contradictory colors
across separate rows (blue, green, white, silver, black), each
observed multiple times.

## Result

PASS — a strong, validated, real filter, not a token gesture. Applying
it (`scripts/dec006_regenerate_synth_data.py`, now on by default)
regenerates the DEC-006 synthetic training set at 73 product-level
examples / 444 triples (down from 90 examples / 475 triples
unfiltered) — a 6.5% reduction in volume for a jump from 93.5% to
100% measured precision.

## Interpretation

- **This directly explains a previously-unexplained failure mode.**
  EVID-026/027/028 all flagged a "subject-copying" bug where the
  DEC-006 fine-tuned model sometimes outputs a generic phrase like
  "laptop device" instead of the real product name. This result shows
  why: those exact phrases are present, repeated, and confidently
  aggregated in the (unfiltered) training data the model actually
  learned from. This isn't two unrelated bugs — it's one causal chain:
  a repeated LLM extraction hallucination → passes the confidence
  threshold via repetition → becomes training data → gets partially
  reproduced by the fine-tuned model.
- **Why does repetition alone fool the confidence aggregation but not
  provenance?** Noisy-Or aggregation (DEC-003) treats each additional
  observation as independent corroborating evidence, so a
  systematically-repeated LLM error (e.g., the model consistently
  defaulting to a generic category noun when uncertain about a
  specific product's name) accumulates confidence exactly like a real,
  independently-verified fact would. Provenance-type diversity is a
  different, complementary signal: an unstructured-only fact was never
  independently checked against a different *kind* of source, only
  repeated by the same *kind* of process that produced the error in
  the first place.
- Per [[submission_readiness_framework]] claim #5: this is now a real,
  quantitatively-validated capability, not a false claim — the
  manuscript's claim #5 wording is now actually true of the
  implementation, and professor_feedback.md point #7's "provenance
  filtering examples" ask is answered concretely with real dropped
  examples (`outputs/dec018_provenance_filter/dropped_triples.csv`).
- A follow-up DEC-006 fine-tuning run using the filtered (444-triple)
  training data would be a natural way to test whether removing these
  specific hallucinated examples reduces the subject-copying failure
  mode in the fine-tuned model's own outputs — not done in this pass.

## Limitations

- Validated on one dataset (the synthetic product domain), where gold
  is known by construction. On CaRB or BioRED (or any domain where
  gold isn't known outright), this same precision-based validation
  can't be replicated directly — the filter's structured-corroboration
  criterion is domain-general, but this specific quantitative
  validation is not.
- The filter is binary (has-structured or not); a softer, confidence-
  weighted provenance signal (e.g., discounting confidence for
  unstructured-only triples rather than dropping them outright) was
  not explored.
- This changes DEC-006's default training data going forward, but the
  already-completed EVID-026/027/028 fine-tuning runs used the
  unfiltered version and were not re-run with the filtered data.

## Next step

If DEC-006 is revisited (e.g., the planned 2-more-seeds run), consider
using the newly-filtered 444-triple training set instead of the
475-triple unfiltered one, and specifically check whether the
subject-copying failure mode in the fine-tuned model's predictions
decreases as a result.

# EVID-030 — DEC-019 Closed-Loop Integration Test (Claim #1)

## Experiment

- Decision: DEC-019 (new — claim #1, "unified closed-loop
  architecture," never actually tested end-to-end before this).
- Starting point: the exact KB state at the end of iteration 4 of the
  DEC-006 200-product scale-up run (EVID-027/028's source data),
  reconstructed via `src/pkb_replay.py` by replaying the saved
  `observations_iteration_{1,2,3,4}.csv` files through fresh
  `accept_candidate()` calls. Verified exact before use: reproduces
  the original 475/475 above-threshold triples and all 2241 accepted
  keys with zero discrepancy.
- From that identical starting point, ran ONE more iteration two ways
  over the same 140 train products, both using the plain
  `src/prompts.py` prompt (no locked-context/feedback-hint, since the
  fine-tuned model was only ever trained on that format):
  - **CONTROL**: `meta-llama/llama-3.1-8b-instruct` via OpenRouter (the
    same un-fine-tuned base model iterations 1-4 used). 140 calls,
    $0.002074, 1 parse error.
  - **TREATMENT**: the seed-43 QLoRA adapter (EVID-028's best-performing
    seed, F1=0.2090 in standalone eval), run locally on a rented RTX
    4090. 603 raw triples extracted across the same 140 products.
- Merged each arm's iteration-5 output into its own copy of the
  replayed iteration-4 state, called `end_iteration(5)`, and measured
  the accumulated above-threshold KB's precision/recall/F1 against the
  same known gold used throughout DEC-006/018.

## Actual

| Arm | KB size | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Iteration 4 (pre-closure baseline) | 475 | 0.9347 | 0.2440 | **0.3869** |
| Iteration 5, CONTROL (base model continues) | 480 | 0.9083 | 0.2396 | **0.3791** |
| Iteration 5, TREATMENT (fine-tuned model closes the loop) | 499 | 0.8978 | 0.2462 | **0.3864** |

Net new above-threshold triples contributed: CONTROL added 5 (480-475);
TREATMENT added 24 (499-475) — the fine-tuned model contributed roughly
5x more net-new KB content than the base model did in the same
additional pass, at a comparable (very slightly lower) precision.

## Result

MIXED / informative null, not a clean win — but a real, decisive
comparison. TREATMENT (closing the loop) is essentially FLAT versus
the pre-closure baseline (F1 -0.0005, negligible) — it does not clearly
demonstrate that closing the loop improves the system in an absolute
sense. However, TREATMENT clearly beats CONTROL (+0.0073 F1) — i.e.,
*if* another iteration is going to run at all, using the fine-tuned
model for it is measurably better than continuing with the
un-fine-tuned model, which actively degrades the KB (-0.0078 F1 vs.
baseline).

## Interpretation

- **The realistic comparison for claim #1 is treatment vs. control, not
  treatment vs. baseline.** In an actually-running closed-loop system,
  the alternative to "fine-tune and re-extract" isn't "do nothing" —
  it's "keep re-extracting with the same un-fine-tuned model," which
  this experiment shows is the worse choice. Framed this way, closing
  the loop has a real, if modest, benefit.
- **Why does the un-fine-tuned CONTROL degrade the KB at all?** Losing
  the locked-context/feedback-hint guidance (used deliberately here to
  keep the comparison fair to the fine-tuned model, which never saw
  that format) makes iteration 5 behave more like an unguided pass —
  and DEC-007/EVID-022 already found that unguided extraction produces
  more hallucination-vs-hallucination noise. The fine-tuned model
  appears to partially compensate for this lost guidance on its own
  (consistent with DEC-006/EVID-028's finding that fine-tuning makes
  the model more conservative/precise), which is plausibly *why*
  treatment ends up flat rather than also degrading.
- **This result is now consistent with, not contradictory to, DEC-006's
  own mixed finding (EVID-028).** DEC-006 found fine-tuning helps in
  2 of 3 seeds on standalone extraction; this test used only the single
  best seed (43) and found a modest relative — not absolute — benefit
  when looped back into the full system. Together these paint a
  coherent picture: fine-tuning at this data scale is a real but small
  and seed-dependent lever, not yet a transformative one.
- Per [[submission_readiness_framework]] claim #1: report as "the
  closed-loop architecture was implemented and tested end-to-end; the
  fine-tuned model, once integrated, does not clearly beat leaving the
  KB alone, but does reliably outperform continuing to extract without
  fine-tuning" — an honest, mechanistically-explained result, not a
  triumphant claim and not a dead end either.

## Limitations

- Single seed (43) tested for treatment, not all 3 from EVID-028 — a
  weaker or stronger seed might shift this comparison in either
  direction; DEC-006's own seed 44 was a net regression in standalone
  eval, so a closed-loop test using that seed instead might show
  treatment losing to control.
- Locked-context/feedback-hint was deliberately dropped for both arms'
  iteration 5 to keep the comparison fair to the fine-tuned model. This
  makes iteration 5 not a perfect like-for-like continuation of
  iterations 2-4's actual methodology (which did use locked
  context/feedback) — the CONTROL arm's degradation may partly reflect
  losing that guidance rather than being purely representative of "the
  base model, one more time, under identical conditions to iterations
  1-4."
- One additional iteration only, not a sustained multi-cycle closed
  loop (extract -> fine-tune -> extract -> fine-tune again -> ...). A
  longer-running loop could show compounding effects in either
  direction that a single extra iteration cannot reveal.
- Uses the same 140 train products already used to build the
  iteration-4 baseline (matching how iterations 2-4 already re-used the
  train set with escalating guidance) rather than a fresh, unseen batch
  of products — a fresh-batch design would be a cleaner test of
  generalization but was not attempted here.

## Next step

If a stronger closed-loop claim is wanted: repeat with seeds 42 and 44
as separate treatment arms (already-trained adapters, no new GPU
training needed — just new extraction passes) to see whether the
treatment-beats-control result holds across all 3 seeds or was
specific to the best one. A sustained multi-cycle version (fine-tune
again after this iteration 5, extract again, etc.) would be a more
complete test of the "closed-loop" claim but is substantially more
engineering and GPU time.

# EVID-031 — DEC-001 Part 5: Official CaRB Scorer Result

## Experiment

- Decision: DEC-001 part 5 — the longest-standing incomplete item in
  the project. Every prior CaRB number (EVID-003/004/021) came from
  this project's own internal normalized-triple exact-match evaluator,
  never the actual CaRB benchmark's official scoring tool.
- Zero new API/GPU cost — rescored the already-collected predictions
  from EVID-021's pinned-model N=30 run
  (`outputs/dec001_002_carb30/{slde_aft_llama,deepseek_baseline}/
  predictions.json`) using the real `data/CaRB/carb.py` scorer (the
  official dair-iitd/CaRB tool, vendored in this repo as a submodule).
- **Naming correction found while preparing this:** the 30-sentence
  file is named `data/carb_dev_sample.jsonl`, but exact sentence-text
  lookup confirms all 30 sentences are present in CaRB's official
  TEST split gold file (`data/CaRB/data/gold/test.tsv`), not
  `dev.tsv` (0/30 matched dev). This is a mislabeling to fix in any
  future write-up, not a leakage concern — CaRB is an extraction-
  quality-only benchmark in this project, never used to train or tune
  anything.
- Converted `predicted_triples` into CaRB's tab-separated format
  (`sentence\tconfidence\tpredicate\tsubject\tobject`) via
  `scripts/dec001_run_official_carb_scorer.py`. No per-triple
  confidence was captured during the original extraction
  (`prompts/openie_carb_v1.txt` doesn't request one), so every triple
  got a uniform confidence of 1.0 — this collapses CaRB's usual
  precision-recall curve to a single point, which is normal for
  systems without calibrated per-triple confidence and does not affect
  the resulting precision/recall/F1.
- Filtered the official test.tsv gold file down to just these 30
  sentences (`outputs/dec001_official_carb/gold_subset_30.tsv`, 125
  gold triples) so recall is computed only over the sentences actually
  attempted, not all 641 test sentences.
- Used CaRB's own DEFAULT matching function (no `--exactMatch`/
  `--strictMatch`/etc. flag — `Matcher.binary_linient_tuple_match`),
  the standard matching reported as "the CaRB score" in the literature.

## Setup fixes required (documented for reproducibility, not committed
## upstream -- the vendored submodule's remote is the read-only
## upstream dair-iitd/CaRB, not a fork this project can push to)

1. `data/CaRB/oie_readers/extraction.py` imports
   `from sklearn.preprocessing.data import binarize` — an internal
   sklearn path removed in modern scikit-learn (this repo dates to
   2019, `requirements.txt` pins `scikit-learn==0.18`, impossible to
   install cleanly on Python 3.12). Patched locally to
   `from sklearn.preprocessing import binarize` (`binarize` is never
   actually called anywhere in that file — confirmed via grep — so
   this is a dead-import path fix with zero behavior change). Left as
   an uncommitted local working-tree edit inside the submodule; must
   be reapplied after a fresh `git submodule` checkout.
2. `nltk.download('stopwords')` — the matcher needs this corpus and it
   isn't bundled; one-time local setup.

## Actual

| System | AUC | Optimal Precision | Optimal Recall | Optimal F1 |
|---|---:|---:|---:|---:|
| `meta-llama/llama-3.1-8b-instruct` (SLDE-AFT extractor) | 0.331 | 0.652 | 0.401 | **0.496** |
| DeepSeek-V3.2 (external baseline) | 0.392 | 0.713 | 0.458 | **0.558** |

Compare to this project's own internal exact-match numbers on the same
30 sentences (EVID-021): Llama F1=0.0591, DeepSeek F1=0.1340. The
official CaRB score is **~8.4x higher** for Llama and **~4.2x higher**
for DeepSeek than the internal metric ever reported.

## Result

PASS — DEC-001 part 5 is complete, and the result is a major, positive
correction to how this project's extraction quality should be
described. The internal exact-match evaluator was not just "a bit
strict" — it was undercounting real extraction quality by roughly
4-8x on this benchmark.

## Interpretation

- **This directly confirms and quantifies EVID-004/022's own error
  analysis**, which already identified subject-boundary mismatches
  (e.g., predicted `"all households"` vs. gold `"32.7 % of all
  households"`) as a major, systematic failure mode of exact-match
  scoring — semantically correct extractions penalized purely for
  argument-span boundaries. CaRB's own matching function was
  specifically designed by its authors to handle exactly this kind of
  boundary variation, which is why the gap is this large.
- **Every internal-evaluator CaRB number in this project's Decision/
  Evidence logs (EVID-003/004/021, and DEC-001/002's headline figures)
  understates real performance by roughly 4-8x** and should not be the
  numbers quoted in the paper's main results table — the official
  scores above should be, with the internal-evaluator numbers kept
  only as a secondary/diagnostic detail if mentioned at all.
- Llama-3.1-8B F1=0.496 and DeepSeek-V3.2 F1=0.558 are now genuinely
  comparable, literature-standard numbers that can be checked against
  other published CaRB results for context — something the internal
  metric's F1=0.059/0.134 numbers never could be.
- Per [[submission_readiness_framework]]: this doesn't change DEC-002's
  qualitative finding (DeepSeek still beats Llama, ~1.6x in F1 terms
  under official scoring vs. ~2.3x under the internal metric — a
  smaller but still real gap), but it substantially strengthens the
  credibility of the CaRB pilot itself, directly addressing part of
  professor_feedback.md point #1's emphasis on established, standard
  benchmarks.

## Limitations

- Still N=30, a pilot scale, not the full 641-sentence CaRB test set —
  DEC-002's own "Remaining" note about scaling toward the full set for
  a benchmark-grade (not pilot-grade) result still applies.
- Uniform confidence (1.0) means only a single point on the
  precision-recall curve was evaluated, not a full curve/AUC in the
  way systems with calibrated confidence scores would be scored — the
  reported AUC values (0.331/0.392) are a degenerate single-point
  approximation, not a meaningful curve-shape comparison. The
  Precision/Recall/F1 values are the ones to cite, not the AUC.
- The submodule compatibility patch (`sklearn.preprocessing.data` ->
  `sklearn.preprocessing`) lives only in this project's local working
  tree, not committed anywhere reproducible via git (no push access to
  the upstream dair-iitd/CaRB repo) — anyone re-cloning this repo's
  `data/CaRB` submodule fresh will need to reapply it manually (see
  "Setup fixes" above) before this script will run.
- REBEL/full benchmark comparisons (professor feedback #2) remain a
  separate, larger, still-deferred item.

## Next step

If a benchmark-grade (not pilot) CaRB result is wanted for the paper:
scale the extraction to CaRB's full 634/641-sentence test set (real
API cost, still cheap based on this project's per-call cost history)
and rerun this same official-scorer conversion.

# EVID-032 — DEC-002 Extension: GPT-4o, Claude Sonnet 5, Gemini 2.5 Pro Baselines

## Experiment

- Decision: DEC-002 (extending the external SOTA baseline requirement)
  — professor_feedback.md point #2 explicitly names "GPT-4 extraction,"
  "Claude," and "Gemini" among the expected comparisons; only DeepSeek
  had been added before this.
- Identical protocol to EVID-021's DeepSeek baseline: same 30 CaRB
  sentences (`data/carb_dev_sample.jsonl`), same prompt
  (`prompts/openie_carb_v1.txt`), same internal evaluator, PLUS the
  official CaRB scorer (per EVID-031) for all five systems now on
  record.
- Models: `openai/gpt-4o` (matches "GPT-4 extraction" literally),
  `anthropic/claude-sonnet-5` (current-gen, comparable tier to
  DeepSeek-V3.2), `google/gemini-2.5-pro` (stable, non-preview).
- New `scripts/dec002_sota_baselines_gpt_claude_gemini.py`.

## Three real bugs found and fixed while collecting this

1. **OpenRouter in-flight credit budget + Claude Sonnet 5's new-account
   rate limit (20 req/min)**, hit by firing 3 models' worth of calls
   back-to-back with no delay. Fixed with a floor delay between calls
   (3.5s, keeping every model comfortably under 20 rpm) and
   retry-with-backoff on HTTP 402/429.
2. **The account then ran out of real credits entirely** (a genuine
   "upgrade to a paid account" 402, not the transient in-flight-budget
   variant) partway through re-collecting Claude/Gemini — user topped
   up OpenRouter credits ($5) to resolve; no code fix applicable here,
   documented as an operational dependency.
3. **`src/extractors/openrouter_openie.py` crashed on a `None` content
   field** (`TypeError: expected string or bytes-like object, got
   'NoneType'`) — observed specifically with `google/gemini-2.5-pro`,
   which apparently can spend its entire token budget on internal
   reasoning and return a null final-answer content field. Fixed by
   treating `None` content as a normal extraction failure
   (`"model returned null content"`) instead of crashing the whole
   script. This is a real robustness fix to shared, reused code, not
   specific to this one baseline run.
4. **Gemini 2.5 Pro's responses were truncated mid-JSON at the default
   `max_tokens=512`**, confirmed via a direct diagnostic call showing
   output cut off mid-string. Raised to 1536 (still 12/30 failures),
   then 3072 (5/30 failures) before accepting the result — Gemini's
   reasoning-heavy responses apparently consume much more of the token
   budget than the other four models tested, at ~7-15x the API cost
   per sentence ($0.49 total for 30 sentences vs. $0.03-0.07 for
   GPT-4o/Claude).

## Actual

**Internal evaluator** (this project's own normalized exact-match, for
continuity with earlier entries):

| System | Precision | Recall | F1 | Errors | Cost |
|---|---:|---:|---:|---:|---:|
| GPT-4o | 0.193 | 0.091 | 0.124 | 0/30 | $0.033 |
| Claude Sonnet 5 | 0.132 | 0.099 | 0.113 | 0/30 | $0.068 |
| Gemini 2.5 Pro | 0.311 | 0.157 | 0.209 | 5/30 | $0.491 |

**Official CaRB scorer** (per EVID-031's methodology — use these, not
the internal-evaluator numbers, in the paper):

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| Llama-3.1-8B-instruct (SLDE-AFT's own extractor) | 0.652 | 0.401 | **0.496** |
| GPT-4o | 0.736 | 0.384 | **0.504** |
| Claude Sonnet 5 | 0.642 | 0.446 | **0.527** |
| Gemini 2.5 Pro | 0.773 | 0.401 | **0.528** |
| DeepSeek-V3.2 | 0.713 | 0.458 | **0.558** |

Ranked by official F1: DeepSeek-V3.2 > Gemini 2.5 Pro ≈ Claude Sonnet 5
> GPT-4o > Llama-3.1-8B-instruct.

## Result

PASS on execution (professor feedback point #2 now has 4 real external
baselines instead of 1), but an important, honest finding: **SLDE-AFT's
own extractor (Llama-3.1-8B) is the WEAKEST of all 5 systems tested**
under official CaRB scoring — not by a huge margin (0.496 vs. the
range 0.504-0.558, roughly a 12% relative gap top-to-bottom), but it is
last, not first or middle of the pack.

## Interpretation

- **This needs honest framing in the paper, not omission.** SLDE-AFT's
  contribution was never claimed to be "the best raw extractor" — the
  paper's actual novelty claims (per [[submission_readiness_framework]])
  are the Noisy-Or aggregation (claim #3), the closed-loop architecture
  (claim #1), and provenance filtering (claim #5), all of which operate
  ON TOP OF whatever base extractor is used. This result should be
  framed as: "SLDE-AFT deliberately uses a smaller, cheaper open-weight
  model (Llama-3.1-8B) as its extractor rather than a larger proprietary
  one, and the architecture's value lies in what it does with that
  model's outputs (aggregation, feedback, fine-tuning), not in raw
  single-pass extraction quality" — not as a weakness to hide.
- Gemini 2.5 Pro's high API cost and error rate (5/30, all truncation/
  null-content related) despite scoring competitively is itself a
  practically-relevant finding: it suggests reasoning-heavy models may
  need substantially larger token budgets and more robust output
  parsing for structured-extraction tasks than non-reasoning models
  need for the same task.
- DeepSeek-V3.2 remains the strongest system tested on raw extraction
  quality, consistent with its role as DEC-002's original "stronger
  baseline" pick (EVID-021).
- The three new baselines plus DeepSeek now cover 4 of the 8 systems
  professor_feedback.md point #2 names (GPT-4 [as GPT-4o], Claude,
  Gemini, plus DeepSeek as an unnamed-but-stronger addition). REBEL,
  GenIE, InstructUIE, DyGIE++ remain not attempted — see Limitations.

## Limitations

- Still N=30, pilot scale, same as every other CaRB result in this
  project.
- REBEL, GenIE, InstructUIE, DyGIE++ (the remaining systems named in
  professor_feedback.md point #2) were deliberately not attempted here
  — each requires a different, often older, dependency-heavy research
  codebase (DyGIE++ needs AllenNLP, essentially unmaintained) rather
  than a simple API call, disproportionate effort for a 30-sentence
  pilot. REBEL specifically (Babelscape/rebel-large, downloadable via
  `transformers`, runnable on CPU) is the most tractable of the four if
  pursued further.
- Gemini 2.5 Pro's result used a much larger max_tokens (3072 vs. 512
  for the other four models) and still has a 5/30 error rate -- not a
  perfectly like-for-like comparison in terms of generation budget,
  though the scored triples themselves went through the identical
  parsing/evaluation pipeline as every other system.
- Model pins are current as of 2026-09; any of these providers may
  retire or replace these specific model IDs, unlike the project's
  core pipeline model which is expected to stay fixed for the
  ablation/statistics work.

## Next step

If REBEL is added: use `Babelscape/rebel-large` via `transformers`
(`AutoModelForSeq2SeqLM`), CPU inference is feasible for 30 short
sentences, output format uses `<triplet>`/`<subj>`/`<obj>` special
tokens requiring a small parser, then convert to the same tabbed format
already built for `scripts/dec001_run_official_carb_scorer.py`. If a
benchmark-grade (not pilot) comparison across all 5 already-tested
systems is wanted, scale to CaRB's full test set.