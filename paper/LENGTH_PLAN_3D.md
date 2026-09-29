# Stage 3d length plan (PROPOSED 2026-09-29, awaiting approval; nothing applied)

## Measured basis (user's compile of commit 842e8f9)

- elsarticle, preprint, 12pt, double spaced: 51 pages in total; the
  Introduction starts on p. 2 and the references on p. 41; the body
  (Introduction to Conclusion) is **38 pages**.
- The body holds **7,468 prose words + 6 tables**, so the measured density
  is **about 197 words per page, table space included**.
- The target of about 20 body pages is about **3,950 words at that
  density**. Moving 2 of the 6 tables to the supplement frees table space,
  so this plan aims at **about 4,150 words + 4 tables**. Expected: about
  20-21 pages. The next compile verifies this; trim further only against
  that real number.

## Ground rules (user)

No result, caveat or limitation is cut. The only moves are:
- tightening prose;
- removing redundancy (a number stated in both Setup and Results is kept
  once);
- moving secondary detail to the supplement, where every moved number
  stays available.

A caveat always stays with the claim it qualifies.

## Plan by section

| Section | Now | Target | Actions (-> supplement destination) |
|---|---:|---:|---|
| **1 Introduction** | 622 | 380 | Contributions (i)-(iv) restate numbers given in the abstract and Results: one sentence each with a section pointer (-180). Closing paragraph (ceiling note, pre-registration note, roadmap): one sentence (-70). Opening and RQ1-RQ4 unchanged. |
| **2 Related work** | 542 | 280 | Background "Adaptation" paragraph (tuning, self-improvement, continual learning, AutoML; closed-loop context) -> **S13** with its citations (-55). DySECT: the per-model recall figures become "5-8 points on four models" (figures -> S13), and the trusted-source and closed-loop attribution sentences are tightened, with attribution kept (-120). Evaluation Gap folded into two sentences at the end of the DySECT subsection; content kept (-60). |
| **3 The rule** | 619 | 370 | Section intro merged into the definition (-40). Remove "this paper cites it rather than claiming it" (said in Section 2) (-20). Ceiling note tightened, keeping "designed property, no measurable harm" (-30). Independence: drop the calibration clause (kept in Limitations) and the computational-cost pointer (S3 already has it) (-60). All three propositions, proofs, the example and the observed-violation sentence stay. |
| **4.1 Datasets** | 571 | 280 | Product-generator detail (schema, gold-set definitions, seeds, split files) -> **S1**, 2 sentences kept (-100). DocRED availability numbers (50.2%, 3.4%, coreference) stated once, in Results 5.1 (-70). DocRED comparability caveat: 1 sentence + pointer to S10 (caveat kept) (-45). BioRED description tightened (-30). Cross-document paragraph: construction and strata kept, numbers stated once in 5.1 (-80). |
| **4.2 Models** | 106 | 70 | CaRB sentence tightened (the 30-sentence comparison is already in S1) (-35). |
| **4.3 Hyperparameters** | 272 | 130 | The product loop's iteration schedule -> **S15** (-70). Confidence and token-logprob paragraphs tightened; definitions kept (-40). |
| **4.4 Metrics** | 388 | 220 | CaRB scorer detail -> **S1** (-40). DocRED/BioRED matching rule tightened (-40). Recall-denominator paragraph -> one clause (-35). "Sources and corroboration" tightened; both definitions kept (-40). |
| **4.5 Statistics** | 271 | 140 | Pre-registration paragraph: every fact kept (which analyses, commit verifiability, the rule-comparison exception, primary/secondary, null convention), fewer words, details in **S12/S19** (-100). Bootstrap paragraph tightened (-30). |
| **5 Results intro** | 47 | 0 | Redundant with the RQ-ordered headings. |
| **5.1 Availability** | 139 | 110 | Light tightening; the canonical place for these numbers. |
| **5.2 Within documents** | 838 + 3 tables | 430 + 1 table | **Move the DocRED and BioRED per-method tables -> S7** (every number cited stays in the text). DocRED text: matching-key narration shortened, keeping the "normalisation closes ~0%, oracle 7.3%" results, with the item counts -> S7 (-135). BioRED text: relation-validity shares -> S7 (-95). Protocol check: the decision-rule definition is already in S11, keep one sentence; the rule-overlap narration is stated once, in Limitations (-175). |
| **5.3 Across documents** | 176 + 1 table | 150 + 1 table | Tighten. |
| **5.4 Counting distinct sources** | 729 + 2 tables | 420 + 2 tables | Method paragraph (six rules, thresholds, bootstrap) shortened, rule definitions -> **S2** (-70). R4/R6: one sentence each with their results (R4 identical to R2, CI [0,0]; R6 below R2 on A), explanation -> S2 (-80). Stronger-extractor paragraph tightened; every number kept (-80). Within-sentence paragraph shortened, since it partly repeats 5.2 (-50). |
| **5.5 DySECT** | 248 | 190 | Tighten; all findings and both framings kept. |
| **6.1 Discussion: why aggregation fails** | 634 | 250 | Remove re-statements of 5.2 numbers (the argument is kept, numbers by pointer) (-250). DySECT-divergence paragraph tightened, both differences + "one reading" kept (-60). Cross-document paragraph tightened (-25). |
| **6.2 Discussion: why source counting helps** | 265 | 110 | The R3-vs-R4/R6 account is kept. The scope paragraph duplicates the Limitations "scope" caveat: stated once, in Limitations (-155). |
| **7 Limitations** | 697 | 470 | **No caveat removed.** Merge "Small admitted counts on DocRED" and "Extraction failures" into one paragraph; drop re-stated numbers where a section pointer suffices; absorb the scope caveat from 6.2 (-225). |
| **8 Conclusion** | 296 | 150 | Drop the RQ-by-RQ numeric recap (numbers are in the abstract and Results); keep the conclusion sentence and the three open experiments, one line each (-145). |
| **Total body** | **7,468 + 6 tables** | **~4,150 + 4 tables** | Expected about 20-21 double-spaced pages |

Not counted in the body: the abstract (233 words, page 1) and the
declarations (363 words), both unchanged.

## What moves to the supplement (nothing is deleted)

- S1: product generator detail; CaRB scorer detail.
- S2: rule definitions R1-R6 in full; the R4/R6 explanation.
- S7: DocRED and BioRED per-method tables; matching-key item counts;
  BioRED relation-validity shares.
- S13: the Background "Adaptation" paragraph with its citations; DySECT
  per-model recall figures.
- S15: the product loop's iteration schedule.

## Verification after applying

- A script check that every number in the pre-trim main text still
  appears in the trimmed main text or in the supplement. It lists any
  number found in neither, and none may be lost.
- The same check for every Limitations paragraph heading/caveat.
- Structural checks (braces, references, labels). Then commit, push, and
  the user compiles for the real page count.
