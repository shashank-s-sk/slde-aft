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
Experiment: SCALED PILOT COMPLETE (10 -> 30 sentences; see EVID-021)
Results: Internal CaRB-30 F1 = 0.0591 (meta-llama/llama-3.1-8b-instruct,
  pinned). Supersedes the old CaRB-10 F1=0.1333 figure (EVID-003), which
  used unpinned `openrouter/auto` and is not a reproducible measurement
  of any specific model — see EVID-021 for why.
Official CaRB score: still TBD (internal normalized exact-match
  evaluator only)

DEC-001, part 1: Prepare CaRB data                 ✅ Done
DEC-001, part 2: Run your LLM on 3 sentences        ✅ Done (now scaled to 30)
DEC-001, part 3: Save and inspect predictions       ✅ Done
DEC-001, part 4: Evaluate internally                ✅ Done
DEC-001, part 5: Export CaRB format and run scorer  — still not completed
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
Implementation: DONE (stronger baseline requirement fulfilled)
Test: DONE (Llama-3.1-8B external baseline CaRB-10, EVID-004; DeepSeek-V3.2
  stronger baseline CaRB-30, EVID-021)
Experiment: PILOT COMPLETE at N=30. DeepSeek-V3.2 F1=0.1340 vs. pinned
  Llama-3.1-8B F1=0.0591 (~2.3x) — see EVID-021.
Results: RECORDED
Remaining:
- REBEL baseline: Deferred; requires an explicit task-alignment and output-mapping protocol
- Official CaRB scoring: TBD
- Scale beyond N=30 toward CaRB's full 634-sentence set if a benchmark-
  grade (not pilot-grade) result is needed

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
Implementation: PARTIAL — zero-cost portion done (src/synthetic_data_generator.py,
  Colab-ready scripts/dec006_lora_finetune.py + dec006_evaluate_adapter.py,
  staged Stage 0 TinyLlama-1.1B / Stage 1 7B-8B QLoRA via a config flag).
  See EVID-025. GPU training itself not yet run.
Testing: DONE for the zero-cost portion (4 new tests, 44/44 suite passing;
  127 real synthetic examples generated from EVID-013's actual PKB run
  as a cross-check, not just synthetic test fixtures)
Experiment: NOT STARTED (needs GPU — free Colab first per the staged
  budget plan; see conversation for the $0 -> ~$5-15 -> ~$20-50 staging)
Results: TBD
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