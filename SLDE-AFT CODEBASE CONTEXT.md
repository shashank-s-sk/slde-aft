# SLDE-AFT CODEBASE CONTEXT
## Version: Prototype → Q1 Research Implementation

IMPORTANT:
This document is a complete contextual description of the existing
SLDE-AFT research codebase.

Use this document together with the actual source code/notebook.

The purpose is to help an LLM understand the existing implementation
before modifying, refactoring, extending, or debugging it.

Do NOT assume that the existing prototype is perfect.

Do NOT assume that every existing result is scientifically validated.

Do NOT replace the architecture merely because the implementation is
currently notebook-based.

First understand what exists.

============================================================
# 1. PROJECT IDENTITY
============================================================

Project name:

SLDE-AFT

Meaning:

Self-Learning Dual-Source Knowledge Extraction and Automated
Fine-Tuning.

Research area:

- Information Extraction
- Open/Closed Information Extraction
- Large Language Models
- Knowledge Representation
- Probabilistic Knowledge Bases
- Retrieval-Augmented Generation
- Feedback-based self-improvement
- Synthetic supervision
- Parameter-efficient fine-tuning
- LoRA
- Knowledge accumulation

Primary research objective:

Build a closed-loop information extraction framework that combines
structured and unstructured information sources, accumulates extracted
knowledge in a persistent knowledge base, uses accumulated knowledge
to guide later extraction, generates synthetic supervision from
high-confidence knowledge, and automatically adapts the extraction
model through LoRA fine-tuning.

The system is intended to become a rigorous Q1-level research
implementation rather than remain only a proof-of-concept prototype.

============================================================
# 2. HIGH-LEVEL SYSTEM IDEA
============================================================

The system follows this general loop:

Structured Input
       |
       v
Structured Extraction
       |
       v
Seed Knowledge
       |
       +-----------------------------+
       |                             |
       v                             |
Unstructured Documents              |
       |                             |
       v                             |
LLM Extraction                      |
       |                             |
       v                             |
Candidate Triples                    |
       |                             |
       v                             |
Knowledge Base <--------------------+
       |
       +--> Feedback Controller
       |
       +--> High-confidence triples
       |
       +--> Synthetic Training Data
       |
       +--> LoRA Fine-Tuning
       |
       v
Updated Extractor
       |
       v
Next Extraction Iteration

The core research idea is that extraction, accumulated knowledge,
feedback, synthetic supervision and model adaptation form a
closed-loop system.

============================================================
# 3. CORE DATA REPRESENTATION
============================================================

The fundamental knowledge representation is:

(subject, predicate, object)

The system additionally tracks:

- confidence
- source_id
- source_type
- provenance
- extractor_version

The normalized triple identity is:

(subject, predicate, object)

Two observations referring to the same normalized triple should be
treated as observations of the same underlying fact.

Do not confuse:

TRIPLE IDENTITY

with

TRIPLE CONFIDENCE

with

TRIPLE PROVENANCE.

These are separate concepts.

============================================================
# 4. DOCUMENT REPRESENTATION
============================================================

Documents are represented using a DocumentUnit-like structure.

Important fields include:

source_id
source_type
content
metadata

Typical source types include:

structured
unstructured

Structured sources may represent:

CSV
JSON
tabular records

Unstructured sources may represent:

plain text
product descriptions
documents
other natural-language content

The system should preserve source identity throughout the pipeline.

============================================================
# 5. TRIPLE REPRESENTATION
============================================================

The RawTriple-like representation contains:

subject
predicate
object
confidence
source_id
provenance
source_type
extractor_version

The triple key is based on:

(subject, predicate, object)

Confidence is metadata attached to an observation or aggregated
knowledge item.

Provenance identifies where the extracted information originated.

============================================================
# 6. PREDICATE SCHEMA
============================================================

The prototype currently uses a fixed predicate vocabulary.

Current predicates include:

manufactured_by
belongs_to_category
has_price_usd
has_screen_size_inch
has_ram_gb
has_storage_gb
has_battery_life_hours
has_weight_kg
has_color
made_of_material
target_market_region
supports_fast_charging
has_noise_cancellation

This is represented conceptually as:

ALLOWED_PREDICATES

The fixed predicate schema is important because the current prototype
is schema-constrained.

Do NOT silently convert the system into completely schema-free OpenIE.

If future benchmark experiments require another schema, use an
adapter or experiment-specific configuration.

Do not destroy the original schema-constrained research setting.

============================================================
# 7. STRUCTURED EXTRACTION
============================================================

The structured extractor converts structured records into the common
triple representation.

Example conceptual transformation:

Structured record:

product = X
manufacturer = Y

becomes:

(X, manufactured_by, Y)

The structured extractor assigns confidence according to the current
prototype's deterministic structured-source policy.

Structured triples are used to establish initial knowledge.

The structured path therefore acts as a knowledge seed for subsequent
unstructured extraction.

============================================================
# 8. UNSTRUCTURED LLM EXTRACTION
============================================================

The unstructured extractor uses an LLM.

The prototype accesses LLMs through the OpenRouter API.

The LLM is instructed to produce structured extraction output.

Expected conceptual output:

[
    {
        "subject": "...",
        "predicate": "...",
        "object": "...",
        "confidence": ...
    }
]

The predicate should belong to ALLOWED_PREDICATES in the original
schema-constrained experiment.

The implementation includes JSON parsing and normalization.

The API key must NEVER be hard-coded.

Use:

OPENROUTER_API_KEY

from the environment.

============================================================
# 9. OPENROUTER ROLE
============================================================

OpenRouter is the API gateway/provider used by the prototype to call
LLM models.

Do not confuse:

OpenRouter
with
the underlying LLM model.

The experimental record must identify:

provider
model
model version if available
temperature
prompt
number of API calls
experiment ID

============================================================
# 10. KNOWLEDGE BASE
============================================================

The prototype contains a knowledge-store component.

The original deterministic implementation uses monotonic accumulation
and confidence merging.

A key design principle is:

Once knowledge is accepted into the persistent store, it should not
simply disappear because a later extraction iteration fails to
produce it.

The knowledge store therefore provides persistence across iterations.

============================================================
# 11. DETERMINISTIC KB VARIANT
============================================================

The original/standard SLDE-AFT configuration uses a confidence
merge strategy based on monotonic max-merge.

Conceptually:

C_new = max(C_existing, C_observation)

This means repeated observations cannot reduce the stored confidence.

This configuration should remain available as a baseline/controlled
variant.

Do NOT confuse it with the Probabilistic KB.

============================================================
# 12. PROBABILISTIC KNOWLEDGE BASE
============================================================

The Probabilistic Knowledge Base is a major research component.

The PKB replaces simple deterministic confidence merging with a
probabilistic evidence aggregation mechanism.

Its conceptual responsibilities are:

1. receive observations
2. preserve observations
3. aggregate confidence
4. identify conflicting alternatives
5. apply conflict adjustment
6. preserve provenance
7. maintain accumulated knowledge across iterations

The finalized mathematical specification is stored separately in:

MATH_SPECIFICATION.md

That document has authority over the mathematical formulation.

Never invent a new formula merely because another formula looks
simpler.

============================================================
# 13. NOISY-OR AGGREGATION
============================================================

The probabilistic implementation uses Conservative Noisy-Or
aggregation.

The purpose is to combine multiple confidence observations for the
same triple.

The prototype uses a shrinkage parameter.

Current prototype value:

lambda = 0.75

The exact finalized equation is defined in:

MATH_SPECIFICATION.md

Do not redefine the mathematics in this document.

This document only explains the software architecture.

============================================================
# 14. CONFLICT / MUTUAL EXCLUSIVITY
============================================================

The Probabilistic KB also contains a conflict mechanism.

The purpose is to reduce support when mutually exclusive alternatives
exist for a relevant predicate.

Important:

Conflict handling is NOT universally valid for every predicate.

It is applicable when the predicate has a functional /
single-valued interpretation.

For example, a predicate representing one current value may support
mutual exclusivity.

A genuinely multi-valued relation should not automatically receive
the same penalty.

The exact mathematical treatment is defined in:

MATH_SPECIFICATION.md

============================================================
# 15. IMPORTANT MATHEMATICAL DISTINCTION
============================================================

The PKB confidence score is a support/confidence score.

Do NOT automatically describe it as:

"the true probability that the triple is correct."

Calibration must be experimentally demonstrated.

The system also does not guarantee factual truth.

The theoretical claims concern the properties of the aggregation
operator under stated assumptions.

============================================================
# 16. PROVENANCE
============================================================

Every extracted triple should retain evidence of its source.

Provenance may contain:

source document
source ID
source type
text window
extractor
iteration
confidence

Provenance has two purposes:

1. auditability
2. synthetic-data quality control

It is not merely a logging feature.

The provenance information can be incorporated into synthetic
training examples so that generated supervision remains traceable.

============================================================
# 17. FEEDBACK CONTROLLER
============================================================

The Feedback Controller is responsible for generating guidance for
later extraction iterations.

The prototype contains two conceptual feedback modes:

ENCOURAGING MODE

Direct extraction toward underrepresented or missing predicates.

PROHIBITIVE MODE

Suppress concepts or extraction patterns that are already saturated
or producing undesirable outputs.

The feedback controller is therefore intended to change future
extraction behaviour rather than simply report metrics.

The feedback mechanism must remain independently switchable so it can
be evaluated in an ablation.

============================================================
# 18. ITERATIVE LOOP
============================================================

The system operates through multiple extraction iterations.

Conceptually:

Iteration 1
    |
    v
Extract
    |
    v
Update KB
    |
    v
Generate feedback
    |
    v
Generate synthetic data if threshold is met
    |
    v
Fine-tune if conditions are met
    |
    v
Iteration 2
    |
    v
...

The number of iterations in the original prototype is typically four.

Do not assume four iterations is theoretically optimal.

It is an experimental configuration.

============================================================
# 19. SYNTHETIC DATA GENERATION
============================================================

High-confidence KB triples are used to generate synthetic training
examples.

The prototype uses a confidence threshold.

Current prototype threshold:

C > 0.88

Conceptually:

High-confidence triple
        |
        v
Synthetic instruction/response example
        |
        v
Fine-tuning dataset

The exact threshold must eventually be treated as an experimental
hyperparameter selected appropriately using validation/development
data.

Never tune it on the final test set.

============================================================
# 20. SYNTHETIC TRAINING EXAMPLE
============================================================

Synthetic examples are intended to resemble instruction-tuning data.

The example can include:

instruction
input
expected extraction
provenance/evidence
confidence

The purpose is to transform accumulated high-confidence knowledge
into self-generated supervision.

The synthetic-data pipeline must preserve traceability.

============================================================
# 21. LORA FINE-TUNING
============================================================

The prototype contains automated LoRA fine-tuning.

The original prototype uses:

TinyLlama-1.1B

as the fine-tuning model/configuration.

This is an existing prototype choice.

It must NOT automatically be treated as the final Q1 model.

The Q1 revision requires investigating larger models and tuning
hyperparameters.

Possible variables include:

base model
epochs
learning rate
LoRA rank
LoRA alpha
LoRA dropout
synthetic dataset size
instruction-generation method
batch size
gradient accumulation

============================================================
# 22. AUTOMATIC ADAPTATION
============================================================

The system's distinctive closed-loop concept is:

knowledge accumulation
        ↓
high-confidence knowledge
        ↓
synthetic supervision
        ↓
LoRA adaptation
        ↓
updated extractor
        ↓
new extraction
        ↓
new knowledge

The purpose is to reduce dependence on manually curated training
examples during iterative operation.

This mechanism must be evaluated experimentally rather than assumed
to improve performance.

============================================================
# 23. EXISTING BASELINES
============================================================

The prototype defines controlled baseline configurations.

B1 — STATIC LLM

LLM extraction without KB guidance or feedback.

Purpose:

Establish the baseline performance of the LLM extractor alone.

B2 — RAG ONLY

Structured triples seed a knowledge store.

The LLM receives knowledge-base context.

No feedback loop is applied.

Purpose:

Measure the contribution of retrieval/context alone.

B3 — FINE-TUNING WITHOUT FEEDBACK

A fine-tuning configuration without the complete feedback loop.

Purpose:

Measure whether adaptation alone explains performance.

SLDE-AFT FULL

Complete closed-loop system.

SLDE-AFT PROB-KB

Complete loop using the Probabilistic Knowledge Base.

These configurations should remain conceptually separate.

============================================================
# 24. CURRENT EVALUATION
============================================================

The original prototype evaluates:

Precision
Recall
F1

using exact triple key matching.

A predicted triple is correct only when:

subject matches
AND
predicate matches
AND
object matches

after the defined normalization.

Partial matches receive no credit under the original protocol.

The gold triple set is deduplicated by:

(subject, predicate, object)

============================================================
# 25. EXISTING EXPERIMENTAL DATA
============================================================

The original prototype evaluates custom product datasets.

Scales include:

20 products
30 products
40 products
50 products

The original gold construction uses the 13-predicate schema.

These experiments are prototype evidence.

They are NOT sufficient by themselves for the final Q1 validation.

Do not present them as equivalent to evaluation on established public
benchmarks.

============================================================
# 26. EXISTING ITERATIVE BEHAVIOUR
============================================================

The original SLDE-AFT Full prototype demonstrated increasing
precision over iterations in the 40-product experiment.

The reported progression was approximately:

Iteration 1:
Precision 0.4897
Recall 0.4250
F1 0.4551

Iteration 2:
Precision 0.6111
Recall 0.4321
F1 0.5063

Iteration 3:
Precision 0.7545
Recall 0.4500
F1 0.5638

Iteration 4:
Precision 0.9000
Recall 0.4500
F1 0.6000

These are EXISTING PROTOTYPE RESULTS.

They must not be fabricated, manually altered, or treated as
independently replicated Q1 evidence.

============================================================
# 27. PROB-KB BEHAVIOUR
============================================================

The original Prob-KB prototype demonstrated persistent recall
behaviour because accepted triples are not removed from the
accumulated KB.

The reported 40-product prototype behaviour included:

Iteration 1:
Precision 0.5283
Recall 1.0000
F1 0.6914

Iteration 2:
Precision 0.5147
Recall 1.0000
F1 0.6796

Iteration 3:
Precision 0.5091
Recall 1.0000
F1 0.6747

Iteration 4:
Precision 0.4973
Recall 1.0000
F1 0.6643

IMPORTANT:

Recall = 1.0000 in this prototype is closely tied to the evaluation
and monotonic accumulation design.

Do NOT automatically interpret this as proof of superior extraction
ability.

It must be carefully investigated in the new experimental protocol.

============================================================
# 28. IMPORTANT RESEARCH ISSUE — EVALUATION ASYMMETRY
============================================================

The existing paper/prototype contains different evaluation behaviour
between configurations.

In particular, the Prob-KB evaluation can encompass accumulated KB
knowledge, whereas the standard SLDE-AFT Full evaluation may focus on
final-iteration LLM extraction.

This creates an important research concern:

Comparisons must use a clearly defined and fair evaluation protocol.

Before claiming that Prob-KB "outperforms" another configuration,
verify:

- same evaluation target
- same prediction pool
- same gold set
- same normalization
- same data access
- same test conditions

If an apparent advantage comes from evaluation design rather than
better extraction, identify it.

============================================================
# 29. Q1 REVISION DIRECTION
============================================================

The existing prototype is only the starting point.

The Q1 revision requires:

1. Public benchmark evaluation
2. External SOTA comparisons
3. Mathematical validation
4. Ablation study
5. Statistical validation
6. Fine-tuning investigation
7. Error analysis
8. Scalability evaluation
9. Cross-domain validation
10. Stronger discussion
11. Better novelty positioning
12. Reproducibility
13. Writing refinement

The codebase must therefore evolve from:

prototype notebook

into:

modular experimental research framework.

============================================================
# 30. PUBLIC BENCHMARK DIRECTION
============================================================

The first planned benchmark direction is:

OpenIE / OpenIE-style benchmark

Reason:

The system fundamentally operates on:

text → triples

and uses:

(subject, predicate, object)

as the common representation.

However, OpenIE datasets may use relation representations that differ
from the fixed ALLOWED_PREDICATES schema.

Therefore the exact benchmark and predicate-mapping strategy must be
explicitly defined.

Never silently map benchmark predicates.

============================================================
# 31. EXTERNAL BASELINES
============================================================

The planned external comparisons include candidates such as:

REBEL
GenIE
InstructUIE
DyGIE++
GPT-based extraction
Llama-based extraction
Claude
Gemini

The practical initial comparison may use:

REBEL
+
one strong LLM baseline

depending on implementation resources.

The final baseline selection is controlled by the decision log.

============================================================
# 32. COMMON EXTRACTION INTERFACE
============================================================

Every extractor should ultimately produce a common representation:

subject
predicate
object

plus optional:

confidence
provenance
source_type
extractor
model
run_id

This enables the same evaluator to compare different systems.

Do not write separate metric implementations for every baseline.

============================================================
# 33. NORMALIZATION
============================================================

Before evaluation, outputs should pass through a common normalization
layer.

Potential normalization includes:

case normalization
whitespace normalization
schema/predicate normalization where explicitly defined

The normalization layer must be documented.

It must not give SLDE-AFT an unfair advantage.

============================================================
# 34. EXPERIMENTAL COMPONENTS THAT MUST BE SEPARATELY TESTABLE
============================================================

The following must eventually be independently switchable:

Feedback Controller
Probabilistic KB
Synthetic Data Generator
LoRA Fine-Tuning
Provenance
Structured Input
Unstructured Input

This enables controlled ablation experiments.

============================================================
# 35. REQUIRED ABLATIONS
============================================================

A0:
Full SLDE-AFT

A1:
Full SLDE-AFT − Feedback Controller

A2:
Full SLDE-AFT − Probabilistic KB

A3:
Full SLDE-AFT − Synthetic Data Generator

A4:
Full SLDE-AFT − LoRA Fine-Tuning

A5:
Full SLDE-AFT − Provenance

A6:
Full SLDE-AFT − Structured Input

A7:
Full SLDE-AFT − Unstructured Input

All unrelated variables should remain controlled.

============================================================
# 36. MATHEMATICAL VALIDATION
============================================================

The Probabilistic KB must eventually be tested for:

1. Calibration
2. Aggregation behaviour
3. Threshold behaviour
4. Convergence
5. Complexity

Required aggregation comparisons include:

Max
Mean
Standard Noisy-Or
Conservative Noisy-Or
Conservative Noisy-Or + conflict adjustment

The exact mathematical formulation is defined in:

MATH_SPECIFICATION.md

============================================================
# 37. CALIBRATION
============================================================

The system should measure:

confidence
empirical accuracy
calibration gap
ECE

A reliability diagram should be generated.

Do not call confidence values "calibrated probabilities" unless the
experiment demonstrates appropriate calibration.

============================================================
# 38. CONVERGENCE
============================================================

Across iterations record:

iteration
mean support
confidence distribution
KB size
new triples
conflicts
triples crossing threshold
runtime
evaluation metrics

Convergence must be empirically studied.

Increasing iterations alone does not prove mathematical convergence.

============================================================
# 39. STATISTICAL VALIDATION
============================================================

The new framework must support multiple independent runs.

Every run should record:

run_id
random seed
dataset
model
configuration
metrics
runtime

Final reporting should support:

mean
standard deviation
confidence intervals
appropriate statistical significance testing

Do not fabricate significance.

============================================================
# 40. ERROR ANALYSIS
============================================================

The implementation should allow examples to be collected for:

Correct extraction
Failed extraction
Hallucinated triple
Conflicting triple
Ambiguous relation
Provenance filtering

Each error should preserve:

input
gold
prediction
system
iteration
error category
provenance

============================================================
# 41. SCALABILITY
============================================================

The implementation should measure:

dataset size
execution time
inference latency
memory consumption
GPU utilization
KB growth
number of triples
number of API calls
cost where measurable

Do not estimate values.

Measure them.

============================================================
# 42. CROSS-DOMAIN GENERALIZATION
============================================================

The current prototype is product-oriented.

The final framework should support additional domains without changing
the core architecture.

Possible domains include:

biomedical
scientific
manufacturing
automotive
legal

The exact domain/dataset is a research decision.

============================================================
# 43. REPRODUCIBILITY
============================================================

Every experiment should save:

experiment ID
dataset
dataset version
model
model version
prompt
hyperparameters
random seed
configuration
metrics
predictions
runtime
software environment

Prompts must be version-controlled.

Configurations must be version-controlled.

Raw predictions must be preserved.

============================================================
# 44. CODE QUALITY TARGET
============================================================

The existing implementation is a research prototype.

The target implementation should become:

modular
testable
reproducible
configurable
traceable
experiment-driven

Avoid:

duplicate definitions
hidden notebook state
hard-coded paths
hard-coded API keys
hard-coded experimental results
uncontrolled global variables
silent data transformations

============================================================
# 45. NOTEBOOK POLICY
============================================================

The notebook is useful for:

experimentation
visualization
demonstration
debugging

But reusable research logic should gradually move into modules.

Do not blindly create a new notebook and abandon the existing
implementation.

Preserve validated behaviour while restructuring.

============================================================
# 46. WHAT MUST NOT BE LOST DURING REFACTORING
============================================================

Do not accidentally remove:

Dual-source extraction
Structured extraction
Unstructured LLM extraction
Fixed predicate schema
Knowledge accumulation
Feedback controller
Synthetic-data generation
LoRA adaptation
Provenance
Probabilistic KB
Noisy-Or aggregation
Conflict handling
Iteration tracking
Baseline configurations
Evaluation metrics

These are research-relevant components.

============================================================
# 47. WHAT MUST NOT BE ASSUMED TO BE VALIDATED
============================================================

The following must NOT be treated as proven merely because the
prototype runs:

- SOTA superiority
- generalization
- calibration
- convergence
- factual correctness
- statistical significance
- scalability
- superiority of fine-tuning
- superiority of Prob-KB
- superiority of feedback

These require experiments.

============================================================
# 48. CURRENT RESEARCH STATUS
============================================================

STATUS:

Prototype exists.

Core architectural components exist.

Initial custom-dataset experiments exist.

Probabilistic KB prototype exists.

Mathematical formulation has been separately finalized.

Q1 validation is still in progress.

The next implementation phase is NOT:

"rewrite everything."

The next phase is:

AUDIT
→
TEST
→
MODULARIZE
→
PUBLIC BENCHMARK
→
FAIR BASELINES
→
ABLATIONS
→
STATISTICS
→
MATHEMATICAL VALIDATION
→
SCALABILITY
→
CROSS-DOMAIN
→
FINAL EVIDENCE

============================================================
# 49. AUTHORITY HIERARCHY
============================================================

When documents disagree, use this order:

1. Explicit latest research decision
2. MATH_SPECIFICATION.md for mathematics
3. DECISION_LOG.md for research decisions
4. Current tested implementation
5. Older prototype behaviour
6. Assumptions/inference

Never silently resolve contradictions.

Report them.

============================================================
# 50. INSTRUCTIONS TO ANY LLM READING THIS
============================================================

Before modifying the code:

STEP 1:
Read this entire context.

STEP 2:
Inspect the actual source code.

STEP 3:
Map this description to the actual implementation.

STEP 4:
Identify discrepancies.

STEP 5:
Do NOT assume this document is more accurate than the code regarding
what the code actually does.

If the code differs from this document, report:

CODEBASE CONTEXT DISCREPANCY

Then state:

Expected according to context:
...

Actually implemented:
...

Research impact:
...

Recommended action:
...

============================================================
# 51. REQUIRED RESPONSE WHEN ASKED TO CHANGE CODE
============================================================

Before making major changes, explain:

1. What component is affected?
2. What does it currently do?
3. Why does it need to change?
4. Which research decision requires the change?
5. Does the mathematical specification change?
6. Does the experiment protocol change?
7. What existing behaviour must be preserved?
8. How will the change be tested?

Then implement.

============================================================
# 52. DO NOT REWRITE WITHOUT A REASON
============================================================

Do not rewrite working components merely because:

- the code is ugly
- another architecture is more fashionable
- another library is easier
- a different implementation is shorter

A refactor must preserve intended behaviour unless the task explicitly
requires behavioural change.

============================================================
# 53. SCIENTIFIC INTEGRITY
============================================================

Never:

fabricate metrics
fabricate benchmark results
invent API outputs
invent model behaviour
invent statistical significance
claim experiments were run when they were not
claim code was tested when it was not
delete failed results
silently alter evaluation rules

If something is unknown:

say:

TBD
UNKNOWN
NOT TESTED
REQUIRES EXPERIMENT
REQUIRES DECISION

============================================================
# 54. FINAL MENTAL MODEL
============================================================

Understand SLDE-AFT as five interacting research layers:

LAYER 1 — EXTRACTION

Structured + Unstructured
        ↓
Candidate triples

LAYER 2 — KNOWLEDGE

Candidate triples
        ↓
Knowledge Base
        ↓
Probabilistic evidence accumulation

LAYER 3 — FEEDBACK

Knowledge state
        ↓
Coverage/conflict analysis
        ↓
Feedback
        ↓
Next extraction

LAYER 4 — SELF-SUPERVISION

High-confidence knowledge
        ↓
Synthetic examples
        ↓
LoRA fine-tuning

LAYER 5 — EVALUATION

Predictions
        ↓
Normalization
        ↓
Gold comparison
        ↓
Precision / Recall / F1
        ↓
Calibration / statistics / scalability / error analysis

The scientific contribution is the interaction between these layers,
not merely any individual component.

============================================================
# 55. MOST IMPORTANT INSTRUCTION
============================================================

Do not treat this as an ordinary software project.

It is a research system.

Every major code modification potentially changes the scientific
experiment.

Therefore distinguish:

CODE CHANGE
from
EXPERIMENTAL CHANGE
from
RESEARCH DESIGN CHANGE.

A cleaner implementation is not necessarily the same scientific
method.

A faster implementation is not necessarily the same experiment.

A better metric is not necessarily a fair comparison.

Always preserve experimental traceability.

END OF SLDE-AFT CODEBASE CONTEXT