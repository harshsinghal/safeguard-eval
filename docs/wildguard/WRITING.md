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
