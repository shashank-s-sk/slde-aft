# Q1 readiness assessment (2026-09-25)

Manuscript: "Corroboration-Gated Confidence Aggregation in Closed-Loop
Information Extraction" (`paper/main.tex`, 32 pages under sn-jnl;
`paper/supplementary.tex`, 9 pages). This document is deliberately
critical: each judgement cites its evidence, and each claim is paired
with the strongest objection a reviewer could still make.

## Bottom line

The paper is now honest and reproducible, but its contribution is modest:
- an elementary formal analysis of someone else's aggregation rule;
- a small, scope-limited correction to that rule;
- a largely negative evaluation of that rule's design, run with a weak
  extractor and a synthetic primary domain.

That is publishable as a careful evaluation study. It is not competitive
as a methods paper in a top-tier venue. The biggest avoidable
weaknesses:
- the central real-text finding rests on one extraction protocol
  (sentence-level, 8B model, non-standard DocRED scoring);
- ~~there is no error-analysis section~~ (done 2026-09-25: Section 6.8,
  ESM S9).

The first is fixable at low cost before submission (see "What remains
weak").

---

## 1. Professor feedback: point-by-point status

| # | Point | Status | Evidence | What is still missing |
|---|---|---|---|---|
| 1 | Public benchmarks | **Partly** | CaRB, 548 sentences, official scorer (EVID-035); DocRED, 845 dev documents (EVID-046); BioRED, 500 abstracts (EVID-047) | TACRED declined (LDC fee, DEC-021); REBEL dataset and Universal-IE datasets not attempted. DocRED uses sentence-level extraction and a custom entity-aware scorer, not the official document-level protocol (Ign F1). The DocRED numbers are therefore **not comparable to the DocRED literature**. |
| 2 | State-of-the-art comparisons | **Partly** | CaRB: DeepSeek-V3.2 on all 548 sentences; GPT-4o, Claude Sonnet 5, Gemini 2.5 Pro on a 30-sentence pilot only (EVID-032/035). BioRED: DeepSeek-V3.2 baseline (EVID-047). REBEL attempted and found incompatible (EVID-033). | GenIE, InstructUIE, DyGIE++ not run. Three of the four frontier LLMs have only 30-sentence results. No external system on DocRED. **No comparison with DySECT itself**, the only closed-loop peer. All comparisons are between extractors, not between frameworks. |
| 3 | Mathematical contribution | **Mostly** | Seven propositions and one corollary with proofs (Section 4); complexity (ESM S3, EVID-036); calibration, ECE 0.333 and Brier 0.297 (EVID-036) | No convergence analysis of the *loop* (only saturation of a single candidate's score). No guarantee about knowledge-base accumulation beyond monotonic growth. The properties are elementary consequences of the Noisy-OR form. |
| 4 | Ablation of every module | **Partly** | Feedback controller and PKB at 30 seeds (EVID-045); structured-only and unstructured-only at 5 seeds, with no held-out evaluation (EVID-020/039) | Synthetic data generator, LoRA fine-tuning and provenance module were **not ablated inside the loop**. Fine-tuning and provenance were evaluated standalone (EVID-044, EVID-029/042), which is not the requested design. |
| 5 | Statistical validation | **Addressed for the main comparisons** | Multi-seed means with sample SD, bootstrap CIs, t-test and Wilcoxon, minimum detectable effect, pre-registration (DEC-027/029/031/032) | Still single-run: closed-loop test (1 seed, EVID-030), calibration (one snapshot), scalability (one run per size). The ablation's MDE of 0.070–0.086 F1 is about 20% of the pipeline's F1 (~0.36), so a practically relevant effect could remain undetected. |
| 6 | Fine-tuning improvement | **Investigated; goal not met** | 7B base (Mistral-7B); epoch and LoRA grids; leakage-free validation/test split; **negative** primary result, −0.021 [−0.042, −0.003] (EVID-044) | Larger synthetic datasets not tried (**90 training examples throughout**); instruction generation not improved beyond fixing its format; no model >7B. The professor asked for "a meaningful improvement"; the paper reports that it did not get one. That is honest, but it concedes the point rather than addressing it. |
| 7 | Error analysis | **Addressed (2026-09-25)** | Section 6.8 (Error Analysis) with a 10-row table of real examples, one per category: correct, not admitted, hallucinated, conflicting (all wrong / correct blocked), near-threshold, relation-type ambiguity, missed corroboration, repeat admitted, boundary error. Plus ESM S9 (counts and more examples). The recheck also corrected EVID-022: the LLM extracted only 104 of 245 text-stated facts; the "hallucinated" counts included 210 correct structured facts. | "Ambiguous relations" is covered by BioRED relation-type confusion (811 predictions), not by a dedicated annotation study. |
| 8 | Scalability | **Partly** | Runtime, KB growth and per-document latency for N = 20–200 (ESM S6, EVID-023); complexity benchmark (ESM S3) | Memory not measured reliably; GPU utilisation not recorded; single runs; **no scaling study on larger data** (the 845-document DocRED run was not profiled). |
| 9 | Multiple domains | **Addressed, with a caveat** | BioRED biomedical (500 abstracts, external baseline) and DocRED Wikipedia (845 documents) | On the public corpora only the *aggregation* stage runs. Structured seeding, the provenance filter, the feedback loop and fine-tuning are exercised **only in the synthetic product domain**. |
| 10 | Analytical discussion | **Mostly** | Why fine-tuning raises precision and lowers recall (Section 7.4); when aggregation works or fails, i.e. the corroboration boundary (7.1); failure modes; calibration mechanisms (7.5) | "Why Prob-KB maintains perfect recall" is not answered, and its premise no longer holds: admission recall at τ = 0.88 is 0.39–0.45 (DEC-026). The paper should say this explicitly rather than leave the question unaddressed. |
| 11 | Novelty positioning | **Partly** | "First system" claims removed; architecture, formula, λ and mode names attributed to DySECT; an explicit evaluation gap (Section 2.3) | The differences from RAG, continual learning, AutoML, UIE, knowledge-graph population and self-training now get about one clause each in a 159-word Background. Knowledge-graph population is represented only by surveys. A reviewer may find the positioning thin. |
| 12 | Reproducibility | **Mostly** | Public GitHub repository (API check, HTTP 200); code, prompts, configs, outputs, `scripts/reproduce_all.py` (DEC-030), scripted figures; no secrets in the history (checked) | Data and code availability statements are still TODO. Software versions are unpinned for every fine-tuning run (Limitations). The superseded exploration's adapters were never committed. Hosted models are fixed by identifier only. |
| 13 | Writing | **Partly** | Length 50 → 32 pages; process language removed; three main figures referenced in the text; all five figures vector and scripted | Three references are still missing identifiers (`UNVERIFIED.md`: AutoGluon, SageMaker Autopilot, GraphRAG). No full audit that every citation supports its sentence. **The compiled PDF has not been proofread visually** (no renderer on the build machine). Transitions have not been reviewed by a human reader. |

---

## 2. Claims, evidence, and the strongest remaining objection

| Claim (where) | Evidence | Strongest reviewer objection |
|---|---|---|
| **Rival ceiling**: a contested single-valued slot scores < 1/(m+1) ≤ 0.5 (Prop. 7, Cor. 1) | Proof, Section 4.2 | "This is a one-line consequence of dividing a quantity below 1 by m+1. Calling it a result overstates it; any reader of DySECT's Eq. 2 can see it." |
| Boundedness, order-invariance, monotonicity, saturation, corroboration requirement | Proofs, Section 4.2 | "These are textbook properties of Noisy-OR. They do not justify a 'formal analysis' contribution." |
| Deterministic repeats violate Noisy-OR's independence assumption (Prop. 8) | Stated, not proved; 31 repeated false positives (EVID-029) | "A known modelling caveat, informally argued; the evidence is one snapshot of a synthetic domain." |
| The ceiling blocks contested slots in practice (0 vs 6/40; 0 under 5–20% corruption) | DEC-026/EVID-041; DEC-028/EVID-042 | "The measurement confirms the algebra, which cannot fail. What matters is whether blocking helps or hurts recall, and the paper never measures that." |
| **Distinct-source counting (R3) raises precision** in the product domain (+0.106 / +0.027; F1 +0.019 / +0.006 at τ = 0.88) | EVID-041, subject bootstrap | "The repeats R3 removes are created by the pipeline's own four-iteration re-reading of the same text, so the fix repairs a self-inflicted defect. The F1 gains are tiny, on two snapshots of synthetic data." |
| R3 raises precision out of domain (DocRED +0.19 on 36 admitted, 9 correct; BioRED +0.054, Llama) | EVID-046/047; secondary, not the pre-registered criterion | "Tiny counts. The pre-registered F1 test is null (DocRED) or negative (BioRED Llama), and there is no effect with DeepSeek." |
| **R3 acts only when the extractor repeats within a source** (scope limit) | 154/138/6 duplicates vs effect size (EVID-046/047) | Largely unobjectionable. It is the paper's most defensible empirical statement about R3. |
| Removing feedback controller or PKB: no significant effect (30 seeds) | EVID-045 | "An MDE of ~0.08 on F1 ≈ 0.36 is weak. The test set is 10 synthetic products, and the retry rule was applied unevenly. The null says little." |
| PKB cannot be claimed to help (point estimate favours removal) | EVID-045, EVID-041 | "Fair, but it undercuts the rule the paper spends Section 4 analysing." |
| **Leakage-free fine-tuning is negative** on its primary metric | EVID-044 (pre-registered) | "90 training examples, a 7B model and one synthetic domain: this tests a weak fine-tuning setup, not the idea. The pooled metric is positive." |
| Closed-loop test: no end-to-end benefit | EVID-030 | "One seed, and a Llama control against a Mistral treatment. This supports no claim in either direction." (The paper says so.) |
| **Extractor recall, not the matching key, is the binding constraint on real text** | DocRED G2 = 29/11,344; BioRED rho = 0.022 (pre-registered, confirmed) | "The constraint is manufactured by the protocol: sentence-level extraction with no document context, an 8B extractor, and DocRED F1 = 0.044, far below the document-level literature. With document-level extraction or a stronger model the conclusion might change. The DeepSeek check is split: more corroboration, larger gap." **This is the objection most likely to decide the review.** |
| Matching-key explanation does not account for the DocRED failure | EVID-046 (oracle-only + incomplete) | "Negative and well supported, but narrow; it rebuts the authors' own earlier hypothesis." |
| Provenance filter raises precision 93.5% → 100% | EVID-029, EVID-043 | "Circular: the structured source and the gold labels come from one generator. Random corruption (DEC-028) is a weak substitute for a real independent source." |
| Aggregated scores are poorly calibrated (ECE 0.333) | EVID-036 | "One snapshot, and self-reported input confidences. Expected, and not analysed further." |
| The extractor is the weakest system on CaRB (0.467 vs 0.571) | EVID-035 | Unobjectionable. It supports the reviewer's "weak implementation" objection above. |
| Runtime scales linearly to N = 200 | EVID-023 | "Single runs, small N, memory unmeasured." |

---

## 3. DySECT attribution after the Related Work cut

**Finding: the cut did weaken the attribution, and in one respect made it
inaccurate. Fixed in this commit.**

- **Inaccuracy.** The shortened text described DySECT's "Encouraging" and
  "Prohibitive" modes as "recovering missed facts and suppressing false
  ones". DySECT's Section 4 defines them differently, as re-verified
  against the arXiv HTML (2603.06915v2):
  - Encouraging injects high-confidence sub-concepts as positive
    examples.
  - Prohibitive marks saturated sub-concepts "as already extracted" to
    avoid *redundant* extraction.

  The shortened text attributed this implementation's meaning (a
  false-pattern block) to DySECT. The same wording was in the
  Introduction and the Framework section.
- **Lost disclosure.** The original text stated that this project's own
  design documents adopted DySECT's mode names and its KNN-based
  hierarchy method. The cut removed that, which matters for how
  derivative the design is.
- **Fix applied:**
  - Section 2.2 now gives DySECT's own definitions of both modes.
  - It states that the original design adopted both names and the
    KNN-based clustering.
  - It states that the implemented false-pattern block differs in
    purpose from DySECT's Prohibitive mode.
  - The Introduction and Section 3.3 were corrected to match.
  - The cost was taken from the Background paragraphs, as instructed
    (all citations kept): DySECT subsection 351 words, Background 159.
- **Still intact after the cut:**
  - the formula identity (Eqs. 1–2);
  - the λ = 0.75 default (re-verified against DySECT's text);
  - the closed loop, the confidence layer, prompt feedback and
    KB-derived fine-tuning attributed to DySECT;
  - "this paper claims none of them";
  - properties "stated but not proved" in DySECT;
  - the capabilities DySECT has that the implementation lacks;
  - no head-to-head comparison claimed.
- **Residual risk:** a reviewer may still judge the evaluated
  implementation derivative of DySECT (it adopted DySECT's names, method
  and formula) and ask why DySECT itself was not evaluated. The paper
  handles this by attribution; it cannot remove the perception.

---

## 4. What remains weak (ranked by likely impact on review)

1. **The real-text conclusion rests on one extraction protocol.** Every
   public-corpus result uses sentence-level extraction without document
   context, mostly with an 8B model, scored by a custom evaluator.
   - *Fix, cheap:* add a document-level extraction arm and a stronger
     extractor arm on DocRED and BioRED (the extraction is cached and
     sharded; about $1–3 of API calls at measured rates).
   - Then test whether aggregation's gap to no aggregation shrinks as the
     corroborated-fact share rises, the paper's own proposed experiment.
   - Report DocRED under its official metric, or state the
     non-comparability prominently.
2. ~~No error-analysis section~~ **Done 2026-09-25** (Section 6.8, ESM S9).
3. **The formal contribution is thin.** The ceiling is a direct
   consequence of the formula. *Mitigation:* reframe it as a *design
   consequence* (contested functional slots are permanently
   unresolvable; no deletion path), which is what the paper actually
   shows, and do not oversell the proofs.
4. **Positive results live in the synthetic domain,** and R3's product-
   domain gain removes repeats that the pipeline's own iteration design
   creates. State this plainly in the R3 subsection, not only in the
   scope limit.
5. **The negative loop results use weak components:** 90 training
   examples, an 8B extractor, and gold-label feedback. A reviewer can
   dismiss them as an evaluation of a weak implementation. The
   Limitations section says so. The only real remedy is the stronger
   runs in item 1 and a larger synthetic training set.
6. **No DySECT head-to-head,** and the design adopted DySECT's names,
   method and formula (Section 3 above).
7. **Remaining single-run evidence:** closed-loop, calibration,
   scalability.
8. **Submission blockers** (not scientific, but mandatory):
   - author details and all eight declarations are TODO;
   - three unverified reference identifiers;
   - both journals' reference style and declaration lists are
     unconfirmed;
   - the compiled PDF has not been proofread visually.

---

## 5. Venue recommendation (evidence-based)

What the evidence supports is a **rigorous, partly pre-registered
evaluation study with negative and scope-limited results and an
elementary formal analysis**. It does not support a methods-advance
framing.
- **Not recommended now:** top-tier methods venues. The formal
  contribution is too elementary, and the empirical story is mostly
  negative on a weak implementation. A rejection on novelty grounds is
  the likely outcome.
- **First choice: Language Resources and Evaluation (LRE).** Its scope is
  evaluation methodology. The paper's strengths match that:
  - a pre-registered protocol;
  - three public corpora;
  - a transparent treatment of oracle and continuity settings;
  - a public, scripted harness.

  To make the fit explicit, frame the paper as an evaluation study and
  release the DocRED/BioRED extraction outputs and scoring harness as a
  resource (both already exist in the repository). The 243-word abstract
  already meets its 150–250-word limit.
- **Second choice: Knowledge and Information Systems (KAIS).** It fits
  the knowledge-base aggregation analysis. But its reviewers are more
  likely to expect a system advance and to weigh the negative results
  against the paper. The manuscript (~12,750 words with references) is
  within its 15,000-word limit.
- **Verify before choosing:** that each journal's *current* quartile
  meets your Q1 requirement (not checked here; quartiles differ between
  JCR and SJR and by subject category), plus each journal's reference
  style and declarations (`UNVERIFIED.md`).
- **In either case,** expect major revisions unless items 1 and 2 above
  are done first. Doing them before submission is the highest-value use
  of the remaining effort: roughly two days of work and a few dollars of
  API calls.
