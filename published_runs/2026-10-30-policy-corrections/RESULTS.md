# Full policy-correction results

Policy text and model weights were frozen before validation/test inference at their registered stages. Only validation chose the revision and cutoffs. The additional project holdout and the repeatedly examined WildGuardTest are separate populations; do not pool their scores.

## Discovery and validation

All candidates preserve the original clauses. p1 clarifies allowed cases; p2 clarifies prohibited cases; p3 combines both; p4 adds two contrastive example pairs. Discovery uses 4,096 previously used fitting examples; fresh validation has 1,536 unique groups.

| Policy | Discovery BA at 0.5 | Discovery FP / FN | Validation BA at 0.5 | Validation BA with selected cutoff | Cutoff |
|---|---:|---:|---:|---:|---:|
| p0 | 98.61% | 18 / 40 | 98.22% | 98.29% | 0.51 |
| p1 | 98.62% | 17 / 41 | 98.43% | 98.43% | 0.5 (native) |
| p2 | 98.61% | 18 / 40 | 98.30% | 98.30% | 0.5 (native) |
| p3 | 98.67% | 16 / 40 | 98.16% | 98.16% | 0.5 (native) |
| p4 | 98.53% | 21 / 40 | 97.84% | 97.99% | 0.6 |

The selected revision is **p1**. This is the best revision on validation under the registered objective; it may still lose to the original policy. Qwen receives this exact revision without Qwen-specific policy search.

### What happened to the discovery mistakes

This is a descriptive check on the examples used to motivate the edits, not evidence of generalization. All rows use cutoff 0.5. The motivating subset contains 19 original errors; the other 39 original errors remain in the population with unchanged labels.

| Revision | Corrected false blocks | Corrected misses | Newly false-blocked | Newly missed | Motivating errors corrected / 19 |
|---|---:|---:|---:|---:|---:|
| p1 | 4 | 2 | 3 | 3 | 3 |
| p2 | 3 | 2 | 3 | 2 | 4 |
| p3 | 5 | 3 | 3 | 3 | 6 |
| p4 | 3 | 3 | 6 | 3 | 4 |

### Qwen transfer validation

Qwen receives the Shieldstral-selected revision without a wording search. Each row also shows a separate cutoff-only selection on the same validation population.

| Policy | BA at 0.5 | FP / FN at 0.5 | BA with selected cutoff | Selected cutoff | FP / FN with selected cutoff |
|---|---:|---:|---:|---:|---:|
| p0 | 88.12% | 115 / 65 | 89.61% | 0.57 | 72 / 88 |
| p1 | 90.43% | 81 / 65 | 90.43% | 0.5 (native) | 81 / 65 |

## Additional project holdout

2048 examples in 2048 recorded duplicate groups. Confidence intervals are 95% paired group-bootstrap intervals.

| Model | Configuration | Policy | Cutoff | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | MCC | FP | FN | Unresolved | AUROC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen | baseline-native | p0 | 0.5 | 88.73% (87.30%–90.03%) | 88.82% | 88.78% | 0.7768 | 140 | 89 | 0 | 0.9599 |
| qwen | baseline-tuned | p0 | 0.57 | 88.85% (87.45%–90.14%) | 88.82% | 88.82% | 0.7767 | 100 | 129 | 0 | 0.9599 |
| qwen | revised-native | p1 | 0.5 | 89.77% (88.40%–91.04%) | 89.79% | 89.78% | 0.7957 | 110 | 99 | 0 | 0.9656 |
| qwen | revised-tuned | p1 | 0.5 (native) | 89.77% (88.40%–91.04%) | 89.79% | 89.78% | 0.7957 | 110 | 99 | 0 | 0.9656 |
| shieldstral | baseline-native | p0 | 0.5 | 98.18% (97.59%–98.75%) | 98.14% | 98.14% | 0.9631 | 8 | 30 | 0 | 0.9956 |
| shieldstral | baseline-tuned | p0 | 0.51 | 98.23% (97.64%–98.79%) | 98.19% | 98.19% | 0.9641 | 7 | 30 | 0 | 0.9956 |
| shieldstral | revised-native | p1 | 0.5 | 98.13% (97.52%–98.70%) | 98.10% | 98.09% | 0.9621 | 8 | 31 | 0 | 0.9957 |
| shieldstral | revised-tuned | p1 | 0.5 (native) | 98.13% (97.52%–98.70%) | 98.10% | 98.09% | 0.9621 | 8 | 31 | 0 | 0.9957 |

### Paired differences

Differences are balanced-accuracy percentage points. These intervals do not adjust for the policy search, multiple comparisons, or earlier public-test use.

| Model | Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |
|---|---|---|---:|---:|---:|---:|
| qwen | revised-tuned | baseline-tuned | +0.92 | +0.17 to +1.70 | 42 | 22 |
| qwen | revised-native | baseline-native | +1.04 | +0.36 to +1.73 | 36 | 16 |
| qwen | baseline-tuned | baseline-native | +0.12 | -0.74 to +0.93 | 40 | 40 |
| shieldstral | revised-tuned | baseline-tuned | -0.10 | -0.29 to +0.09 | 1 | 3 |
| shieldstral | revised-native | baseline-native | -0.05 | -0.20 to +0.10 | 1 | 2 |
| shieldstral | baseline-tuned | baseline-native | +0.05 | +0.00 to +0.16 | 1 | 0 |

### Operating targets selected on validation

These profiles hold the selected policy fixed and choose another cutoff for each target. A validation target is not a guarantee on new data.

| Model | Validation target | Policy | Cutoff | False-block rate | Harmful recall | Target held? |
|---|---|---|---:|---:|---:|---|
| qwen | false_block_limit | p0 | 0.71 | 4.84% | 76.52% | Yes |
| qwen | false_block_limit | p1 | 0.66 | 4.64% | 80.49% | Yes |
| qwen | catch_target | p0 | 0.51 | 12.60% | 90.06% | Yes |
| qwen | catch_target | p1 | 0.51 | 9.27% | 89.39% | No |
| shieldstral | false_block_limit | p0 | 0.11 | 2.12% | 98.96% | Yes |
| shieldstral | false_block_limit | p1 | 0.08 | 3.02% | 99.05% | Yes |
| shieldstral | catch_target | p0 | 0.86 | 0.30% | 94.22% | Yes |
| shieldstral | catch_target | p1 | 0.8 | 0.50% | 95.36% | Yes |

## Reused WildGuardTest

1699 examples in 1699 recorded duplicate groups. Confidence intervals are 95% paired group-bootstrap intervals.

| Model | Configuration | Policy | Cutoff | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | MCC | FP | FN | Unresolved | AUROC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen | baseline-native | p0 | 0.5 | 86.47% (84.87%–88.12%) | 86.11% | 86.05% | 0.7249 | 158 | 78 | 0 | 0.9345 |
| qwen | baseline-tuned | p0 | 0.57 | 86.01% (84.37%–87.75%) | 86.17% | 86.00% | 0.7199 | 119 | 116 | 0 | 0.9345 |
| qwen | revised-native | p1 | 0.5 | 86.82% (85.20%–88.51%) | 86.76% | 86.64% | 0.7336 | 130 | 95 | 0 | 0.9375 |
| qwen | revised-tuned | p1 | 0.5 (native) | 86.82% (85.20%–88.51%) | 86.76% | 86.64% | 0.7336 | 130 | 95 | 0 | 0.9375 |
| shieldstral | baseline-native | p0 | 0.5 | 90.30% (88.82%–91.68%) | 90.70% | 90.52% | 0.8116 | 58 | 100 | 0 | 0.9485 |
| shieldstral | baseline-tuned | p0 | 0.51 | 90.29% (88.81%–91.68%) | 90.70% | 90.52% | 0.8116 | 57 | 101 | 0 | 0.9485 |
| shieldstral | revised-native | p1 | 0.5 | 90.15% (88.69%–91.56%) | 90.58% | 90.40% | 0.8093 | 57 | 103 | 0 | 0.9479 |
| shieldstral | revised-tuned | p1 | 0.5 (native) | 90.15% (88.69%–91.56%) | 90.58% | 90.40% | 0.8093 | 57 | 103 | 0 | 0.9479 |

### Paired differences

Differences are balanced-accuracy percentage points. These intervals do not adjust for the policy search, multiple comparisons, or earlier public-test use.

| Model | Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |
|---|---|---|---:|---:|---:|---:|
| qwen | revised-tuned | baseline-tuned | +0.81 | -0.04 to +1.63 | 31 | 21 |
| qwen | revised-native | baseline-native | +0.35 | -0.48 to +1.15 | 31 | 20 |
| qwen | baseline-tuned | baseline-native | -0.46 | -1.49 to +0.53 | 39 | 38 |
| shieldstral | revised-tuned | baseline-tuned | -0.13 | -0.43 to +0.14 | 2 | 4 |
| shieldstral | revised-native | baseline-native | -0.15 | -0.46 to +0.14 | 2 | 4 |
| shieldstral | baseline-tuned | baseline-native | -0.01 | -0.20 to +0.15 | 1 | 1 |

### Operating targets selected on validation

These profiles hold the selected policy fixed and choose another cutoff for each target. A validation target is not a guarantee on new data.

| Model | Validation target | Policy | Cutoff | False-block rate | Harmful recall | Target held? |
|---|---|---|---:|---:|---:|---|
| qwen | false_block_limit | p0 | 0.71 | 6.88% | 76.13% | No |
| qwen | false_block_limit | p1 | 0.66 | 6.56% | 78.65% | No |
| qwen | catch_target | p0 | 0.51 | 14.92% | 87.53% | No |
| qwen | catch_target | p1 | 0.51 | 12.28% | 86.07% | No |
| shieldstral | false_block_limit | p0 | 0.11 | 8.47% | 89.26% | No |
| shieldstral | false_block_limit | p1 | 0.08 | 8.78% | 89.79% | No |
| shieldstral | catch_target | p0 | 0.86 | 4.76% | 82.23% | No |
| shieldstral | catch_target | p1 | 0.8 | 4.87% | 82.76% | No |

All original labels and unresolved cases remain in their denominators. The machine-readable results also retain category/adversarial slices, precision, recall, specificity, Brier score and log loss. Source prompts remain private.
