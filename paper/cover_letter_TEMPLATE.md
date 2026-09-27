# Cover letter — TEMPLATE

Every `[PLACEHOLDER: ...]` must be filled in by the authors. Nothing in
a placeholder has been decided, and no value below has been invented.
LRE requires a cover letter that gives, for **each** author, at least
one of: a verified ORCID profile, a university homepage, or a CV link.

---

[PLACEHOLDER: date]

To the Editors-in-Chief,
*Language Resources and Evaluation*

**Submission: "Corroboration-Gated Confidence Aggregation in Closed-Loop Information Extraction"**
**Article type:** Full-length paper

Dear Editors,

We submit the manuscript named above for consideration as a full-length
paper in *Language Resources and Evaluation*.

**What the paper does.** Closed-loop information extraction pools facts
extracted by a language model in a knowledge base that scores each fact
by its supporting evidence, and feeds the knowledge base back into the
extractor. The paper analyses the aggregation rule published for this
purpose by the DySECT system, which it attributes throughout and does
not claim, and evaluates an independent implementation of the design. It:
- proves the rule's formal properties, including a ceiling that makes
  contested single-valued slots permanently inadmissible;
- tests a distinct-source correction and states its scope limit;
- reports a controlled, partly pre-registered evaluation, most of whose
  results are negative or null.

**Why LRE.** The paper's central empirical findings concern what two
widely used resources, DocRED and BioRED, support for a class of
extraction methods that aggregate confidence across sources. It measures
how many gold facts their annotations support from two or more sentences
(50.2% of DocRED's by evidence sentences but 3.4% by named entities;
35.1% of BioRED's by co-mention), and shows that extractors realise at
most 3.1%, so aggregation lowered F1 in every configuration tested. It
also reports the DocRED extractions under DocRED's official evaluation
metrics, with the caveats of that mapping, alongside the formal analysis
of the aggregation rule.

**Reproducibility.** Code, prompts, configurations, extraction outputs,
and a reproduction script are in
https://github.com/shashank-s-sk/slde-aft [PLACEHOLDER: commit hash or
archived DOI of the submitted version]. The Electronic Supplementary
Material (a separate PDF) gives extended setup, full tables, and the
protocol-check design.

**Statements.**
- This manuscript has not been published and is not under consideration
  elsewhere. [PLACEHOLDER: authors to confirm.]
- Preprint: [PLACEHOLDER: "none", or the preprint server and identifier.]
- All authors have approved the submission. [PLACEHOLDER: authors to
  confirm.]
- Competing interests: [PLACEHOLDER: as in the manuscript's Statements
  and Declarations.]
- Funding: [PLACEHOLDER: as in the manuscript's Statements and
  Declarations.]

**Authors** (LRE requires at least one of ORCID, homepage, or CV link
per author):

| Author | Affiliation | Email | ORCID | Homepage or CV |
|---|---|---|---|---|
| Shashank Kumar Sadashiva (corresponding) | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| Ahmed Ebada | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |

[PLACEHOLDER: optional suggested reviewers, with affiliations and
emails, and any reviewers to exclude, with reasons.]

Sincerely,

[PLACEHOLDER: corresponding author's name, affiliation, and contact
details]
