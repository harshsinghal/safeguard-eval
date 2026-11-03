# Results: cyber requests and complete skill packages

These are separate, balanced test populations. Accuracy equals balanced accuracy here. False blocks count benign items labeled BLOCK; misses count attack/malicious-source items labeled ALLOW. Unresolved outputs remain in denominators. Scores describe configured systems on these cohorts, not universal model quality.

Policy candidates and learned-head configurations were frozen on validation before test inference. Neural heads use the first registered seed as primary; all three seeds are shown below. All paired intervals are exploratory, grouped bootstrap estimates without multiple-comparison adjustment.

## CyberSecEval base requests: 330 examples

The primary Jina neural head matches all 330 source labels. Its [100%, 100%] empirical bootstrap interval is degenerate because the observed sample contains no errors; it is **not evidence of zero future error**. Labels are perfectly associated with the two source collections. A trained head may learn residual corpus/style cues; this test cannot separate that from harmful-intent recognition.

| System | Balanced accuracy | Macro F1 | False blocks | Misses | MCC |
|---|---:|---:|---:|---:|---:|
| Jina v2 + neural head | 100.00% | 100.00% | 0/165 | 0/165 | 1.000 |
| Jina v2 + logistic regression | 99.70% | 99.70% | 1/165 | 0/165 | 0.994 |
| Kev 4B | 84.55% | 84.35% | 7/165 | 44/165 | 0.709 |
| Jev 1.14 (API) | 83.33% | 83.07% | 7/165 | 48/165 | 0.688 |
| Shieldstral 3B | 83.33% | 83.28% | 18/165 | 37/165 | 0.671 |
| Clef-Flash 9B | 78.48% | 78.45% | 29/165 | 42/165 | 0.571 |
| Llama Guard 4 12B (custom policy) | 77.27% | 76.80% | 14/165 | 61/165 | 0.569 |
| PolicyLM 1.7B | 70.91% | 70.73% | 35/165 | 61/165 | 0.423 |
| Qwen3.5 4B | 60.91% | 53.86% | 0/165 | 129/165 | 0.350 |
| Llama Guard 4, fixed default taxonomy | 72.42% | 71.09% | 10/165 | 81/165 | 0.497 |

Prompt Guard targets injection/jailbreak instructions rather than the entire task. Its fixed, windowed diagnostic result is **55.76%** balanced accuracy, with 2 false blocks and 144 misses.

Always ALLOW and always BLOCK each achieve 50% balanced accuracy. The learned Jina heads use fitting labels; prompted systems keep their weights fixed.

| System | Grouped 95% interval for balanced accuracy | Unresolved |
|---|---:|---:|
| PolicyLM 1.7B | [65.75%, 76.07%] | 0 |
| Shieldstral 3B | [78.92%, 87.58%] | 0 |
| Kev 4B | [80.65%, 88.01%] | 0 |
| Clef-Flash 9B | [73.40%, 82.70%] | 0 |
| Jev 1.14 (API) | [79.27%, 87.03%] | 0 |
| Qwen3.5 4B | [57.91%, 64.05%] | 0 |
| Llama Guard 4 12B (custom policy) | [72.86%, 81.60%] | 0 |
| Prompt Guard 2 86M (diagnostic) | [53.20%, 58.61%] | 0 |
| Jina v2 + logistic regression | [99.01%, 100.00%] | 0 |
| Jina v2 + neural head | [100.00%, 100.00%] | 0 |

### What changed with policy selection?

The comparison is brief policy versus validation-selected policy at the same fixed decision rule. A test regression is retained; we do not switch back after seeing it.

| System | Selected policy | Brief BA | Selected BA | Change (pp) | Paired 95% interval (pp) |
|---|---|---:|---:|---:|---:|
| PolicyLM 1.7B | contrasts | 50.91% | 70.91% | +20.00 | [+14.41, +25.40] |
| Shieldstral 3B | contrasts | 79.39% | 83.33% | +3.94 | [+1.39, +6.68] |
| Kev 4B | structured | 81.21% | 84.55% | +3.33 | [+0.14, +6.42] |
| Clef-Flash 9B | brief | 78.48% | 78.48% | +0.00 | [+0.00, +0.00] |
| Jev 1.14 (API) | contrasts | 81.21% | 83.33% | +2.12 | [+0.20, +4.36] |
| Qwen3.5 4B | brief | 60.91% | 60.91% | +0.00 | [+0.00, +0.00] |
| Llama Guard 4 12B (custom policy) | structured | 75.45% | 77.27% | +1.82 | [+0.00, +3.85] |

Llama Guard's selected custom policy versus its fixed default taxonomy: **+4.85 points**, paired interval [+2.03, +7.83]. The native taxonomy was a fixed control, not part of the three-candidate authoring search.

## MalSkillBench complete textual packages: 512 examples

| System | Balanced accuracy | Macro F1 | False blocks | Misses | MCC |
|---|---:|---:|---:|---:|---:|
| Jev 1.14 (API) | 95.51% | 95.50% | 1/256 | 22/256 | 0.913 |
| Clef-Flash 9B | 90.82% | 90.79% | 8/256 | 39/256 | 0.822 |
| Qwen3.5 4B | 85.55% | 85.24% | 0/256 | 74/256 | 0.743 |
| Jina v2 + neural head | 81.64% | 81.64% | 43/256 | 51/256 | 0.633 |
| Jina v2 + logistic regression | 79.49% | 79.49% | 48/256 | 57/256 | 0.590 |
| Kev 4B | 73.24% | 71.55% | 6/256 | 131/256 | 0.533 |
| Llama Guard 4 12B (custom policy) | 70.70% | 70.04% | 37/256 | 113/256 | 0.434 |
| PolicyLM 1.7B | 61.72% | 60.90% | 135/256 | 61/256 | 0.245 |
| Shieldstral 3B | 58.01% | 49.02% | 0/256 | 215/256 | 0.295 |
| Llama Guard 4, fixed default taxonomy | 70.31% | 68.88% | 21/256 | 131/256 | 0.450 |

Prompt Guard targets injection/jailbreak instructions rather than the entire task. Its fixed, windowed diagnostic result is **50.00%** balanced accuracy, with 57 false blocks and 199 misses.

Always ALLOW and always BLOCK each achieve 50% balanced accuracy. The learned Jina heads use fitting labels; prompted systems keep their weights fixed.

| System | Grouped 95% interval for balanced accuracy | Unresolved |
|---|---:|---:|
| PolicyLM 1.7B | [57.57%, 65.75%] | 0 |
| Shieldstral 3B | [55.75%, 60.44%] | 0 |
| Kev 4B | [70.12%, 76.43%] | 0 |
| Clef-Flash 9B | [88.28%, 93.26%] | 0 |
| Jev 1.14 (API) | [93.80%, 97.19%] | 0 |
| Qwen3.5 4B | [82.83%, 88.35%] | 0 |
| Llama Guard 4 12B (custom policy) | [66.77%, 74.45%] | 0 |
| Prompt Guard 2 86M (diagnostic) | [45.98%, 53.68%] | 0 |
| Jina v2 + logistic regression | [75.91%, 83.06%] | 0 |
| Jina v2 + neural head | [78.04%, 85.11%] | 0 |

### What changed with policy selection?

The comparison is brief policy versus validation-selected policy at the same fixed decision rule. A test regression is retained; we do not switch back after seeing it.

| System | Selected policy | Brief BA | Selected BA | Change (pp) | Paired 95% interval (pp) |
|---|---|---:|---:|---:|---:|
| PolicyLM 1.7B | contrasts | 52.93% | 61.72% | +8.79 | [+5.25, +12.34] |
| Shieldstral 3B | contrasts | 57.81% | 58.01% | +0.20 | [-0.99, +1.32] |
| Kev 4B | structured | 67.19% | 73.24% | +6.05 | [+3.54, +8.66] |
| Clef-Flash 9B | structured | 80.86% | 90.82% | +9.96 | [+7.31, +12.57] |
| Jev 1.14 (API) | structured | 93.95% | 95.51% | +1.56 | [-0.16, +3.31] |
| Qwen3.5 4B | contrasts | 82.23% | 85.55% | +3.32 | [+1.39, +5.31] |
| Llama Guard 4 12B (custom policy) | contrasts | 66.60% | 70.70% | +4.10 | [+1.46, +6.70] |

Llama Guard's selected custom policy versus its fixed default taxonomy: **+0.39 points**, paired interval [-2.10, +2.94]. The native taxonomy was a fixed control, not part of the three-candidate authoring search.

## Do companion files help?

For prompted systems and Prompt Guard, this changes only the available text: full package versus SKILL.md, under the same selected policy, weights and cutoff. Positive changes favor the full package.

| System | Full package BA | SKILL.md-only BA | Full false blocks / misses | Document-only false blocks / misses | Change (pp) | Paired 95% interval (pp) |
|---|---:|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | 61.72% | 57.81% | 135 / 61 | 129 / 87 | +3.91 | [+1.86, +5.98] |
| Shieldstral 3B | 58.01% | 55.86% | 0 / 215 | 0 / 226 | +2.15 | [+1.03, +3.51] |
| Kev 4B | 73.24% | 69.14% | 6 / 131 | 5 / 153 | +4.10 | [+2.41, +5.98] |
| Clef-Flash 9B | 90.82% | 82.03% | 8 / 39 | 9 / 83 | +8.79 | [+6.46, +11.28] |
| Jev 1.14 (API) | 95.51% | 88.09% | 1 / 22 | 2 / 59 | +7.42 | [+5.22, +9.72] |
| Qwen3.5 4B | 85.55% | 75.59% | 0 / 74 | 0 / 125 | +9.96 | [+7.54, +12.50] |
| Llama Guard 4 12B (custom policy) | 70.70% | 62.11% | 37 / 113 | 44 / 150 | +8.59 | [+5.97, +11.27] |
| Prompt Guard 2 86M (diagnostic) | 50.00% | 51.56% | 57 / 199 | 51 / 197 | -1.56 | [-2.73, -0.59] |

### Packages with companion files only

This prespecified subset contains 177 packages: 49 benign and 128 malicious. Balanced accuracy weights the two classes equally. The other 335 packages contain only SKILL.md; their two native requests should be identical.

| System | Full BA | Document-only BA | Full false blocks / misses | Document-only false blocks / misses | Change (pp) | Paired 95% interval (pp) |
|---|---:|---:|---:|---:|---:|---:|
| PolicyLM 1.7B | 62.42% | 58.39% | 33 / 10 | 27 / 36 | +4.03 | [-2.23, +9.52] |
| Shieldstral 3B | 58.20% | 53.91% | 0 / 107 | 0 / 118 | +4.30 | [+2.00, +6.97] |
| Kev 4B | 70.46% | 62.89% | 1 / 73 | 0 / 95 | +7.57 | [+3.54, +11.20] |
| Clef-Flash 9B | 96.09% | 77.89% | 0 / 10 | 1 / 54 | +18.21 | [+13.45, +23.01] |
| Jev 1.14 (API) | 97.66% | 83.59% | 0 / 6 | 0 / 42 | +14.06 | [+10.00, +18.18] |
| Qwen3.5 4B | 91.41% | 71.48% | 0 / 22 | 0 / 73 | +19.92 | [+15.41, +24.59] |
| Llama Guard 4 12B (custom policy) | 78.40% | 56.81% | 7 / 37 | 14 / 74 | +21.60 | [+15.37, +28.25] |
| Prompt Guard 2 86M (diagnostic) | 45.42% | 52.32% | 11 / 111 | 5 / 109 | -6.90 | [-11.76, -2.43] |

Single-file repeat controls (identical request hashes / cases; changed decisions):

- PolicyLM 1.7B: 335/335; 0 changed decisions.

- Shieldstral 3B: 335/335; 0 changed decisions.

- Kev 4B: 335/335; 0 changed decisions.

- Clef-Flash 9B: 335/335; 0 changed decisions.

- Jev 1.14 (API): 335/335; 2 changed decisions.

- Qwen3.5 4B: 335/335; 0 changed decisions.

- Llama Guard 4 12B (custom policy): 335/335; 0 changed decisions.

- Prompt Guard 2 86M (diagnostic): 335/335; 0 changed decisions.

The Jina comparison below **retrains separate heads for each view**. It measures two input/training pipelines, not the same classifier with evidence removed.

| Head | Full-package BA | Separately trained SKILL.md-only BA | Full false blocks / misses | Document-only false blocks / misses | Change (pp) | Paired 95% interval (pp) |
|---|---:|---:|---:|---:|---:|---:|
| Jina v2 + logistic regression | 79.49% | 76.95% | 48 / 57 | 46 / 72 | +2.54 | [-0.61, +5.70] |
| Jina v2 + neural head | 81.64% | 78.71% | 43 / 51 | 46 / 63 | +2.93 | [+0.05, +5.70] |

## Neural seed sensitivity

The first seed is primary. No seed or seed ensemble was selected using test results.

| Task / input | Seed 20261104 | Seed 20261105 | Seed 20261106 |
|---|---:|---:|---:|
| cyber / Jina v2 + neural head | 100.00% | 100.00% | 99.39% |
| skills / Jina v2 + neural head | 81.64% | 83.40% | 81.25% |
| skills / Jina v2 + neural, SKILL.md only | 78.71% | 79.88% | 78.71% |

## Boundaries and detailed slices

The cyber task uses source-derived labels; dual-use and benign-looking reconnaissance requests remain a limitation. The original JSON-wrapper pilot was superseded before test. Skills are text-only, size-limited and mostly generated in the test cohort; only three wild malicious packages are present. This is not evidence of safe execution, successful exploitation, or performance on all future attacks.

All source, category, behavior and length slices, selected configurations, error counts and paired comparisons are in [results.json](../../published_runs/2026-11-03-cyber-skill-guardrails/results.json). [Methods](METHODS.md) · [Pre-test plan](PLAN.md) · [Public evidence](../../published_runs/2026-11-03-cyber-skill-guardrails/README.md).
