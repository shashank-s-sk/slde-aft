# Stage 4: what the authors need to supply (one pass)

Everything below goes into `paper/main.tex` (title page and declarations)
and `paper/cover_letter_DRAFT.md`. Nothing here is invented. Items marked
**Required** block submission.

## A. Author details

| # | Item | For | Required? | Current value |
|---|---|---|---|---|
| A1 | Corresponding author's **institutional email** | title page, cover letter | Required (professor's request) | Gmail address |
| A2 | Corresponding author's **affiliation and full postal address** | title page | Required by Elsevier | "HOPn UG, Germany" (is this right?) |
| A3 | **Prof. Ebada's email** | title page | Required | placeholder |
| A4 | **Prof. Ebada's affiliation** (the same as A2, or a university?) | title page | Required | assumed the same as A2 |
| A5 | ORCID iDs for both authors | title page, cover letter | Recommended | none |

## B. Declarations in the manuscript

| # | Item | What to send |
|---|---|---|
| B1 | **Declaration of competing interest** | Either "no competing interests" or the interests. **Check this:** the affiliation is a company (HOPn UG); if HOPn UG has any commercial interest in knowledge-base or extraction products, declare it. **KBS requires this as a separate Word document generated with Elsevier's declarations tool (declarations.elsevier.com) and uploaded at submission**, in addition to the statement in the manuscript (see D5). |
| B2 | **CRediT roles** | For each author, pick from the 14 official names, exactly as written: Conceptualization, Data curation, Formal analysis, Funding acquisition, Investigation, Methodology, Project administration, Resources, Software, Supervision, Validation, Visualization, Writing - original draft, Writing - review and editing. |
| B3 | **Funding** | The source and grant number, or confirm "no specific grant" (sentence already drafted). Include API credits or compute paid by an employer or grant, if any. |
| B4 | **AI declaration** | Approve the text now in `main.tex` (before the references; the same as `paper/AI_DECLARATION_DRAFT.md`), or send edits. |
| B5 | **Data availability: Zenodo deposit is MANDATORY** | KBS research data policy "Option C": data must be deposited in a repository and cited/linked in the article (a commit hash alone does not satisfy it). The manuscript's data statement now has a Zenodo DOI slot. Deposit steps and the decisions needed are in section E. |

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
| D4 | KBS abstract and keyword limits | DONE 2026-09-29 (user, from the official guide): abstract "does not exceed 250 words" (ours: 233); keywords "1 to 7" (ours: 6). Compliant. |
| D5 | **Declarations-tool document** | At submission: generate the competing-interest declaration at declarations.elsevier.com (a Word document) and upload it as a separate file. **Easy to miss; required.** |

## E. Zenodo deposit (mandatory; prepared, nothing created yet)

Prepared: `scripts/zenodo_deposit.py` (create -> upload -> publish, with
publish gated behind `--i-confirm`) and `paper/zenodo_metadata.json`.
The archive is `git archive` of the final commit, about 97 MB. It
excludes the raw BioRED corpus files and the CaRB sentence sample, which
are third-party data. DocRED raw files are not in the repository.

Recommended order, which puts the DOI in the manuscript before the final
commit:
1. `create`: a draft deposition with a **pre-reserved DOI**. The draft is
   not public and can be deleted.
2. I put the DOI into `main.tex` (data statement and data citation),
   commit, and push. **That is the final commit.**
3. `upload --commit <final hash>`.
4. You check the draft on zenodo.org, then `publish --i-confirm`.
   **Publishing is irreversible.** The DOI resolves only after publishing.

| # | Decision needed from you | Notes |
|---|---|---|
| E1 | **Zenodo token** | Create a personal access token at zenodo.org -> Applications (scopes: deposit:write, deposit:actions) and add `ZENODO_TOKEN=...` to `.env` (git-ignored). Do not paste it in chat. Optional: also a sandbox.zenodo.org token for a dry run first. |
| E2 | **Licence** | One licence per record. Suggested: MIT (code) or CC-BY-4.0 (outputs and analyses). The repository currently has **no LICENSE file**; I will add the matching one. |
| E3 | **Creators' affiliations and ORCIDs** | The same as A2/A4/A5. |
| E4 | **Version label** | e.g. "1.0.0-submission". |
| E5 | **Third-party data exclusion** | Confirm excluding the raw BioRED files and the CaRB sample (default). The derived extraction outputs, which include DocRED/BioRED entity strings, stay in the deposit. |
