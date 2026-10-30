# Full frozen-representation results

All test rows use 1,699 prompts: 754 harmful and 945 benign. No unresolved outputs. These are frozen validation selections, not a ranking chosen from test scores.

## Selected configurations

| Method | Features | C | Balanced cutoff | Validation balanced accuracy |
|---|---|---:|---:|---:|
| Qwen final-layer probe | qwen-l24-mean | 0.01 | 0.52 | 88.52% |
| PolicyLM final-layer probe | policylm-l28-slot | 0.01 | 0.35 | 94.96% |
| Combined final-layer probe | qwen-l24-mean + policylm-l28-slot | 0.01 | 0.48 | 94.64% |
| Qwen layer/pooling search | qwen-l12-mean | 0.01 | 0.61 | 90.63% |
| PolicyLM layer/pooling search | policylm-l21-slot | 0.1 | 0.6 | 95.39% |
| Combined selected representations | qwen-l12-mean + policylm-l21-slot | 0.01 | 0.63 | 95.10% |
| PolicyLM native score | Native category probability | — | 0.49 | 92.67% |

## Balanced operating points

| Method | Balanced accuracy (95% interval) | Accuracy | Macro-F1 | MCC | Recall | False-block rate | FP | FN | AUROC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Qwen final-layer probe | 82.44% (80.59%–84.16%) | 83.46% | 82.88% | 0.6667 | 73.34% | 8.47% | 80 | 201 | 0.8942 |
| PolicyLM final-layer probe | 88.43% (86.88%–89.85%) | 88.88% | 88.66% | 0.7744 | 84.48% | 7.62% | 72 | 117 | 0.9403 |
| Combined final-layer probe | 87.09% (85.53%–88.56%) | 87.82% | 87.49% | 0.7543 | 80.64% | 6.46% | 61 | 146 | 0.9396 |
| Qwen layer/pooling search | 83.11% (81.36%–84.80%) | 84.34% | 83.67% | 0.6884 | 72.15% | 5.93% | 56 | 210 | 0.9109 |
| PolicyLM layer/pooling search | 86.80% (85.16%–88.30%) | 87.58% | 87.22% | 0.7500 | 79.84% | 6.24% | 59 | 152 | 0.9364 |
| Combined selected representations | 86.85% (85.17%–88.40%) | 87.70% | 87.32% | 0.7532 | 79.31% | 5.61% | 53 | 156 | 0.9394 |
| PolicyLM native score | 86.18% (84.54%–87.72%) | 86.58% | 86.34% | 0.7275 | 82.63% | 10.26% | 97 | 131 | 0.9418 |
| PolicyLM score at 0.5 | 86.15% (84.51%–87.66%) | 86.58% | 86.33% | 0.7275 | 82.36% | 10.05% | 95 | 133 | 0.9418 |
| Historical WildGuard 7B | 89.81% (88.31%–91.17%) | 90.35% | 90.13% | 0.8051 | 85.01% | 5.40% | 51 | 113 | — |
| Historical specialist equal-log-odds ensemble | 91.08% (89.65%–92.39%) | 91.47% | 91.30% | 0.8272 | 87.67% | 5.50% | 52 | 93 | — |

Historical controls used a different validation population and prior selection procedure. Their scores are context, not an equal-budget comparison. Native PolicyLM here uses fresh outputs and this study’s validation cutoff. The fixed 0.5 row preserves the original benchmarking convention, not the vendor’s default preset.

## At most 5% false blocks on validation

Each profile selects its own C and cutoff on validation. The recall-constrained profile minimizes false blocks subject to at least 90% validation recall; it need not use a lower cutoff than the balanced profile.

| Method | Candidate | Cutoff | Test false-block rate | Test recall | Constraint held on test? |
|---|---|---:|---:|---:|---|
| Qwen final-layer probe | qwen-l24-mean__C0.01 | 0.71 | 4.55% | 63.26% | Yes |
| PolicyLM final-layer probe | policylm-l28-slot__C0.01 | 0.47 | 6.35% | 81.83% | No |
| Combined final-layer probe | qwen-l24-mean+policylm-l28-slot__C0.01 | 0.57 | 5.93% | 79.05% | No |
| Qwen layer/pooling search | qwen-l12-mean__C0.01 | 0.63 | 5.71% | 71.75% | No |
| PolicyLM layer/pooling search | policylm-l21-slot__C0.01 | 0.43 | 6.77% | 83.02% | No |
| Combined selected representations | qwen-l12-mean+policylm-l21-slot__C0.1 | 0.5 (native) | 6.88% | 80.77% | No |
| PolicyLM native score | policylm-native | 0.64 | 6.98% | 79.31% | No |

## At least 90% harmful recall on validation

Each profile selects its own C and cutoff on validation. The recall-constrained profile minimizes false blocks subject to at least 90% validation recall; it need not use a lower cutoff than the balanced profile.

| Method | Candidate | Cutoff | Test false-block rate | Test recall | Constraint held on test? |
|---|---|---:|---:|---:|---|
| Qwen final-layer probe | qwen-l24-mean__C0.01 | 0.49 | 9.74% | 74.14% | No |
| PolicyLM final-layer probe | policylm-l28-slot__C0.01 | 0.74 | 4.97% | 75.46% | No |
| Combined final-layer probe | qwen-l24-mean+policylm-l28-slot__C0.01 | 0.82 | 4.34% | 73.34% | No |
| Qwen layer/pooling search | qwen-l12-mean__C0.01 | 0.5 (native) | 7.83% | 76.53% | No |
| PolicyLM layer/pooling search | policylm-l21-slot__C0.01 | 0.72 | 4.55% | 76.13% | No |
| Combined selected representations | qwen-l12-mean+policylm-l21-slot__C0.01 | 0.73 | 4.55% | 76.39% | No |
| PolicyLM native score | policylm-native | 0.57 | 8.47% | 80.50% | No |

## Combined-method paired comparisons

Differences are percentage points of balanced accuracy. Positive favors the combined method. Intervals use the same 2,000 duplicate-group resamples and are descriptive and unadjusted.

| Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |
|---|---|---:|---:|---:|---:|
| Combined final-layer probe | Qwen final-layer probe | +4.65 | +3.07 to +6.19 | 118 | 44 |
| Combined final-layer probe | PolicyLM final-layer probe | -1.34 | -2.21 to -0.49 | 17 | 35 |
| Combined final-layer probe | Qwen layer/pooling search | +3.98 | +2.65 to +5.38 | 96 | 37 |
| Combined final-layer probe | PolicyLM layer/pooling search | +0.29 | -0.64 to +1.28 | 35 | 31 |
| Combined final-layer probe | Combined selected representations | +0.24 | -0.72 to +1.12 | 30 | 28 |
| Combined final-layer probe | PolicyLM native score | +0.91 | -0.33 to +2.14 | 69 | 48 |
| Combined final-layer probe | PolicyLM score at 0.5 | +0.94 | -0.32 to +2.17 | 68 | 47 |
| Combined final-layer probe | Historical WildGuard 7B | -2.72 | -3.90 to -1.55 | 27 | 70 |
| Combined final-layer probe | Historical specialist equal-log-odds ensemble | -3.99 | -5.39 to -2.74 | 31 | 93 |
| Combined selected representations | Qwen final-layer probe | +4.41 | +2.77 to +5.97 | 121 | 49 |
| Combined selected representations | PolicyLM final-layer probe | -1.58 | -2.62 to -0.54 | 28 | 48 |
| Combined selected representations | Combined final-layer probe | -0.24 | -1.12 to +0.72 | 28 | 30 |
| Combined selected representations | Qwen layer/pooling search | +3.74 | +2.42 to +5.07 | 88 | 31 |
| Combined selected representations | PolicyLM layer/pooling search | +0.05 | -0.74 to +0.90 | 24 | 22 |
| Combined selected representations | PolicyLM native score | +0.67 | -0.61 to +1.98 | 69 | 50 |
| Combined selected representations | PolicyLM score at 0.5 | +0.70 | -0.56 to +1.97 | 67 | 48 |
| Combined selected representations | Historical WildGuard 7B | -2.96 | -4.15 to -1.75 | 27 | 72 |
| Combined selected representations | Historical specialist equal-log-odds ensemble | -4.23 | -5.55 to -2.96 | 28 | 92 |

## Additional explanatory contrasts

These descriptive contrasts were calculated to explain the frozen results; they did not select any configuration.

| Method | Comparator | Difference | 95% interval | Corrected | Newly wrong |
|---|---|---:|---:|---:|---:|
| PolicyLM final-layer probe | PolicyLM native score | +2.25 | +1.21 to +3.35 | 67 | 28 |
| PolicyLM final-layer probe | Historical WildGuard 7B | -1.38 | -2.47 to -0.34 | 31 | 56 |
| PolicyLM final-layer probe | Historical specialist equal-log-odds ensemble | -2.65 | -3.94 to -1.50 | 31 | 75 |
| PolicyLM layer/pooling search | PolicyLM final-layer probe | -1.63 | -2.66 to -0.66 | 25 | 47 |
| Qwen layer/pooling search | Qwen final-layer probe | +0.67 | -0.71 to +2.11 | 72 | 57 |

The machine-readable `test-results.json` in the evidence bundle additionally contains every category/adversarial slice, average precision, Brier score, log loss, full confusion matrices and extraction provenance. `validation.json` retains all candidate probabilities and operating-point grids. No source prompts or hidden vectors are published.
