# Can complementary models reduce moderation errors?

A predeclared, training-selected logistic ensemble across specialist, general-purpose and decision models. The backbone weights and policies stayed fixed. Official public tests were reused; Jev test calls were refreshed after the ensemble freeze. These are exploratory results.

## wildguard

1,699 test examples: 754 BLOCK and 945 ALLOW. Fitting: 4,096; validation: 1,536.

Training selection retained **shieldstral**. The final validation cutoff was 0.49. Test balanced accuracy: **90.53%**, with **60 false blocks and 95 misses**.

### Registered comparisons

| Method | Components | Balanced accuracy | Accuracy | False blocks | Misses |
|---|---|---:|---:|---:|---:|
| primary | shieldstral | 90.53% | 90.88% | 60 | 95 |
| open-only | shieldstral | 90.53% | 90.88% | 60 | 95 |
| specialist-only | shieldstral | 90.53% | 90.88% | 60 | 95 |
| decision-only | jev, kev | 89.68% | 90.11% | 61 | 107 |
| all-logistic | clef, cope, jev, kev, policylm, qwen-4b, shieldstral | 90.43% | 90.76% | 63 | 94 |
| single/policylm/calibrated | policylm | 86.02% | 86.64% | 80 | 147 |
| single/policylm/raw | policylm | 86.02% | 86.64% | 80 | 147 |
| single/shieldstral/calibrated | shieldstral | 90.53% | 90.88% | 60 | 95 |
| single/shieldstral/raw | shieldstral | 90.53% | 90.88% | 60 | 95 |
| single/cope/calibrated | cope | 90.22% | 90.70% | 52 | 106 |
| single/cope/raw | cope | 90.22% | 90.70% | 52 | 106 |
| single/qwen-4b/calibrated | qwen-4b | 86.00% | 86.29% | 108 | 125 |
| single/qwen-4b/raw | qwen-4b | 86.00% | 86.29% | 108 | 125 |
| single/jev/calibrated | jev | 88.92% | 89.52% | 54 | 124 |
| single/jev/raw | jev | 88.83% | 89.41% | 57 | 123 |
| single/kev/calibrated | kev | 86.89% | 87.64% | 61 | 149 |
| single/kev/raw | kev | 86.89% | 87.64% | 61 | 149 |
| single/clef/calibrated | clef | 87.45% | 87.88% | 83 | 123 |
| single/clef/raw | clef | 87.45% | 87.88% | 83 | 123 |
| equal-probability | policylm, shieldstral, cope, qwen-4b, jev, kev, clef | 90.72% | 91.11% | 55 | 96 |
| equal-logodds | policylm, shieldstral, cope, qwen-4b, jev, kev, clef | 90.91% | 91.29% | 54 | 94 |
| specialist-equal-logodds | policylm, shieldstral, cope | 90.79% | 90.94% | 75 | 79 |
| nonlinear | policylm, shieldstral, cope, qwen-4b, jev, kev, clef | 90.46% | 90.82% | 60 | 96 |
| best-individual | shieldstral | 90.53% | 90.88% | 60 | 95 |

### Primary paired differences

Positive differences favor the selected mixed ensemble. These intervals are unadjusted and conditional on saved outputs.

| Primary versus | Balanced-accuracy change, points (95% interval) | Errors corrected | New errors | False blocks change | Misses change |
|---|---:|---:|---:|---:|---:|
| open-only | +0.00 (+0.00, +0.00) | 0 | 0 | +0 | +0 |
| specialist-only | +0.00 (+0.00, +0.00) | 0 | 0 | +0 | +0 |
| decision-only | +0.85 (-0.32, +2.07) | 57 | 44 | -1 | -12 |
| all-logistic | +0.09 (-0.20, +0.38) | 4 | 2 | -3 | +1 |
| single/policylm/calibrated | +4.51 (+3.18, +5.89) | 102 | 30 | -20 | -52 |
| single/policylm/raw | +4.51 (+3.18, +5.89) | 102 | 30 | -20 | -52 |
| single/shieldstral/calibrated | +0.00 (+0.00, +0.00) | 0 | 0 | +0 | +0 |
| single/shieldstral/raw | +0.00 (+0.00, +0.00) | 0 | 0 | +0 | +0 |
| single/cope/calibrated | +0.31 (-0.70, +1.36) | 40 | 37 | +8 | -11 |
| single/cope/raw | +0.31 (-0.70, +1.36) | 40 | 37 | +8 | -11 |
| single/qwen-4b/calibrated | +4.53 (+3.08, +6.00) | 118 | 40 | -48 | -30 |
| single/qwen-4b/raw | +4.53 (+3.08, +6.00) | 118 | 40 | -48 | -30 |
| single/jev/calibrated | +1.61 (+0.35, +2.86) | 66 | 43 | +6 | -29 |
| single/jev/raw | +1.70 (+0.41, +2.94) | 67 | 42 | +3 | -28 |
| single/kev/calibrated | +3.63 (+2.12, +5.14) | 108 | 53 | -1 | -54 |
| single/kev/raw | +3.63 (+2.12, +5.14) | 108 | 53 | -1 | -54 |
| single/clef/calibrated | +3.07 (+1.62, +4.52) | 102 | 51 | -23 | -28 |
| single/clef/raw | +3.07 (+1.62, +4.52) | 102 | 51 | -23 | -28 |
| equal-probability | -0.20 (-1.01, +0.59) | 22 | 26 | +5 | -1 |
| equal-logodds | -0.38 (-1.18, +0.44) | 21 | 28 | +6 | +1 |
| specialist-equal-logodds | -0.27 (-1.08, +0.54) | 25 | 26 | -15 | +16 |
| nonlinear | +0.07 (+0.00, +0.21) | 1 | 0 | +0 | -1 |
| best-individual | +0.00 (+0.00, +0.00) | 0 | 0 | +0 | +0 |

### Learned equation

For each listed component, clip its BLOCK score to [0.000001, 0.999999] and compute log(score / (1-score)). The final score is sigmoid(intercept + the weighted sum of those log-odds). These coefficients are conditional on the other correlated model scores; they are not percentages or causal importance.

Intercept: `0.233144077`.

| Component | Log-odds coefficient |
|---|---:|
| shieldstral | 0.374156672 |

### Training selection path

| Step | Candidate components | OOF balanced accuracy | Accepted? |
|---:|---|---:|---|
| 1 | shieldstral | 98.67% | Yes |
| 2 | clef, shieldstral | 98.67% | No: gain below 0.2 points |

The OOF values were used to search subsets and regularization; they are not independent final accuracy estimates. Full rejected candidates, error overlaps, folds, parameters and component ablations are preserved in fitting.json.

### Operating targets

| Primary selection profile | Validation target met | Test target met | False-block rate | Miss rate |
|---|---|---|---:|---:|
| false_block_limit | Yes | No | 8.47% | 10.74% |
| catch_target | Yes | No | 4.66% | 19.10% |

## hatexplain

1,924 test examples: 594 BLOCK and 1,330 ALLOW. Fitting: 4,096; validation: 1,536.

Training selection retained **jev, kev, shieldstral**. The final validation cutoff was 0.48. Test balanced accuracy: **79.97%**, with **282 false blocks and 112 misses**.

### Registered comparisons

| Method | Components | Balanced accuracy | Accuracy | False blocks | Misses |
|---|---|---:|---:|---:|---:|
| primary | jev, kev, shieldstral | 79.97% | 79.52% | 282 | 112 |
| open-only | kev, qwen-4b, shieldstral | 78.69% | 79.11% | 269 | 133 |
| specialist-only | policylm, shieldstral | 76.95% | 78.43% | 255 | 160 |
| decision-only | jev | 78.35% | 77.03% | 334 | 108 |
| all-logistic | clef, jev, kev, policylm, qwen-4b, shieldstral | 81.03% | 81.24% | 245 | 116 |
| single/policylm/calibrated | policylm | 64.05% | 65.18% | 439 | 231 |
| single/policylm/raw | policylm | 64.05% | 65.18% | 439 | 231 |
| single/shieldstral/calibrated | shieldstral | 77.44% | 77.70% | 291 | 138 |
| single/shieldstral/raw | shieldstral | 77.44% | 77.70% | 291 | 138 |
| single/qwen-4b/calibrated | qwen-4b | 75.87% | 77.13% | 277 | 163 |
| single/qwen-4b/raw | qwen-4b | 75.87% | 77.13% | 277 | 163 |
| single/jev/calibrated | jev | 78.35% | 77.03% | 334 | 108 |
| single/jev/raw | jev | 78.42% | 76.09% | 368 | 92 |
| single/kev/calibrated | kev | 75.13% | 74.64% | 348 | 140 |
| single/kev/raw | kev | 75.17% | 74.69% | 347 | 140 |
| single/clef/calibrated | clef | 75.06% | 76.40% | 285 | 169 |
| single/clef/raw | clef | 74.82% | 76.72% | 269 | 179 |
| equal-probability | policylm, shieldstral, qwen-4b, jev, kev, clef | 78.00% | 76.92% | 330 | 114 |
| equal-logodds | policylm, shieldstral, qwen-4b, jev, kev, clef | 77.83% | 76.82% | 330 | 116 |
| specialist-equal-logodds | policylm, shieldstral | 72.38% | 70.89% | 419 | 141 |
| nonlinear | policylm, shieldstral, qwen-4b, jev, kev, clef | 81.08% | 79.83% | 295 | 93 |
| without/jev | kev, shieldstral | 77.76% | 78.01% | 287 | 136 |
| without/kev | jev, shieldstral | 79.81% | 79.11% | 293 | 109 |
| without/shieldstral | jev, kev | 79.03% | 78.48% | 298 | 116 |
| best-individual | jev | 78.42% | 76.09% | 368 | 92 |

### Primary paired differences

Positive differences favor the selected mixed ensemble. These intervals are unadjusted and conditional on saved outputs.

| Primary versus | Balanced-accuracy change, points (95% interval) | Errors corrected | New errors | False blocks change | Misses change |
|---|---:|---:|---:|---:|---:|
| open-only | +1.28 (-0.10, +2.67) | 78 | 70 | +13 | -21 |
| specialist-only | +3.03 (+1.52, +4.51) | 100 | 79 | +27 | -48 |
| decision-only | +1.62 (+0.05, +3.21) | 128 | 80 | -52 | +4 |
| all-logistic | -1.05 (-2.22, +0.19) | 42 | 75 | +37 | -4 |
| single/policylm/calibrated | +15.92 (+13.59, +18.34) | 384 | 108 | -157 | -119 |
| single/policylm/raw | +15.92 (+13.59, +18.34) | 384 | 108 | -157 | -119 |
| single/shieldstral/calibrated | +2.53 (+1.07, +3.91) | 98 | 63 | -9 | -26 |
| single/shieldstral/raw | +2.53 (+1.07, +3.91) | 98 | 63 | -9 | -26 |
| single/qwen-4b/calibrated | +4.10 (+2.31, +6.02) | 161 | 115 | +5 | -51 |
| single/qwen-4b/raw | +4.10 (+2.31, +6.02) | 161 | 115 | +5 | -51 |
| single/jev/calibrated | +1.62 (+0.05, +3.21) | 128 | 80 | -52 | +4 |
| single/jev/raw | +1.55 (-0.04, +3.14) | 144 | 78 | -86 | +20 |
| single/kev/calibrated | +4.84 (+3.20, +6.49) | 179 | 85 | -66 | -28 |
| single/kev/raw | +4.80 (+3.16, +6.47) | 179 | 86 | -65 | -28 |
| single/clef/calibrated | +4.91 (+3.13, +6.72) | 160 | 100 | -3 | -57 |
| single/clef/raw | +5.15 (+3.31, +7.02) | 160 | 106 | +13 | -67 |
| equal-probability | +1.97 (+0.72, +3.29) | 97 | 47 | -48 | -2 |
| equal-logodds | +2.14 (+1.00, +3.29) | 89 | 37 | -48 | -4 |
| specialist-equal-logodds | +7.59 (+5.75, +9.36) | 227 | 61 | -137 | -29 |
| nonlinear | -1.11 (-2.26, -0.00) | 52 | 58 | -13 | +19 |
| without/jev | +2.21 (+1.01, +3.43) | 73 | 44 | -5 | -24 |
| without/kev | +0.16 (-0.26, +0.56) | 13 | 5 | -11 | +3 |
| without/shieldstral | +0.94 (-0.48, +2.36) | 98 | 78 | -16 | -4 |
| best-individual | +1.55 (-0.04, +3.14) | 144 | 78 | -86 | +20 |

### Learned equation

For each listed component, clip its BLOCK score to [0.000001, 0.999999] and compute log(score / (1-score)). The final score is sigmoid(intercept + the weighted sum of those log-odds). These coefficients are conditional on the other correlated model scores; they are not percentages or causal importance.

Intercept: `-1.14154946`.

| Component | Log-odds coefficient |
|---|---:|
| jev | 0.203900869 |
| kev | 0.045705784 |
| shieldstral | 0.298909095 |

### Training selection path

| Step | Candidate components | OOF balanced accuracy | Accepted? |
|---:|---|---:|---|
| 1 | jev | 79.42% | Yes |
| 2 | jev, shieldstral | 79.75% | Yes |
| 3 | jev, kev, shieldstral | 79.99% | Yes |
| 4 | clef, jev, kev, shieldstral | 80.06% | No: gain below 0.2 points |

The OOF values were used to search subsets and regularization; they are not independent final accuracy estimates. Full rejected candidates, error overlaps, folds, parameters and component ablations are preserved in fitting.json.

### Operating targets

| Primary selection profile | Validation target met | Test target met | False-block rate | Miss rate |
|---|---|---|---:|---:|
| false_block_limit | Yes | Yes | 4.06% | 64.31% |
| catch_target | Yes | Yes | 37.82% | 8.75% |

## Limits

This is a bounded configured-system comparison, not an architecture or training-data causal study. Different families are not guaranteed to make complementary errors. Scores are not interchangeable calibrated probabilities. The same public tests and development histories have informed earlier research; no fresh independently labeled test was created. WildGuardTrain model-derived labels differ from the human-labeled test. Jev canary scores varied even for identical requests, so all new Jev development and test outputs were collected in this study; intervals do not capture API variability. No policy optimization, new representation head, second-pass routing, or backbone fine-tuning was performed.
