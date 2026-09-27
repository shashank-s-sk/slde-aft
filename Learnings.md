# SLDE-AFT Learnings

A running log of small, concrete lessons learned while executing the
DEC-xxx decisions. Each entry is one bullet: what was learned and why
it matters. Not a status log (that's `Decision log.md` /
`Evidence log.md`) — only things worth remembering the next time
similar work is done.

## Inferences (per-run, structured)

Unlike the bullet-point lessons below, this section is a table: one row
per conclusion drawn from a specific EVID entry, with an honest
confidence label. The point is to separate "what the numbers say" from
"what we're allowed to conclude" — a run can produce ten numbers and
only two or three legitimate inferences, and writing them down here
right after the run (same sitting as the EVID entry) stops a hypothesis
from quietly turning into a stated fact by the time it reaches the paper.

**Confidence labels**: **CONFIRMED** (directly demonstrated, no further
evidence needed) · **HYPOTHESIS** (plausible, not yet tested — must not
be stated as fact in the paper) · **INSUFFICIENT DATA** (sample/seed
count too small — the honest paper text is "unknown," not a guess) ·
**REFUTED** (tested with more data and did not hold up — keep the row,
don't delete it, so the same hypothesis doesn't get proposed again
without checking here first).

| EVID | Observation | Inference | Confidence | What would upgrade this |
|---|---|---|---|---|
| EVID-013 | KB size grew every iteration (534→576→613→657), never shrank | Retention monotonicity (math spec property) holds empirically at this scale, independent of extraction quality | CONFIRMED | N/A — structural property, already demonstrated |
| EVID-013 | Train-set LLM-only F1 went 0.367→0.368→0.289→0.418 (non-monotonic; iteration 3 dips) | Feedback/locked-context guidance does not reliably improve extraction iteration-over-iteration in this run | CONFIRMED (the non-monotonicity itself) | — |
| EVID-013 | (same data) | Iteration 3's dip may be caused by early false-positive triples persisting in the locked-context string (Prob-KB never deletes) and misleading the model | HYPOTHESIS | DEC-007 error analysis: inspect which triples were in the iteration-3 locked context and whether they're disproportionately wrong |
| EVID-013 | 117/657 retained triples have >=1 competing object; 602/657 sit on functional-predicate slots | Conflict adjustment meaningfully engages on real product-domain data, not just the synthetic EVID-005/EVID-009 toy data | CONFIRMED | — |
| EVID-013 | 25.2% of calls returned 0 triples with no error; 6.5% failed to parse | A substantial share of the recall gap is attributable to LLM extraction/formatting reliability, not the PKB aggregation formula | CONFIRMED as a contributing factor — not yet shown to be the *dominant* cause | Compare recall lost to zero-yield/parse-failure calls vs. recall lost to correct-JSON-but-wrong-content calls |
| EVID-013 | Held-out F1: val 0.597 (n=5) vs test 0.197 (n=10) | Whether this gap reflects real overfitting to the feedback signal or is sampling noise | INSUFFICIENT DATA | DEC-005 multi-seed runs (seeds 42-46) on the same split; if the gap persists in direction/magnitude across seeds, upgrade to CONFIRMED |
| EVID-013 | Best iteration F1 (0.418) vs. historical 40-product prototype's reported final F1 (0.90) | This is *not* evidence that Prob-KB underperforms the deterministic KB — different subset, different KB math, different iteration-eval protocol nuances | CONFIRMED (that the comparison is invalid as-is) | A controlled DEC-004-style ablation: same products, same iterations, same eval code, Prob-KB vs. deterministic max-merge as the only variable |

| EVID-014 | Above τ=0.88: precision 0.780 (99TP/28FP). Below τ: precision 0.276 | Threshold-based admission genuinely separates correct from incorrect triples on real data, not just synthetic | CONFIRMED | — |
| EVID-014 | Whole-KB F1: raw support 0.489 vs conflict-adjusted 0.532 (+0.043) | Conflict adjustment modestly improves aggregate admission quality over unadjusted Noisy-Or, on real data | CONFIRMED | Repeat across seeds (DEC-005) to confirm it's not a one-run artifact |
| EVID-014 | On the 117 rows with an actual competitor (9 gold positives): F1 0.185 (raw) vs 0.167 (conflict-adjusted) | The aggregate F1 gain is not coming from correctly resolving real conflicts — conflict adjustment is flat-to-worse exactly where it's designed to matter, trading recall for a smaller precision gain | CONFIRMED (matches EVID-005's synthetic finding, now on real data) | Larger n of real conflict cases (more products, or DEC-005 seeds) to check if this holds up |

| EVID-016 | without_feedback beat full on both train F1 (0.328 vs 0.265) and held-out test F1 (0.634 vs 0.481) | The Feedback Controller may be actively hurting extraction, not helping — opposite of the architecture's assumption | **REFUTED by EVID-020** — see below | — |
| EVID-016 | without_prob_kb (deterministic max-merge) underperformed full on both metrics (F1 0.202 vs 0.265 train; 0.245 vs 0.481 held-out) | Prob-KB outperforms deterministic max-merge in this pilot — supportive of DEC-003's contribution | **REFUTED by EVID-020** — see below | — |
| EVID-016 | unstructured_only F1 was normal for iterations 1-3 (0.40-0.47) then collapsed to exactly 0.0 at iteration 4, with zero KB growth that iteration | Unexplained — could be a real behavioral effect or a call-level failure spike; cannot currently tell which | CONFIRMED as a credit-exhaustion artifact (EVID-017/018), not a real behavioral effect | — |
| EVID-020 | 5-seed means: full train F1 0.423, without_feedback 0.288, without_prob_kb 0.344; paired t-test/Wilcoxon p-values all 0.31-0.51 | No statistically significant difference between full and either ablation at N=20/5 seeds. The EVID-016 "without_feedback beats full" result does not replicate — direction even reverses on train F1 | CONFIRMED (properly powered multi-seed test, this is the trustworthy answer) | A larger-N (50+) confirmatory run if a real effect is still suspected |
| EVID-020 | full's held-out test F1: 0.349, 0.816, 0.0, 0.0, 0.292 across 5 seeds (std 0.335, exceeding the mean) | N=20's held-out split (4 test products) is too small/noisy to support any firm ablation conclusion on its own | CONFIRMED | Re-run at N=50 where held-out test has 10 products instead of 4 |
| EVID-020 | unstructured_only train F1 0.457 +/- 0.099 — highest mean, lowest std of any config | Possibly the most consistent-performing config, but untested against full for significance (different evaluation shape — no held-out set) | INSUFFICIENT DATA | A significance test would need a comparable evaluation target for unstructured_only vs full, not yet designed |
| EVID-021 | Pinned Llama-3.1-8B on CaRB-30: F1=0.059. Old CaRB-10 pilot (EVID-003) using `openrouter/auto`: F1=0.133, on fewer sentences | `openrouter/auto` was very likely routing to a stronger model than Llama-3.1-8B for that old pilot, making EVID-003's F1 not a reproducible measurement of any specific named model | HYPOTHESIS (direction is consistent with this, but which model `auto` actually used is not recoverable after the fact) | N/A — can't be checked retroactively; the fix going forward is to always pin, which is now done |
| EVID-021 | DeepSeek-V3.2 F1=0.134 vs. pinned Llama-3.1-8B F1=0.059 on the same 30 CaRB sentences, same prompt | DeepSeek is a meaningfully stronger extractor than Llama-3.1-8B on open-domain OpenIE text (~2.3x F1) | CONFIRMED | — |
| EVID-022 | 0 pure false negatives in the product-domain train set across 4 cumulative iterations, despite iteration 4 alone having recall 0.355 | "Recall" reported per-iteration understates what the system actually observed — nearly every gold fact was seen at least once somewhere across the 4 passes, just not always admitted in any single pass | CONFIRMED | — |
| EVID-022 | Of 117 conflicting-slot triples, 108 are hallucination-vs-hallucination conflicts and only 1 is a confirmed gold match | Conflict adjustment mostly has nothing genuinely correct to protect — most conflicts it resolves are between two wrong answers, not a right one and a wrong one | CONFIRMED | — |
| EVID-022 | CaRB subject-boundary mismatch (dropping numeric qualifiers like "32.7% of") reproduced independently on a fresh 30-sentence sample | Confirmed as a recurring, systematic failure mode, not a one-off from the original 10-sentence sample (EVID-004) | CONFIRMED | — |
| EVID-023 | Mean per-document latency stayed ~4.0s flat from N=20 to N=200, despite KB growing to 2,814 entries; runtime scaled linearly with N | The system doesn't slow down per-item as accumulated knowledge grows, at least up to this scale — real, positive scalability evidence | CONFIRMED (up to N=200; untested beyond) | Test at larger N (500-1000) if the paper needs a stronger scalability claim |
| EVID-023 | mem_delta was -29.63MB at N=100 (memory went down) | Running all sweep sizes sequentially in one process contaminates memory measurements via cross-run garbage collection — the numbers are not usable | CONFIRMED as a methodology flaw, not a finding | Re-run each size as an isolated subprocess if a real memory measurement is ever needed |
| EVID-024 | BioRED strict exact-match F1=0.0074 vs. relaxed containment-match F1=0.1029 (14x more TPs) on the same predictions | A single evaluation number can badly mislead when gold construction involves a surface-text proxy for a normalized concept — always compute a relaxed/secondary metric before reporting a domain as "failing" | CONFIRMED | — |
| EVID-024 | Relaxed BioRED F1 (0.103) is still well below the product domain's typical range (~0.3-0.7) but comparable to CaRB's Llama score (0.059) | The biomedical domain is genuinely harder for this pipeline than the synthetic product domain, independent of the evaluation-protocol artifact | HYPOTHESIS (n=15 pilot only) | Scale beyond n=15; add real entity linking instead of first-mention proxy |
| EVID-025 | Old notebook's B3 baseline (cell 22) substitutes a different OpenRouter model instead of using the actually fine-tuned local TinyLlama adapter it trained in cell 20 | The manuscript's B3/B4 numbers and the Table-9 "Iterative FT" numbers come from two different, inconsistent code paths — another reason not to treat old prototype numbers as settled without checking which code actually produced them | CONFIRMED | — |

**Open questions carried forward**: why does iteration 3 dip (→DEC-007)?
Prob-KB vs. deterministic KB on identical inputs, isolated from every
other confound, at a larger N where the effect might actually show up
(→ a future larger-scale DEC-004/005 re-run)? Of the zero-triple calls,
how many of the 7 visible facts *should* have been extracted (→DEC-007,
sharpens the recall-gap inference above)? Is unstructured_only's
apparent consistency (lowest std) real or coincidental (→ needs its own
significance test design)?

## Evaluation / metrics

- Exact-match OpenIE evaluation is sensitive to surface formatting
  (e.g. `32.7%` vs `32.7 %`). A normalization step is needed before
  scoring, or true positives get miscounted as false negatives.
  (source: EVID-002)
- LLMs doing OpenIE extraction tend to (a) drop numeric/percentage
  qualifiers from subjects and (b) merge two gold facts into one
  compound triple. Both look like "wrong" predictions under exact
  match even when the model understood the sentence correctly.
  (source: EVID-004)
- A more "sophisticated" aggregation formula is not automatically
  better on the metric — in the DEC-003 toy validation, Conservative
  Noisy-Or + conflict adjustment scored worst (P/R/F1 = 0) while plain
  max-merge scored best. Don't assume the fancier math wins; measure
  it. (source: EVID-005)

## Instrumentation / logging

- Historical run artifacts (the 40-product notebook outputs) do not
  contain per-observation confidence histories or PKB snapshots —
  only aggregate iteration metrics. Once a run is done without that
  logging, the fine-grained history cannot be reconstructed after the
  fact. Lesson: instrument *before* running an experiment you plan to
  report on, not after. (source: EVID-007)
- Claimed computational complexity must match what was actually
  executed. The O(1) running-residual PKB update is a proposed
  optimized design in the math spec, not something the current
  prototype runs — reporting it as measured would be a fabricated
  claim. (source: EVID-005 notes)

## Data / splits

- The 20/30/40/50-product notebooks share identical attribute lists and
  the same `random.seed(42)` before generation, so product index 1..N
  in a smaller run is bit-identical to index 1..N in a larger run. This
  let one 50-product split apply to all four sizes by filtering
  `product_idx <= N`, instead of needing four separate splits — but it's
  an assumption tied to those specific notebook cells staying unedited,
  not a general guarantee. (source: EVID-010)

## Cost / API

- OpenRouter's `/api/v1/credits` endpoint can report `total_credits: 0`
  while real paid calls still go through and bill successfully — don't
  trust that field alone to mean "calls will fail." A real minimal call
  is a better test than reading the dashboard-style endpoints. At
  `meta-llama/llama-3.1-8b-instruct` pricing, a 3-product real
  extraction smoke test cost $0.0000225 total — full experiment runs at
  this scale are not going to be the budget constraint. (source: EVID-011)
- That "it works despite $0 total_credits" state produced an HTTP 402
  "insufficient credits" error after ~$0.0064 of cumulative real spend
  — but the actual root cause (EVID-018) was our own code never setting
  `max_tokens` on the request. OpenRouter pre-authorizes credits against
  the model's *entire context window* when no cap is given, not against
  realistic usage, so a low-but-genuinely-sufficient balance can still
  get rejected. Corrected lesson: before concluding "we're out of
  money," check whether the request itself is asking for something
  absurd (like an implicit 117K-token completion cap) — a one-line fix
  (`max_tokens=512`) resolved it with zero top-up needed. Don't jump to
  "the user must pay more" as the first hypothesis for a payment-shaped
  error; verify the request is sane first. (source: EVID-018)

## Testing

- A glue-code bug (mismatched keyword arguments between two modules
  written at different times — `probkb_v2_adapter.py` calling
  `pkb_instrumentation.py`'s `save_iteration_artifacts()` with names
  that didn't match its real signature) survived undetected because the
  adapter had never actually been run end to end. A cheap offline test
  plus a mocked zero-cost dry run of the full pipeline caught it before
  any real API spend, rather than discovering it mid-run at call #50+.
  (source: EVID-012)

## Results (real run)

- In the full DEC-003 product-domain run, train-set iteration F1 was
  *not* monotonically increasing (0.367 → 0.368 → 0.289 → 0.418) —
  iteration 3 dipped below iterations 1-2 before iteration 4 recovered.
  This does not match the historical uninstrumented 40-product run's
  reported steady climb (0.49 → 0.90). Don't assume the historical
  "precision increases with iterations" narrative generalizes to a
  different KB variant (Prob-KB vs. deterministic max-merge) or a
  different product subset without checking — they are not the same
  experiment even though both are called "SLDE-AFT Full." (source: EVID-013)
- Held-out F1 on 5 val products (0.597) vs. 10 test products (0.197)
  swung widely on a single seed. At this sample size that gap could be
  real overfitting to the feedback signal or could just be noise — don't
  report a val/test gap like this as a finding until multiple seeds
  (DEC-005) confirm it's not sample-size noise.
- About 1 in 4 real extraction calls (25%) return zero triples with no
  error, and about 1 in 15 (6.5%) fail to produce parseable JSON at all,
  at full-scale measurement (n=155) with this prompt/model. Matches the
  smaller-sample smoke-test signal (EVID-004, EVID-011) — now confirmed
  at scale, not just plausible from n=3.

## Process (2)

- When copying a run-script pattern to a new experiment (DEC-003's
  script → DEC-004's ablation pilot), double-check that *every* piece of
  the original's diagnostic logging came along, not just the metrics
  you're actively looking for. `scripts/dec004_ablation_pilot.py`
  dropped the per-call `call_log.json` that DEC-003's script had, and
  the very first real run produced an anomaly (a config's F1 collapsing
  to 0.0 in one iteration) that can't be diagnosed because of exactly
  that missing log. Cheap logging you don't yet need is much cheaper
  than a re-run. (source: EVID-016)

## Process

- `Decision log.md` / `Evidence log.md` can silently drift behind the
  actual repo state — a scaled 3-seed/3-scenario DEC-003 experiment
  (`outputs/dec003_scaled/`), passing unit tests, and a working
  candidate-buffer adapter (`src/probkb_v2_adapter.py`) all existed on
  disk without a corresponding EVID entry or updated DEC-003 status.
  Lesson: write the EVID entry and flip the status line in the same
  sitting you finish the work, not later — otherwise "what's left"
  has to be re-derived from the filesystem instead of read off the log.

Two problems with Section 2.

1. Sections 2.1-2.6 are placeholders ("[reused from the old draft...]"),
   not prose. Write them out in full. You may reuse the old draft's
   wording where it is still accurate, but the section must read as
   finished text with no bracketed notes. Remove every "first system"
   and "to the best of our knowledge no existing system" claim.
2. Show me Section 2.7 (DySECT) in full — it was cut off. Confirm the
   citation details from the ACL Anthology record before writing it, and
   state explicitly which capabilities DySECT shares with SLDE-AFT
   (closed loop, probabilistic KB confidence, prompt-augmentation
   feedback, synthetic training data from high-confidence triples,
   hierarchical abstraction, human curation interface) and which are
   ours (structured seeding at fixed confidence, provenance as a gate on
   training data, the conservative Noisy-OR rule with shrinkage and the
   exclusivity penalty plus its formal analysis, and the empirical
   evaluation).

Also verify the years and venues for Ji et al. and Nguyen: the old
reference list has both with incomplete details. Put anything you cannot
confirm in paper/UNVERIFIED.md rather than in the bibliography.

Commit, show me the full text of 2.1-2.7, and stop.

Section 2 is approved with six fixes. Do not start Section 3 yet.

1. The "5-8 percentage points" recall claim for DySECT: I cannot verify
   this from any public source. Open the paper's Table 1 (DocRED, recall
   and average extracted triples). If the figure is there, cite it
   precisely with the models it applies to; if not, delete the sentence
   and state only that they report consistent recall improvements across
   models under KB-guided prompting. Record the outcome in
   paper/UNVERIFIED.md.
2. Acronym: the abstract expands DySECT as "Dynamic Self-Evolving
   Extraction and Curation Toolkit"; the paper title is "A Dynamic
   Self-Evolving Extraction System". Use both correctly.
3. DySECT's KB is built on Theo (Mitchell et al.), per their repository.
   Verify and cite Theo if accurate.
4. Verify Ji et al. (knowledge graph survey): the old reference list gives
   32(5):2429-2443 with no year; confirm the correct volume, issue, pages
   and year from IEEE TNNLS before using it.
5. Two different Wang et al. 2023 papers are cited (InstructUIE, Wang X.
   et al.; SELF-INSTRUCT, Wang Y. et al.). Give them distinct keys and
   make sure the numeric citations point to the right entries.
6. Note for the Discussion (do not write it yet): DySECT evaluates on
   DocRED and reports recall improvements there, whereas our DocRED pilot
   found aggregation reduced recall from 0.032 to 0.005. State this
   contrast honestly when we reach the Discussion.

Then Section 3 (Research Gap). The old draft's Table 1 claims SLDE-AFT is
the only system satisfying all six capability dimensions. That claim is no
longer supportable: add DySECT as a column, fill it from Section 2.7, and
rewrite the section so the gap is stated as what remains untested rather
than what no system has built. Remove every "no existing system" and
"first" claim.

Section 2 is approved with six fixes. Do not start Section 3 yet.

1. The "5-8 percentage points" recall claim for DySECT: I cannot verify
   this from any public source. Open the paper's Table 1 (DocRED, recall
   and average extracted triples). If the figure is there, cite it
   precisely with the models it applies to; if not, delete the sentence
   and state only that they report consistent recall improvements across
   models under KB-guided prompting. Record the outcome in
   paper/UNVERIFIED.md.
2. Acronym: the abstract expands DySECT as "Dynamic Self-Evolving
   Extraction and Curation Toolkit"; the paper title is "A Dynamic
   Self-Evolving Extraction System". Use both correctly.
3. DySECT's KB is built on Theo (Mitchell et al.), per their repository.
   Verify and cite Theo if accurate.
4. Verify Ji et al. (knowledge graph survey): the old reference list gives
   32(5):2429-2443 with no year; confirm the correct volume, issue, pages
   and year from IEEE TNNLS before using it.
5. Two different Wang et al. 2023 papers are cited (InstructUIE, Wang X.
   et al.; SELF-INSTRUCT, Wang Y. et al.). Give them distinct keys and
   make sure the numeric citations point to the right entries.
6. Note for the Discussion (do not write it yet): DySECT evaluates on
   DocRED and reports recall improvements there, whereas our DocRED pilot
   found aggregation reduced recall from 0.032 to 0.005. State this
   contrast honestly when we reach the Discussion.

Then Section 3 (Research Gap). The old draft's Table 1 claims SLDE-AFT is
the only system satisfying all six capability dimensions. That claim is no
longer supportable: add DySECT as a column, fill it from Section 2.7, and
rewrite the section so the gap is stated as what remains untested rather
than what no system has built. Remove every "no existing system" and
"first" claim.

Section 2 is approved with six fixes. Do not start Section 3 yet.

1. The "5-8 percentage points" recall claim for DySECT: I cannot verify
   this from any public source. Open the paper's Table 1 (DocRED, recall
   and average extracted triples). If the figure is there, cite it
   precisely with the models it applies to; if not, delete the sentence
   and state only that they report consistent recall improvements across
   models under KB-guided prompting. Record the outcome in
   paper/UNVERIFIED.md.
2. Acronym: the abstract expands DySECT as "Dynamic Self-Evolving
   Extraction and Curation Toolkit"; the paper title is "A Dynamic
   Self-Evolving Extraction System". Use both correctly.
3. DySECT's KB is built on Theo (Mitchell et al.), per their repository.
   Verify and cite Theo if accurate.
4. Verify Ji et al. (knowledge graph survey): the old reference list gives
   32(5):2429-2443 with no year; confirm the correct volume, issue, pages
   and year from IEEE TNNLS before using it.
5. Two different Wang et al. 2023 papers are cited (InstructUIE, Wang X.
   et al.; SELF-INSTRUCT, Wang Y. et al.). Give them distinct keys and
   make sure the numeric citations point to the right entries.
6. Note for the Discussion (do not write it yet): DySECT evaluates on
   DocRED and reports recall improvements there, whereas our DocRED pilot
   found aggregation reduced recall from 0.032 to 0.005. State this
   contrast honestly when we reach the Discussion.

Then Section 3 (Research Gap). The old draft's Table 1 claims SLDE-AFT is
the only system satisfying all six capability dimensions. That claim is no
longer supportable: add DySECT as a column, fill it from Section 2.7, and
rewrite the section so the gap is stated as what remains untested rather
than what no system has built. Remove every "no existing system" and
"first" claim.

Section 2 is approved with six fixes. Do not start Section 3 yet.

1. The "5-8 percentage points" recall claim for DySECT: I cannot verify
   this from any public source. Open the paper's Table 1 (DocRED, recall
   and average extracted triples). If the figure is there, cite it
   precisely with the models it applies to; if not, delete the sentence
   and state only that they report consistent recall improvements across
   models under KB-guided prompting. Record the outcome in
   paper/UNVERIFIED.md.
2. Acronym: the abstract expands DySECT as "Dynamic Self-Evolving
   Extraction and Curation Toolkit"; the paper title is "A Dynamic
   Self-Evolving Extraction System". Use both correctly.
3. DySECT's KB is built on Theo (Mitchell et al.), per their repository.
   Verify and cite Theo if accurate.
4. Verify Ji et al. (knowledge graph survey): the old reference list gives
   32(5):2429-2443 with no year; confirm the correct volume, issue, pages
   and year from IEEE TNNLS before using it.
5. Two different Wang et al. 2023 papers are cited (InstructUIE, Wang X.
   et al.; SELF-INSTRUCT, Wang Y. et al.). Give them distinct keys and
   make sure the numeric citations point to the right entries.
6. Note for the Discussion (do not write it yet): DySECT evaluates on
   DocRED and reports recall improvements there, whereas our DocRED pilot
   found aggregation reduced recall from 0.032 to 0.005. State this
   contrast honestly when we reach the Discussion.

Then Section 3 (Research Gap). The old draft's Table 1 claims SLDE-AFT is
the only system satisfying all six capability dimensions. That claim is no
longer supportable: add DySECT as a column, fill it from Section 2.7, and
rewrite the section so the gap is stated as what remains untested rather
than what no system has built. Remove every "no existing system" and
"first" claim.

Commit, show me the corrected 2.7 and the new Section 3, and stop.

DEC-027 accepted as a negative result. Four things:

1. Report macro (per-product bootstrap, -0.021 [-0.042, -0.003]) as the
   primary outcome, since that is what was pre-registered. Report micro F1
   (0.511 -> 0.553, t p = 0.006) alongside it, and explain the divergence:
   micro pools triples and rewards precision across many products, macro
   weights products equally and reflects the per-product recall loss.
   Do not present micro as the headline.
2. Add the mechanism: recall fell in all 5 seeds (0.464 -> 0.414-0.425),
   the first time recall has moved in any fine-tuning run; on the 8-product
   set it was pinned at 0.125 by the small gold count. Validation selection
   used F1 where recall was flat across configurations, so it effectively
   selected on precision alone and chose the most conservative adapter.
3. Add the software-version caveat to EVID-044 in one line: no run in this
   project pinned torch/transformers/trl/bitsandbytes; only PEFT versions
   are recoverable from adapter metadata (DEC-027: 0.21.0 throughout).
   Add `pip freeze > outputs/<run>/pip_freeze.txt` to the runbook.
4. Add that validation selection was decided by precision alone, with the
   top three configurations within 0.01 F1 on 20 products.

Then update paper/main.tex and Results Summary.md so EVID-044 supersedes
EVID-040 as the fine-tuning result, and the claim reads as negative rather
than exploratory-positive. Commit, push, stop. Do not start DEC-029 yet.

Yes, carry out the instructions with all four of your corrections — they
are right and mine were wrong. Two additions:

1. Resolve the 99 vs 137 false-positive discrepancy rather than noting it.
   True positives match exactly, so the gap is entirely in false-positive
   counting, and the reported micro precision depends on which convention
   is used. Find the cause (global deduplication of identical triples,
   predictions with unmatched subjects being dropped, or similar), state it
   in EVID-044, and say which convention the reported micro numbers use.
   If the two conventions give different micro F1 values, report both.
2. When rechecking the EVID-040 citations around main.tex:1053 and
   1207-1229, make sure no remaining text presents the old +0.064 result as
   a current finding. EVID-040 should appear only as a superseded
   exploratory result with its tuning-on-test caveat.

Then commit, push, and stop before DEC-029.

---

## Project memory: DEC-029 run, wait-time log (2026-09-24)

Reference record of how long DEC-029 (30-seed ablation, 25 new seeds
47-71 x 3 configs = 75 runs x 155 API calls = 11,625 calls) took and how
long I waited. All times are local (+02:00), taken from file timestamps
in `outputs/dec029_ablation_extended/`.

**Timeline**

| Time | Event |
|---|---|
| 13:58:31 | Run started, sequential (one run at a time) |
| ~14:00 | First measurement: about 8 s per API call. Projection for sequential: 11,625 x 8.07 s = 93,814 s = **26.1 h** (13-26 h depending on API speed) |
| 14:01:30 (approx.) | Sequential run stopped after 16 calls (kept in cache, reused, not re-paid) |
| 14:01:46 | Restarted as **6 parallel shards** (3 configs x seeds 47-59 / 60-71) |
| 14:15:44 | I asked "is the run finished?" -> 0/75 done, first 6 runs at 116-140/155 calls |
| 14:17:27-14:20:19 | First 6 runs completed (one per shard) |
| 14:20:22 | I asked "how much time?" -> 6/75 done, ETA given as ~18:10 |
| 14:25:07 | This log written |

**Measured duration of the first 6 runs (start 14:01:46)**

| Run | Finished | Duration |
|---|---|---|
| without_feedback / seed 47 | 14:17:27 | 15 min 41 s |
| full / seed 47 | 14:18:11 | 16 min 25 s (had 16 calls already cached) |
| full / seed 60 | 14:19:45 | 17 min 59 s |
| without_prob_kb / seed 47 | 14:19:50 | 18 min 04 s |
| without_prob_kb / seed 60 | 14:19:59 | 18 min 13 s |
| without_feedback / seed 60 | 14:20:19 | 18 min 33 s |
| **Mean** | | (15.68 + 16.42 + 17.98 + 18.07 + 18.22 + 18.55) / 6 = **17.49 min per run** |

**Projection from those measurements**

- Sequential: 75 runs x 17.49 min = 1,311.8 min = **21.9 h**
- Parallel: the longest shards (seeds 47-59) have 13 runs each, so
  13 x 17.49 min = 227.4 min = **3 h 47 min** after 14:01:46, i.e. an
  expected finish around **17:49**. The earlier ETA of ~18:10 was more
  conservative (11.5 rounds x 20 min).
- Speed-up from parallelising: 21.9 h / 3.8 h = **about 5.8x**.
- Cost is unaffected by parallelising: ~$0.22 expected ($0.29 worst case).

**What happened after that (actual)**

| Time | Event |
|---|---|
| ~15:50 | Run stopped by Claude Code: the whole PC was critically low on memory (only 1.1 of 5.9 GB free). 43/75 runs were done. Nothing lost: every finished call was cached |
| ~16:06 | While programs were being closed, an editor saved old copies over `Decision log.md`, `AUDIT.md` and a script (plus stray voice-typing text). Found and restored from git at 18:25; damaged copies were backed up |
| 16:05:45 | Resumed with 3 processes instead of 6 (each process uses only ~33 MB; the memory pressure came from the rest of the PC) |
| 16:44:48 | without_prob_kb crashed on a network timeout (OpenRouter did not answer within 90 s); restarted from cache |
| 17:10 | without_prob_kb crashed again (connection dropped mid-response); relaunched with automatic restart |
| 17:52:09 | full and without_feedback finished (25/25 each) |
| 18:12:30 | without_prob_kb finished: **75/75 runs done** |
| 18:13:41-18:20:28 | Retry pass for 3 runs with >=20% failed calls (inherited DEC-023 rule) |

**Actual totals**

- Wall-clock: 13:58:31 -> 18:20:28 = **4 h 21 min 57 s** (15,717 s).
  - Runs only (to 18:12:30): 4 h 13 min 59 s.
  - Time lost to the memory stop: ~15 min (last progress ~15:50, resumed 16:05:45).
- Compared with the projections:
  - sequential estimate 21.9 h -> actual 4.4 h, about **5x faster**;
  - first parallel ETA 17:49 -> actual 18:12:30, **23.5 min later**,
    because of the memory stop, dropping from 6 to 3 processes, and the
    two network crashes.
- My waiting: 18 progress checks between 14:15 and 18:12 (~4 h), plus questions about lost data and OpenRouter credits.
- Cost: **$0.24** (sum of per-call costs in the final call logs:
  $0.2409). Pre-registered estimate $0.246. OpenRouter balance
  afterwards: $5.00 - $1.99 used = $3.01 left.
- Calls: 11,625 in the final logs, all HTTP 200.

**Lessons:**
- Close other programs *before* a long run, not during it. Closing
  editors mid-run saved old copies over tracked files. After any
  interruption, check `git status` for files you did not mean to change.
- This PC has only ~6 GB RAM. 3 parallel processes were stable; 6
  were stopped under memory pressure (from the whole PC, not the
  processes).
- `openrouter_llm.py` does not catch network errors (timeouts, dropped
  connections), so one bad connection ends a process. Run with an
  automatic restart loop until that is fixed.
- API-bound experiments here are limited by per-call latency
(3-19 s, mean ~8 s), not by compute or cost. Independent (config, seed)
runs with their own caches should be sharded in parallel from the start.
Estimate wall-clock time (calls x mean latency / parallel shards) next to
the dollar cost before launching.

Approved: add the cache and parallel option, then pre-register DEC-031 with
these decisions.

Scope: all 843 eligible dev documents, ALL sentences (~6,870 calls, ~$0.13,
~3 h). Cost is approved.

Sentence selection: all sentences is the primary setting. The pilot sent only
gold evidence sentences, which is an oracle that tells the extractor which
sentences contain a relation. Add an evidence-only arm solely for
comparability with the pilot, and add a line to the manuscript's DocRED pilot
text stating that the pilot used this oracle setting.

Matching-key arms (all recomputed offline from the same extractions):
  (a) exact string, as now;
  (b) pure string normalisation - case/whitespace folding, article and
      punctuation stripping, no gold resources. This is the deployable arm
      and the PRIMARY comparison for the matching-key hypothesis;
  (c) gold-alias assisted, using DocRED's entity mentions - reported as an
      ORACLE UPPER BOUND and labelled as such everywhere. It cannot support
      a claim about what a deployed system would achieve.
Plus R3 (distinct-source counting) on the same extractions: first
out-of-domain test of the corrected rule.

Report for every arm: precision, recall, F1, admitted counts, contested-slot
counts and how many admitted anything. Pre-register what confirms and what
refutes the matching-key explanation, including what result would mean the
explanation is wrong.

Show me the pre-registration and the normalisation rules before running.

Write up DEC-032 as EVID-047 with this framing:

1. Extractor-recall hypothesis: CONFIRMED on Llama by the pre-registered
   rule (rho = 0.022, R2 below no aggregation, CI excludes zero). But report
   the split in the DeepSeek check plainly: DeepSeek recovers MORE
   corroborated facts (1.35% vs 0.75%, CI excludes zero) yet has a LARGER
   aggregation gap (-0.064 vs -0.040). State that low extractor recall is
   necessary but not sufficient to explain the failure, and note the likely
   reason: DeepSeek's higher no-aggregation F1 (0.081 vs 0.053) means it
   loses more when aggregation discards nearly everything.
2. R3 is scope-limited, and say why: it corrects repeat-counting, so it only
   acts when the extractor duplicates within a source. Llama 138 duplicates
   -> precision +0.054 [+0.015, +0.094]; DeepSeek 6 duplicates -> +0.004,
   CI includes zero. F1 is Negative for Llama and Null for DeepSeek by the
   pre-registered rule. This is the honest scope statement for the corrected
   rule and should appear in the Discussion too.
3. Cost was $0.686 against the $1.98 estimate; DeepSeek's actual multiplier
   was well below the 9.7x assumed.
4. The pilot correction stands regardless of these results: the 15-document
   pilot sent whole abstracts in a single call, so each document had one
   source and nothing could be aggregated. The pilot tested the extractor
   only, never the framework. Supersede it everywhere it appears.

Then update paper/main.tex and Results Summary.md: BioRED is now a
500-abstract second domain with an external baseline, and professor point 9
is addressed. Commit, push, stop.


Confirmed venue: Language Resources and Evaluation (LRE), not KAIS. This
resolves the word-cap uncertainty - LRE does not impose KAIS's 15,000-word
rule, so do not plan cuts around it. Still measure the float sizes exactly
for the record, but treat it as informational, not a constraint to cut to.

On DocRED official metrics: yes, do the recommended plan -
1. Add the one-sentence non-comparability caveat in main text (60-100 words).
2. Score official-style F1/Ign-F1/Evidence-F1 on the 845 already-extracted
   documents, in the supplement, with the two caveats stated (out-of-schema
   relations, unmatched entities).
3. Skip the $0.10 full-998-document extraction - it doesn't buy
   comparability with the literature either way, so it's not worth the
   scope creep this late.

Do not touch the notebooks or Learnings.md - I'll handle those.

After this, check the LRE submission guidelines/template specifically
(different from KAIS's) and confirm the manuscript matches: reference
style, structural requirements, declarations format. Report back before
changing anything.
changing anything.

Three decisions:

1. Approved: switch to sn-apa (author-date). Recompile and re-check length
   after the switch, since APA citations add words.

2. Trim toward the 24-27 page target from the earlier length plan, not the
   current 35. Do NOT cut any experimental result, caveat, or limitation.
   Cut candidates instead: tighten the DEC-031/032/033 write-ups (report
   final numbers and the verdict, move step-by-step methodology detail to
   the supplement where it isn't already there), reduce process narration
   ("we then checked...", "this confirms..."), and check for redundancy
   between the three Section-6.1-labeled results paragraphs you just found
   (DocRED, BioRED, protocol check) - fixing the duplicate-label bug may
   also surface duplicated framing text across them.

3. Fix the three-way "Section 6.1" label collision first, before anything
   else: give DocRED, BioRED and the protocol check their own numbered
   subsections (6.1, 6.2, 6.3 or similar) so cross-references are unique.

4. Draft the cover letter and declarations as TEMPLATES with clearly marked
   placeholders for: funding source, competing interests, author
   contributions, ethics/consent (state N/A if genuinely not applicable),
   and ORCID/homepage links. Do not invent any of these values - I will fill
   them in with Ebada.

Show me the trimmed length and the section-numbering fix before further
changes. Commit, push, stop.