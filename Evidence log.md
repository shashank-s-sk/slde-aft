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