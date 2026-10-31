# Learning which moderation models complement each other

Registered before new inference, combiner fitting, or evaluation on 31 October
2026. This is a local protocol for an exploratory extension, not an external
preregistration. Preserve this plan; record amendments separately.

## Question and scope

Can a small learned combination of specialist, general-purpose, and decision-model
scores reduce moderation errors compared with a strong individual and existing
ensemble controls? Models enter the combination because they improve development
predictions together, not simply because they belong to different families.

This study changes only the score combiner and decision cutoff. Policies and
language-model weights remain frozen. It does not execute the proposed policy
optimization, representation-head stacking, or targeted second-pass experiments.
The candidate pool is bounded by existing comparable evidence and budget; it is
not every model or every policy tested in the repository.

## Data and frozen components

Reuse the group-disjoint 4,096 fitting and 1,536 validation examples per benchmark
from the first ensemble study. They exclude that study's prior policy-development
examples. Verify that the original Jev/Kev/Clef fitting and validation groups,
including examples used in their authored policies, do not overlap these new
development populations. All continuous scores must align exactly by ID, content
hash, label and duplicate group; no inner joins that silently remove cases.

| Benchmark | Candidate score sources | Final test |
|---|---|---|
| WildGuard prompt harmfulness | PolicyLM 1.7B, Shieldstral 3B, CoPE, Qwen3.5 4B, Jev 1.14, Kev 4B, Clef-Flash 9B | 1,699 labeled WildGuardTest prompts |
| HateXplain, hate versus non-hate | PolicyLM 1.7B, Shieldstral 3B, Qwen3.5 4B, Jev 1.14, Kev 4B, Clef-Flash 9B | All 1,924 official test posts |

Reuse native specialist and HateXplain Qwen scores and policies from the first
ensemble archive. WildGuard Qwen uses the direct conditional A/B score with the
fixed Shieldstral policy from the Shieldstral representation study, consistently
across fitting, validation and test. This is one available general-purpose-model
configuration, not a claim to its optimal prompt. It is not a trained feature head.
The registration records exact policies, revisions, adapters, and score semantics.

For both datasets, Jev uses its earlier balanced-validation-selected detailed
policy, Kev its brief policy, and Clef its example-bearing policy. These choices
were made on the original decision-study validation populations, which are excluded
from this study's fitting and validation. Generate missing development scores
using the same pinned native interfaces; reuse their archived test scores only
after the new final selections are frozen. Validate new-versus-archived scoring on
small original-development canaries before bulk inference. No test canaries.

WildGuardTrain labels are model-derived; the official test labels are human
annotations. HateXplain uses its existing binary label mapping. Both official test
sets have been repeatedly examined by this project. They are held out of the new
combiner's fitting and selection but are not fresh blind tests. No independent
human-labeled holdout is commissioned in this bounded study. Results are
exploratory and must not be presented as new independent confirmation.

## Training-only model selection

Use seed 20261031 and five stratified group-disjoint fitting folds. The only inputs
are frozen BLOCK scores; labels, categories, text and provenance metadata are not
features. Native scorers are already fixed and were not fitted on these development
labels. Every new scaler and classifier is fitted inside its training fold when
producing out-of-fold predictions. A final deployable classifier is then fitted on
all fitting rows, without validation or test refitting.

The primary method is forward selection with logistic regression on clipped
log-odds. Clip probabilities to [1e-6, 1-1e-6], standardize with fitting-only
statistics, and use L2 logistic regression with class_weight='balanced', C in
[0.01, 0.1, 1, 10], and max_iter=2000. These are reconstructed binary log-odds,
not full-vocabulary raw logits or guaranteed calibrated probabilities.

Start with the single component having the highest pooled out-of-fold balanced
accuracy. At each step, try adding each remaining model, refit coefficients and
select C and the exploratory OOF cutoff using the registered grid. Add the best
candidate only if it improves OOF balanced accuracy by at least 0.002 (0.2 points).
Stop at four components or when no addition meets that rule. A one-model outcome
is allowed. Break ties deterministically by balanced accuracy, the lower of the
two class recalls, macro-F1, smaller C, and sorted component names. Log the complete
search path, including rejected additions. The OOF score is a selection statistic,
not an unbiased final result after searching subsets and hyperparameters.

Before looking at validation or test outcomes, report fitting-only correlations,
error overlap, and directional rescue counts from OOF individual classifiers.
Disagreement alone is insufficient: an added model must improve joint predictions.
An oracle selecting the correct component using the true label is only a diagnostic
upper bound on development data; never report it as deployed accuracy.

## Controls and bounded alternatives

Apply the same forward-selection algorithm to an open-weight-only pool (excluding
Jev), specialist-only pool, and decision-only pool. Other controls are:

- Logistic regression on all candidate log-odds, with C chosen on fitting OOF.
- Equal raw-probability and equal log-odds averages of all candidates; an equal
  log-odds average of the specialist pool, corresponding to the earlier strong
  WildGuard method but with the new study's validation-selected cutoff.
- One nonlinear alternative on all raw scores: histogram gradient boosting with
  depth 2, 100 iterations, learning rate 0.05, minimum leaf size 40, L2=1, balanced
  class weights, early_stopping=False. No further nonlinear architecture search.
- Each individual raw score and its one-feature logistic control; the best
  individual is chosen on validation, never by its test score.
- Remove each selected component from the primary combination in turn, refit on
  fitting data and choose C by the same OOF procedure. Record those component
  ablations even if they appear worse. Skip an empty combination.

Coefficients are conditional contributions in a correlated score model, not causal
importance or percentages. Report signs, scaling and intercept, plus actual changes
in error counts. Standard logistic coefficients may be negative. Do not force a
representative from every family or discard a weak individual merely because its
standalone accuracy is lower.

## Validation, freeze, and final evaluation

Use the existing leaderboard's threshold grid (0 through 1 in steps of .01, plus
an all-ALLOW endpoint) and deterministic profile rules. The primary objective is
balanced accuracy. Each selected method gets its own validation-selected cutoff;
native individual decisions are also controls. Freeze separate 5% compliant-error
and 90% violation-catch profiles and report whether they hold on test.

Keep unresolved scores explicit. A combination requires its own component scores;
an unrelated model's failure must not invalidate a single-model decision. Exclude
incomplete fitting rows per fitted subset and report counts. If new inference
fails, stop and resolve implementation issues instead of silently dropping models
or examples. Retain genuine context/decision failures as unresolved test errors.

Freeze the protocol, source hashes, native input scores, fitted objects, component
selection, coefficients, validation outputs, cutoffs and software environment
before accessing the new experiment's test outputs. The preflight may inspect
archive schemas and hashes, but no test outcome is used to choose the system.
Evaluate all registered methods once; do not replace a selected configuration after
seeing test results.

Primary paired contrasts: selected mixed ensemble versus (a) validation-selected
best individual and (b) specialist equal-log-odds control. Secondary contrasts
include all-model logistic, open-only, decision-only and component-removal controls.
Keep the earlier common leaderboard and released WildGuard model as contextual
historical references, without silently mixing their validation protocols.

Report balanced/ordinary accuracy, macro-F1, MCC, both error counts and rates,
coverage, AUROC, average precision, Brier score and log loss. Report category slices
with counts, and 2,000 paired duplicate-group bootstrap intervals. Intervals are
exploratory, unadjusted, and conditional on frozen outputs; they exclude policy
search, labeling and model-training uncertainty. A higher aggregate score may
still trade false blocks for misses. Highlight reductions in both separately.

## Cost and reproducibility

The latest cumulative provider spend is $15.26540555656 of the authorized $20 cap,
leaving $4.73459444344. Reserve at most $1 for new Jev API calls and $2.40 for a
three-hour GPU run at no more than $0.80/hour with no additional storage charge.
GPU.ai is first choice, RunPod a fallback within the same budget. Never raise the
cap implicitly. Reconcile billing and terminate resources after collection.

Publish prompt-free scores, metadata, exact policies, source snapshots, frozen
selections, search traces, coefficients, results, all negative findings, and CPU
reproduction instructions. Keep source prompts and credentials private. Preserve
older evidence bundles and leaderboard selections unchanged. No backbone weights
are fine-tuned; fitting the ensemble is still supervised learning.
