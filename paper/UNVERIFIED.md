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
