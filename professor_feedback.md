# Professor Feedback — SLDE-AFT Paper

Dear Shashank,

Thank you for your considerable effort on this work. The paper demonstrates a solid understanding of current research in information extraction, LLM adaptation, and knowledge representation. The proposed SLDE-AFT architecture has good potential and addresses an interesting research gap. However, if our goal is publication in a strong Q1 journal, the paper requires substantial improvements before submission.

Please address the following points carefully.

## 1. Strengthen the Experimental Evaluation (Highest Priority)

This is currently the weakest aspect of the paper.

The evaluation uses only a custom dataset of 20 to 50 products. While this is acceptable for demonstrating a proof of concept, it is insufficient for validating a new research framework intended for the broader AI community.

Please add experiments using established public benchmarks such as:

- DocRED
- TACRED
- REBEL benchmark
- Universal IE datasets
- OpenIE benchmark datasets

Using only a custom dataset will significantly reduce the paper's credibility during peer review.

## 2. Compare Against State-of-the-Art Methods

The current baselines are mostly internal variations of your own system.

A Q1 reviewer will expect comparisons with strong external methods including:

- REBEL
- GenIE
- InstructUIE
- DyGIE++
- GPT-4 extraction
- Llama-3 extraction
- Claude
- Gemini

Without these comparisons, reviewers cannot determine whether SLDE-AFT actually advances the state of the art.

## 3. Improve the Mathematical Contribution

Currently, the mathematical novelty is limited.

The Noisy-Or confidence aggregation is useful but should be strengthened.

Please include:

- Formal derivation
- Theoretical justification
- Convergence discussion
- Computational complexity analysis
- Confidence calibration analysis

If possible, provide theoretical guarantees regarding the probabilistic knowledge accumulation process.

## 4. Conduct a Proper Ablation Study

Each module should be evaluated independently.

Please evaluate the system after removing:

- Feedback Controller
- Probabilistic KB
- Synthetic Data Generator
- LoRA Fine-Tuning
- Provenance Module
- Structured Input
- Unstructured Input

This will clearly demonstrate the contribution of every architectural component.

## 5. Add Statistical Validation

Currently, all reported improvements are based on single values.

Please perform:

- Multiple independent runs
- Mean ± standard deviation
- Confidence intervals
- Statistical significance testing (t-test or Wilcoxon)

Without statistical validation, reviewers may question whether the reported improvements are reproducible.

## 6. Improve the Fine-Tuning Section

The fine-tuning results are currently too weak.

The reported F1 improvement remains very small, making it difficult to justify the automatic fine-tuning component as a major contribution.

Please investigate:

- Larger base models (7B or above)
- Additional training epochs
- Larger synthetic datasets
- Improved instruction generation
- Better LoRA hyperparameter tuning

The fine-tuning component should produce a meaningful improvement.

## 7. Add Error Analysis

A Q1 paper should include qualitative analysis.

Please provide examples of:

- Correct extraction
- Failed extraction
- Hallucinated triples
- Conflicting triples
- Ambiguous relations
- Provenance filtering examples

Explain why the system succeeds or fails in each case.

## 8. Evaluate Scalability

The scalability section should be expanded considerably.

Please report:

- Execution time
- Memory consumption
- GPU utilization
- KB growth
- Inference latency

Evaluate the system on much larger datasets.

## 9. Validate on Multiple Domains

Currently, all experiments are based on consumer products.

Please evaluate at least one additional domain, such as:

- Biomedical
- Scientific publications
- Manufacturing
- Automotive
- Legal documents

This will demonstrate that the framework generalizes beyond a single application.

## 10. Strengthen the Discussion

The discussion should be more analytical.

Instead of only describing results, explain:

- Why precision improves significantly
- Why recall remains relatively unchanged
- Why Prob-KB maintains perfect recall
- Under which scenarios the framework performs best
- Where the framework may fail

Readers should understand both the strengths and limitations of the proposed approach.

## 11. Improve the Novelty Positioning

The current novelty statement is good but should be more precise.

Explicitly explain how SLDE-AFT differs from:

- Retrieval-Augmented Generation
- Continual Learning
- AutoML
- Universal Information Extraction
- Knowledge Graph Population
- Self-Training

Avoid broad claims such as "the first system" unless they are fully supported by the literature.

## 12. Improve Reproducibility

Please prepare supplementary materials including:

- Source code
- Datasets
- Prompts
- Configuration files
- Hyperparameters
- Evaluation scripts

High-quality journals increasingly expect reproducible research.

## 13. Refine the Writing

The manuscript is generally well written. However, several sections can be made more concise.

Please:

- Reduce repetitive explanations
- Shorten long paragraphs
- Improve transitions between sections
- Ensure every figure is fully discussed in the text
- Verify that every reference directly supports the associated claim

## Overall Assessment

This paper presents a promising and well-structured research idea with the potential to make a meaningful contribution to self-improving information extraction systems. The architectural design is coherent, the literature review is comprehensive, and the writing quality is already at a good level.

However, the experimental validation is not yet sufficient for publication in a strong Q1 journal. Our highest priority must be to strengthen the empirical evidence through larger-scale evaluations, comparisons with state-of-the-art methods, rigorous statistical analysis, and deeper theoretical justification.

Once these improvements are completed, I believe the manuscript will be substantially stronger and much more competitive for publication in a reputable Q1 journal.
