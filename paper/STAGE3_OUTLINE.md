# Stage 3 outline: restructure, integrate new results, cut to about 20 pages

Status: PROPOSED 2026-09-29, awaiting user approval. No manuscript edits yet.

## Where the paper is now

- Main text: about 10,300 prose words and 11 floats (8 tables, 3 figures),
  plus a 251-word abstract and 54 references. It last compiled to 35 pages
  in total.
- The target of about 20 pages in total (sn-jnl default layout, references
  included) means about 6,500-7,000 prose words, 5-6 tables, at most 1
  figure, and about 40 references.

## New spine (the professor's order)

The paper's question becomes: *how much corroboration do resources
provide, how much do extractors realise, and what does counting distinct
sources buy?* The closed loop leaves the main text.

| # | Section | Content | Words |
|---|---|---|---:|
| - | Abstract | Rewritten: availability -> extractor recall (within and across documents) -> R3 (robust to a stronger extractor and to the confidence source) -> DySECT's released code | ~200 |
| 1 | Introduction | Problem; the rule attributed to DySECT (m(t) disambiguated); 3 RQs; 4 contributions; one line that the closed-loop evaluation (all nulls or negatives) is in the ESM | ~700 |
| 2 | Related work | Background (condensed) + DySECT (two-part framing: "by design; we test that independence assumption") | ~600 |
| 3 | The rule and its properties | Definition; **definition of a source**; the independence proposition; the corroboration proposition; **rival ceiling as ONE proposition, noted as a designed property with no observed harm**; other propositions and proofs -> ESM | ~600 |
| 4 | Setup | Corpora: DocRED, BioRED, the **cross-document subset**, and the product snapshots A/B (stated as real LLM extractions on synthetic products). Extractors, units, confidence variants (verbalized/logprob), metrics, statistics (primary/secondary; Table S19) | ~900 |
| 5.1 | Results: availability | Annotation-level corroboration (DocRED 50.2% / 3.4%, BioRED 35.1%); cross-document recurrence (4.8%, 65% geography) | ~250 |
| 5.2 | Results: extractor recall is the binding constraint | Within document (DocRED/BioRED + protocol check, existing table); **across documents (DEC-038, GEO/OTHER table)**; aggregation lowers F1 everywhere | ~700 |
| 5.3 | Results: counting distinct sources (R3) | Product snapshots (primary F1-selected; secondary tau=0.88 table); **stronger extractor (DEC-036: A robust, B borderline)**; **logprob confidence (count-driven either way)**; within-sentence duplicates; R3-doc precision across documents | ~800 |
| 5.4 | Results: DySECT's released system | Repeat counting is documented and active (87.5%); penalty never fired; m(t) type-level; effect on recall small (one sentence, "a check found no material effect"); 78/100 overlap stated as a property of the released code | ~350 |
| 6 | Discussion | Why aggregation fails (recall, coreference); when source counting helps (the two repeat mechanisms); implications for DySECT-like systems | ~700 |
| 7 | Limitations | Only caveats for claims still in the main text (moved claims take their caveats to the ESM, per the existing rule) | ~600 |
| 8 | Conclusion | | ~250 |

**Main-text floats (6):**
1. Availability vs realised corroboration (new, merges existing numbers).
2. Protocol check (existing).
3. Cross-document GEO/OTHER (new).
4. R3 vs R2 on product snapshots (existing Table 1, with DEC-036 DeepSeek/logprob columns added).
5. DySECT audit (new, small).
6. Optionally the architecture figure, shrunk. Recommendation: drop it.

## Moved to the ESM (supplement), with all their caveats

- The closed-loop framework description: feedback controller, synthetic
  supervision.
- The 30-seed module ablation (null).
- Leakage-free fine-tuning (negative).
- The closed-loop integration test.
- The provenance filter and its corruption check.
- Calibration (ECE) and the reliability figure.
- Scalability.
- Product-domain error analysis.
- CaRB extractor quality (one sentence stays in Setup).
- The remaining formal propositions and proofs.
- The rival-ceiling figure.

The supplement currently has no bibliography. It gets one for the
citations the moved material needs.

## Decisions I need from you

1. **Meaning of "synthetic-domain material".** My reading: move the
   closed-loop, fine-tuning, provenance, calibration, scalability and
   product error-analysis material, but KEEP the product snapshots A/B as
   R3 evidence. They are real LLM extractions, they are the basis of
   Table 1, and the professor asked for that comparison to be rerun with a
   stronger extractor. Agree?
2. **ESM or a separate paper for the closed loop and fine-tuning?**
   Recommend the ESM now: the nulls stay reported and nothing is lost. A
   separate paper remains possible later.
3. **Title.** The current title ("... in Closed-Loop Information
   Extraction") no longer fits. Options:
   (a) "How Much Corroboration Do LLM Extractors Realise? Source-Counted
   Noisy-OR Aggregation Across Sentences and Documents";
   (b) "Corroboration-Gated Aggregation for LLM Information Extraction:
   Resource Availability, Extractor Recall, and Source Counting".
   Recommend (b).
4. **What "~20 pages" counts.** I will count the sn-jnl default single
   column including references (the referee double-spacing option would
   roughly double it). Confirm.

## Execution (commit after each; stop for review after 3b and after 3d)

- **3a:** move material to the ESM unchanged, with caveats; add the
  supplement bibliography.
- **3b:** add the new results: DEC-038 table and text, DEC-036 columns and
  text (observed differences), the DySECT subsection, and S19 rows for
  both pre-registrations. -> **review stop**
- **3c:** reframe: new abstract, introduction, RQs and contributions,
  reordered Results, discussion. Apply the Stage C wording notes: "by
  design" instead of "defect", the m(t) sentences, rival ceiling as one
  proposition.
- **3d:** trim to target. Report the word and float counts; the page
  count still needs a compile on your side. -> **review stop**

The cover letter (Stage 4) comes after Stage 3. The venue stays on hold.
