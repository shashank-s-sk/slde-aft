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
