# SLDE-AFT

Self-Learning Dual-Source Knowledge Extraction and Automated Fine-Tuning.
A closed-loop information-extraction framework combining structured and
unstructured extraction, a Probabilistic Knowledge Base (PKB), a
feedback controller, synthetic-data generation, and automated LoRA
fine-tuning.

This README documents the **modular, tested pipeline** (`src/`,
`scripts/`, `tests/`) built to strengthen the original prototype
notebooks (`SLDE_AFT_DualSource_Final_(20/30/40/50).ipynb`) against the
supervisor feedback in `professor_feedback.md`. See
`SLDE-AFT CODEBASE CONTEXT.md` for the full architectural background,
`Decision log.md` / `Evidence log.md` for what has and hasn't been
validated, and `Learnings.md` for lessons learned along the way — those
three files are the authoritative status record; this README is a
practical "how to run it" guide.

## Project status

**Do not treat any number in this repository as paper-ready until you
check its status in `Decision log.md`.** As of this writing:

- DEC-001 (public benchmark, CaRB): pilot only (10 sentences)
- DEC-002 (external baseline): pilot only (one Llama baseline on CaRB-10)
- DEC-003 (PKB math): experimentally complete except the paper write-up
- DEC-004 (ablation study): one clean single-seed pilot run complete
- DEC-005 (statistical validation): in progress
- DEC-006 through DEC-013: not started

## Repository structure

```
configs/     Functional-predicate policies (which predicates are
             treated as single-valued, for PKB conflict adjustment)
data/        Generated datasets, the leakage-safe product split, and
             CaRB benchmark data
docs/        (reserved for methodology/reproduction docs)
notebooks/   Original prototype notebooks + DEC-00x exploratory notebooks
outputs/     Generated experiment results (gitignored — regenerate via
             the scripts below, don't expect these to be committed)
prompts/     Versioned extraction prompt templates
src/         Reusable, tested pipeline code (see below)
scripts/     Entry points that run a full experiment using src/
tests/       Unit tests for everything in src/ (pytest)
```

### `src/` contents

| Module | Purpose |
|---|---|
| `datasets/product_generator.py` | Deterministic synthetic product generator (faithful port of the notebooks' `generate_product_record`) |
| `datasets/carb_adapter.py` | CaRB benchmark loader/adapter |
| `extractors/structured.py` | Deterministic structured (CSV-column) extractor, confidence 0.98 |
| `extractors/openrouter_llm.py` | OpenRouter LLM extractor (unstructured text → triples) |
| `pkb_math.py` | Conservative Noisy-Or aggregation + conflict adjustment (the DEC-003 math) |
| `pkb_instrumentation.py` | Per-observation and per-iteration PKB snapshot logging |
| `probkb_v2_adapter.py` | `CandidateBufferAdapter` — the Probabilistic KB, wired to the math + instrumentation |
| `deterministic_kb_adapter.py` | Monotonic max-merge KB (the DEC-004 "without Prob-KB" ablation target) |
| `feedback_builder.py` | Feedback-hint construction (the DEC-004 "without Feedback" ablation target) |
| `leakage_split.py` | Builds the 70/10/20 train/val/test product split |
| `experiment_runner.py` | `ExperimentConfig` + `run_experiment()` — the shared runner behind DEC-004 and DEC-005 |
| `evaluator.py` | Triple normalization + precision/recall/F1 |

## Setup

1. Python 3.12+ (developed and tested on 3.12.6).
2. `pip install -r requirements.txt`
3. Create a `.env` file in the repo root (already gitignored) containing:
   ```
   OPENROUTER_API_KEY=<your key>
   ```
   **Never commit this file or paste the key anywhere else.** Every
   script in `scripts/` reads it via a small inline parser (see any
   script's `load_api_key()`), not `python-dotenv`, so no extra
   dependency is needed.
4. Run the test suite to confirm the environment works, with zero API
   cost: `pytest tests/ -v`

## Reproducing experiments

Every script below is idempotent-ish and writes to its own
`outputs/<name>/` directory. **Real API calls cost real (if tiny)
money** — see the cost notes in `Evidence log.md` (EVID-011 onward);
typical full runs at this project's scale cost well under $0.01.

| Script | What it does | Real API calls |
|---|---|---|
| `python -m scripts.dec003_product_smoke_test` | 3-product smoke test of the real extraction pipeline | 3 |
| `python -m scripts.dec003_product_probkb_run` | Full instrumented product-domain PKB run (35 train x 4 iterations + 15 held-out) | ~155 |
| `python -m scripts.dec004_ablation_pilot` | 5-config ablation pilot at N=20 (full, without_feedback, without_prob_kb, structured_only, unstructured_only) | ~229 |
| `python -m scripts.dec004_rerun_unstructured_only` | Re-runs just the `unstructured_only` config | ~52 |
| `python -m scripts.dec005_multiseed_run` | Same 5 configs x 5 seeds (42-46); **automatically skips any (config, seed) whose saved `call_log.json` already has <20% error rate**, so it's safe to re-invoke after an interruption (e.g. a mid-run credit exhaustion) without re-spending on already-clean data | up to ~1,145 |

All of the above read `OPENROUTER_API_KEY` from `.env` and use
`meta-llama/llama-3.1-8b-instruct` via OpenRouter unless the script
says otherwise. Every run saves a `call_log.json` (per-call cost,
latency, HTTP status, error, and — for failed calls — the raw model
response) alongside its metrics, specifically so anomalies can be
diagnosed from saved artifacts instead of requiring a re-run.

### Zero-cost / offline

- `pytest tests/ -v` — full test suite, no network calls.
- `python -m src.leakage_split` — regenerates `data/product_split.csv`
  and its manifest.
- Every script above can be dry-run with zero cost by monkeypatching
  `extract_unstructured_llm` before calling `main()` — see the pattern
  used throughout this project's development (mock the LLM call,
  verify the pipeline wiring, then run for real).

## Known limitations (as of this writing)

- All experiments so far use a **single seed** (42) except the
  in-progress DEC-005 run — no result should be treated as
  statistically validated until DEC-005 completes and significance
  tests are run.
- The product dataset is entirely synthetic (see
  `src/datasets/product_generator.py`); no public benchmark result
  beyond a 10-sentence CaRB pilot exists yet.
- Held-out val/test splits at N=20 are very small (3 and 4 products) —
  single-product differences swing precision/recall substantially.
- LoRA fine-tuning (DEC-006) has not been ported from the original
  notebooks into `src/` yet; it still only exists in
  `SLDE_AFT_DualSource_Final_(*).ipynb`.
- A provenance *filter* (as opposed to provenance *logging*, which
  exists) has not been implemented anywhere in the pipeline.

## Where to look for more detail

- `SLDE-AFT CODEBASE CONTEXT.md` — full architectural/research context, read this before modifying anything.
- `SLDE_AFT_Mathematical_Contribution_Final.pdf` — the authoritative math specification for the PKB.
- `Decision log.md` — what was decided, why, and current status per decision (DEC-001 through DEC-013+).
- `Evidence log.md` — what was actually run, with real numbers (EVID-001 onward).
- `Learnings.md` — lessons learned, including a running inference table with confidence labels (CONFIRMED / HYPOTHESIS / INSUFFICIENT DATA).


## PROMPT
You are helping me bring the SLDE-AFT repo and paper up to the standard a strong Q1 journal reviewer expects. Read these first, in order: README.md, professor_feedback.md, slde_aft_next_steps.md, "Decision log.md" (status dashboard), "Results Summary.md", then the relevant EVID entries in "Evidence log.md". Then run `pytest tests -q`.

## Ground rules (non-negotiable)
1. Never invent, estimate, round, or "clean up" any number. Every figure must come from a saved output file or an EVID entry. If a number can't be traced, say so.
2. Never delete or overwrite existing experiments, notebooks, or outputs. Work on a new branch `q1-rework`. Commit after each phase.
3. Never read, print, or commit `.env` or the API key.
4. Before any run that costs API money, or GPU time beyond a few minutes, give me a cost/time estimate and wait for my approval. Anything estimated over $2 always needs approval.
5. Pre-register before running: for each new experiment, write the hypothesis, metric, seeds, test, and what result would count as a null in the Decision log BEFORE running it. Report nulls and negatives honestly. No re-running to chase significance.
6. After each phase, update "Decision log.md", "Evidence log.md" and "Results Summary.md" consistently, then stop and give me a short report (what was done, what changed, what is still weak). Do not start the next phase until I say go.

## Phase 0 - Audit (no API spend)
Produce `AUDIT.md`: for each of the 13 professor points, what exists, what is missing, and which claims in "Results Summary.md" are stronger than the underlying evidence. Specifically check and report on:
- The "Claim 3 (Noisy-Or) is strongest" framing versus the ablation result where `without_prob_kb` (max-merge) is numerically >= full at N=50, and versus EVID-014, where the +0.043 F1 is conflict-adjusted vs RAW Noisy-Or (not vs a naive baseline), single run, and flat-to-negative on the 117 conflict rows.
- Whether the epochs=5 choice was selected on the same held-out test set used for the 5-seed confirmation (EVID-037/038/040).
- Whether the provenance-filter result (93.5% -> 100%) is circular because the structured CSV and the gold labels come from the same generator (`src/datasets/product_generator.py`).
- Whether the "base" fine-tuning F1 is one fixed number used in a one-sample t-test.
- Which experiments have no raw outputs committed (outputs/ is gitignored).

## Phase 1 - Fix validity threats
1a. Tuning leakage: redo hyperparameter/epoch selection using the validation split only, then evaluate once on the untouched test split. If the split is too small, propose a larger leakage-safe split (e.g. extend `data/product_split_200.csv` usage) and show me the manifest before running.
1b. Noisy-Or vs baselines: run a multi-seed (>=10) end-to-end comparison of max-merge, mean, standard Noisy-Or, conservative Noisy-Or, and conflict-adjusted conservative Noisy-Or, on held-out data, with a validation-chosen threshold. Report best-F1, precision, recall, ECE, Brier, and paired tests. Also run it on the DocRED and CaRB-derived data if feasible.
1c. Provenance circularity: design and run an experiment where the structured source is corrupted at controlled noise rates (e.g. 0/5/10/20%). Report the filter's precision/recall under noise. If the filter only works because structured data is perfect, say so.
1d. For fine-tuning significance: the base model is deterministic (greedy decoding), so do NOT invent per-seed base variance. Instead quantify test-set uncertainty: (1) paired bootstrap over test PRODUCTS comparing base vs each fine-tuned seed on identical products, reporting 95% CIs on F1 difference; (2) rerun on a larger leakage-safe held-out set (>=30 products) with hyperparameters chosen on the validation split only. Report training-seed variance and test-set variance separately. Do not claim generalization from the 8-product test set.
## Phase 2 - Reproducibility (professor point 12)
- Commit (or provide a documented download script for) the raw outputs behind every reported number, excluding large adapters and secrets.
- Add `scripts/reproduce_all.py` that regenerates every table in "Results Summary.md" from saved raw outputs, and diff its output against the summary.
- Fix README status (it's stale), complete `requirements.txt` (torch, transformers, peft, trl, bitsandbytes etc. in a separate `requirements-finetune.txt`), record pinned model IDs, dates, temperature/top-p/max-tokens, seeds, hardware.
- Create `docs/` with reproduction steps and a data/licensing note.

## Phase 3 - Close evidence gaps (get approval per experiment)
- Scalability (point 8): rerun memory measurement in isolated subprocesses; log GPU memory/utilization for fine-tuning and inference; extend beyond N=200 if budget allows; fix or benchmark the O(N) accepted_slot_keys scan (indexed version wired in, same math, with a regression test).
- DocRED (point 1): implement a paraphrase/entity-normalised matching key as an option, and rerun the pilot on a larger sample (>=100 docs). Report it honestly even if it stays negative.
- Second domain (point 9): scale BioRED beyond n=15 with a relaxed-and-strict scorer and at least one external baseline.
- Baselines (point 2): extend GPT-4o/Claude/Gemini to a larger CaRB subset with CIs, if cost is acceptable. Do not report REBEL's raw F1; keep the incompatibility finding.
- Error analysis (point 7): curate a table of correct, failed, hallucinated, conflicting, ambiguous, and provenance-filtered examples with explanations.

## Phase 4 - Manuscript support
Write into `paper/` (LaTeX, Springer template placeholder), using only verified numbers:
- Math section: formal definition, derivation, boundedness and evidence-monotonicity proof for a fixed conflict set, convergence discussion and its limits under dynamic conflicts, complexity, calibration.
- Novelty positioning vs RAG, continual learning, AutoML, Universal IE, KG population, self-training. No "first system" claims.
- Missing Sections 8-11 (ablation, discussion, limitations, conclusion) and a rewritten abstract/results using the pinned-model numbers, not the old `openrouter/auto` figures.
- A claim-evidence table: each claim, its evidence, its strength (validated / trend / null / negative), and the exact wording I am allowed to use.
- Limitations must state: synthetic product domain, small held-out sets, single extractor family, API-model drift, monotonic-recall interpretation, TACRED not pursued.

Start with Phase 0 only. Stop when AUDIT.md is done.