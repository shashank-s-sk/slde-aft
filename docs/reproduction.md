# Reproduction Notes

Per DEC-030 (professor_feedback.md point 12). This file records the
pinned model identifiers, run dates, decoding settings, seeds, and
hardware actually used to produce the numbers in `paper/main.tex` and
`Results Summary.md`, plus a data/licensing note. It does not repeat
the raw numbers themselves -- see `Evidence log.md` (EVID-xxx) and
`Decision log.md` (DEC-xxx) for those, and `scripts/reproduce_all.py`
to regenerate and cross-check them from the committed raw outputs
under `outputs/`.

## Pinned model identifiers

All API-based extraction and baseline scoring used [OpenRouter](https://openrouter.ai/)
with an explicit, pinned model string (never `openrouter/auto`, which
the original pre-`q1-rework` draft used and which is not a reproducible
measurement of any specific model -- see `paper/main.tex` Section 6/7
and Results Summary.md's "Structural manuscript issues" note).

| Role | Model identifier | Provider |
|---|---|---|
| Core pipeline extractor (product domain, DocRED, BioRED) | `meta-llama/llama-3.1-8b-instruct` | OpenRouter |
| CaRB external baseline | `deepseek/deepseek-v3.2` | OpenRouter |
| CaRB external baseline (pilot scale only) | `openai/gpt-4o` | OpenRouter |
| CaRB external baseline (pilot scale only) | `anthropic/claude-sonnet-5` | OpenRouter |
| CaRB external baseline (pilot scale only) | `google/gemini-2.5-pro` | OpenRouter |
| Fine-tuning base model | `mistralai/Mistral-7B-Instruct-v0.3` (Hugging Face) | Local (rented GPU) |

`mistralai/Mistral-7B-Instruct-v0.3` was chosen over
`meta-llama/Llama-3.1-8B-Instruct` specifically to avoid a Hugging Face
gated-repository approval wait that would have burned paid GPU-pod
time unpredictably (EVID-026).

## Decoding settings

- **Temperature: 0** for every extraction and baseline call in this
  project (`src/extractors/openrouter_llm.py` and
  `src/extractors/openrouter_openie.py` both default `temperature=0.0`;
  verified directly, not assumed).
- **max_tokens: 512** by default (`src/extractors/openrouter_llm.py`,
  `src/extractors/openrouter_openie.py`), raised to **3072** for
  Gemini 2.5 Pro specifically on the CaRB baseline runs (EVID-032 --
  Gemini's reasoning-heavy responses consumed the default budget
  before reaching the final answer; even at 3072, 5/30 pilot-sentence
  calls still returned no valid output).
- Fine-tuning inference (`scripts/dec006_evaluate_adapter.py`) uses
  greedy decoding with `min_new_tokens=100` (EVID-026 -- a very short
  fine-tune was observed to emit an immediate end-of-sequence token
  under unconstrained greedy decoding without this floor).
- Confidence values entering the Noisy-OR aggregation are **self-reported
  by the model**, not derived from token probabilities or any
  calibration procedure: the core pipeline prompt
  (`src/extractors/openrouter_llm.py`, line 35) instructs a confidence
  in [0.80, 0.96]; the fine-tuning data-generation/evaluation prompt
  (`src/prompts.py`, line 28) instructs [0.85, 0.99] -- a deliberately
  different range, not a typo (Section 6 of `paper/main.tex`).

## Seeds

| Purpose | Seed(s) |
|---|---|
| Synthetic product generation (`src/datasets/product_generator.py`) | 42 |
| Train/val/test product split (`src/leakage_split.py`) | 7 (distinct from the generation seed by design) |
| Confirmatory multi-seed runs (fine-tuning, module ablation) | 42-46 (DEC-005/006 convention) |
| DEC-029 extended ablation | 47-71 (25 new seeds added to the existing 42-46; see `Decision log.md` DEC-029 for the final achieved count) |
| DocRED pilot document sampling (DEC-020) | 42 |
| DEC-028 corruption draws (which rows are corrupted, which wrong value each receives) | 1-5 per non-zero corruption rate (0% needs no seed) |
| DEC-026 validation/test subject-string split | 42 |
| Bootstrap resampling (DEC-026/027/028) | project-specific fixed seeds recorded in each script's own `BOOT_SEED` constant, not reused across DECs |

## Hardware

- **API-based extraction and scoring**: no special hardware -- any
  machine with network access to OpenRouter.
- **LoRA/QLoRA fine-tuning and local adapter inference**: rented
  RunPod GPU pods. RTX 4090 (24GB) primary
  (EVID-026, EVID-037); RTX 3090 substituted for some runs after RTX
  4090 pods failed GPU sanity checks (EVID-028's DEC-006 seed 43/44
  runs) -- runtime is not compared across GPU types anywhere in this
  project's reported numbers.

## Approximate run dates (from commit history, not invented)

| Date | Milestone |
|---|---|
| 2026-09-08 | DEC-002 Llama-3.1-8B CaRB-10 pilot baseline |
| 2026-09-12 | DEC-004 through DEC-009 (ablation pilot, statistical validation infrastructure, error analysis, scalability sweep, BioRED pilot, DEC-006 zero-cost build) |
| 2026-09-14 | DEC-006 first real GPU fine-tuning run (Mistral-7B QLoRA) |
| 2026-09-16 | DEC-018 provenance filter; DEC-019 closed-loop integration test |
| 2026-09-17 | DEC-002 extension (GPT-4o/Claude/Gemini baselines); REBEL attempt |
| 2026-09-18 | CaRB full-scale scoring scripts; DEC-003 calibration/complexity; DEC-022 epoch/LoRA grid Stages 1-2 |
| 2026-09-19 | DEC-022 complete (epochs=5 significant vs. base); DEC-023 N=50 ablation complete |
| 2026-09-20 | AUDIT.md validity-threat audit |
| 2026-09-22 to 2026-09-23 | DEC-026 (aggregation-rule replay), manuscript Sections 2-8 drafted, DEC-027 through DEC-030 (Tier 1 validity experiments) |

Exact per-EVID dates are in each EVID entry's own text in
`Evidence log.md` and in `git log`; this table is a coarse milestone
summary, not a substitute for either.

## Data and licensing

- **Synthetic product domain** (`src/datasets/product_generator.py`):
  this project's own code, deterministic, seeded. No external license
  constraint -- it generates its own data, it does not redistribute
  any third-party dataset.
- **CaRB**: MIT License (Data Analytics and Intelligence Research
  (DAIR) Group, IIT Delhi, 2021) -- verified directly against
  `data/CaRB/LICENSE` in this repository, not assumed.
- **DocRED**: obtained via the `thunlp/docred` Hugging Face mirror,
  MIT licensed (Decision log.md DEC-020) -- used in place of DocRED's
  own Google-Drive-only distribution specifically because the mirror
  is directly scriptable.
- **BioRED**: obtained from NCBI's public FTP distribution
  (`https://ftp.ncbi.nlm.nih.gov/pub/lu/BioRED/BIORED.zip`, EVID-024);
  NCBI-published biomedical corpus, public domain (U.S. government
  work) per NCBI's standard data-release terms.
- **TACRED**: scoped but not obtained (a paid LDC license, $25
  non-member fee) -- explicitly declined by user decision given CaRB
  and DocRED already cover open-domain and closed-schema extraction at
  no additional cost (Decision log.md DEC-021). No TACRED data exists
  anywhere in this repository.

## What is and is not committed under `outputs/`

`outputs/` is gitignored by default (`outputs/*` in `.gitignore`).
As of DEC-030, targeted exceptions commit the raw outputs behind every
number currently cited in `paper/main.tex`:

`dec001_002_carb30`, `dec001_official_carb`, `dec001_part6_carb_full`,
`dec001_part6_official_carb`, `dec002_baseline`, `dec002_rebel_baseline`,
`dec002_sota_baselines`, `dec003_product_probkb_v2`,
`dec003_real_calibration`, `dec003_complexity_benchmark`,
`dec005_multiseed`, `dec006_adapters` (config/tokenizer files only --
see below), `dec006_eval`, `dec006_scaleup_probkb`,
`dec006_synthetic_data`, `dec008_scalability`, `dec009_biored_pilot`,
`dec018_provenance_filter`, `dec019_closedloop`,
`dec020_docred_extract_and_pkb`, `dec020_docred_pilot`,
`dec023_ablation_n50`, `dec026_aggregation_rules`.

**Adapter weight files** (`*.safetensors`, `*.bin`) are excluded from
new commits regardless of directory, matching the project's standing
`.gitignore` rule. **Historical note, found during DEC-030, not fixed
retroactively**: five `adapter_model.safetensors` files (14MB each,
under this project's own >50MB exclusion threshold) were already
committed to `outputs/dec006_adapters/` and one to
`outputs/dec025_adapters/` before the `*.safetensors` gitignore rule
existed (commit `4945f15`, 2026-09-14, and later). They were left in
place rather than rewritten out of history (README ground rule 2:
never delete or overwrite existing outputs); no new adapter weight
files have been added since the rule was introduced. If repository
size becomes a concern, removing these five specific historical files
via a dedicated, separately-approved history-rewrite is future work,
not done as part of DEC-030.

`outputs/dec025_adapters/`, `outputs/dec025_closedloop/`, and several
early exploratory/smoke-test directories (`carb_10_dev`,
`carb_smoke_test_3`, `dec003_pkb_validation`,
`dec003_probkb_local_test`, `dec003_product_audit`,
`dec003_product_smoke_3`, `dec003_scaled`, `dec004_ablation_pilot`,
`dec007_error_analysis`) are **not** covered by a `.gitignore`
exception, because no EVID number reachable from `paper/main.tex`
currently cites them. `outputs/dec028_provenance_corruption/`
(DEC-028/EVID-042) is also not yet exception-listed, for the same
reason -- EVID-042 is documented in `Evidence log.md` and
`Results Summary.md` but is not yet cited from `paper/main.tex` itself
(Section 8's Discussion does not yet reference it). If DEC-028's
result is pulled into the manuscript, add a targeted exception for
that directory at the same time, following the same pattern as the
other 22 above.
