# Stage 3d, second pass (PROPOSED 2026-09-29; nothing applied)

Measured basis (user's compile of a42c74f): body 25 pages holding 4,752
words + 4 tables, so **~190 words/page**. Getting to 20 pages means
removing about 950 words, or the equivalent in table space (a 4-row table
is about 0.6 page, or about 115 words).

Ground rules unchanged: no result, caveat or limitation is cut; only
tightening, de-duplication, and moves to the supplement. The same
number-preservation and caveat checks run afterwards.

| # | Item | Now | After | Saves | Q1 risk |
|---|---|---:|---:|---:|---|
| 1 | Merge the DocRED and BioRED subsubsections into one "DocRED and BioRED" subsection. Keep each corpus's F1 gap, raw/corroborated shares and oracle result; the per-corpus R3 detail is already summarised in 5.4 ("Outside the product domain") and kept in full in S7 | ~330 | ~200 | 130 | Low |
| 2 | Metrics: the DocRED/BioRED normalisation recipe -> S1 ("normalised entity-mention matching" stays); the "Sources and corroboration" definitions stay, fewer words | 259 | 170 | 90 | Low |
| 3 | Stronger-extractor table -> S2. Its 4 logprob values go into one sentence; the verbalized values are already in the text | 1 table | 1 sentence | ~115 equiv. | Low-moderate |
| 4 | Related work, DySECT: the trusted-source exemption detail -> S13; the attribution sentence shortened (attribution kept) | 301 | 230 | 70 | Low |
| 5 | Datasets: shorten the DocRED comparability sentence (pointer to S10 stays) and the BioRED description; the cross-document paragraph drops numbers repeated in 5.1 | 309 | 240 | 70 | Low |
| 6 | Aggregation settings: the token-logprob paragraph tightened (definition kept) | 172 | 120 | 50 | Low |
| 7 | Statistical protocol: keep the facts, with detail by pointer to S12/S19 | 160 | 110 | 50 | Low |
| 8 | Discussion 6.1: the "product domain masks the constraint" sentence -> a pointer to S16 | 274 | 200 | 70 | Low |
| 9 | DySECT results: tighten; all findings kept | 215 | 170 | 45 | Low |
| 10 | Introduction: tighten the contributions sentence | 370 | 330 | 40 | Low |
| **Subtotal (recommended, Option B)** | | | | **~730 words-equivalent, about 3.8 pages -> about 21 pages** | |
| 11 | Rule section: move the two proofs to S14 (statements stay) | 488 | 400 | 90 | **Moderate-high** |
| 12 | Limitations: move the numeric detail of "Small counts and protocol choices" (unparsable rates, rho excluding failures) to S11; the caveat statements stay | 557 | 470 | 90 | **Moderate-high** |
| **Total (Option A, full)** | | | | **~910 words-equivalent, about 4.8 pages -> about 20 pages** | |
