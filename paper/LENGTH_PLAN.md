# Length-reduction plan (proposed 2026-09-25; NOT applied, awaiting approval)

Baseline under the sn-jnl template: **50 pages**, of which pages 1-41 are
the main text (~14,660 prose words + ~1,150 words in tables/figures),
pages 42-46 the appendix, and the rest references. Word counts are from
`paper/main.tex` (prose only; comments, commands and maths excluded).

**Target:** a main text of about 24-27 pages (~8,500 prose words), with
moved material going to a separate Electronic Supplementary Material (ESM)
file, which Springer journals accept and which does not count toward the
article's length.

**Ground rules:** no limitation or caveat is cut. Where a claim moves to
the ESM, any caveat attached to it moves with it, and every caveat that
qualifies a claim still in the main text stays in the main text. The
Limitations section (823 words) and the Introduction (754) are not
touched.

| # | Section | Now (words) | Proposed action | Words saved (main text) |
|---|---|---:|---|---:|
| A1 | Related Work, six paradigm subsections + synthesis | 1,158 | Merge into one "Background" subsection (~350), keeping every citation | ~800 |
| A2 | Related Work, DySECT | 1,055 | Keep attribution, formula identity, shared/different capabilities and comparability; tighten to ~500 | ~550 |
| B | Cross-Paradigm Research Gap | 350 | Fold into the end of Related Work (~120); the Introduction already states the gap | ~230 |
| C | Evaluated Framework | 947 | Keep module facts and the gold-label caveat; remove verification narration ("verified directly this session", grep details) | ~350 |
| D1 | Formal Analysis, Computational Complexity | 117 | Move to ESM; the unindexed-scan limitation stays in Limitations | ~115 |
| D2 | Formal Analysis 5.4 + Results "DEC-026" (duplicated) | 763 prose + 447 table words, 5 tables | Report DEC-026 once, in Section 5.4; keep the tau=0.88 bootstrap table in the main text; move the other 4 tables to the ESM | ~250 prose + ~350 table words |
| D3 | Formal Analysis, Summary | 135 | Cut (the Conclusion covers it) | ~135 |
| E1 | Setup, Datasets | 586 | Move CaRB exclusion mechanics and pilot histories to the ESM (the pilots' oracle / one-source caveats stay, one sentence each) | ~240 |
| E2 | Setup, Models and Hardware | 255 | Move GPU/pod details to the ESM | ~100 |
| E3 | Setup, Hyperparameters and Prompts | 387 | Move prompt-template detail to the ESM; keep the two-confidence-range caveat (one sentence) | ~190 |
| E4 | Setup, Metrics | 502 | Keep definitions; move the recall-denominator exposition and CaRB scorer detail to the ESM | ~250 |
| E5 | Setup, Statistical Protocol | 511 | Keep the protocol and null convention; move the Wilcoxon-floor explanation and the tuning-leakage history to the ESM | ~210 |
| E6 | Setup, Note on DEC-026 | 63 | Fold into 5.4 | ~50 |
| F1 | Results, Fine-tuning | 997 + 3 floats | Move the superseded 8-product exploration (text, 5-seed table, fig_finetuning) to the ESM; keep DEC-027 plus one sentence naming the exploration with its tuned-on-test caveat | ~450 + ~100 table words + 1 figure |
| F2 | Results, Ablation | 518 | Move the 5-seed history and the SD-correction note (with its table) to the ESM; keep the 30-seed result, MDE and retry caveat | ~220 |
| F3 | Results, DocRED + BioRED | 481 | Move evidence-only / whole-abstract continuity arms and secondary evaluators to the ESM (numbers stay in EVID-046/047) | ~130 |
| F4 | Results, Scalability | 114 + 1 figure | Move to the ESM; keep one sentence; the memory/GPU limitation stays in Limitations | ~90 + 1 figure |
| F5 | Results, Provenance | 274 | Compress the two-gold-set explanation, keeping both precision figures | ~70 |
| G1 | Discussion, DocRED/BioRED/DySECT | 494 | Remove restated results; keep the corroboration-scarcity argument and the two DySECT differences | ~190 |
| G2 | Discussion, Rival ceiling generalises | 123 | Merge into Formal Analysis (~60) | ~60 |
| G3 | Discussion, R3 | 399 | Tighten; keep the scope statement | ~150 |
| G4 | Discussion, Ablations | 260 | Tighten; keep the MDE and PKB-direction statements | ~110 |
| G5 | Discussion, Fine-tuning | 363 | Tighten; keep the recall-loss mechanism and its "not isolated" caveat | ~140 |
| H | Whole paper, process language | — | Remove session/process narration and in-prose DEC/EVID identifiers (keep them in comments) | ~500 |
| I | Conclusion | 623 | Tighten the open-questions list; keep all six items | ~170 |
| | **Total** | | | **~5,800 prose words + ~450 table words + 2 figures** |

Estimated result: ~8,850 prose words and ~24-26 main-text pages, plus
~3-4 pages of references. The ESM would hold ~12 pages: the moved tables,
figures and exposition, plus the current appendix.

Items most likely to draw reviewer objection if moved: F1 (the
superseded fine-tuning exploration) and D2 (the full DEC-026 tables).
Both stay one click away in the ESM, with pointers from the main text.
