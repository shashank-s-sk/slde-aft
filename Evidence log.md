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