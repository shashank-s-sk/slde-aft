# DEC-002 External LLM Baseline Error Analysis

## Experiment

- Decision: DEC-002
- Dataset: CaRB first 10 development sentences
- Gold triples: 35
- Model: `meta-llama/llama-3.1-8b-instruct`
- Provider: OpenRouter
- Prompt: `openie_carb_v1`
- Temperature: `0.0`
- Evaluator: Shared internal normalized exact-match triple evaluator

## Metrics

| Metric | Value |
|---|---:|
| Precision | 0.0345 |
| Recall | 0.0286 |
| F1 | 0.0312 |
| True positives | 1 |
| False positives | 28 |
| False negatives | 34 |
| Predicted triples | 29 |
| Gold triples | 35 |

## Error categories

### Correct extraction

**Sentence:** A partial list of turbomachinery that may use one or more centrifugal compressors within the machine are listed here.

**Matching triple:**

```text
(turbomachinery; may use; one or more centrifugal compressors)
```

**Interpretation:** The model produced a triple whose subject, predicate, and object aligned with the CaRB gold representation after normalization.

### Subject-boundary mismatch

**Sentence:** 32.7% of all households were made up of individuals and 15.7% had someone living alone who was 65 years of age or older.

**Prediction:**

```text
(all households; were made up of; individuals)
```

**Gold:**

```text
(32.7% of all households; were made up of; individuals)
```

**Interpretation:** The extraction is semantically related, but the model omitted the percentage phrase from the subject. It is therefore counted as a false positive under exact matching and causes a corresponding false negative for the gold triple.

### Subject-boundary mismatch

**Sentence:** 32.7% of all households were made up of individuals and 15.7% had someone living alone who was 65 years of age or older.

**Prediction:**

```text
(all households; had; someone living alone who was 65 years of age or older)
```

**Gold:**

```text
(15.7% of all households; had; someone living alone who was 65 years of age or older)
```

**Interpretation:** The model preserved most of the relation and object but omitted the quantitative part of the subject. This does not satisfy the shared exact-match evaluation rule.

### Compound-fact segmentation mismatch

**Sentence:** A CEN forms an important but small part of a Local Strategic Partnership.

**Prediction:**

```text
(a cen; forms; an important but small part of a local strategic partnership)
```

**Gold extractions:**

```text
(a cen; forms; an important part of a local strategic partnership)
(a cen; forms; a small part of a local strategic partnership)
```

**Interpretation:** The model produced one combined extraction, while CaRB gold annotations split the compound description into two triples. The combined output is treated as one false positive, while both separate gold triples are treated as false negatives.

## Conclusion

The low internal exact-match score is influenced by three recurring failure modes:

1. Subject-boundary omissions, particularly numerical modifiers.
2. Differences in predicate/object segmentation.
3. Merging of compound facts that CaRB represents as multiple gold triples.

These examples show that strict normalized exact matching penalizes semantically related triples whose boundaries differ from the gold annotation style. This analysis does not change the reported metrics. The same evaluator and normalization were applied consistently to the SLDE-AFT configuration and the external baseline.