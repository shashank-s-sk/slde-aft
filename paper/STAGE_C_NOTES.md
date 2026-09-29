# Stage C wording notes (hold — do NOT apply until the Stage C writing pass)

Decisions recorded 2026-09-29 from DEC-035 / EVID-050. Apply only in the
Stage C manuscript pass, together with the rest of `new feddback.md`.

## 1. Replace "defect" with the by-design framing (user-approved 2026-09-29)

Approved wording: DySECT counts repeated observations, including re-reads
of one source, as independent support **by design**; this paper tests that
independence assumption. Basis: DySECT Sect. 2.2, "Frequencies are
incorporated by treating f_i as repeated independent support for the same
confidence value (equivalently, by exponentiating the corresponding term)".

Locations in paper/main.tex (line numbers as of commit a22f672):
- l.1456-1457 "they target different defects" -> e.g. "they target
  different parts of the rule".
- l.1469 "The same defect appears outside the product domain" -> "The same
  repeat counting appears ...".
- Anywhere R3 is described as fixing an error: use "in our implementation"
  (professor) and "tests the independence assumption".
- supplementary.tex / cover letter: no "defect" found at time of writing;
  re-grep at Stage C.

## 2. Disambiguate m(t): ours != DySECT's (user-approved 2026-09-29)

DySECT's m(t) = "number of mutually exclusive instances detected for t";
in its code (`findAllMutuallyExclusiveInstances`) this is a TYPE-LEVEL
count: concepts declared mutually exclusive with the subject/object type
of which the entity is also an instance. Ours = number of rival object
values already accepted for a designated single-valued (subject,
predicate) slot. Same formula C = C_agg/(m+1), different m. In DySECT's
released KB the division fired 0 times out of 61,676 stored confidences.

Add one explicit sentence at each place that implies they are the same:
- l.76-78 (intro): "a conservative Noisy-OR with a mutual-exclusivity
  penalty for single-valued predicates" is attributed to DySECT, but
  DySECT's penalty is type-level, not per single-valued predicate.
- l.224-228 (related work, "What this paper takes from DySECT"): "the
  mutual-exclusivity penalty C = C_agg/(m(t)+1), which is the rule
  evaluated throughout this paper" -> add: DySECT's m(t) counts type-level
  mutual-exclusion conflicts; this paper keeps the functional form but
  counts rival values of a designated single-valued slot, so the penalty
  and the rival ceiling are properties of our instantiation.
- l.396-397 (Eq. conflict definition): add "(this reinterprets DySECT's
  m(t), Sect. 2.2)".
- Abstract (l.54): "The rule studied is the conservative Noisy-OR with a
  mutual-exclusivity penalty that the DySECT system published ..." -> say
  "adapted from DySECT", or state the reinterpretation in the body only.
- Rival-ceiling proposition: professor asked to reduce it to one
  proposition noted as a designed property; the note should say it holds
  for our m(t). For DySECT's code it also holds algebraically at its only
  live threshold (0.5), except a seed/trusted triple (C_agg=1) with k=1,
  which scores exactly 0.5 and passes its ">= 0.5" test.

## 3. Optional sentence on DySECT's released run (EVID-050)

In DySECT's released KB, 4,030 of the 4,604 generalization edges eligible
for its DocRED prompt (87.5%) pass its 0.5 threshold only through repeated
observations of the same source/document. Use only if the DySECT rerun
(DEC-035b) is not done; otherwise report the rerun result.

## 4. Write-up framing approved 2026-09-29 (hold for the manuscript pass)

- **DySECT (EVID-050/051): two parts.**
  (i) The independence violation is real and structural. In DySECT's
  released KB, 87.5% of the prompt-eligible generalization edges pass its
  0.5 threshold only through repeated observations of the same
  source/document.
  (ii) Its effect on DySECT's own recall is small. Repeat-counted vs
  source-deduplicated KB: +0.80 pts, 95% CI [-0.77, +2.35], crossing 0 and
  below the pre-registered 2-pt threshold (Llama-3.3-70B, gpt-4.1-mini
  judge). Step A was an internal go/no-go; cite it at most as "a check found
  no material effect".
  The 78/100 overlap between DySECT's KB-building documents and its 500
  evaluation documents is a property of its **released code**
  (`data_prep.py`), not a claim about the runs reported in its paper.
- **DEC-036 (EVID-052).** Dataset A is a robust replication with the
  stronger extractor: DeepSeek R3-R2 precision +0.227 [0.038, 0.417];
  Llama rerun +0.098 [0.020, 0.215]. Dataset B is weak or borderline for
  both extractors: DeepSeek +0.008 [0, 0.027]; Llama +0.012 [0, 0.033].
  NOT a uniform two-for-two confirmation.
- **Logprob finding, stated precisely.** Token-logprob confidences are
  more compressed than verbalized ones (median about 1.0 for nearly all
  triples, vs about 0.91 verbalized). Spearman correlation between the
  Noisy-OR score and the observation count stays at 0.89-0.95 under either
  confidence. The count-driven pattern is therefore not caused by the
  prompt's [0.80, 0.96] wording.

## 5. Stage 1 (consistency fixes) - APPLIED 2026-09-29, awaiting review

All six "Must fix" items from `new feddback.md`:
1. **0.26/0.75% vs 0.17/0.73%.** These are two definitions, both correct:
   "recovered from >= 2 sentences" (g2_raw) and "corroborated" (g2_verified:
   >= 2 genuinely supporting sentences). Both are now defined in Metrics
   ("Sources and corroboration") and labelled in 6.2/6.3. The abstract,
   intro and conclusion now say "corroborated": their 3.1% ceiling is the
   verified share; the raw share would be 3.95%.
2. **+0.106 vs +0.099.** Table 1 printed the bootstrap *mean*; Table S2's
   values give the *observed* difference (0.9322 - 0.8333). Table 1, the
   F1-selected figures in the text (+0.0106 -> +0.0101) and the supplement's
   bootstrap table now all report observed differences with percentile
   CIs. Every other analysis script already reported observed differences.
3. **"221 times"** -> "2 to 21 times" (both places; an en-dash lost in
   conversion).
4. **"real-data snapshots"** -> "snapshots of real LLM extractions on
   synthetic products" (abstract, intro, conclusion). "Real data" ->
   "real LLM extractions" in the calibration statements and the subsection
   title.
5. **"Source"** is defined precisely (Metrics). Prop. (independence) now
   covers both shared-source mechanisms: re-reads (product domain) and
   within-sentence duplicate emissions (DocRED/BioRED).
6. **Primary vs secondary.** The Statistical Protocol paragraph was
   rewritten. The new Supplementary S12 table gives the status of every
   analysis. DEC-026's fixed-tau Table 1 is now labelled **secondary** (it
   was added after first results); its pre-registered primary is F1 at the
   selected threshold.

**Carry-forward for later stages:** when DEC-036 goes into the paper, use
OBSERVED differences, not the EVID-052 bootstrap means:
- DeepSeek R3-R2 precision: A **+0.229** [0.038, 0.417]; B **+0.008** [0.000, 0.027].
- Llama rerun: A **+0.095** [0.020, 0.215]; B **+0.013** [0.000, 0.033].

No LaTeX compiler is available on this machine. Checked statically: braces
and environments balance, every \ref has a label. A PDF compile is still
needed.
