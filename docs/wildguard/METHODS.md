# Methods and implementation record

This document describes the implemented experiment. The dated [plan](PLAN.md), [notebook](NOTES.md), candidate registry and immutable freeze preserve the order of decisions. Final scores belong in [RESULTS.md](RESULTS.md).

## Estimand

Measure agreement with WildGuardMix **prompt harmfulness** labels when model weights remain fixed and the written policy changes. Harmful maps to BLOCK; unharmful maps to ALLOW. Assistant responses, source labels, subcategory and adversarial flags never enter inference requests. There is no REVIEW class. Runtime and parsing failures remain incorrect in the accuracy denominator.

The primary cross-model comparison uses the policy/model chosen on validation before test access against the released WildGuard checkpoint. Within-model p0 versus tuned comparisons estimate the effect of the policy intervention in each documented deployment. All these models have already been trained; this experiment does not compare policy optimization with a newly run, equal-compute fine-tuning procedure.

## Data

Dataset: [AllenAI WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix), revision `d29c47f41c8b51348b5c8e8c81c039b3132b66d1`. The upstream dataset is attributed to Han et al., *WildGuard: Open One-Stop Moderation Tools for Safety Risks, Jailbreaks, and Refusals of LLMs* (2024), [paper](https://arxiv.org/abs/2406.18495), under the dataset card's ODC-BY license and access conditions. Public artifacts contain derived evaluation records rather than source prompt text.

The importer retains all 86,759 training rows, including 14 empty prompts. NFKC, case-folding and whitespace normalization find 47,804 unique prompts. Word 5-shingle MinHash (64 permutations, seed 20261024) retrieves candidates at LSH threshold 0.65; exact Jaccard >=0.85 joins connected components. This produces 47,617 groups, with 16 groups containing conflicting labels. Labels are not rewritten. Approximate lexical retrieval is not a semantic duplication or model-training contamination audit.

Groups are assigned to fitting (69,366 rows), validation (8,700) and internal audit (8,693), balancing predominant label/adversarial/category strata using deterministic quotas. Fixed proportional stratified row samples use stable hash order: pilot 256, search fit 1,024, search validation 512, final internal audit 512. The expanded fitting estimate uses 8,192 rows. Group separation applies across partitions; different fitting samples can overlap. None of these internal partitions is held out from WildGuard's original weight training.

Official WildGuardTest is downloaded only after the policy/settings freeze. Its task population excludes only null prompt-harmfulness labels, following the official evaluation. Original repeated rows remain in the primary row-weighted score. Deduplicated first-row-per-group and no-detected-train-overlap results are sensitivity analyses, not replacements for the official population.

## Policy search

Start with a substantive taxonomy and benign exceptions. Evaluate p0 and two shared candidates on all four policy models. Then evaluate two model-specific candidates per model. The bounded search contains 11 policy files and 20 model/policy combinations, each on the same fitting and validation samples. There are no weight updates, in-context demonstrations, copied training prompts or row-specific exceptions. Only block, allow and precedence rules change; task and output scaffolding remain fixed.

Edits are agent-authored from fitting-error patterns. Aggregate validation scores were visible as work progressed, so validation is selection data, not an independent confirmation set. Validation prompts and individual validation errors were not used to write edits. The original maximum three-round allowance was reduced to one shared and one model-specific round for the budget; this is not an exhaustive search or proof of maximum achievable accuracy.

The shared policy maximizes equally weighted mean validation accuracy across four models. Each model's winner is selected from all five candidates evaluated for that model, including p0. Ties prefer shorter policy text, then lexicographic policy ID. The primary model/policy is the highest validation-accuracy policy-model configuration. Policies, model revisions, source hashes, decoding settings, audit population and optional threshold controls are frozen before official-test access. Identical shared and individual selections reuse predictions.

## Adapters and runtime

One GPU.ai RTX PRO 6000 Blackwell Server with 96 GB memory runs models sequentially. Full dependency freezes, GPU/driver details and launch jobs accompany the evidence. Primary scores use temperature zero and no retries. Dynamic batching can still introduce numerical variation; this is one inference run per unique configuration, not a repeatability study.

| Model | Input and output | Runtime |
|---|---|---|
| WildGuard | Official three-line completion template, empty assistant response; validate all three fields, score prompt field; 128 output tokens | vLLM; original transformers 4.57.6 slow-tokenizer input IDs with one BOS; vocabulary-verified converted decoder |
| PolicyLM-1.7B | Pinned native `PolicyLM` helper; one category, block/allow/exception rules; score >=0.5 | transformers 4.57.6, BF16; upstream cleaning and 2,000-character windows, no character cap, native batch rows 1 |
| Shieldstral-1.0-3B | Document/query/instruction custom-policy template; normalized yes/no token score >=0.5 | vLLM 0.31.0, BF16; one output token |
| CoPE-B-A4B | Policy/content/BLOCK-label template; normalized 1/0 token score >=0.5 | vLLM 0.31.0, BF16; one output token |
| GPT-OSS Safeguard-20B | Policy system message, prompt-only JSON input, binary decision JSON; medium reasoning, 8,192 completion-token cap | vLLM 0.31.0, native MXFP4 checkpoint, TRITON_ATTN and OpenAI reasoning parser |

The score adapters request both label token alternatives explicitly. Their score normalizes the highest log probability for each recognized binary label variant; it is not a calibrated estimate of true harmfulness. HTTP inference uses concurrency 32; native PolicyLM is sequential. Warm-throughput and latency observations are descriptive, not a controlled speed ranking.

Safeguard's pilot showed repetitive generation ending at the token cap. The cap was increased from 4,096 to 8,192 before main search and then fixed for all policies. The original pilot and entire repeated pilot are retained. Root cause is unresolved, so its results describe this deployment; failures cannot establish an intrinsic limitation of the model. WildGuard required a tokenizer compatibility repair before successful inference. Failed setup and download time remain part of compute cost.

## Metrics and controls

Primary metric: accuracy, including failures as wrong. Also report harmful recall, benign false-block rate, harmful F1, macro F1, official-compatible harmful F1, and the full ALLOW/BLOCK/ERROR confusion matrix. In the official-compatible F1, parsing errors are counted as the wrong binary label; the separately reported ordinary class F1 treats ERROR as an additional predicted outcome. These differ when failures occur. Category slices are source-label strata and may contain only one class.

Paired accuracy differences use 2,000 connected-group bootstrap replicates, seed 20261024, sampling groups with replacement and retaining their row counts. Intervals are conditional on the selected policies. The preselected primary comparison is distinguished from exploratory model/policy comparisons; no family-wise correction is applied to those exploratory intervals. One search seed and a small validation sample limit stability claims.

Secondary calibration chooses score thresholds on validation only over 0.01–0.99 in increments of 0.01, with ties closest to 0.5, then lower. Freeze thresholds before test and rescore the same predictions. Report p0 threshold-only and tuned-policy-plus-threshold controls separately; they do not replace the fixed-0.5 primary comparison. WildGuard and Safeguard have no comparable score in these adapters.

## Evidence and limits

Run manifests bind model and policy hashes, dataset hashes, source hashes, settings and source-row IDs. Raw requests/responses and gated text remain in a private archive. Public gzip predictions omit generated reasons, preserve failures and carry checksums; scores can be recomputed without inference or dataset access. The final archive records setup failures, jobs, package versions, cleanup and provider billing.

[Model exposure](MODEL_EXPOSURE.md) documents known training sources and unknown overlap. PolicyLM explicitly lists a source that includes WildGuardMix; exact split exposure is unverified. The other model cards do not establish row-level exclusion. Train/test label provenance also differs: upstream training labels are GPT-4-derived, while test labels use human annotation. Benchmark agreement is not universal moderation correctness. Further datasets, independently reviewed labels, repeated searches and matched fine-tuning baselines are needed before broader causal or deployment claims.
