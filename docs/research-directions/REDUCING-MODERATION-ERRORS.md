# Next steps: reducing moderation errors on unseen examples

**Status: recorded proposal; not started.** The user asked to retain these ideas
and will say when to run them. This document does not authorize model inference,
GPU rentals, API spending, or a new evaluation. It is a research agenda, not a
frozen experimental protocol.

## The question we want to answer

Given labeled examples and a fixed development budget, what complete system makes
the fewest moderation mistakes on new examples? We want to reduce false blocks
of legitimate content and missed violations. Policy text, model choice, internal
representations, score combinations, calibration, and decision cutoffs are tools
toward that goal.

The unit of comparison is the complete configuration: policy, native adapter,
model revision, any learned classifier or combiner, and the final decision rule.
We optimize using training and validation data; the held-out test estimates how
well the selected system generalizes. We do not optimize directly against test
results.

The latest [policy-correction study](../policy-corrections/README.md) answered a
narrower question. We wrote revisions from Shieldstral training mistakes, selected
one using Shieldstral validation, and applied the same text to Qwen. No weights or
learned knowledge moved between models. That transfer result does not establish
the best complete system for either model.

## What the completed work gives us

| Existing result | Why it matters for the next study |
|---|---|
| [PolicyLM representation classifier](../activation-probe/README.md): false blocks fell from 97 to 72 and misses from 131 to 117 relative to its native-score control. | A learned readout can reduce both types of error. It is worth checking whether its information complements stronger models. |
| [Shieldstral representation study](../shield-probe/README.md): the direct score reached 90.53% balanced accuracy, versus 90.39% for its feature classifier and 90.35% for the combined Shieldstral/Qwen feature classifier. | More features and another model are not automatic improvements. Keep strong, simple controls. |
| [Common-validation leaderboard](../leaderboard/README.md): the specialist equal-log-odds ensemble reached 91.08% balanced accuracy on WildGuardTest. | This is an existing system to challenge, not evidence that every new ensemble will help. The gain over the strongest individual specialist remained uncertain. |
| [Decision-model ensembles](../decision-ensemble/README.md): combining Jev, Kev, and Clef did not establish a clear advantage from retaining scores rather than decisions. | Look for useful complementary errors before adding another model or more complex scoring. |

These studies have different development histories and, in some cases, different
validation populations. Their headline results motivate candidates; they are not
a substitute for comparing all new arms under one registered protocol.

## First priority: combine complementary signals

Start with an error-complementarity audit on eligible development examples. When
one component is wrong, how often is another right? Examine both error types and
relevant content slices. Use matching examples across components and keep policy-
development examples out of later combiner evaluation.

Candidate inputs include specialist native scores, a PolicyLM representation
classifier's score, a decision-model score, and a general-purpose LLM score if it
adds useful information. Select a small set from development evidence rather
than including every available model. The existing specialist and decision-only
ensembles remain controls.

Fit a regularized logistic regression on these scores. Compare it with one bounded
nonlinear alternative, such as a shallow gradient-boosted tree model. Remove one
component at a time to measure its contribution. The new question is whether
mixing model families with learned representation scores improves a complete
system; earlier studies combined these sources separately.

Generate out-of-fold predictions for learned component classifiers before fitting
the combiner: each training prediction must come from a classifier that did not
fit that example. Fit feature scaling and other learned preprocessing inside the
same folds. Freeze policies on a separate authoring subset before generating
these predictions, or perform policy development within the appropriate folds.
Otherwise policy search can leak labels even when the classifier fitting is
cross-validated. The [stacking reference](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingClassifier.html)
explains the out-of-fold principle.

An oracle that chooses the correct component after seeing the label can estimate
potential headroom on development data. It is only a diagnostic upper bound,
never a deployable system or a leaderboard result.

## Second priority: optimize policy and cutoff together

Run a bounded, model-specific search rather than assuming one transferred policy
is optimal. Use recurring training errors to propose clarifications, exceptions,
or contrastive examples. Also check correctly classified counterexamples: fixing
one failure must not hide newly introduced mistakes.

Compare each candidate with its own validation-selected cutoff and a fixed-cutoff
control. Keep the intended moderation boundary fixed and document any proposed
scope changes for policy-owner review. Retain the original policy and unsuccessful
candidates. Predeclare the editing budget and stopping rule, and use development
folds to check whether an apparent gain is stable.

The earlier correction study used one round and four appended revisions. This
proposal tests a broader but bounded optimization process. It does not assume
that more rounds, more clauses, or more examples will improve generalization.

## Third priority: a targeted second pass

For uncertain predictions or model disagreements, test whether additional relevant
context helps. One candidate is a second assessment with a few labeled examples
retrieved exclusively from the training set, including legitimate lookalikes and
similar violations.

Choose the routing rule, retrieval method, example count, and second-pass model
using development data. Exclude the query itself and its duplicate group from
retrieval during development evaluation. Freeze the route before testing; test
labels never identify which examples should receive a second pass.

Compare the routed system with the strong single model and full ensemble. Count
corrected errors, newly introduced errors, calls, latency, failures, and cost.
Reconsideration and retrieval are hypotheses to test, not guarantees of better
answers.

This proposed primary comparison still makes an ALLOW/BLOCK decision for every
example. A human REVIEW arm would be a separate operational experiment, with
coverage, reviewer workload, and reviewer errors reported. Reviewed cases cannot
simply be counted as correct classifications.

## Shared evaluation rules to settle before execution

- **Data:** keep duplicate groups and related source examples together. Reserve
  training data for authoring and fitting, validation for selection, and a final
  test for the frozen system. Record all prior uses of candidate examples.
- **Fresh evidence:** official WildGuardTest and HateXplain test sets have been
  examined repeatedly. Preserve them as historical comparisons, but do not call
  another run a new blind test. Identify a genuinely unused project holdout,
  preferably independently human-labeled and representative of the target task.
  Re-splitting previously inspected examples does not erase their prior use.
- **Label provenance:** WildGuardTrain's model-derived labels and the official
  human-labeled test are different evidence sources. The large validation-to-test
  gap in the Shieldstral study motivates checking content and label differences;
  it does not establish their cause. Keep ambiguity visible and never relabel test
  cases to favor a model.
- **Primary objective:** predeclare balanced accuracy, which gives benign and
  harmful classes equal weight. Also report ordinary accuracy, both error rates
  and counts, macro-F1, uncertainty, and relevant content slices. If deployment
  costs or class prevalence motivate a different objective, state it before
  selection.
- **Success:** a reduction in both false-block and miss rates is the clearest
  improvement. If one rises, disclose the tradeoff even when balanced accuracy
  improves. Use paired uncertainty estimates; do not claim a reliable gain from
  a small point-estimate difference alone.
- **Calibration and thresholds:** probability calibration estimates how scores
  relate to observed outcomes; a cutoff chooses when to block. Neither is a
  guarantee of better separation. Fit calibrators on predictions independent of
  component fitting and select thresholds without test labels. See the
  [calibration reference](https://scikit-learn.org/stable/modules/calibration.html).
- **Controls:** compare against the strongest eligible individual configuration
  and existing ensemble under the same new protocol. Preserve frozen historical
  results separately. Show component-removal controls and equal-weight averages
  alongside learned combinations.
- **Training and resources:** keep language-model weights frozen. Learned heads,
  calibrators, and combiners still require labeled data and supervised training.
  Record total compute, API cost, latency, and operational failures; compare an
  open-weight configuration with any API-dependent arm where appropriate.

## Restart checklist — all pending

- [ ] Receive the user's instruction to begin; confirm the applicable compute budget.
- [ ] Audit eligible development predictions and prior-use records.
- [ ] Identify the fresh final evaluation population and its labeling process.
- [ ] Select a small component pool using development errors.
- [ ] Register splits, candidate search limits, metrics, controls, and stopping rules.
- [ ] Run the mixed-signal comparison; retain unsuccessful combinations.
- [ ] Consider policy optimization and a targeted second pass using development evidence.
- [ ] Freeze all final choices before accessing the new test labels.
- [ ] Publish all registered results, uncertainty, cost, and reproducible evidence.

No items have been executed for this proposed program. The immediate next action
is documentation only; execution waits for the user.
