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

## 6. Stage 2 (clean-up) - APPLIED 2026-09-29, awaiting review

- **Jargon:** no DEC-/EVID- identifiers, "this project", or "an earlier
  account" remain in the main text's visible text (the % comments are
  kept as the audit trail). Superseded 15-document pilots were removed
  from the main text (they stay in Suppl. S7). The CaRB 5-system
  comparison is now a one-line pointer to Suppl. S1. The DocRED
  discussion now opens with the exact-string hypothesis rather than "an
  earlier account". Supplement IDs were replaced with descriptive names.
- **Verifiable pre-registration:** new Suppl. Table S19 (label
  tab:s13-prereg) gives each pre-registration commit hash and time, its
  first-result commit, and the logged run start where one exists
  (DocRED: started 48 s after the pre-reg commit; BioRED: 16 s after).
  The main text states this. **Honest exception:** the offline rule
  comparison's specification was committed together with its first
  results (36da4dd), so its order is not verifiable; the text says so.
  **Carry-forward:** add rows for DEC-036 (2f3a731) and DEC-038 (f87e91a)
  when they enter the paper.
- **References:** all 54 checked against authoritative sources (ACL
  Anthology BibTeX, Crossref, JMLR, PMLR, NeurIPS proceedings, arXiv API).
  Fixed:
  - Venue names are now the full official ones (no "Proceedings of ACL").
  - Missing volumes and pages were filled.
  - Five preprints now cite their published versions (LoRA, FLAN and
    Self-RAG at ICLR; the continual-learning survey in TPAMI; the
    explainability survey in ACM TIST; OA-Mine at WWW 2022).
  - **Wrong authors corrected:**
    - Open-IE survey: 5 wrong names.
    - DocRED: one missing Liu.
    - SageMaker Autopilot: 4 missing authors.
    - Llama 3 and Gemini 2.5: wrong 21st name and a silently truncated
      list; now 20 names + others.
  - DySECT uses "Aminnaseri" (Anthology form). Prose uses \citet only, so
    naming is consistent.
  - Remaining entries without pages are legitimate (ICLR, arXiv-only,
    an edited book).
- **OPEN (needs the user):** institutional email for the corresponding
  author (currently a Gmail address; affiliation Hopn UG). Prof. Ebada's
  email is still a placeholder.

## 7. Stage 3a (move to supplement) - APPLIED 2026-09-29

Moved verbatim to the supplement:
- S13: framework (modules).
- S14: order-invariance, monotonicity, saturation, conflict-penalty
  propositions.
- S15: fine-tuning model; multi-seed/MDE protocol.
- S16: results on calibration, provenance, ablation, fine-tuning, closed
  loop, scalability and error analysis, with 3 figures and their tables.
- S17: discussion of ablations, fine-tuning and calibration.
- S18: limitations of those results (provenance gate, feedback not
  self-supervised, ablation power, closed-loop single seed, software
  versions, resource use, unindexed scan).

The API model-identifier caveat stayed in the main text as "Model
versions". The supplement gained amsthm, natbib and a bibliography
(apalike). Cross-document references were rewritten (main -> "Supplementary
Section S1x"; supplement -> named main-text sections/equations).

After the move the main text is about 6,990 prose words, 4 tables and
0 figures (before: 10,300 words, 11 floats). The intro, abstract and
conclusion still describe moved results; they are rewritten in 3c.

**Next:** 3b (add the new results). Measuring 3d needs a real
double-spaced compile (user instruction). Title decision needed before 3c.
AI declaration draft: `paper/AI_DECLARATION_DRAFT.md` (awaiting user
review).

## 8. Stage 3b (new results) - APPLIED 2026-09-29, review stop

Added to main.tex:
- Setup: "Cross-document redundancy subset" paragraph (GEO/OTHER strata
  defined, document list pre-committed); DeepSeek-V3.2 also re-extracts
  the product snapshots and the subset; "Token-logprob confidence"
  paragraph.
- After Table 1: "A stronger extractor and token-logprob confidence"
  paragraph + Table tab:dec036 (observed differences). The primary rule
  HOLDS (A robust, B borderline). F1 at the selected threshold: A +0.032
  [0.005, 0.075], B null. The Llama rerun reproduces A and is weaker on B.
  The logprob finding is stated as approved.
- Results: new subsection "Corroboration Across Documents" + Table
  tab:crossdoc (rows generated from analysis_result.json). New subsection
  "The Rule in DySECT's Released System": two-part framing (by design;
  active 87.5%); penalty never fired; m(t) is type-level. Step A appears
  ONLY as "a check ... found no material effect" (no numbers, per the
  user). The 78/100 overlap is stated as a property of the released code.
- The pre-registration list in Statistical Protocol now names both new
  analyses.

Added to supplement: S12 status rows (stronger extractor, cross-document,
DySECT audit) and S19 pre-registration rows (2f3a731 -> ad40563; f87e91a
-> 678f373). The Step A recall check is not listed (internal).

Decisions recorded: title (a) "How Much Corroboration Do LLM Extractors
Realise? ..." (apply in 3c). The AI declaration was revised (broad scope,
no versions, literature-search bullet, no-generative-figures statement).
3d: add real double spacing, commit and push; the user compiles and
reports the page count.

## 9. Stage 3c (reframe) - APPLIED 2026-09-29

- Title (a); new abstract (233 words): availability -> realised
  (within/across) -> R3 (+ stronger extractor, logprob) -> DySECT.
- Intro: three conditions (supply, realise, independence); RQ1-RQ4 in
  that order; 4 contributions; the rival ceiling is mentioned as a
  designed property; the closed loop is a pointer to the supplement.
- Related work: DySECT rewritten with "by design; we test that
  independence assumption" and the m(t) disambiguation (item 2 of the
  Stage C notes). The gap is restated as three unmeasured things. The
  Evaluated Framework section became a paragraph opening Section 3.
- Rule section: definition + m(t) note after Eq. (2). "Properties Used":
  corroboration, **rival ceiling as ONE proposition with an inline proof
  + "designed property, no measurable harm" note**, independence ("DySECT
  adopts this by design"). The boundedness proposition moved to S14; the
  corollary was removed (its content is in the note).
- Results reordered: 5.1 availability (new), 5.2 within documents
  (DocRED, BioRED, protocol as subsubsections), 5.3 across documents, 5.4
  counting distinct sources (the old empirical-validation block,
  retitled, + DEC-036, + a within-sentence/cross-document paragraph), 5.5
  DySECT. The CaRB subsection became one sentence in Setup (Models).
- Setup: the product domain is reframed as "product snapshots" (real LLM
  extractions of synthetic products); fine-tuning leakage and confidence
  template details went to the supplement; the recall-denominator and
  bootstrap paragraphs no longer mention fine-tuning.
- Discussion: "defect" is gone (-> "different parts of the rule", "The
  same repeat counting"); cross-document paragraph added; DySECT
  divergence paragraph notes the released-system finding, labelled "one
  reading"; the R3 account is linked to the DEC-036 rerun.
- Limitations: "Synthetic products in the rule comparison"; "Confidence
  carries little information" (logprob finding); "The extractors"
  (DeepSeek now tested on every main-text conclusion); new "The
  cross-document subset" and "The DySECT audit".
- Conclusion rewritten around the three conditions, the RQs and the open
  experiments.
- Supplement: new title; range proposition in S14; the two-template
  confidence caveat in S18; "Table 1 of the main text" references made
  descriptive (the table order changed).

Size: about 7,630 prose words, 6 tables, 0 figures, abstract 233 words.
**Next: 3d** - add real double spacing to the template, commit and push;
the user compiles and reports the page count; trim against it.
AI declaration still awaiting the user's final approval before insertion.

## 10. Stage 3d step 1 - double-spaced Elsevier build, pushed for the user's compile

- main.tex front and back matter converted from Springer sn-jnl to
  Elsevier elsarticle (preprint,12pt,authoryear) with setspace
  \doublespacing. The body is unchanged. Both finalist venues (KBS, ESWA)
  are Elsevier with this template, so the choice is venue-neutral. The
  sn-jnl version is in git history (b2eccad).
- Elsevier back matter: competing interest, CRediT, funding
  (placeholders); data and code availability (existing text); the AI
  declaration (revised draft text, marked pending approval) before the
  references; bibliography style elsarticle-harv.
- The user compiles (pdflatex, bibtex, pdflatex x2) and reports the real
  page count; 3d trimming is done against that number, not a word-count
  estimate (user instruction).
- Supplement untouched (compiled separately; not counted).
