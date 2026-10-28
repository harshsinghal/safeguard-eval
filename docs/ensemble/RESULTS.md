# Complete ensemble results

Every family below was registered before fitting. Its configuration and blocking threshold were selected on validation accuracy, with macro-F1 as the first tie-break. Logistic regression was the primary method. All scores are percentages; differences are percentage points.

Test results are exploratory because these official tests were used in earlier studies. Intervals are unadjusted paired group-bootstrap intervals (2,000 replicates), not corrections for multiple comparisons or model-selection uncertainty.

## WildGuard · 3 specialists

Test examples: **1,699**. Validation-selected ensemble: `weighted/lambda0`. Validation-selected individual: `single/shieldstral/logistic-C0.01`.

| Method | Test accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| WildGuard model | 90.35 | 90.13 | 85.01 | 51 | 113 |
| Selected individual | 90.88 | 90.71 | 87.40 | 60 | 95 |
| Equal average | 91.41 | 91.24 | 87.67 | 53 | 93 |
| Calibrated average | 91.17 | 91.02 | 88.06 | 60 | 90 |
| Learned weighted average | 90.88 | 90.71 | 87.40 | 60 | 95 |
| Logistic regression | 90.76 | 90.59 | 87.14 | 60 | 97 |
| Random forest | 90.94 | 90.77 | 87.40 | 59 | 95 |

The comparison below is against the individual selected on validation, including its calibration/threshold tuning.

| Ensemble | Accuracy difference | 95% interval | Cases corrected | Cases made wrong |
|---|---:|---:|---:|---:|
| Equal average | +0.53 | -0.12 to +1.18 | 21 | 12 |
| Calibrated average | +0.29 | -0.29 to +0.94 | 18 | 13 |
| Learned weighted average | +0.00 | +0.00 to +0.00 | 0 | 0 |
| Logistic regression | -0.12 | -0.35 to +0.12 | 1 | 3 |
| Random forest | +0.06 | +0.00 to +0.18 | 1 | 0 |

### Individual-model controls

| Model | Raw score at 0.5: accuracy | Validation-selected individual: accuracy | Selected threshold / configuration |
|---|---:|---:|---|
| policylm | 86.82 | 86.46 | 0.46 / `single/policylm/logistic-C1` |
| shieldstral | 90.82 | 90.88 | 0.34 / `single/shieldstral/logistic-C0.01` |
| cope | 90.76 | 90.70 | 0.49 / `single/cope/logistic-C0.1` |

A threshold on a calibrated score is not the same numerical threshold on the raw score. Monotonic single-model calibration changes the decision boundary, not the order of examples.

### Frozen choices

| Family | Candidate | Validation accuracy | Threshold |
|---|---|---:|---:|
| single | `single/shieldstral/logistic-C0.01` | 98.70 | 0.34 |
| equal-raw | `equal/raw` | 97.66 | 0.43 |
| equal-calibrated | `equal/calibrated` | 98.18 | 0.37 |
| weighted | `weighted/lambda0` | 98.70 | 0.29 |
| logistic | `logistic/C1` | 98.63 | 0.41 |
| forest | `forest/depth4-leaf20` | 98.63 | 0.41 |

Learned averaging weights: policylm 0.00%, shieldstral 99.41%, cope 0.59%.

### Complementary errors

| Pair | Disagreements | Both wrong | First correct, second wrong | Second correct, first wrong |
|---|---:|---:|---:|---:|
| policylm / shieldstral | 133 | 126 | 29 | 104 |
| policylm / cope | 158 | 115 | 43 | 115 |
| shieldstral / cope | 77 | 118 | 40 | 37 |

A hindsight rule that could choose a correct individual whenever one existed would reach 94.00%. It uses the answer key and cannot be deployed. It is not an upper bound on ensembles that use continuous scores.

The highest test accuracy among all registered individual configurations was 90.88%. This is a descriptive hurdle, not a test-based selector.

All candidate metrics, binary confusion matrices, category/platform/annotation-agreement slices and per-example decisions are retained in the cohort evidence. Single-label slices should be interpreted using counts and recall, not their two-class macro-F1.

## HateXplain · 2 specialists

Test examples: **1,924**. Validation-selected ensemble: `forest/depth2-leaf20`. Validation-selected individual: `single/shieldstral/logistic-C0.01`.

| Method | Test accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| Selected individual | 79.57 | 75.62 | 63.64 | 177 | 216 |
| Equal average | 72.87 | 67.16 | 50.51 | 228 | 294 |
| Calibrated average | 74.38 | 68.53 | 50.67 | 200 | 293 |
| Learned weighted average | 77.86 | 73.97 | 63.47 | 209 | 217 |
| Logistic regression | 75.57 | 69.85 | 51.85 | 184 | 286 |
| Random forest | 79.31 | 75.25 | 62.79 | 177 | 221 |

The comparison below is against the individual selected on validation, including its calibration/threshold tuning.

| Ensemble | Accuracy difference | 95% interval | Cases corrected | Cases made wrong |
|---|---:|---:|---:|---:|
| Equal average | -6.70 | -8.43 to -4.83 | 101 | 230 |
| Calibrated average | -5.20 | -6.87 to -3.48 | 92 | 192 |
| Learned weighted average | -1.72 | -2.75 to -0.73 | 31 | 64 |
| Logistic regression | -4.00 | -5.56 to -2.54 | 75 | 152 |
| Random forest | -0.26 | -0.62 to +0.10 | 5 | 10 |

### Individual-model controls

| Model | Raw score at 0.5: accuracy | Validation-selected individual: accuracy | Selected threshold / configuration |
|---|---:|---:|---|
| policylm | 68.71 | 72.19 | 0.52 / `single/policylm/logistic-C1` |
| shieldstral | 53.17 | 79.57 | 0.48 / `single/shieldstral/logistic-C0.01` |

A threshold on a calibrated score is not the same numerical threshold on the raw score. Monotonic single-model calibration changes the decision boundary, not the order of examples.

### Frozen choices

| Family | Candidate | Validation accuracy | Threshold |
|---|---|---:|---:|
| single | `single/shieldstral/logistic-C0.01` | 79.30 | 0.48 |
| equal-raw | `equal/raw` | 73.76 | 0.74 |
| equal-calibrated | `equal/calibrated` | 74.80 | 0.45 |
| weighted | `weighted/lambda0` | 78.06 | 0.50 |
| logistic | `logistic/C1` | 76.24 | 0.52 |
| forest | `forest/depth2-leaf20` | 79.10 | 0.39 |

Learned averaging weights: policylm 11.10%, shieldstral 88.90%.

### Complementary errors

| Pair | Disagreements | Both wrong | First correct, second wrong | Second correct, first wrong |
|---|---:|---:|---:|---:|
| policylm / shieldstral | 410 | 259 | 134 | 276 |

A hindsight rule that could choose a correct individual whenever one existed would reach 86.54%. It uses the answer key and cannot be deployed. It is not an upper bound on ensembles that use continuous scores.

The highest test accuracy among all registered individual configurations was 79.57%. This is a descriptive hurdle, not a test-based selector.

All candidate metrics, binary confusion matrices, category/platform/annotation-agreement slices and per-example decisions are retained in the cohort evidence. Single-label slices should be interpreted using counts and recall, not their two-class macro-F1.

## HateXplain · specialists + Qwen

Test examples: **1,924**. Validation-selected ensemble: `forest/depth4-leaf20`. Validation-selected individual: `single/qwen-4b/logistic-C0.01`.

| Method | Test accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| Selected individual | 79.16 | 74.03 | 56.23 | 141 | 260 |
| Equal average | 75.83 | 70.73 | 55.22 | 199 | 266 |
| Calibrated average | 77.55 | 74.17 | 67.00 | 236 | 196 |
| Learned weighted average | 79.47 | 75.11 | 60.94 | 163 | 232 |
| Logistic regression | 78.69 | 75.29 | 67.34 | 216 | 194 |
| Random forest | 79.73 | 74.73 | 57.07 | 135 | 255 |

The comparison below is against the individual selected on validation, including its calibration/threshold tuning.

| Ensemble | Accuracy difference | 95% interval | Cases corrected | Cases made wrong |
|---|---:|---:|---:|---:|
| Equal average | -3.33 | -5.15 to -1.56 | 111 | 175 |
| Calibrated average | -1.61 | -3.17 to -0.10 | 104 | 135 |
| Learned weighted average | +0.31 | -0.78 to +1.30 | 57 | 51 |
| Logistic regression | -0.47 | -1.87 to +0.83 | 89 | 98 |
| Random forest | +0.57 | -0.78 to +1.87 | 84 | 73 |

### Individual-model controls

| Model | Raw score at 0.5: accuracy | Validation-selected individual: accuracy | Selected threshold / configuration |
|---|---:|---:|---|
| policylm | 68.71 | 72.19 | 0.52 / `single/policylm/logistic-C1` |
| shieldstral | 53.17 | 79.57 | 0.48 / `single/shieldstral/logistic-C0.01` |
| qwen-4b | 72.04 | 79.16 | 0.55 / `single/qwen-4b/logistic-C0.01` |

A threshold on a calibrated score is not the same numerical threshold on the raw score. Monotonic single-model calibration changes the decision boundary, not the order of examples.

### Frozen choices

| Family | Candidate | Validation accuracy | Threshold |
|---|---|---:|---:|
| single | `single/qwen-4b/logistic-C0.01` | 79.82 | 0.55 |
| equal-raw | `equal/raw` | 77.02 | 0.74 |
| equal-calibrated | `equal/calibrated` | 78.26 | 0.43 |
| weighted | `weighted/lambda0` | 80.47 | 0.54 |
| logistic | `logistic/C10` | 80.08 | 0.52 |
| forest | `forest/depth4-leaf20` | 80.99 | 0.49 |

Learned averaging weights: policylm 0.00%, shieldstral 34.66%, qwen-4b 65.34%.

### Complementary errors

| Pair | Disagreements | Both wrong | First correct, second wrong | Second correct, first wrong |
|---|---:|---:|---:|---:|
| policylm / shieldstral | 410 | 259 | 134 | 276 |
| policylm / qwen-4b | 416 | 260 | 141 | 275 |
| shieldstral / qwen-4b | 322 | 236 | 165 | 157 |

A hindsight rule that could choose a correct individual whenever one existed would reach 90.59%. It uses the answer key and cannot be deployed. It is not an upper bound on ensembles that use continuous scores.

The highest test accuracy among all registered individual configurations was 79.57%. This is a descriptive hurdle, not a test-based selector.

All candidate metrics, binary confusion matrices, category/platform/annotation-agreement slices and per-example decisions are retained in the cohort evidence. Single-label slices should be interpreted using counts and recall, not their two-class macro-F1.

