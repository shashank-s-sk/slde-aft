# AUDIT.md — Phase 0 Audit (Q1 Rework)

**Scope:** per README.md's Phase 0 instructions — no API spend, no new experiments. This audits what already exists against professor_feedback.md's 13 points, checks the 5 specifically-flagged validity concerns, and flags every place `Results Summary.md`'s language is stronger than the underlying evidence supports.

**Method:** every number below is traced to a specific EVID-xxx entry in `Evidence log.md` or a script in `scripts/`/`src/`, read directly for this audit. Nothing is estimated or rounded beyond what the source states. Where I could not trace a number, I say so explicitly.

**Pre-check:** `pytest tests -q` → **49 passed in 111.82s, 0 failures.** The codebase itself is not the problem; the concerns below are about experimental design and claim framing.

---

## Part A — The 5 specifically-flagged concerns (checked first, they're the most urgent)

### A1. Is the "Claim 3 (Noisy-Or) is strongest" framing overstated?

**Yes, in two independent ways — both confirmed.**

1. **Ablation tension:** `Results Summary.md` calls Claim 3 "the strongest, most defensible result in the project." But DEC-023's own N=50 ablation (EVID-039) found `without_prob_kb` (max-merge, Noisy-Or removed) scored **numerically higher** than `full`: held-out test F1 mean 0.3783 vs. 0.3451. The paired significance test didn't distinguish them (p=0.63/1.0), so this isn't "Noisy-Or hurts" — but it directly contradicts "strongest, most defensible": the one experiment that actually removes the mechanism in the full closed loop shows no benefit, and if anything a numerically worse `full`.
2. **EVID-014's comparison isn't what `Results Summary.md` says it is.** I read EVID-014 directly: the "+0.043 F1" figure is **conflict-adjusted Noisy-Or vs. raw (unadjusted) Noisy-Or support** — not vs. a naive/no-aggregation baseline. `Results Summary.md` currently says *"improves F1 by +0.043 in aggregate over a naive baseline"* — this is not what was measured. Raw Noisy-Or is itself a non-trivial aggregation mechanism, not a naive baseline (e.g., "just keep the last observation" or "no aggregation at all"). Additionally, per EVID-014 itself: single seed/single run, and **flat-to-negative on the 117 rows that actually have a competing alternative** (F1 0.1846 → 0.1667, i.e., worse) — the aggregate improvement is coming from the 540 rows where conflict-adjustment barely matters, not from the mechanism doing its stated job (resolving genuine conflicts).

**Verdict: the "strongest, most defensible claim" framing needs to be walked back to something like "shows a real aggregate effect on one real-data run, with an unresolved tension against the closed-loop ablation and a documented failure to resolve genuine multi-candidate conflicts" — not the current unqualified superlative.**

### A2. Was epochs=5 selected using the same test set as the 5-seed confirmation?

**Yes — confirmed by reading the code directly.** `scripts/dec006_evaluate_adapter.py` (line 125-141) always evaluates on `build_product_split()`'s fixed `test` split (the same 8-product leakage-safe set, after excluding 2 leaked products) — there is no separate validation split used anywhere in DEC-006/022's pipeline.

- Stage 1 (epochs ∈ {2,3,5,8}) picked epochs=5 because it scored best **on this exact 8-product test set**.
- Stage 2 (LoRA rank/alpha/lr grid) picked the winning config the same way, on the same test set.
- Stage 3 (the "confirmatory" 5-seed run) evaluated that same winning config, **on the same test set again.**

**This is hyperparameter selection on the test set — a real validity threat, not a stylistic nitpick.** With only 8 products and 9 configurations tried across Stages 1-2, some of the apparent epochs=5 advantage is very plausibly the search fitting this specific small test set's idiosyncrasies rather than a generalizable effect. **The reported one-sample t-test p=0.0028 (EVID-040) should not be presented as clean, unbiased significance.** `Results Summary.md` and `Decision log.md` currently do present it that way ("the first fine-tuning configuration in the project to reach conventional statistical significance") with no mention of this leakage.

### A3. Is the provenance-filter result (93.5% → 100%) circular?

**Yes — confirmed by reading `src/datasets/product_generator.py` directly.** `gold_unstructured` (line 94-96) is constructed literally *from* `gold_structured`, which is built from the same generated attribute values that populate the structured CSV row. In this synthetic dataset, "the structured source" and "the gold label" are, by construction, close to the same thing.

This means: "requiring structured corroboration before accepting a triple" and "matching gold" are testing something close to a tautology in this dataset — of course a triple that agrees with the data-generating source agrees with the gold that was built from the same source. **This does not mean the provenance-filter idea is wrong or useless** — but the current 93.5%→100% number does not demonstrate that the filter would help in a realistic setting where the structured source itself could contain errors, which is the actual real-world justification given for the mechanism ("provenance actively filters synthetic training data quality"). `Results Summary.md` presents this as "a rare case where ground truth is known exactly" — true, but doesn't disclose that this also makes the validation partially circular for the filter's stated purpose.

### A4. Is "base" fine-tuning F1 one fixed number used in a one-sample t-test?

**Yes — confirmed.** `scripts/dec006_5seed_stats.py` line 29 loads `base_f1` once from a single saved metrics.json and uses it as a fixed `popmean` in `stats.ttest_1samp(vals, popmean=base_f1)` (line 39) for every comparison. This is defensible as a design choice (the base model uses deterministic/greedy decoding, so it genuinely has no seed-to-seed variance) — **but it means the test only captures variance in the fine-tuning process across seeds, not variance from the test set itself.** With only 8 test products, a single product's result flipping changes F1 by roughly 1/8 = 12.5 percentage points on recall terms. No bootstrap-over-test-products confidence interval has been computed. Combined with A2's tuning leakage, this compounds the case that **p=0.0028 overstates how settled this result is.**

### A5. Which experiments have no raw outputs committed?

**All of them.** `outputs/` is entirely gitignored (`.gitignore` line: `outputs/`). I counted **32 top-level experiment output directories** currently on disk (`carb_10_dev`, `dec001_002_carb30`, `dec001_part6_carb_full`, `dec003_product_probkb_v2`, `dec005_multiseed`, `dec006_adapters`, `dec006_eval`, `dec020_docred_extract_and_pkb`, `dec023_ablation_n50`, and 23 more) — **none are in git.** Every number in `Evidence log.md` traces to a local file that a third party (or a future you, on a different machine) cannot access from the GitHub repo alone. This is professor_feedback.md point #12's core ask, unaddressed.

---

## Part B — Manuscript consistency issues (found while reading `SLDE.docx`/`SLDE.pdf` directly)

- **Duplicate "Table 8" numbering, confirmed by direct read**: the per-iteration table for SLDE-AFT Full ("Table 8 Per-iteration precision, recall, F1, new-triple growth, and runtime...") and the per-iteration table for SLDE-AFT Prob-KB ("Table 8 Per-iteration precision, recall, F1, KB size, and growth...") are both labeled Table 8. Table 9 (fine-tuning) is therefore also mislabeled relative to a correct sequential count.
- **Sections 8-11 (Ablation Analysis, Discussion, Limitations/Future Work, Conclusion) do not exist** despite being promised in Section 1's roadmap paragraph. Already known; restated here for completeness.
- **Abstract and Keywords are empty placeholders** — headings exist, no text.
- **Sections 4.6, 5.4, 6.1, 6.2, 6.3, 7 all describe the original prototype** (TinyLlama-1.1B, OpenRouter Auto, Google Colab T4, B1/B2/B3 baselines) rather than the actual validated pipeline (Llama-3.1-8B/Mistral-7B, pinned models, RunPod, the real `full`/`without_feedback`/`without_prob_kb`/`structured_only`/`unstructured_only` ablation design). Already flagged in a prior session pass; restated here since it's directly relevant to "claims stronger than evidence" — the manuscript's Results section currently reports numbers (Precision 0.9000, 84% gain, Recall=1.0000) that are **not from any of the pinned, validated experiments in `Evidence log.md` at all** — they're from a run using unpinned `openrouter/auto` routing, which cannot be attributed to any specific, reproducible model.

---

## Part C — Professor feedback's 13 points: what exists, what's missing, overclaim check

| # | Point | What exists | What's missing | Results Summary overclaim? |
|---|---|---|---|---|
| 1 | Public benchmarks | CaRB full-scale (EVID-035, N=548, solid); DocRED pilot (DEC-020, n=15); BioRED pilot (DEC-009, n=15); TACRED explicitly declined w/ documented reason | REBEL-benchmark (dataset)/Universal-IE untried | DocRED's n=15 is very small for the generality of the claim made ("the framework does not transfer to open-domain text") — real finding, but should be labeled clearly as a preliminary pilot, not a general conclusion |
| 2 | SOTA comparison | DeepSeek/Llama at full CaRB scale (N=548); GPT-4o/Claude/Gemini at pilot scale only (N=30); REBEL model incompatibility documented | GenIE/InstructUIE/DyGIE++ untried | No major overclaim — pilot vs. full-scale status is already disclosed separately |
| 3 | Math contribution | Noisy-Or formalized, real-data check (EVID-014), calibration (EVID-036, ECE=0.333), complexity (EVID-036, O(N)/O(N²)) | Formal boundedness/monotonicity proof, convergence discussion (pure math-writing) | **Yes — see A1 above.** "Strongest, most defensible" framing is in real tension with the N=50 ablation and mischaracterizes EVID-014's actual comparison |
| 4 | Ablation study | DEC-004/005 (N=20, null) + DEC-023 (N=50, null, properly powered) | None — this is honestly done | No overclaim on the ablation itself; but see A1, since claim 3's framing depends on ablation results too |
| 5 | Statistical validation | 5-seed convention throughout; N=20 and N=50 for ablation; 5-seed for fine-tuning | Bootstrap CIs over test products (README Phase 1d); multiple-comparison correction across the ablation family (5 configs tested, no correction applied) | **Yes — see A2, A4.** The fine-tuning "significance" doesn't disclose tuning-on-test-set leakage or the fixed-base-constant limitation |
| 6 | Fine-tuning section | Full epoch/LoRA grid (DEC-022), "significant" result (EVID-040) | Redo with validation/test split separated (README Phase 1a) | **Yes — same issue as point 5.** This is the point most directly affected by A2 |
| 7 | Error analysis | DEC-007 general analysis; DEC-018 provenance-filter examples (concrete, matches this point's ask) | — | **Yes — see A3.** The provenance-filter's headline number doesn't disclose the circularity in how it was validated |
| 8 | Scalability | DEC-008 runtime/latency (positive, N≤200); DEC-003 complexity analysis (O(N)/O(N²), honest) | Memory measurement still broken (known, disclosed); GPU utilization/memory during fine-tuning not logged | No overclaim found — this section is already appropriately hedged |
| 9 | Multiple domains | BioRED pilot (n=15) | No external baseline on BioRED; scale beyond n=15 | Already labeled as pilot-scale; reasonably honest, though n=15 is very small for the "harder but not a near-total failure" framing given |
| 10 | Discussion | Not written | Section 9 entirely | N/A |
| 11 | Novelty positioning | Not written | Section on differentiation vs. RAG/continual learning/AutoML/UIE/KG-pop/self-training | N/A |
| 12 | Reproducibility | Decision log/Evidence log/Results Summary trail | **See A5 — zero raw outputs committed anywhere.** No `scripts/reproduce_all.py`. `requirements.txt` doesn't separate fine-tuning deps. README status text is stale (still says "DEC-006 through DEC-013: not started") | This is a real, substantial gap, not just a documentation nicety |
| 13 | Writing refinement | Not started | Duplicate Table 8 (Part B); missing sections; Abstract/Keywords empty | N/A |

---

## Part D — Summary: what this means for submission readiness

Cross-referencing against `slde_aft_next_steps.md`'s own decision-rule table: given that (a) the ablation shows PKB/feedback do **not** reliably improve held-out extraction over simpler alternatives at the scales tested, and (b) the fine-tuning "significant" result has an unresolved tuning-leakage threat, the current evidence most closely matches this row from that table:

> *"PKB aggregation is the only reliably improved component → Write a focused Springer workshop paper on confidence-aware and provenance-aware PKB accumulation"*

— and even that row is now in question given A1. **Before any of the manuscript sections (7-11) are finalized with current numbers, Phase 1's validity fixes (tuning-leakage correction, provenance-circularity test, Noisy-Or vs. real baselines, test-set-uncertainty quantification) should be run**, per README.md's own prescribed order. Writing the paper now, using the numbers as currently reported, risks putting claims into the manuscript that a rigorous reviewer (or this audit) can directly contradict from data already in the repository.

## Part E — What did NOT need fixing (confirmed solid on this pass)

- Test suite: 49/49 passing.
- CaRB full-scale numbers (EVID-035): no leakage/circularity issue found — separate model, separate benchmark, official scorer.
- DEC-023's null result methodology itself: no issue found — the ablation used a proper validation-free comparison (no hyperparameter was tuned for the ablation study itself).
- DEC-008 scalability and DEC-003 complexity findings: no overclaim found.

---

*Per Phase 0 instructions: stopping here. No experiments run, no numbers changed, no files other than this audit and the branch checkout created. Awaiting direction on whether to proceed to Phase 1.*
