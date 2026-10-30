# Full Shieldstral/Qwen representation results

All rows use the same 1,699 test prompts: 754 harmful and 945 benign. Settings and cutoffs were selected on validation before the test pass. The tables preserve protocol order rather than ranking observed test scores.

## Frozen balanced selections

| Method | Representation / candidate | C | Cutoff | Validation balanced accuracy |
|---|---|---:|---:|---:|
| Qwen final-layer probe | qwen-l32-mean | 0.1 | 0.75 | 91.94% |
| Shieldstral final-layer probe | shieldstral-l26-last | 0.01 | 0.42 | 98.86% |
| Combined final-layer probe | qwen-l32-mean + shieldstral-l26-last | 0.1 | 0.35 | 98.90% |
| Qwen layer/pooling search | qwen-l24-last | 0.01 | 0.52 | 96.01% |
| Shieldstral layer/pooling search | shieldstral-l26-last | 0.01 | 0.42 | 98.86% |
| Combined selected representations | qwen-l24-last + shieldstral-l26-last | 0.01 | 0.49 | 99.11% |
| Logistic combination of output scores | qwen-logit + shieldstral-logit | 1.0 | 0.58 | 98.68% |
| Qwen direct B/A score | qwen-native | — | 0.6 | 88.97% |
| Shieldstral direct yes/no score | shieldstral-native | — | 0.34 | 98.73% |
| Equal probability average | score-equal-probability | — | 0.52 | 98.52% |
| Equal log-odds average | score-equal-logodds | — | 0.52 | 98.52% |

## Balanced operating points

| Method | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | MCC | Recall | False-block rate | FP | FN | Unresolved | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen final-layer probe | 83.93% (82.20%–85.57%) | 85.11% | 84.50% | 0.7036 | 73.47% | 5.61% | 53 | 200 | 0 | 0.9226 |
| Shieldstral final-layer probe | 90.39% (88.94%–91.75%) | 90.76% | 90.59% | 0.8127 | 87.14% | 6.35% | 60 | 97 | 0 | 0.9471 |
| Combined final-layer probe | 90.35% (88.86%–91.77%) | 90.70% | 90.53% | 0.8114 | 87.27% | 6.56% | 62 | 96 | 0 | 0.9452 |
| Qwen layer/pooling search | 88.81% (87.25%–90.31%) | 89.41% | 89.15% | 0.7861 | 83.55% | 5.93% | 56 | 124 | 0 | 0.9491 |
| Shieldstral layer/pooling search | 90.39% (88.94%–91.75%) | 90.76% | 90.59% | 0.8127 | 87.14% | 6.35% | 60 | 97 | 0 | 0.9471 |
| Combined selected representations | 90.14% (88.65%–91.50%) | 90.58% | 90.39% | 0.8094 | 86.21% | 5.93% | 56 | 104 | 0 | 0.9404 |
| Logistic combination of output scores | 90.39% (88.91%–91.80%) | 90.76% | 90.59% | 0.8127 | 87.14% | 6.35% | 60 | 97 | 0 | 0.9511 |
| Qwen direct B/A score | 86.00% (84.38%–87.71%) | 86.29% | 86.08% | 0.7217 | 83.42% | 11.43% | 108 | 125 | 0 | 0.9345 |
| Shieldstral direct yes/no score | 90.53% (89.03%–91.89%) | 90.88% | 90.71% | 0.8150 | 87.40% | 6.35% | 60 | 95 | 0 | 0.9485 |
| Equal probability average | 90.41% (88.97%–91.78%) | 90.82% | 90.64% | 0.8140 | 86.74% | 5.93% | 56 | 100 | 0 | 0.9518 |
| Equal log-odds average | 90.35% (88.89%–91.71%) | 90.76% | 90.58% | 0.8128 | 86.74% | 6.03% | 57 | 100 | 0 | 0.9556 |
| Qwen direct score at 0.5 | 86.47% (84.87%–88.12%) | 86.11% | 86.05% | 0.7249 | 89.66% | 16.72% | 158 | 78 | 0 | 0.9345 |
| Shieldstral direct score at 0.5 | 90.30% (88.82%–91.68%) | 90.70% | 90.52% | 0.8116 | 86.74% | 6.14% | 58 | 100 | 0 | 0.9485 |
| Historical WildGuard 7B | 89.81% (88.31%–91.17%) | 90.35% | 90.13% | 0.8051 | 85.01% | 5.40% | 51 | 113 | 0 | — |
| Historical three-specialist score ensemble | 91.08% (89.65%–92.39%) | 91.47% | 91.30% | 0.8272 | 87.67% | 5.50% | 52 | 93 | 0 | — |

Historical rows use earlier validation procedures. Direct scores condition on the canonical label pair; they are not free-generation accuracy. All new rows use this study’s fixed policy and 1,536-row validation population.

## At most 5% false blocks on validation

Each profile selects its own candidate and cutoff. A validation constraint does not guarantee the same constraint on test.

| Method | Candidate | Cutoff | Test false-block rate | Test recall | Constraint held on test? |
|---|---|---:|---:|---:|---|
| Qwen final-layer probe | qwen-l32-mean__C0.1 | 0.75 | 5.61% | 73.47% | No |
| Shieldstral final-layer probe | shieldstral-l26-last__C0.1 | 0.1 | 8.15% | 88.33% | No |
| Combined final-layer probe | qwen-l32-mean+shieldstral-l26-last__C0.01 | 0.07 | 8.04% | 89.12% | No |
| Qwen layer/pooling search | qwen-l24-last__C0.01 | 0.42 | 7.30% | 84.88% | No |
| Shieldstral layer/pooling search | shieldstral-l26-last__C0.1 | 0.1 | 8.15% | 88.33% | No |
| Combined selected representations | qwen-l24-last+shieldstral-l26-last__C0.01 | 0.08 | 8.25% | 88.59% | No |
| Logistic combination of output scores | qwen-logit+shieldstral-logit__C0.01 | 0.28 | 11.01% | 91.11% | No |
| Qwen direct B/A score | qwen-native | 0.74 | 6.03% | 74.27% | No |
| Shieldstral direct yes/no score | shieldstral-native | 0.11 | 8.47% | 89.26% | No |
| Equal probability average | score-equal-probability | 0.43 | 7.83% | 87.67% | No |
| Equal log-odds average | score-equal-logodds | 0.21 | 9.31% | 90.19% | No |

## At least 90% harmful recall on validation

Each profile selects its own candidate and cutoff. A validation constraint does not guarantee the same constraint on test.

| Method | Candidate | Cutoff | Test false-block rate | Test recall | Constraint held on test? |
|---|---|---:|---:|---:|---|
| Qwen final-layer probe | qwen-l32-mean__C0.1 | 0.66 | 5.82% | 74.67% | No |
| Shieldstral final-layer probe | shieldstral-l26-last__C0.1 | 0.97 | 4.44% | 80.64% | No |
| Combined final-layer probe | qwen-l32-mean+shieldstral-l26-last__C0.01 | 0.98 | 4.44% | 79.84% | No |
| Qwen layer/pooling search | qwen-l16-mean__C0.001 | 0.6 | 4.13% | 77.19% | No |
| Shieldstral layer/pooling search | shieldstral-l20-mean__C0.1 | 0.85 | 4.97% | 83.16% | No |
| Combined selected representations | qwen-l24-last+shieldstral-l26-last__C0.001 | 0.93 | 4.66% | 81.83% | No |
| Logistic combination of output scores | qwen-logit+shieldstral-logit__C0.001 | 0.59 | 4.66% | 84.22% | No |
| Qwen direct B/A score | qwen-native | 0.54 | 13.44% | 86.34% | No |
| Shieldstral direct yes/no score | shieldstral-native | 0.9 | 4.44% | 80.24% | No |
| Equal probability average | score-equal-probability | 0.73 | 4.13% | 82.49% | No |
| Equal log-odds average | score-equal-logodds | 0.77 | 4.66% | 83.16% | No |

## Prespecified paired contrasts

Differences are balanced-accuracy percentage points. Intervals use 2,000 paired duplicate-group bootstrap samples and are descriptive, unadjusted for multiple comparisons, search or repeated public-test use.

| Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |
|---|---|---:|---:|---:|---:|
| Combined final-layer probe | Qwen final-layer probe | +6.42 | +4.96 to +7.79 | 121 | 26 |
| Combined final-layer probe | Shieldstral final-layer probe | -0.04 | -0.48 to +0.39 | 6 | 7 |
| Combined final-layer probe | Qwen layer/pooling search | +1.54 | +0.50 to +2.60 | 51 | 29 |
| Combined final-layer probe | Shieldstral layer/pooling search | -0.04 | -0.48 to +0.39 | 6 | 7 |
| Combined final-layer probe | Combined selected representations | +0.21 | -0.36 to +0.83 | 13 | 11 |
| Combined final-layer probe | Logistic combination of output scores | -0.04 | -0.49 to +0.40 | 6 | 7 |
| Combined final-layer probe | Qwen direct B/A score | +4.36 | +2.88 to +5.84 | 117 | 42 |
| Combined final-layer probe | Shieldstral direct yes/no score | -0.17 | -0.66 to +0.29 | 6 | 9 |
| Combined final-layer probe | Equal probability average | -0.05 | -0.62 to +0.49 | 10 | 12 |
| Combined final-layer probe | Equal log-odds average | +0.00 | -0.57 to +0.56 | 11 | 12 |
| Combined final-layer probe | Qwen direct score at 0.5 | +3.89 | +2.35 to +5.34 | 132 | 54 |
| Combined final-layer probe | Shieldstral direct score at 0.5 | +0.05 | -0.45 to +0.56 | 9 | 9 |
| Combined final-layer probe | Historical WildGuard 7B | +0.55 | -0.25 to +1.33 | 25 | 19 |
| Combined final-layer probe | Historical three-specialist score ensemble | -0.73 | -1.66 to +0.22 | 23 | 36 |
| Combined selected representations | Qwen final-layer probe | +6.21 | +4.76 to +7.53 | 116 | 23 |
| Combined selected representations | Shieldstral final-layer probe | -0.25 | -0.86 to +0.32 | 11 | 14 |
| Combined selected representations | Combined final-layer probe | -0.21 | -0.83 to +0.36 | 11 | 13 |
| Combined selected representations | Qwen layer/pooling search | +1.33 | +0.31 to +2.34 | 46 | 26 |
| Combined selected representations | Shieldstral layer/pooling search | -0.25 | -0.86 to +0.32 | 11 | 14 |
| Combined selected representations | Logistic combination of output scores | -0.25 | -0.84 to +0.30 | 10 | 13 |
| Combined selected representations | Qwen direct B/A score | +4.14 | +2.67 to +5.56 | 116 | 43 |
| Combined selected representations | Shieldstral direct yes/no score | -0.39 | -0.98 to +0.20 | 10 | 15 |
| Combined selected representations | Equal probability average | -0.27 | -0.87 to +0.35 | 11 | 15 |
| Combined selected representations | Equal log-odds average | -0.21 | -0.84 to +0.40 | 12 | 15 |
| Combined selected representations | Qwen direct score at 0.5 | +3.67 | +2.08 to +5.16 | 135 | 59 |
| Combined selected representations | Shieldstral direct score at 0.5 | -0.16 | -0.74 to +0.41 | 10 | 12 |
| Combined selected representations | Historical WildGuard 7B | +0.33 | -0.46 to +1.14 | 22 | 18 |
| Combined selected representations | Historical three-specialist score ensemble | -0.94 | -1.89 to -0.05 | 22 | 37 |
| Qwen final-layer probe | Qwen direct B/A score | -2.06 | -3.95 to -0.27 | 110 | 130 |
| Shieldstral final-layer probe | Shieldstral direct yes/no score | -0.13 | -0.44 to +0.16 | 2 | 4 |

The evidence bundle also contains all category/adversarial slices, average precision, Brier scores, log loss, full confusion matrices and feature provenance. `validation.json` retains all candidate probabilities and threshold grids; `fits/` contains coefficients and scalers. Prompts and embeddings remain private.
