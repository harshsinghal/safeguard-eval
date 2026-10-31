# Frozen-feature classifier results

All choices were made on validation. Seed 20261031 is the predeclared primary neural-network run; the other two seeds are repetitions, not candidates from which to select a better test result. LR is deterministic. Tables retain protocol order. These are reused public test sets, not fresh confirmation.

## wildguard

### balanced

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.33 | 88.82% | 88.37% | 72 | 118 | 0.8860 | 0.7732 | 0.9404 |
| policylm/mlp | 0.51 | 86.70% | 85.64% | 47 | 179 | 0.8620 | 0.7352 | 0.9200 |
| policylm/contrastive | 0.61 | 85.76% | 84.78% | 62 | 180 | 0.8527 | 0.7142 | 0.9101 |
| modernbert/lr | 0.55 | 80.16% | 78.90% | 93 | 244 | 0.7933 | 0.6001 | 0.8635 |
| modernbert/mlp | 0.83 | 80.40% | 79.22% | 97 | 236 | 0.7963 | 0.6041 | 0.8643 |
| modernbert/contrastive | 0.93 | 80.16% | 78.75% | 82 | 255 | 0.7921 | 0.6023 | 0.8691 |

### accuracy

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.33 | 88.82% | 88.37% | 72 | 118 | 0.8860 | 0.7732 | 0.9404 |
| policylm/mlp | 0.51 | 86.70% | 85.64% | 47 | 179 | 0.8620 | 0.7352 | 0.9200 |
| policylm/contrastive | 0.61 | 85.76% | 84.78% | 62 | 180 | 0.8527 | 0.7142 | 0.9101 |
| modernbert/lr | 0.51 | 79.87% | 78.77% | 108 | 234 | 0.7914 | 0.5922 | 0.8635 |
| modernbert/mlp | 0.81 | 80.40% | 79.23% | 98 | 235 | 0.7964 | 0.6040 | 0.8643 |
| modernbert/contrastive | 0.91 | 80.46% | 79.10% | 83 | 249 | 0.7956 | 0.6078 | 0.8691 |

### false block limit

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.45 | 88.35% | 87.66% | 59 | 139 | 0.8804 | 0.7649 | 0.9404 |
| policylm/mlp | 0.44 | 86.76% | 85.74% | 49 | 176 | 0.8628 | 0.7359 | 0.9200 |
| policylm/contrastive | 0.49 | 85.87% | 84.96% | 65 | 175 | 0.8542 | 0.7160 | 0.9101 |
| modernbert/lr | 0.69 | 79.40% | 77.51% | 54 | 296 | 0.7797 | 0.5958 | 0.8635 |
| modernbert/mlp | 0.96 | 79.46% | 77.47% | 46 | 303 | 0.7792 | 0.6001 | 0.8633 |
| modernbert/contrastive | 0.99 | 79.05% | 77.01% | 46 | 310 | 0.7743 | 0.5924 | 0.8751 |

### catch target

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.72 | 86.29% | 85.19% | 48 | 185 | 0.8576 | 0.7272 | 0.9404 |
| policylm/mlp | 0.72 | 85.76% | 84.45% | 37 | 205 | 0.8509 | 0.7201 | 0.9200 |
| policylm/contrastive | 0.95 | 85.29% | 84.05% | 47 | 203 | 0.8464 | 0.7085 | 0.9101 |
| modernbert/lr | 0.41 | 78.05% | 77.68% | 180 | 193 | 0.7772 | 0.5546 | 0.8500 |
| modernbert/mlp | 0.17 | 80.05% | 79.58% | 154 | 185 | 0.7970 | 0.5946 | 0.8660 |
| modernbert/contrastive | 0.15 | 81.17% | 80.52% | 130 | 190 | 0.8075 | 0.6170 | 0.8691 |

### Training-seed variation at the balanced setting

| Backend / head | Mean accuracy | Accuracy range | Mean balanced accuracy | Balanced accuracy range |
|---|---:|---:|---:|---:|
| policylm/lr | 88.82% | 88.82–88.82% | 88.37% | 88.37–88.37% |
| policylm/mlp | 86.34% | 85.76–86.70% | 85.29% | 84.58–85.66% |
| policylm/contrastive | 86.74% | 85.76–87.58% | 85.85% | 84.78–86.80% |
| modernbert/lr | 80.16% | 80.16–80.16% | 78.90% | 78.90–78.90% |
| modernbert/mlp | 80.60% | 80.40–80.93% | 79.40% | 79.06–79.94% |
| modernbert/contrastive | 80.38% | 80.16–80.69% | 78.94% | 78.75–79.29% |

### Paired comparisons at the balanced setting

| Method minus comparator | Balanced accuracy difference | Paired 95% interval | Change in FP | Change in FN |
|---|---:|---:|---:|---:|
| policylm/mlp minus policylm/lr | -2.72 pp | [-3.86, -1.59] pp | -25 | +61 |
| policylm/contrastive minus policylm/mlp | -0.86 pp | [-1.99, +0.32] pp | +15 | +1 |
| policylm/contrastive minus policylm/lr | -3.58 pp | [-4.68, -2.44] pp | -10 | +62 |
| modernbert/mlp minus modernbert/lr | +0.32 pp | [-0.98, +1.65] pp | +4 | -8 |
| modernbert/contrastive minus modernbert/mlp | -0.47 pp | [-1.43, +0.50] pp | -15 | +19 |
| modernbert/contrastive minus modernbert/lr | -0.15 pp | [-1.43, +1.17] pp | -11 | +11 |

Intervals use 2,000 paired duplicate-group bootstrap draws for the fixed primary seed. They are exploratory and unadjusted; they do not include training-seed, model-search, repeated-test-use or labeling uncertainty. Negative FP/FN differences mean fewer mistakes.

## hatexplain

### balanced

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.44 | 76.87% | 78.01% | 332 | 113 | 0.7507 | 0.5239 | 0.8633 |
| policylm/mlp | 0.29 | 76.72% | 77.75% | 332 | 116 | 0.7488 | 0.5194 | 0.8616 |
| policylm/contrastive | 0.37 | 77.34% | 78.21% | 320 | 116 | 0.7546 | 0.5289 | 0.8605 |
| modernbert/lr | 0.45 | 71.62% | 71.88% | 383 | 163 | 0.6942 | 0.4092 | 0.7949 |
| modernbert/mlp | 0.38 | 70.58% | 71.97% | 421 | 145 | 0.6880 | 0.4078 | 0.7952 |
| modernbert/contrastive | 0.49 | 71.78% | 72.23% | 385 | 158 | 0.6965 | 0.4152 | 0.7984 |

### accuracy

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.72 | 80.46% | 74.87% | 140 | 236 | 0.7596 | 0.5247 | 0.8630 |
| policylm/mlp | 0.67 | 79.42% | 74.63% | 171 | 225 | 0.7524 | 0.5065 | 0.8616 |
| policylm/contrastive | 0.8 | 79.57% | 72.88% | 128 | 265 | 0.7428 | 0.4968 | 0.8605 |
| modernbert/lr | 0.78 | 75.78% | 65.11% | 93 | 373 | 0.6641 | 0.3777 | 0.7949 |
| modernbert/mlp | 0.79 | 76.20% | 69.09% | 164 | 294 | 0.7015 | 0.4122 | 0.7952 |
| modernbert/contrastive | 0.82 | 75.26% | 68.46% | 183 | 293 | 0.6933 | 0.3930 | 0.7843 |

### false block limit

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.88 | 78.74% | 68.04% | 53 | 356 | 0.6999 | 0.4652 | 0.8630 |
| policylm/mlp | 0.96 | 75.94% | 62.01% | 21 | 442 | 0.6230 | 0.3877 | 0.8616 |
| policylm/contrastive | 0.96 | 76.25% | 62.84% | 28 | 429 | 0.6350 | 0.3948 | 0.8605 |
| modernbert/lr | 0.81 | 75.62% | 63.97% | 74 | 395 | 0.6509 | 0.3699 | 0.7949 |
| modernbert/mlp | 0.95 | 75.94% | 64.66% | 78 | 385 | 0.6592 | 0.3802 | 0.7952 |
| modernbert/contrastive | 0.99 | 74.74% | 62.49% | 73 | 413 | 0.6324 | 0.3409 | 0.7843 |

### catch target

| Backend / head | Cutoff | Accuracy | Balanced accuracy | FP | FN | Macro-F1 | MCC | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| policylm/lr | 0.33 | 71.83% | 76.50% | 475 | 67 | 0.7099 | 0.4902 | 0.8633 |
| policylm/mlp | 0.07 | 68.19% | 75.18% | 573 | 39 | 0.6784 | 0.4723 | 0.8616 |
| policylm/contrastive | 0.05 | 66.22% | 73.93% | 615 | 35 | 0.6599 | 0.4534 | 0.8605 |
| modernbert/lr | 0.3 | 58.06% | 67.33% | 757 | 50 | 0.5805 | 0.3422 | 0.7980 |
| modernbert/mlp | 0.04 | 53.95% | 64.92% | 848 | 38 | 0.5388 | 0.3104 | 0.7952 |
| modernbert/contrastive | 0.03 | 47.87% | 60.99% | 975 | 28 | 0.4723 | 0.2543 | 0.7984 |

### Training-seed variation at the balanced setting

| Backend / head | Mean accuracy | Accuracy range | Mean balanced accuracy | Balanced accuracy range |
|---|---:|---:|---:|---:|
| policylm/lr | 76.87% | 76.87–76.87% | 78.01% | 78.01–78.01% |
| policylm/mlp | 76.30% | 75.88–76.72% | 77.52% | 77.27–77.75% |
| policylm/contrastive | 77.84% | 77.34–78.74% | 78.01% | 77.77–78.21% |
| modernbert/lr | 71.62% | 71.62–71.62% | 71.88% | 71.88–71.88% |
| modernbert/mlp | 71.67% | 70.58–72.87% | 71.84% | 71.39–72.17% |
| modernbert/contrastive | 72.80% | 71.78–73.70% | 71.49% | 69.56–72.69% |

### Paired comparisons at the balanced setting

| Method minus comparator | Balanced accuracy difference | Paired 95% interval | Change in FP | Change in FN |
|---|---:|---:|---:|---:|
| policylm/mlp minus policylm/lr | -0.25 pp | [-1.77, +1.25] pp | +0 | +3 |
| policylm/contrastive minus policylm/mlp | +0.45 pp | [-0.66, +1.60] pp | -12 | +0 |
| policylm/contrastive minus policylm/lr | +0.20 pp | [-1.20, +1.63] pp | -12 | +3 |
| modernbert/mlp minus modernbert/lr | +0.09 pp | [-1.75, +1.84] pp | +38 | -18 |
| modernbert/contrastive minus modernbert/mlp | +0.26 pp | [-0.94, +1.45] pp | -36 | +13 |
| modernbert/contrastive minus modernbert/lr | +0.35 pp | [-1.52, +2.12] pp | +2 | -5 |

Intervals use 2,000 paired duplicate-group bootstrap draws for the fixed primary seed. They are exploratory and unadjusted; they do not include training-seed, model-search, repeated-test-use or labeling uncertainty. Negative FP/FN differences mean fewer mistakes.
