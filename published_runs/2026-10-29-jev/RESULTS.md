# Jev 1.14: complete benchmark results

Policies and thresholds were selected on validation before test inference. These are reused public test sets, so comparisons are exploratory. All tasks are binary ALLOW/BLOCK; no REVIEW label was evaluated.

For Jev, `/calibrated` means only that the classification threshold was chosen on validation. Its probabilities were not transformed and no calibration model was fitted. The historical individual controls used learned score calibrators.

## wildguard

Validation-selected policy: **examples**. Thresholds: `{'brief': 0.55, 'examples': 0.6}`.

| Configuration | Accuracy | Macro-F1 | BLOCK recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| brief/default | 89.35% | 89.19% | 87.14% | 84 | 97 |
| detailed/default | 90.05% | 89.87% | 86.34% | 66 | 103 |
| examples/default | 90.17% | 90.01% | 87.27% | 71 | 96 |
| brief/calibrated | 89.35% | 89.16% | 85.94% | 75 | 106 |
| selected/default | 90.17% | 90.01% | 87.27% | 71 | 96 |
| selected/calibrated | 89.94% | 89.71% | 84.62% | 55 | 116 |
| WildGuard-7B | 90.35% | 90.13% | 85.01% | 51 | 113 |
| policylm calibrated | 86.46% | 86.25% | 83.29% | 104 | 126 |
| shieldstral calibrated | 90.76% | 90.60% | 87.40% | 62 | 95 |
| cope calibrated | 90.70% | 90.50% | 85.94% | 52 | 106 |
| Log-odds ensemble (specialists) | 91.29% | 91.14% | 88.46% | 61 | 87 |

### Validation policy comparison

| Policy | Accuracy | Macro-F1 |
|---|---:|---:|
| brief | 91.21% | 91.16% |
| detailed | 91.60% | 91.57% |
| examples | 91.99% | 91.95% |

### Selected/calibrated Jev minus each reference

| Reference | Accuracy difference (points) | 95% paired interval | Cases fixed | Cases broken |
|---|---:|---:|---:|---:|
| brief/default | +0.59 | -0.47 to +1.59 | 47 | 37 |
| WildGuard-7B | -0.41 | -1.65 to +0.88 | 54 | 61 |
| policylm calibrated | +3.47 | +2.00 to +4.94 | 114 | 55 |
| shieldstral calibrated | -0.82 | -2.06 to +0.41 | 48 | 62 |
| cope calibrated | -0.77 | -1.82 to +0.35 | 36 | 49 |
| Log-odds ensemble (specialists) | -1.35 | -2.53 to -0.12 | 44 | 67 |

### Separating wording from thresholds

These additional descriptive intervals were computed after inspecting the initial results. No test-based optimization or extra inference followed.

| Comparison | Accuracy difference (points) | 95% paired interval |
|---|---:|---:|
| policy_at_native_choice | +0.82 | -0.18 to +1.88 |
| threshold_on_selected_policy | -0.24 | -0.94 to +0.47 |
| selected_vs_brief_both_threshold_tuned | +0.59 | -0.47 to +1.59 |

Intervals use 2,000 paired duplicate-group bootstrap draws and are unadjusted. Historical references used different development budgets and sometimes trained calibrators or ensembles; these comparisons do not isolate architecture. Full confusion matrices, calibration metrics, and content slices are in results.json.

## hatexplain

Validation-selected policy: **examples**. Thresholds: `{'brief': 0.96, 'examples': 0.9}`.

| Configuration | Accuracy | Macro-F1 | BLOCK recall | False blocks | Missed violations |
|---|---:|---:|---:|---:|---:|
| brief/default | 69.33% | 68.82% | 91.41% | 539 | 51 |
| detailed/default | 72.77% | 71.77% | 87.37% | 449 | 75 |
| examples/default | 75.16% | 73.82% | 85.19% | 390 | 88 |
| brief/calibrated | 79.47% | 75.87% | 66.16% | 194 | 201 |
| selected/default | 75.16% | 73.82% | 85.19% | 390 | 88 |
| selected/calibrated | 80.67% | 76.11% | 59.93% | 134 | 238 |
| policylm calibrated | 71.88% | 62.59% | 35.69% | 159 | 382 |
| shieldstral calibrated | 79.57% | 75.62% | 63.64% | 177 | 216 |
| Log-odds ensemble (specialists) | 78.79% | 72.26% | 48.99% | 105 | 303 |
| qwen-4b calibrated | 79.16% | 74.03% | 56.23% | 141 | 260 |
| Log-odds ensemble (specialists + Qwen) | 80.82% | 76.58% | 61.95% | 143 | 226 |

### Validation policy comparison

| Policy | Accuracy | Macro-F1 |
|---|---:|---:|
| brief | 70.73% | 70.19% |
| detailed | 74.06% | 73.11% |
| examples | 76.77% | 75.51% |

### Selected/calibrated Jev minus each reference

| Reference | Accuracy difference (points) | 95% paired interval | Cases fixed | Cases broken |
|---|---:|---:|---:|---:|
| brief/default | +11.33 | +8.98 to +13.84 | 405 | 187 |
| policylm calibrated | +8.78 | +6.76 to +10.79 | 299 | 130 |
| shieldstral calibrated | +1.09 | -0.78 to +2.96 | 169 | 148 |
| Log-odds ensemble (specialists) | +1.87 | +0.10 to +3.69 | 166 | 130 |
| qwen-4b calibrated | +1.51 | -0.36 to +3.28 | 165 | 136 |
| Log-odds ensemble (specialists + Qwen) | -0.16 | -1.82 to +1.56 | 132 | 135 |

### Separating wording from thresholds

These additional descriptive intervals were computed after inspecting the initial results. No test-based optimization or extra inference followed.

| Comparison | Accuracy difference (points) | 95% paired interval |
|---|---:|---:|
| policy_at_native_choice | +5.82 | +4.41 to +7.28 |
| threshold_on_selected_policy | +5.51 | +3.48 to +7.54 |
| selected_vs_brief_both_threshold_tuned | +1.20 | +0.10 to +2.29 |

Intervals use 2,000 paired duplicate-group bootstrap draws and are unadjusted. Historical references used different development budgets and sometimes trained calibrators or ensembles; these comparisons do not isolate architecture. Full confusion matrices, calibration metrics, and content slices are in results.json.

## Usage

8,103 benchmark requests; 22,261 classifications; one separate synthetic connectivity request. Actual API charge: **$0.424208**, within the $2.00 ceiling. No GPU rental.

Median request latency 0.323s; p95 0.552s. Client-observed requests with two or three independent policy questions, concurrency up to eight; not a matched serving benchmark.
