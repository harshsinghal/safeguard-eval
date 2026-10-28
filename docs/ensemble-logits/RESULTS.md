# Log-odds ensemble: complete results

All configurations and thresholds were selected on validation before this extension was tested. Policies, model weights and examples stayed fixed. Earlier official test results were already known, so all comparisons remain exploratory. Differences and confidence intervals below are in percentage points.

## WildGuard · specialists

Fit: 4,096; validation: 1,536; test: 1,699.

| Method | Accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| Previous probability logistic | 90.76% | 90.59% | 87.14% | 60 | 97 |
| New log-odds logistic | 91.29% | 91.14% | 88.46% | 61 | 87 |
| Individual selected with expanded controls | 90.76% | 90.60% | 87.40% | 62 | 95 |
| Previously selected individual | 90.88% | 90.71% | 87.40% | 60 | 95 |
| Previously selected ensemble | 90.88% | 90.71% | 87.40% | 60 | 95 |
| Equal log-odds average | 90.94% | 90.81% | 89.52% | 75 | 79 |
| WildGuard external baseline | 90.35% | 90.13% | 85.01% | 51 | 113 |

### Primary comparisons

| New log-odds logistic versus… | Accuracy difference | 95% interval | Macro-F1 difference | Cases corrected | Cases made wrong |
|---|---:|---:|---:|---:|---:|
| Previous probability logistic | +0.53 | +0.18 to +0.94 | +0.55 | 10 | 1 |
| Individual selected with expanded controls | +0.53 | +0.24 to +0.94 | +0.55 | 9 | 0 |
| Previously selected individual | +0.41 | +0.12 to +0.77 | +0.43 | 8 | 1 |
| Previously selected ensemble | +0.41 | +0.12 to +0.77 | +0.43 | 8 | 1 |
| WildGuard external baseline | +0.94 | +0.06 to +1.77 | +1.02 | 34 | 18 |

Intervals use 2,000 paired duplicate-group bootstrap replicates. They are unadjusted, exclude search/inference uncertainty, and do not turn the reused tests into confirmatory evidence.

### Individual controls selected on validation

| Model | Selected configuration | Accuracy | Macro-F1 | Violation recall |
|---|---|---:|---:|---:|
| policylm | `single/policylm/logistic-C1` | 86.46% | 86.25% | 83.29% |
| shieldstral | `logit-single/shieldstral/C0.01` | 90.76% | 90.60% | 87.40% |
| cope | `logit-single/cope/C0.01` | 90.70% | 90.50% | 85.94% |

Highest individual accuracy across all registered configurations on this test: **90.88%**. This is a descriptive hurdle, not a test-selected baseline for fitting.

### Every new configuration

| Configuration | Validation accuracy | Threshold | Test accuracy | Macro-F1 | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|---:|
| `logit-single/policylm/C0.01` | 92.25% | 0.49 | 86.58% | 86.34% | 96 | 132 |
| `logit-single/policylm/C0.1` | 92.25% | 0.50 | 86.82% | 86.56% | 91 | 133 |
| `logit-single/policylm/C1` | 92.25% | 0.50 | 86.82% | 86.56% | 91 | 133 |
| `logit-single/policylm/C10` | 92.25% | 0.50 | 86.87% | 86.63% | 91 | 132 |
| `logit-single/policylm/C100` | 92.25% | 0.50 | 86.87% | 86.63% | 91 | 132 |
| `logit-single/shieldstral/C0.01` | 98.70% | 0.50 | 90.76% | 90.60% | 62 | 95 |
| `logit-single/shieldstral/C0.1` | 98.70% | 0.50 | 90.76% | 90.60% | 62 | 95 |
| `logit-single/shieldstral/C1` | 98.70% | 0.50 | 90.76% | 90.60% | 62 | 95 |
| `logit-single/shieldstral/C10` | 98.70% | 0.50 | 90.76% | 90.60% | 62 | 95 |
| `logit-single/shieldstral/C100` | 98.70% | 0.50 | 90.76% | 90.60% | 62 | 95 |
| `logit-single/cope/C0.01` | 94.92% | 0.49 | 90.70% | 90.50% | 52 | 106 |
| `logit-single/cope/C0.1` | 94.92% | 0.51 | 90.70% | 90.50% | 52 | 106 |
| `logit-single/cope/C1` | 94.92% | 0.52 | 90.70% | 90.50% | 52 | 106 |
| `logit-single/cope/C10` | 94.92% | 0.50 | 90.70% | 90.50% | 52 | 106 |
| `logit-single/cope/C100` | 94.92% | 0.50 | 90.70% | 90.50% | 52 | 106 |
| `logit-logistic/C0.01` | 98.24% | 0.44 | 91.41% | 91.25% | 55 | 91 |
| `logit-logistic/C0.1` | 98.57% | 0.55 | 91.11% | 90.94% | 54 | 97 |
| `logit-logistic/C1` | 98.57% | 0.66 | 91.05% | 90.87% | 52 | 100 |
| `logit-logistic/C10` | 98.63% | 0.40 | 91.29% | 91.14% | 61 | 87 |
| `logit-logistic/C100` | 98.63% | 0.40 | 91.29% | 91.14% | 61 | 87 |
| `logit-equal` | 97.27% | 0.06 | 90.94% | 90.81% | 75 | 79 |

### The learned equation

Let each input be that model’s reconstructed log-odds. These coefficients absorb the training-only standardization:

| Term | Coefficient |
|---|---:|
| Intercept | 0.712154 |
| policylm | 0.031066 |
| shieldstral | 0.765226 |
| cope | 0.049981 |

Apply sigmoid to the sum and BLOCK when the result is at least **0.40**. Negative coefficients are permitted. A coefficient is conditional on the other model scores, not a causal measure of the model’s quality.

## HateXplain · specialists

Fit: 4,096; validation: 1,536; test: 1,924.

| Method | Accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| Previous probability logistic | 75.57% | 69.85% | 51.85% | 184 | 286 |
| New log-odds logistic | 78.79% | 72.26% | 48.99% | 105 | 303 |
| Individual selected with expanded controls | 79.57% | 75.62% | 63.64% | 177 | 216 |
| Previously selected individual | 79.57% | 75.62% | 63.64% | 177 | 216 |
| Previously selected ensemble | 79.31% | 75.25% | 62.79% | 177 | 221 |
| Equal log-odds average | 77.34% | 71.51% | 52.02% | 151 | 285 |

### Primary comparisons

| New log-odds logistic versus… | Accuracy difference | 95% interval | Macro-F1 difference | Cases corrected | Cases made wrong |
|---|---:|---:|---:|---:|---:|
| Previous probability logistic | +3.22 | +1.61 to +4.89 | +2.40 | 173 | 111 |
| Individual selected with expanded controls | -0.78 | -2.03 to +0.52 | -3.36 | 72 | 87 |
| Previously selected individual | -0.78 | -2.03 to +0.52 | -3.36 | 72 | 87 |
| Previously selected ensemble | -0.52 | -1.77 to +0.73 | -2.99 | 72 | 82 |

Intervals use 2,000 paired duplicate-group bootstrap replicates. They are unadjusted, exclude search/inference uncertainty, and do not turn the reused tests into confirmatory evidence.

### Individual controls selected on validation

| Model | Selected configuration | Accuracy | Macro-F1 | Violation recall |
|---|---|---:|---:|---:|
| policylm | `logit-single/policylm/C0.1` | 71.88% | 62.59% | 35.69% |
| shieldstral | `single/shieldstral/logistic-C0.01` | 79.57% | 75.62% | 63.64% |

Highest individual accuracy across all registered configurations on this test: **79.57%**. This is a descriptive hurdle, not a test-selected baseline for fitting.

### Every new configuration

| Configuration | Validation accuracy | Threshold | Test accuracy | Macro-F1 | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|---:|
| `logit-single/policylm/C0.01` | 71.42% | 0.42 | 71.47% | 64.57% | 218 | 331 |
| `logit-single/policylm/C0.1` | 71.68% | 0.47 | 71.88% | 62.59% | 159 | 382 |
| `logit-single/policylm/C1` | 71.48% | 0.43 | 71.00% | 64.41% | 233 | 325 |
| `logit-single/policylm/C10` | 71.48% | 0.43 | 71.00% | 64.44% | 234 | 324 |
| `logit-single/policylm/C100` | 71.48% | 0.43 | 71.00% | 64.44% | 234 | 324 |
| `logit-single/shieldstral/C0.01` | 79.30% | 0.43 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C0.1` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C1` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C10` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C100` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-logistic/C0.01` | 79.23% | 0.44 | 79.16% | 74.79% | 168 | 233 |
| `logit-logistic/C0.1` | 78.97% | 0.46 | 79.57% | 75.16% | 159 | 234 |
| `logit-logistic/C1` | 79.36% | 0.55 | 78.79% | 72.26% | 105 | 303 |
| `logit-logistic/C10` | 79.36% | 0.55 | 78.85% | 72.34% | 105 | 302 |
| `logit-logistic/C100` | 79.36% | 0.55 | 78.90% | 72.43% | 105 | 301 |
| `logit-equal` | 77.73% | 0.91 | 77.34% | 71.51% | 151 | 285 |

### The learned equation

Let each input be that model’s reconstructed log-odds. These coefficients absorb the training-only standardization:

| Term | Coefficient |
|---|---:|
| Intercept | -2.501133 |
| policylm | -0.059926 |
| shieldstral | 0.572218 |

Apply sigmoid to the sum and BLOCK when the result is at least **0.55**. Negative coefficients are permitted. A coefficient is conditional on the other model scores, not a causal measure of the model’s quality.

## HateXplain · specialists + Qwen

Fit: 4,096; validation: 1,536; test: 1,924.

| Method | Accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| Previous probability logistic | 78.69% | 75.29% | 67.34% | 216 | 194 |
| New log-odds logistic | 80.82% | 76.58% | 61.95% | 143 | 226 |
| Individual selected with expanded controls | 79.16% | 74.03% | 56.23% | 141 | 260 |
| Previously selected individual | 79.16% | 74.03% | 56.23% | 141 | 260 |
| Previously selected ensemble | 79.73% | 74.73% | 57.07% | 135 | 255 |
| Equal log-odds average | 78.74% | 73.17% | 53.70% | 134 | 275 |

### Primary comparisons

| New log-odds logistic versus… | Accuracy difference | 95% interval | Macro-F1 difference | Cases corrected | Cases made wrong |
|---|---:|---:|---:|---:|---:|
| Previous probability logistic | +2.13 | +0.83 to +3.37 | +1.29 | 100 | 59 |
| Individual selected with expanded controls | +1.66 | +0.26 to +3.07 | +2.55 | 115 | 83 |
| Previously selected individual | +1.66 | +0.26 to +3.07 | +2.55 | 115 | 83 |
| Previously selected ensemble | +1.09 | +0.21 to +2.03 | +1.85 | 49 | 28 |

Intervals use 2,000 paired duplicate-group bootstrap replicates. They are unadjusted, exclude search/inference uncertainty, and do not turn the reused tests into confirmatory evidence.

### Individual controls selected on validation

| Model | Selected configuration | Accuracy | Macro-F1 | Violation recall |
|---|---|---:|---:|---:|
| policylm | `logit-single/policylm/C0.1` | 71.88% | 62.59% | 35.69% |
| shieldstral | `single/shieldstral/logistic-C0.01` | 79.57% | 75.62% | 63.64% |
| qwen-4b | `logit-single/qwen-4b/C0.01` | 79.16% | 74.03% | 56.23% |

Highest individual accuracy across all registered configurations on this test: **79.57%**. This is a descriptive hurdle, not a test-selected baseline for fitting.

### Every new configuration

| Configuration | Validation accuracy | Threshold | Test accuracy | Macro-F1 | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|---:|
| `logit-single/policylm/C0.01` | 71.42% | 0.42 | 71.47% | 64.57% | 218 | 331 |
| `logit-single/policylm/C0.1` | 71.68% | 0.47 | 71.88% | 62.59% | 159 | 382 |
| `logit-single/policylm/C1` | 71.48% | 0.43 | 71.00% | 64.41% | 233 | 325 |
| `logit-single/policylm/C10` | 71.48% | 0.43 | 71.00% | 64.44% | 234 | 324 |
| `logit-single/policylm/C100` | 71.48% | 0.43 | 71.00% | 64.44% | 234 | 324 |
| `logit-single/shieldstral/C0.01` | 79.30% | 0.43 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C0.1` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C1` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C10` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/shieldstral/C100` | 79.30% | 0.45 | 79.57% | 75.62% | 177 | 216 |
| `logit-single/qwen-4b/C0.01` | 79.82% | 0.51 | 79.16% | 74.03% | 141 | 260 |
| `logit-single/qwen-4b/C0.1` | 79.82% | 0.55 | 79.16% | 74.03% | 141 | 260 |
| `logit-single/qwen-4b/C1` | 79.82% | 0.55 | 79.16% | 74.03% | 141 | 260 |
| `logit-single/qwen-4b/C10` | 79.82% | 0.55 | 79.16% | 74.03% | 141 | 260 |
| `logit-single/qwen-4b/C100` | 79.82% | 0.55 | 79.16% | 74.03% | 141 | 260 |
| `logit-logistic/C0.01` | 80.79% | 0.49 | 80.61% | 76.40% | 148 | 225 |
| `logit-logistic/C0.1` | 81.05% | 0.51 | 80.82% | 76.58% | 143 | 226 |
| `logit-logistic/C1` | 80.86% | 0.52 | 80.35% | 75.83% | 141 | 237 |
| `logit-logistic/C10` | 80.79% | 0.52 | 80.35% | 75.83% | 141 | 237 |
| `logit-logistic/C100` | 80.79% | 0.52 | 80.35% | 75.83% | 141 | 237 |
| `logit-equal` | 79.69% | 0.89 | 78.74% | 73.17% | 134 | 275 |

### The learned equation

Let each input be that model’s reconstructed log-odds. These coefficients absorb the training-only standardization:

| Term | Coefficient |
|---|---:|
| Intercept | -2.119081 |
| policylm | -0.093452 |
| shieldstral | 0.375076 |
| qwen-4b | 0.361003 |

Apply sigmoid to the sum and BLOCK when the result is at least **0.51**. Negative coefficients are permitted. A coefficient is conditional on the other model scores, not a causal measure of the model’s quality.

