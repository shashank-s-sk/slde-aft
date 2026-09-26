# Results Summary — SLDE-AFT

**Purpose of this file:** a single, self-contained, paper-ready summary of every real result this project has produced, with honest interpretation for each. Written so it can be pasted directly into any LLM (or read by a human) when drafting the manuscript's Results/Discussion sections, with no need to cross-reference `Decision log.md` / `Evidence log.md` for the numbers themselves — those two files remain the detailed, process-oriented working logs (rationale, full limitations, next steps); this file is the distilled, citable output.

**How to keep this in sync:** whenever a new EVID-xxx entry changes a claim's status or headline number, update the corresponding section here too. `Decision log.md`'s STATUS DASHBOARD table is the fast-scan index; this file is the narrative version meant for writing prose from.

**Do not invent or round numbers beyond what's shown here.** Every number below is sourced from a specific EVID-xxx entry in `Evidence log.md` — cite that EVID number if asked where a figure came from.

---

## The 5 claimed novelty contributions — final status

| # | Claim | Verdict | Headline number |
|---|---|---|---|
| 1 | Unified closed-loop architecture | Tested end-to-end; flat vs. baseline, beats not-fine-tuning | F1 0.3869 → 0.3864 (loop) vs. 0.3791 (no fine-tune) |
| 2 | Automated synthetic supervision | **Negative on the primary, leakage-free, pre-registered test — the earlier positive result did not replicate** | Primary (DEC-027/EVID-044, paired bootstrap over 40 held-out test products, leakage-free validation/test split): point estimate **-0.0214**, 95% CI **[-0.0417, -0.0034]** — excludes zero on the negative side. Supersedes EVID-040's exploratory p=0.0028 result (tuned on its own test set; now historical only, see Claim 2 below) |
| 3 | Noisy-Or math contribution | A real, positive real-data finding, **but not an unqualified "strongest" claim** — it sits in tension with the N=50 ablation | +0.043 F1 (conflict-adjusted vs. **raw/unadjusted Noisy-Or**, not a naive/no-aggregation baseline — AUDIT.md A1); real-data ECE=0.3332 (EVID-036). **The N=50 ablation (EVID-039) found removing this mechanism (`without_prob_kb`) scored numerically as well as or better than keeping it** — report both findings together |
| 4 | Feedback Controller reduces manual reliance | Null at 30 seeds; effects ≥≈0.08 F1 ruled out | DEC-029/EVID-045 (N=50, 30 seeds): without_feedback −0.032 [−0.090, +0.023], p=0.28; without_prob_kb +0.034 [−0.010, +0.082], p=0.16 (no-retry primary; +0.048 [−0.003, +0.101] with retries). Achieved MDE 0.070–0.086 F1, vs. ≈0.29 at the earlier 5 seeds (EVID-020/039). The probabilistic-KB point estimate favours removing it |
| 5 | Provenance actively filters training data | A real precision result, **now also validated under a noisy (not just noise-free) structured source** | Precision 93.5% → 100% vs. `gold_structured` (92.6% → 99.1% vs. `gold_unstructured` — see Claim 5 below for why these differ; `gold_structured` is primary, drops 31/475 wrong triples). DEC-028 (EVID-042) tests the original circularity concern directly: corrupting the structured source 0-20% still shows a large, statistically significant precision advantage in every case |

Plus two foundational corrections: **official CaRB benchmark scores are 4-8x higher than every previously-reported internal-evaluator number**, and CaRB is now at full 548-sentence scale, not a 30-sentence pilot (see below) — use the official, full-scale numbers, not the internal or pilot ones, anywhere CaRB is cited.

**All four caveats above come from `AUDIT.md` (2026-09-20/21), a methodological review that checked every headline claim in this file directly against the underlying code and data. Where this file and `AUDIT.md` conflict, `AUDIT.md`'s corrected framing is authoritative — the sections below have been updated to match it.**

---

## Claim 3 — Noisy-Or Conservative Confidence Aggregation (the math contribution)

**A real, positive real-data finding — but do NOT call it "the strongest, most defensible claim in the paper" or any equivalent unqualified superlative. AUDIT.md found this framing is in direct tension with the project's own ablation evidence; report both sides together.**

- Real-data check (EVID-014): the conservative Noisy-Or + mutual-exclusivity-penalty aggregation improves F1 by **+0.043** in aggregate **compared to raw (unadjusted) Noisy-Or support** — NOT compared to a naive/no-aggregation baseline. Raw Noisy-Or is itself a non-trivial aggregation mechanism; do not describe this comparison as "vs. naive," on real (not synthetic) product-domain data.
- Full instrumented run (EVID-013, 155 API calls, $0.00259): train-set iteration F1 progressed **0.3668 → 0.3682 → 0.2894 → 0.4183** across 4 iterations — non-monotonic and not fully explained (flagged for future error analysis, see DEC-007). Held-out F1: **val 0.5970** (n=5), **test 0.1970** (n=10).
- Toy/scaled synthetic validation (EVID-005/009) also supports the mechanism working as designed.
- **Direct tension with the project's own ablation (AUDIT.md A1, new):** DEC-023's N=50 ablation (EVID-039) found `without_prob_kb` (max-merge, i.e. this mechanism *removed* from the full closed loop) scored **numerically higher** than `full` on held-out test F1 (0.3783 vs. 0.3451). The 30-seed extension (DEC-029/EVID-045) confirms the direction: +0.034, 95% CI [−0.010, +0.082], p=0.16 (no-retry primary). That is not significant, so this still isn't "Noisy-Or hurts" — but it directly contradicts describing this as the project's strongest, most defensible result. **Report both the positive EVID-014 finding and this ablation tension together, honestly.**

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

| | n | Precision vs. `gold_structured` (primary) | Precision vs. `gold_unstructured` |
|---|---:|---:|---:|
| Unfiltered | 475 | 93.5% | 92.6% |
| Passes filter (has structured corroboration) | 444 | **100.0%** | 99.1% |
| Fails filter (unstructured-only) | 31 | **0.0%** — every single one wrong | 0.0% |

- **Mechanistic bonus finding:** the 31 dropped triples are almost all generic device-category nouns ("laptop device", "tablet device") standing in for the real product name, repeated 2-21 times each and mistaken by Noisy-Or aggregation for corroborating evidence. This *directly explains* (not just correlates with) the "subject-copying" failure mode seen in the DEC-006 fine-tuned model's outputs — it learned from these exact hallucinated examples.
- **Original circularity caveat (AUDIT.md A3 — verified directly against `src/datasets/product_generator.py`):** in this synthetic dataset, the gold labels used to score the filter are constructed *from the same generator* as the structured source data the filter checks against, so "requires structured corroboration" and "matches gold" were, by construction, close to the same test in the EVID-029 measurement above.
- **Gold-set caveat, found by `scripts/reproduce_all.py` (DEC-030, new — report, don't silently reconcile):** EVID-029's 93.5%→100% figures score against `gold_structured` (all 13 structured facts per product, reconstructed independently inside `scripts/dec018_provenance_filter_validation.py`), **not** against the same snapshot's own `gold_label` column, which reflects `gold_unstructured` (the subset of facts actually mentioned in generated text — the set DEC-026/028's own gold reconstruction uses). Recomputing against `gold_label` instead gives 92.6%→99.1%, not 93.5%→100% — a real ~0.9-point difference on the headline "100%" figure, not a rounding artifact. The published 93.5%→100% number is correct and reproducible under EVID-029's own stated method; the point is that two different columns in this project both get called "gold," and Claim 5's number is the `gold_structured` one specifically. State this explicitly wherever the 100% figure is cited, the same way the recall-denominator distinction is already stated for Claim 1/DEC-026.

**DEC-028 (EVID-042, new): the filter tested directly under a noisy structured source, not just argued to need it.** 0%/5%/10%/20% of the 200-product run's structured observations were corrupted to a different, plausible value (drawn from that predicate's own fixed value pool) before a full replay through the real, unmodified PKB acceptance code — gold labels never touched or re-derived from the corrupted data, which is what breaks the circularity. Sanity check: the zero-corruption replay reproduced EVID-029's 475/444/31 exactly before any corrupted rate was trusted.

| Rate | Passing precision | Removed precision | Bootstrap diff (95% CI) |
|---|---:|---:|---|
| 0% | 99.1% | 0.0% | +0.991 [0.979, 1.000] |
| 5% | 99.1% | 3.1% | +0.957 [0.909, 0.986] |
| 10% | 99.0% | 10.2% | +0.878 [0.769, 0.947] |
| 20% | 98.6% | 15.0% | +0.823 [0.688, 0.911] |

**All four rates exclude zero — the filter's precision advantage survives a genuinely noisy structured source, not just the noise-free original.** A second, important finding surfaced only because the user flagged it before approval: under the published (conflict-adjusted) rule, **zero** of the contested slots corruption creates are ever admitted, at any rate — the rival ceiling (Claim 3) suppresses all of them, so the table above is measured entirely over uncontested slots. A second scoring arm with the conflict penalty disabled (support-only, immune to the ceiling by construction) resolves 81-88% of those same contested slots and still shows the filter discriminating correctly, with a smaller but still-significant margin (e.g. +0.705, CI [0.488, 0.836] at 20% corruption). **Report both: the deployed system's own numbers (conflict-adjusted, ceiling active) and the ceiling-free numbers (support-only) that show the filter's discriminative power isn't merely an artifact of the ceiling hiding the hard cases.**

**Suggested framing:** "Requiring structured corroboration for provenance-based filtering raises synthetic training-data precision from 93.5% to 100% (92.6% to 99.1% against the narrower `gold_unstructured` set) under a noise-free structured source (EVID-029), and continues to separate correct from incorrect triples by a large, statistically significant margin when the structured source itself is corrupted at controlled rates up to 20% (EVID-042) — the filter's value is not an artifact of the structured source and gold labels sharing a generator. A companion analysis using an uncapped scoring rule (removing the confidence-aggregation rival ceiling described in Claim 3) confirms the filter still discriminates correctly even on the contested slots the ceiling would otherwise exclude from measurement entirely."

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

## Claim 2 — Automated Synthetic Supervision from High-Confidence Triples (negative on the primary, leakage-free test — supersedes the earlier positive result)

**Headline result (DEC-027/EVID-044): a leakage-free replication — independent validation split for hyperparameter selection, untouched 40-product test split for confirmation — finds a **negative** effect on the pre-registered primary metric: the 95% CI excludes zero on the negative side.** This result was pre-registered specifically to fix AUDIT.md A2 (below) and, per that pre-registration's own "what counts as a null" clause, **supersedes EVID-040's exploratory p=0.0028 result as the manuscript's headline fine-tuning claim.** EVID-040 is not deleted. It is demoted to a superseded exploratory result, with the caveat that its hyperparameters were tuned on its own test set (see the methodology history further down this section).

**Primary, pre-registered test — paired bootstrap over the 40 held-out test products** (mean per-product F1 difference, fine-tuned minus base, averaged across 5 confirmatory seeds, 10,000 resamples): point estimate **-0.0214**, 95% CI **[-0.0417, -0.0034]** — excludes zero, on the negative side. The pre-registered positive criterion (CI excludes 0 AND point estimate ≥ +0.03) is not met.

**Winning configuration** (selected on the 20-product validation split only, never the test split): epochs=8, rank=16/alpha=32/lr=2e-4 (the original default LoRA setting), validation F1=0.7444. It won outright: the runners-up (rank=32; lr=3e-4) scored 0.7336, 0.0108 behind, just outside the pre-registered 0.01 tie tolerance, so the tie-break rule never applied. **Selection was decided by precision alone.** Validation recall was flat (0.593-0.600) across every configuration with ≥5 epochs, the top three were within 0.011 F1 on 20 products, and the winner was separated only by its false-positive count (0 vs. 5). F1-based selection therefore picked the most conservative adapter, the one that made the fewest validation predictions (83).

| Seed (test split) | Precision | Recall | F1 |
|---|---:|---:|---:|
| Base (fresh eval) | 0.5677 | 0.4643 | 0.5108 |
| 42 | 0.8722 | 0.4143 | 0.5617 |
| 43 | 0.8939 | 0.4214 | 0.5728 |
| 44 | 0.8207 | 0.4250 | 0.5600 |
| 45 | 0.7733 | 0.4143 | 0.5395 |
| 46 | 0.7041 | 0.4250 | 0.5301 |

**A genuine tension, reported rather than resolved by picking the favorable number:** the secondary, descriptive whole-set (micro) comparison goes the other way — mean F1=0.5528 vs. base 0.5108, one-sample t p=0.0058 (Wilcoxon p=0.0625, the n=5 floor). **The primary (per-product, macro) bootstrap is negative and significant; the secondary (whole-set, micro) comparison is positive and significant.** Fine-tuning raises precision sharply (0.568→0.70-0.89) but **lowers recall in every single seed** (0.464 base vs. 0.414-0.425 across all 5 seeds). A per-product decomposition (EVID-044) shows where each statistic registers the change. Every test product has exactly 7 gold triples.

- **Micro rises because false positives disappear on products the base model already failed.** On 21 of 40 products the base model scores F1=0 while still making 134 false positives. Fine-tuning cuts these to ~33, often by predicting nothing. Pooled micro precision credits every removed false positive, but those products stay at F1=0 per product, so macro does not move.
- **Macro falls because of the per-product recall loss.** On the 19 products the base model gets partly right, true positives fall 130 → 117.6 (seed mean) with false positives already near zero, so nothing offsets the loss. 28 products are unchanged, 9 are worse (~1.4 true positives lost each), and 3 are better.

This is the first recall drop that is consistent across all seeds on a leakage-free split. Recall had moved before (EVID-026 0.30→0.17; EVID-028 seed 44 0.125→0.089). But on the 8-product set used by EVID-034/037/038/040 the base model found only 7 of 56 gold triples, so a ~10% loss of true positives was less than one triple and could not show up. Here it is 11-14 triples in every seed.

**Micro counting convention.** Reported micro figures pool all products' predictions into one global set before scoring (`src/evaluator.py`), so an identical wrong triple repeated across products counts as one false positive. This is the whole of the 99 (global) vs. 137 (per-product) base false-positive gap: the base model repeats 38 wrong triples across products. True positives are identical under both conventions. Per-product counting gives base F1=0.4753 vs. seed mean 0.5460 (+0.071, t p=0.0022); global counting (reported) gives 0.5108 vs. 0.5528 (+0.042, p=0.0058). Neither affects the primary, which already scores per product.

The micro result is secondary and descriptive; it is not the headline. The pre-registration named the paired bootstrap as primary specifically to avoid this kind of aggregate-level result being taken at face value, so **the primary's null is the reported result.**

**Suggested framing:** "An earlier, smaller-scale exploration (8 test products, same split used for both hyperparameter selection and confirmation) found a statistically significant fine-tuning improvement (p=0.0028). A larger, properly separated replication (20-product validation split for selection, 40-product held-out test split for confirmation, pre-registered paired bootstrap as the primary test) does not confirm this effect — the 95% CI on the primary metric excludes zero on the negative side. Fine-tuning raises precision sharply but lowers recall in every seed, and the net per-product effect is a small, statistically supported decline. The pooled whole-set F1 still rises, but only because fine-tuning removes false positives on products where the base model found nothing correct. Validation-based selection, where recall was flat across configurations, chose the most conservative adapter, which contributes to the recall loss. We report this negative result as the current evidence."

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

**Historical note:** p=0.066 is above the 0.05 threshold — this epochs=3 result was never conventionally significant. It was later followed by EVID-040 (epochs=5, p=0.0028), and **both are now superseded by EVID-044's negative leakage-free result** — keep this table for the methodology narrative ("we investigated hyperparameters and found a better configuration"), not as the primary claim. Both fine-tuning results used the pre-DEC-018 unfiltered training data (for comparability across seeds) — whether DEC-018's provenance filter changes this picture is a separate, not-yet-run comparison.

**Epoch/LoRA hyperparameter grid, new (EVID-037/038):** directly answers professor feedback point #6's previously-untested "additional training epochs" and "better LoRA hyperparameter tuning" asks — every prior run above used a fixed, never-validated epochs=3/rank=16/alpha=32/lr=2e-4. A staged search at seed 42 (same 90-example data, same test set) found:

| Epochs (rank=16, alpha=32, lr=2e-4) | Precision | Recall | F1 |
|---|---:|---:|---:|
| 2 | 0.2121 | 0.1250 | 0.1573 |
| 3 (original default) | 0.5385 | 0.1250 | 0.2029 |
| **5** | **1.0000** | 0.1250 | **0.2222** |
| 8 | 1.0000 | 0.1250 | 0.2222 (identical to 5, wasted compute) |

A follow-up LoRA grid (rank {8,32}, learning rate {1e-4,3e-4}) at epochs=5 found the **original rank=16/alpha=32/lr=2e-4 already optimal** — every alternative underperformed it. **Winning combined configuration: epochs=5, everything else unchanged.**

Recall was 0.1250 in every configuration of this grid and in the base model. **This does not show that fine-tuning leaves recall unchanged.** The base model found only 7 of 56 gold triples, so a ~10% true-positive loss (the size EVID-044 measured) is less than one triple. On the larger 280-triple test split, recall fell in every seed (EVID-044).

**Historical only (superseded; tuned on its own test set):** this grid and EVID-040 selected and confirmed hyperparameters on the same 8-product test set. Do not cite the epochs=5 gain or the p=0.0028 confirmatory result as a current finding. They belong only in the methodology narrative, as the exploration that DEC-027/EVID-044 replaced with a leakage-free replication.

**Status update: EVID-040 (epochs=5, p=0.0028 vs. base, 8-product test split used for both selection and confirmation) is now historical context, not the headline result.** DEC-024's pre-registered leakage-free follow-up was executed as DEC-027 (EVID-044, above): an independent 20-product validation split for hyperparameter selection and an untouched 40-product test split for confirmation. **That leakage-free replication does not confirm a positive effect on its primary metric (95% CI [-0.0417, -0.0034], negative) — see the headline result at the top of this section, which is now the paper's primary fine-tuning claim.** This subsection's EVID-026 through EVID-038 tables remain useful for the methodology narrative ("we investigated hyperparameters and progressively tightened the evaluation"), not as the primary evidence.

---

## Claim 4 — Feedback Controller Reduces Reliance on Manual Feedback (null at 30 seeds; effects of ~0.08 F1 or larger ruled out)

- Single-seed pilot (EVID-016/019, N=20) suggested `without_feedback` beat the full pipeline — a surprising, counter-to-claim direction.
- Proper 5-seed statistical validation (EVID-020, seeds 42-46, N=20): **no significant difference** between `without_feedback`/`without_prob_kb` and the full pipeline (paired t-test/Wilcoxon, all p=0.31–0.51). The earlier single-seed direction did not replicate — with 5 seeds, `without_feedback`'s mean F1 is actually *lower* than full's, reversing the earlier apparent direction, and still not significant either way.
- **N=50 confirmatory rerun (EVID-039, DEC-023, seeds 42-46), identical design, only the product count changed:**

| Config | Held-out test F1 mean (std) | Diff vs. full | Paired t p | Wilcoxon p |
|---|---:|---:|---:|---:|
| full | 0.3451 (0.0934) | — | — | — |
| without_feedback | 0.3005 (0.1728) | -0.0446 | 0.5707 | 0.625 |
| without_prob_kb | 0.3783 (0.1744) | +0.0332 | 0.6348 | 1.000 |

**The null replicates and the measurement gets tighter at N=50, not weaker.** `full`'s variance shrank 3.6x (test F1 std: 0.335 at N=20 → 0.093 at N=50). `without_feedback`'s direction flipped sign again (positive at N=20, negative at N=50), consistent with genuine noise around a near-zero true effect rather than a real effect being masked by noise.

**Power caveat at n=5 (AUDIT.md Part C):** at 5 seeds a paired t-test needs Cohen's d≈1.68 for 80% power at α=0.05, so the 5-seed design could only detect effects of **≈0.29-0.30 F1**. This was the reason for DEC-029.

**30-seed extension (DEC-029, EVID-045 — this is now the headline ablation result).** Same N=50 design, 25 new seeds (47-71) added to DEC-023's 42-46, only the three configs below, cost $0.24. Held-out test F1, paired comparisons against `full` over 30 seeds (95% CI: paired bootstrap over seeds, 10,000 resamples):

| Config | F1 mean (sample SD) | Diff vs. full [95% CI] | Paired t(29), p | Wilcoxon p | Seeds above full | Achieved MDE (condition SD / paired-diff SD) |
|---|---:|---|---:|---:|---:|---:|
| full | 0.3633 (0.1629) | — | — | — | — | — |
| without_feedback | 0.3311 (0.1534) | **-0.032 [-0.090, +0.023]** | -1.09, 0.28 | 0.38 | 13/30 | 0.081 / 0.085 |
| without_prob_kb (**primary: no retries**) | 0.3977 (0.1626) | **+0.034 [-0.010, +0.082]** | 1.43, **0.16** | 0.21 | 18/30 | 0.086 / 0.070 |
| without_prob_kb (retry-inclusive) | 0.4108 (0.1609) | +0.048 [-0.003, +0.101] | 1.77, 0.087 | 0.15 | 18/30 | 0.085 / 0.078 |

- **Why the no-retry figure is primary for without_prob_kb.** The runner inherits DEC-023's rule of re-running any (config, seed) run with ≥20% failed calls, retrying only the failed ones. Failed calls here are unparsable model output; every API call returned HTTP 200. Four runs triggered the rule, and **three of the four were without_prob_kb runs**. **No `full` run triggered it.** In each of those three without_prob_kb runs the retry raised held-out F1 (seed 53: 0.407→0.492; seed 68: 0.248→0.489; seed 71: 0.324→0.390). So the rule was applied unevenly and **biased the comparison in the direction of the observed effect**. The no-retry figure avoids that bias. It does not remove every difference between configs: without_prob_kb also has a somewhat higher failed-call rate overall (9.6% vs. 6.4% for full), which, if anything, works against it in the no-retry version. The feedback-controller result is identical under both versions: its one triggering run, seed 59, kept the same held-out F1 after the retry.
- **How strong the null is now:** the achieved minimum detectable effect (paired t-test, 80% power, α=0.05, required Cohen's d=0.529 at n=30) is **0.070-0.086 F1** across both comparisons and both SD methods. At 5 seeds it was **≈0.29**. The 30-seed null therefore rules out effects of either module of roughly **0.08 F1 or larger**, about 3.5x smaller than before. Smaller effects are still not ruled out.
- **Feedback controller: a clean null.** -0.032, 95% CI [-0.090, +0.023], p=0.28. The point estimate slightly favours keeping the controller, but the data are compatible with no effect.
- **Probabilistic KB: the point estimate favours *removing* it.** Removing it gives +0.034 (no retries) or +0.048 (with retries), and the CI's lower bound is just below zero (-0.010 / -0.003). So **the paper cannot claim that the probabilistic KB improves held-out F1.** This agrees with two independent results:
  - **DEC-026 (EVID-041):** max-merge (R1) matched or exceeded the published Noisy-Or rule (R2). It exceeded R2 at each rule's own F1-selected threshold, and was not significantly different at the shared τ=0.88 threshold.
  - **The rival ceiling (Claim 3):** the published rule structurally blocks every contested single-valued slot while a rival value exists. That is a mechanism that can hold back recall that max-merge does not. This consistency is not a demonstrated cause of the ablation difference.
- The two seed blocks agree in sign and size: the original 5 seeds give -0.045 / +0.033, and the 25 new seeds give -0.030 / +0.050 (retry-inclusive).

**Verdict:** no significant effect of either module at 30 seeds. Effects of ≈0.08 F1 or larger are ruled out for both at 80% power. For the probabilistic KB, the evidence leans the *other* way: removing it does not hurt and may help slightly. Per DEC-029's pre-registration, this is the final answer at 30 seeds, with no further seed extension.

**Suggested framing:** "Extending the module ablation to 30 seeds found no significant effect of removing either the feedback controller (ΔF1 = −0.032, 95% CI [−0.090, +0.023]) or the probabilistic knowledge base (ΔF1 = +0.034, 95% CI [−0.010, +0.082], p = 0.16). At this sample size the design detects effects of about 0.07–0.09 F1 with 80% power, compared with about 0.29 at five seeds. The null therefore rules out moderate effects of either module, not only large ones. For the probabilistic knowledge base, the point estimate favours removal. Together with the aggregation-rule replay, where max-merge matched or exceeded the Noisy-Or rule, this means we cannot claim that probabilistic aggregation improves held-out F1 in this pipeline." Report the retry-inclusive figure (+0.048, CI [−0.003, +0.101]) alongside it, with the retry-asymmetry explanation.

**This claim's correct manuscript treatment:** the feedback controller is "proposed and tested; no effect of ≈0.08 F1 or larger". The probabilistic KB is "no benefit detected; the evidence leans against it". Neither is an unqualified assertion that the module has no effect.

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

**Systematic error analysis (DEC-007, EVID-022):** **Corrected 2026-09-25:** the LLM extracted only 104 of the 245 text-stated training facts (42%) across 4 iterations; the rest were present only through structured seeding (the earlier "zero pure false negatives" claim tested KB presence, not LLM extraction). Of the 117 triples on contested slots, 108 are incorrect and 9 correct, spread over 47 slots (38 with only wrong candidates, 9 with the correct value competing); the earlier "1 of 117" was a misreading. The paper's Error Analysis subsection (Table: errors) and ESM S9 give the corrected counts and curated real examples.

**Scalability (DEC-008, EVID-023):** runtime scales linearly with N (no quadratic blowup) up to N=200; mean per-document latency stays flat (~4.0s) regardless of accumulated KB size (grew to 2,814 entries) — the key positive scalability claim. Memory measurement from this pass is unusable (methodology flaw: sequential runs in one process contaminate GC-affected deltas) — don't cite memory numbers from EVID-023.

**Second domain — BioRED at scale (DEC-032, EVID-047; supersedes the DEC-009 pilot).** 500 BioRED Train+Dev abstracts (5,462 sentences, 4,906 gold facts). Two extractors on the same inputs: Llama-3.1-8B (the pipeline's) and the **external baseline DeepSeek-V3.2**. Every sentence is extracted, plus whole abstracts for pilot continuity. Cost $0.686. The primary evaluator matches any annotated mention of a gold concept, with unordered pairs. Strict first-mention and relaxed containment are also reported, as in the pilot.

| Sentence level | P | R | F1 | Admitted (correct) |
|---|---:|---:|---:|---:|
| Llama, no aggregation | 0.036 | 0.096 | **0.053** | 13,034 (473) |
| Llama, R2 | 0.127 | 0.007 | 0.012 | 256 (32) |
| Llama, R3 | 0.181 | 0.005 | 0.010 | 146 (26) |
| DeepSeek, no aggregation | 0.069 | 0.097 | **0.081** | 6,934 (475) |
| DeepSeek, R2 | 0.296 | 0.009 | 0.017 | 144 (42) |
| DeepSeek, R3 | 0.299 | 0.008 | 0.016 | 139 (41) |

- **Measured first:**
  - Extractor recall is 0.096 (Llama) and 0.097 (DeepSeek).
  - Only **0.75%** (Llama) / **1.35%** (DeepSeek) of gold facts are recovered from 2+ sentences, although **35.1%** are co-mentioned in 2+ sentences (co-mention proxy; no evidence annotations exist).
  - rho = 0.022 / 0.038.
  - 96.6% / 100% of extracted triples use a valid BioRED relation type, against 49.2% on DocRED, so off-schema output is not the issue here.
- **Extractor-recall constraint: CONFIRMED on Llama by the pre-registered rule.** rho < 0.2, and R2 is below no aggregation (−0.041, CI [−0.049, −0.033]). **This replicates DocRED in a second domain:** the text offers corroboration, and the extractor realises almost none of it.
- **The DeepSeek check split.**
  - DeepSeek recovers significantly more corroborated facts (+0.0059, CI [+0.0021, +0.0098]).
  - Yet it has a *larger* aggregation gap (−0.064 vs. −0.040).
  - This is arithmetic, not a second cause: both extractors' R2 lands near F1 ≈ 0.01-0.02, so the gap tracks no-aggregation F1, which is higher for DeepSeek (0.081 vs. 0.053; higher precision at equal recall).
  - The "smaller gap" prediction was badly specified. A stronger extractor raises corroboration measurably, but nowhere near enough.
- **R3 is scope-limited.** It collapses repeats within a source, so it only acts when the extractor duplicates itself.
  - **Llama (138 within-sentence duplicates):** precision +0.054, CI [+0.015, +0.094], but F1 is **Negative** by the pre-registered rule (−0.0021, CI [−0.0048, −0.0002]) because R3 also drops true positives (32→26).
  - **DeepSeek (6 duplicates):** precision +0.004 [−0.011, +0.016], F1 **Null**.
- **The pilot is superseded.** It sent each whole abstract in one call, so every document had one source and nothing could be aggregated: it tested the extractor only, never the framework. It also listed 6 of 8 relation types, used an order-sensitive strict evaluator, and had no baseline. Its numbers (strict F1 0.007, relaxed 0.103, n=15) are historical only.

**Suggested framing:** "On 500 BioRED abstracts, a second public domain, corroboration-gated aggregation again lowers F1 relative to no aggregation, for both the pipeline's extractor and a much stronger external baseline (DeepSeek-V3.2). As on DocRED, the constraint is extraction, not the text. A third of gold facts are co-mentioned in two or more sentences, but the extractors recover only 0.75-1.35% of facts from more than one sentence. The stronger extractor recovers more corroborated facts but still far too few, and because its unaggregated output is more precise it loses more when aggregation discards nearly everything. Distinct-source counting (R3) raises precision only where the extractor repeats itself within a sentence (Llama: +0.054), and has no effect with an extractor that does not (DeepSeek)."


**Framework-level validation on DocRED at scale (DEC-031, EVID-046; supersedes DEC-020's 15-document pilot).** The PKB/Noisy-Or framework, not just the extractor, run on all 845 eligible DocRED dev documents, extracting from **every sentence** (6,861 calls, $0.21). The pilot sent only gold evidence sentences, an oracle setting. Three matching keys: exact; normalised (deployable, primary); gold-alias (**oracle upper bound only**). R2 and R3 on each, all from the same extractions. Primary evaluator: alias-aware and identical for every arm.

| Arm (all sentences) | P | R | F1 | Admitted (correct) | Docs admitting anything |
|---|---:|---:|---:|---:|---:|
| No aggregation | 0.036 | 0.057 | **0.044** | 17,914 (645) | 845 |
| exact key, R2 | 0.060 | 0.001 | 0.002 | 184 (11) | 135 |
| normalised key, R2 | 0.058 | 0.001 | 0.002 | 191 (11) | 139 |
| gold-alias key, R2 (oracle) | 0.117 | 0.003 | 0.005 | 248 (29) | 184 |
| exact key, R3 | 0.250 | 0.001 | 0.002 | 36 (9) | 32 |
| gold-alias key, R3 (oracle) | 0.406 | 0.003 | 0.005 | 69 (28) | 64 |

- **The exact-string explanation does not hold.** The pilot blamed exact-string keying for aggregation lowering F1. At scale:
  - normalisation closes **~0%** of the gap to no aggregation (recall and pooled rate identical to exact);
  - even the gold-alias oracle closes only **7.3%**;
  - every PKB arm stays far below no aggregation (oracle: −0.039 F1, CI [−0.044, −0.034]).

  Pre-registered outcome: ORACLE-ONLY + INCOMPLETE. The primary normalised-vs-exact CI excludes zero only mechanically: normalisation admits 7 extra false positives, giving an F1 difference of −0.000001.
- **The finding: cross-sentence corroboration is scarce in the extractions.**
  - Only **29 of 11,344 gold facts (0.26%)** are recovered from two or more sentences. An aggregation rule that requires corroboration cannot admit facts that are never corroborated, whatever the key.
  - The text itself does not lack corroboration: **50.2%** of gold facts have 2+ evidence sentences in the annotations.
  - The bottleneck is the extractor's recall (645 of 11,344 facts recovered at all), compounded across sentences.
- **Half the output is off-schema:** only 49.2% of extracted triples use a DocRED relation name, so about half are false positives before any aggregation.
- **R3 out of domain: a precision gain, not an F1 gain.**
  - Precision rises with R3: 0.060→0.250 with the exact key (+0.190, CI [+0.084, +0.315]), and 0.117→0.406 with the oracle key (+0.289, CI [+0.204, +0.384]).
  - The cause is removing 154-194 within-sentence duplicate observations. This is the repeat-counting defect R3 targets, now shown on real text.
  - The counts are small: 36 admitted, 9 correct. The pre-registered F1 test is a null (−0.0003, CI [−0.0009, +0.00003]), and the precision comparison was a secondary analysis.

**Hyperparameters differ from the product-domain runs (state this when comparing the two settings):** DocRED uses **shrinkage=0.5, threshold=0.70**, versus **0.75 / 0.88** in the product domain. This is DEC-020's documented recalibration, kept fixed in DEC-031. No conflict penalty is applied on DocRED, so the rival ceiling does not operate there.

**Suggested framing:** "On 845 DocRED documents, PKB aggregation lowers F1 relative to no aggregation under every matching key tested. This includes an oracle key built from gold entity mentions, which closes only 7% of the gap, so the failure is not caused by how facts are matched. It is caused by the absence of corroboration in the extractions: the sentence-level extractor recovers only 29 of 11,344 gold facts from two or more sentences, although half the facts have multiple supporting sentences in the text. Distinct-source counting (R3) raises the precision of what is admitted roughly fourfold by discarding within-sentence repeats, the same defect it corrects in the product domain, but on counts too small to move F1."

**Earlier pilot (DEC-020, historical, superseded):** 15 documents, gold evidence sentences only. Naive F1 0.033 vs. PKB 0.010. Its exact-string root-cause diagnosis is superseded by the result above.

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
| 1 | Strengthen experimental evaluation (public benchmarks) | CaRB now full-scale (DEC-001, EVID-035, N=548); DocRED framework-level test at 845 documents (DEC-031/EVID-046, supersedes the DEC-020 pilot; aggregation fails from scarce cross-sentence corroboration, not the matching key); BioRED second domain at 500 abstracts with an external baseline (DEC-032/EVID-047, supersedes the DEC-009 pilot; the extractor-recall constraint replicates). TACRED scoped and explicitly declined with a documented reason (DEC-021). REBEL-benchmark (the dataset)/Universal-IE still not attempted, lowest priority |
| 2 | Compare against SOTA methods | DeepSeek-V3.2, GPT-4o, Claude Sonnet 5, Gemini 2.5 Pro all done (DEC-002, EVID-031/032/035) — 4 of 8 named systems covered, DeepSeek now at full CaRB scale too. REBEL attempted and found task-incompatible with CaRB scoring (EVID-033, real finding, not a gap). GenIE/InstructUIE (likely same incompatibility)/DyGIE++ (AllenNLP) not attempted |
| 3 | Improve mathematical contribution | DEC-003's Noisy-Or result — a real, positive real-data finding, but **not an unqualified "strongest claim"** (in tension with the N=50 ablation, AUDIT.md A1); real-data calibration (ECE=0.3332) and computational complexity analysis now done (EVID-036). The rival-ceiling failure mode is now empirically confirmed AND a corrected rule (source-count) is tested and shown to help, on two datasets (DEC-026, EVID-041) — a second candidate fix (evidence-share) tested and found to be a null, reported honestly. Formal derivation/boundedness proof/convergence discussion (steps 2-4) still needed — pure math-writing, not experiments |
| 4 | Proper ablation study | DEC-004/005 — done, honest null result |
| 5 | Statistical validation | DEC-005/023/029 (ablation: 5 seeds at N=20, 30 seeds at N=50 — null result, achieved MDE 0.070–0.086 F1, down from ≈0.29 at 5 seeds, EVID-045) and DEC-006/022/027 (fine-tuning, 5 seeds, **leakage-free primary bootstrap is negative, CI excludes zero below**, EVID-044, superseding EVID-040's earlier p=0.0028, which was tuned on its own test set) — both now have real numbers, both need their respective caveats stated |
| 6 | Improve fine-tuning section | DEC-006/018/022/027 — AUDIT.md A2's tuning-leakage limitation directly fixed by DEC-027's independent validation/test split; the leakage-free primary result (EVID-044) is negative (CI excludes zero below), superseding EVID-040's earlier p=0.0028 result. Previously-untested asks (additional epochs, LoRA hyperparameter tuning) fully investigated via a systematic grid in both DEC-022 and DEC-027 |
| 7 | Add error analysis with examples | DEC-007 (general) + DEC-018/EVID-029 (concrete provenance-filtering examples, exactly what this point asks for) |
| 8 | Evaluate scalability | DEC-008 — done, positive result, memory data unusable |
| 9 | Validate on multiple domains | **Addressed.** DEC-032/EVID-047: BioRED as a second public domain at 500 abstracts, with an external baseline (DeepSeek-V3.2), full aggregation arms and pre-registered tests. Supersedes the 15-abstract DEC-009 pilot, which tested the extractor only. The DocRED result (DEC-031) is a third public corpus |
| 10 | Strengthen discussion (why precision/recall behave as they do) | Claim #2's precision-vs-recall mechanistic finding directly answers this |
| 11 | Improve novelty positioning | Not started (writing task, DEC-011) |
| 12 | Improve reproducibility | Not started (packaging task, DEC-012) — this file plus the Evidence log's EVID-xxx trail already provide most of the substance |
| 13 | Refine writing | Not started (writing task, DEC-013) — deferred until all experiments are done, per standing project rule |
