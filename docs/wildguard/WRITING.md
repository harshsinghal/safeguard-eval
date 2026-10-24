# Writing and evidence map

This is an outline for later articles and a research report, not a statement of results.

## Article 1: A policy is an experimental variable

Explain the motivating moderation task, why a taxonomy and examples are different, the initial policy, error-based revisions, and the exact changes that helped or hurt. Use within-model initial-to-tuned accuracy, then show failed edits and why training improvement may not generalize. Link every figure to frozen policy and run artifacts.

## Article 2: Building a benchmark that resists self-deception

Discuss repeated prompts, paired assistant responses, source label conflicts, training-versus-test annotation, leakage barriers, parse failures, threshold calibration, sample versus full-population scores, uncertainty and compute limits. Contrast the earlier injection arena with the more controlled WildGuard experiment without treating either as a universal ranking.

## Article 3: Operating policy models on a small budget

Document provider choice, checkpoint/runtime compatibility, batching, model-specific adapters, latency measurement limitations, billed setup/download time, interrupted runs and cleanup. Use actual billing records; do not infer dollar cost solely from generation time.

## Research report structure

1. Question and registered hypothesis; distinguish policy optimization from additional weight training.
2. Related work: WildGuard/WildGuardMix, custom-policy classifiers, prompt optimization and safety evaluation; add a literature review before publication.
3. Data and labels: pinned revision, group construction, split counts, duplicates/conflicts, exclusion rules, task-specific test size and dataset terms.
4. Models and adapters: provenance, native formats, score interpretation, decoding, quantization, windowing and context.
5. Search method: candidate budget, sampled/full fitting populations, human/agent involvement, candidate history, validation selection and threshold control.
6. Evaluation: primary model selected before test; all comparison rows; paired intervals, category/adversarial slices, parse errors and calibration effects.
7. Qualitative analysis: categorize disagreements with blinded or independent human review where possible; preserve original benchmark labels.
8. Compute and reproducibility: exact artifacts, hashes, dependencies, costs and failures.
9. Limitations: public-benchmark contamination, heterogeneous model sizes/training data, noisy labels, selection effects, one-seed search, limited compute and absent independent replication.
10. Conclusions restricted to observed results. Negative results are findings.

## Evidence requirements

- Every reported score: run ID, dataset IDs/hash, split, count, adapter, policy hash, threshold, error count.
- Every gain: comparator, whether paired, confidence interval and whether policy or threshold changed.
- Every policy edit: dated rationale from fitting errors, parent policy and complete retained text.
- Every exclusion or deviation: reason, timing relative to test access and effect on coverage.
- Every public example: verify upstream redistribution conditions and quote minimally; prefer paraphrased error categories.
- A stronger causal claim needs additional datasets, repeated search seeds, matched base models, independent label review, and ideally equal-compute fine-tuning baselines. These are future studies, not implied by this run.

## Study questions to answer from the frozen results

| Question | Required comparison | Claim boundary |
|---|---|---|
| Does changing the policy help? | Each model's validation-selected policy versus its p0, fixed threshold, paired test rows | Deployment-specific policy effect; retain non-improvements |
| Does the chosen policy model beat WildGuard? | Preselected primary configuration versus official WildGuard on the full labeled test population | One public benchmark, heterogeneous models and uncertain training exposure |
| Is one shared policy portable? | p0/shared/individual roles within each model, including identical-role aliases | Shared selection used all four validation results; no unseen-model transfer claim |
| Is the gain simply a different blocking threshold? | p0 at 0.5, p0 calibrated, tuned at 0.5, tuned calibrated | Thresholds selected on validation; keep the policy-only primary separate |
| Do fitting gains transfer? | Search fit, expanded fit, validation, internal audit and official test | Different label provenance and repeated source rows can affect comparisons |
| What did operational reliability change? | Failure counts and official-compatible F1, with full failures retained | Runtime-specific observations; unresolved Safeguard degeneration needs a separate ablation |

Before a research-paper submission, add an independent held-out dataset and repeated policy-search seeds. A general claim about policy tuning versus fine-tuning also requires matched base models and a newly run fine-tuning baseline with a stated data/compute budget. Those are follow-up studies, not missing rows to conceal in the current report.

## Findings ready for a first article draft

- Policy wording is useful but not uniformly beneficial: selected Shieldstral improves by 2.88 test-accuracy points and PolicyLM by 1.77; CoPE's small gain and Safeguard's small decline have intervals spanning zero.
- The primary Shieldstral/WildGuard comparison is +0.47 points with an interval spanning zero. A headline claiming demonstrated superiority would overstate the result.
- Calibration is a necessary comparator: Shieldstral's initial policy rises from 87.93% to 90.11% with a validation-selected threshold, versus 90.82% for its tuned policy. The remaining difference is uncertain.
- The validation winner need not be the test winner: PolicyLM selected its compact policy, but its shared checklist scored higher on test. Keep the original selection.
- Benchmark labels matter: two-of-three versus unanimous annotation slices differ substantially, and training uses a different labeling process. Describe agreement with labels, not universal moderation correctness.
- Operational reliability is part of the measurement: Safeguard's repetitive generation failures stay in the denominator, and fewer failures do not necessarily mean more correct predictions.

The detailed scores, paired counts and uncertainty belong to the frozen evidence report, not rounded claims copied between drafts. Link each article figure to its CSV, SVG, analysis JSON and exact policy files. Do not use these results to claim downstream prompt-injection protection or performance on the earlier image-prompt task.
