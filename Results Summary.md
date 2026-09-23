# Results Summary — SLDE-AFT

**Purpose of this file:** a single, self-contained, paper-ready summary of every real result this project has produced, with honest interpretation for each. Written so it can be pasted directly into any LLM (or read by a human) when drafting the manuscript's Results/Discussion sections, with no need to cross-reference `Decision log.md` / `Evidence log.md` for the numbers themselves — those two files remain the detailed, process-oriented working logs (rationale, full limitations, next steps); this file is the distilled, citable output.

**How to keep this in sync:** whenever a new EVID-xxx entry changes a claim's status or headline number, update the corresponding section here too. `Decision log.md`'s STATUS DASHBOARD table is the fast-scan index; this file is the narrative version meant for writing prose from.

**Do not invent or round numbers beyond what's shown here.** Every number below is sourced from a specific EVID-xxx entry in `Evidence log.md` — cite that EVID number if asked where a figure came from.

---

## The 5 claimed novelty contributions — final status

| # | Claim | Verdict | Headline number |
|---|---|---|---|
| 1 | Unified closed-loop architecture | Tested end-to-end; flat vs. baseline, beats not-fine-tuning | F1 0.3869 → 0.3864 (loop) vs. 0.3791 (no fine-tune) |
| 2 | Automated synthetic supervision | Real effect vs. base, **but the hyperparameter selection has a disclosed tuning-leakage limitation** | Mean F1=0.2012 (std 0.0194) across 5 seeds vs. base 0.1373 — one-sample t-test **p=0.0028** (EVID-040). **Caveat: epochs=5 was selected using the same 8-product test set later used to report this p-value (AUDIT.md A2) — report as suggestive, not clean confirmatory significance, unless DEC-024's validation-split rerun is completed first** |
| 3 | Noisy-Or math contribution | A real, positive real-data finding, **but not an unqualified "strongest" claim** — it sits in tension with the N=50 ablation | +0.043 F1 (conflict-adjusted vs. **raw/unadjusted Noisy-Or**, not a naive/no-aggregation baseline — AUDIT.md A1); real-data ECE=0.3332 (EVID-036). **The N=50 ablation (EVID-039) found removing this mechanism (`without_prob_kb`) scored numerically as well as or better than keeping it** — report both findings together |
| 4 | Feedback Controller reduces manual reliance | Honest null, tested at two scales, **power-limited** | N=20: p=0.31–0.51 (EVID-020); N=50: p=0.57–1.0, variance shrank 3.6x (EVID-039). **At n=5 seeds this design can only detect effects of ≈0.29-0.30 F1 or larger (Cohen's d=1.68 for 80% power, AUDIT.md Part C) — do not call this "properly powered" without that qualifier; it rules out large effects only** |
| 5 | Provenance actively filters training data | A real precision result, **but validated under a partially circular setup** | Precision 93.5% → 100% (drops 31/475 wrong triples). **Caveat: gold labels and the structured source it corroborates against are both derived from the same generator (AUDIT.md A3) — this does not test robustness to a structured source that itself contains errors, the realistic scenario the filter is meant for** |

Plus two foundational corrections: **official CaRB benchmark scores are 4-8x higher than every previously-reported internal-evaluator number**, and CaRB is now at full 548-sentence scale, not a 30-sentence pilot (see below) — use the official, full-scale numbers, not the internal or pilot ones, anywhere CaRB is cited.

**All four caveats above come from `AUDIT.md` (2026-09-20/21), a methodological review that checked every headline claim in this file directly against the underlying code and data. Where this file and `AUDIT.md` conflict, `AUDIT.md`'s corrected framing is authoritative — the sections below have been updated to match it.**

---

## Claim 3 — Noisy-Or Conservative Confidence Aggregation (the math contribution)

**A real, positive real-data finding — but do NOT call it "the strongest, most defensible claim in the paper" or any equivalent unqualified superlative. AUDIT.md found this framing is in direct tension with the project's own ablation evidence; report both sides together.**

- Real-data check (EVID-014): the conservative Noisy-Or + mutual-exclusivity-penalty aggregation improves F1 by **+0.043** in aggregate **compared to raw (unadjusted) Noisy-Or support** — NOT compared to a naive/no-aggregation baseline. Raw Noisy-Or is itself a non-trivial aggregation mechanism; do not describe this comparison as "vs. naive," on real (not synthetic) product-domain data.
- Full instrumented run (EVID-013, 155 API calls, $0.00259): train-set iteration F1 progressed **0.3668 → 0.3682 → 0.2894 → 0.4183** across 4 iterations — non-monotonic and not fully explained (flagged for future error analysis, see DEC-007). Held-out F1: **val 0.5970** (n=5), **test 0.1970** (n=10).
- Toy/scaled synthetic validation (EVID-005/009) also supports the mechanism working as designed.
- **Direct tension with the project's own ablation (AUDIT.md A1, new):** DEC-023's N=50 ablation (EVID-039) found `without_prob_kb` (max-merge, i.e. this mechanism *removed* from the full closed loop) scored **numerically higher** than `full` on held-out test F1 (0.3783 vs. 0.3451). The paired significance test did not distinguish them (p=0.63/1.0), so this isn't "Noisy-Or hurts" — but it directly contradicts describing this as the project's strongest, most defensible result. **Report both the positive EVID-014 finding and this ablation tension together, honestly.**

**Honest nuance for the Discussion section:** the aggregation helps *in aggregate* (vs. raw Noisy-Or, single run), but doesn't specifically resolve genuine fact conflicts well — of 117 real conflicts found, 108 were hallucination-vs-hallucination (the model contradicting its own wrong answer across passes), not correct-vs-incorrect, and conflict-adjustment is flat-to-negative (F1 0.1846→0.1667) on precisely those 117 rows. Report this nuance; don't imply the math resolves truth-vs-falsehood conflicts when it mostly resolves noise-vs-noise ones, and the aggregate improvement comes from the other 540 rows where the conflict/non-conflict distinction barely matters.

**Suggested framing:** "The conservative Noisy-Or aggregation with mutual-exclusivity penalty improves aggregate extraction F1 by 4.3 points relative to unadjusted Noisy-Or support on one real-data run; however, this improvement is flat-to-negative on the subset of triples with a genuine competing alternative, and a separate N=50 closed-loop ablation found no significant difference (and a numerically higher score) when the mechanism was removed entirely — the aggregate real-data benefit and the ablation result should both be reported, not just the favorable one."

**Real-data calibration and computational complexity (EVID-036, new):** closes the two remaining DEC-003 deliverables the professor asked for by name (point #3).

- **Calibration:** on the 657-triple gold-labeled real snapshot from EVID-013, **ECE=0.3332, Brier score=0.2969** — confirms the score should be reported as an aggregated confidence, not a calibrated posterior probability (exactly what this project's own original design decision already anticipated). The worst-calibrated bins (0.6-0.9 confidence, but 0% actual accuracy) are almost entirely functional predicates with **zero competitors** — cases where the extractor confidently repeated the same wrong value with nothing ever recorded to challenge it. This is the calibration-curve signature of the same failure mode Claim 5's provenance filter was built to catch, seen from a different angle.
- **Complexity:** the production PKB's candidate-acceptance path is empirically confirmed **O(N) per call / O(N²) cumulative** (72.7x latency growth for 80x more observations), caused by a linear scan in `pkb_instrumentation.accepted_slot_keys` over every candidate ever accepted. An indexed alternative (same Noisy-Or math, illustrative only, not wired into production) achieves ~O(1) per call / O(N) cumulative. Not a current performance problem (N has stayed in the hundreds; DEC-008's linear-runtime finding is dominated by LLM API latency, which masks this), but a forward-looking scalability finding worth stating.

**Suggested framing (calibration):** "Real-data calibration analysis (ECE=0.333) confirms the Noisy-Or score functions as an aggregated confidence rather than a calibrated probability; miscalibration concentrates in functional-predicate slots with no competing alternative, where repeated but ungrounded extractions accumulate confidence without genuine corroboration."

**Suggested framing (complexity):** "The current candidate-acceptance implementation scales O(N) per observation (O(N²) cumulative) due to an unindexed slot lookup; an indexed alternative reduces this to O(1) per observation with no change to the underlying aggregation mathematics, relevant if the framework is scaled beyond hundreds of observations per run."

**Confidence is model-self-reported, not derived from calibration or token probabilities (new, verified directly against `src/extractors/openrouter_llm.py` line 35):** the extraction prompt instructs the LLM: *"Output confidence between 0.80 and 0.96."* Every per-observation confidence value feeding the Noisy-Or formula is the model's own stated number within this instructed range, not computed from log-probabilities, ensembling, or any external calibration signal. State this plainly when describing the confidence input to Equation 1 — it explains part of why the real-data ECE (0.333, above) is poor: the input signal itself was never designed to be a calibrated probability.

**A provable ceiling for contested single-valued-predicate slots (new, verified directly against `src/pkb_math.py`, `src/pkb_instrumentation.py`, and `configs/functional_predicates_product_domain.json`):** 12 of the 13 product-domain predicates are configured as functionally single-valued (`has_color` is the sole exception). For these, `conflict_adjusted_confidence` computes C_t = A_t / (m_t + 1), where A_t (conservative Noisy-Or support) is always < 1. **Consequence: whenever a slot has one or more rival candidate values (m_t ≥ 1), C_t < 0.5 by construction — mathematically bounded well below the project's 0.88 acceptance threshold.** A contested single-valued-predicate slot can therefore never be admitted into the knowledge base while a rival exists for it, regardless of how much observational support accumulates. Separately confirmed: no candidate is ever deleted or pruned from the accepted-candidates store anywhere in `src/probkb_v2_adapter.py` or `src/pkb_instrumentation.py` (no `del`/`pop`/`remove` on the accepted dict) — consistent with the architecture's stated monotonic design (Section 4.4), but combined with the ceiling above, it means a genuinely contested functional slot is not just slow to resolve, it is structurally unresolvable under the current formula and threshold. **Do not estimate how much recall this costs — that has not been measured — state it as a proven mathematical property of the current design, with the recall impact explicitly marked as unmeasured/future work.**

**Empirical confirmation of the ceiling, plus a tested correction — and an honest null for a second candidate fix (DEC-026, EVID-041, new).** This is also the direct response to the proof above ("the recall impact explicitly marked as unmeasured/future work"): it stays unmeasured (that would require a new extraction run), but whether the ceiling actually suppresses admission on real already-collected data, and whether a corrected rule beats it, is now measured, offline, at zero additional API/GPU cost. Same DySECT (arXiv 2603.06915) formula this project's Eq. 1-2 already matches — the contribution here is the failure-mode analysis and the corrected-rule test, not the formula itself.

- Five aggregation rules replayed over the identical stored observations from two gold-labeled snapshots (657 triples/35 products; 2241 triples/140 products), each with its own validation-selected threshold and held-out test evaluation (35 and 92 test-split subjects respectively): R1 max-merge (no conflict handling), **R2 the published rule (unchanged)**, R3 source-count (Noisy-Or aggregated over distinct `(source_type, source_id)` pairs instead of repeat observations — a direct fix for the repeat-counting failure mode below), R4 evidence-share (`C(t)=A(t)^2/sum_j A(t_j)`, a candidate fix for the ceiling), R5 = R3+R4 combined.
- **The ceiling is confirmed, not just proven:** R2 admits exactly **0** contested single-valued-predicate slots on both test splits, while the unconstrained R1 baseline admits 6 and 40 respectively — the ceiling, not the data, is what blocks contested admission under the published rule.
- **R4 (the evidence-share ceiling fix) is a clean, reproducible null:** it produces an admitted set **byte-identical to R2 on both datasets** (bootstrap 95% CI for the F1 difference is exactly [0.0000, 0.0000] on 10,000 resamples over test subjects). The algebraic cap is removed, but every observed contested-slot score in this data falls well short of the operating threshold (max 0.581 vs. tau=0.73 on dataset A) — so it never actually changes which triples are admitted. R5 inherits this null (its R4 component contributes nothing, so R5 = R3's result exactly).
- **R3 (the repeat-counting fix) is a small but statistically real win:** F1 improves over R2 on **both** independent snapshots (+0.0106, 95% CI [0.0028, 0.0222] on 657-triple data; +0.0039, CI [0.0013, 0.0075] on 2241-triple data), driven entirely by a **precision** gain at unchanged recall (e.g. 0.5095→0.5214 at fixed R=0.9571) — deduplicating repeated same-source observations removes artificially inflated confidence on hallucinated-but-uncontested candidates, exactly the mechanism EVID-029's "laptop device"-style repeated-hallucination finding predicted.

**Suggested framing:** "Replaying five aggregation rules over two independent gold-labeled real-data snapshots confirms the rival ceiling empirically (the published rule admits zero contested single-valued slots on either test set, versus 6/40 for an unconstrained baseline) and shows that a repeat-counting correction (aggregating over distinct sources rather than repeat observations) yields a small but statistically significant F1 improvement on both (+0.011, +0.004; 95% CIs exclude zero), driven by precision. A candidate fix for the ceiling itself (an evidence-share reformulation) was also tested and found to make no measurable difference on this data — an honestly-reported negative result, not evidence that no ceiling fix could work, only that this specific formulation does not move this specific data."

**Approved follow-up round (DEC-026 addendum, EVID-041 revised, new):**

- **Headline — R1 vs. R2, REVISED after the round-2 fixed-tau bootstrap (read this before citing either rule):** at each rule's own independently F1-selected threshold, R1 (max-merge) beats R2 (published) on both precision and recall on both datasets (e.g. dataset A: P=0.5385/R=1.0000 vs. P=0.5095/R=0.9571), matching the same direction already found in the project's N=50 closed-loop ablation (`without_prob_kb` >= `full`, AUDIT.md A1, EVID-039). **But at the pipeline's actual shared operating threshold (tau=0.88), this does not hold**: bootstrap CIs (10,000 resamples, precision/recall/F1 separate) show R1's precision is significantly *worse* than R2's and its recall significantly *better*, and the two cancel — R1's F1 gain over R2 at tau=0.88 does **not** reach significance on either dataset (CI includes 0). **R1's apparent win is an artifact of letting it pick its own (much higher, 0.98) threshold; at one shared operating point it is a precision-for-recall trade with no net F1 gain, and it achieves whatever it does get by abandoning all protection against contradictory values in single-valued slots (6/40 and 20/69 contested-slot admissions at its two thresholds, vs. 0 for R2/R3 at either).** This is why R1 is not cited as a corrected rule anywhere in the manuscript — it is cited only as empirical confirmation that the ceiling is real (R2 admits 0 contested slots where R1 admits many).
- **Fixed pipeline threshold (tau=0.88), with its own bootstrap CIs:** R3's precision advantage over R2 **does** survive at tau=0.88 on both datasets (+0.1060 [0.0321,0.2267] on A, +0.0270 [0.0076,0.0519] on B, CIs exclude 0), at *exactly unchanged* recall (bootstrap CI exactly [0,0] both datasets — R3 and R2 admit the identical TP/FN split at this threshold, the dedup only removes false positives here) — F1 CI also excludes 0 on both. **R3 is the one rule whose improvement over R2 is robust to threshold choice — significant at both the F1-selected threshold and the fixed pipeline threshold — which is why it is the rule Section 4 cites as the correction, not R1.**
- **R6 (exploratory, post-hoc, labeled as such):** an unsquared evidence-share variant (`A(t)/sum_j A(t_j)`, no square) tested after seeing R4's null. **Underperforms R2** (dataset A: F1 −0.0429, CI excludes 0 — statistically worse; dataset B: −0.0131, CI does not exclude 0). Root cause verified directly, not just observed: for every *uncontested* slot, the unsquared formula reduces to `A(t)/A(t) = 1.0` exactly, regardless of actual evidence strength — confirmed on all 495 of dataset A's 495 uncontested functional-predicate rows scoring exactly 1.0. **This is a structural finding about the rule, not just this dataset:** any share-based conflict-adjustment formula must reduce to `A(t)` when a slot is uncontested to avoid this failure mode — R4's square satisfies that requirement (and is therefore well-formed, if empirically inert here); R6's absence of a square violates it. Escaping the ceiling is not free — a correct share-based fix has its own independently-derivable correctness requirement, and R6 shows what happens when it's violated.
- **Recall denominator, stated explicitly:** DEC-026's recall uses `gold_unstructured` for train-split products (imported from the original DEC-003/DEC-006 scripts' own gold logic — same set as those scripts' own `train_gold_keys` and the snapshot's own `gold_label` column). **Comparable** to EVID-014's whole-KB recall on the same 657-snapshot at the same tau=0.88 (0.4041 there vs. 0.3929 on DEC-026's test-split half — consistent, a useful cross-check). **Not comparable** to EVID-013's held-out recall (different products, no threshold admission) or to EVID-030/DEC-019's closed-loop recall (0.2440 — uses `gold_structured`, a stricter/larger denominator, verified directly against that script's source). **State this explicitly wherever DEC-026's recall numbers are cited alongside any other recall figure in this project.**
- `outputs/dec026_aggregation_rules/` is now committed to the repository (an explicit, one-time exception to the project's standing outputs/-is-gitignored convention, made because this experiment is load-bearing for the paper's contribution) — full per-triple scores, splits, threshold grids, and bootstrap distributions are available for direct inspection, not just this summary.

**Remaining DEC-003 gap:** formal boundedness/evidence-monotonicity proof and a convergence discussion (steps 3-4) are pure mathematical derivation tasks, not experiments — still to be written directly into the manuscript's math section.

---

## Claim 5 — Provenance-Based Filtering (a real precision result, now validated under a noisy structured source too)

**A rare case where ground truth is known exactly** (the product domain is synthetically generated), enabling a real precision measurement, not just an implementation claim. AUDIT.md originally found the EVID-029 validation partially circular (structured source and gold come from the same generator); **DEC-028 (EVID-042, new) closes that gap directly, not by argument but by measurement** — see below.

- Filter rule: a triple is kept only if at least one of its observations came from a **structured** source (not just repeated unstructured/LLM observations).
- Validated on 475 above-threshold triples from the 200-product PKB run (EVID-029):

| | n | Precision vs. gold |
|---|---:|---:|
| Unfiltered | 475 | 93.5% |
| Passes filter (has structured corroboration) | 444 | **100.0%** |
| Fails filter (unstructured-only) | 31 | **0.0%** — every single one wrong |

- **Mechanistic bonus finding:** the 31 dropped triples are almost all generic device-category nouns ("laptop device", "tablet device") standing in for the real product name, repeated 2-21 times each and mistaken by Noisy-Or aggregation for corroborating evidence. This *directly explains* (not just correlates with) the "subject-copying" failure mode seen in the DEC-006 fine-tuned model's outputs — it learned from these exact hallucinated examples.
- **Original circularity caveat (AUDIT.md A3 — verified directly against `src/datasets/product_generator.py`):** in this synthetic dataset, the gold labels used to score the filter are constructed *from the same generator* as the structured source data the filter checks against, so "requires structured corroboration" and "matches gold" were, by construction, close to the same test in the EVID-029 measurement above.

**DEC-028 (EVID-042, new): the filter tested directly under a noisy structured source, not just argued to need it.** 0%/5%/10%/20% of the 200-product run's structured observations were corrupted to a different, plausible value (drawn from that predicate's own fixed value pool) before a full replay through the real, unmodified PKB acceptance code — gold labels never touched or re-derived from the corrupted data, which is what breaks the circularity. Sanity check: the zero-corruption replay reproduced EVID-029's 475/444/31 exactly before any corrupted rate was trusted.

| Rate | Passing precision | Removed precision | Bootstrap diff (95% CI) |
|---|---:|---:|---|
| 0% | 99.1% | 0.0% | +0.991 [0.979, 1.000] |
| 5% | 99.1% | 3.1% | +0.957 [0.909, 0.986] |
| 10% | 99.0% | 10.2% | +0.878 [0.769, 0.947] |
| 20% | 98.6% | 15.0% | +0.823 [0.688, 0.911] |

**All four rates exclude zero — the filter's precision advantage survives a genuinely noisy structured source, not just the noise-free original.** A second, important finding surfaced only because the user flagged it before approval: under the published (conflict-adjusted) rule, **zero** of the contested slots corruption creates are ever admitted, at any rate — the rival ceiling (Claim 3) suppresses all of them, so the table above is measured entirely over uncontested slots. A second scoring arm with the conflict penalty disabled (support-only, immune to the ceiling by construction) resolves 81-88% of those same contested slots and still shows the filter discriminating correctly, with a smaller but still-significant margin (e.g. +0.705, CI [0.488, 0.836] at 20% corruption). **Report both: the deployed system's own numbers (conflict-adjusted, ceiling active) and the ceiling-free numbers (support-only) that show the filter's discriminative power isn't merely an artifact of the ceiling hiding the hard cases.**

**Suggested framing:** "Requiring structured corroboration for provenance-based filtering raises synthetic training-data precision from 93.5% to 100% under a noise-free structured source (EVID-029), and continues to separate correct from incorrect triples by a large, statistically significant margin when the structured source itself is corrupted at controlled rates up to 20% (EVID-042) — the filter's value is not an artifact of the structured source and gold labels sharing a generator. A companion analysis using an uncapped scoring rule (removing the confidence-aggregation rival ceiling described in Claim 3) confirms the filter still discriminates correctly even on the contested slots the ceiling would otherwise exclude from measurement entirely."

---

## Claim 1 — Unified Closed-Loop Architecture (tested end-to-end for the first time)

Every module existed and was tested standalone before this; this is the first test of the actual closed loop: extraction → PKB → synthetic data → LoRA fine-tune → **re-extraction with the fine-tuned model, fed back into the same PKB**.

Design (EVID-030): reconstructed the exact 4-iteration KB state (verified bit-for-bit reproducible), then ran one more iteration two ways from that identical starting point:

| Arm | KB size | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Iteration 4 (pre-closure baseline) | 475 | 0.9347 | 0.2440 | 0.3869 |
| Iteration 5, base model continues (control) | 480 | 0.9083 | 0.2396 | 0.3791 |
| Iteration 5, fine-tuned model closes loop (treatment) | 499 | 0.8978 | 0.2462 | 0.3864 |

**Verdict:** closing the loop is essentially flat vs. doing nothing further (-0.0005 F1, negligible). **In this single-seed comparison, TREATMENT held an advantage over CONTINUING with the un-fine-tuned model** (F1 0.3864 vs. 0.3791), which actively degrades the KB in this run (-0.0078 F1 vs. the pre-closure baseline). The fine-tuned model also contributed ~5x more net-new correct-enough content (24 vs. 5 net new above-threshold triples) at comparable precision. **Do not describe this as "reliably beats" or "reliably outperforms" — those words imply a robustness this single-seed result has not demonstrated.**

**Suggested framing:** "Integrating the fine-tuned model back into the iterative pipeline neither degrades the knowledge base nor clearly improves it in absolute terms; in this single-seed comparison it held an advantage over continued extraction without fine-tuning, though the design confounds fine-tuning with a change of base model (see caveat below) and has not been repeated across seeds."

**Caveats to state honestly:**
- **Single-seed result:** only seed 43 (the best-performing of 3 standalone seeds) was tested for TREATMENT; a weaker seed (44 was a net regression standalone) might shift this comparison. This is a single comparison, not a distribution — "reliably" is not yet an earned word for it.
- **Model-mismatch confound (verified directly against `scripts/dec006_lora_finetune.py` and EVID-030):** CONTROL uses `meta-llama/llama-3.1-8b-instruct`; TREATMENT uses the fine-tuned QLoRA adapter, which is fine-tuned **Mistral-7B-Instruct-v0.3**, not a fine-tuned Llama-3.1-8B. These are two different base model families. **The observed TREATMENT-vs-CONTROL difference is confounded by this model swap — some or all of the apparent "closing the loop helps" effect could be attributable to Mistral-7B being a different (better or worse) model than Llama-3.1-8B at this task, independent of whether fine-tuning itself contributed anything.** State this explicitly; do not attribute the full difference to fine-tuning/closing the loop without this caveat.

---

## Claim 2 — Automated Synthetic Supervision from High-Confidence Triples (real effect vs. base, with a disclosed tuning-leakage limitation)

**Headline result (EVID-040): the epochs=5 configuration is the first fine-tuning result in the project to reach conventional statistical significance vs. base — but this must be reported with the leakage caveat below, not as clean confirmatory evidence.**

**Tuning-leakage caveat (AUDIT.md A2, new — verified directly against `scripts/dec006_evaluate_adapter.py`): every evaluation in this section — the epoch/LoRA grid search AND this "confirmatory" 5-seed run — used the identical 8-product test split.** There was no independent validation set separating "which configuration to pick" from "how well does the picked configuration generalize." With only 8 products and 9 configurations tried across the grid (Stages 1-2 below), some of the apparent epochs=5 advantage is plausibly the search fitting this specific small test set rather than a fully generalizable effect. **DEC-024 (pre-registered in `Decision log.md`) specifies the correct fix — select hyperparameters on an independent validation split, confirm once on an untouched test split — but has not been run** (the user chose to proceed with manuscript writing using this honest caveat instead of spending another GPU session). **The manuscript must state this limitation explicitly wherever p=0.0028 is cited — do not present it as unqualified, clean statistical significance.**

| Seed | Precision | Recall | F1 |
|---|---:|---:|---:|
| 42 | 1.0000 | 0.1250 | 0.2222 |
| 43 | 0.4667 | 0.1250 | 0.1972 |
| 44 | 1.0000 | 0.1250 | 0.2222 |
| 45 | 1.0000 | 0.1071 | 0.1935 |
| 46 | 0.2692 | 0.1250 | 0.1707 |

Mean F1 = **0.2012** (std 0.0194) vs. base F1=0.1373. **One-sample t-test vs. base: p=0.0028** (significant). Wilcoxon signed-rank: p=0.0625 — the mathematical floor for a 5-sample test, reached because all 5 seeds improved over base.

**Important, precise scope of the claim:** a direct paired comparison against the earlier epochs=3 configuration (EVID-034, same 5 seeds) is NOT significant (paired t p=0.4461, Wilcoxon p=0.6250), despite epochs=5's higher mean (0.2012 vs. 0.1814) and notably tighter spread (std 0.0194 vs. 0.0352). **The correct claim is "epochs=5 is significantly better than the base model" — not "epochs=5 is proven significantly better than epochs=3."** Both are true findings; don't conflate them. **And per the leakage caveat above, even the "significantly better than base" claim should be qualified as selected-and-tested-on-the-same-data, not an independently confirmed result.**

**Suggested framing:** "A hyperparameter search found that extending fine-tuning from 3 to 5 epochs, with LoRA rank/alpha/learning rate unchanged, produces a statistically significant improvement over the base model (one-sample t-test, p=0.0028, n=5 seeds) on the held-out test set used for both selection and evaluation; we note this as a limitation and identify an independent validation-based confirmation as a direction for future work (Section 10). The original 3-epoch configuration, by contrast, showed only a non-significant trend (p=0.066)."

---

### Methodology and prior escalation history (for the Discussion/Methods section)

Four fine-tuning runs, escalating in rigor and sample size:

1. **EVID-026** (33 training examples, 15 optimizer steps): fine-tuning **decreased** F1 (0.3231 → 0.2264). Diagnosed as too small/short a fine-tune, not evidence against the approach.
2. **EVID-027** (90 examples via a 200-product scale-up): initially appeared to show a clean positive result — but a real train/test leakage bug was found (2 of 10 test products were also used in training) and those numbers were retracted.
3. **EVID-028 → EVID-034** (leakage fixed, extended from 3 to 5 seeds on the corrected 8-product test set — **use this final table**):

| | Precision | Recall | F1 |
|---|---:|---:|---:|
| Base | 0.1522 | 0.1250 | 0.1373 |
| Fine-tuned, seed 42 | 0.5385 | 0.1250 | 0.2029 (+0.0656) |
| Fine-tuned, seed 43 | 0.6364 | 0.1250 | 0.2090 (+0.0717) |
| Fine-tuned, seed 44 | 0.1515 | 0.0893 | 0.1124 (−0.0249) |
| Fine-tuned, seed 45 | 1.0000 | 0.1071 | 0.1935 (+0.0562) |
| Fine-tuned, seed 46 | 0.3889 | 0.1250 | 0.1892 (+0.0519) |

Mean fine-tuned F1 = 0.1814 (std 0.0394) vs. base 0.1373 — mean **+0.0441**, and the std is now *smaller* than the mean effect (reversed from the n=3 result). **4 of 5 seeds positive.** One-sample t-test: t=2.507, **p=0.066** (trending toward significance, not conventionally significant). Wilcoxon signed-rank: p=0.125 (near the n=5 test's power floor of 0.0625).

**The one clean, mechanistic finding, true across the whole series:** base, seed 42, and seed 43 all catch the *exact same* 7 true positives (identical recall) — fine-tuning's measured effect (where it helps) is **eliminating false positives** (46 → 13 → 11 total predictions), not finding new correct facts. This is a real, citable answer to professor feedback point #10 ("why precision improves significantly, why recall remains relatively unchanged").

**Suggested framing:** "Fine-tuning improved F1 in 4 of 5 seeds tested (mean +0.044), with a one-sample t-test trending toward significance (p=0.066) — a stronger, more consistent signal than an earlier 3-seed analysis, though not yet conventionally significant. The measured benefit is attributable primarily to a reduction in false-positive extractions rather than a gain in recall."

**Historical note:** p=0.066 is above the 0.05 threshold — this epochs=3 result was never conventionally significant. **It is now superseded as the paper's headline number by the epochs=5 result above (EVID-040, p=0.0028)** — keep this table for the methodology narrative ("we investigated hyperparameters and found a better configuration"), not as the primary claim. Both fine-tuning results used the pre-DEC-018 unfiltered training data (for comparability across seeds) — whether DEC-018's provenance filter changes this picture is a separate, not-yet-run comparison.

**Epoch/LoRA hyperparameter grid, new (EVID-037/038):** directly answers professor feedback point #6's previously-untested "additional training epochs" and "better LoRA hyperparameter tuning" asks — every prior run above used a fixed, never-validated epochs=3/rank=16/alpha=32/lr=2e-4. A staged search at seed 42 (same 90-example data, same test set) found:

| Epochs (rank=16, alpha=32, lr=2e-4) | Precision | Recall | F1 |
|---|---:|---:|---:|
| 2 | 0.2121 | 0.1250 | 0.1573 |
| 3 (original default) | 0.5385 | 0.1250 | 0.2029 |
| **5** | **1.0000** | 0.1250 | **0.2222** |
| 8 | 1.0000 | 0.1250 | 0.2222 (identical to 5, wasted compute) |

A follow-up LoRA grid (rank {8,32}, learning rate {1e-4,3e-4}) at epochs=5 found the **original rank=16/alpha=32/lr=2e-4 already optimal** — every alternative underperformed it. **Winning combined configuration: epochs=5, everything else unchanged.**

**The mechanistic finding holds with zero exceptions across all 9 grid runs plus base: recall is pinned at 0.1250 in every single configuration.** Epochs/rank/alpha/lr all affect only precision (suppressing false positives), never recall — the cleanest, most consistent version of this project's recurring fine-tuning mechanism finding.

**Suggested framing:** "A hyperparameter search across training epochs (2-8) and LoRA rank/alpha/learning rate found that extending training from 3 to 5 epochs improved F1, while the originally-chosen LoRA hyperparameters were already optimal in the range tested; recall remained unchanged across every configuration, confirming that additional training exclusively improves precision by suppressing false positives."

**Status update: the 5-seed confirmatory run is now done (EVID-040, seeds 43-46 added to the existing seed 42) — see the headline result at the top of this section.** epochs=5's significance vs. base (p=0.0028) is now a multi-seed finding, not a single-seed anecdote — **but see the tuning-leakage caveat at the top of this section before citing this as clean confirmatory evidence.** This is the paper's headline fine-tuning number going forward; the epochs=3 result immediately below is now the "earlier, less-tuned configuration" for methodological narrative, not the primary evidence. DEC-024 (pre-registered, not run) specifies the leakage-free follow-up if a stronger claim is needed later.

---

## Claim 4 — Feedback Controller Reduces Reliance on Manual Feedback (honest null, now tested at two scales)

- Single-seed pilot (EVID-016/019, N=20) suggested `without_feedback` beat the full pipeline — a surprising, counter-to-claim direction.
- Proper 5-seed statistical validation (EVID-020, seeds 42-46, N=20): **no significant difference** between `without_feedback`/`without_prob_kb` and the full pipeline (paired t-test/Wilcoxon, all p=0.31–0.51). The earlier single-seed direction did not replicate — with 5 seeds, `without_feedback`'s mean F1 is actually *lower* than full's, reversing the earlier apparent direction, and still not significant either way.
- **N=50 confirmatory rerun (EVID-039, DEC-023, seeds 42-46), identical design, only the product count changed:**

| Config | Held-out test F1 mean (std) | Diff vs. full | Paired t p | Wilcoxon p |
|---|---:|---:|---:|---:|
| full | 0.3451 (0.0934) | — | — | — |
| without_feedback | 0.3005 (0.1728) | -0.0446 | 0.5707 | 0.625 |
| without_prob_kb | 0.3783 (0.1744) | +0.0332 | 0.6348 | 1.000 |

**The null replicates and the measurement gets tighter at N=50, not weaker.** `full`'s variance shrank 3.6x (test F1 std: 0.335 at N=20 → 0.093 at N=50). `without_feedback`'s direction flipped sign again (positive at N=20, negative at N=50), consistent with genuine noise around a near-zero true effect rather than a real effect being masked by noise.

**Power caveat (AUDIT.md Part C, new — computed directly): do not describe this as "properly powered" without qualification.** At n=5 seeds, a paired/one-sample t-test needs Cohen's d≈1.68 for 80% power at α=0.05. Using the observed stds (0.1728/0.1744), the smallest reliably detectable mean difference is **≈0.29-0.30 F1** — a very large effect. **This design rules out large effects only; it cannot distinguish "no effect" from "a small-to-moderate effect that this sample size can't detect."**

**Verdict:** no ablation effect **of ≈0.3 F1 or larger** detected at either N=20 or N=50. Per DEC-023's own pre-registered commitment, this is the final answer — no further re-runs chasing significance — but the manuscript should state the detectable-effect-size limitation alongside the null, not present it as a general "feedback doesn't matter" conclusion.

**Suggested framing:** "A five-seed statistical validation, repeated at both N=20 and N=50 products, found no significant difference in F1 between the full pipeline and ablated variants without the feedback controller or probabilistic knowledge base (all p ≥ 0.34 across both scales). Variance dropped substantially at the larger scale (full's held-out test F1 std: 0.335 → 0.093). At n=5 seeds, this design can detect only effects of approximately 0.3 F1 or larger (80% power, α=0.05); the null result rules out a large effect but cannot rule out a smaller one."

**This claim's correct manuscript treatment:** explicit reframing as "proposed and tested at two independent scales; no effect of ≈0.3 F1 or larger detected either time" — not an unqualified assertion that feedback has no effect, and not something that needs a further, larger re-run (already addressed at the scales tested).

---

## Foundational correction — Official CaRB Benchmark Scores (use these, not the old numbers)

**Every CaRB number reported before EVID-031 used this project's own internal exact-match evaluator, which undercounts real performance by roughly 4-8x** due to subject-boundary-mismatch scoring artifacts (e.g., penalizing a predicted `"all households"` against gold `"32.7% of all households"` as entirely wrong, despite being the same fact).

**Full-scale official scores (EVID-035, N=548 of CaRB's 641 test-split sentences — the headline number, use this):**

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| DeepSeek-V3.2 (external baseline) | 0.713 | 0.477 | **0.571** |
| Llama-3.1-8B-instruct (SLDE-AFT's own extractor) | 0.589 | 0.387 | **0.467** |

Cost: $0.0520 total for both systems at full scale.

**30-sentence pilot scores (EVID-031/032, historical — kept for reference, not the headline anymore)** — also covering 3 more SOTA systems not yet re-run at full scale:

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| DeepSeek-V3.2 (external baseline) | 0.713 | 0.458 | 0.558 |
| Gemini 2.5 Pro | 0.773 | 0.401 | 0.528 |
| Claude Sonnet 5 | 0.642 | 0.446 | 0.527 |
| GPT-4o | 0.736 | 0.384 | 0.504 |
| Llama-3.1-8B-instruct (SLDE-AFT's own extractor) | 0.652 | 0.401 | 0.496 |

**The pilot numbers held up well at full scale** — both deltas are small (Llama -0.029, DeepSeek +0.013), in opposite directions, no dramatic shift. GPT-4o/Claude/Gemini were not re-run at full scale (cost-deferred, ~$12.66 combined for full 5-system parity — optional, not required); their pilot numbers above are still the only ones available for those three.

(Internal-evaluator numbers, superseded since EVID-031 and not to be used as headline figures.)

**Use the full-scale (N=548) numbers above anywhere CaRB results are cited in the paper** — no longer caveat this as "pilot only."

**Important, honest finding — state this explicitly, don't omit it:** SLDE-AFT's own extractor (Llama-3.1-8B) is the **weakest of all 5 systems tested**, though the gap is modest (~12% relative, top to bottom). This does not undermine the paper's actual novelty claims — the Noisy-Or aggregation, closed-loop architecture, and provenance filtering all operate *on top of* whatever base extractor is used, and SLDE-AFT deliberately uses a smaller, cheaper, open-weight model rather than a larger proprietary one. Frame it as: "the architecture's value lies in what it does with the base extractor's outputs, not in having the single strongest raw extractor."

**Practical note worth a sentence in Methods:** Gemini 2.5 Pro required a much larger token budget (3072 vs. 512 for the other four models) and still had a 5/30 error rate on this task — reasoning-heavy models may need more generous generation budgets and more robust output parsing for structured extraction than non-reasoning models need for the same task.

**Caveat (updated):** now 548 of CaRB's 641 test-split sentences (85.5%) for Llama/DeepSeek — no longer a pilot-scale limitation. The ~93-sentence gap is a pre-existing whitespace/quoting mismatch between CaRB's raw sentence file and its gold-annotation file, not a deliberate exclusion.

**REBEL was attempted and found genuinely incompatible with CaRB's evaluation, not simply "not run"** (EVID-033) — worth a sentence in the paper's limitations, not silence. REBEL (`Babelscape/rebel-large`) is a *closed* relation-extraction model trained on Wikidata's fixed schema (canonical predicates like `"point in time"`, `"has part"`, `"subclass of"` and linked entity names), fundamentally different from CaRB's *open*-domain span-based extraction (free-text predicates copied verbatim from the sentence). Scoring REBEL's output against CaRB's span matcher gave F1=0.0000 — not because REBEL performs badly, but because the two systems represent facts in incompatible formats; a fair comparison would need an entity-linking/relation-verbalization mapping layer, out of scope for this pilot. **Do not cite REBEL's raw F1 anywhere — cite this qualitative finding instead.** GenIE and InstructUIE likely share this same incompatibility (also schema/KB-grounded); DyGIE++ remains untried (AllenNLP dependency).

---

## Other supporting results

**Systematic error analysis (DEC-007, EVID-022):** zero pure false negatives in the product-domain train set (every gold fact was observed at least once across 4 iterations) — recall failures are recoverable, not fundamental misses. Conflict adjustment overwhelmingly resolves hallucination-vs-hallucination conflicts (108 of 117), not correct-vs-incorrect ones (1 of 117) — report this nuance wherever the conflict-resolution mechanism is described.

**Scalability (DEC-008, EVID-023):** runtime scales linearly with N (no quadratic blowup) up to N=200; mean per-document latency stays flat (~4.0s) regardless of accumulated KB size (grew to 2,814 entries) — the key positive scalability claim. Memory measurement from this pass is unusable (methodology flaw: sequential runs in one process contaminate GC-affected deltas) — don't cite memory numbers from EVID-023.

**Domain generalization — BioRED biomedical pilot (DEC-009, EVID-024):** strict exact-match F1=0.0074 is misleadingly low (mostly a gold-construction/boundary-mismatch artifact, same family of issue as the CaRB correction above). Relaxed containment-match F1=0.1029 (14x more true positives found) is the fairer read: the biomedical domain is genuinely harder than the product domain, but not a near-total failure. **Report both numbers together with this explanation — never the strict number alone**, which would be a misleading characterization.

**Framework-level validation on DocRED (DEC-020, EVID-030's public-data counterpart, new):** the first time the actual PKB/Noisy-Or framework — not just the raw extractor — was tested on public data, using a 15-document pilot from DocRED's human-annotated dev split (189 gold triples, 356 observations, cost $0.00131).

| | Precision | Recall | F1 |
|---|---:|---:|---:|
| Naive baseline (no aggregation) | 0.034 | 0.032 | **0.033** |
| PKB-aggregated (≥0.70 confidence) | 0.333 | 0.005 | **0.010** |

**Honest verdict: aggregation raises precision ~10x but collapses recall so far that F1 gets worse, not better** — a real, diagnosed negative result, not a null one. Root cause traced directly (not just observed): the PKB's aggregation key requires an EXACT string match on subject/predicate/object. In the product domain, the same fact is named consistently across sources, so repeated observations corroborate each other. On open Wikipedia text, the model phrases the same fact slightly differently across its own evidence sentences often enough that they almost never produce byte-identical triples — so genuine corroboration is rarely recognized as such, and almost nothing crosses the accept threshold.

**Hyperparameters differ from the product-domain runs (state this explicitly when comparing the two settings):** the DocRED pilot used **shrinkage=0.5, threshold=0.70**, versus **shrinkage=0.75, threshold=0.88** in the canonical product-domain run (`scripts/dec003_product_probkb_run.py`). This was a deliberate, documented recalibration for DocRED's sparser evidence structure (see DEC-020), not an oversight — but it means the two settings' numbers are not directly comparable as an apples-to-apples test of the same aggregation configuration on two domains; the domain-transfer finding above is about the matching-key mechanism, not a controlled hyperparameter comparison.

**Suggested framing:** "Testing the framework's Noisy-Or aggregation on DocRED reveals a real limitation: exact-string-match corroboration, effective in the product domain's consistently-named entities, fails to recognize the same fact when phrased differently across evidence sentences in open text — aggregation improves precision roughly 10-fold but at a severe recall cost, indicating the current implementation does not transfer to open-domain multi-sentence text without an entity-linking or paraphrase-aware matching key."

This is a genuine, citable answer to professor feedback point #10 ("where the framework may fail") — use it in Limitations, not just Discussion.

**TACRED — scoped, then explicitly declined (DEC-021):** professor feedback point #1 names TACRED; a $25 LDC license fee was confirmed as the actual (modest) cost, but the user chose not to pursue it given CaRB + DocRED already cover two genuinely different public-benchmark task types (open extraction vs. closed-schema document-level RE) at both the extractor and framework level. **State this explicitly in Limitations, do not omit it silently:** *"TACRED requires a paid LDC license; given resource constraints, we prioritized cost-free public benchmarks (CaRB, DocRED) spanning open-domain and closed-schema, document-level extraction."*

---

## Structural manuscript issues (independent of the 5 claims — fix before submission)

- **All of SLDE.pdf's reported Table 7-9 results used `openrouter/auto`** (unpinned model routing), per the manuscript's own Section 5.4 — this is not just the CaRB pilot's problem. The headline numbers currently in the draft (Precision 0.9000, "84% gain," Recall=1.0000) are **not a reproducible measurement of any specific named model**. This is exactly the single-run/unpinned-methodology problem professor feedback point #5 criticizes. All of the pinned-model numbers in this file are the fix — they will not match the old draft's numbers, and that's expected, not a regression.
- **The manuscript is missing Sections 8-11** (Ablation Analysis, Discussion, Limitations/Future Work, Conclusion) — it currently jumps from Section 7.5 straight to References despite the introduction promising them. This file's per-claim sections above are meant to seed exactly those sections once writing begins.
- **The old notebook's B3 baseline and Table-9 "Iterative FT" results come from two different, inconsistent code paths** (found while porting DEC-006) — do not cite old B3/B4/Table-9 numbers from the notebook without checking which code path actually produced them.
- **`refrence master copy.xlsx` (the annotated reference database) is not committed to any git branch** — it exists only as a local file on the working machine. If a fresh session or collaborator needs it, it must be shared separately; it will not be found by reading the repo alone.
- **Two confirmed bibliography errors in the existing reference list, both verified directly:** (1) reference [19] and reference [54] are the same paper — Lewis et al., "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," NeurIPS 2020 — listed twice under different numbers; consolidate to one entry and update all in-text citations accordingly. (2) Reference [48] (TACRED, "Position-aware Attention and Supervised Data Improve Slot Filling," Zhang et al.) is listed as ACL 2017; confirmed via the paper's ACL Anthology record (ID D17-1004) that it was published at **EMNLP 2017**, not ACL 2017 — correct the venue.

---

## Mapping to professor_feedback.md's 13 points (quick reference)

| # | Point | Where it's addressed here |
|---|---|---|
| 1 | Strengthen experimental evaluation (public benchmarks) | CaRB now full-scale (DEC-001, EVID-035, N=548); DocRED framework-level pilot (DEC-020, new — tests the framework, not just the extractor); BioRED domain pilot (DEC-009). TACRED scoped and explicitly declined with a documented reason (DEC-021). REBEL-benchmark (the dataset)/Universal-IE still not attempted, lowest priority |
| 2 | Compare against SOTA methods | DeepSeek-V3.2, GPT-4o, Claude Sonnet 5, Gemini 2.5 Pro all done (DEC-002, EVID-031/032/035) — 4 of 8 named systems covered, DeepSeek now at full CaRB scale too. REBEL attempted and found task-incompatible with CaRB scoring (EVID-033, real finding, not a gap). GenIE/InstructUIE (likely same incompatibility)/DyGIE++ (AllenNLP) not attempted |
| 3 | Improve mathematical contribution | DEC-003's Noisy-Or result — a real, positive real-data finding, but **not an unqualified "strongest claim"** (in tension with the N=50 ablation, AUDIT.md A1); real-data calibration (ECE=0.3332) and computational complexity analysis now done (EVID-036). The rival-ceiling failure mode is now empirically confirmed AND a corrected rule (source-count) is tested and shown to help, on two datasets (DEC-026, EVID-041) — a second candidate fix (evidence-share) tested and found to be a null, reported honestly. Formal derivation/boundedness proof/convergence discussion (steps 2-4) still needed — pure math-writing, not experiments |
| 4 | Proper ablation study | DEC-004/005 — done, honest null result |
| 5 | Statistical validation | DEC-005/023 (ablation, 5 seeds at both N=20 and N=50 — null result, but only rules out effects ≥~0.3 F1, AUDIT.md Part C) and DEC-006/022 (fine-tuning, 5 seeds, **epochs=5 config significant at p=0.0028 vs. base, but with a disclosed tuning-leakage limitation**, EVID-040/AUDIT.md A2) — both now have real numbers, both need their respective caveats stated |
| 6 | Improve fine-tuning section | DEC-006/018/022 — a real result achieved (p=0.0028 vs. base, EVID-040), previously-untested asks (additional epochs, LoRA hyperparameter tuning) fully investigated via a systematic grid (DEC-022). **Must disclose the tuning-leakage limitation (AUDIT.md A2) — the same test set was used for both hyperparameter selection and confirmation; DEC-024 is pre-registered to fix this but not yet run** |
| 7 | Add error analysis with examples | DEC-007 (general) + DEC-018/EVID-029 (concrete provenance-filtering examples, exactly what this point asks for) |
| 8 | Evaluate scalability | DEC-008 — done, positive result, memory data unusable |
| 9 | Validate on multiple domains | DEC-009 (BioRED) — one additional domain, pilot scale only |
| 10 | Strengthen discussion (why precision/recall behave as they do) | Claim #2's precision-vs-recall mechanistic finding directly answers this |
| 11 | Improve novelty positioning | Not started (writing task, DEC-011) |
| 12 | Improve reproducibility | Not started (packaging task, DEC-012) — this file plus the Evidence log's EVID-xxx trail already provide most of the substance |
| 13 | Refine writing | Not started (writing task, DEC-013) — deferred until all experiments are done, per standing project rule |
