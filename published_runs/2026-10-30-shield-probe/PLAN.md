# Shieldstral and Qwen: do hidden representations add value?

Status: registered before new inference or classifier fitting. This is the first
of two approved experiments. The [training-error correction study](../../docs/research-directions/TRAINING-ERROR-CORRECTIONS.md)
is recorded for later and is not part of this run.

## Question and controls

Can a supervised classifier on frozen Shieldstral-1.0-3B and Qwen3.5-4B
representations improve harmful-prompt classification over either representation
alone and over combining their two output scores? This is predictive evaluation,
not a mechanistic explanation of policy understanding. A trained head needs
labeled data even though language-model weights and policy text remain fixed.

Primary representations are Shieldstral's final answer-position hidden vector
(3,072 values) and Qwen's final-layer submitted-content mean (2,560 values).
Their concatenation has 5,632 values. Primary comparisons are the two individual
linear probes, the concatenated probe, each model's direct label score with a
validation-selected cutoff, and a logistic combination of the two label log-odds.
Unweighted probability and log-odds averages are simple score-only controls.
The combined probe must beat the validation-selected stronger single probe and
the learned score combination to establish its proposed extra value.

## Fixed models, policy and adapters

* Shieldstral: `mistralai/Shieldstral-1.0-3B`, revision
  `003ec7e2b0bab5f0e6307edbaf186fa5822b76f5`, 26 text blocks, width 3,072.
* Qwen: `Qwen/Qwen3.5-4B`, revision
  `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, 32 text blocks, width 2,560.
* Both are BF16 frozen checkpoints, text-only, evaluation/inference mode, no
  optimizer on language-model parameters and no generated reasoning or answers.
  Published names describe approximate language-model sizes; complete checkpoints
  include multimodal components (3,849,090,048 and 4,659,865,088 parameters).
* Both use the exact previously selected Shieldstral harmfulness policy at
  `published_runs/2026-10-27-ensemble/policies/wildguard/shieldstral.json`.
  No policy candidate search or error-based edits in this experiment.
* Shieldstral retains the existing native system message and
  `<Instruct>/<Query>/<Document>` adapter in `evals.run.build_payload`, including
  JSON-quoted submitted content. Qwen retains `evals.qwen_policy.run.render`,
  the native chat template with thinking disabled, and raw submitted content as
  the user message, following the same task framing as the preceding representation experiment.
  Honor the pinned Qwen template's trimming of outer content whitespace.
* Native-score controls read the exact canonical yes/no (Shieldstral) or B/A
  (Qwen) single-token logits at the answer position and normalize those two values.
  These are conditional two-label scores, not calibrated risk probabilities or
  free-generation accuracy. Save token IDs, raw margin and top-token diagnostics;
  do not silently omit a case because another token has the highest logit.

## Populations and leakage limits

Reuse the exact earlier probe populations: 4,096 fitting, 1,536 validation and
1,699 labeled WildGuardTest prompts (945 ALLOW, 754 BLOCK). Identifiers, text
hashes and recorded duplicate groups must be disjoint. Preserve earlier overlap
exclusions and the 26 unlabeled test exclusions. Only prompt text is classified,
not assistant responses. Extractors receive label-free input files; metadata
labels are available only to fitting/selection/scoring code. Preserve population
hashes and authorized source restoration instructions from the previous study.

Test inputs are uploaded only after the new pre-test freeze. The public test and
these development populations have been examined in previous studies: this is an
exploratory replication with a new freeze, not an untouched blind evaluation.
It does not establish generalization to HateXplain or to newly edited policies.

## Features and registered search

Primary: final Shieldstral layer 26, last input/answer position; final Qwen layer
32, content mean. Secondary: Shieldstral layers 13, 20, 26 and Qwen layers 16,
24, 32, each with content mean or final input token. Content means exclude policy,
template and padding; Shieldstral pools the serialized document including JSON
quotes. Empty Qwen content means use a zero vector, retaining the original row.
Earlier layers are block outputs; final layers include native final normalization.
Layer numbers do not identify equivalent computations across architectures.

No truncation. Inputs exceeding 8,192 tokens are unresolved and retained in all
denominators. Unexpected runtime/shape/masking errors stop the run for a recorded
technical repair, rather than silently dropping examples. Validate tokenization,
content spans, finite shapes, frozen gradients and answer-score parity with full
native forward passes on 16 fitting examples before full extraction. Direct head
projection versus full forward score tolerance is 0.002 in probability, with
actual differences reported. Cache float32 representations privately.

Fit StandardScaler on fitting rows only; L2 logistic regression, no class weights,
intercept, C in [0.0001, 0.001, 0.01, 0.1, 1], lbfgs, max_iter 3,000, tolerance
1e-6, seed 20261030, two BLAS threads. Nonconverged fits are invalid, not winners.
At most 70 representation fits: 60 individual layer/pooling fits plus five primary
combined and five secondary combined (reuse identical candidates). Select each
secondary individual representation on validation, then combine those two; do
not search their full cross-product. Add five logistic score-combination fits.
For score features/averages, clip conditional probabilities to [1e-6, 1-1e-6]
before converting to log-odds. No other feature types or learned algorithms.

Use existing leaderboard balanced-accuracy selection and deterministic tie rules,
with cutoff grid 0..1 by .01 plus 1.000000001. Also freeze separate operating
profiles for at most 5% false blocks and at least 90% harmful recall on validation.
Retain both individual score controls at cutoff 0.5 for context. Do not select or
retune on test. Freeze code, policy, input hashes, coefficients, scalers, chosen
representations and cutoffs before test extraction. Do not refit on validation.

## Results and interpretation

Report all registered selections, including negative findings. Primary metric is
balanced accuracy, supported by ordinary accuracy, macro-F1, MCC, both error
counts/rates, recall, specificity, AUROC/AP, calibration diagnostics, unresolved
coverage and pre-existing category/adversarial slices. Use 2,000 paired bootstrap
draws over recorded duplicate groups (seed 20261029); intervals are descriptive,
unadjusted for search, repeated public-test use or multiple comparisons.

Prespecified paired contrasts: primary and secondary combined probes against
each other and all other reported configurations; individual primary probes
against their own score controls. Report corrected errors and new errors as well
as the balanced-accuracy difference. Include archived WildGuard and specialist
score ensemble as historical context with different earlier validation procedures.
Keep this 1,536-row validation study separate from the common-512 leaderboard.

An improved cutoff does not imply improved ranking; check AUROC and operating
profiles. A better head does not show that it follows policy changes. Combined
representations require both encoders at deployment. Record extraction latency,
memory, environment, all failures and compute cost, without calling them matched
production-serving benchmarks. Reproduce every fit and metric from cached evidence.

## Budget and completion

Prior cumulative spend: $14.17540555656 of $20; remaining $5.82459444344.
Use GPU.ai first, RunPod fallback within the same cap. Reserve no more than
$2.40 for a single three-hour rental at <=$0.80/hour including disk, with provider
auto-termination. Verify available credit, actual price and no existing jobs.
Collect caches, terminate the GPU, confirm termination, remove temporary SSH
credentials and reconcile billing before final reporting. Perform optional CPU
analysis locally after terminating paid compute.

Completion is tracked separately in `progress.json`. Publish a readable report,
README entry, full metrics, training/selection records, fitted coefficients,
prompt-free predictions, code snapshots, runtime/cost records and checksums.
Keep prompts and embeddings private. Do not overwrite earlier evidence archives.

References: [Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[Qwen](https://huggingface.co/Qwen/Qwen3.5-4B),
[WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix),
[preceding representation study](../../docs/activation-probe/README.md).
