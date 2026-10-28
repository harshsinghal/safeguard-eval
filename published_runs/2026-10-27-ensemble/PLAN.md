# Ensemble study: frozen policy interpreters

Registered 27 October 2026, before ensemble fitting or test evaluation.

Question: can a learned combination of fixed policy-model scores improve on a
validation-selected, calibrated individual model? WildGuard itself is an external
comparator. Language-model weights, selected policy texts and native adapters stay
fixed. Training a small combiner is supervised learning and requires labeled data.

## Registered comparisons

- WildGuard specialists: PolicyLM p4, Shieldstral p4 and CoPE p3 from the original
  WildGuard study. WildGuard is excluded from ensemble inputs.
- HateXplain specialists: PolicyLM p0 and Shieldstral p2, selected in the prior study.
- Secondary HateXplain mixed ensemble: the same two specialists plus Qwen 4B p1.
- Safeguard is excluded from this numerical-score study because its archived
  interface supplies categorical decisions, not numerical scores. No confidence
  scores will be invented. A categorical-input extension is deferred.

Each cohort includes raw single models at 0.5, validation-thresholded singles,
single-feature logistic calibration controls, an equal raw-score average, an equal
calibrated-score average, a learned nonnegative weighted average, regularized
logistic stacking, and a shallow random forest. The primary ensemble is logistic
stacking. A separately reported best ensemble is selected on validation only.
Every registered method is reported, including negative results.

## Separation and data

Audit and reuse cached scores only where they were not used to edit/select the
underlying policies. Exclude earlier fitting, demonstration, validation and audit
groups. For WildGuard, use the previously scored 8,192-row final-fit population,
excluding development groups from all prior WildGuard-based studies and known
train/test overlap groups. If fewer than 5,632 eligible rows remain, allocate 75%
of the eligible groups to fitting and 25% to validation with a fixed seed.
Otherwise target 4,096 fitting and 1,536 validation rows, keeping groups whole.

For HateXplain, reconstruct the pinned official training population and the
existing exact/near-duplicate groups. Exclude all previously used fitting,
demonstration, validation and test groups. Select 4,096 fresh fitting and 1,536
fresh validation rows by deterministic, stratified group sampling. Obtain missing
scores using the same pinned checkpoints, policy bodies and native adapters.
No official-test content needs new GPU inference.

Use seed 20261027. All models must have identical unique example IDs, text hashes,
labels and group metadata within a comparison. No demographic, category, target,
annotator or source label metadata enters the feature matrix: only model scores.
All development exclusions, hashes and actual counts are recorded before fitting.
The official tests retain 1,699 usable WildGuard harmfulness labels and 1,924
HateXplain posts. HateXplain maps hate to BLOCK and offensive/normal to ALLOW.

## Fitting and selection

Fit on ensemble-training only. Logistic stacking uses standardized raw scores,
L2 regularization and C in [0.01, 0.1, 1, 10, 100]. Use the same grid for each
single-feature logistic control. Fit independent C=1 sigmoid calibrators on raw
scores for soft averaging; train weighted averaging on five-fold grouped
out-of-fold calibrated scores, then apply full-training calibrators at inference.
This cross-fitting concerns calibration, not language-model retraining.

Weighted averaging minimizes training log loss with nonnegative weights summing
to one, plus squared distance from equal weights with strength [0, 0.01, 0.1].
Random forest uses 300 trees, max_depth [2, 4], min_samples_leaf [20, 80], fixed
seed and no class reweighting. No content embeddings, extra model features,
new policy search or wider hyperparameter search will be added after results.

Select thresholds on ensemble-validation from 0.00 to 1.00 in steps of 0.01,
plus 1.000000001 for an all-ALLOW control. Optimize accuracy, then macro-F1,
then threshold nearest 0.5, then lower threshold, then lexical candidate ID.
Select hyperparameters and the strongest individual with the same validation
objective. Keep all training fits and validation candidate scores.

Before test evaluation, save a freeze binding model objects, coefficients,
calibrators, thresholds, selected IDs, source code, policies and development-data
hashes. Never refit on validation or test. Test results do not select methods.

## Evaluation

Primary metric: accuracy. Also report binary macro-F1, harmful/hate F1 and recall,
false blocks, missed violations, confusion matrices, score log loss/Brier score
and inference failures. Errors count incorrect; do not silently discard failed
examples. If a required base output fails, the ensemble result is ERROR. Training
failures are excluded explicitly and counted, never converted to valid scores.

Use 2,000 paired group-bootstrap replicates for accuracy and macro-F1 differences
against the validation-selected calibrated single, and against WildGuard where
applicable. Report corrected and newly wrong cases. The highest observed test
score among registered singles is a descriptive extra hurdle, not a selector.
Intervals are descriptive, unadjusted, and exclude policy-search/inference
uncertainty. The primary specialist comparisons are identified explicitly.

Inspect complementary errors on development data first. On test, report agreement,
shared mistakes and an explicitly non-deployable hindsight oracle diagnostic.
Slice WildGuard by category/adversarial status and HateXplain by original label,
platform and annotation agreement. Compare improvements with the number of model
calls and archived timing, without claiming a production latency/cost benchmark.

## Scope and budget

These are exploratory follow-ups: earlier official test results are already known.
Fresh ensemble-development rows do not make reused tests wholly unseen, and
upstream checkpoint exposure to public benchmarks is unknown. We do not claim
enterprise accuracy, hidden-intent detection or validated REVIEW routing.

Prior cumulative spend: $12.12119753456. Cumulative authorization: $20.
Remaining: $7.87880246544. Plan at most one two-hour GPU rental at <=$1.99/hour,
with no storage surcharge and provider automatic termination, reserving at most
$3.98. GPU.ai first, RunPod fallback under the same cap. Verify live pricing and
credit before provisioning, collect evidence, terminate, and reconcile billing.

## Progress checklist

- [ ] Audit cached scores and exclude previously used groups.
- [ ] Prepare and hash fresh HateXplain development partitions.
- [ ] Implement and test fitting, freeze, evaluation and reproduction.
- [ ] Score missing development rows with pinned models.
- [ ] Fit/select each cohort and freeze before test scoring.
- [ ] Evaluate complete official tests and paired uncertainty.
- [ ] Publish prompt-free evidence and readable findings locally.
- [ ] Reproduce results on CPU and reconcile/terminate compute.
