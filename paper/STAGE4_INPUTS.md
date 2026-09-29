# Stage 4: what the authors need to supply (one pass)

Everything below goes into `paper/main.tex` (title page and declarations)
and `paper/cover_letter_DRAFT.md`. Nothing here is invented. Items marked
**Required** block submission.

## A. Author details

| # | Item | For | Required? | Current value |
|---|---|---|---|---|
| A1 | Corresponding author's **institutional email** | title page, cover letter | Required (professor's request) | Gmail address |
| A2 | Corresponding author's **affiliation and full postal address** | title page | Required by Elsevier | "Hopn UG, Germany" (is this right?) |
| A3 | **Prof. Ebada's email** | title page | Required | placeholder |
| A4 | **Prof. Ebada's affiliation** (the same as A2, or a university?) | title page | Required | assumed the same as A2 |
| A5 | ORCID iDs for both authors | title page, cover letter | Recommended | none |

## B. Declarations in the manuscript

| # | Item | What to send |
|---|---|---|
| B1 | **Declaration of competing interest** | Either "no competing interests" (standard sentence already drafted) or the interests. **Check this:** the affiliation is a company (Hopn UG). If Hopn UG has any commercial interest in knowledge-base or extraction products, declare it. |
| B2 | **CRediT roles** | For each author, pick from: Conceptualization; Methodology; Software; Validation; Formal analysis; Investigation; Resources; Data curation; Writing - original draft; Writing - review & editing; Visualization; Supervision; Project administration; Funding acquisition. |
| B3 | **Funding** | The source and grant number, or confirm "no specific grant" (sentence already drafted). Include API credits or compute paid by an employer or grant, if any. |
| B4 | **AI declaration** | Approve the text now in `main.tex` (before the references; the same as `paper/AI_DECLARATION_DRAFT.md`), or send edits. |
| B5 | **Data availability** | Choose one: (a) archive the submitted version on Zenodo (free; gives a DOI; I can prepare the release notes); or (b) cite the commit hash of the submitted version (I fill it in at submission). |

## C. Cover letter (`paper/cover_letter_DRAFT.md`)

| # | Item | What to send |
|---|---|---|
| C1 | **Venue** | DONE 2026-09-29: **Knowledge-Based Systems** (user's comparison: both Q1, IF 9.62 vs 9.4, similar APC; KBS scope fits better). ESWA paragraph deleted; `\journal{}` set. |
| C2 | Not under consideration elsewhere; all authors approve | Confirm both. |
| C3 | Preprint | "None", or server and identifier. |
| C4 | Suggested / excluded reviewers | Optional: names, affiliations, emails, and reasons for exclusions. |
| C5 | Date and signature | Filled in at submission. |

## D. Files and checks at submission

| # | Item | Who |
|---|---|---|
| D1 | **Highlights**: approve or edit `paper/HIGHLIGHTS_DRAFT.md` (5 bullets, all <= 85 characters) | You |
| D2 | **Visual proofread of the compiled PDFs** (main and supplement). No one has read the rendered pages yet, and three restructuring passes changed many cross-references | You (I cannot render PDFs here) |
| D3 | Compile the supplement once | DONE 2026-09-29: 33 pages, 0 errors, 0 undefined references or citations |
| D4 | Confirm KBS's abstract word limit (ours: 233 words) and keyword limit (ours: 6) | **You**: the KBS guide on ScienceDirect loads only in a browser (fetching it returns an empty JavaScript page), so I could not verify it |
