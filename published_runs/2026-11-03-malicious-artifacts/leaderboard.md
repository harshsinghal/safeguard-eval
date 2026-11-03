# Malicious artifact screening results

Validation-selected systems. Code and skills are different tasks; do not average these leaderboards.
All systems received the same bounded artifact view. Trained systems used supervised fitting labels.

## Code

| Model | Selected configuration | Accuracy | Balanced accuracy (95% CI) | False blocks | Missed threats | Unresolved |
|---|---|---:|---:|---:|---:|---:|
| liquid | lr5e-05-epoch3 | 91.25% | 91.25% (86.48%–95.76%) | 3 | 11 | 0 |
| jev | brief | 90.00% | 90.00% (84.90%–95.14%) | 0 | 16 | 0 |
| clef | structured | 88.75% | 88.75% (83.82%–93.90%) | 0 | 18 | 0 |
| tfidf | C10 | 88.12% | 88.12% (82.50%–93.75%) | 0 | 19 | 0 |
| policylm | evidence | 86.88% | 86.88% (81.61%–92.14%) | 6 | 15 | 0 |
| qwen | brief | 86.88% | 86.88% (81.69%–92.47%) | 0 | 21 | 0 |
| kev | evidence | 78.75% | 78.75% (71.25%–87.86%) | 0 | 34 | 0 |
| shieldstral | structured | 76.25% | 76.25% (69.14%–84.64%) | 1 | 37 | 0 |

## Skills

| Model | Selected configuration | Accuracy | Balanced accuracy (95% CI) | False blocks | Missed threats | Unresolved |
|---|---|---:|---:|---:|---:|---:|
| tfidf | C10 | 73.92% | 70.19% (66.53%–73.19%) | 258 | 103 | 0 |
| liquid | lr5e-05-epoch3 | 68.86% | 65.06% (60.79%–68.42%) | 288 | 143 | 0 |
| policylm | structured | 55.27% | 61.86% (57.57%–65.36%) | 39 | 580 | 0 |
| jev | structured | 48.12% | 57.21% (54.82%–60.35%) | 0 | 718 | 0 |
| clef | structured | 45.74% | 55.24% (52.81%–58.45%) | 0 | 751 | 0 |
| qwen | structured | 44.44% | 54.17% (51.93%–57.15%) | 0 | 769 | 0 |
| kev | structured | 43.71% | 53.51% (51.46%–56.34%) | 2 | 777 | 0 |
| shieldstral | structured | 42.34% | 52.44% (50.90%–54.72%) | 0 | 798 | 0 |

