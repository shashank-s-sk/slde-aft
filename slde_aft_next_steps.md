# SLDE-AFT Next Steps

## 1. Preserve and verify current work

- Keep the current SLDE-AFT architecture, title, code, notebooks, PDFs, datasets, raw outputs, and result CSVs.
- Do not delete or overwrite the existing 20-, 30-, 40-, and 50-product experiments.
- Save the exact OpenRouter model ID, model-routing date, temperature, top-p, max tokens, prompt version, API settings, Python package versions, GPU/runtime details, and random seeds.
- Create one script or notebook that reproduces every number reported in Tables 7–9 directly from saved raw outputs.
- Fix manuscript consistency issues: duplicate Table 8 numbering, missing promised Sections 8–11, incomplete or duplicate references, and any mismatch between text and tables.

## 2. Create a leakage-safe split

- Split product entities into train, validation, and held-out test sets, for example 70% / 10% / 20%.
- Save the split as a CSV or JSON file using a fixed random seed.
- Ensure test products do not appear in synthetic training examples, fine-tuning data, few-shot prompt examples, feedback-controller exemplar data, threshold selection, or validation tuning.
- For the held-out test, evaluate extraction from unstructured text only.
- Do not provide structured target triples as test-time KB seed data for held-out products.

## 3. Separate the three evaluations

- Report unstructured extraction quality: evaluate only triples extracted from text.
- Report cumulative PKB quality: evaluate all triples stored in the PKB across iterations.
- Report structured ingestion quality separately: CSV-to-triple conversion is deterministic and should not be mixed with LLM extraction performance.
- Do not describe cumulative Recall = 1.0000 as pure extractor performance.
- Describe it as a result of monotonic knowledge preservation under the defined PKB policy.

## 4. Run source and feedback ablations

- Compare unstructured-only extraction, structured-only ingestion, static dual-source extraction, KB-guided extraction, and full SLDE-AFT.
- Compare no feedback, Encouraging Mode only, Prohibitive Mode only, and both feedback modes.
- Keep input documents, prompt budget, base model, number of iterations, and evaluation set identical across conditions.
- Report precision, recall, F1, false positives, new gold triples, KB growth, prompt cost, and runtime per iteration.

## 5. Validate PKB mathematics

- Compare max merge, mean aggregation, standard Noisy-Or, Conservative Noisy-Or, and conflict-adjusted Conservative Noisy-Or.
- Sweep thresholds from 0.00 to 1.00, preferably in increments of 0.01.
- Report best F1, precision, recall, ECE, Brier score, retained triples, and conflict counts.
- Test several conflict levels and observation-count settings.
- Treat the conflict-adjusted score as a conservative ranking/admission score unless calibration experiments show it is a well-calibrated probability.

## 6. Validate the fine-tuning claim

- Evaluate the base model before fine-tuning on the held-out unstructured test set.
- Compare no fine-tuning, unfiltered synthetic-data fine-tuning, confidence-filtered PKB synthetic-data fine-tuning, and confidence + provenance-filtered synthetic-data fine-tuning.
- Use the same held-out test set for every condition.
- Report pre/post fine-tuning precision, recall, F1, ECE, Brier score, and training-example count.
- Run at least 3 random seeds; use 5 seeds if computationally feasible.
- Claim self-learning improvement only if the complete method improves reliably over no-fine-tuning and unfiltered controls.

## 7. Improve paper evidence

- Keep the current broad SLDE-AFT architecture and original research direction.
- Narrow only the claims if the data does not yet prove every component improves performance.
- Add confidence intervals or mean ± standard deviation across runs.
- Add a limitations section covering the synthetic product domain, small-scale data, monotonic PKB recall interpretation, fine-tuning instability, and API-model reproducibility limitations.
- Add at least one larger or more realistic dataset/domain before targeting a full journal.

## Decision rule for submission

| Experimental outcome | Recommended paper positioning |
|---|---|
| Feedback, PKB, provenance filtering, and fine-tuning all improve held-out extraction consistently | Keep the full SLDE-AFT title and submit as a strong conference paper |
| Feedback and PKB improve, but fine-tuning is inconsistent | Keep SLDE-AFT architecture; present auto fine-tuning as a prototype/feasibility component |
| PKB aggregation is the only reliably improved component | Write a focused Springer workshop paper on confidence-aware and provenance-aware PKB accumulation |
| Results are stable across seeds and include held-out evaluation plus ablations | Consider a full Springer-affiliated conference track |
| Results use one synthetic domain or lack controls | Start with a Springer workshop/short-paper venue |

## One-line goal

> Prove that SLDE-AFT improves held-out unstructured extraction, not only cumulative knowledge-base recall, and prove which modules—structured seed, PKB aggregation, feedback, provenance filtering, and automated fine-tuning—create that improvement.
