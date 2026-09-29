# Feedback round 2: decisions index

This file is an index. It maps each item of the professor's second-round
feedback (`new feddback.md`, received 2026-09-29) to the decisions and
evidence that answer it. Full rationale lives in `Decision log.md` (DEC-xxx)
and full numbers in `Evidence log.md` (EVID-xxx). Keep this file in sync
when a status changes.

Pre-registration commits: `2f3a731` (DEC-036 and the DEC-035b staged plan,
committed before any of those runs). Result commits: `ad40563`, `fc5a5eb`,
`f49eec5`.

## Must add (experiments)

| # | Feedback item | DEC | EVID | Status | Key result |
|---|---|---|---|---|---|
| 1 | Test findings on DySECT's released code: source deduplication, ceiling, R3 | DEC-035, DEC-035b | EVID-050, EVID-051 | DONE | No source dedup. Repeat counting is DySECT's **documented design** (Sect. 2.2) and active in its released KB: 87.5% of prompt-eligible generalization edges pass 0.5 only via repeats. The mutual-exclusion penalty fired 0/61,676; DySECT's m(t) is type-level, ours counts rival slot values. Effect on DySECT's own recall (Step A, internal): +0.80 pts [-0.77, +2.35], below the 2-pt threshold, NO-GO; Step B not run. |
| 2 | Add a multi-document redundancy corpus | DEC-037 | EVID-053 | DATA CHECK DONE; subset design being costed | TAC KBP/LDC dropped (same reasoning as DEC-021). DocRED dev+train: 2,179/45,212 distinct gold facts (4.8%) recur across documents; 65% are geography relations. Any subset is reported stratified by geography vs other relations. |
| 3 | Token-logprob confidence variant | DEC-036 | EVID-052 | DONE | Logprob confidences are more compressed than verbalized ones (median about 1.0). Score-vs-count correlation stays 0.89-0.95 under both, so the count-driven pattern is not caused by the [0.80, 0.96] prompt wording. |
| 4 | Rerun the main aggregation comparison with a stronger extractor | DEC-036 | EVID-052 | DONE (pre-registered rule: HOLDS) | DeepSeek-V3.2 R3-R2 precision: A +0.227 [0.038, 0.417] (robust); B +0.008 [0, 0.027] (weak or borderline, as is Llama's +0.012). Not a uniform two-for-two confirmation. |

## Must change (framing), must fix (consistency), must clean up, must align

All of these are writing tasks, held for the Stage C manuscript pass
(experiments first). Approved wording and the locations to change are in
`paper/STAGE_C_NOTES.md`:

- "defect" replaced by "by design; we test that independence assumption"
  (user-approved 2026-09-29).
- One disambiguating sentence wherever the paper equates our m(t) with
  DySECT's (user-approved 2026-09-29).
- Write-up framing for DySECT (two parts), DEC-036 (A robust, B
  borderline) and the logprob finding (user-approved 2026-09-29).
- Consistency items diagnosed so far:
  - "221 times" is the `2--21` en-dash lost in conversion (main.tex l.534).
  - The DEC-026 replay reproduces Table 1's +0.106 exactly
    (bootstrap mean, dataset A); the +0.099 in Table S2 still has to be
    traced.
  - 0.26%/0.75% vs 0.17%/0.73% is not yet reconciled.
- Venue: LRE on hold. KBS vs ESWA to be compared after the experiments.

## Other decisions this round

- 2026-09-29: OpenRouter credit ran out mid-run. All contaminated outputs
  were discarded unscored; scripts now stop on a 402. See the Decision log
  notes under DEC-036.
- DeepSeek logprob runs are pinned to DigitalOcean. AtlasCloud returned no
  logprobs and Friendli rejects top_logprobs.
