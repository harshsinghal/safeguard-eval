# How the smart ensemble works

Each model reads a fixed policy and the same piece of content, then supplies a
BLOCK score. A small logistic regression learns how to combine those scores.
It can give one model more influence, use another to correct it, or leave a
model out. It does not read the content itself.

The experiment asks whether the combination makes fewer moderation mistakes,
not whether every family deserves a place in the system.

## Three separate stages

1. **Fit and choose components on 4,096 training examples.** Split duplicate
   groups into five folds. For each candidate combination, fit on four folds
   and predict the fifth. Start with the strongest single component in these
   out-of-fold predictions. Add a model only if the refitted combination improves
   balanced accuracy by at least 0.2 percentage points. Stop at four models.
   Try four predeclared regularization strengths at each step.
2. **Choose operating cutoffs on 1,536 validation examples.** Fit the chosen
   combination on the fitting population. Use separate validation examples to
   choose when its score becomes a BLOCK. Freeze the components, coefficients,
   cutoff, inputs and code. Do not refit on validation.
3. **Evaluate the frozen systems on the official tests.** WildGuard has 1,699
   labeled prompts; HateXplain has 1,924 posts. Report false blocks, misses and
   balanced accuracy together, with paired uncertainty intervals.

These official test sets have already been used elsewhere in the project. They
are excluded from this new fitting and selection, but they are not fresh blind
tests. The fitting and validation populations also exclude the earlier decision
models' policy-development groups. The registration preserves that audit.

## What enters the equation

WildGuard uses PolicyLM, Shieldstral, CoPE, Qwen3.5-4B, Jev, Kev and Clef. HateXplain
uses the same pool without CoPE. Policies and backbone weights stay fixed. This
is a comparison of particular model-policy configurations, not every model in the
repository at its best possible setting.

The equation uses each model's binary log-odds: a transformation of its BLOCK
score. Scores are clipped away from zero and one. A scaler learned only from
fitting rows prevents a model's numerical range alone from determining the fit.
The final published coefficients are converted back to the log-odds scale so
the equation can be reconstructed directly.

Coefficients are not percentages. They depend on the other models in the
combination; correlated models can share influence or receive a negative
coefficient. Removing a component and refitting is a more useful check of its
contribution than reading its coefficient alone.

WildGuard's Qwen input is its direct conditional A/B score under the fixed
Shieldstral policy from the representation study. It is not the trained
representation classifier, and is not a claim to Qwen's optimal prompt.

## What makes this more than an average

Training-only diagnostics count when one model corrects another's false blocks
or misses, and when both are wrong. Disagreement alone does not qualify a model
for inclusion: adding it must improve the fitted combination's out-of-fold
balanced accuracy.

The search is bounded and greedy. It does not promise the globally best subset;
two useful models might only help when added together. We therefore also retain
an all-model logistic regression and one fixed shallow gradient-boosting control.
Other controls include equal averages, single models with and without logistic
rescaling, specialist-only and decision-only selection, and an open-weight-only
pool excluding the Jev API. Every registered result is reported.

The fitting score used to search these options is optimistic after selection.
Only the frozen test comparison estimates performance beyond that selection,
subject to the reused-test limitation above.

## What counts as success

Balanced accuracy gives equal importance to correctly allowing benign content
and catching violations. A gain can still conceal a tradeoff. We report the
actual number of false blocks and missed violations, and explicitly check whether
both fall. Paired duplicate-group bootstrap intervals compare methods on the
same cases.

Two additional validation profiles target a 5% compliant-error limit or 90%
violation recall. We report whether those targets survive on test; choosing a
validation cutoff is not a guarantee about deployment.

Scores are not assumed to be calibrated probabilities. The one-feature logistic
controls rescale scores using balanced class weights; they do not establish
population-probability calibration. AUROC, Brier score, log loss, coverage and
content slices accompany the classification metrics.

An empty WildGuard fitting prompt is retained as unresolved for the three decision
models. Only combinations requiring those scores exclude it during fitting.
Unresolved evaluation cases count as errors, not free correct answers.

## What this experiment does not establish

We do not know which examples each provider used to train its model, so different
error patterns cannot establish a training-data explanation. We do not fine-tune
backbone weights, rewrite policies, add representation heads, or run a second-pass
classifier. The combiner itself is supervised learning and needs labeled examples.

Jev returned slightly different scores for identical historical requests. Its
development outputs are therefore recollected, and its full test outputs are
requested only after freezing. The intervals are conditional on those outputs;
they do not measure API variability. Kev and Clef must pass development canary
checks before reusing their archived test outputs.

See the [registered plan](PLAN.md), [preflight amendments](AMENDMENTS.md), and
[implementation](../../evals/smart_ensemble/).
