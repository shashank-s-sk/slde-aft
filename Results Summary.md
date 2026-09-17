# Results Summary — SLDE-AFT

**Purpose of this file:** a single, self-contained, paper-ready summary of every real result this project has produced, with honest interpretation for each. Written so it can be pasted directly into any LLM (or read by a human) when drafting the manuscript's Results/Discussion sections, with no need to cross-reference `Decision log.md` / `Evidence log.md` for the numbers themselves — those two files remain the detailed, process-oriented working logs (rationale, full limitations, next steps); this file is the distilled, citable output.

**How to keep this in sync:** whenever a new EVID-xxx entry changes a claim's status or headline number, update the corresponding section here too. `Decision log.md`'s STATUS DASHBOARD table is the fast-scan index; this file is the narrative version meant for writing prose from.

**Do not invent or round numbers beyond what's shown here.** Every number below is sourced from a specific EVID-xxx entry in `Evidence log.md` — cite that EVID number if asked where a figure came from.

---

## The 5 claimed novelty contributions — final status

| # | Claim | Verdict | Headline number |
|---|---|---|---|
| 1 | Unified closed-loop architecture | Tested end-to-end; flat vs. baseline, beats not-fine-tuning | F1 0.3869 → 0.3864 (loop) vs. 0.3791 (no fine-tune) |
| 2 | Automated synthetic supervision | Mixed, probably net-positive, not yet conclusive | Mean F1 +0.0375 (std 0.0541) across 3 seeds |
| 3 | Noisy-Or math contribution | **Strongest, most defensible result in the project** | +0.043 F1 aggregate; held-out test F1=0.197 |
| 4 | Feedback Controller reduces manual reliance | Honest null | p=0.31–0.51, no significant effect (5 seeds) |
| 5 | Provenance actively filters training data | **Validated, second-strongest result** | Precision 93.5% → 100% (drops 31/475 wrong triples) |

Plus a foundational correction: **official CaRB benchmark scores are 4-8x higher than every previously-reported internal-evaluator number** (see below) — use the official numbers, not the internal ones, anywhere CaRB is cited.

---

## Claim 3 — Noisy-Or Conservative Confidence Aggregation (the math contribution)

**This is the strongest, most defensible claim in the paper. Lead with it.**

- Real-data check (EVID-014): the conservative Noisy-Or + mutual-exclusivity-penalty aggregation improves F1 by **+0.043** in aggregate over a naive baseline, on real (not synthetic) product-domain data.
- Full instrumented run (EVID-013, 155 API calls, $0.00259): train-set iteration F1 progressed **0.3668 → 0.3682 → 0.2894 → 0.4183** across 4 iterations — non-monotonic and not fully explained (flagged for future error analysis, see DEC-007). Held-out F1: **val 0.5970** (n=5), **test 0.1970** (n=10).
- Toy/scaled synthetic validation (EVID-005/009) also supports the mechanism working as designed.

**Honest nuance for the Discussion section:** the aggregation helps *in aggregate*, but doesn't specifically resolve genuine fact conflicts well — of 117 real conflicts found, 108 were hallucination-vs-hallucination (the model contradicting its own wrong answer across passes), not correct-vs-incorrect. Report this nuance; don't imply the math resolves truth-vs-falsehood conflicts when it mostly resolves noise-vs-noise ones.

**Suggested framing:** "The conservative Noisy-Or aggregation with mutual-exclusivity penalty improves aggregate extraction F1 by 4.3 points on real data; however, error analysis shows it primarily suppresses repeated hallucinations rather than adjudicating between one correct and one incorrect competing claim."

---

## Claim 5 — Provenance-Based Filtering (validated, second-strongest result)

**A rare case where ground truth is known exactly** (the product domain is synthetically generated), enabling a real precision measurement, not just an implementation claim.

- Filter rule: a triple is kept only if at least one of its observations came from a **structured** source (not just repeated unstructured/LLM observations).
- Validated on 475 above-threshold triples from the 200-product PKB run (EVID-029):

| | n | Precision vs. gold |
|---|---:|---:|
| Unfiltered | 475 | 93.5% |
| Passes filter (has structured corroboration) | 444 | **100.0%** |
| Fails filter (unstructured-only) | 31 | **0.0%** — every single one wrong |

- **Mechanistic bonus finding:** the 31 dropped triples are almost all generic device-category nouns ("laptop device", "tablet device") standing in for the real product name, repeated 2-21 times each and mistaken by Noisy-Or aggregation for corroborating evidence. This *directly explains* (not just correlates with) the "subject-copying" failure mode seen in the DEC-006 fine-tuned model's outputs — it learned from these exact hallucinated examples.

**Suggested framing:** "Requiring structured corroboration for provenance-based filtering raises synthetic training-data precision from 93.5% to 100% on the validated subset, by removing systematically-hallucinated triples that repeated confidently enough to cross the confidence threshold despite never being grounded in a structured fact."

---

## Claim 1 — Unified Closed-Loop Architecture (tested end-to-end for the first time)

Every module existed and was tested standalone before this; this is the first test of the actual closed loop: extraction → PKB → synthetic data → LoRA fine-tune → **re-extraction with the fine-tuned model, fed back into the same PKB**.

Design (EVID-030): reconstructed the exact 4-iteration KB state (verified bit-for-bit reproducible), then ran one more iteration two ways from that identical starting point:

| Arm | KB size | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Iteration 4 (pre-closure baseline) | 475 | 0.9347 | 0.2440 | 0.3869 |
| Iteration 5, base model continues (control) | 480 | 0.9083 | 0.2396 | 0.3791 |
| Iteration 5, fine-tuned model closes loop (treatment) | 499 | 0.8978 | 0.2462 | 0.3864 |

**Verdict:** closing the loop is essentially flat vs. doing nothing further (-0.0005 F1, negligible), **but it reliably beats the realistic alternative** of continuing to extract with the un-fine-tuned model, which actively degrades the KB (-0.0078 F1). The fine-tuned model also contributed ~5x more net-new correct-enough content (24 vs. 5 net new above-threshold triples) at comparable precision.

**Suggested framing:** "Integrating the fine-tuned model back into the iterative pipeline neither degrades the knowledge base nor clearly improves it in absolute terms, but reliably outperforms the realistic alternative of continued extraction without fine-tuning — indicating the closed loop is safe to run and modestly beneficial rather than transformative at this scale."

**Caveat to state honestly:** single seed (43, the best of 3) tested for treatment; a weaker seed (44 was a net regression standalone) might shift this comparison.

---

## Claim 2 — Automated Synthetic Supervision from High-Confidence Triples (mixed)

Three fine-tuning runs, escalating in rigor:

1. **EVID-026** (33 training examples, 15 optimizer steps): fine-tuning **decreased** F1 (0.3231 → 0.2264). Diagnosed as too small/short a fine-tune, not evidence against the approach.
2. **EVID-027** (90 examples via a 200-product scale-up): initially appeared to show a clean positive result — but a real train/test leakage bug was found (2 of 10 test products were also used in training) and those numbers were retracted.
3. **EVID-028** (leakage fixed, 3 seeds on the corrected 8-product test set):

| | Precision | Recall | F1 |
|---|---:|---:|---:|
| Base | 0.1522 | 0.1250 | 0.1373 |
| Fine-tuned, seed 42 | 0.5385 | 0.1250 | 0.2029 (+0.0656) |
| Fine-tuned, seed 43 | 0.6364 | 0.1250 | 0.2090 (+0.0717) |
| Fine-tuned, seed 44 | 0.1515 | 0.0893 | 0.1124 (−0.0249) |

Mean fine-tuned F1 = 0.1748 (std 0.0541) vs. base 0.1373 — mean +0.0375, but the std exceeds the mean effect and 1 of 3 seeds regressed. **Not statistically conclusive at n=3.**

**The one clean, mechanistic finding regardless of significance:** base, seed 42, and seed 43 all catch the *exact same* 7 true positives (identical recall) — fine-tuning's entire measured effect (where it helps) is **eliminating false positives** (46 → 13 → 11 total predictions), not finding new correct facts. This is a real, citable answer to professor feedback point #10 ("why precision improves significantly, why recall remains relatively unchanged") independent of whether the aggregate F1 claim survives more seeds.

**Suggested framing:** "Fine-tuning improved F1 in 2 of 3 seeds tested (mean +0.038, not yet statistically significant), with the entire measured benefit attributable to a reduction in false-positive extractions rather than any gain in recall — both fine-tuned and base models recovered an identical set of true positives."

**Honest limitation to state:** do not claim "fine-tuning works" outright; report as implemented-and-tested with a probably-positive, seed-dependent effect, matching the same cautious register as claim #4's null result.

---

## Claim 4 — Feedback Controller Reduces Reliance on Manual Feedback (honest null)

- Single-seed pilot (EVID-016/019, N=20) suggested `without_feedback` beat the full pipeline — a surprising, counter-to-claim direction.
- Proper 5-seed statistical validation (EVID-020, seeds 42-46, N=20): **no significant difference** between `without_feedback`/`without_prob_kb` and the full pipeline (paired t-test/Wilcoxon, all p=0.31–0.51). The earlier single-seed direction did not replicate — with 5 seeds, `without_feedback`'s mean F1 is actually *lower* than full's, reversing the earlier apparent direction, and still not significant either way.

**Verdict:** no ablation effect detected at N=20/5-seed scale. This is the single biggest tension between the manuscript's current claims and the rigorous evidence.

**Suggested framing:** "A five-seed statistical validation found no significant difference in F1 between the full pipeline and ablated variants without the feedback controller or probabilistic knowledge base (p=0.31–0.51 across paired t-tests and Wilcoxon signed-rank tests), indicating the feedback mechanism's benefit, if any, is not detectable at this scale."

**This claim needs either:** (a) a larger-N confirmatory run before submission, or (b) explicit reframing in the manuscript as "proposed and tested; no significant effect detected at this scale" rather than an assertion that feedback helps.

---

## Foundational correction — Official CaRB Benchmark Scores (use these, not the old numbers)

**Every CaRB number reported before EVID-031 used this project's own internal exact-match evaluator, which undercounts real performance by roughly 4-8x** due to subject-boundary-mismatch scoring artifacts (e.g., penalizing a predicted `"all households"` against gold `"32.7% of all households"` as entirely wrong, despite being the same fact).

**Official scores** (EVID-031/032, run via the real `data/CaRB/carb.py` tool, N=30 sentences, default lenient matching) — now covering 5 systems, 4 of the 8 professor feedback point #2 names GPT-4/Claude/Gemini plus DeepSeek:

| System | Precision | Recall | F1 |
|---|---:|---:|---:|
| DeepSeek-V3.2 (external baseline) | 0.713 | 0.458 | **0.558** |
| Gemini 2.5 Pro | 0.773 | 0.401 | **0.528** |
| Claude Sonnet 5 | 0.642 | 0.446 | **0.527** |
| GPT-4o | 0.736 | 0.384 | **0.504** |
| Llama-3.1-8B-instruct (SLDE-AFT's own extractor) | 0.652 | 0.401 | **0.496** |

(Internal-evaluator numbers, now superseded and not to be used as headline figures.)

**Use the official numbers above anywhere CaRB results are cited in the paper.**

**Important, honest finding — state this explicitly, don't omit it:** SLDE-AFT's own extractor (Llama-3.1-8B) is the **weakest of all 5 systems tested**, though the gap is modest (~12% relative, top to bottom). This does not undermine the paper's actual novelty claims — the Noisy-Or aggregation, closed-loop architecture, and provenance filtering all operate *on top of* whatever base extractor is used, and SLDE-AFT deliberately uses a smaller, cheaper, open-weight model rather than a larger proprietary one. Frame it as: "the architecture's value lies in what it does with the base extractor's outputs, not in having the single strongest raw extractor."

**Practical note worth a sentence in Methods:** Gemini 2.5 Pro required a much larger token budget (3072 vs. 512 for the other four models) and still had a 5/30 error rate on this task — reasoning-heavy models may need more generous generation budgets and more robust output parsing for structured extraction than non-reasoning models need for the same task.

**Caveat:** still a 30-sentence pilot, not CaRB's full 641-sentence test set — note this as a scale limitation, not a validity one. REBEL, GenIE, InstructUIE, DyGIE++ (the remaining professor-feedback-named systems) were not attempted — each needs a different, dependency-heavy research codebase rather than a simple API call.

---

## Other supporting results

**Systematic error analysis (DEC-007, EVID-022):** zero pure false negatives in the product-domain train set (every gold fact was observed at least once across 4 iterations) — recall failures are recoverable, not fundamental misses. Conflict adjustment overwhelmingly resolves hallucination-vs-hallucination conflicts (108 of 117), not correct-vs-incorrect ones (1 of 117) — report this nuance wherever the conflict-resolution mechanism is described.

**Scalability (DEC-008, EVID-023):** runtime scales linearly with N (no quadratic blowup) up to N=200; mean per-document latency stays flat (~4.0s) regardless of accumulated KB size (grew to 2,814 entries) — the key positive scalability claim. Memory measurement from this pass is unusable (methodology flaw: sequential runs in one process contaminate GC-affected deltas) — don't cite memory numbers from EVID-023.

**Domain generalization — BioRED biomedical pilot (DEC-009, EVID-024):** strict exact-match F1=0.0074 is misleadingly low (mostly a gold-construction/boundary-mismatch artifact, same family of issue as the CaRB correction above). Relaxed containment-match F1=0.1029 (14x more true positives found) is the fairer read: the biomedical domain is genuinely harder than the product domain, but not a near-total failure. **Report both numbers together with this explanation — never the strict number alone**, which would be a misleading characterization.

---

## Structural manuscript issues (independent of the 5 claims — fix before submission)

- **All of SLDE.pdf's reported Table 7-9 results used `openrouter/auto`** (unpinned model routing), per the manuscript's own Section 5.4 — this is not just the CaRB pilot's problem. The headline numbers currently in the draft (Precision 0.9000, "84% gain," Recall=1.0000) are **not a reproducible measurement of any specific named model**. This is exactly the single-run/unpinned-methodology problem professor feedback point #5 criticizes. All of the pinned-model numbers in this file are the fix — they will not match the old draft's numbers, and that's expected, not a regression.
- **The manuscript is missing Sections 8-11** (Ablation Analysis, Discussion, Limitations/Future Work, Conclusion) — it currently jumps from Section 7.5 straight to References despite the introduction promising them. This file's per-claim sections above are meant to seed exactly those sections once writing begins.
- **The old notebook's B3 baseline and Table-9 "Iterative FT" results come from two different, inconsistent code paths** (found while porting DEC-006) — do not cite old B3/B4/Table-9 numbers from the notebook without checking which code path actually produced them.

---

## Mapping to professor_feedback.md's 13 points (quick reference)

| # | Point | Where it's addressed here |
|---|---|---|
| 1 | Strengthen experimental evaluation (public benchmarks) | CaRB official scores (DEC-001); BioRED domain pilot (DEC-009) — still only 2 domains/benchmarks, DocRED/TACRED/REBEL-benchmark/Universal-IE not attempted |
| 2 | Compare against SOTA methods | DeepSeek-V3.2, GPT-4o, Claude Sonnet 5, Gemini 2.5 Pro all done (DEC-002, EVID-031/032) — 4 of 8 named systems covered. REBEL/GenIE/InstructUIE/DyGIE++ still not done (REBEL most tractable if pursued) |
| 3 | Improve mathematical contribution | DEC-003's Noisy-Or result — strongest claim, but formal derivation/convergence/complexity analysis for the manuscript text still needs writing |
| 4 | Proper ablation study | DEC-004/005 — done, honest null result |
| 5 | Statistical validation | DEC-005 (ablation, 5 seeds) and DEC-006/028 (fine-tuning, 3 seeds) — both real, neither fully conclusive |
| 6 | Improve fine-tuning section | DEC-006/018 — real, mixed, mechanistically-explained result now exists (previously "too weak to report") |
| 7 | Add error analysis with examples | DEC-007 (general) + DEC-018/EVID-029 (concrete provenance-filtering examples, exactly what this point asks for) |
| 8 | Evaluate scalability | DEC-008 — done, positive result, memory data unusable |
| 9 | Validate on multiple domains | DEC-009 (BioRED) — one additional domain, pilot scale only |
| 10 | Strengthen discussion (why precision/recall behave as they do) | Claim #2's precision-vs-recall mechanistic finding directly answers this |
| 11 | Improve novelty positioning | Not started (writing task, DEC-011) |
| 12 | Improve reproducibility | Not started (packaging task, DEC-012) — this file plus the Evidence log's EVID-xxx trail already provide most of the substance |
| 13 | Refine writing | Not started (writing task, DEC-013) — deferred until all experiments are done, per standing project rule |
