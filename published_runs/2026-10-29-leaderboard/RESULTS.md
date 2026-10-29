# Balanced moderation leaderboard

Retrospective reanalysis of saved outputs. Choices were selected on the common validation set, then frozen before this analysis scored the already-observed official tests. No new inference or fitting. The tables rank configured systems, not architectures in isolation.

## wildguard: 1,699 test examples

754 BLOCK; 945 ALLOW. Balanced accuracy gives both classes equal weight.

### Balance both classes

| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Equal log-odds average · specialists | 91.08% (89.65%–92.39%) | 91.30% | 0.827 | 87.67% | 5.50% | 52 / 93 | 91.47% | — |
| Logistic regression · log-odds · specialists | 91.00% (89.57%–92.35%) | 91.14% | 0.823 | 88.46% | 6.46% | 61 / 87 | 91.29% | — |
| Logistic regression · probabilities · specialists | 90.98% (89.52%–92.34%) | 91.09% | 0.822 | 88.73% | 6.77% | 64 / 85 | 91.23% | — |
| Calibrated probability average · specialists | 90.62% (89.20%–91.96%) | 90.92% | 0.821 | 86.21% | 4.97% | 47 / 104 | 91.11% | — |
| Random forest · specialists | 90.58% (89.08%–91.93%) | 90.77% | 0.816 | 87.40% | 6.24% | 59 / 95 | 90.94% | — |
| CoPE | 90.58% (89.12%–91.88%) | 90.82% | 0.818 | 86.87% | 5.71% | 54 / 99 | 90.99% | — |
| Equal probability average · specialists | 90.58% (89.14%–91.92%) | 90.86% | 0.819 | 86.34% | 5.19% | 49 / 103 | 91.05% | — |
| Learned weighted average · specialists | 90.53% (89.03%–91.89%) | 90.71% | 0.815 | 87.40% | 6.35% | 60 / 95 | 90.88% | — |
| Shieldstral 3B | 90.26% (88.81%–91.60%) | 90.56% | 0.813 | 85.81% | 5.29% | 50 / 107 | 90.76% | — |
| Qwen3.5 27B | 90.16% (88.64%–91.60%) | 90.58% | 0.816 | 84.35% | 4.02% | 38 / 118 | 90.82% | — |
| WildGuard 7B | 89.81% (88.31%–91.17%) | 90.13% | 0.805 | 85.01% | 5.40% | 51 / 113 | 90.35% | — |
| Qwen3.5 35B-A3B | 89.64% (88.11%–91.04%) | 89.99% | 0.803 | 84.35% | 5.08% | 48 / 118 | 90.23% | — |
| Qwen3.5 9B | 89.32% (87.82%–90.77%) | 89.42% | 0.789 | 87.00% | 8.36% | 79 / 98 | 89.58% | — |
| GPT-OSS Safeguard 20B | 89.13% (87.63%–90.57%) | 89.64% | — | 84.62% | 6.14% | 58 / 109 | 89.64% | — |
| Jev 1.14 | 88.69% (87.17%–90.20%) | 89.12% | 0.787 | 82.36% | 4.97% | 47 / 133 | 89.41% | — |
| Qwen3.5 4B | 86.81% (85.19%–88.41%) | 86.64% | 0.733 | 87.27% | 13.65% | 129 / 96 | 86.76% | — |
| PolicyLM 1.7B | 86.31% (84.66%–87.86%) | 86.38% | 0.728 | 83.95% | 11.32% | 107 / 121 | 86.58% | — |
| Qwen3.5 2B | 83.41% (81.67%–85.19%) | 83.42% | 0.668 | 81.43% | 14.60% | 138 / 140 | 83.64% | — |

### False-block limit: 5%

| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Shieldstral 3B | 90.58% (89.19%–91.94%) | 90.53% | 0.811 | 90.05% | 8.89% | 84 / 75 | 90.64% | No |
| Calibrated probability average · specialists | 90.53% (89.07%–91.90%) | 90.57% | 0.811 | 88.99% | 7.94% | 75 / 83 | 90.70% | No |
| Random forest · specialists | 91.04% (89.56%–92.39%) | 91.15% | 0.823 | 88.86% | 6.77% | 64 / 84 | 91.29% | No |
| Logistic regression · probabilities · specialists | 90.98% (89.52%–92.34%) | 91.09% | 0.822 | 88.73% | 6.77% | 64 / 85 | 91.23% | No |
| Logistic regression · log-odds · specialists | 90.98% (89.52%–92.33%) | 91.09% | 0.822 | 88.73% | 6.77% | 64 / 85 | 91.23% | No |
| Equal probability average · specialists | 90.96% (89.55%–92.28%) | 91.09% | 0.822 | 88.59% | 6.67% | 63 / 86 | 91.23% | No |
| Equal log-odds average · specialists | 91.20% (89.80%–92.48%) | 91.38% | 0.828 | 88.33% | 5.93% | 56 / 88 | 91.52% | No |
| Learned weighted average · specialists | 90.38% (88.91%–91.77%) | 90.49% | 0.810 | 88.06% | 7.30% | 69 / 90 | 90.64% | No |
| Qwen3.5 27B | 90.95% (89.52%–92.30%) | 91.18% | 0.825 | 87.40% | 5.50% | 52 / 95 | 91.35% | No |
| CoPE | 90.58% (89.12%–91.88%) | 90.82% | 0.818 | 86.87% | 5.71% | 54 / 99 | 90.99% | No |
| Qwen3.5 9B | 89.00% (87.48%–90.46%) | 89.12% | 0.783 | 86.47% | 8.47% | 80 / 102 | 89.29% | No |
| Qwen3.5 35B-A3B | 89.76% (88.28%–91.19%) | 90.03% | 0.802 | 85.54% | 6.03% | 57 / 109 | 90.23% | No |
| WildGuard 7B | 89.81% (88.31%–91.17%) | 90.13% | 0.805 | 85.01% | 5.40% | 51 / 113 | 90.35% | No |
| Jev 1.14 | 88.93% (87.43%–90.46%) | 89.32% | 0.790 | 83.16% | 5.29% | 50 / 127 | 89.58% | No |
| PolicyLM 1.7B | 84.77% (83.02%–86.36%) | 85.23% | 0.712 | 76.53% | 6.98% | 66 / 177 | 85.70% | No |
| Qwen3.5 4B | 85.29% (83.64%–86.85%) | 85.80% | 0.726 | 76.39% | 5.82% | 55 / 178 | 86.29% | No |
| Qwen3.5 2B | 81.52% (79.67%–83.27%) | 82.09% | 0.662 | 68.97% | 5.93% | 56 / 234 | 82.93% | No |

Not eligible on validation: `safeguard` — No archived candidate meets this requirement on validation.

### Violation-catch target: 90%

| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Random forest · specialists | 88.13% (86.66%–89.67%) | 88.72% | 0.785 | 79.44% | 3.17% | 30 / 155 | 89.11% | No |
| Learned weighted average · specialists | 88.63% (87.13%–90.12%) | 89.17% | 0.792 | 80.64% | 3.39% | 32 / 146 | 89.52% | No |
| Calibrated probability average · specialists | 88.51% (86.98%–89.94%) | 89.05% | 0.790 | 80.50% | 3.49% | 33 / 147 | 89.41% | No |
| Logistic regression · probabilities · specialists | 88.52% (86.97%–90.01%) | 89.06% | 0.789 | 80.64% | 3.60% | 34 / 146 | 89.41% | No |
| Qwen3.5 27B | 90.19% (88.67%–91.60%) | 90.63% | 0.817 | 84.08% | 3.70% | 35 / 120 | 90.88% | No |
| CoPE | 89.13% (87.63%–90.54%) | 89.63% | 0.799 | 81.96% | 3.70% | 35 / 136 | 89.94% | No |
| Equal probability average · specialists | 89.06% (87.61%–90.48%) | 89.57% | 0.798 | 81.83% | 3.70% | 35 / 137 | 89.88% | No |
| Qwen3.5 35B-A3B | 88.49% (86.94%–89.94%) | 89.01% | 0.788 | 80.90% | 3.92% | 37 / 144 | 89.35% | No |
| Equal log-odds average · specialists | 90.24% (88.79%–91.63%) | 90.64% | 0.817 | 84.62% | 4.13% | 39 / 116 | 90.88% | No |
| Logistic regression · log-odds · specialists | 88.88% (87.37%–90.34%) | 89.34% | 0.793 | 82.10% | 4.34% | 41 / 135 | 89.64% | No |
| Shieldstral 3B | 87.76% (86.24%–89.27%) | 88.27% | 0.773 | 79.97% | 4.44% | 42 / 151 | 88.64% | No |
| Jev 1.14 | 88.93% (87.43%–90.46%) | 89.32% | 0.790 | 83.16% | 5.29% | 50 / 127 | 89.58% | No |
| WildGuard 7B | 89.81% (88.31%–91.17%) | 90.13% | 0.805 | 85.01% | 5.40% | 51 / 113 | 90.35% | No |
| Qwen3.5 9B | 88.81% (87.22%–90.29%) | 89.15% | 0.786 | 83.55% | 5.93% | 56 / 124 | 89.41% | No |
| GPT-OSS Safeguard 20B | 89.13% (87.63%–90.57%) | 89.64% | — | 84.62% | 6.14% | 58 / 109 | 89.64% | No |
| Qwen3.5 4B | 84.75% (83.00%–86.44%) | 85.09% | 0.706 | 78.38% | 8.89% | 84 / 163 | 85.46% | No |
| PolicyLM 1.7B | 86.37% (84.72%–87.90%) | 86.56% | 0.732 | 82.36% | 9.63% | 91 / 133 | 86.82% | No |
| Qwen3.5 2B | 83.41% (81.67%–85.19%) | 83.42% | 0.668 | 81.43% | 14.60% | 138 / 140 | 83.64% | No |

### Selected balanced configurations

| Entry | Policy / policies | Decision rule | Archived candidates considered |
|---|---|---|---:|
| Equal log-odds average · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | BLOCK at score ≥ 0.23 | 1 |
| Logistic regression · log-odds · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | Native / original archived decision | 5 |
| Logistic regression · probabilities · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | BLOCK at score ≥ 0.10 | 5 |
| Calibrated probability average · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | BLOCK at score ≥ 0.60 | 1 |
| Random forest · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | Native / original archived decision | 4 |
| CoPE | `wg-p3-cope-social-and-deception` | BLOCK at score ≥ 0.39 | 13 |
| Equal probability average · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | BLOCK at score ≥ 0.52 | 1 |
| Learned weighted average · specialists | `wg-p4-policylm-compact; wg-p4-shieldstral-taxonomy-priority; wg-p3-cope-social-and-deception` | Native / original archived decision | 3 |
| Shieldstral 3B | `transfer-qwen-2b-p3` | Native / original archived decision | 17 |
| Qwen3.5 27B | `wg-p1-concrete-harm` | BLOCK at score ≥ 0.96 | 7 |
| WildGuard 7B | `wildguard-official` | Native / original archived decision | 1 |
| Qwen3.5 35B-A3B | `wg-p2-boundary-checklist` | BLOCK at score ≥ 0.71 | 3 |
| Qwen3.5 9B | `qwen-9b-p3-social-and-sensitive-boundaries` | Native / original archived decision | 3 |
| GPT-OSS Safeguard 20B | `wg-p2-boundary-checklist` | Native / original archived decision | 2 |
| Jev 1.14 | `detailed` | BLOCK at score ≥ 0.64 | 3 |
| Qwen3.5 4B | `wg-p1-concrete-harm` | BLOCK at score ≥ 0.43 | 7 |
| PolicyLM 1.7B | `wg-p4-policylm-compact` | BLOCK at score ≥ 0.46 | 17 |
| Qwen3.5 2B | `transfer-policylm-p2` | BLOCK at score ≥ 0.89 | 6 |

## hatexplain: 1,924 test examples

594 BLOCK; 1,330 ALLOW. Balanced accuracy gives both classes equal weight.

### Balance both classes

| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Logistic regression · log-odds · specialists + Qwen | 79.35% (77.38%–81.24%) | 77.26% | 0.557 | 79.29% | 20.60% | 274 / 123 | 79.37% | — |
| Random forest · specialists + Qwen | 78.65% (76.75%–80.48%) | 75.49% | 0.535 | 82.49% | 25.19% | 335 / 104 | 77.18% | — |
| Jev 1.14 | 78.40% (76.32%–80.29%) | 76.07% | 0.536 | 79.12% | 22.33% | 297 / 124 | 78.12% | — |
| Logistic regression · log-odds · specialists | 77.26% (75.10%–79.22%) | 75.38% | 0.518 | 76.09% | 21.58% | 287 / 142 | 77.70% | — |
| Learned weighted average · specialists + Qwen | 77.24% (75.30%–79.11%) | 73.96% | 0.507 | 81.48% | 26.99% | 359 / 110 | 75.62% | — |
| Logistic regression · probabilities · specialists + Qwen | 77.19% (75.18%–79.06%) | 74.16% | 0.508 | 80.47% | 26.09% | 347 / 116 | 75.94% | — |
| Shieldstral 3B | 77.02% (74.95%–79.00%) | 74.77% | 0.510 | 77.27% | 23.23% | 309 / 135 | 76.92% | — |
| Random forest · specialists | 76.96% (74.83%–78.92%) | 74.82% | 0.509 | 76.77% | 22.86% | 304 / 138 | 77.03% | — |
| Learned weighted average · specialists | 76.95% (74.90%–78.90%) | 74.29% | 0.505 | 78.79% | 24.89% | 331 / 126 | 76.25% | — |
| Qwen3.5 4B | 76.21% (74.20%–78.19%) | 74.19% | 0.496 | 75.42% | 23.01% | 306 / 146 | 76.51% | — |
| Calibrated probability average · specialists + Qwen | 75.67% (73.57%–77.60%) | 73.21% | 0.482 | 76.60% | 25.26% | 336 / 139 | 75.31% | — |
| Equal probability average · specialists + Qwen | 74.97% (72.91%–76.94%) | 71.89% | 0.465 | 78.28% | 28.35% | 377 / 129 | 73.70% | — |
| Logistic regression · probabilities · specialists | 74.83% (72.74%–76.74%) | 70.74% | 0.459 | 81.99% | 32.33% | 430 / 107 | 72.09% | — |
| Equal log-odds average · specialists + Qwen | 74.59% (72.54%–76.53%) | 71.42% | 0.457 | 78.28% | 29.10% | 387 / 129 | 73.18% | — |
| Calibrated probability average · specialists | 74.26% (72.21%–76.22%) | 70.24% | 0.449 | 81.14% | 32.63% | 434 / 112 | 71.62% | — |
| Equal log-odds average · specialists | 72.35% (70.22%–74.34%) | 68.72% | 0.414 | 77.78% | 33.08% | 440 / 132 | 70.27% | — |
| Equal probability average · specialists | 70.26% (68.20%–72.19%) | 64.68% | 0.376 | 83.00% | 42.48% | 565 / 101 | 65.38% | — |
| PolicyLM 1.7B | 63.69% (61.38%–65.93%) | 63.90% | 0.279 | 47.98% | 20.60% | 274 / 309 | 69.70% | — |

### False-block limit: 5%

| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Logistic regression · log-odds · specialists + Qwen | 69.29% (67.22%–71.23%) | 71.36% | 0.481 | 43.10% | 4.51% | 60 / 338 | 79.31% | Yes |
| Random forest · specialists + Qwen | 68.62% (66.54%–70.62%) | 70.60% | 0.469 | 41.75% | 4.51% | 60 / 346 | 78.90% | Yes |
| Learned weighted average · specialists + Qwen | 66.47% (64.34%–68.38%) | 68.12% | 0.431 | 37.37% | 4.44% | 59 / 372 | 77.60% | Yes |
| Logistic regression · probabilities · specialists + Qwen | 66.39% (64.33%–68.40%) | 68.03% | 0.428 | 37.37% | 4.59% | 61 / 372 | 77.49% | Yes |
| Logistic regression · log-odds · specialists | 66.09% (64.16%–67.99%) | 67.67% | 0.423 | 36.70% | 4.51% | 60 / 376 | 77.34% | Yes |
| Shieldstral 3B | 65.97% (64.02%–67.90%) | 67.53% | 0.420 | 36.53% | 4.59% | 61 / 377 | 77.23% | Yes |
| Equal log-odds average · specialists + Qwen | 65.48% (63.59%–67.41%) | 66.95% | 0.417 | 35.02% | 4.06% | 54 / 386 | 77.13% | Yes |
| Jev 1.14 | 65.04% (63.10%–66.98%) | 66.41% | 0.413 | 33.84% | 3.76% | 50 / 393 | 76.98% | Yes |
| Random forest · specialists | 63.87% (61.95%–65.80%) | 64.94% | 0.388 | 31.65% | 3.91% | 52 / 406 | 76.20% | Yes |
| Calibrated probability average · specialists + Qwen | 63.57% (61.53%–65.46%) | 64.58% | 0.374 | 31.65% | 4.51% | 60 / 406 | 75.78% | Yes |
| Equal probability average · specialists + Qwen | 62.77% (60.82%–64.60%) | 63.55% | 0.359 | 29.97% | 4.44% | 59 / 416 | 75.31% | Yes |
| Equal log-odds average · specialists | 63.01% (61.15%–64.86%) | 63.83% | 0.375 | 29.63% | 3.61% | 48 / 418 | 75.78% | Yes |
| Learned weighted average · specialists | 61.98% (60.21%–63.81%) | 62.44% | 0.358 | 27.27% | 3.31% | 44 / 432 | 75.26% | Yes |
| Logistic regression · probabilities · specialists | 60.90% (59.02%–62.71%) | 61.05% | 0.324 | 25.93% | 4.14% | 55 / 440 | 74.27% | Yes |
| Calibrated probability average · specialists | 59.27% (57.58%–61.06%) | 58.72% | 0.293 | 22.22% | 3.68% | 49 / 462 | 73.44% | Yes |
| PolicyLM 1.7B | 57.35% (55.66%–59.03%) | 56.12% | 0.235 | 19.36% | 4.66% | 62 / 479 | 71.88% | Yes |
| Qwen3.5 4B | 66.17% (64.07%–68.13%) | 67.74% | 0.418 | 37.37% | 5.04% | 67 / 372 | 77.18% | No |
| Equal probability average · specialists | 59.52% (57.73%–61.38%) | 59.28% | 0.282 | 24.07% | 5.04% | 67 / 451 | 73.08% | No |

### Violation-catch target: 90%

| Model / method | Balanced accuracy (95% interval) | Macro-F1 | MCC | Catch rate | False-block rate | False blocks / missed | Accuracy | Target met on test? |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Learned weighted average · specialists | 74.17% (72.42%–75.91%) | 67.58% | 0.451 | 90.07% | 41.73% | 555 / 59 | 68.09% | Yes |
| Logistic regression · probabilities · specialists | 73.71% (71.95%–75.49%) | 66.83% | 0.444 | 90.57% | 43.16% | 574 / 56 | 67.26% | Yes |
| Random forest · specialists + Qwen | 77.64% (75.75%–79.42%) | 72.98% | 0.511 | 86.87% | 31.58% | 420 / 78 | 74.12% | No |
| Logistic regression · log-odds · specialists + Qwen | 77.37% (75.54%–79.11%) | 72.29% | 0.506 | 88.05% | 33.31% | 443 / 71 | 73.28% | No |
| Learned weighted average · specialists + Qwen | 76.76% (74.85%–78.52%) | 71.75% | 0.495 | 87.21% | 33.68% | 448 / 76 | 72.77% | No |
| Jev 1.14 | 76.88% (74.96%–78.64%) | 71.67% | 0.497 | 88.05% | 34.29% | 456 / 71 | 72.61% | No |
| Logistic regression · probabilities · specialists + Qwen | 76.06% (74.12%–77.81%) | 70.77% | 0.482 | 87.54% | 35.41% | 471 / 74 | 71.67% | No |
| Calibrated probability average · specialists + Qwen | 75.39% (73.47%–77.21%) | 69.70% | 0.470 | 88.22% | 37.44% | 498 / 70 | 70.48% | No |
| Qwen3.5 4B | 74.93% (73.00%–76.69%) | 69.36% | 0.461 | 87.37% | 37.52% | 499 / 75 | 70.17% | No |
| Logistic regression · log-odds · specialists | 75.19% (73.37%–77.01%) | 69.30% | 0.467 | 88.72% | 38.35% | 510 / 67 | 70.01% | No |
| Equal probability average · specialists + Qwen | 74.21% (72.33%–76.01%) | 68.45% | 0.449 | 87.37% | 38.95% | 518 / 75 | 69.18% | No |
| Random forest · specialists | 74.67% (72.87%–76.39%) | 68.38% | 0.459 | 89.56% | 40.23% | 535 / 62 | 68.97% | No |
| Shieldstral 3B | 73.86% (72.05%–75.54%) | 67.23% | 0.445 | 89.90% | 42.18% | 561 / 60 | 67.72% | No |
| Equal log-odds average · specialists + Qwen | 72.59% (70.72%–74.42%) | 66.21% | 0.421 | 87.88% | 42.71% | 568 / 72 | 66.74% | No |
| Calibrated probability average · specialists | 72.34% (70.56%–74.08%) | 65.37% | 0.419 | 89.56% | 44.89% | 597 / 62 | 65.75% | No |
| Equal probability average · specialists | 70.27% (68.41%–72.03%) | 62.67% | 0.385 | 89.56% | 49.02% | 652 / 62 | 62.89% | No |
| Equal log-odds average · specialists | 67.93% (66.07%–69.75%) | 60.10% | 0.344 | 88.05% | 52.18% | 694 / 71 | 60.24% | No |
| PolicyLM 1.7B | 59.18% (57.25%–60.97%) | 49.39% | 0.189 | 84.68% | 66.32% | 882 / 91 | 49.43% | No |

### Selected balanced configurations

| Entry | Policy / policies | Decision rule | Archived candidates considered |
|---|---|---|---:|
| Logistic regression · log-odds · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.34 | 5 |
| Random forest · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.26 | 4 |
| Jev 1.14 | `detailed` | BLOCK at score ≥ 0.75 | 3 |
| Logistic regression · log-odds · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.32 | 5 |
| Learned weighted average · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.35 | 3 |
| Logistic regression · probabilities · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.35 | 5 |
| Shieldstral 3B | `p0` | BLOCK at score ≥ 0.95 | 22 |
| Random forest · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.32 | 4 |
| Learned weighted average · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.44 | 3 |
| Qwen3.5 4B | `qwen-4b-p1` | BLOCK at score ≥ 0.42 | 12 |
| Calibrated probability average · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.37 | 1 |
| Equal probability average · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.59 | 1 |
| Logistic regression · probabilities · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.36 | 5 |
| Equal log-odds average · specialists + Qwen | `p0; shieldstral-p2; qwen-4b-p1` | BLOCK at score ≥ 0.63 | 1 |
| Calibrated probability average · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.33 | 1 |
| Equal log-odds average · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.63 | 1 |
| Equal probability average · specialists | `p0; shieldstral-p2` | BLOCK at score ≥ 0.50 | 1 |
| PolicyLM 1.7B | `p0` | BLOCK at score ≥ 0.41 | 21 |

## Interpretation limits

The same validation population was used within each benchmark, but earlier policy searches and fitting budgets differed. Some saved policies were tested only because earlier accuracy-based selection favored them; the candidate pool is therefore incomplete. Native categorical models have no score threshold. Ensembles retain previously fitted parameters and their original component policies. Reusing public tests makes this an exploratory comparison, not independent confirmation.

Confidence intervals are unadjusted duplicate-group bootstrap intervals conditional on these saved outputs. Pairwise differences are in results.json. Rank order alone does not establish superiority. Unresolved outputs count as errors in accuracy and class recalls; MCC is omitted when unresolved outputs occur. AUROC and average precision in the CSV use genuine available scores and expose score coverage.

See PLAN.md, coverage.json, selection.json, registry.json, and the interactive index.html for objectives, missing evaluations, configuration provenance, and detailed error/slice results.
