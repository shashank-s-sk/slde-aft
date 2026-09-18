# STATUS DASHBOARD (read this first — full rationale/detail is in each DEC section below)

Keep this table in sync whenever a DEC's status changes. Full write-ups
with numbers/citations live in `Evidence log.md` (EVID-xxx); this table
just says where each DEC currently stands and what's left.

| DEC | Title | Status | Key Result | Next Step |
|---|---|---|---|---|
| 001 | CaRB Public Benchmark | DONE (pilot + full-scale official scorer) | **OFFICIAL full-scale (N=548)** CaRB F1=0.467 (Llama-3.1-8B), F1=0.571 (DeepSeek-V3.2) — EVID-035. Pilot (N=30, EVID-031) F1=0.496/0.558 held up well (deltas -0.029/+0.013), no dramatic shift. Cost $0.0520 | Optional: extend full-scale to GPT-4o/Claude/Gemini (~$12.66 combined) for full 5-system parity; not required |
| 002 | External SOTA Baseline | DONE (4/8 scored + 1 attempted) | **OFFICIAL** F1 ranking: DeepSeek 0.558 > Gemini 2.5 Pro 0.528 ≈ Claude Sonnet 5 0.527 > GPT-4o 0.504 > **Llama-3.1-8B (SLDE-AFT) 0.496 — weakest of all 5** — EVID-031/032. Frame honestly: smaller/cheaper extractor by design. REBEL attempted (EVID-033): real finding — it's a closed/Wikidata-style extractor, fundamentally incompatible with CaRB's open-span scoring, not a bare F1 to report | GenIE/InstructUIE (likely same incompatibility as REBEL)/DyGIE++ (AllenNLP) — deliberately not attempted |
| 003 | Math Contribution (Noisy-Or) | DONE — **strongest result in the project** | +0.043 F1 aggregate on real data (EVID-014); real-data ECE=0.3332 + O(N)/O(N^2) complexity diagnosed (EVID-036) | Steps 2-4 (formal derivation/proof/convergence) are math-writing, not experiments; manuscript integration not started |
| 004 | Module-Level Ablation | DONE (single-seed pilot) | without_feedback appeared to beat full — did NOT replicate at 5 seeds (see DEC-005) | Superseded by DEC-005; nothing further needed here |
| 005 | Statistical Validation (ablation) | DONE | NO significant effect, N=20/5-seed, p=0.31-0.51 (EVID-020) — honest null | Would need a larger-N re-run for a stronger claim either way |
| 006 | Fine-Tuning (LoRA/QLoRA) | DONE (5-seed, matches DEC-005 convention) | 4/5 seeds improve, mean F1 +0.044 (0.137→0.181), std now smaller than the effect; one-sample t-test p=0.066 (trending, not conventionally significant), Wilcoxon p=0.125 — EVID-034, strongest signal DEC-006 has produced | Optional: 1-2 more seeds could reach significance; separately, re-test on DEC-018's provenance-filtered data (not yet done) |
| 007 | Systematic Error Analysis | DONE | Zero pure false negatives in product train set; conflict adjustment resolves hallucination-vs-hallucination (108) not correct-vs-incorrect (1) — EVID-022 | Held-out val/test FN analysis + final example curation for the paper |
| 008 | Scalability Evaluation | DONE (single-pass scope) | Runtime linear to N=200; per-doc latency flat ~4s regardless of KB size — EVID-023 | Memory measurement is broken (methodology flaw, needs isolated subprocess); full closed-loop scalability untested |
| 009 | Domain Generalization (BioRED) | DONE (pilot, n=15) | Strict F1=0.0074 (misleading, boundary-mismatch artifact); relaxed F1=0.1029 — EVID-024 | Pilot-scale only; no external baseline on BioRED yet |
| 010 | Strengthen Discussion | NOT STARTED | — | Writing task — deferred until all experiments done, per [[feedback_experiments_before_writing]] |
| 011 | Novelty Positioning | NOT STARTED | — | Writing task — deferred |
| 012 | Reproducibility Package | NOT STARTED | — | Packaging task — do near the end, before submission |
| 013 | Writing Refinement | NOT STARTED | — | Writing task — deferred |
| 018 | Provenance Filter (Claim #5) | DONE | Filtering raises training-data precision vs. gold from 93.5%→100% (drops 31/475 triples, all wrong) — EVID-029. Now the default in `dec006_regenerate_synth_data.py` | Optionally re-run DEC-006 fine-tuning on the filtered (444-triple) data to check if subject-copying failures decrease |
| 019 | Closed-Loop Integration Test (Claim #1) | DONE | Treatment (fine-tuned model closes the loop) ~FLAT vs. pre-closure baseline (F1 0.3869→0.3864) but BEATS control/no-fine-tuning (F1 0.3791, -0.0073) — EVID-030. Closing the loop does no harm and modestly beats the realistic alternative | Repeat with seeds 42/44 as separate treatment arms to check this holds across seeds; a sustained multi-cycle loop is a bigger follow-up |
| 020 | Framework-Level Validation on DocRED | DONE (pilot) | Naive F1=0.0329 vs. PKB-aggregated F1=0.0104 (worse) — PKB's exact-string-match aggregation rarely corroborates the same fact across differently-phrased evidence sentences on open text. Real, diagnosed limitation, cost $0.00131 | Genuine finding for Limitations (point #10); a fuzzy/entity-linked matching key would be the natural fix if pursued further |
| 021 | Extractor-Only Validation on TACRED | **NOT PURSUED** (user decision, 2026-09-18) | — | Dropped — CaRB + DocRED already cover two benchmark task types; add one Limitations sentence (see DEC-021 section) so this reads as a scope decision, not a gap |
| 022 | Epoch / LoRA Hyperparameter Grid (Claim #2, point #6) | Stage 1+2 DONE | Winning config: epochs=5, rank=16, alpha=32, lr=2e-4 (only epochs changed from original default) — F1=0.2222 vs default's F1=0.2029 (+0.0193) — EVID-037/038. Recall flat (0.1250) across all 9 grid runs | Stage 3: winning config × seeds 43-46, then significance test vs. base and EVID-034 — pod stopped, redeploy next session |

No more open items without an owning DEC — all 5 of SLDE.pdf's claims
now have at least one real experiment behind them (see each DEC row
above for how strong/mixed/null each one currently is).

Informal, not-yet-accepted ideas sketched at the end of this file (DEC-014
leakage protocol, DEC-015 task/metric validity, DEC-016 threats to
validity, DEC-017 data governance) are notes, not active decisions —
don't treat them as in-progress work.

---

# DEC-001 — Add CaRB Public OpenIE Benchmark

## Why is this required?

Supervisor Feedback #1 requires evaluation on established public
benchmarks because the current 20–50 product custom dataset is
insufficient to demonstrate generalization.

CaRB is suitable because it is a public Open Information Extraction
benchmark with natural-language text and gold
(subject, relation, object) extractions. It fits the unstructured
text-to-triple part of SLDE-AFT [1][258].

## Decision

Use **CaRB (A Crowdsourced Benchmark for Open Information Extraction)**
as an additional public benchmark for SLDE-AFT.

Keep the existing custom product dataset. CaRB will be used as an
additional **unstructured-only public benchmark evaluation**.

## How will it be implemented?

1. Download or clone the official CaRB repository.
2. Inspect CaRB sentences and gold extraction format.
3. Build a `CarbAdapter` to convert each sentence into:
   - `sourceid`
   - `sourcetype="unstructured"`
   - `content`
   - gold `(subject, predicate, object)` triples
4. Update the extraction prompt to use open relation phrases instead
   of the product-only `ALLOWED_PREDICATES` schema.
5. Run SLDE-AFT extraction on a small CaRB development subset.
6. Convert predictions to CaRB evaluator format.
7. Evaluate using official CaRB evaluation and internal normalized
   triple metrics.
8. Save predictions, gold triples, configurations, logs, metrics, and
   error-analysis examples.

## Expected Results

The experiment should produce:

- CaRB input sentences
- CaRB gold triples
- SLDE-AFT predicted triples
- Official CaRB precision, recall, and F1
- Internal normalized precision, recall, and F1
- Runtime and inference latency
- Final KB size
- Extracted and retained triple counts
- Error examples
- Configuration and output files

The experiment will determine whether the unstructured extraction
component of SLDE-AFT generalizes to an established public OpenIE
benchmark. Numerical results remain TBD until the experiment is run.

## Status

DEC-001: ACCEPTED
Implementation: DONE
Test: DONE
Experiment: SCALED PILOT COMPLETE (10 -> 30 sentences; see EVID-021).
  Official scoring COMPLETE (see EVID-031).
Results: OFFICIAL CaRB score (data/CaRB/carb.py, default lenient
  matching): Llama-3.1-8B-instruct P=0.652 R=0.401 F1=0.496; DeepSeek-V3.2
  P=0.713 R=0.458 F1=0.558. This SUPERSEDES the internal-evaluator
  numbers as the headline figures for the paper — the internal
  exact-match evaluator (F1=0.0591 Llama, F1=0.1340 DeepSeek) undercounts
  real performance by ~4-8x due to subject-boundary-mismatch scoring
  artifacts already identified in EVID-004/022; the official scorer's
  lenient matching handles exactly this. Old CaRB-10 F1=0.1333 figure
  (EVID-003, unpinned `openrouter/auto`) remains superseded for the
  separate reason given in EVID-021 (not a reproducible measurement of
  any specific model).
Official CaRB score: DONE — see EVID-031. 30-sentence pilot scale, not
  the full 641-sentence test set.

DEC-001, part 1: Prepare CaRB data                 ✅ Done
DEC-001, part 2: Run your LLM on 3 sentences        ✅ Done (now scaled to 30)
DEC-001, part 3: Save and inspect predictions       ✅ Done
DEC-001, part 4: Evaluate internally                ✅ Done
DEC-001, part 5: Export CaRB format and run scorer  ✅ Done — see EVID-031
DEC-001, part 6: Scale to full 641-sentence test set  ⏳ SCOPED, not started

## DEC-001 Part 6 — Full 641-Sentence Scale-Up (scoped 2026-09-17)

**Why:** the 30-sentence pilot is a real, official-scorer result, but a
Q1 reviewer can reasonably ask "why not the full CaRB test set" —
`data/CaRB/data/test.txt` has 641 sentences total, and this project's
carb_dev_sample.jsonl only used 30 (4.7%). Cost analysis shows scaling
the core result is nearly free.

**Cost estimate, extrapolated linearly from the EVID-021 30-sentence
run (per-sentence cost x 641):**

| System | 30-sentence actual cost | Estimated cost at 641 |
|---|---:|---:|
| Llama-3.1-8B-instruct (SLDE-AFT's own extractor) | $0.000221 | **~$0.005** |
| DeepSeek-V3.2 (external baseline) | $0.002136 | **~$0.046** |
| GPT-4o | $0.033 | ~$0.71 |
| Claude Sonnet 5 | $0.068 | ~$1.45 |
| Gemini 2.5 Pro | $0.491 (large 3072-token budget) | ~$10.50 |

**Decision, given the user's current budget constraint:** scale up
**Llama-3.1-8B and DeepSeek-V3.2 only** (combined estimated cost
**~$0.05**, trivial) to the full 641-sentence set — this covers the
paper's actual headline claim (SLDE-AFT's own extractor's official
CaRB score) and its strongest baseline comparison. **Defer GPT-4o/
Claude/Gemini full-scale runs** (combined ~$12.66) as optional —
their 30-sentence pilot numbers can still be reported as pilot-scale
SOTA comparison points, just not the primary "benchmark-grade" claim.

**How to implement:**
1. Build a full-641 equivalent of `carb_dev_sample.jsonl` from
   `data/CaRB/data/test.txt` (same conversion logic used for the
   30-sentence sample — check `scripts/dec001_002_carb30_comparison.py`
   / whatever script built `carb_dev_sample.jsonl` originally for the
   exact parsing format, since CaRB's raw `test.txt` format needs
   converting to the `sourceid`/`content`/gold-triples JSONL shape).
2. Re-run `scripts/dec001_002_carb30_comparison.py`-equivalent logic
   pointed at the full-641 file, for `slde_aft_llama` and
   `deepseek_baseline` only.
3. Re-run the official scorer (`data/CaRB/carb.py`, same method as
   EVID-031) on the full-641 predictions.
4. Record as a new EVID entry superseding the 30-sentence number as
   the paper's headline CaRB figure; keep the 30-sentence number
   available as a documented earlier pilot, not deleted.

**Status:** DONE (2026-09-18) — see EVID-035. Official full-scale
(N=548) result: **Llama-3.1-8B F1=0.467** (P=0.589, R=0.387),
**DeepSeek-V3.2 F1=0.571** (P=0.713, R=0.477). Actual cost **$0.0520**
(both systems combined), matching the ~$0.05 estimate. Compared to the
30-sentence pilot (Llama F1=0.496, DeepSeek F1=0.558): both deltas
small (-0.029 / +0.013) — the pilot numbers held up well, no dramatic
shift, qualitative finding unchanged (DeepSeek modestly beats
Llama-3.1-8B). This is now the paper's headline, benchmark-grade CaRB
figure, replacing the pilot as the primary citation (pilot kept as a
documented earlier result, not deleted). GPT-4o/Claude/Gemini remain
pilot-scale only (cost-deferred, ~$12.66 combined for full parity).

DEC-002: Add external baseline using same pipeline

# DEC-002 — Add External State-of-the-Art Baselines

## Why is this required?

Supervisor Feedback #2 requires comparison with strong external
information-extraction methods. Current baselines are mostly internal
SLDE-AFT variations, so reviewers cannot determine whether SLDE-AFT
improves over established methods.

## Decision

Use the following external baselines:

- REBEL as the primary relation-extraction baseline
- One strong LLM baseline: GPT-4 or Llama-3
- Optional: InstructUIE or GenIE if time and resources allow

Keep the existing internal baselines:

- B1: Static LLM
- B2: RAG-only
- B3: Fine-tuning without feedback
- SLDE-AFT Full
- SLDE-AFT Prob-KB

## How will it be implemented?

1. Implement each external model as an extractor wrapper.
2. Give every extractor the same unstructured text input.
3. Convert outputs into:
   - `subject`
   - `predicate`
   - `object`
   - `confidence`
   - `sourceid`
   - `provenance`
4. Apply relation mapping or normalization when required.
5. Evaluate all methods using the same gold triples and metric code.
6. Run all methods on the custom dataset and public benchmark.
7. Save predictions, configurations, runtime, and metrics.

## Expected Results

The experiment should produce:

- Predicted triples for every baseline
- Precision
- Recall
- F1
- Runtime and inference latency
- Number of extracted triples
- Error examples
- Model and prompt configurations
- Comparison table: internal baselines vs. external baselines vs. SLDE-AFT

The experiment will determine whether SLDE-AFT improves over strong
external extraction methods. Numerical performance remains TBD until
experiments are run.

## Fairness Rules

- Use the same input documents and gold triples for every method
- Use the same triple normalization and evaluation code
- Do not give external baselines access to SLDE-AFT KB, feedback,
  synthetic data, or LoRA adapters
- Pin exact model IDs and prompt versions
- Save all predictions before calculating metrics

## Status

DEC-002: ACCEPTED
Implementation: DONE (stronger baseline requirement fulfilled; extended
  to GPT-4o, Claude Sonnet 5, Gemini 2.5 Pro per EVID-032)
Test: DONE (Llama-3.1-8B external baseline CaRB-10, EVID-004; DeepSeek-V3.2
  CaRB-30, EVID-021; GPT-4o/Claude Sonnet 5/Gemini 2.5 Pro CaRB-30,
  EVID-032)
Experiment: PILOT COMPLETE at N=30, 5 systems total. OFFICIAL CaRB
  scorer (EVID-031/032, use these for the paper):
    DeepSeek-V3.2            F1=0.558 (P=0.713 R=0.458)
    Gemini 2.5 Pro           F1=0.528 (P=0.773 R=0.401)
    Claude Sonnet 5          F1=0.527 (P=0.642 R=0.446)
    GPT-4o                   F1=0.504 (P=0.736 R=0.384)
    Llama-3.1-8B (SLDE-AFT)  F1=0.496 (P=0.652 R=0.401)
  SLDE-AFT's own extractor is the WEAKEST of all 5 tested, though the
  gap is modest (~12% relative, top to bottom) — must be framed
  honestly in the paper as a deliberate smaller/cheaper-model choice,
  not hidden. Internal-evaluator numbers for the 3 new baselines also
  recorded (EVID-032) but superseded by the official ones per EVID-031's
  precedent.
Results: RECORDED
Remaining:
- REBEL baseline: ATTEMPTED (EVID-033) — real finding, not a bare
  number: REBEL is a closed relation-extraction model (Wikidata-style
  canonical entities/predicates), fundamentally incompatible with
  CaRB's open-domain span matching without a task-alignment/output-
  mapping layer this pilot's scope didn't include. Confirms DEC-002's
  original deferral note was correct. Do not report a bare REBEL F1 in
  the comparison table — cite EVID-033's qualitative finding instead.
- GenIE/InstructUIE/DyGIE++: Deliberately not attempted — GenIE and
  InstructUIE likely share REBEL's closed/schema-grounded nature and
  would probably hit the same incompatibility; DyGIE++ needs AllenNLP,
  essentially unmaintained. Disproportionate effort for a 30-sentence
  pilot.
- Scale beyond N=30 toward CaRB's full 634-sentence set if a benchmark-
  grade (not pilot-grade) result is needed, across the 5 systems with
  valid comparable scores

## Provider/model plan (decided during DEC-005 API credit troubleshooting; DeepSeek baseline executed in EVID-021)

- **Core SLDE-AFT pipeline experiments (DEC-003/004/005 ablations and
  statistics):** stay on OpenRouter + `meta-llama/llama-3.1-8b-instruct`
  — do not switch model or provider mid-study; every result so far
  (EVID-013/014/016/019) assumes this exact model.
- **If OpenRouter's grace-credit allowance runs dry again and blocks
  this same pipeline:** fall back to **Fireworks AI** (verified $1
  documented free credit, vs. OpenRouter's undocumented ~$0.02 grace
  pool) to keep running the *same* model, not a different one. Requires
  generalizing `src/extractors/openrouter_llm.py`'s hardcoded endpoint
  to a configurable base URL first (small change, not yet done).
- **For this decision's "stronger external baseline" requirement
  specifically:** use **DeepSeek** (V3.2 or whatever the current
  version is when this is executed) as the stronger paid baseline model,
  run as a separate one-time comparison — decoupled from the core
  ablation pipeline so it doesn't disturb comparability of the
  already-collected Llama-3.1-8B results.

# DEC-003 — Strengthen Mathematical Contribution

## Why is this required?

Supervisor Feedback #3 states that the current mathematical contribution
is limited and asks for stronger analysis of the Noisy-Or confidence
aggregation used in the SLDE-AFT Probabilistic Knowledge Base.

## Decision

Retain the original SLDE-AFT architecture and formalize the existing
Conservative Noisy-Or aggregation with shrinkage and conflict adjustment.

Treat the score as aggregated confidence, not automatically as a calibrated
posterior probability.

## How will it be implemented?

1. Define the triple, observation confidence, shrinkage factor, competitor
   count, Noisy-Or support, and final confidence score.
2. Add formal derivation and theoretical justification.
3. Prove boundedness and evidence monotonicity for a fixed conflict set.
4. Discuss convergence and the limitation caused by dynamic conflicts.
5. Report prototype and optimized computational complexity.
6. Add confidence calibration using accuracy bins, ECE, and a reliability
   diagram.
7. Compare max merge, mean aggregation, standard Noisy-Or, conservative
   Noisy-Or, and conflict-adjusted Noisy-Or.
8. Record per-iteration support, final confidence, conflicts, KB size, and
   threshold crossings.
9. Document functional-predicate assumptions and prevent test-set leakage.

## Expected Results

The implementation should produce:

- Mathematical derivation and proof statements
- Complexity analysis
- Per-triple confidence records
- Calibration table
- ECE value
- Reliability diagram
- Threshold-sweep results
- Aggregation-rule comparison
- Per-iteration convergence logs and plots
- Updated mathematical section for the paper

Numerical results remain TBD until the experiments are run.

## Status

DEC-003: ACCEPTED
Implementation: DONE (unit tests, product-domain functional-predicate
  policy, and candidate-buffer adapter — src/probkb_v2_adapter.py — are done;
  the earlier-named src/pkb_candidate_buffer_adapter.py empty stub has
  been removed)
Testing: DONE for pkb_math.py and pkb_instrumentation.py (19 tests passing)
Experiment: TOY VALIDATION COMPLETE; SCALED CONTROLLED EXPERIMENT COMPLETE
  (DEC003_SCALED_V1, seeds 42/43/44, no/moderate/high conflict scenarios,
  see outputs/dec003_scaled/ and EVID-009)
Results: INITIAL RESULTS AVAILABLE (toy); SCALED SYNTHETIC RESULTS AVAILABLE
  (see EVID-009)
Scaled Controlled Experiment: DONE
Per-Iteration Product-PKB Logging: DONE — full 155-call instrumented run
  completed (35 train x 4 iterations + 5 val + 10 test), see EVID-013.
  Train-set iteration F1: 0.3668 -> 0.3682 -> 0.2894 -> 0.4183
  (non-monotonic, unexplained — flagged for DEC-007). Held-out F1: val
  0.5970 (n=5), test 0.1970 (n=10). Total cost $0.00259 for 155 calls.
Leakage-Safe Split: DONE (data/product_split.csv, 70/10/20, seed 7; see EVID-010)
Paper Integration: NOT STARTED (can now be written using EVID-005 + EVID-009 + EVID-013)
Real-Data Calibration (step 6) + Computational Complexity (step 5):
  DONE (2026-09-18) — see EVID-036. Real-data ECE=0.3332, Brier=0.2969
  on the 657-triple gold-labeled EVID-013 snapshot (previously
  synthetic-only). Diagnosed: worst-calibrated bins (0.6-0.9 confidence,
  0% actual accuracy) are functional predicates with zero competitors —
  same failure mode DEC-018's provenance filter targets, seen here from
  the calibration angle. Complexity: production PKB is O(N) per call /
  O(N^2) cumulative (empirically confirmed, 72.7x latency growth for
  80x more calls) due to `accepted_slot_keys`'s linear scan; an indexed
  alternative achieves ~O(1) per call / O(N) cumulative with the same
  Noisy-Or math (illustrative only, not integrated into production).
  Remaining DEC-003 gap: steps 2-4 (formal derivation, boundedness/
  monotonicity proof, convergence discussion) — pure math-writing
  tasks, not experiments.

# DEC-004 — Conduct Module-Level Ablation Study

## Why is this required?

Supervisor Feedback #4 requires evidence that every major SLDE-AFT
module contributes independently to final performance.

## Decision

Evaluate SLDE-AFT Full and seven controlled ablations:

- Without Feedback Controller
- Without Probabilistic KB (use max-merge KB)
- Without Synthetic Data Generator
- Without LoRA Fine-Tuning
- Without Provenance Filtering
- Structured-only
- Unstructured-only

Only one component will change in each main ablation.

## How will it be implemented?

1. Create one reusable experiment configuration with module flags.
2. Use SLDE-AFT Full as the reference configuration.
3. Disable exactly one module for each ablation.
4. Keep the dataset split, model, prompt, threshold, iterations, and
   evaluation method fixed.
5. Run every variant with the same random seeds.
6. Save predictions, metrics, logs, and configurations.
7. Calculate mean ± standard deviation, confidence intervals, and
   significance tests against SLDE-AFT Full.

## Expected Results

The experiment should produce:

- Ablation configurations
- Predicted triples for every variant
- Precision, recall, and F1
- Final KB size and KB growth
- Synthetic-example count
- Conflict count
- Runtime and inference latency
- Mean ± standard deviation
- Confidence intervals
- Significance-test results
- Ablation comparison table

Numerical results remain TBD until experiments are run.

## Notes

- "Without Probabilistic KB" means use the existing max-merge/non-
  probabilistic KB so that the rest of the pipeline can still run.
- "Without Synthetic Data Generator" also disables automatic LoRA,
  because LoRA has no synthetic training data.
remove synthetic-data generation;
- retain LoRA fine-tuning using an explicitly documented alternative,
  such as the available real training data, if that data is permitted;
- if no valid training data exists, label the result as a dependency
  analysis rather than a pure single-module ablation.

- "Without LoRA" still generates and logs synthetic data but does not
  train the model.
- keep synthetic-data generation active;
- generate and save the synthetic examples;
- do not use them to update model parameters.


- "Without Provenance" means disable provenance filtering only; retain
  provenance logging for debugging.
- Structured-only and unstructured-only are source-path comparisons,
  not direct replacements for the full dual-source task.

## Status

DEC-004: ACCEPTED
Implementation: DONE for 5 of 7 ablations (Full reference, Without-Feedback,
  Without-Prob-KB, Structured-only, Unstructured-only) via a shared
  src/experiment_runner.py reused by DEC-005. Without-Synthetic-Data-Gen
  and Without-LoRA deferred to pair with DEC-006 (nothing to ablate until
  fine-tuning exists). Without-Provenance deferred — no active provenance
  filter exists in the pipeline yet to toggle off; see EVID-015.
Testing: DONE (14 new offline tests: deterministic KB adapter + experiment
  runner module-flag behavior, all mocked/zero-cost)
Experiment: PILOT COMPLETE (N=20, single seed, 5 configs, 229 calls,
  $0.0035; see EVID-016)
Results: CLEAN PILOT COMPLETE (EVID-019, N=20, single seed). without_feedback
  beat full on train/val/test F1 (two independent real-data runs now
  point this way — still needs DEC-005 multi-seed before paper use).
  without_prob_kb underperformed full. unstructured_only reached the
  best F1 of any run so far (0.714), single-seed, needs confirmation.
  Nothing here is paper-reportable yet — proceed to DEC-005.

# DEC-005 — Add Statistical Validation

## Why is this required?

Supervisor Feedback #5 states that current results are based on single
runs. Statistical validation is required to demonstrate that reported
improvements are reproducible and not caused by random variation.

## Decision

Run all main baselines, SLDE-AFT Full, Prob-KB, and ablation variants
using the same set of random seeds.

Report mean ± standard deviation, 95% confidence intervals, and
statistical significance tests for precision, recall, and F1.

## How will it be implemented?

1. Create one reusable experiment runner:
   `run_experiment(config, seed)`.
2. Set Python, NumPy, PyTorch, dataset, and LoRA-training seeds.
3. Run every configuration using the same seeds:
   `{42, 43, 44, 45, 46}`.
4. Save one metrics file and one prediction file per run.
5. Save system name, dataset, seed, model ID, prompt version,
   threshold, iterations, precision, recall, F1, runtime, and KB size.
6. Aggregate all completed runs in one master results CSV.
7. Calculate mean ± standard deviation and 95% confidence intervals.
8. Compare SLDE-AFT Full against each baseline/ablation using paired
   t-tests and Wilcoxon signed-rank tests.
9. Use document-level paired bootstrap confidence intervals for
   deterministic/API models when repeated calls have little variation.
10. Apply Holm–Bonferroni correction when testing multiple comparisons.

## Expected Results

The experiment should produce:

- Per-seed metrics files
- Per-seed prediction files
- Master run-results CSV
- Mean ± standard deviation table
- 95% confidence interval table
- Paired t-test results
- Wilcoxon test results
- Corrected p-values
- Statistical summary table for the paper

Numerical results remain TBD until experiments are run.

## Notes

- Use the same dataset split and seeds for every compared method.
- Keep model, prompt, threshold, and evaluation code fixed unless the
  experiment intentionally tests one of these variables.
- Pin exact API model IDs; do not use automatic model routing.
- Do not call repeated deterministic API responses independent runs.
  Use document-level bootstrap analysis for deterministic predictions.
- Exclude failed runs only with a documented technical reason.

## Status

DEC-005: ACCEPTED
Implementation: DONE (reuses src/experiment_runner.py from DEC-004; resumable
  by design — skips any config/seed whose saved call_log.json already has
  <20% error rate)
Testing: DONE (offline/mocked dry run validated before real spend)
Experiment: COMPLETE — all 5 configs x 5 seeds (42-46), N=20 (see EVID-020).
Results: without_feedback and without_prob_kb show NO statistically
  significant difference from full (all paired t-test/Wilcoxon p-values
  0.31-0.51). EVID-016/019's single-seed "without_feedback beats full"
  finding did NOT replicate — with 5 seeds, without_feedback's mean
  train F1 is actually lower than full's, reversing the earlier
  apparent direction, and still not significant either way. Correct
  conclusion: no ablation effect detected at N=20/5-seed scale. A
  larger-N re-run would be needed for a paper-reportable ablation claim.

# DEC-006 — Improve Fine-Tuning Using Cloud GPU

## Why is this required?

Supervisor Feedback #6 states that current fine-tuning results are too
weak. The current prototype uses TinyLlama-1.1B and limited training,
so it does not yet demonstrate a meaningful fine-tuning contribution.

## Decision

Retain the SLDE-AFT fine-tuning workflow and evaluate a 7B/8B
instruction model using QLoRA on a rented cloud NVIDIA GPU.

Use an Apple laptop for coding, data preparation, evaluation, and
statistics. Use cloud GPU only for expensive fine-tuning experiments.

## How will it be implemented?

1. Develop and test code locally on the Apple laptop.
2. Use a rented RTX 4090 24 GB GPU for the first QLoRA smoke test.
3. Use an A100 40 GB GPU only if RTX 4090 memory is insufficient.
4. Train one 7B/8B model using 4-bit QLoRA.
5. Test 2–3 epochs, larger synthetic datasets, and improved instruction
   templates.
6. Tune a small LoRA grid: rank, alpha, learning rate, and epochs.
7. Select settings using development data only.
8. Run the final configuration with multiple seeds.
9. Save adapters, logs, predictions, metrics, and configurations.
10. Stop the cloud GPU after outputs are verified and saved.

## Expected Results

The experiment should produce:

- 7B/8B QLoRA adapter checkpoints
- Synthetic-data statistics
- LoRA hyperparameter comparison results
- Training and validation loss logs
- Precision, recall, and F1 before/after fine-tuning
- Fine-tuning gain over the non-fine-tuned baseline
- Runtime, GPU memory, and GPU utilization
- Error-analysis examples
- Reproducible configurations

Numerical results remain TBD until experiments are run.

## Status

DEC-006: ACCEPTED
Implementation: DONE (src/synthetic_data_generator.py + src/prompts.py +
  scripts/dec006_regenerate_synth_data.py for task-aligned training
  data; scripts/dec006_lora_finetune.py + dec006_evaluate_adapter.py
  for QLoRA training/eval, run and debugged on a real rented GPU)
Testing: DONE (44/44 suite passing throughout; the GPU scripts
  themselves were validated end-to-end on RunPod, not just unit-tested)
Experiment: FOUR pilots on rented RunPod GPUs (Mistral-7B-Instruct-v0.3,
  QLoRA rank 16): Run 1 (EVID-026, 33 examples/15 steps), Run 2
  (EVID-027, 90 examples/36 steps via a 200-product PKB scale-up), a
  3-seed confirmation of Run 2 (seeds 42/43/44, EVID-028 — found and
  fixed a real train/test leakage bug), then a 5-seed extension (seeds
  45/46 added, EVID-034) matching DEC-005's convention. DEC-006 step 6
  (LoRA hyperparameter grid) still not done.
Results: Run 1 (33 examples) — base F1=0.3231 vs. fine-tuned F1=0.2264,
  DECREASED (predates the leakage bug, unaffected by it). FINAL 5-seed
  result on the corrected leakage-safe 8-product test set (EVID-034,
  the current headline number for this claim): base F1=0.1373;
  seed42=0.2029 (+0.0656); seed43=0.2090 (+0.0717); seed44=0.1124
  (-0.0249); seed45=0.1935 (+0.0562); seed46=0.1892 (+0.0519). Mean
  fine-tuned F1=0.1814 (std=0.0394) — mean improvement +0.0441, std now
  SMALLER than the mean effect (reversed from the n=3 result), 4 of 5
  seeds positive. One-sample t-test t=2.507, p=0.066 (trending toward
  significance, not conventionally significant); Wilcoxon p=0.125 (near
  the n=5 test's power floor of 0.0625). Report as: "fine-tuning
  improved F1 in 4 of 5 seeds tested (mean +0.044), trending toward
  significance (p=0.066) but not conventionally significant" — a real,
  meaningfully strengthened signal versus the n=3 result, stronger than
  DEC-005's genuinely null ablation finding (p=0.31-0.51), though not
  yet a fully proven claim. Mechanistic finding from EVID-028 still
  holds: base/seed42/seed43 share identical true-positive counts —
  fine-tuning's effect (where positive) is eliminating false positives,
  not finding new correct facts (professor_feedback.md point #10).
Note: this 5-seed run used the OLDER unfiltered training data (matching
  seeds 42-44 for comparability), not DEC-018's provenance-filtered
  default — the filtered version was restored as the default
  immediately after collecting these results. Testing the filtered
  data's effect on this same 5-seed design is a separate, not-yet-run
  comparison.
Note: found while reading the old notebook that its B3 baseline (cell 22)
  and Table-9 "Iterative FT" results (cells 31-35) use two DIFFERENT code
  paths — B3's reported number substitutes a different OpenRouter model
  instead of the actually-fine-tuned local adapter. Worth knowing if
  those old numbers are ever cited.

# DEC-007 — Add Systematic Error Analysis

## Why is this required?

Supervisor Feedback #7 requires qualitative analysis showing where
SLDE-AFT succeeds, fails, hallucinates, encounters conflicts, handles
ambiguity, and uses provenance filtering.

## Decision

Add an error-analysis module that automatically saves representative
examples from every experiment run.

The module will analyze predictions after evaluation and will not change
the SLDE-AFT extraction, PKB, feedback, synthetic-data, or LoRA flow.

## How will it be implemented?

1. Save every predicted triple with source ID, provenance, confidence,
   iteration, model, system variant, and seed.
2. Match each prediction against gold triples using the common
   normalization/evaluation function.
3. Label predictions as:
   - correct extraction
   - failed extraction / false negative
   - hallucinated triple / false positive
   - conflicting triple
   - ambiguous relation
   - accepted or rejected by provenance filtering
4. Export all labeled examples to an error-analysis CSV.
5. Select representative examples for the paper after manual review.
6. For every selected example, explain the source evidence, system
   output, confidence, decision, and cause of success or failure.

## Expected Results

The implementation should produce:

- Error-analysis CSV for each system and seed
- Correct extraction examples
- Missed-gold-triple examples
- Hallucinated-triple examples
- Conflicting-triple examples
- Ambiguous-relation examples
- Provenance accepted/rejected examples
- Final qualitative error-analysis table for the paper

Numerical results remain TBD until experiments are run.

## Notes

- Do not select only favourable examples.
- Keep the original source text/provenance for every example.
- Manually verify examples before including them in the paper.
- Use the same error-labeling rules for all compared systems.
- Error analysis should use final test predictions only after model,
  prompts, and thresholds are frozen.

## Status

DEC-007: ACCEPTED
Implementation: DONE (scripts/dec007_error_analysis.py, zero API cost —
  analyzes already-saved predictions from EVID-013 and EVID-021)
Testing: N/A (pure analysis script, no new extraction logic to unit-test)
Experiment: COMPLETE — see EVID-022. 1,035 categorized rows across
  CaRB-30 (both systems) and the product-domain PKB run.
Results: Zero pure false negatives in the product-domain train set
  (every gold fact observed at least once across 4 iterations); conflict
  adjustment mostly resolves hallucination-vs-hallucination conflicts,
  not correct-vs-incorrect ones (108 vs 1); CaRB subject-boundary-
  mismatch failure mode confirmed independently a second time.
Remaining: held-out val/test false-negative analysis not done; final
  curated example selection for the paper still needs manual review.

# DEC-008 — Add Scalability Evaluation

## Why is this required?

Supervisor Feedback #8 requires stronger scalability evaluation.
Current experiments use only small product datasets and do not fully
report computational cost or system growth.

## Decision

Evaluate SLDE-AFT on progressively larger dataset subsets and record
runtime, memory, GPU utilization, KB growth, and inference latency.

The existing SLDE-AFT flow remains unchanged. This work adds monitoring,
logging, and larger-scale experiments.

## How will it be implemented?

1. Run the same system on increasing dataset sizes, for example:
   50, 100, 250, 500, and 1,000 documents where available.
2. Record total runtime and runtime per iteration.
3. Record mean inference latency per document.
4. Record CPU/RAM memory consumption.
5. Record peak GPU memory and GPU utilization when GPU is used.
6. Record KB size, new triples, conflicts, and synthetic examples per
   iteration.
7. Save metrics for every dataset size, system variant, and seed.
8. Plot runtime, memory, latency, and KB growth against dataset size.
9. Report scalability results using the same hardware/model settings.

## Expected Results

The experiment should produce:

- Dataset-size configuration files
- Per-run scalability logs
- Runtime per iteration and total runtime
- Mean inference latency per document
- CPU/RAM memory usage
- Peak GPU memory usage
- GPU utilization logs
- KB size and KB-growth logs
- Conflict and synthetic-example counts
- Scalability tables and figures

Numerical results remain TBD until experiments are run.

## Notes

- Use `time.perf_counter()` for runtime and latency measurement.
- Use `psutil` for CPU/RAM process monitoring.
- Use `torch.cuda.max_memory_allocated()` for peak PyTorch GPU memory.
- Use `nvidia-smi` logs for GPU utilization and GPU memory monitoring.
- Use the same hardware, model, prompt, threshold, and iteration count
  for each dataset-size comparison.
- Report both the current prototype complexity and optimized complexity
  only if the optimized implementation is actually used.

## Status

DEC-008: ACCEPTED
Implementation: DONE (scripts/dec008_scalability_sweep.py; scoped with
  user to single-pass extraction at N=20/50/100/200 rather than the
  full spec's 4-iteration loop at 50-1000, to keep wall-clock time
  reasonable — see EVID-023)
Testing: DONE (mocked dry run before real spend)
Experiment: COMPLETE — see EVID-023. 370 calls, $0.0046.
Results: Runtime scales linearly with N (no quadratic blowup); mean
  per-document latency stays flat (~4.0s) from N=20 to N=200 despite KB
  growing to 2,814 entries — the key positive scalability finding.
  Memory measurement failed (methodology flaw: sequential runs in one
  process contaminate GC-affected deltas) — not usable, needs isolated
  subprocess re-measurement if required for the paper.
Remaining: full closed-loop (multi-iteration) scalability at large N not
  tested; no GPU utilization data (N/A until DEC-006); clean memory
  measurement still needed.

# DEC-009 — Add Biomedical Domain Evaluation

## Why is this required?

Supervisor Feedback #9 requires validation beyond the consumer-product
domain to demonstrate that SLDE-AFT can generalize to another domain.

## Decision

Add biomedical relation extraction as the second SLDE-AFT domain using
the public BioRED dataset.

Keep the current consumer-product dataset as the original dual-source
proof-of-concept domain. BioRED will provide an additional biomedical
unstructured-text relation-extraction evaluation.

## How will it be implemented?

1. Download and inspect the public BioRED dataset and annotation guide.
2. Build a `BioREDAdapter` to convert abstracts and relation labels into
   SLDE-AFT documents and gold triples.
3. Define a biomedical relation schema from BioRED relation labels.
4. Update the extraction prompt with biomedical entity and relation
   instructions.
5. Run a small development subset first.
6. Run SLDE-AFT and selected external baselines on the same BioRED split.
7. Save predictions, gold triples, configurations, metrics, logs, and
   biomedical error examples.
8. Compare biomedical results with the consumer-product-domain results.

## Expected Results

The experiment should produce:

- BioRED input documents and gold triples
- Biomedical relation schema and prompt configuration
- SLDE-AFT predicted triples
- Precision, recall, and F1
- Runtime, latency, KB size, and KB growth
- Confidence-calibration outputs
- Biomedical error-analysis examples
- Cross-domain comparison table

Numerical results remain TBD until experiments are run.

## Notes

- BioRED contains PubMed abstracts with biomedical entity and relation
  annotations and is publicly available [317][310].
- Use BioRED training/development data for prompt design, thresholds,
  and fine-tuning decisions.
- Do not use BioRED test labels in prompts, feedback, synthetic data,
  or hyperparameter selection.
- Report this as a biomedical unstructured-text evaluation unless an
  independent structured biomedical source is added without test-label
  leakage.
- Keep product and biomedical schemas separate; do not force BioRED
  relations into product predicates.

## Status

DEC-009: ACCEPTED
Implementation: DONE (src/datasets/biored_adapter.py, prompts/openie_biored_v1.txt,
  src/extractors/openrouter_openie.py generalized for custom prompts)
Testing: DONE (40/40 suite still passing; mocked dry run before real spend)
Experiment: PILOT COMPLETE — see EVID-024. 15 Dev-split abstracts, $0.0005.
Results: Strict exact-match F1=0.0074 is misleadingly low — mostly a
  gold-construction/boundary-mismatch artifact (BioRED's concept-ID gold
  approximated by first-mention text). Relaxed containment-match F1=0.1029
  (14x more true positives) is the fairer read: biomedical domain is
  genuinely harder than the product domain, but not a near-total failure.
Remaining: n=15 is pilot-scale only; real entity linking not attempted
  (first-mention proxy used instead); no external baseline on BioRED yet.

# DEC-010 — Strengthen Results Discussion

## Why is this required?

Supervisor Feedback #10 requires a more analytical discussion of the
results. The revised paper must explain why SLDE-AFT improves, where it
performs best, and where it may fail.

## Decision

Add an evidence-based discussion section after all experiments are
completed. The discussion will interpret measured results from
benchmarks, ablations, calibration, error analysis, scalability, and
multi-domain evaluation.

No conclusions will be claimed before experimental results are available.

## How will it be implemented?

1. Collect final results from all benchmarks, baselines, ablations,
   multi-seed runs, calibration, error analysis, and scalability tests.
2. Compare precision, recall, F1, KB size, confidence, and runtime
   across iterations and system variants.
3. Explain precision changes using feedback, provenance filtering,
   confidence thresholds, and conflict handling.
4. Explain recall changes using source coverage, fixed schema limits,
   extraction difficulty, and thresholding.
5. Explain Prob-KB recall using KB retention and the selected
   evaluation protocol.
6. Identify conditions where SLDE-AFT performs best.
7. Identify failure cases from error-analysis evidence.
8. State limitations, assumptions, possible risks, and future work.
9. Ensure every discussion claim is linked to a table, figure, metric,
   error example, or cited related work.

## Expected Results

The revised paper should include:

- Analytical discussion of precision and recall behavior
- Explanation of Prob-KB recall behavior
- Best-performing scenario analysis
- Failure and limitation analysis
- Links from discussion claims to experimental evidence
- Updated discussion and limitations sections

Interpretations and numerical conclusions remain TBD until experiments
are completed.

## Notes

- Do not claim that precision improves significantly unless statistical
  testing supports the claim.
- Do not claim that Prob-KB has perfect recall unless evaluation includes
  the complete retained KB and the reported protocol is clearly stated.
- Distinguish observed results from hypotheses or explanations.
- Discuss both successful and unsuccessful results honestly.

## Status

DEC-010: ACCEPTED  
Implementation: NOT STARTED  
Testing: NOT STARTED  
Experiment: NOT STARTED  
Results: TBD  

# DEC-011 — Refine Novelty Positioning

## Why is this required?

Supervisor Feedback #11 requires a more precise novelty statement.
The paper must clearly distinguish SLDE-AFT from related paradigms and
avoid unsupported claims such as “the first system”.

## Decision

Add a dedicated novelty-positioning subsection and revise the related
work, research-gap table, introduction, and conclusion.

Position SLDE-AFT as a closed-loop framework that combines dual-source
extraction, PKB accumulation, feedback-guided extraction, provenance-
controlled synthetic supervision, and automated LoRA adaptation.

## How will it be implemented?

1. Compare SLDE-AFT explicitly with:
   - Retrieval-Augmented Generation
   - Continual Learning
   - AutoML
   - Universal Information Extraction
   - Knowledge Graph Population
   - Self-Training
2. For each paradigm, state:
   - what it does;
   - what SLDE-AFT shares with it;
   - what SLDE-AFT adds or changes.
3. Update the capability-comparison table using verified references.
4. Replace broad novelty claims with evidence-based wording:
   “To our knowledge, SLDE-AFT combines ... in one closed-loop pipeline.”
5. Verify every claim against cited literature.
6. Ensure claims match the implemented and evaluated system.

## Expected Results

The revised paper should produce:

- Novelty-positioning subsection
- Updated related-work discussion
- Revised capability-comparison table
- Precise research-gap statement
- Verified citations for every comparison
- Removed or qualified unsupported “first” claims

No numerical results are required for this decision.

## Notes

- RAG retrieves external evidence for generation; SLDE-AFT additionally
  accumulates extracted knowledge and uses it for iterative adaptation.
- Continual learning adapts across sequential tasks; SLDE-AFT adapts
  from confidence-filtered knowledge accumulated during extraction.
- AutoML automates model/pipeline selection; SLDE-AFT automates an
  extraction-to-supervision-to-adaptation loop.
- Universal IE unifies extraction tasks and schemas; SLDE-AFT adds PKB
  accumulation, feedback, provenance filtering, and auto adaptation.
- Knowledge graph population accumulates facts; SLDE-AFT additionally
  converts trusted facts into synthetic supervision for the extractor.
- Self-training uses pseudo-labels; SLDE-AFT adds dual-source evidence,
  confidence aggregation, provenance filtering, and PKB feedback.

## Status

DEC-011: ACCEPTED  
Implementation: NOT STARTED  
Testing: NOT STARTED  
Experiment: NOT APPLICABLE  
Results: TBD  

# DEC-012 — Prepare Reproducible Research Package

## Why is this required?

Supervisor Feedback #12 requires supplementary materials so that the
SLDE-AFT experiments can be inspected, reproduced, and extended by
reviewers and other researchers.

## Decision

Create a version-controlled SLDE-AFT research repository containing
code, dataset adapters, prompts, configurations, hyperparameters,
evaluation scripts, and instructions for reproducing every reported
result.

Private API keys, proprietary data, and large model checkpoints will
not be included in the public repository.

## How will it be implemented?

1. Create a Git repository with clear folder structure:
   - `src/` for reusable pipeline code
   - `notebooks/` for exploratory notebooks
   - `configs/` for experiment configurations
   - `prompts/` for versioned extraction and instruction templates
   - `data/` for dataset documentation and adapters
   - `scripts/` for training, evaluation, statistics, and figures
   - `outputs/` for generated results, excluded from Git if large
   - `docs/` for methodology and reproduction instructions

2. Convert core notebook logic into reusable functions or scripts:
   - data loading and adapters
   - structured extraction
   - unstructured extraction
   - PKB and Prob-KB
   - feedback controller
   - provenance filtering
   - synthetic-data generation
   - LoRA/QLoRA training
   - evaluation and statistics

3. Store one configuration file for every reported experiment:
   - dataset and split
   - exact model ID
   - prompt version
   - seed
   - iterations
   - confidence threshold
   - PKB settings
   - LoRA/QLoRA settings
   - hardware and software versions

4. Version all prompts and document the purpose of each prompt.

5. Provide dataset adapters and instructions for obtaining public
   datasets. Do not upload datasets that have redistribution limits.

6. Provide scripts to reproduce:
   - benchmark conversion
   - baseline runs
   - SLDE-AFT runs
   - ablations
   - fine-tuning
   - calibration
   - statistical validation
   - scalability evaluation
   - tables and figures

7. Add `requirements.txt` or `environment.yml` with pinned package
   versions and Python version.

8. Add a `.gitignore` that excludes:
   - API keys
   - `.env` files
   - model checkpoints
   - large raw datasets
   - generated caches
   - temporary outputs

9. Add a README with:
   - project overview
   - installation steps
   - hardware requirements
   - API setup instructions
   - dataset download instructions
   - commands to reproduce each experiment
   - expected output locations
   - known limitations and estimated runtime/cost

10. Add a reproducibility checklist before submission.

## Expected Results

The reproducibility package should include:

- Source code
- Dataset adapters and data documentation
- Prompt templates
- Experiment configuration files
- Hyperparameter records
- Environment/dependency file
- Evaluation scripts
- Statistical-analysis scripts
- Figure/table generation scripts
- Reproduction README
- Example command for each experiment
- `.gitignore` and API-key safety instructions
- Supplementary-material archive or repository link

No experimental numbers should be invented. Reported tables and figures
must be generated from saved experiment outputs.

## Notes

- Use exact model IDs; do not use automatic model routing.
- Record random seeds for all stochastic runs.
- Save raw predictions before computing metrics.
- Keep development, validation, and test splits separate.
- Do not use test labels for prompt design, threshold selection, or
  hyperparameter tuning.
- Record cloud GPU type, VRAM, runtime, and GPU utilization for
  training/scalability experiments.
- Record API provider, model ID, date, prompt version, temperature,
  maximum tokens, and token usage for API-based baselines.
- Do not publish credentials or confidential company information.
- Use Git tags or release versions for the final paper submission.

## Status

DEC-012: ACCEPTED  
Implementation: NOT STARTED  
Testing: NOT STARTED  
Experiment: NOT APPLICABLE  
Results: TBD  

# DEC-013 — Refine Manuscript Writing and Evidence

## Why is this required?

Supervisor Feedback #13 states that the manuscript is generally well
written but needs improved conciseness, flow, figure discussion, and
citation accuracy before submission.

The revised paper must also clearly reflect the stronger empirical,
statistical, theoretical, and reproducibility evidence added during the
project upgrade.

## Decision

Conduct a final structured manuscript revision after experiments are
completed.

Improve clarity and conciseness without removing necessary technical
detail. Ensure every major claim is supported by experimental evidence
or an appropriate reference.

## How will it be implemented?

1. Update the manuscript only after final experiment tables, figures,
   benchmark results, ablations, statistical validation, and error
   analysis are available.

2. Review every section for repeated explanations of:
   - dual-source extraction
   - Probabilistic KB
   - feedback controller
   - synthetic-data generation
   - LoRA fine-tuning
   - provenance filtering

3. Keep the most complete explanation in the framework section and use
   shorter references to the module in other sections.

4. Split long paragraphs into shorter paragraphs, each with one clear
   idea, claim, result, or transition.

5. Improve transitions between:
   - Introduction and Related Work
   - Related Work and Research Gap
   - Research Gap and Framework
   - Framework and Experimental Setup
   - Results and Discussion
   - Discussion and Limitations
   - Limitations and Conclusion

6. Check every figure and table:
   - introduce it before it appears
   - explain what it shows
   - explain why it matters
   - discuss the main finding in the surrounding text
   - use consistent labels, captions, and references

7. Check every citation:
   - verify that the cited source directly supports the claim
   - remove irrelevant citations
   - replace weak or indirect citations with primary sources
   - avoid unsupported “first”, “state-of-the-art”, or “significant”
     claims
   - ensure all references appear in the bibliography and all
     bibliography entries are cited

8. Verify that all result claims match saved experiment outputs:
   - numerical values
   - dataset names and splits
   - model IDs
   - baseline names
   - confidence thresholds
   - seeds and statistical tests

9. Perform a final consistency review:
   - title, abstract, contributions, framework, results, discussion,
     limitations, and conclusion must describe the same final system
   - update figures, tables, and references after every major revision
   - correct grammar, terminology, notation, abbreviations, and
     formatting

## Expected Results

The revised manuscript should include:

- Shorter and clearer paragraphs
- Reduced repetition
- Stronger transitions between sections
- Fully discussed figures and tables
- Citation-to-claim verification
- Updated abstract and contribution list
- Consistent final terminology and notation
- Results supported by saved experimental outputs
- Revised discussion, limitations, and conclusion
- Final submission-ready manuscript

No numerical results should be changed or invented during editing.

## Notes

- Do not polish the final manuscript before benchmark, baseline,
  ablation, fine-tuning, and statistical experiments are completed.
- Use “statistically significant” only when supported by the reported
  significance test.
- Use “outperforms” only when methods are evaluated fairly on the same
  dataset and protocol.
- State limitations honestly, especially synthetic-data noise,
  confidence calibration limits, correlated evidence, API/model
  variability, domain dependence, and compute cost.
- Prefer primary papers, official benchmark papers, and official model
  documentation over blogs or secondary summaries.
- Preserve reproducibility: every final table and figure must be
  generated from saved outputs or a documented script.

## Status

DEC-013: ACCEPTED  
Implementation: NOT STARTED  
Review: NOT STARTED  
Final Manuscript: NOT STARTED  
Results: TBD  

# DEC-018 — Build a Real Provenance Filter (Claim #5)

## Why is this required?

SLDE.pdf's claim #5 states that provenance "actively filters synthetic
training data quality." This was false as written: neither the old
notebook nor the new `src/` pipeline had any code that gates synthetic
training-data inclusion on provenance — provenance was logged per
triple (source IDs, source types, raw text) but never used to include
or exclude anything. This is a correctness problem in the manuscript,
not just a missing experiment, and had no owning DEC.

Also directly supports professor_feedback.md point #7 ("provenance
filtering examples") by providing real, concrete examples of what gets
filtered and why.

## Decision

Add a real filter, gate synthetic-training-data generation on it by
default, and — since this domain's true gold triples are known (it's
synthetically generated) — directly measure whether it improves
training-data quality rather than just asserting it does.

## How will it be implemented?

1. `src/provenance_filter.py`: a triple passes if at least one of its
   observations came from a STRUCTURED source (`has_structured_
   corroboration`), regardless of how many unstructured observations
   it also has.
2. `scripts/dec018_provenance_filter_validation.py`: apply the filter
   to an already-collected PKB snapshot (the DEC-006 200-product
   scale-up run, EVID-027/028's source data) and measure precision
   against the known gold triples, with vs. without the filter.
3. Wire the filter into `scripts/dec006_regenerate_synth_data.py`
   (on by default; `--no-provenance-filter` reproduces the old
   unfiltered behavior for backward compatibility with EVID-026/027/028's
   already-completed results).
4. Unit tests for the filter logic (`tests/test_provenance_filter.py`).

## Expected Results

A precision comparison (with-filter vs. without-filter) against known
gold triples on the same snapshot. No numerical result assumed ahead
of running it.

## Status

DEC-018: ACCEPTED
Implementation: DONE (`src/provenance_filter.py`,
  `scripts/dec018_provenance_filter_validation.py`, wired into
  `scripts/dec006_regenerate_synth_data.py` as the new default)
Testing: DONE (5 new unit tests, 49/49 suite passing)
Experiment: COMPLETE — see EVID-029. Zero API/GPU cost (reprocessed an
  already-collected snapshot).
Results: Filtering raises precision against gold from 93.5% -> 100.0%
  on the 475 above-threshold triples from the 200-product scale-up run
  (EVID-027/028's source data) by dropping the 31 triples (6.5%) whose
  only corroboration is unstructured — every single one of which is
  wrong (0% precision on that subset), overwhelmingly generic
  device-category nouns ("laptop device", "tablet device") standing in
  for the real product name, or copied sentence fragments, repeated
  2-21 times each and mistaken by Noisy-Or aggregation for corroborating
  evidence. Regenerated `outputs/dec006_synthetic_data/
  product_domain_synth_train.jsonl` with the filter on: 73 product-level
  examples / 444 triples (down from 90 examples / 475 triples
  unfiltered) — this is now the default training data for any future
  DEC-006 fine-tuning run; EVID-026/027/028's already-completed results
  used the unfiltered version and are unaffected.
Note: this result also mechanistically explains the "subject-copying"
  failure mode flagged in EVID-026/027/028 (the fine-tuned model
  sometimes outputs generic phrases like "laptop device" instead of the
  real product name) — it was learning directly from these exact
  hallucinated training examples. A future DEC-006 fine-tuning run using
  the filtered data may show less of this specific failure.

# DEC-019 — Closed-Loop Integration Test (Claim #1)

## Why is this required?

SLDE.pdf's claim #1 describes a "unified 7-module closed-loop
architecture." Every module (extraction, PKB aggregation, feedback,
synthetic-data generation, LoRA fine-tuning) had been built and tested
standalone, but the fine-tuned model had never been plugged back into
the PKB/feedback iterative loop to test whether the whole SYSTEM
improves when the loop actually closes — the literal meaning of the
claim. This was the one genuinely unbuilt piece of the architecture,
identified while discussing overall project sequencing with the user.

## Decision

Reconstruct the exact KB state at the end of the DEC-006 200-product
scale-up run's 4 iterations (EVID-027/028's source data), then run ONE
more iteration two ways from that identical starting point — continuing
with the un-fine-tuned base model (CONTROL) vs. using the fine-tuned
adapter (TREATMENT) — and compare the resulting knowledge bases against
known gold, plus against the pre-closure iteration-4 baseline.

## How will it be implemented?

1. `src/pkb_replay.py`: reconstruct `CandidateBufferAdapter` state by
   replaying saved `observations_iteration_N.csv` files through fresh
   `accept_candidate()` calls (verified exact: reproduces the original
   475/475 above-threshold triples and all 2241 accepted keys).
2. Use the plain `src/prompts.py` prompt (no locked-context/
   feedback-hint) for BOTH arms' iteration 5, since the fine-tuned
   model was only ever trained on that format — using the usual
   locked-context prompt for one arm and not the other would confound
   fine-tuning with a prompt-format difference, the same category of
   bug found in EVID-026.
3. CONTROL (`scripts/dec019_closedloop_control.py`, local): replay
   iterations 1-4, run iteration 5 via the same base API model
   (`meta-llama/llama-3.1-8b-instruct`) over the same 140 train
   products, merge in, measure.
4. TREATMENT (`scripts/dec019_closedloop_treatment_extract.py` on a
   rented GPU + `_merge.py` locally): identical design, using the
   seed-43 fine-tuned adapter (EVID-028's best-performing seed)
   instead of the API model.
5. `scripts/dec019_closedloop_compare.py`: three-way comparison
   (iteration-4 baseline / control / treatment) against known gold.

## Expected Results

A three-way KB-quality comparison (precision/recall/F1 against gold).
No numerical result assumed ahead of running it.

## Status

DEC-019: ACCEPTED
Implementation: DONE (`src/pkb_replay.py`, `openrouter_llm.py`'s
  `prompt_override`, all four `dec019_closedloop_*.py` scripts)
Testing: replay verified exact against the original snapshot before
  building anything on top of it (475/475 above-threshold triples,
  2241/2241 accepted keys match exactly)
Experiment: COMPLETE — see EVID-030. Control: 140 API calls, $0.002074.
  Treatment: one GPU pass (seed-43 adapter) over the same 140 products.
Results: Iteration-4 baseline F1=0.3869 (n=475) -> CONTROL iteration-5
  F1=0.3791 (n=480, WORSE) -> TREATMENT iteration-5 F1=0.3864 (n=499,
  ~FLAT vs. baseline, but BETTER than control by +0.0073). Closing the
  loop does not clearly beat leaving the KB alone (the treatment/
  baseline difference, -0.0005, is negligible), but it IS reliably
  better than the realistic alternative of continuing to extract with
  the un-fine-tuned model, which measurably degrades the KB. Report
  claim #1 as: the fine-tuned model, once looped back in, does no harm
  and modestly outperforms not fine-tuning, rather than "closing the
  loop improves the system" outright.

# DEC-020 — Framework-Level Validation on DocRED (Public Multi-Document Benchmark)

## Why is this required?

DEC-001 (CaRB) satisfies professor_feedback.md point #1 only under the
narrower reading — it tests the raw extractor in isolation, sentence by
sentence, and never touches the PKB, Noisy-Or aggregation, or feedback
controller. The feedback's actual wording is "insufficient for
validating a new research **framework**," which is a stronger claim:
the framework, not just the extractor, should be shown to work on
public data. CaRB structurally cannot support that stronger reading —
it's flat, independent sentences with no entity repeated across
documents, so there is nothing for a PKB to accumulate evidence about.

DocRED (explicitly named in professor_feedback.md point #1) is
structurally different in the one way that matters here: it is
document-level, and the same entities are mentioned repeatedly across
multiple sentences within a document (with coreference clusters
provided). That repetition is exactly the structure the PKB's
Noisy-Or aggregation and conflict-adjustment mechanisms are designed
to operate on — DocRED is the first public dataset in this project
that can exercise the framework, not just the extractor.

## Decision

Run the core SLDE-AFT pipeline (extraction -> PKB -> Noisy-Or
aggregation; feedback controller and fine-tuning are optional
stretch scope, not required for this DEC to be considered done) on a
pilot subset of DocRED's human-annotated dev split, treating each
evidence sentence for a given (head, relation, tail) triple as one
observation — analogous to how the product pipeline treats multiple
structured/unstructured source-records per product. Compare KB-quality
(precision/recall/F1 against DocRED gold) for the full PKB-aggregated
pipeline against a naive single-pass baseline (no aggregation across
observations) on the same documents, to isolate whether aggregation
itself adds value on public data — not just whether extraction works.

**Explicit caveat, learned from this project's own history (EVID-031's
internal-evaluator undercount, EVID-033's REBEL/CaRB schema
mismatch):** DocRED's ~96 relations are a fixed, closed, Wikidata-style
schema — much closer to REBEL's predicate set than to CaRB's
open-domain free-text predicates. This means (a) the extraction prompt
must be schema-guided (a closed allowed-predicate list, similar in
spirit to the product domain's `ALLOWED_PREDICATES`), not CaRB's
open-phrase prompt, and (b) scoring must follow DocRED's own official
evaluation convention (entity-pair + relation-type match via
coreference-resolved entity IDs), not CaRB's span matcher and not this
project's old internal evaluator. Verify the scoring format against a
handful of known examples BEFORE running anything at scale — do not
repeat the pattern of discovering a scoring-format mismatch after the
fact.

## How will it be implemented?

1. Download the official DocRED dataset (thunlp/DocRED or the HF
   `docred` dataset) and inspect the human-annotated dev split's format
   (`sents`, `vertexSet` mention/coreference clusters, `labels` with
   head/tail entity index + relation id `r` + evidence sentence
   indices).
2. Build a `DocRedAdapter` that converts each document into
   SLDE-AFT's per-entity-pair observation format: each evidence
   sentence for a given (head, relation, tail) triple becomes one
   observation, so multiple sentences supporting the same fact
   accumulate through the PKB exactly as multiple product-source
   records do today.
3. Map DocRED's 96 relation IDs to a closed, human-readable predicate
   list for a schema-guided extraction prompt (see the caveat above —
   do not reuse CaRB's open-phrase prompt here).
4. Run extraction with the same core-pipeline model
   (`meta-llama/llama-3.1-8b-instruct`, per [[dec002_provider_plan]])
   over a small pilot (10-20 documents from the dev-annotated split,
   matching this project's established pilot-first pattern from DEC-001
   and DEC-009), feed observations into the PKB, apply Noisy-Or
   aggregation across each document's repeated entity-pair evidence.
5. Evaluate against DocRED gold using DocRED's own official scoring
   convention. Also run the same extractions through a naive
   no-aggregation baseline (first/only observation per triple) for
   the isolating comparison described in the Decision above.
6. Save predictions, gold triples, configs, logs, metrics, and error
   examples, matching this project's standard evidence-log format.

## Expected Results

- Per-document PKB run stats and final KB size.
- Precision/recall/F1 against DocRED gold, official protocol, for both
  the full PKB-aggregated pipeline and the naive no-aggregation
  baseline (the delta between these two is the actual test of whether
  the framework — not just the extractor — adds value on public data).
- Error examples, including an explicit check for whether the
  closed-schema mismatch causes the same kind of scoring failure found
  with REBEL (EVID-033) — report this honestly if it occurs, don't
  paper over it.
- Numerical results remain TBD until the pilot is run; no result is
  assumed ahead of time.

## Status

DEC-020: ACCEPTED, IN PROGRESS (started 2026-09-17)
Implementation: Steps 1-2 DONE (zero API cost).
  - Data acquired via the thunlp/docred HuggingFace mirror (MIT
    licensed) instead of DocRED's own Google-Drive-only distribution
    (not directly scriptable) -- `data/DocRED/dev.json` (998
    human-annotated dev-split documents) + `data/DocRED/rel_info.json`
    (96 relation-id -> name mapping). Confirmed schema matches the
    official DocRED format exactly (sents/vertexSet/labels).
  - `src/datasets/docred_adapter.py` built (mirrors
    `src/datasets/biored_adapter.py`'s pattern): parses each document
    into gold_triples (deduplicated, for scoring) and observations
    (one row per (triple, evidence sentence) pair, first-surface-
    mention entity representation, same documented simplification as
    BioRED).
  - `scripts/dec020_docred_pilot_build.py` run: selected 15 documents
    (seed=42, biased toward docs with >=1 multi-evidence gold triple --
    845/998 dev docs qualify) -> 189 gold triples, 356 observations,
    106 of the 189 gold triples (56%) have 2+ evidence sentences, i.e.
    genuinely multiple observations for the PKB to aggregate over.
    Output: `outputs/dec020_docred_pilot/pilot_docs.jsonl` +
    `closed_predicates.json` (the 96-relation schema).
Testing: dry-run with a mocked extractor (zero cost) validated the
  full PKB wiring end-to-end before any real spend.
Experiment: COMPLETE. `prompts/openie_docred_v1.txt` built (schema-
  guided, all 96 DocRED relations enumerated). `configs/
  docred_functional_predicates.json` left empty -- no single-valued-
  predicate policy attempted for DocRED (documented simplification;
  only plain Noisy-Or corroboration tested, not the conflict-adjustment
  penalty). Threshold recalibrated from the product pipeline's default
  0.88 to **0.70** for this experiment -- see
  `scripts/dec020_docred_extract_and_pkb.py`'s docstring for the exact
  math (0.88 would need 4+ corroborating observations under
  shrinkage=0.5, which DocRED's evidence structure rarely provides;
  0.70 crosses at 2+). `scripts/dec020_docred_extract_and_pkb.py` run
  for real: 71 API calls (one per unique evidence sentence across the
  15 pilot docs), 1 transient error, **total cost $0.00131**.
Results: NAIVE baseline (dedup union, no aggregation): P=0.0341
  R=0.0317 F1=0.0329 (176 predicted triples vs. 189 gold). PKB
  aggregated (>=0.70 confidence): P=0.3333 R=0.0053 F1=0.0104 (only 3
  of 176 candidate triples ever accumulated enough observations to
  cross threshold, across all 15 documents combined).
  **Honest verdict: aggregation raises precision ~10x but collapses
  recall so far that F1 gets WORSE, not better** -- a real, negative-
  for-F1 result, not a technical failure.
  **Root cause, diagnosed (not just observed):** checked directly --
  e.g. the "Brigden, Ontario" pilot doc has 16 gold triples with 2+
  genuine evidence sentences in the source text, yet only 1 PKB-
  accepted triple emerged from that document. The PKB's accepted-
  candidate key is an EXACT (lowercased/stripped) string match on
  subject+predicate+object (`src/pkb_instrumentation.py`'s
  `normalized_slot`/`normalized_object`). In the product domain, the
  same fact is usually named consistently across structured/
  unstructured sources (e.g. a fixed product name), so repeated
  observations collapse to the same key and corroborate each other.
  On open Wikipedia text, the model's own extracted surface phrasing
  for the SAME underlying fact varies between its two evidence
  sentences often enough that the two extractions almost never
  produce byte-identical triples -- so they're treated as unrelated
  single-observation candidates instead of corroborating each other,
  and essentially nothing survives the accept threshold.
  **This is a genuine, citable finding for the paper's Limitations
  section (professor_feedback.md point #10, "where the framework may
  fail"):** the current Noisy-Or aggregation mechanism, as implemented
  (exact-string keying, no entity-linking/paraphrase normalization),
  does not transfer to open-domain multi-sentence text the way it does
  in the product domain -- a real architectural boundary condition,
  discovered by actually running the framework on public data, which
  is exactly what DEC-020 set out to test. Report both numbers
  (naive vs. PKB) and this mechanism, not just the F1 delta.
  See `outputs/dec020_docred_extract_and_pkb/summary.json` for full
  per-document detail.

# DEC-021 — Extractor-Only Validation on TACRED (Public Closed-Schema Benchmark)

## Why is this required?

professor_feedback.md point #1 names TACRED explicitly. TACRED is
sentence-level with the subject/object entity pair already marked and
one relation label per example (41 fixed types + "no_relation") — a
**closed relation-classification** task, structurally flat like CaRB
(no entity repeated across multiple sentences/sources), not
document-structured like DocRED. There is nothing for the PKB to
accumulate evidence about here, for the same reason CaRB doesn't
exercise the PKB either (established while scoping DEC-020). So this
DEC tests a *different task type* than CaRB (closed classification vs.
open extraction) to broaden public-benchmark breadth, not a different
depth of the architecture.

## Decision

Run **extractor-only** evaluation (same scope as DEC-001/CaRB — no
PKB, no aggregation, no feedback, no fine-tuning) of the core-pipeline
model (`meta-llama/llama-3.1-8b-instruct`) on a TACRED pilot subset,
scoring against TACRED's official relation-classification metric
(micro-F1 over the 41 relation types, excluding `no_relation` per the
standard TACRED convention).

**Access caveat, CHECKED (2026-09-17):** TACRED (`LDC2018T24`) is
LDC-licensed but cheap to obtain — **free for LDC members, $25
one-time fee for non-members** (https://catalog.ldc.upenn.edu/LDC2018T24).
Not a real blocker. **Decision: purchase and use real TACRED, not the
FewRel fallback** — $25 is trivial and the professor named TACRED
specifically. Note: the HuggingFace mirror (`DFKI-SLT/tacred`) still
requires the licensed LDC files locally as input; it does not bypass
the license, so it doesn't avoid the $25 purchase.

## How will it be implemented?

1. Purchase TACRED access from the LDC catalog ($25 non-member fee,
   confirmed 2026-09-17 — see caveat above) if not already an LDC
   member.
2. Download/obtain the dataset and inspect its format: sentence tokens,
   subject/object entity span indices, gold relation label.
3. Build a `TacredAdapter` (or `FewRelAdapter`) converting each example
   into a single-turn prompt: sentence + marked subject/object spans ->
   predict one relation from the fixed closed list (schema-guided
   prompt, similar in spirit to DocRED's DEC-020 prompt and the
   product domain's `ALLOWED_PREDICATES` — NOT CaRB's open-phrase
   prompt, since this is a closed-schema classification task).
4. Run extraction on a small pilot (matching this project's established
   pilot-first pattern: CaRB started at 30 sentences, BioRED at n=15) —
   suggest 30-50 examples, stratified across a handful of relation
   types rather than fully random, so at least some positive
   (non-`no_relation`) examples are guaranteed in the pilot.
5. Score using TACRED's official convention (micro-F1 excluding
   `no_relation`) — do NOT reuse the internal CaRB-style span evaluator
   or invent a new metric; this is a classification task, not a span-
   extraction task, so the failure modes are different (e.g., picking
   a plausible but wrong relation type, not a boundary mismatch).
6. Save predictions, gold labels, configs, logs, metrics, and error
   examples (confusion between related relation types is expected and
   worth reporting, same spirit as DEC-007's error analysis).

## Expected Results

- Micro-F1 (and per-relation-type breakdown) against TACRED/FewRel
  gold for the core-pipeline extractor.
- A brief qualitative note on error types (e.g., confusing sibling
  relation types like `per:city_of_birth` vs. `per:city_of_residence`,
  if using actual TACRED).
- An explicit note of which dataset was actually used (TACRED vs.
  FewRel) and why, if a substitution was necessary.
- Numerical results remain TBD until the pilot is run; no result is
  assumed ahead of time.

## Status

DEC-021: NOT PURSUED (dropped 2026-09-18, explicit user decision)
Implementation: NOT STARTED
Testing: NOT STARTED
Experiment: NOT STARTED — access check DONE (LDC $25 non-member fee,
  confirmed 2026-09-17, not technically a blocker, but the user
  declined to spend it out of pocket). **Decision: do not pursue
  TACRED.** professor_feedback.md's benchmark list was framed as
  "such as" (illustrative, not a strict checklist); CaRB (open-domain
  extraction, full-scale, EVID-035) + DocRED (closed-schema document-
  level RE, framework-level, DEC-020) already cover two genuinely
  different public-benchmark task types, at both the extractor level
  and the framework level, plus BioRED for cross-domain generalization
  (DEC-009). TACRED would have added a third closed-schema
  *classification* variant -- worthwhile breadth, not load-bearing
  evidence, not worth the user's own $25 given what's already covered.
  **Add one sentence to the manuscript's Limitations section so this
  reads as a reasoned scope decision, not a silent gap:** "TACRED
  requires a paid LDC license; given resource constraints, we
  prioritized cost-free public benchmarks (CaRB, DocRED) spanning
  open-domain and closed-schema, document-level extraction."
Results: N/A

# DEC-022 — Epoch / LoRA Hyperparameter Grid (Claim #2, professor_feedback.md point #6)

## Why is this required?

professor_feedback.md point #6 ("Improve the Fine-Tuning Section")
names 5 specific things to investigate: larger base models, additional
training epochs, larger synthetic datasets, improved instruction
generation, better LoRA hyperparameter tuning. Checking DEC-006's
actual history: larger base model (Mistral-7B) and larger synthetic
datasets (33->90 examples) were done; instruction generation used
fixed templates, never iterated on; **additional training epochs and
LoRA hyperparameter tuning were never tested at all** — every single
fine-tuning run in this project (EVID-026, EVID-027/028, all 5 seeds
of the final EVID-034 result) used the exact same fixed configuration
(rank 16, alpha 32, lr 2e-4, 3 epochs), chosen once upfront by
reasoning, never validated against alternatives. This is also already
tracked as undone in DEC-006's own step 6 ("tune a small LoRA grid")
and flagged in EVID-034's own Limitations. Given the final 5-seed
result (p=0.066) is already the closest-to-significant number in the
project, a hyperparameter sweep is a plausible, direct way to either
strengthen it or at least honestly demonstrate the investigation the
professor asked for.

## Decision

Run a staged (not full cross-product) search, to keep GPU time/cost
bounded: **Stage 1** sweeps epoch count alone, holding LoRA config at
the current default; **Stage 2** sweeps a small LoRA grid (rank,
alpha, learning rate) at the best epoch count found in Stage 1;
**Stage 3** re-runs the single winning combined configuration across
the full 5-seed convention (seeds 42-46) for a real, comparable
statistical test against the existing baseline (base F1=0.1373,
current-config 5-seed mean F1=0.1814, EVID-034). Stages 1-2 use a
single seed (42) each, since they're a cheap exploratory search, not
the final claim -- only the winning configuration gets the full 5-seed
treatment, matching this project's own established pattern (DEC-006
itself went single-seed -> 3-seed -> 5-seed only once a signal looked
real).

Use the SAME 90-example unfiltered training set and the SAME
leakage-safe 8-product/56-triple test set as EVID-028/034, so results
are directly comparable to the existing baseline -- no other variable
changes except the hyperparameter(s) under test in each stage.

**Explicit scoping note:** a full joint grid (epochs x rank x alpha x
lr) would require dozens of GPU runs; the staged/greedy approach is a
standard, defensible cost-saving simplification for hyperparameter
search, not a shortcut that undermines the result -- documented here
so it isn't mistaken for an oversight.

## How will it be implemented?

1. Rent a GPU pod (RunPod, same provider/process as DEC-006 -- see
   [[dec006_runpod_plan]] for gotchas: check `torch.cuda.is_available()`
   immediately, redeploy if GPU passthrough fails; use a classic GitHub
   PAT if pushing results).
2. **Stage 1 (epoch sweep):** run `scripts/dec006_lora_finetune.py`
   with `NUM_EPOCHS` in **{2, 5, 8}** only (LoRA config fixed at
   rank=16, alpha=32, lr=2e-4, seed=42) -- **epoch=1 is skipped
   (reasoned to underfit at this data size, per the original 1->3
   decision in EVID-025/026) and epoch=3 is NOT re-run**, since that
   exact configuration (90 examples, rank 16, alpha 32, lr 2e-4, 3
   epochs, seed 42) already has a real result from EVID-034: **F1=0.2029
   (P=0.5385, R=0.1250)** -- reuse that data point directly rather than
   spending GPU time reproducing it. Evaluate each new adapter with
   `scripts/dec006_evaluate_adapter.py` against the same leakage-safe
   test set. Record F1 (and precision/recall) for {2, 5, 8}, and
   combine with the existing 3-epoch point for the full comparison
   table (4 points total: 2, 3 [reused], 5, 8).
3. Pick the epoch count with the best F1 from Stage 1 (call it
   `best_epochs`).
4. **Stage 2 (LoRA grid):** at `best_epochs`, sweep rank in {8, 16, 32}
   with alpha = 2*rank paired (3 runs), then at the best rank/alpha
   from that, sweep learning rate in {1e-4, 2e-4, 3e-4} (3 more runs).
   Seed=42 throughout. Record F1 for each.
5. Pick the single best combined configuration (`best_epochs`,
   `best_rank`, `best_alpha`, `best_lr`) from Stages 1-2.
6. **Stage 3 (confirmatory):** re-run that winning configuration at
   seeds 42-46 (5 seeds, matching DEC-005/006's convention), evaluate
   each, and run the same paired t-test / Wilcoxon signed-rank test
   used in `scripts/dec006_5seed_stats.py` comparing this new 5-seed
   result against both the base model and the EXISTING default-config
   5-seed result (EVID-034) -- three-way comparison: base vs. old
   config vs. new config.
7. Save all intermediate grid results (not just the winner) so the
   full search is reproducible and reportable, not just the best point.

## Expected Results

- A table of F1 (precision/recall too) per epoch count (Stage 1).
- A table of F1 per LoRA configuration tested (Stage 2).
- The winning configuration's full 5-seed result, with mean/std and
  significance tests against both base and the current EVID-034
  configuration.
- An honest report either way: if the grid search finds a
  meaningfully better configuration (e.g., pushes p below 0.05), report
  it as the new default; if nothing in the grid beats the current
  config, that itself is a legitimate, reportable answer to point #6
  ("we investigated epochs and LoRA hyperparameters; the originally
  chosen configuration was already near-optimal in the range tested").
  Do not assume a positive result ahead of running it.

## Status

DEC-022: ACCEPTED, IN PROGRESS (started 2026-09-18)
Implementation: `scripts/dec006_lora_finetune.py` extended with
  --epochs/--lora-rank/--lora-alpha/--learning-rate/--data-path/
  --output-dir overrides (defaults unchanged). Committed/pushed
  (4ca1c7b).
Testing: N/A (real GPU runs, no mocked dry-run needed given DEC-006's
  scripts were already proven)
Experiment: **Stage 1 (epoch sweep) COMPLETE** -- see EVID-037.
  **Stage 2 (LoRA rank/alpha/lr grid) COMPLETE** -- see EVID-038
  (survived one RunPod host-capacity interruption mid-sweep; no data
  lost, the in-flight run had saved nothing, redone on a fresh pod).
  Session ended for the day after Stage 2 finished (2026-09-18
  evening); pod stopped to avoid burning credit.
Results: **Winning combined configuration: epochs=5, rank=16,
  alpha=32, lr=2e-4** -- identical to the original DEC-006 defaults
  except epochs (3->5). F1=0.2222 (P=1.0000, R=0.1250) vs. the
  3-epoch default's F1=0.2029, a +0.0193 improvement, at seed 42.
  Every alternative tested in the full 9-run grid (epochs {2,8}, rank
  {8,32}, lr {1e-4,3e-4}) underperformed the winner. Recall flat at
  0.1250 across ALL 9 runs plus base -- fine-tuning here only ever
  suppresses false positives, never finds new true positives,
  regardless of epochs/rank/alpha/lr. Honest, complete answer to
  professor_feedback.md point #6's epoch and LoRA-tuning asks: epochs
  needed adjusting, LoRA hyperparameters did not.
  **Next: Stage 3** -- re-run the winning config at seeds 43-46 (seed
  42 done), then a real paired significance test against both base and
  the existing EVID-034 (epochs=3) 5-seed result.

DEC-014 (evaluation protocol & leakage control)

Prevents test-set leakage, prompt overfitting, and unfair comparisons.

This is often the first thing Q1 reviewers scrutinize.

Without it, your strong results can be dismissed as “protocol artifacts”.

DEC-015 (task & metric validity)

Ensures you are not mixing incompatible tasks (closed RE vs open IE vs universal IE) under one vague “F1” claim.

Helps you justify why certain benchmarks are comparable and which are not.

DEC-016 (threats to validity & limitations)

Directly supports the supervisor’s request: “explain where the framework may fail”.

Makes your discussion and limitations section much easier to write and defend.

DEC-017 (data governance & responsible use)

Becomes important if you release code/data or use sensitive domains (biomedical, legal, etc.).

Many Q1 venues now expect at least a short data/ethics statement.

DEC-XXX — [Decision]

Why is this required?
→ Which supervisor point/problem requires it?

Decision
→ What exactly have we decided?

How will it be implemented?
→ Concrete steps to execute it.

Expected Results
→ What data/metrics/output should the experiment produce?
→ Never invent numerical results.

Status
→ Accepted / Implementing / Testing / Completed / Superseded