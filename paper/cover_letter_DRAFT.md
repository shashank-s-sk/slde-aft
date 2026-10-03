# Cover letter: DRAFT (Stage 4, 2026-09-29)

Replaces `cover_letter_TEMPLATE.md` (written for LRE). Every
`[NEEDED: ...]` is something only the authors can supply; see
`paper/STAGE4_INPUTS.md`. Venue: Knowledge-Based Systems (decided
2026-09-29).

---

[NEEDED: date]

To the Editor-in-Chief,
*Knowledge-Based Systems*

**Submission:** "How Much Corroboration Do LLM Extractors Realise?
Source-Counted Noisy-OR Aggregation Across Sentences and Documents"
**Article type:** Full-length article

Dear Editor,

We submit the manuscript named above for consideration as a full-length
article in *Knowledge-Based Systems*.

**What the paper does.** Knowledge-base systems that populate themselves
with facts extracted by language models often admit a fact only when
more than one source supports it, scoring it with a Noisy-OR over
repeated observations. The paper asks whether the conditions such a rule
needs actually hold, for the rule published with the DySECT system,
which it attributes throughout and does not claim. It reports four
findings:

1. **Availability.** How much corroboration two widely used resources
   supply: 50.2% of DocRED's gold facts have two or more evidence
   sentences, but only 3.4% name both entities in two; across 4,051
   DocRED documents, 4.8% of facts recur in two or more documents.
2. **Realisation.** Extractors realise almost none of it: at most 3.1%
   of facts within documents (on BioRED; 0.98% on DocRED), and 0.8-4.1% of
   multi-document facts on a
   pre-registered 2,010-document subset. Aggregation lowered F1 in every
   configuration: in the evaluated settings, extractor-realised
   corroboration, rather than the aggregation rule itself, was the
   dominant constraint.
3. **Independence.** Counting distinct sources instead of repeated
   observations raised the precision of admitted facts. In a
   pre-registered rerun this held with a stronger extractor, robustly on
   one dataset and borderline on the other, and with token-probability
   confidence.
4. **The released system.** DySECT's released code counts repeats by
   design, and this decides whether most of the concept generalisations
   its extractor can use pass its threshold. A check found no material
   effect on its recall.

**Fit with Knowledge-Based Systems.** The paper concerns how
knowledge bases built from automatically extracted facts score and admit
those facts: when evidence aggregation adds reliable knowledge and when
it only discards recall. It combines a formal analysis of the scoring
rule with pre-registered empirical tests and an audit of a published
system's released code.

**Length.** The body of the manuscript, from the Introduction to the end
of the Conclusion, is 24 double line spaced pages including tables and
figures (the PDF is 35 pages in total with the title page, declarations
and references). The guide for authors asks for papers of "preferably no
more than 20 double line spaced manuscript pages, including tables and
figures"; the body is four pages above that stated preference. The
closed-loop evaluation, rule definitions and per-method tables are
already in the supplementary material, and we can shorten further if the
editor prefers.

**Scope of the evidence, stated plainly.**
- The public-corpus and cross-document analyses are single extraction
  runs at temperature 0, with bootstrap confidence intervals. The only
  multi-seed experiment (thirty seeds) is the closed-loop ablation in
  the supplementary material.
- DeepSeek-V3.2 is the external extractor for every main-text result.
  GPT-4o, Claude Sonnet 5 and Gemini 2.5 Pro appear only in a
  30-sentence CaRB comparison.
- The rule comparison replays real LLM extractions of *synthetic*
  products; its pre-registration was committed together with its first
  results, which the paper states.
- The closed-loop evaluation of the implementation (ablation,
  leakage-free fine-tuning, calibration) found no benefit. It is
  reported in full in the supplementary material, not omitted.

**Pre-registration and reproducibility.** Each pre-registered analysis
is a timestamped commit in the public repository,
https://github.com/shashank-s-sk/slde-aft; the commit hashes are listed
in the supplementary material. Code, prompts, extraction outputs and
analysis scripts are in the same repository [NEEDED: archived release
DOI (e.g. Zenodo) or the commit hash of the submitted version].

**Use of AI tools.** Declared in the manuscript, in the section before
the references.

**Statements.**
- The manuscript has not been published and is not under consideration
  elsewhere. [NEEDED: confirm]
- Preprint: [NEEDED: "none", or server and identifier]
- All authors have approved the submission. [NEEDED: confirm]
- Competing interests and funding: as declared in the manuscript.

[NEEDED (optional): suggested reviewers with affiliations and emails;
reviewers to exclude, with reasons.]

Sincerely,

Shashank Kumar Sadashiva (corresponding author)
[NEEDED: affiliation, postal address, institutional email, ORCID]
On behalf of both authors (Shashank Kumar Sadashiva, Ahmed Ebada)
