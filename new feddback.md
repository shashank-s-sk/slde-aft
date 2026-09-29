Hi Shashank,
Good progress. To reach Q1 level, the paper needs the following.
Must add (experiments)

Test our findings on DySECT's released code: does it deduplicate by source, and do the ceiling and R3 apply there?
Add one multi-document redundancy corpus (e.g. TAC KBP slot filling or a redundant subset you construct). DocRED and BioRED are single-document, so they are a poor test of corroboration.
Add a token-logprob confidence variant if it is cheap. Verbalized confidence in [0.80, 0.96] makes the score almost count-driven.
Add a rerun of the main aggregation comparison with one stronger extractor, so the conclusion does not rest on an 8B model.
Must change (framing)

Remove the word "defect" until the DySECT code check is done. Write "in our implementation".
Lead with the corroboration-availability and extractor-recall findings, then R3.
Reduce the rival ceiling to one proposition with a note that it is a designed property. It is elementary, and the paper itself shows no harm from it.
Move the closed-loop, fine-tuning and synthetic-domain material to the supplement or a separate paper.
Cut to about 20 pages.
Must fix (consistency)

The same Llama sentence-level runs give 0.26% and 0.75% in Sections 6.2 and 6.3, but 0.17% and 0.73% in Table 4. Reconcile them or define verified versus unverified corroboration.
Table 1 gives R3 minus R2 precision on dataset A as +0.106, but Table S2 gives +0.099. Explain or correct.
"221 times" in Proposition 8 and Section 6.6 should probably be "2 to 21".
Replace "real-data snapshots" with "snapshots of real LLM extractions on synthetic products".
Define "source" precisely. Proposition 8 talks about re-reads, but the DocRED repeats are within-sentence duplicates.
State which analyses were primary versus secondary, given the many confidence intervals.
Must clean up (presentation)

Remove the internal jargon (DEC-, EVID-), "an earlier account in this project" and the superseded pilots from the main text.
Give verifiable pre-registration evidence (timestamped commit hashes or OSF) and say which analyses were pre-registered.
Fill the empty fields in about 15 references and fix proceedings capitalization. The ACL Anthology lists the DySECT first author as Aminnaseri.
Use an institutional email for the corresponding author.
Must align (cover letter and venue)

The cover letter must match the paper. Do not claim "all results multi-seed" (DocRED, BioRED and scalability are single runs) or "5 external systems" (only DeepSeek runs at full scale).
Hold off on Language Resources and Evaluation. It is Q1 only in Linguistics and Language, and its scope is resources and evaluation methodology. After the experiments we compare Knowledge-Based Systems and Expert Systems with Applications, with quartile checked in Scopus.