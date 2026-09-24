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
| 020 | Framework-Level Validation on DocRED | DONE (pilot) | Naive F1=0.0329 vs. PKB-aggregated F1=0.0104 (worse) — PKB's exact-string-match aggregation rarely corroborates the same fact across differently-phrased evidence sentences on open text. Real, diagnosed limitation, cost $0.00131 | Genuine finding for Limitations (point #10); a fuzzy/entity-linked matching key would be the natural fix if pursued further **Superseded by DEC-031/EVID-046: exact-string explanation does not hold at 845 docs** |
| 021 | Extractor-Only Validation on TACRED | **NOT PURSUED** (user decision, 2026-09-18) | — | Dropped — CaRB + DocRED already cover two benchmark task types; add one Limitations sentence (see DEC-021 section) so this reads as a scope decision, not a gap |
| 022 | Epoch / LoRA Hyperparameter Grid (Claim #2, point #6) | **DONE — all 3 stages** | **epochs=5 config SIGNIFICANT vs. base** (one-sample t-test p=0.0028, 5-seed mean F1=0.2012 vs base 0.1373) — EVID-037/038/040. First fine-tuning config in the project to cross p<0.05. Not proven significantly better than the old epochs=3 config specifically (p=0.45/0.63) | None required. Optional: re-test epochs=5 on DEC-018's provenance-filtered data |
| 023 | N=50 Ablation Confirmatory Run (Claim #4, point #5) | DONE | Null result replicates at N=50: without_feedback p=0.57/0.63, without_prob_kb p=0.63/1.0 (t/Wilcoxon) — EVID-039. Variance shrank 3.6x vs N=20 (std 0.335→0.093). **Correction (AUDIT.md, 2026-09-20): n=5 seeds only detects effects >=~0.29-0.30 F1 (Cohen's d=1.68 needed for 80% power) — not "properly powered" for small-to-moderate effects, just a tighter measurement than N=20** | None — per DEC-023's pre-registered commitment, no further re-runs; reframe claim #4 as "tested at two scales, no effect >=~0.3 F1 detected either time" |
| 024 | Fine-Tuning Hyperparameter Selection Without Tuning-Leakage | PRE-REGISTERED, DEFERRED | User chose to write the manuscript now with an honest tuning-leakage caveat instead of running this fix | Available as future work / a revision-stage improvement if needed; not run |
| 025 | Closed-Loop Retest With the Headline (epochs=5) Fine-Tuned Model | SCOPED, NOT YET RUN | DEC-019's closed-loop test (EVID-030) used the now-superseded epochs=3 seed-43 adapter, not the paper's actual epochs=5 headline model (EVID-040) — Claims #1 and #2 have never been jointly tested | Needs a rented GPU pod + explicit go-ahead to spend; scripts ready (`scripts/dec025_closedloop_*.py`) |
| 029 | Higher-Powered Module Ablation (30 seeds) | DONE | Null for both modules; achieved MDE 0.070-0.086 F1 (EVID-045) | Written into Results Summary/main.tex |
| 031 | DocRED at Scale With a Normalised Matching Key | DONE (EVID-046) | Matching key does not explain the failure (norm closes ~0% of gap, oracle 7.3%); only 29/11,344 gold facts recovered from 2+ sentences; R3 precision 0.06->0.25, F1 null | Supersedes DEC-020's pilot |
| 032 | BioRED at Scale (extractor recall vs. corroboration) | PRE-REGISTERED, approved ($1.98) | — | Run extraction, then offline analysis |

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
  **SUPERSEDED (2026-09-24) by DEC-031/EVID-046:** the root-cause
  diagnosis above (exact-string keying) does not hold at 845 documents.
  A normalised key closes ~0% of the no-aggregation gap, and even a
  gold-alias oracle key closes only 7.3%. The binding constraint is that
  the extractor recovers only 29 of 11,344 gold facts from 2+ sentences
  (50.2% have 2+ evidence sentences in the gold annotations). This pilot
  also sent only gold evidence sentences to the extractor (an oracle
  setting). The text above is kept as the historical record.

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

DEC-022: DONE (all 3 stages complete, 2026-09-19)
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
  **Stage 3 (5-seed confirmatory run) COMPLETE** -- see EVID-040.
  Trained/evaluated seeds 43-46 (seed 42 already known) at the winning
  config. 5-seed F1: 0.2222/0.1972/0.2222/0.1935/0.1707, mean=0.2012
  (std=0.0194). **One-sample t-test vs. base: p=0.0028 -- SIGNIFICANT**
  (first fine-tuning config in the project to cross p<0.05). Wilcoxon
  p=0.0625 (the n=5 mathematical floor -- all 5 seeds positive vs.
  base). Direct paired comparison vs. the old epochs=3 config
  (EVID-034): p=0.45/0.63 -- NOT significant, so epochs=5 is proven
  significantly better than base, but not proven significantly better
  than epochs=3 specifically. Recommend citing this (epochs=5,
  p=0.0028) as the manuscript's primary fine-tuning evidence, with
  EVID-034's epochs=3 result demoted to "an earlier, less-tuned
  configuration."

# DEC-023 — N=50 Ablation Confirmatory Run (Claim #4, professor_feedback.md point #5)

## Why is this required?

DEC-005's N=20/5-seed ablation (EVID-020) found no significant
difference between `without_feedback`/`without_prob_kb` and the full
pipeline (p=0.31-0.51). Diagnosed root cause: the held-out test set at
N=20 has only 3-4 products, producing extreme per-seed variance (two
of five seeds scored held-out F1=0.0 exactly for `full`, std=0.335 —
larger than the mean itself). This is a statistical-power problem, not
necessarily proof of a zero effect: a real small-to-moderate effect
could easily be invisible at this noise level. DEC-005's own recorded
next step already named the fix ("a larger, paper-reportable ablation/
statistics result... needs a fresh run at full N=50 (or larger)
scale") but it was never executed.

**Explicit framing, agreed with the user:** this experiment is designed
to INCREASE STATISTICAL POWER to detect whatever effect actually
exists, not to engineer a positive result. Checked the actual feedback-
hint implementation (`src/feedback_builder.py`) first — it is NOT a
weak or buggy mechanism: it directly tells the model, in the next
iteration's prompt, which gold facts are still missing, which of its
own outputs are unsupported, and which predicates are undercovered.
There is no coding defect to "fix" here. If N=50 still shows no effect,
that is the correct, reportable conclusion — do not re-run further
seeds/scales hunting for significance once a fair, adequately-powered
test has been done.

## Decision

Re-run DEC-005's exact design (`src/experiment_runner.py`,
`scripts/dec005_multiseed_run.py`) completely unchanged except
`N_PRODUCTS` (20 -> 50). Same 5 configs (full, without_feedback,
without_prob_kb, structured_only, unstructured_only), same 5 seeds
(42-46), same model, same statistical tests (paired t-test + Wilcoxon
signed-rank vs. `full`).

## How will it be implemented?

1. Change `scripts/dec005_multiseed_run.py`'s `N_PRODUCTS = 20` to
   `N_PRODUCTS = 50` (the only code change).
2. Verify the leakage-safe split logic (`src/leakage_split.py`)
   produces a sensible 50-product train/val/test partition before
   spending on the real run (per this project's own established
   gotcha: splits computed at different N are not nested/consistent —
   confirm the new split doesn't silently overlap with any other
   experiment's data).
3. Dry-run with a mocked extractor first (zero cost), matching this
   project's standing practice before any real API spend.
4. Run the real 5-config x 5-seed sweep. Estimate: the N=20 version
   cost $0.017718 total; N=50 (~2.5x the products) should stay well
   under $1, but confirm actual cost as the run progresses rather than
   assuming.
5. Run the same paired significance tests as EVID-020, report
   whichever result actually comes out — significant, still null, or
   reversed — without re-running additional seeds/scales to chase a
   particular answer.

## Expected Results

- Mean +/- std F1 (train and held-out) for all 5 configs at N=50.
- Paired t-test / Wilcoxon p-values for without_feedback and
  without_prob_kb vs. full.
- A materially larger held-out test set (proportionally, ~7-10
  products instead of 3-4) should substantially shrink the variance
  that made EVID-020 inconclusive, whichever direction the mean effect
  turns out to point.
- Numerical results remain TBD until the experiment is run — no
  outcome is assumed ahead of time, in either direction.

## Status

DEC-023: DONE (2026-09-19) -- see EVID-039
Implementation: `scripts/dec023_ablation_n50.py` (reuses
  `src/experiment_runner.py` unchanged except N_PRODUCTS). Added
  per-call caching (`ExperimentConfig.cache_path`) to
  `src/experiment_runner.py` mid-run after 5 consecutive system-level
  low-memory kills destroyed whole-run progress; verified correct with
  a standalone test (caught a real bug: cached triples were initially
  missing fields needed by accept_candidate) before trusting it. All 6
  pre-existing experiment_runner tests still pass.
Testing: DONE (caching mechanism verified with a mocked flaky-then-
  fixed extractor before relying on it for the real run)
Experiment: COMPLETE. Total cost $0.0819. One reliability incident: a
  duplicate/concurrent background process ran briefly against the same
  output files before being caught and killed -- verified no data
  corruption resulted (see EVID-039's Reliability notes).
Results: **Null result replicates and gets STRONGER at N=50, not
  weaker.** Held-out test F1 paired vs. full: without_feedback mean
  diff=-0.045 (p=0.57/0.63 t/Wilcoxon), without_prob_kb mean
  diff=+0.033 (p=0.63/1.0). All comparisons p>=0.34. Critically,
  variance shrank substantially vs. EVID-020 (full's test F1 std:
  0.335 at N=20 -> 0.093 at N=50) -- so this is now a properly-powered
  null, not an inconclusive one. without_feedback's direction flipped
  sign again (N=20: +0.142; N=50: -0.045), consistent with noise
  around a near-zero true effect. **Per DEC-023's own pre-registered
  commitment: this is the final answer, no further re-runs.** Claim #4
  should be framed in the manuscript as "proposed and tested at two
  scales (N=20, N=50); no significant effect detected either time."

# DEC-024 — Fine-Tuning Hyperparameter Selection Without Tuning-Leakage (Phase 1a, AUDIT.md A2 fix)

## PRE-REGISTRATION (written before any run, per README.md's ground rule 5)

**Why this is required:** `AUDIT.md`'s A2 finding, verified directly against `scripts/dec006_evaluate_adapter.py`: DEC-022's epoch/LoRA hyperparameter search and its "confirmatory" 5-seed evaluation both used the identical 8-product test split (`data/product_split.csv`). There was no independent validation split separating "which config to pick" from "how well does the picked config generalize" — textbook tuning-on-the-test-set leakage. The reported one-sample t-test p=0.0028 (EVID-040) should not be trusted as an unbiased estimate.

**Fix:** use `data/product_split_200.csv` (verified: 140 train / 20 validation / 40 test, seed 7/42, confirmed identical to `src/leakage_split.build_product_split(n_products=200)` -- not a separately-computed file, just a snapshot of the same deterministic function). Select every hyperparameter using ONLY the 20-product validation split; evaluate the single winning configuration exactly once on the untouched 40-product test split.

**Hypothesis:** the epoch/LoRA configuration selected using only the validation split will still show an improvement over the base (non-fine-tuned) Mistral-7B model when evaluated on the untouched 40-product test split, though the effect size and significance may differ from EVID-040's leakage-affected result.

**Metric:** F1 (precision/recall also reported), computed by the existing leakage-safe, name-based exclusion logic already in `dec006_evaluate_adapter.py` (unchanged).

**Design:**
1. **Grid search (validation-only, seed 42, single run per config — matching DEC-022 Stage 1-2's own precedent of single-seed exploration before multi-seed confirmation):**
   - Epochs ∈ {2, 3, 5, 8}, LoRA fixed at the original default (rank=16, alpha=32, lr=2e-4). Evaluate each on the 20-product **validation** split (requires adding an `--eval-split {val,test}` option to `dec006_evaluate_adapter.py`, defaulting to `test` so existing usage is unaffected).
   - At the winning epoch count: rank ∈ {8,32} (alpha=2×rank) and lr ∈ {1e-4,3e-4}, same validation-only evaluation. (Reuses DEC-022's exact grid values for comparability.)
   - Pick the single best config by validation F1.
2. **Base-model reference (fresh, on the NEW test split — the old base F1=0.1373 is from a different 8-product test set and is not valid here per AUDIT.md A6):** evaluate the un-fine-tuned Mistral-7B once on the 40-product test split.
3. **Confirmatory run:** train the winning config at seeds 42-46 (5 seeds, matching DEC-005/006's convention), evaluate each **once** on the 40-product test split -- this evaluation happens exactly once per seed, with no further hyperparameter adjustment based on the result.
4. **Statistics:** one-sample t-test and Wilcoxon signed-rank of the 5 test-split F1 values against the fresh base F1 (step 2), matching EVID-034/040's method for comparability. Additionally report a paired bootstrap over test PRODUCTS (per README Phase 1d) to separate seed-level variance from test-set-level uncertainty -- not done in any prior DEC-006/022 result.

**Seeds:** 42-46 for the confirmatory step (5 seeds). Seed 42 only for the exploratory grid.

**What counts as a null:** p >= 0.05 (one-sample t-test) for the winning config vs. the fresh base F1 on the 40-product test set. **This will be reported as a null if that is the result** -- no re-running, no additional seeds, no post-hoc grid re-expansion to chase significance (ground rule 5).

**What this does NOT fix:** the provenance-filter circularity (A3) and the DEC-019 model-mismatch confound (A6) are separate issues, not addressed by this experiment. DEC-023's ablation power limitation (n=5, detects only effects >=~0.3 F1) is inherited here too -- if the true effect is small-to-moderate, this design will not reliably detect it either, and that limitation should be stated alongside any null result from this DEC.

## Cost / time estimate (awaiting approval before any run)

- GPU: same rented RunPod RTX 4090 (or 3090 fallback) used throughout DEC-006/022. Requires the user to deploy a pod, per that established workflow -- not something runnable from this session directly.
- Training runs: 4 (epoch grid) + 4 (LoRA grid) + 5 (confirmatory seeds) = 13 fine-tuning runs, each in the same ~100-500s range observed in DEC-022 (scales with epoch count). Estimated total GPU wall-clock: **~35-45 minutes.**
- Evaluation runs: 8 (grid, on 20 val products) + 5 (confirmatory, on 40 test products) + 1 (base model, on 40 test products) -- inference-only, a few minutes total, not a significant cost driver.
- No new OpenRouter/API costs (this is entirely local GPU fine-tuning + evaluation, same as DEC-006/022).
- **Estimated cost: well under $2** (RunPod community-cloud RTX 4090 rates are typically $0.30-0.50/hour; ~45 min of GPU time is a fraction of that), but this is a GPU-time estimate, not a precise dollar figure -- confirm actual pod rate before starting.

## Status

DEC-024: PRE-REGISTERED, DEFERRED (2026-09-21, explicit user decision).
  User chose to proceed with manuscript writing using honest, hedged
  language about the tuning-leakage limitation (AUDIT.md A2) rather
  than spend another GPU session running this fix first. Not
  cancelled -- the pre-registration stands and this remains available
  as genuine future work / a revision-stage improvement if a reviewer
  asks for it. The manuscript's fine-tuning claim (Section 7/Claim #2)
  must state the leakage caveat explicitly rather than presenting
  p=0.0028 as clean, unqualified significance.

# DEC-025 — Closed-Loop Retest With the Headline Fine-Tuned Model (Claim #1, epochs=3 -> epochs=5 swap)

## Why is this required?

DEC-019's closed-loop test (EVID-030, Claim #1's evidence) already runs
at N=200 (140 train-split products from `data/product_split_200.csv`,
reconstructing `outputs/dec006_scaleup_probkb`'s 4-iteration KB state)
-- this was verified directly against `scripts/dec019_closedloop_control.py`
after an earlier incorrect claim in this session that it was N=50 only;
that was wrong and is corrected here. What IS still true: DEC-019's
TREATMENT arm used `outputs/dec006_adapters/mistral7b_qlora_seed43`,
confirmed by the script's own docstring to be the **epochs=3** adapter
from EVID-028's era. The paper's actual headline fine-tuning result
(EVID-040, p=0.0028) is the **epochs=5** configuration from DEC-022/023
-- a model that has never been fed back into the closed loop. Claim #1
and Claim #2's headline numbers currently come from two different,
never-jointly-tested fine-tuned models.

## Decision

Re-run DEC-019's closed-loop comparison with a single variable changed:
swap the TREATMENT arm's adapter from epochs=3/seed=43 to epochs=5/seed=43
(same seed, so only the epoch count differs -- isolates that one
variable instead of confounding it with seed variation). Reuse DEC-019's
iteration-4 baseline and CONTROL arm unchanged (both are independent of
which fine-tuned adapter is being tested, so re-running them would spend
money to re-derive an answer already known).

## How will it be implemented?

1. **Train (GPU, new cost):**
   ```
   python scripts/dec006_lora_finetune.py --seed 43 --epochs 5 \
       --data-path outputs/dec006_synthetic_data/product_domain_synth_train_90unfiltered.jsonl \
       --output-dir outputs/dec025_adapters/mistral7b_qlora_epochs5_seed43
   ```
   (Same 90-example unfiltered dataset EVID-037/038/040 used, for direct
   comparability with the winning grid result -- not the current
   73-example provenance-filtered production default.)
2. **Extract (GPU, new cost):** `scripts/dec025_closedloop_epochs5_treatment_extract.py`
   -- same 140 train-split products, same plain prompt format, same
   generation config as DEC-019's treatment-extract step.
3. **Merge (local, zero cost):** `scripts/dec025_closedloop_epochs5_treatment_merge.py`
   -- replays iterations 1-4 fresh from the same snapshot DEC-019 used,
   merges in the epochs=5 model's iteration-5 triples, computes the same
   two metrics DEC-019 reported.
4. **Compare (local, zero cost):** `scripts/dec025_closedloop_compare.py`
   -- prints/saves a 4-row table: iteration-4 baseline, CONTROL
   (reused from DEC-019 as-is), TREATMENT epochs=3 (DEC-019, for
   reference), TREATMENT epochs=5 (this DEC, the headline-model result).

## Expected Results

A 4-row precision/recall/F1/KB-size comparison showing whether closing
the loop with the model that is actually the paper's headline
fine-tuning result behaves differently from DEC-019's original
epochs=3 finding (flat vs. baseline, beats not-fine-tuning in a
single-seed comparison). Numerical results remain TBD until the
experiment is run -- do not assume the direction in advance.

## What this does NOT fix

This is still a single-seed (43) comparison, still confounded by the
same model-family swap DEC-019 already disclosed (CONTROL uses
Llama-3.1-8B, TREATMENT uses fine-tuned Mistral-7B) -- this DEC only
changes which epoch count of the Mistral-7B adapter is used, it does
not address the model-family confound or add seed variation. If the
result is a null or flat finding, per this project's standing ground
rule (README.md ground rule 5 / DEC-023's precedent) it will be
reported as such -- no re-running to chase a different outcome.

## Cost / time estimate (awaiting approval before any run)

- GPU: same rented RunPod RTX 4090 workflow as DEC-006/022/024 -- requires
  the user to deploy a pod; not runnable from this session directly.
- Training: 1 run, epochs=5 on 90 examples -- DEC-022's own epochs=5
  grid run took well under 10 minutes on this same hardware.
- Extraction: 140 inference calls on the same GPU, no new OpenRouter/API
  spend -- comparable in wall-clock time to DEC-019's original treatment
  extraction (a few minutes).
- Merge + compare: zero cost, runs locally.
- **Estimated cost: a small fraction of an hour of RunPod time (well
  under $1 at typical $0.30-0.50/hour RTX 4090 rates)** -- confirm actual
  pod rate before starting.

## Status

DEC-025: SCOPED, NOT YET RUN (2026-09-22). Script and pre-registration
  written; awaiting a rented GPU pod and explicit go-ahead to spend
  before executing steps 1-2 above.

# DEC-026 — Offline Comparison of Confidence-Aggregation Rules (renumbered from task file's "DEC-025")

**Numbering note:** the task brief (`CLAUDE_TASK_dec025_aggregation_rules (1).md`)
labels this DEC-025, but DEC-025 above is already an active, separately
scoped decision (closed-loop retest with the epochs=5 adapter). This work
is logged as **DEC-026** instead; all file paths use `dec026_` in place
of the task file's `dec025_`. Flagged for the user's confirmation rather
than silently assumed.

## Why is this required?

DySECT (Amin-Naseri, Kim & Hruschka, ACL 2026, arXiv 2603.06915) already
publishes this project's exact aggregation rule (Eq. 1 conservative
Noisy-Or with lambda=0.75, Eq. 2 conflict-adjusted `/(m+1)` divisor), so
the formula itself cannot be claimed as a contribution (Section 2.7 of
the manuscript already documents this). Two failure modes of that rule
are already established in this repository from real (non-synthetic)
data:
- **Rival ceiling** (structural): for any functionally single-valued
  predicate with >=1 competing object, `C(t) = A(t)/(m+1) <= 0.5 < tau
  (0.88)`, so a contested slot can never be admitted regardless of
  evidence strength.
- **Repeat-counting** (EVID-029, EVID-036): the same document read
  multiple times (same model, temperature 0) produces identical output,
  and Noisy-Or's `f_i` exponent treats each repeat as independent
  corroboration. EVID-029 found 31 unstructured-only triples observed
  2-21 times each, 0% correct against gold; EVID-036 found ECE=0.3332 on
  the same 657-triple snapshot this DEC reuses.

This DEC replays the already-collected, gold-labeled snapshots through
five scoring rules (unchanged observations, only the aggregation
formula varies) to test whether a corrected rule beats the published
one, and reports honestly if it does not.

## Data

Two independent datasets, evaluated and reported separately (not
pooled) — different runs, different scale, a mini-replication check on
whether any winning rule agrees across both:

| Dataset | Snapshot file | Observations | Triples | Unique subject strings | Gold split source |
|---|---|---|---|---|---|
| **A (product657)** | `outputs/dec003_product_probkb_v2/train_kb/pkb_snapshot_iteration_4.csv` | `outputs/dec003_product_probkb_v2/train_kb/observations_iteration_{1-4}.csv` | 657 | 69 | `data/product_split.csv` (35 train products), gold reconstructed via `scripts/dec003_product_probkb_run.normalize_gold` on `products[idx][3]` (gold_unstructured), imported not re-derived |
| **B (product200)** | `outputs/dec006_scaleup_probkb/train_kb/pkb_snapshot_iteration_4.csv` | `outputs/dec006_scaleup_probkb/train_kb/observations_iteration_{1-4}.csv` | 2241 (475 above tau=0.88 under the published rule) | 183 | `data/product_split_200.csv` (140 train products), gold reconstructed via `scripts/dec006_scaleup_probkb_run.normalize_gold` on the same tuple index, imported not re-derived |

Both snapshots already carry a `gold_label` column (candidate-level,
1=matches a gold key) and per-triple JSON lists
(`observation_confidences`, `source_ids`, `source_types`, `provenance`)
aligned by index — these lists are the only per-observation data used;
`src/pkb_replay.py` is not needed since no KB state reconstruction is
required (the snapshot already IS the accepted-candidate state; only
its scoring is being recomputed). Functional-predicate status
(`functional_predicate` column) and structural competitor counts
(`competitor_count` column) are reused as-is from both snapshots since
both are properties of `configs/functional_predicates_product_domain.json`
and the fixed candidate pool, not of the scoring rule — recomputing
them per rule would be redundant and risks introducing a discrepancy
against the already-validated snapshot generation code.

**Recall denominator:** precision/recall/F1 use the FULL train-split
gold key set (`prf()`-style TP/FP/FN, matching `scripts/dec003_product_
probkb_run.py` and `scripts/dec006_scaleup_probkb_run.py`'s own
convention), not just the rows with `gold_label==1` inside the
snapshot. This means gold triples the extractor never even proposed as
a candidate count as false negatives for every rule equally (all five
rules share one fixed candidate pool per dataset) — recall differences
across rules come only from which already-extracted candidates cross
the threshold.

## Rules — precise definitions (flagging two ambiguities in the task brief for sign-off)

All five rules consume the same per-triple `observation_confidences`
(+ aligned `source_ids`/`source_types`) list; nothing is re-extracted.

- **R1 Max-merge:** `C(t) = max_i c_i` over all observations, all
  predicates alike. No conflict/functional-predicate handling at all
  (matches the original deterministic `LockedKnowledgeStore` baseline
  referenced in EVID-013's interpretation).
- **R2 Published rule:** unchanged — `conservative_noisy_or` (lambda=0.75)
  then, for functional predicates only, `/(competitor_count+1)`
  (`src/pkb_math.final_confidence`, already computed and stored as
  `conflict_adjusted_final_confidence` in both snapshots — reused
  directly, not recomputed).
- **R3 Source-count:** **ambiguity flag** — the task text says "as R1's
  noisy-or form," but R1 is max-merge, which has no noisy-or form. Read
  as R2's Eq.1+Eq.2 form with the repeat-count exponent replaced by a
  distinct-source count (consistent with the "Why" section's
  repeat-counting critique, and with "only the scoring changes" applying
  one axis at a time). Precise definition: a **distinct source** = a
  unique `(source_type, source_id)` pair in the triple's aligned lists
  (matches the task's own example, "structured row, unstructured
  document" — e.g. `("structured","product_1")` vs.
  `("unstructured","product_1")` count as two distinct sources; two
  `("unstructured","product_1")` entries from different iterations count
  as one). Verified empirically: 159/657 rows in dataset A have a
  repeated `(source_type, source_id)` pair, so this dedup is not a
  no-op. When a source repeats, its representative confidence is the
  **max** confidence among its repeats (a specific, pre-registered
  choice — not mean or first). `A_R3(t) = 1 - prod_s(1 - 0.75 *
  c_s_max)` over distinct sources `s`, then `/(competitor_count+1)` for
  functional predicates only (same functional-predicate gating as R2),
  else `A_R3(t)` unchanged.
- **R4 Evidence-share:** uses R2's original (repeat-counted, not
  source-deduped) `A(t)`. Formula taken **literally** from the task
  text: `C(t) = A(t) * A(t) / sum_j A(t_j) = A(t)^2 / sum_j A(t_j)`,
  where the sum is over every candidate object `j` in the same
  normalized `(subject, predicate)` slot (including `t` itself; a
  slot with no competitor reduces to `C(t)=A(t)`, i.e. no ceiling for
  an uncontested candidate — the property this rule is designed to
  have). **Ambiguity flag:** applied only to functional predicates, by
  analogy with R2/R3's scope (Eq. 2's divisor is explicitly documented
  as functional-predicate-only, and the "share of slot support" concept
  is meaningless for `has_color`, where multiple simultaneous true
  values are legitimate, not a conflict). Non-functional predicates get
  plain `A(t)`, same as R2.
- **R5 = R3 + R4 combined:** same evidence-share formula as R4, but
  built from R3's distinct-source `A_R3(t)` (numerator and every
  `A_R3(t_j)` in the denominator), functional predicates only.

## Validation/test split

By **unique subject string**, per dataset, independently:
`sorted(unique subjects)`, shuffled with `random.Random(42).shuffle`,
first half -> validation, second half -> test (dataset A: 34/35;
dataset B: 91/92). All triples sharing a subject stay in the same
split. **Caveat, stated up front rather than discovered later:** per
EVID-029's own finding, a large fraction of "subjects" in both
snapshots are not real product names but hallucinated fragments (e.g.
`"It is a laptop device"`, `"The display measures 15.6 inches"`) —
dataset A has 69 unique subject strings against only 35 actual train
products. Splitting by exact subject string is the most granular
leakage-safe unit the stored data supports; it is not a guarantee of
true product-level independence, and this limitation will be restated
next to any result.

## Threshold-selection procedure

Per rule, per dataset: grid search `tau` in `{0.00, 0.01, ..., 1.00}`
(101 values) on the **validation** split only, selecting the `tau`
maximizing F1; ties broken toward the **larger** `tau` (deterministic,
matches this project's existing bias toward a conservative/high fixed
threshold). That single `tau` is then applied to the **test** split
exactly once. No re-selection, no peeking at test to adjust `tau`.

## Metrics (test split, reported once per rule per dataset)

- Precision, recall, F1 at the selected `tau` (recall denominator as
  defined above).
- ECE (10 equal-width bins, same convention as
  `scripts/dec003_real_data_calibration.py`) and Brier score, using each
  rule's own score as the "confidence."
- Number of admitted (>= tau) triples.
- Number of **contested single-valued slots with any candidate
  admitted**: `(subject_norm, predicate)` pairs where the predicate is
  functional and the slot has >=2 distinct objects among its
  candidates, restricted to test-split subjects, counted if any
  candidate in that slot scores >= the rule's own test threshold.
  Reported per rule; R2 is expected near zero by construction but will
  be measured, not asserted.
- 95% bootstrap CI (10,000 resamples) for F1(rule) − F1(R2) on the test
  split: resample **subjects** (not triples) with replacement, include
  all triples of each resampled subject (with duplicates when a subject
  is drawn more than once), recompute F1 for both rules at their
  already-fixed (not re-selected) thresholds, take the difference,
  report the 2.5th/97.5th percentiles. Done for R1, R3, R4, R5 vs. R2,
  independently for dataset A and B (8 CIs total).

## What counts as a null

If, for a given dataset, no rule among R3/R4/R5 has a 95% bootstrap CI
for F1 − F1(R2) that excludes zero, that is a **null result** and will
be reported as such — no re-running, no threshold or split
re-selection to chase significance (README ground rule 5). Disagreement
between dataset A and B's winning rule (if any) will also be reported
plainly rather than resolved by picking whichever is more favorable.

## Deliverables (all under `outputs/dec026_aggregation_rules/`)

- `{dataset}_per_triple_scores.csv` — one row per triple per rule (raw
  scores, admitted flag at that rule's test-selected tau), `dataset` in
  `{product657, product200}`.
- `{dataset}_val_test_split.json` — the exact subject-to-split
  assignment (for reproducibility of the seed-42 shuffle).
- `{dataset}_threshold_selection.csv` — the full validation-F1 grid per
  rule (not just the argmax), so the selection is auditable.
- `{dataset}_metrics_summary.json` — precision/recall/F1/ECE/
  Brier/admitted-count/contested-slot-count per rule.
- `{dataset}_bootstrap_ci.json` — the 10,000-resample F1-difference
  distributions' summary stats and percentiles per rule.
- New EVID entry (Evidence log.md) with the full results table across
  both datasets, and this Decision log status row updated with the
  outcome.
- A short written statement of whether R3, R4, or R5 beats R2 on either
  or both datasets, whether the result is a null, and exactly what may
  be claimed from it in the manuscript.

## Cost / time estimate

Zero — pure pandas/Python replay over already-saved CSVs, no API calls,
no GPU. Estimated wall-clock: a few minutes.

## Status

DEC-026: RUN, COMPLETE, first pass (2026-09-23). Full results in
  EVID-041 (first version). Mixed outcome, not a clean win or a clean
  null: R2's rival ceiling confirmed empirically real (0 contested-slot
  admissions vs. R1's 6/40); R4's evidence-share fix, exactly as
  specified, is a byte-identical null against R2 on both datasets (max
  contested-slot score never approaches threshold); R3 (source-count /
  repeat-counting fix) delivers a small but statistically robust F1
  improvement over R2 on both datasets (CI excludes 0), via a precision
  gain at fixed recall; R5 is numerically identical to R3 (its R4
  component contributes nothing). Raw outputs:
  `outputs/dec026_aggregation_rules/`.

## Addendum — four approved follow-ups (2026-09-23, all zero-cost replay, no re-running of the original comparison)

Approved by the user alongside DEC-026's first-pass results, before
Section 4 resumed. All four executed together in the same script
(`scripts/dec026_aggregation_rules_replay.py`, updated in place, not
forked) and reported in EVID-041's revised version.

1. **Secondary analysis at the pipeline's fixed operating threshold**
   (tau=0.88, not F1-selected): rerun for every rule (now including R6,
   below) on the same test split, same gold sets, reporting precision,
   recall, F1, admitted count, and contested-slot admissions **alongside**
   (not replacing) the F1-selected numbers. No new threshold selection,
   no new bootstrap for this secondary view unless it changes a
   conclusion.
2. **R6 (exploratory, post-hoc — added after seeing R4's null, not part
   of the original pre-registration, labeled as such everywhere it is
   reported):** unsquared evidence share, `C(t) = A(t) / sum_j A(t_j)`,
   same scope (functional predicates only) and same input (R2's
   original support) as R4. Goes through the identical pipeline: val-only
   threshold grid search, test-split metrics at both the F1-selected and
   fixed 0.88 thresholds, and a bootstrap F1-difference CI against R2 on
   the same 10,000 subject resamples used for R1/R3/R4/R5. **What counts
   as a null for R6 specifically:** a 95% CI that does not exclude zero,
   exactly the same standard applied to R1/R3/R4/R5 — no different bar
   because it was added after seeing R4's result.
3. **Recall-denominator statement:** EVID-041 must say explicitly which
   gold set defines the recall denominator (train-split `gold_unstructured`
   facts, imported from the original DEC-003/DEC-006 run scripts' own
   `normalize_gold()` — the same set those scripts' own `train_gold_keys`
   and the snapshot's own `gold_label` column already use), and state
   plainly whether that makes DEC-026's recall comparable to recall
   figures reported elsewhere in the project (EVID-013's held-out
   val/test recall, EVID-014's whole-KB recall, EVID-030/DEC-019's
   closed-loop recall) — verified during this addendum: EVID-014's
   657-snapshot whole-KB recall is a directly comparable, same-gold-set,
   same-snapshot number; EVID-013's held-out recall is not (different,
   non-train products, single pass, no threshold admission); EVID-030's
   closed-loop recall is not (uses `gold_structured`, a larger/stricter
   full-structured-facts set, not `gold_unstructured`).
4. **Commit `outputs/dec026_aggregation_rules/`:** add a targeted
   `.gitignore` exception (`outputs/*` plus `!outputs/dec026_aggregation_rules/`,
   replacing the previous blanket `outputs/` line) and commit the
   directory's contents (per-triple scores, split assignments, threshold
   grids, bootstrap distributions) — an explicit, one-time exception to
   this project's standing convention of never committing `outputs/`
   (a gap AUDIT.md already flags project-wide), made because this
   specific experiment is now load-bearing for the paper's contribution.
   No other `outputs/` directory is affected by this change.

**Also required in EVID-041's revised write-up:** state as a headline
comparison that R1 (max-merge, no conflict handling) beats R2 (the
published rule) on **both** precision and recall on both datasets,
with the caveat that both rules' thresholds were independently
F1-selected on validation, and that this direction (unconstrained
aggregation numerically outperforming the conflict-adjusted published
rule) matches the same direction already found in the project's N=50
closed-loop ablation (`without_prob_kb` >= `full`, AUDIT.md A1,
EVID-039) — not a new, isolated finding, a second real-data
confirmation of an existing tension already on record.

## Addendum 2 — Bootstrap CIs at the fixed tau=0.88 operating point, plus a structural reading of R6 (2026-09-23)

Two further approved items, both zero-cost, same replay, no new
splits/thresholds:

1. **Bootstrap CIs at the pipeline's fixed operating threshold
   (tau=0.88), not just the F1-selected one** -- precision, recall and
   F1 differences reported separately (not just F1), for R1 vs. R2 and
   R3 vs. R2 (10,000 subject resamples, same procedure as the
   F1-selected comparison). Rationale stated by the user: the
   fixed-threshold comparison is what goes in the paper, so it needs
   its own CIs. **This changed a conclusion, not just added detail**:
   at tau=0.88, R1's F1 advantage over R2 no longer excludes zero on
   either dataset (it was a clean, significant win at each rule's own
   F1-selected threshold) -- R1 trades a large, significant precision
   loss for a large, significant recall gain, and the two roughly
   cancel in F1 at the fixed threshold. R3's precision gain over R2
   *does* hold at tau=0.88 on both datasets (CI excludes zero), with
   recall unchanged (CI exactly [0,0] -- R3 and R2 admit the identical
   true-positive/false-negative split at this threshold, the dedup only
   removes false positives here). Full numbers: EVID-041.
2. **Add to EVID-041's conclusion:** R6's failure demonstrates the
   rival ceiling is a structural property of share-based aggregation,
   not an artifact of this dataset's scale -- any share-based
   normalizer must reduce to `A(t)` when a slot is uncontested (matching
   R2's own behavior there); the squared form (R4/R5) has this
   property, the unsquared form (R6) does not, and that is *why* R6
   fails, independent of which snapshot it's tested on. A result about
   the rule's mathematical form, not just about this project's data.

## Status (addendum 2)

DEC-026: RUN, COMPLETE, both addenda incorporated (2026-09-23). See
  EVID-041 (revised) for the fixed-tau bootstrap CIs and the structural
  reading of R6. Section 4 of the manuscript may now resume, using
  exactly the claims specified alongside this approval: (a) the
  aggregation formula and lambda=0.75 are DySECT's, cited not claimed;
  (b) this paper's contribution is the formal analysis (boundedness,
  monotonicity, corroboration requirement, saturation, rival ceiling)
  plus the empirical demonstration that the ceiling blocks every
  contested slot at both thresholds tested; (c) the corrected rule is
  R3 (distinct-source counting), reported with its measured gain at
  tau=0.88 and CI -- R4/R5/R6 reported as tested and null/negative, not
  as contributions.

# DEC-027 — Leakage-Free Fine-Tuning Evaluation (executes the previously-scoped DEC-024 design)

## Why is this required?

AUDIT.md A2 / Results Summary Claim 2 state a standing, disclosed
limitation: EVID-040's headline fine-tuning result (epochs=5,
p=0.0028 vs. base) used the identical 8-product test split for both
hyperparameter selection (DEC-022 Stages 1-2) and confirmation (Stage
3) -- no independent validation split separated "which configuration
to pick" from "how well does the picked configuration generalize."
DEC-024 pre-registered the fix on 2026-09-21 but was scoped and
deferred, not run, by explicit user decision at the time. This DEC
executes that design without modification to its statistical core,
adding the specific reporting requirements from the current task brief
(a pre-registered minimum effect of interest, a paired bootstrap over
test products as the primary test, an explicit leakage-guard unit
test, and a stated provenance-filter choice). This result replaces
Section 7's current exploratory fine-tuning subsection as the manuscript's headline
fine-tuning evidence -- the current numbers are not discarded, but are
demoted to "an earlier, tuning-leakage-affected exploration," matching
this project's existing convention for superseded results (e.g. how
EVID-034's epochs=3 result was demoted, not deleted, when EVID-040
superseded it).

## Data and split

`data/product_split_200.csv` (140 train / 20 validation / 40 test,
seed 7/42, already used by DEC-006/018/019/026). Training data:
the existing 90-example **unfiltered** synthetic set derived from this
same 200-product run's train-KB snapshot (already committed per the
2026-09-22 commit "Commit the 90-example unfiltered synthetic training
set for DEC-025"), identical to what EVID-037/038/040's grid used.
**Design choice, flagged for review:** unfiltered, not
provenance-filtered, is used deliberately so this experiment isolates
only the leakage-selection-procedure fix -- switching to the
provenance-filtered 73-example set at the same time would confound two
independent variables (selection procedure and training-data
composition) in one result. A provenance-filtered rerun of this same
leakage-free design is identified as natural follow-up work, not done
here. If the user prefers the filtered set as primary instead, say so
before approval; this is a reversible choice at this stage, not after
training starts.

**Test-set gold triple count, stated before running so recall is
interpretable afterwards (per user instruction, 2026-09-23):** the 40
test-split products carry **280 `gold_unstructured` triples total, 7
per product exactly** (every product's generated text visibly mentions
7 of 13 predicates by design; verified directly by generating all 200
products at seed 42 and summing `len(gold_unstructured)` over the 40
test-split indices from `data/product_split_200.csv` -- not assumed
uniform, checked: min and max per product are both 7). This is the
recall denominator `scripts/dec006_evaluate_adapter.py`'s own
evaluator uses (`Triple` objects built from `gold_unstructured`,
verified directly against that script). A test-split recall of, e.g.,
0.10 therefore means 28 of these 280 triples were recovered, not a
fraction of some other, larger or smaller gold set -- stated
explicitly so this DEC's recall numbers are not read against the
wrong denominator the way DEC-030/EVID-043 found had already happened
once in this project for the provenance filter's `gold_structured`
vs. `gold_unstructured` distinction.

**Leakage guard, built and demonstrated before running (per user
instruction, 2026-09-23):** `src/dec027_leakage_guard.py` (reusing
`scripts/dec006_evaluate_adapter.py`'s own `load_trained_subjects()`,
not reimplemented) and `tests/test_dec027_leakage_guard.py`. Both
committed tests pass: (1) the actual committed training file
(`product_domain_synth_train_90unfiltered.jsonl`) contains no
validation/test product -- clean, verified, not assumed; (2) a planted
violation (one held-out product's own training example injected into
a `tmp_path` scratch copy) is correctly caught. **Demonstrated live, not
only via the pytest suite**: a scratch file
(`outputs/_scratch_dec027_leakage_demo.jsonl`, injecting product
"Auralex Headphones Air 147", a real validation/test product) was
built, run through `assert_no_leakage()` uncaught, and produced:

```
AssertionError: DEC-027 leakage guard FAILED: 1 validation/test product(s)
found as a training-example subject in
'outputs/_scratch_dec027_leakage_demo.jsonl': ['Auralex Headphones Air 147']
```

The scratch file was then deleted and the real training file
re-verified clean (`assert_no_leakage` on the committed file: no
exception, "Clean: no leakage in the real committed training file.").
The training/evaluation runbook aborts on this same assertion before
any GPU time is spent, per the original pre-registration.

## Design

1. **Validation-only grid search (seed 42 only, matching DEC-022
   Stages 1-2's own single-seed-exploration precedent), evaluated on
   the 20-product VALIDATION split, never the test split:**
   - Epochs in {2,3,5,8}, LoRA fixed at rank 16/alpha 32/lr
     2e-4 (the existing default).
   - At the winning epoch count: rank in {8,32} (alpha=2xrank)
     and lr in {1e-4, 3e-4}, same
     validation-only evaluation (reuses DEC-022's exact grid values for
     comparability).
   - **Selection rule, pre-registered exactly as specified:** best
     validation F1; ties within 0.01 go to the simpler (lower
     rank) or shorter (fewer epochs) configuration. Every validation
     score from the grid is saved and reported, not only the winner's.
2. **Fresh base-model reference**, evaluated once on the untouched
   40-product test split (the existing F1=0.1373 number is from a
   different, 8-product test set derived from the 50-product superset
   and does not transfer here, per AUDIT.md A6 and this task's own
   instruction).
3. **Confirmatory run:** the single winning configuration, trained at
   seeds 42-46 (reusing the seed-42 adapter already trained during
   grid search rather than retraining it, matching DEC-022 Stage
   1-to-3's own reuse precedent), evaluated exactly once per seed on
   the 40-product test split.
4. **Leakage guard, as a unit test, not a manual check:** a new
   `tests/test_dec027_leakage_guard.py` asserts, for the actual
   training JSONL file used, that no product name from the validation
   or test index sets (loaded from `data/product_split_200.csv`)
   appears as the subject of any training example, mirroring
   `scripts/dec006_evaluate_adapter.py`'s existing cross-split guard
   but as an executable, CI-style assertion rather than a runtime
   print statement. The training/evaluation scripts abort (non-zero
   exit) if this test fails, before any GPU time is spent.

## Statistics

- **Primary test:** paired bootstrap over the 40 test products. For
  each product, compute its F1 difference (fine-tuned - base),
  averaged across the 5 confirmatory seeds; resample products with
  replacement, 10,000 times (matching DEC-026's established
  cluster-bootstrap convention); report the 95% percentile CI of
  the mean per-product difference. **Positive only if the CI excludes
  0 AND the point estimate is >= 0.03** (the pre-registered
  minimum effect of interest, chosen because it is an order of
  magnitude above noise on this metric scale and below EVID-040's
  originally-reported +0.064, so a real but smaller-than-previously-reported
  effect would still register as positive rather than being
  swallowed by an overly strict threshold).
- **Secondary, descriptive only:** one-sample t-test and Wilcoxon
  signed-rank of the 5 seeds' test-split F1 against the fresh base
  F1, matching EVID-034/040's method for comparability; note
  Wilcoxon's p=0.0625 floor at n=5 explicitly if reached
  (the manuscript's Experimental Setup Section 6 statistical-protocol subsection's established convention).
- **Variance reported separately, not conflated:** (a) training-seed
  variance -- sample SD of the 5 seeds' whole-test-set F1; (b)
  test-product variance -- SD of the per-product F1 differences
  used in the primary bootstrap. These answer different questions (how
  much does the outcome depend on the training seed, vs. how much does
  it depend on which products are in the test set) and are not
  combined into one number.

## What counts as a null

The primary bootstrap CI includes 0, or excludes 0 but the point
estimate is <0.03. **This will be reported as a null exactly as
found, including if it reverses the direction of EVID-040's original
(leakage-affected) result -- no re-running, no grid re-expansion, no
switching to the provenance-filtered data post-hoc to chase
significance.** A null here is itself the answer to AUDIT.md A2, not a
failed experiment: it would mean the previously-reported effect was
plausibly an artifact of tuning on the evaluation data, which is
exactly the failure mode DEC-024/DEC-027 exists to detect. **If this
result is a null, that null supersedes EVID-040's exploratory positive
result as the manuscript's headline fine-tuning claim -- the manuscript
must state this supersession explicitly wherever fine-tuning is
discussed, not report the two results side by side as if equally
weighted evidence.** (User instruction, 2026-09-23.)

## Cost / time estimate (awaiting approval)

Identical to DEC-024's own estimate, since the design is unchanged:
rented RunPod GPU (RTX 4090, with 3090 fallback per this project's
established pattern); 8 exploratory grid trainings (4 epoch x
1 seed, 4 LoRA x 1 seed, reusing the epoch winner as one LoRA
grid point) + 4 new confirmatory trainings (seeds 43-46, seed 42
reused from the grid) = 12 fine-tuning runs, each in the
~100-500s range observed in DEC-022; inference passes (8 validation
evaluations, 5 test evaluations, 1 base-model evaluation) add a few
minutes. **Estimated total: 35-45 minutes of GPU wall-clock**, matching
the user's own ~45-minute estimate; at typical RunPod RTX 4090
community rates (0.30-0.50/hour), **well under $1**, but this is a
time estimate, not a confirmed price -- confirm the actual pod rate
before starting, per standing project convention.

## Status

DEC-027: APPROVED (2026-09-23), unfiltered training set confirmed as
  primary, supersession clause added above. Queued third (after
  DEC-028, DEC-030), before DEC-029, per user-specified run order.
  **EXECUTED (2026-09-23), COMPLETE -- see EVID-044.** Primary
  pre-registered result: NULL (paired bootstrap point estimate -0.0214,
  95% CI [-0.0417, -0.0034], excludes zero on the negative side).
  Per the supersession clause above, this null supersedes EVID-040's
  exploratory positive result as the manuscript's headline fine-tuning
  claim.

---

# DEC-028 — Provenance Filter Under a Noisy Structured Source (Claim #5 circularity fix)

## Why is this required?

AUDIT.md A3 / Results Summary Claim 5 flag a real circularity: in the
synthetic product domain, structured records and gold labels are
generated by the same function call
(`src/datasets/product_generator.py`, the manuscript's Experimental Setup Section 6 datasets subsection),
so "corroborated by a structured source" and "matches gold" are close
to the same statement by construction. EVID-029's 93.5% to 100%
precision-lift result is real but was measured only under this
noise-free structured source, and cannot by itself show the filter
adds value when the structured source is imperfect, which is the
realistic deployment condition this filter is meant for.

## Design, precisely, to avoid recreating the same circularity in a different form

**The corruption is applied to individual observation rows, before a
full replay through the real PKB acceptance and aggregation code
(`src/pkb_replay.py`, `src/probkb_v2_adapter.py`), not as a post-hoc
relabeling of the already-built snapshot.** This distinction is the
whole point of the design, stated explicitly because a naive
implementation could reintroduce circularity in a new form:

1. Start from the already-saved `observations_iteration_{1,2,3,4}.csv`
   files of the 200-product run (`outputs/dec006_scaleup_probkb/train_kb/`,
   EVID-027/029's source data) -- the exact same observation rows used
   throughout DEC-006/018/019/026, zero new extraction.
2. For a corruption rate r in {0%, 5%, 10%, 20%}: independently,
   for each observation row whose `source_type == "structured"`, corrupt
   it with probability r by replacing its `object` value with a
   **different** value drawn uniformly from that predicate's own fixed
   value pool as literally enumerated in
   `src/datasets/product_generator.py` (e.g. `has_color` draws from
   `colors = ["black","silver","blue","white","green"]` excluding the
   true value; numeric predicates draw from their own fixed pools --
   `price_usd` from `[199,249,...,1299]`, etc.) -- a "plausible wrong
   value" defined precisely by the generator's own domain, not
   invented ad hoc. Unstructured observation rows are never touched.
3. **Replay** the (partially corrupted) full observation set through a
   fresh `CandidateBufferAdapter` via `src/pkb_replay.py`'s existing
   `replay_iterations`, exactly as DEC-019/DEC-026 already do,
   producing a new snapshot in which the corrupted structured values
   have gone through the real Noisy-OR aggregation and tau=0.88
   admission logic -- a triple whose only structured observation was
   corrupted genuinely loses structured corroboration in this replay
   (its accepted entry, if any, now reflects only unstructured
   evidence); the corrupted (wrong) object value, if strong enough,
   can itself become a newly-accepted candidate with structured
   corroboration.
4. **Gold labels are never touched and never re-derived from the
   corrupted data**: they remain exactly `gold_unstructured` (or,
   where relevant, `gold_structured`) from the true, uncorrupted
   generator output for these 140 train products, imported the same
   way DEC-026 already does
   (`scripts/dec006_scaleup_probkb_run.py`'s own `normalize_gold`).
   This is what prevents the corruption from recreating circularity:
   the ground truth used to score the filter is structurally
   independent of which observations were corrupted, at every
   corruption rate.
5. Apply `src/provenance_filter.py`'s existing, unmodified
   `has_structured_corroboration` to the replayed snapshot at each
   rate, and score against true gold.

## Addendum (2026-09-23, before any run): the rival ceiling confounds the design as originally written

Flagged by the user before approval, and correct: when a structured
value is corrupted, the corrupted (wrong) object and the true object
now compete in the same functionally single-valued slot (the manuscript's
rival-ceiling proposition's m(t)>=1 case, src/pkb_math.py). Both candidates'
scores are then capped below 1/(m(t)+1) <= 0.5, so **neither** can
reach tau=0.88 regardless of which one is actually correct -- the
originally-specified design would have silently computed filter
precision only over the minority of triples whose corruption happened
not to create real competition (e.g.\ the true value already had
enough independent unstructured support to remain admitted alongside a
weak corrupted rival, or the corrupted slot is on the one
non-functional predicate, `has_color`). This would understate how much
work the filter is actually doing, for a reason having nothing to do
with provenance. Three changes, made before any run:

**(a) Ceiling visibility, reported per corruption rate, per arm
(defined in (b) below):** the number of admitted triples; the number
of contested single-valued-predicate slots the corruption created
(slots with m(t)>=1 that were uncontested, m(t)=0, before
corruption); and how many of those newly-contested slots have any
candidate admitted at all -- the same "contested slots with admission"
definition DEC-026 already established, reused here for
consistency rather than redefined. This makes ceiling-driven exclusion
visible in the reported numbers rather than silently folded into a
single precision figure.

**(b) Two arms, run in full and reported side by side, not just one:**
- **Conflict-adjusted arm (as originally specified):** C(t) =
  A(t)/(m(t)+1) for functional predicates, i.e. the published rule,
  unchanged.
- **Support-only arm (new):** C(t) = A(t) for every predicate,
  functional or not -- the conflict-adjustment divisor is disabled
  entirely, so admission depends only on accumulated Noisy-OR support,
  never on how many rivals a slot has. This arm cannot be blocked by
  the ceiling by construction (no division by m(t)+1 occurs), so it
  isolates whether the provenance filter itself still separates
  correct from incorrect triples once the ceiling can no longer
  suppress admission on either side of a contested slot. Both arms use
  the identical corrupted observation set and the identical five
  corruption seeds per rate -- only the scoring rule differs, matching
  this project's established "only the scoring changes" convention
  from DEC-026.

**(c) Sanity check, required before proceeding to any non-zero
corruption rate:** at r=0% (no corruption), the conflict-adjusted
arm's replay must reproduce EVID-029's published numbers exactly --
475 above-threshold triples, 444 passing the filter, 31 removed. **If
it does not reproduce these three numbers exactly, stop immediately,
report the discrepancy (which number(s) differ and by how much) to the
user, and do not proceed to the 5/10/20% corruption rates or the
support-only arm.** This is a correctness gate on the replay mechanism
itself, not a result to interpret -- a mismatch here means the
replay does not faithfully reconstruct EVID-029's known-correct state,
and every corrupted-rate result downstream would be untrustworthy
until fixed.

## Metrics, per corruption rate, per arm

- **Admitted triples** (total count above the arm's threshold) --
  new, per the addendum.
- **Contested single-valued-predicate slots created by corruption**
  (m(t)>=1 where m(t)=0 pre-corruption) -- new, per the addendum.
- **Of those, how many have any candidate admitted** -- new, per the
  addendum; expected near 0 for the conflict-adjusted arm at every
  rate (the ceiling holds regardless of corruption rate -- it is a
  property of the formula, not of how the contest arose) and expected
  to be visibly nonzero for the support-only arm, which is exactly
  the contrast this addendum exists to make visible.
- Precision of triples that pass the filter (have >= 1 structured
  observation surviving in the replayed snapshot), against true gold.
- Precision of triples the filter removes (structured-only-absent),
  against true gold.
- Count of true-correct triples wrongly removed (their only structured
  corroboration was corrupted away, and no unstructured corroboration
  alone crossed the arm's threshold).
- Count of incorrect triples that wrongly pass (a corrupted, wrong
  object value received strong-enough support under the arm's own
  scoring rule to be accepted as a candidate with structured
  corroboration).
- Five corruption seeds per non-zero rate (independent draws of which
  rows are corrupted and which wrong value each receives); 0% needs
  no seed variation since nothing is randomized. Report mean, sample
  SD, and 95% bootstrap CI (10,000 resamples over the 140 train
  products, matching DEC-026's convention) at each rate, for both arms.

## Pre-registered expectation and null criterion

**Applies separately within each arm** (the filter is applied to
whichever set of candidates that arm's own threshold admits, so
"passing-set" and "removed-set" below mean the conflict-adjusted arm's
admitted set for the conflict-adjusted arm's numbers, and the
support-only arm's own admitted set for its numbers -- the two arms
are not pooled).

**Expected shape:** passing-set precision should degrade gradually as
r increases (some corrupted-but-structurally-corroborated triples
will pass), but should remain measurably above removed-set precision
at every tested rate up to 20% -- the filter should still be doing
net-positive work, just with a smaller margin than the noise-free
100% vs. 0% result.
**What counts as the filter failing, pre-registered exactly:** at a
given rate, if the 95% bootstrap CI for (passing-set precision -
removed-set precision) includes 0 or is negative, the filter's
structured-corroboration criterion no longer distinguishes correct
from incorrect triples at that noise level, and this is reported as
such -- not reframed, not excused by "real structured sources are
cleaner than this."

## Cost / time estimate

Zero -- pure replay of already-saved observation rows through existing,
unmodified PKB code, no API calls, no GPU. Estimated wall-clock: a few
minutes for 4 rates x up to 5 seeds x 2 arms = 34 replay runs (rate 0%
needs only 1 per arm, since nothing is randomized there).

## Status

DEC-028: RUN, COMPLETE (2026-09-23). Sanity check passed exactly
  (475/444/31, matching EVID-029). Ceiling confound confirmed exactly
  as predicted: 0 corruption-created contested slots ever admitted
  under the conflict-adjusted (published) rule at any rate; the
  support-only arm resolves 81-88% of the same contested slots instead.
  Filter precision robust at every tested rate in both arms -- all 8
  rate x arm bootstrap CIs for (passing precision - removed precision)
  exclude zero, including the hardest tested condition (support-only,
  20% corruption: +0.705, CI [0.488, 0.836]). Full results: EVID-042.
  A bug in the first draft of the bootstrap (resampling restricted to
  the 140 real products, silently dropping most removed-set triples,
  which are disproportionately fragment-subject hallucinations) was
  caught and fixed before this entry -- see EVID-042's Limitations.
  Raw outputs: `outputs/dec028_provenance_corruption/`.

---

# DEC-029 — Higher-Powered Module Ablation (extends DEC-023/EVID-039)

## Why is this required?

AUDIT.md's correction to DEC-023 (already stated in Results Summary
Claim 3 and restated in the manuscript's Discussion Section 8 ablations
subsection) is precise about what a 5-seed null does and does not show:
it excludes only large effects (~ 0.29-0.30 absolute F1,
Cohen's d ~ 1.68 for 80% power at n=5), not
small-to-moderate ones. This DEC extends the seed count to narrow that
detectable-effect floor, without changing the design in any other way.

**Expected minimum detectable effect, pre-registered before running
(user-supplied, using the same observed SD ~ 0.17 AUDIT.md's own
calculation is based on, paired t-test, alpha=0.05, 80% power):**

| n (seeds) | Approximate MDE (absolute F1) |
|---|---:|
| 5 (existing) | ~0.286 |
| 10 | ~0.169 |
| 15 | ~0.132 |
| 20 | ~0.112 |
| 30 | ~0.090 |

These are projections from a fixed assumed SD, stated up front rather
than only after the run; the actually-achieved MDE (computed from this
run's own observed SD, which may differ from 0.17) is reported
alongside every null result per the Statistics section below, not
substituted silently for this pre-registered projection.

## Design

Extends `scripts/dec023_ablation_n50.py`'s existing design (same
N=50 product superset, same 3 of its 5 configs specified by this
task -- `full`, `without_feedback`, `without_prob_kb`; `structured_only`
and `unstructured_only` are out of scope here, matching the task
brief's own scoping) with new seeds beyond the existing 42-46, saved to
a new `outputs/dec029_ablation_extended/` directory so EVID-039's
original 5-seed result is never overwritten (README ground rule 2).
Combined analysis (existing 5 seeds + new seeds) is computed as a
separate step, not by modifying EVID-039's own saved files.

**Seed count: 30 total (25 new: seeds 47-71), approved and confirmed
below the user's own $0.30 threshold.** The user asked for the cost of
30 as well as 20 and pre-authorized 30 if it came in under $0.30; the
cost estimate below confirms $0.246, so 30 total seeds is the run
target, not 20.

**Zero-cost fallback if the budget does not allow more seeds:** a
paired bootstrap over the 10 held-out test products at the existing 5
seeds (42-46) only -- resample products with replacement, 10,000
times, using each resampled product's mean-across-5-seeds F1
difference from `full`, reporting the 95% CI. This quantifies
test-set-level uncertainty (which products happen to be in the test
split) without any new extraction, complementary to but not a
replacement for the seed-level power increase the main design provides
(it answers "how much does the test-set composition affect the
estimate," not "how much does training-seed variance affect it").

## Statistics

- Paired t-test and Wilcoxon signed-rank of `without_feedback` and
  `without_prob_kb` against `full`, at the full achieved seed count,
  matching EVID-020/039's existing method for direct comparability.
- 95% CI for every comparison (paired bootstrap over seeds, same
  percentile-CI convention used throughout this project).
- **Minimum detectable effect, computed and reported, not assumed:**
  using the same method as AUDIT.md's n=5 calculation (paired
  t-test, alpha=0.05, 80% power, using this run's own observed
  SD, not EVID-039's), reported explicitly alongside any null result.
  Approximate expectation from EVID-039's existing SDs (~ 0.19-0.20,
  sample-SD-corrected): at n=15, Cohen's d ~ 0.77 gives an
  approximate MDE of ~ 0.15 F1; at n=20, d ~ 0.65
  gives ~ 0.13 F1 -- approximate, pre-run projections only,
  to be replaced with the actually-achieved figure after running, per
  this DEC's own reporting requirement.
- **No null from this DEC is described as "properly powered" without
  stating the achieved minimum detectable effect next to it** -- the
  exact wording AUDIT.md already requires elsewhere in this project,
  applied here from the start rather than corrected after the fact.

## Cost estimate

EVID-039's own 25-combination (5 configs x 5 seeds) 5-seed run
cost $0.0819 total, ~$0.003276/combination. This DEC uses only 3 of
those 5 configs.

- **20 total seeds (15 new x 3 configs = 45 new combinations): ~$0.147.**
- **30 total seeds (25 new x 3 configs = 75 new combinations): ~$0.246.**

Both well under the $2 approval threshold; 30 is also under the user's
specific $0.30 threshold for this decision, so **30 total seeds (25
new) is confirmed as the run target**, per the user's own
pre-authorization.

## What counts as a null

p >= 0.05 (or a bootstrap CI including 0) for a comparison, reported
exactly as found at the achieved seed count (30 total), with the
achieved MDE stated alongside it -- no further seed extension to chase
significance beyond the 30 seeds approved here.

## Status

DEC-029: RUN (2026-09-24) -- see EVID-045. Null for both modules at 30 seeds,
  achieved MDE ~0.08 F1; cost $0.24. Originally APPROVED (2026-09-23), 30 total seeds (25 new: 47-71)
  confirmed as the run target at ~$0.246, with the pre-registered MDE
  table above added before running. Queued last (after DEC-028,
  DEC-030, DEC-027), the only DEC in this batch with real API cost.

---

# DEC-030 — Reproducibility Package (professor_feedback.md point 12)

## Why is this required?

professor_feedback.md point 12 asks for reproducibility directly.
AUDIT.md's Phase 0 audit already flagged that `outputs/` is
gitignored project-wide (the same gap DEC-026's own commit exception
was a one-off fix for), that `requirements.txt` bundles fine-tuning
dependencies (torch/transformers/peft/trl/bitsandbytes) into every
install even for users who never touch the GPU path, and that no
single script regenerates the manuscript's own tables from raw data.

## Scope (this is a deliverables list, not a statistical experiment --
## pre-registered here as what "done" means, per ground rule 1's
## spirit even though there is no hypothesis to test)

1. **Commit raw outputs behind every number reported in the
   manuscript.** Extend the existing `outputs/*` / `!outputs/dec026_aggregation_rules/`
   pattern in `.gitignore` (Section 7's own committed precedent) with
   one targeted exception per `outputs/dec0NN_*` directory actually
   cited by an EVID number reachable from the manuscript, EXCLUDING any
   file >50MB (in practice, LoRA adapter weights --
   `*.safetensors`/`*.bin`, already globally ignored) and anything
   under `.env`/secrets (already ignored, unaffected). A
   `scripts/download_adapters.md` (or equivalent) documents where the
   excluded adapter weights can be obtained instead (e.g. re-run the
   relevant fine-tuning script, or a separately-hosted archive if the
   user provides one) rather than silently leaving them unreachable
   with no explanation.
2. **`scripts/reproduce_all.py`**: regenerates every table currently in
   `paper/main.tex`'s Section 7 (and its Table S1-S8 appendix) from the
   committed raw outputs above, and diffs its regenerated values
   against `Results Summary.md`'s own numbers. **Any mismatch is
   reported in the script's own output, not silently corrected** --
   this is a verification tool, not a second source of truth.
3. **Fix the stale README status text** (verified against the current
   `README.md` for what is actually stale before editing, not assumed).
4. **Split `requirements.txt`** into a base file and
   `requirements-finetune.txt` (torch, transformers, peft, trl,
   bitsandbytes), so a CaRB/DocRED/BioRED-only reproduction never needs
   GPU-fine-tuning dependencies installed.
5. **`docs/reproduction.md`**: every pinned model ID used anywhere in
   this project (the manuscript's Experimental Setup Section 6 models subsection's own list, restated
   here for a reader who only wants this one file), the dates each was
   run (from each EVID entry's own commit history, not guessed),
   decoding settings (temperature 0, per-script max-token limits where
   they differ), every seed convention used (42-46 confirmatory, 7 for
   splits, 42 for generation), hardware (RunPod RTX 4090/3090), and a
   data/licensing note (the synthetic generator is this project's own
   code with no external license constraint; DocRED is MIT-licensed
   via the thunlp mirror per Decision log.md's DEC-020 entry; BioRED is
   NCBI public-domain; CaRB's own license, if not already recorded, is
   verified before writing it, not assumed).

## What counts as this DEC not being done

Any of the five items above left incomplete, or
`scripts/reproduce_all.py` reporting a mismatch against `Results
Summary.md` that is not then reported to the user plainly (not
silently patched in either file to make the diff pass).

## Cost / time estimate

Zero API/GPU cost -- engineering and documentation work plus git
operations. Time is implementation effort, not a metered resource;
no approval threshold applies, but this DEC still runs only after the
user's go-ahead alongside the other three, per this task's own
"stopping for approval between each" instruction.

## Status

DEC-030: RUN, COMPLETE (2026-09-23). All five items done: 22
  `.gitignore` exceptions added (632 files, ~76MB committed);
  `scripts/reproduce_all.py` written and run (21 PASS, 2 READ, 0
  MISMATCH, 1 disclosed GAP); README status/limitations rewritten;
  `requirements-finetune.txt` split out; `docs/reproduction.md` added.
  **One genuine finding, reported not silently fixed**: EVID-029's
  93.5%->100% provenance-filter figures use `gold_structured`, not the
  snapshot's own `gold_label` column (`gold_unstructured`) -- the
  latter gives 92.6%->99.1% instead. The published number is correct
  under its own stated method; both are now documented (EVID-043,
  Results Summary.md Claim 5). Also found: 8 `outputs/` directories,
  including 5 adapter `.safetensors` files, were already committed
  before any `outputs/` gitignore rule existed -- left in place, not
  rewritten out of history, documented in `docs/reproduction.md`.

---

# DEC-031 — DocRED at Scale With a Normalised Matching Key (pre-registered 2026-09-24, before any extraction)

## Why is this required?

The manuscript currently *speculates* that exact-string matching caused
DEC-020's DocRED result: on the 15-document pilot, PKB aggregation
lowered F1 from 0.033 (no aggregation) to 0.010, because the same fact
phrased differently in different sentences was rarely pooled into one
candidate. This DEC tests that explanation at scale, and runs R3
(DEC-026's distinct-source rule) outside the synthetic product domain
for the first time. The paper's claim about R3 depends on this.

## Decisions (user-approved, 2026-09-24)

- **Documents:** all **845** DocRED dev documents with at least one
  gold triple supported by 2+ evidence sentences. This is DEC-020's own
  eligibility rule. An earlier estimate said 843 using a slightly
  different count; 845 is the figure from the pilot's rule. It includes
  the 15 pilot documents.
- **Sentences (PRIMARY: all):** one extraction call for **every
  sentence** of those documents: 6,861 calls. The pilot sent only gold
  evidence sentences, which is an oracle: it tells the extractor which
  sentences contain a relation. An **evidence-only arm** (the 3,918
  gold-evidence sentences, a subset of the same extractions, no extra
  calls) is reported solely for comparability with the pilot. The
  manuscript's pilot text now says the pilot used this oracle setting.
- **Extraction:** identical to DEC-020: `meta-llama/llama-3.1-8b-instruct`,
  `prompts/openie_docred_v1.txt`, temperature 0, max_tokens 1024, one
  sentence per call with no document context
  (`scripts/dec031_docred_extract.py`). Crash-safe per-call cache,
  sharded across processes. Network failures are re-requested.
  **Unparsable model output is never re-requested**, for any sentence,
  so no arm or document gets extra attempts (the DEC-029 retry-asymmetry
  lesson, EVID-045).
- **Matching-key arms**, all computed offline from the same extractions
  (`src/dec031_docred.py`):
  - **(a) exact:** the PKB adapter's current key (strip + lowercase).
  - **(b) normalised (PRIMARY for the matching-key hypothesis;
    deployable, no gold resources):** Unicode NFKC, casefold, drop a
    possessive 's, delete periods and apostrophes ("U.S." -> "us"),
    replace every other Unicode punctuation character with a space,
    collapse whitespace, strip, drop one leading "the"/"a"/"an".
  - **(c) gold-alias assisted: ORACLE UPPER BOUND, labelled as such
    everywhere.** A string whose (b) form equals the (b) form of a
    mention of exactly one gold entity in the document is keyed to
    that entity; ambiguous forms fall back to (b). It uses DocRED gold
    annotations and cannot support any claim about what a deployed
    system would achieve.
- **Aggregation rules:** R2 (conservative Noisy-Or over every
  observation) and R3 (the same over distinct source sentences). Both
  use confidence 1.0 per observation, shrinkage 0.5, and admit at
  tau = 0.70, i.e. 2+ observations (R2) or 2+ distinct sentences (R3).
  These are DEC-020's parameters, fixed and not tuned (no validation
  split). No conflict penalty: `configs/docred_functional_predicates.json`
  is empty as in DEC-020, so the rival ceiling does not operate here.
- **Baseline:** no aggregation. Every extracted triple is admitted.

## Evaluation (identical for every arm)

- **Primary evaluator:** per document, an admitted item matches gold
  fact (head, relation, tail) when its predicate equals the relation
  name and its subject/object (b)-forms equal the (b)-form of *any*
  gold mention of the head/tail entity. Items are mapped to
  evaluation keys (the matched gold fact, else the item's own
  (b)-normalised triple) and deduplicated per document before counting.
  So no arm gains or loses from how it spells or groups a fact.
  Counts are summed over documents (micro).
  - Using gold mentions *in evaluation* is standard for DocRED and
    applies equally to every arm, including no-aggregation. It is
    separate from arm (c), which uses gold mentions *in aggregation*.
- **Secondary evaluator (continuity with DEC-020):** exact match
  against gold triples written with each entity's first mention.
- **Reported for every arm and both sentence settings:** precision,
  recall, F1 (both evaluators); admitted-item count; contested slots
  (a (subject, predicate) with 2+ distinct object keys) among all
  candidates and among admitted items; the number of documents in
  which anything was admitted.
- **Diagnostics:**
  - **G2** = gold facts that the raw extractions recover from 2+
    distinct sentences, i.e. the facts aggregation could corroborate.
  - **Pooled rate** = the share of G2 facts that an admitted item
    recovers.
  - **Within-sentence duplicate observations** per key: if there are
    none, R3 is identical to R2 by construction.
- **Statistics:** paired bootstrap over documents, 10,000 resamples
  (seed 20310924). Pooled counts are recomputed per resample, and the
  95% percentile CI of each difference is reported.

## What confirms and what refutes the matching-key explanation (primary setting: all sentences, R2, primary evaluator)

- **CONFIRMED (deployable form):** norm-minus-exact F1 > 0 with 95% CI
  excluding 0, **and** the pooled rate on G2 is higher under (b) with
  CI excluding 0.
  - Strength is graded by the share of the naive-minus-exact F1 gap
    that (b) closes: >=50% means "largely explains"; <50% means
    "partially explains".
  - If PKB-(b) F1 is also not significantly below no aggregation,
    exact-string matching fully accounts for the pilot's failure.
- **ORACLE-ONLY:** (b) fails the test above but (c) passes it. Then
  the problem is entity resolution, not surface spelling. The
  deployable claim is not supported, and (c) is reported only as an
  upper bound.
- **REFUTED (the explanation is wrong):** neither (b) nor (c) raises
  F1 or the pooled rate over (a) with a CI excluding 0. In that case
  the failure is not caused by the matching key. The expected
  alternative is that the extractor rarely recovers the same fact from
  two or more sentences (a small G2). The report will say so and give
  G2 as a share of all gold facts.
- **INCOMPLETE:** (b) or (c) passes, but PKB-(c) F1 is still
  significantly below no aggregation. Then matching explains at most
  part of the failure, and the rest is attributed to low
  multi-sentence recovery (G2).
- Any of these outcomes is reported as found. The evidence-only
  setting is reported alongside, but it does not decide the verdict.

## R3 (first out-of-domain test of the corrected rule)

Primary R3 comparison: R3 minus R2 F1 under key (b), all sentences.
- **Positive:** CI excludes 0 above. The corrected rule helps out of
  domain.
- **Null:** CI includes 0.
- **Untestable here:** key (b) has zero within-sentence duplicate
  observations, so R3 is identical to R2 by construction. That is
  reported as such, not as a null.
- **Negative:** CI excludes 0 below. Reported as found.
R3 is also reported under keys (a) and (c).

## Cost / time

- 6,861 calls at the pilot's $0.0000185/call gives **~$0.13**,
  user-approved.
- ~3 h with 3 parallel processes (DEC-029: 6 were unstable on this
  PC's 6 GB of RAM).
- The analysis is offline and zero-cost.

## Status

DEC-031: PRE-REGISTERED (2026-09-24), cost approved; extraction not yet
started at the time of this commit.

DEC-031: RUN (2026-09-24) -- see EVID-046. 845 docs, 6,861 calls, $0.2111.
  Pre-registered outcome: ORACLE-ONLY + INCOMPLETE -- the matching key does not
  explain the DocRED failure (normalised key closes ~0% of the gap, oracle 7.3%);
  only 29/11,344 gold facts are recovered from 2+ sentences. R3 F1: null;
  R3 precision +0.19 to +0.29 (secondary).

---

# DEC-032 — BioRED at Scale: Extractor Recall vs. Corroboration in a Second Public Domain (pre-registered 2026-09-24; NOT RUN until approved)

## Why is this required?

DEC-031 (EVID-046) found that on DocRED the binding constraint on PKB
aggregation is extractor recall compounded across sentences, not the
matching key. The extractions recover only 29 of 11,344 gold facts from
2+ sentences, although 50.2% have 2+ evidence sentences in the text.
This DEC tests whether the same pattern holds in a second public
domain, biomedical abstracts. It also replaces the 15-abstract DEC-009
pilot (EVID-024), and runs R3 on a second out-of-domain corpus. If the
pattern repeats, that is a cross-domain finding; if it does not, that
is equally informative.

## Did the pilot use an oracle setting?

**No evidence-sentence oracle, but the pilot is not comparable in
another way.** DEC-009 sent each **whole abstract** (title + abstract)
in one call per document and gave the model no gold information (no
evidence sentences, no entities). That is not the kind of oracle
DEC-020 used on DocRED. But whole-abstract extraction gives one source
per document, so nothing could be aggregated. The pilot never tested
the framework, only the extractor.

Two further pilot facts to state plainly:
- **Its prompt listed only 6 of BioRED's 8 relation types.**
  Drug_Interaction and Conversion were missing (14 of 4,906 gold facts
  in this corpus, 0.3%), so those facts were unreachable.
- **Its strict evaluator required argument order.** BioRED relations
  are unordered pairs.

## Corpus

- **All 500 Train + Dev abstracts:** 400 + 100, 5,462 sentences,
  **4,906** unique gold facts (unordered concept pairs with a relation
  type). The Test split is never used, per DEC-009's rule.
- **Sentences:** the title is sentence 0. The abstract is split by the
  fixed regex in `src/dec032_biored.py::SENTENCE_SPLIT`: a split after
  `.`, `!` or `?` followed by whitespace and an upper-case letter, digit
  or opening bracket, except after "e.g.", "i.e.", "et al.", "vs.",
  "Fig.", "approx." or "ca.".
- **Annotation-level corroboration, computed before any extraction
  (zero cost).** BioRED has no evidence-sentence annotations, so the
  measure is whether the two gold concepts are *co-mentioned* in a
  sentence (from the annotated mention offsets):
  - **35.1%** of gold facts are co-mentioned in 2+ sentences. This is
    the annotation-level corroboration rate, against DocRED's 50.2%
    evidence-based rate. It is a proxy: co-mention is necessary for a
    sentence to state the relation, but it does not prove it does.
  - **89.7%** are co-mentioned in at least one sentence. This is the
    most that sentence-level extraction could ever reach.

## Design (follows DEC-031)

- **Primary setting: every sentence, one call each.** Prompt
  `prompts/openie_biored_sent_v1.txt`. It is the pilot's prompt with
  two changes: it says "one sentence" instead of "title and abstract",
  and it lists all **8** relation types (see the diff in the commit).
  The pilot's 6-type list was an omission, not a design choice.
- **Pilot-continuity setting: whole abstract, one call each.** Pilot
  prompt `openie_biored_v1.txt`, unchanged. Reported as no aggregation
  only.
- **Extractors:**
  - `meta-llama/llama-3.1-8b-instruct`, the pipeline's extractor.
  - **External baseline: `deepseek/deepseek-v3.2`** (DEC-002's
    external baseline). Same prompts, same sentences, same abstracts,
    so the numbers can be read against a much stronger model.
  - Both use temperature 0 and max_tokens 1024.
- **Crash-safe and parallel:** `scripts/dec032_biored_extract.py`,
  with DEC-031's per-call cache and sharding. Unparsable output is
  never re-requested.
- **Arms**, all recomputed offline from the same extractions
  (`scripts/dec032_biored_analyze.py`), for each extractor:
  - **no aggregation:** every extracted triple admitted;
  - **R2:** conservative Noisy-Or over every observation;
  - **R3:** the same over distinct source sentences.

  Both rules use confidence 1.0 per observation, shrinkage 0.5, and
  admit at tau = 0.70 (2+ observations / 2+ distinct sentences). These
  are the DocRED values; nothing is tuned. The matching key is DEC-031's
  normalised key (b). DEC-031 showed the key is not the binding factor,
  so a single deployable key is used. No conflict penalty (no BioRED
  functional-predicate policy exists), so contested slots are
  descriptive.
- **Evaluators.** All work per document, with unordered argument
  pairs and predictions deduplicated per gold fact:
  - **PRIMARY: alias-aware exact.** The predicate equals the relation
    type, and subject/object equal, after DEC-031 normalisation, *any*
    annotated mention of the two gold concepts. BioRED annotates every
    mention with its concept ID, so this is the principled analogue of
    DEC-031's evaluator.
  - **Secondary, as the pilot reported: strict and relaxed.**
    - strict: exact match to each concept's first mention;
    - relaxed containment: either string contains the other, the
      pilot's heuristic.

  Relaxed is not primary because containment matches short strings
  loosely (e.g. "p53" inside any longer mention).
- **Reported per extractor and arm:** P/R/F1 under all three
  evaluators; admitted count; contested slots among candidates and
  among admitted items; documents admitting anything.

## Measured FIRST, before any aggregation result (per extractor, sentence level)

1. Extractor recall: no aggregation, primary evaluator.
2. Extraction-level corroboration: **G2** = gold facts the extractions
   recover from 2+ distinct sentences, as a share of the 4,906 gold
   facts, with a bootstrap CI.
3. Annotation-level corroboration for contrast: 35.1% (2+ sentences);
   89.7% (1+).
4. **rho = G2 share / 35.1%**, how much of the corroboration available
   in the text the extractions actually realise.
5. The share of extracted triples whose predicate is one of the 8
   BioRED relation types (DocRED: 49.2%).

## Extractor-recall-constraint hypothesis (H_ER)

"Aggregation that requires corroboration fails because the extractor
rarely recovers the same fact from 2+ sources, not because the text
lacks corroboration." Decided on Llama at sentence level, primary
evaluator. Statistics: paired bootstrap over documents, 10,000
resamples.

- **CONFIRMED:** rho < 0.2 **and** R2 F1 < no-aggregation F1 with the
  CI excluding 0. The extractions realise under a fifth of the
  available corroboration, and aggregation loses.
- **REFUTED, if either holds:**
  - rho >= 0.5 and R2 F1 is still significantly below no aggregation.
    Corroboration is recovered, yet aggregation fails, so the
    constraint is elsewhere.
  - R2 F1 is not below no aggregation (CI includes 0 or is above 0).
    The predicted failure does not occur.
- **PARTIAL:** 0.2 <= rho < 0.5 with R2 significantly below no
  aggregation.
- **Secondary, cross-extractor check (DeepSeek):** H_ER predicts that a
  stronger extractor realises more corroboration. It predicts a higher
  G2 share than Llama (CI of the difference excluding 0), and a smaller
  R2-minus-no-aggregation F1 gap. This is reported as supporting or not
  supporting H_ER. It does not decide the verdict.

## R3: testable or untestable

- **Primary R3 comparison:** R3 minus R2 F1, Llama, sentence level.
  - Positive: CI excludes 0 above.
  - Null: CI includes 0.
  - Negative: CI excludes 0 below.
- **Pre-registered secondary: R3 minus R2 precision.** After DEC-031,
  where the precision gain appeared but was not the pre-registered
  test, it is named in advance here.
- **Untestable:** zero within-sentence duplicate observations. Then R3
  is identical to R2 by construction, and this is reported as
  "untestable here", not as a null.
- **Too thin to interpret:** R2 and R3 admit fewer than 20 items each.
  Reported with the counts, and no direction is claimed.
- The same comparisons are reported for DeepSeek.

## Cost / time estimate (DEC-031 per-call figures)

- Llama: $0.0000308/call, from DEC-031 ($0.2111 / 6,861).
- DeepSeek: 9.7x Llama per call, the ratio measured on full-scale CaRB
  ($0.0000860 vs. $0.0000089), giving $0.000299/call.
- Whole-abstract calls: $0.0000339 (Llama, measured in the pilot) and
  $0.000329 (DeepSeek).
- Throughput: DEC-031 ran 6,861 calls in 43 min with 3 processes (~160
  calls/min). DeepSeek's latency on CaRB was similar to Llama's (mean
  3.5 s vs. 3.3 s).

| Component | Calls | Cost |
|---|---:|---:|
| Llama, sentences | 5,462 | $0.17 |
| DeepSeek, sentences | 5,462 | $1.63 |
| Llama, whole abstracts | 500 | $0.02 |
| DeepSeek, whole abstracts | 500 | $0.16 |
| **Total** | **11,924** | **~$1.98** |

About 75 min with 3 processes. The analysis is offline and zero-cost.

## Status

DEC-032: PRE-REGISTERED (2026-09-24). User approved the full design and
~$1.98 cost (2026-09-24); extraction not yet started at the time of this commit.



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