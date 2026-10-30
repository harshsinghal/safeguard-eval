# WildGuard decision-score ensemble results

Exploratory October 30, 2026 follow-up using saved native BLOCK probabilities. All new fitting used 1,024 training prompts; policy, hyperparameter and cutoff selection used 512 separate validation prompts. The 1,699 test prompts were held out of those operations but had been examined in earlier studies.

## Frozen input policies

| Model | Selected policy | Raw validation balanced accuracy |
|---|---|---:|
| jev | detailed | 93.42% |
| kev | brief | 92.06% |
| clef | detailed | 90.93% |

Brief and detailed were the eligible policy pool. Example-bearing policies lack saved fitting scores and were excluded from new ensemble inputs. Their earlier selected individual results remain historical references below.

## Jev + Kev + Clef

Methods appear in registered order, not in a ranking selected from test results. 'Best' refers to validation selection.

| Method | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | Catch rate | False-block rate | False blocks / missed | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Probability logistic — primary | 89.32% (87.76%–90.77%) | 89.70% | 89.51% | 85.94% | 7.30% | 69 / 106 | 0 |
| Log-odds logistic | 89.11% (87.56%–90.54%) | 89.23% | 89.10% | 88.06% | 9.84% | 93 / 90 | 0 |
| Equal probability average | 89.45% (87.86%–90.90%) | 89.82% | 89.63% | 86.21% | 7.30% | 69 / 104 | 0 |
| Equal calibrated average | 88.76% (87.21%–90.27%) | 89.11% | 88.92% | 85.68% | 8.15% | 77 / 108 | 0 |
| Equal log-odds average | 89.74% (88.20%–91.17%) | 90.11% | 89.93% | 86.47% | 6.98% | 66 / 102 | 0 |
| Learned weighted average | 89.08% (87.56%–90.52%) | 89.41% | 89.23% | 86.21% | 8.04% | 76 / 104 | 0 |
| Random forest | 89.14% (87.58%–90.64%) | 89.46% | 89.28% | 86.21% | 7.94% | 75 / 104 | 0 |
| Decision-only logistic | 89.05% (87.55%–90.57%) | 89.82% | 89.52% | 82.23% | 4.13% | 39 / 134 | 0 |
| Fixed majority vote | 88.71% (87.17%–90.24%) | 89.35% | 89.08% | 83.02% | 5.61% | 53 / 128 | 0 |
| Validation-selected best individual | 88.69% (87.17%–90.20%) | 89.41% | 89.12% | 82.36% | 4.97% | 47 / 133 | 0 |
| Jev: selected individual | 88.69% (87.17%–90.20%) | 89.41% | 89.12% | 82.36% | 4.97% | 47 / 133 | 0 |
| Kev: selected individual | 86.91% (85.19%–88.53%) | 87.52% | 87.23% | 81.43% | 7.62% | 72 / 140 | 0 |
| Clef: selected individual | 86.91% (85.24%–88.47%) | 87.40% | 87.15% | 82.49% | 8.68% | 82 / 132 | 0 |
| Validation-selected best score ensemble | 89.08% (87.56%–90.52%) | 89.41% | 89.23% | 86.21% | 8.04% | 76 / 104 | 0 |

### Selected settings

| Method | Candidate | BLOCK cutoff | Validation balanced accuracy |
|---|---|---:|---:|
| Probability logistic — primary | `probability-logistic/C10` | 0.56 | 94.43% |
| Log-odds logistic | `logodds-logistic/C100` | 0.41 | 93.85% |
| Equal probability average | `equal-probability` | 0.46 | 94.22% |
| Equal calibrated average | `equal-calibrated` | 0.49 | 94.38% |
| Equal log-odds average | `equal-logodds` | 0.45 | 94.22% |
| Learned weighted average | `weighted/lambda0.1` | native / fixed | 94.80% |
| Random forest | `forest/depth4-leaf20` | 0.49 | 94.77% |
| Decision-only logistic | `decision-logistic/C0.01` | 0.67 | 91.85% |
| Fixed majority vote | `majority` | native / fixed | 91.74% |
| Validation-selected best individual | `single/jev/logodds/C0.01` | 0.55 | 93.42% |
| Jev: selected individual | `single/jev/logodds/C0.01` | 0.55 | 93.42% |
| Kev: selected individual | `single/kev/logodds/C1` | 0.62 | 92.24% |
| Clef: selected individual | `single/clef/probability/C1` | native / fixed | 91.14% |
| Validation-selected best score ensemble | `weighted/lambda0.1` | native / fixed | 94.80% |

### Primary score equation

```text
ensemble_score = sigmoid(-5.963441 +4.049201 × p_jev +4.567234 × p_kev +4.987910 × p_clef)
```

Here p_model is the saved native BLOCK probability under that model's selected policy. Coefficients include the fitting-only standardization in the equation above. They are fitted coefficients, not causal importance scores. The score is not assumed to be a calibrated probability for production traffic.

## Open weights only: Kev + Clef

Methods appear in registered order, not in a ranking selected from test results. 'Best' refers to validation selection.

| Method | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | Catch rate | False-block rate | False blocks / missed | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Probability logistic — primary | 87.52% (85.84%–89.05%) | 88.17% | 87.87% | 81.70% | 6.67% | 63 / 138 | 0 |
| Log-odds logistic | 87.50% (85.83%–89.04%) | 88.17% | 87.87% | 81.56% | 6.56% | 62 / 139 | 0 |
| Equal probability average | 87.60% (85.95%–89.20%) | 87.99% | 87.77% | 84.08% | 8.89% | 84 / 120 | 0 |
| Equal calibrated average | 87.72% (86.09%–89.31%) | 88.23% | 87.98% | 83.16% | 7.72% | 73 / 127 | 0 |
| Equal log-odds average | 87.64% (86.02%–89.21%) | 88.05% | 87.83% | 83.95% | 8.68% | 82 / 121 | 0 |
| Learned weighted average | 87.88% (86.25%–89.40%) | 88.05% | 87.89% | 86.34% | 10.58% | 100 / 103 | 0 |
| Random forest | 88.10% (86.47%–89.59%) | 88.23% | 88.08% | 87.00% | 10.79% | 102 / 98 | 0 |
| Decision-only logistic | 88.02% (86.41%–89.56%) | 88.17% | 88.02% | 86.74% | 10.69% | 101 / 100 | 0 |
| Fixed majority vote | 88.02% (86.41%–89.56%) | 88.17% | 88.02% | 86.74% | 10.69% | 101 / 100 | 0 |
| Validation-selected best individual | 86.91% (85.19%–88.53%) | 87.52% | 87.23% | 81.43% | 7.62% | 72 / 140 | 0 |
| Kev: selected individual | 86.91% (85.19%–88.53%) | 87.52% | 87.23% | 81.43% | 7.62% | 72 / 140 | 0 |
| Clef: selected individual | 86.91% (85.24%–88.47%) | 87.40% | 87.15% | 82.49% | 8.68% | 82 / 132 | 0 |
| Validation-selected best score ensemble | 88.10% (86.47%–89.59%) | 88.23% | 88.08% | 87.00% | 10.79% | 102 / 98 | 0 |

### Selected settings

| Method | Candidate | BLOCK cutoff | Validation balanced accuracy |
|---|---|---:|---:|
| Probability logistic — primary | `probability-logistic/C0.1` | 0.63 | 92.76% |
| Log-odds logistic | `logodds-logistic/C10` | 0.68 | 92.76% |
| Equal probability average | `equal-probability` | 0.44 | 92.78% |
| Equal calibrated average | `equal-calibrated` | 0.53 | 92.44% |
| Equal log-odds average | `equal-logodds` | 0.44 | 92.60% |
| Learned weighted average | `weighted/lambda0.1` | 0.42 | 92.49% |
| Random forest | `forest/depth4-leaf80` | 0.47 | 92.85% |
| Decision-only logistic | `decision-logistic/C0.01` | native / fixed | 90.99% |
| Fixed majority vote | `majority` | native / fixed | 90.99% |
| Validation-selected best individual | `single/kev/logodds/C1` | 0.62 | 92.24% |
| Kev: selected individual | `single/kev/logodds/C1` | 0.62 | 92.24% |
| Clef: selected individual | `single/clef/probability/C1` | native / fixed | 91.14% |
| Validation-selected best score ensemble | `forest/depth4-leaf80` | 0.47 | 92.85% |

### Primary score equation

```text
ensemble_score = sigmoid(-5.108810 +4.964985 × p_kev +6.977456 × p_clef)
```

Here p_model is the saved native BLOCK probability under that model's selected policy. Coefficients include the fitting-only standardization in the equation above. They are fitted coefficients, not causal importance scores. The score is not assumed to be a calibrated probability for production traffic.

## Historical references

These retain their earlier balanced-validation selections, which used different policy pools and fitting histories. None is an input to the new ensemble unless it is one of the explicitly named decision-model components above.

| Reference | Balanced accuracy | Accuracy | False blocks / missed |
|---|---:|---:|---:|
| Jev 1.14 | 88.69% | 89.41% | 47 / 133 |
| Kev 4B | 86.93% | 87.58% | 69 / 142 |
| Clef-Flash 9B | 87.62% | 87.99% | 86 / 118 |
| WildGuard 7B | 89.81% | 90.35% | 51 / 113 |
| CoPE | 90.58% | 90.99% | 54 / 99 |
| Qwen3.5 27B | 90.16% | 90.82% | 38 / 118 |
| Equal log-odds average · specialists | 91.08% | 91.47% | 52 / 93 |

## Registered paired comparisons

Differences below are balanced-accuracy percentage points, A minus B. The 2,000-draw group-bootstrap intervals are descriptive and unadjusted. An interval spanning zero does not resolve a clear difference.

| A | B | Difference | 95% interval | Cases fixed / broken |
|---|---|---:|---:|---:|
| `all-three/probability-logistic/balanced` | `all-three/single/balanced` | +0.63 | -0.43 to +1.58 | 39 / 34 |
| `all-three/probability-logistic/balanced` | `reference/wildguard` | -0.49 | -1.73 to +0.73 | 51 / 62 |
| `all-three/probability-logistic/balanced` | `all-three/decision-logistic/balanced` | +0.27 | -0.67 to +1.19 | 32 / 34 |
| `all-three/probability-logistic/balanced` | `all-three/majority/balanced` | +0.61 | -0.26 to +1.47 | 29 / 23 |
| `open-only/probability-logistic/balanced` | `open-only/single/balanced` | +0.61 | -0.44 to +1.65 | 45 / 34 |
| `open-only/probability-logistic/balanced` | `all-three/probability-logistic/balanced` | -1.80 | -2.83 to -0.81 | 24 / 50 |
| `all-three/best-score-ensemble/balanced` | `all-three/single/balanced` | +0.39 | -0.67 to +1.44 | 41 / 41 |
| `all-three/probability-logistic/balanced` | `reference/jev` | +0.63 | -0.43 to +1.58 | 39 / 34 |
| `all-three/probability-logistic/balanced` | `reference/kev` | +2.39 | +1.19 to +3.59 | 68 / 32 |
| `all-three/probability-logistic/balanced` | `reference/clef` | +1.70 | +0.52 to +2.84 | 63 / 34 |
| `all-three/probability-logistic/balanced` | `reference/cope` | -1.26 | -2.47 to -0.09 | 36 / 58 |
| `all-three/probability-logistic/balanced` | `reference/qwen-27b` | -0.84 | -1.95 to +0.22 | 33 / 52 |
| `all-three/probability-logistic/balanced` | `reference/wildguard-specialists/logit-equal` | -1.76 | -2.94 to -0.69 | 29 / 59 |

## Separately selected operational targets

These use their own validation-selected settings, not the balanced cutoff. A validation target is not a test guarantee.

| Cohort / method | Target | Catch rate | False-block rate | Test target met? |
|---|---|---:|---:|---|
| all-three / probability-logistic | false_block_limit | 86.34% | 7.51% | No |
| all-three / probability-logistic | catch_target | 83.42% | 6.35% | No |
| all-three / single | false_block_limit | 83.16% | 5.29% | No |
| all-three / single | catch_target | 83.16% | 5.29% | No |
| all-three / best-score-ensemble | false_block_limit | 86.21% | 7.94% | No |
| all-three / best-score-ensemble | catch_target | 83.42% | 5.61% | No |
| open-only / probability-logistic | false_block_limit | 81.70% | 6.67% | No |
| open-only / probability-logistic | catch_target | 81.70% | 6.67% | No |
| open-only / single | false_block_limit | 81.43% | 7.62% | No |
| open-only / single | catch_target | 82.23% | 8.15% | No |
| open-only / best-score-ensemble | false_block_limit | 81.70% | 6.67% | No |
| open-only / best-score-ensemble | catch_target | 81.70% | 6.67% | No |

## Evidence and limitations

See `results.json` for all metrics, calibration diagnostics, category slices and paired comparisons; `parameters.json` for all fitted coefficients and averaging weights; `validation-grid.json.gz` for the full search; and `test-predictions.json.gz` for scores and frozen decisions. `PLAN.md`, `registration.json`, and `freeze.json` record the procedure and hashes.

The selected component policies, score scales, clipping convention, validation objective and cohort all affect this comparison. Previously examined tests, repeated validation use, machine-versus-human annotation differences, incomplete upstream training disclosure and limited candidate pools prevent treating this as a performance ceiling or architecture verdict. Ensembles require two or three model evaluations per input; saved-score replay does not measure live serving latency or cost.

Added GPU/API cost: $0. Small calibrators and combiners were trained on labels; no language-model weights were updated.
