# Liquid classifier: complete results

WildGuard prompt harmfulness: 4,096 fitting, 1,536 validation and 1,699 test prompts.
All configurations below were selected on validation before test inference. Higher is better
for accuracy, balanced accuracy, F1, MCC, recall and specificity; lower is better for errors.
The primary objective is ordinary accuracy. Primary seed is 20261031, not the best test seed.

| Selection objective | Pipeline | Checkpoint / C | Cutoff | Seed | Accuracy | Balanced accuracy | False blocks | Missed harmful |
|---|---|---|---:|---:|---:|---:|---:|---:|
| accuracy | frozen | frozen-c0.01 | 0.58 | 20261031 | 82.22% | 80.88% | 68 | 234 |
| accuracy | finetuned | finetuned-lr5e-05-e3 | 0.68 | 20261031 | 86.40% | 85.49% | 60 | 171 |
| accuracy | finetuned | finetuned-lr5e-05-e3 | 0.68 | 20261101 | 85.52% | 84.52% | 62 | 184 |
| accuracy | finetuned | finetuned-lr5e-05-e3 | 0.68 | 20261102 | 86.76% | 86.02% | 70 | 155 |
| balanced | frozen | frozen-c0.01 | 0.58 | 20261031 | 82.22% | 80.88% | 68 | 234 |
| balanced | finetuned | finetuned-lr5e-05-e3 | 0.86 | 20261031 | 85.70% | 84.64% | 56 | 187 |
| balanced | finetuned | finetuned-lr5e-05-e3 | 0.86 | 20261101 | 85.11% | 83.95% | 54 | 199 |
| balanced | finetuned | finetuned-lr5e-05-e3 | 0.86 | 20261102 | 86.11% | 85.22% | 65 | 171 |
| false_block_limit | frozen | frozen-c0.01 | 0.70 | 20261031 | 81.34% | 79.61% | 47 | 270 |
| false_block_limit | finetuned | finetuned-lr5e-05-e3 | 0.89 | 20261031 | 85.46% | 84.36% | 55 | 192 |
| false_block_limit | finetuned | finetuned-lr5e-05-e3 | 0.89 | 20261101 | 84.99% | 83.81% | 54 | 201 |
| false_block_limit | finetuned | finetuned-lr5e-05-e3 | 0.89 | 20261102 | 86.05% | 85.10% | 61 | 176 |
| catch_target | frozen | frozen-c0.01 | 0.46 | 20261031 | 83.34% | 82.48% | 93 | 190 |
| catch_target | finetuned | finetuned-lr5e-05-e3 | 0.95 | 20261031 | 85.23% | 84.01% | 49 | 202 |
| catch_target | finetuned | finetuned-lr5e-05-e3 | 0.95 | 20261101 | 85.17% | 83.92% | 47 | 205 |
| catch_target | finetuned | finetuned-lr5e-05-e3 | 0.95 | 20261102 | 85.93% | 84.87% | 54 | 185 |

## Training variation

Fine-tuned results across all three seeds; no seed averaging is used for prediction.

| Profile | Mean accuracy | Accuracy range | Mean balanced accuracy | Balanced accuracy range |
|---|---:|---:|---:|---:|
| accuracy | 86.23% | 85.52–86.76% | 85.34% | 84.52–86.02% |
| balanced | 85.64% | 85.11–86.11% | 84.60% | 83.95–85.22% |
| false_block_limit | 85.50% | 84.99–86.05% | 84.42% | 83.81–85.10% |
| catch_target | 85.44% | 85.17–85.93% | 84.27% | 83.92–84.87% |

## Paired comparisons

Fine-tuned minus frozen, primary seed; percentage points. The 2,000 duplicate-group bootstrap
draws hold predictions fixed. These intervals exclude seed/search uncertainty and are unadjusted.

| Profile | Accuracy difference (95% interval) | Balanced difference (95% interval) | Corrected / newly wrong |
|---|---:|---:|---:|
| accuracy | +4.18 (+2.71, +5.65) | +4.60 (+3.05, +6.19) | 117 / 46 |
| balanced | +3.47 (+2.06, +4.83) | +3.75 (+2.30, +5.23) | 106 / 47 |

## Validation selections

| Profile | Pipeline | Selected candidate | Cutoff | Mean validation accuracy | Mean validation balanced accuracy |
|---|---|---|---:|---:|---:|
| accuracy | frozen | frozen-c0.01 | 0.58 | 89.06% | 89.21% |
| balanced | frozen | frozen-c0.01 | 0.58 | 89.06% | 89.21% |
| false_block_limit | frozen | frozen-c0.01 | 0.70 | 87.50% | 87.97% |
| catch_target | frozen | frozen-c0.01 | 0.46 | 88.28% | 88.14% |
| accuracy | finetuned | finetuned-lr5e-05-e3 | 0.68 | 93.99% | 93.96% |
| balanced | finetuned | finetuned-lr5e-05-e3 | 0.86 | 93.92% | 94.01% |
| false_block_limit | finetuned | finetuned-lr5e-05-e3 | 0.89 | 93.79% | 93.90% |
| catch_target | finetuned | finetuned-lr5e-05-e3 | 0.95 | 93.47% | 93.65% |

The CSV includes fixed-.5 results, precision, class F1, MCC, both error rates,
coverage, AUROC, average precision, Brier and log loss for every selected seed.
The evidence bundle also contains category/adversarial slices. Test results are exploratory:
this public test has been used repeatedly, and pretraining contamination is not audited.
