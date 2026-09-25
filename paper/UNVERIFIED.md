# Unverified items

Per the manuscript task's ground rule 2: anything not independently
verified this session is logged here rather than written into the
manuscript as if confirmed. Update this file every time a later section
adds a new unverified item, and remove an entry once it is verified and
the corresponding source is fixed.

## Section 2 (Related Work)

- **`erickson2020autogluon` (AutoGluon-Tabular) arXiv identifier.** The
  reference database (`refrence master copy.xlsx`) records only "2020,
  arXiv" with no identifier. I recalled a plausible arXiv number from
  training-data memory but did not verify it via search this session, so
  it has been left out of `references.bib` (journal field only, no
  `arXiv:` number). Verify on arxiv.org before submission and add the
  identifier back.
- **`das2020sagemaker` (Amazon SageMaker Autopilot) arXiv identifier.**
  Same situation as above -- database gives "2020, arXiv" with no
  identifier; not verified this session; left out of the `.bib` entry.
- **`edge2025graphrag` (GraphRAG) arXiv identifier.** Database gives
  "2025, arXiv" / "Preprint" with no identifier; not verified this
  session; left out of the `.bib` entry.

## Resolved since the first pass

- **Ji et al. (knowledge graph survey) volume/issue/pages.** A second
  instruction flagged that "the old reference list gives 32(5):2429-2443
  with no year." Re-checked via multiple independent sources (Monash
  University, Aalto University, University of Helsinki repositories,
  Semantic Scholar, NSF PAR, Google Scholar's indexed record with DOI) --
  all six independently agree on **volume 33, issue 2, pages 494-514,
  DOI 10.1109/TNNLS.2021.3070843** (2022 journal issue, 2021 early
  access). None matches "32(5):2429-2443" -- that figure does not appear
  in any source checked and is not used in `references.bib`. The existing
  `ji2021kgsurvey` entry (already 33(2):494-514 from the first pass) is
  correct as-is; no change made.
- **DySECT's "5-8 percentage points" recall claim.** Verified directly
  against the full PDF (not just the abstract/metadata), Table 1 and
  Section 5: "simply exposing the extractor to KB-derived hierarchical
  abstractions yields a recall improvement of 5-8% on 1st iteration of
  extractions compared to the baseline configuration without KB
  feedback," confirmed against Table 1's raw numbers (e.g. GPT-4.1
  22.80%->30.62%, a difference of 7.82 percentage points, positive-mode
  iteration 1). Section 2.7 now cites this with the exact per-model
  numbers rather than a paraphrase.
- **DySECT's KB is built on Theo (Mitchell et al., 1989).** Confirmed
  directly in the PDF's own text ("The knowledge base representation is
  built on top of Theo (Mitchell et al., 1989)") and its reference list.
  Added as `mitchell1989theo` in `references.bib` and cited in Section 2.7.
- **Author surname correction:** the lead author's surname is
  "Amin-Naseri" (hyphenated), per the PDF byline -- corrected from
  "Aminnaseri" in the bib entry's `author` field. The citation key
  `aminnaseri2026dysect` is left unchanged to avoid a churny rename.
- **DySECT/SLDE-AFT confidence formula match (new, high-priority finding,
  not from the original six-item list):** DySECT's Equations 1-2
  (Section 2.2 of their paper) are the same Conservative Noisy-OR with
  shrinkage (default lambda=0.75) plus mutual-exclusivity penalty
  C(t)=Cagg(t)/(m(t)+1) as SLDE-AFT's own formula, confirmed against
  `scripts/dec003_product_probkb_run.py`'s `SHRINKAGE = 0.75`. Section 2.7
  now states this plainly instead of claiming the two aren't comparable.
  **This affects the original novelty statement's Claim 3 wording** ("a
  novel...formula...not present in any prior extraction-KB system") --
  that specific claim is no longer supportable once DySECT is cited as
  related work, and needs the user's direction on how Section 4 and the
  Introduction's contributions list should be reworded.

- **Feedback-mode naming match and hierarchical-abstraction mechanism
  match (Section 2.7, new).** Both verified directly against the full
  DySECT PDF (arXiv 2603.06915v2, re-fetched this session): Section 4
  ("Feedback Modes") names the two directions "Encouraging (positive)"
  and "Prohibitive (negative)"; Section 2.2 ("Knowledge Base Growth")
  describes "KNN-based clustering over the children's embeddings" with
  an LLM proposing cluster labels. Cross-checked against SLDE-AFT's own
  design documents (`SLDE_AFT_Revised_Contribution_Document.docx`,
  `SLDE.docx`, extracted via their `word/document.xml`): both
  independently specify "Encouraging Mode"/"Prohibitive Mode" naming
  for the Feedback Controller and the exact phrase "Automatic
  hierarchical abstraction via KNN clustering and LLM-based subconcept
  labeling." Also verified directly against `src/feedback_builder.py`
  that the shipped code uses neither mode label as a literal string
  (stated in the text so the match isn't overstated as an
  implementation-level fact).

## What WAS verified this session (for contrast, not an action item)

- The DySECT citation (`aminnaseri2026dysect`) was independently verified
  via web search against the ACL Anthology (ID 2026.acl-demo.69) and
  arXiv (2603.06915) -- author names, venue, and identifier all confirmed
  to match the task's own description.
- The TACRED venue correction (EMNLP 2017, not ACL 2017) was confirmed
  both in `refrence master copy.xlsx` and independently via the ACL
  Anthology record (ID D17-1004) earlier in this project's audit work.
- The Lewis et al. RAG paper's duplicate listing ([19] and [54] in the
  old draft) was confirmed to be the same paper and consolidated to one
  `.bib` entry (`lewis2020rag`).
- All other bibliographic details in `references.bib` (venue, year,
  author list, page numbers where given) were taken directly from
  `refrence master copy.xlsx`'s `Full_Reference` field, not reconstructed
  from memory.

## Resolved 2026-09-25: model citations and hutter2019automl

- Llama 3 (arXiv:2407.21783), Mistral 7B (arXiv:2310.06825), GPT-4o
  System Card (arXiv:2410.21276) and Gemini 2.5 (arXiv:2507.06261):
  verified against the arXiv API records (title, first authors, date).
- DeepSeek-V3.2: citation block copied from the official
  deepseek-ai/DeepSeek-V3.2 repository README; OpenRouter's
  deepseek/deepseek-v3.2 maps to that repository.
- Claude Sonnet 5: cited to Anthropic's model documentation page
  (platform.claude.com/docs/en/models/sonnet-5/overview). The page has
  no publication date, so the bib year is the year of access (2026).
- GPT-4.1, GPT-4.1-mini, Kimi K2.5 and LLaMA-3.3 70B are named in
  DySECT without any citation of their own (checked in the arXiv HTML
  of 2603.06915v2). They are cited "as DySECT reports them": every
  mention in main.tex sits next to a citation of aminnaseri2026dysect.
- hutter2019automl: changed from @incollection to @book (an edited
  volume); editors, series, publisher and DOI verified against Crossref.
  BibTeX's "empty author / empty booktitle" warnings are gone.

## Open 2026-09-25: target-journal requirements (Stage 5)

Springer's journal guideline pages (link.springer.com/journal/10579 and
/10115 submission-guidelines) refused automated access (cookie wall), so
these could only be confirmed via search snippets and must be checked in
a browser before submission:
- **Reference style** for LRE and for KAIS. main.tex uses Springer's
  numbered style (sn-mathphys-num) for both as a placeholder; switching
  to author-year is a one-word change in the class option.
- **Required declarations** for each journal. main.tex lists the
  template's standard set (funding, competing interests, ethics,
  consent, data/materials/code availability, author contribution).
- Confirmed via search snippet only: LRE asks for a 150--250-word
  abstract; KAIS limits manuscripts to 15,000 words (5,000 for short
  papers), per its editorial FAQ (kais.zhonghuapu.com).
- **Figure formats**: Springer's general artwork guidance favours vector
  (EPS/PDF) for line art. fig_finetuning.png, fig_rival_ceiling.png and
  fig_scalability.png are 300-dpi raster images carried over from the
  Word draft with no generating script in the repository.
