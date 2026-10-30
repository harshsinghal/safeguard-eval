# Frozen representations: can a small generalist complement PolicyLM?

Registered before feature extraction, fitting, or new test evaluation.

## Question and scope

For WildGuard prompt harmfulness, can a logistic regression trained on the
concatenation of Qwen and PolicyLM hidden representations improve on the same
classifier trained on either representation alone? These are supervised,
task-specific classifiers. Both language models remain frozen. This is not a
training-free method, a new policy-authoring result, or a mechanistic explanation.

Use Qwen/Qwen3.5-0.8B, revision
`2fc06364715b967f1860aea9cf38778875588b17`, and musubilabs/policylm-1.7b,
revision `b3b2cd408a08a68ab6a30c1fc1e440204e44d57e`. Qwen3.5's small checkpoint
is 0.8B; Qwen3-0.6B and Qwen3-Embedding-0.6B are different models. Text only.
No new policy search: reuse PolicyLM p4 from the original WildGuard study, in
PolicyLM's native Category interface and the existing Qwen system-prompt renderer.

## Data and safeguards

Reuse the first ensemble study's exact 4,096 fitting / 1,536 validation rows,
whose duplicate groups excluded prior policy-development and known test overlap.
Use all 1,699 labeled WildGuardTest prompts (754 harmful / 945 benign); exclude
the same 26 unlabeled records as earlier studies. Verify identifiers, text hashes,
labels, groups, and source hashes against frozen archives. Save assignments and
assert disjoint identifiers, text hashes and duplicate groups across splits.
Only prompt text and the fixed policy enter the language models. Labels enter
classifier fitting or scoring only. Dataset categories, adversarial flags and
other metadata never enter features. Test labels are never selection inputs.

These populations and public test results have been examined in prior studies.
This is an exploratory follow-up with a new pre-test freeze, not an untouched
blind benchmark. Upstream exposure of checkpoints to public data is unknown.

## Representations

Extract activations in inference/evaluation mode, bf16 model weights, no generation
and no weight updates. Cache pooled vectors in float32; record checkpoint,
tokenizer, policy, adapter, environment and artifact hashes.

* Qwen: hidden-state tuple indices 12, 18 and 24 (half, three-quarter and final
  depth). Pool either the mean of tokens overlapping the submitted user-content
  span, excluding policy, template and padding, or the final input token. Use
  its native chat template with thinking disabled. No truncation: over 8,192
  tokens is an explicit unresolved extraction. Batch size one initially.
* PolicyLM: tuple indices 14, 21 and 28. Pool either the single native category
  `[L]` position, or the mean of content tokens after the compiled policy prefix.
  Preserve upstream cleaning, 2,000-character windowing, and max_batch_rows=1.
  Average pooled vectors equally across all native windows and cleaning variants
  for each original message. Never turn windows into separately labeled samples.
  Preserve and also record the unmodified native maximum-window category score.
* Intermediate indices are outputs after that many blocks; final output includes
  final normalization. Layer numbers are architectural locations, not equivalent
  computations between these different model architectures.
  PolicyLM uses read-only block hooks at the same depths because its released
  optional hidden-state path fails on a batch-dimension bug. Match its native
  MNTP output alignment exactly, including its shifted positions; do not change
  the pretrained head's slot alignment. This technical amendment preceded fitting.
* Concatenate per-example vectors; never average coordinates from different models
  or average all positive/negative examples into class centroids.

Confirm shapes, finite values, masking, no gradient computation, and native
PolicyLM score parity with/without extraction hooks on 16 fitting examples.
Technical fixes can be made before fitting and recorded; search choices cannot
be expanded after outcomes. Never drop a failed test example. A failure in either
input makes the combined prediction unresolved; count it as incorrect.

## Registered comparisons and selection

Primary features: Qwen final-layer content mean (1,024 values), PolicyLM final
category slot (2,048 values), and their concatenation (3,072 values).

Primary comparisons: each single-model probe, the combined probe, and PolicyLM's
native score with a validation-selected cutoff. Also retain its fixed 0.5 cutoff
for continuity with earlier runs. Compare the combined probe with the
validation-selected stronger single probe and with both singles individually.

StandardScaler and L2 logistic regression fit on fitting rows only, with intercept,
no class weighting, C in [0.0001, 0.001, 0.01, 0.1, 1], deterministic lbfgs,
max_iter=3000, tol=1e-6. Treat convergence failure as an invalid candidate.
Threshold grid 0..1 by .01, plus 1.000000001. Choose balanced accuracy; break
ties by larger minimum class recall, macro-F1, proximity to .5, lower threshold,
then lexical candidate identifier. Also freeze separate operating points for
at most 5% false blocks and at least 90% harmful recall on validation.

Secondary search: six representations per model (three layers x two poolings),
each with the same five C values. Choose one representation and C per model
on validation, concatenate those two chosen representations, and fit the same
five C values. Do not test all cross-products or expand the grid. Primary
single fits are reused within the secondary search. At most 70 probe fits,
including the five primary and five secondary combined fits. Report all
validation candidates, all primary/secondary selected methods and negative results.

Freeze choices, thresholds, coefficients/scalers, code, data, policy and feature
hashes before test extraction/evaluation. Do not refit on validation. Select no
method from test results. Test extraction can compute registered layers, but
evaluate only frozen configurations.

## Reporting

Primary metric balanced accuracy. Also accuracy, macro-F1, MCC, harmful recall,
specificity, false blocks/misses with denominators, AUROC/AP, unresolved coverage,
Brier/log loss and predefined category/adversarial slices. Use 2,000 paired
duplicate-group bootstrap replicates for confidence intervals and differences.
Intervals are descriptive, unadjusted for multiple comparisons, and exclude
feature/model/policy-search uncertainty. The strongest observed test method is
not promoted as the primary result.

Compare with archived WildGuard and the earlier specialist score ensemble as
context, explicitly identifying differing validation objectives/populations.
Record extraction runtime, memory and input/window counts; these are experiment
measurements, not production latency or provider recommendations. Combined
features require two encoders at serving time. A useful result must justify
that extra cost and improve on the single-feature controls, not just on a native
head. Success on one fixed policy does not demonstrate adaptation to new policies.

## Budget and deliverables

Prior cumulative paid spend $13.79540555656; cumulative cap $20; remaining
$6.20459444344. One GPU.ai RTX6000 Ada at <=$0.65/hour, no disk surcharge,
provider auto-termination <=3 hours reserves at most $1.95. RunPod is a fallback
only within the same remaining cap. Verify actual price, credit and termination;
reconcile usage. Download caches before terminating. CPU classifier fits may run
locally without retaining a GPU. No new API classification charges.

Maintain this plan, progress, implementation notes, readable findings, source
snapshots, checksummed prompt-free predictions, coefficient artifacts and CPU
reproduction. Keep licensed source prompts and potentially reconstructable
embeddings in private local caches. Publishing predictions permits metric
reproduction; refitting additionally requires locally regenerated cached features.
Do not overwrite earlier immutable archives or paper releases.

## Progress

- [ ] Audit and prepare pinned populations and policy.
- [ ] Implement extraction, fitting, freeze, evaluation and meaningful tests.
- [ ] Verify extraction on fitting-only smoke examples.
- [ ] Extract development features and fit/select on validation.
- [ ] Freeze, extract test features and report all registered comparisons.
- [ ] Reproduce, document, publish evidence, terminate and reconcile compute.

References: [TaskTracker](https://github.com/microsoft/TaskTracker),
[paper](https://arxiv.org/abs/2406.00799),
[Qwen](https://huggingface.co/Qwen/Qwen3.5-0.8B),
[PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b),
[WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix).
