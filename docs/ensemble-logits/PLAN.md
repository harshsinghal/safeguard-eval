# Log-odds ensemble follow-up

Written on 27 October 2026 before this extension is fitted. Earlier probability-space ensemble results and their official test scores are already known. This is an exploratory extension, not a new confirmatory trial or an external preregistration.

## Question and fixed inputs

Does a linear combination of model log-odds perform better than the same type of combination of probability-like scores, when policy texts, model weights, examples, fitting budget and selection rule are held fixed?

Use the immutable `published_runs/2026-10-27-ensemble` scores and the same three cohorts: WildGuard specialists (PolicyLM, Shieldstral, CoPE), HateXplain specialists (PolicyLM, Shieldstral), and the secondary HateXplain mixed cohort (the two specialists plus Qwen 4B). Preserve the prior 4,096 fitting and 1,536 validation examples per benchmark, all duplicate groups and policy/model identities. Official tests retain 1,699 WildGuard prompts and 1,924 HateXplain posts. WildGuard itself remains an external comparator, never an input feature. HateXplain maps hate to BLOCK and offensive/normal to ALLOW.

No policies, model weights, adapters, examples or labels will be changed. No GPU or API inference is needed. Added paid compute is zero; cumulative spend remains $12.50119753456 of $20. This does not count local CPU, researcher or assistant time as zero cost.

## Representation and bounded search

Convert each stored score p to float64 `log(p) - log1p(-p)`. These are reconstructed decision log-odds, not freshly captured full-vocabulary logits or hidden activations. Earlier inspection found all stored valid scores strictly inside (0,1). Reject nonfinite/boundary scores rather than selecting clipping limits using results. Failed model outputs remain failed and are not fitted as artificial scores.

Primary: logistic regression on the log-odds features, with StandardScaler fitted on training only, L2 regularization, and C in [0.01, 0.1, 1, 10, 100]. This matches the prior probability-feature logistic search. The combiner learns an intercept and coefficients; they need not be nonnegative or sum to one.

Controls: fit a single-feature log-odds logistic calibrator for each individual model with the same C grid. Select the strongest individual on validation from the union of these controls and the prior raw, thresholded and probability-calibrated individuals. Retain both old and new individual results so a representation gain is not misattributed to combining models.

One secondary comparator: sigmoid of the equal arithmetic mean of model log-odds, with no learned weights. Tune only its classification threshold. No new forest, mixed-feature, interaction, embedding, weighting or clipping search will be added after results. There are 21 new candidates in each three-model cohort and 16 in the two-model cohort: 58 total.

Select thresholds using the original grid: 0.00 to 1.00 in increments of 0.01, plus 1.000000001 for all-ALLOW. Select by validation accuracy, then macro-F1, threshold nearest 0.5, lower threshold and lexical candidate ID. Keep the prior probability-space primary and previously selected ensemble as frozen references; do not select them again on test. Fit only on training. Do not refit on validation.

## Freeze, evaluation and reporting

Verify the prior evidence checksums. Register the source and input hashes. Freeze all three cohorts' new fitted objects, training transforms, coefficients, thresholds, selections, policy identities and code hashes before running this extension's test evaluation. Copy test inputs only after every cohort is frozen. Preserve the prior study unchanged.

Primary comparisons: selected log-odds logistic ensemble versus (a) the prior probability-feature logistic ensemble and (b) the strengthened validation-selected individual. Also report the prior selected individual and prior selected ensemble, and the external WildGuard model where applicable. The equal-log-odds method is secondary. Any best observed test result across methods is descriptive, never a new selected winner.

Report accuracy, macro-F1, violation F1/recall, false blocks, missed violations, errors and calibration metrics. Retain all candidate results and individual controls. Use the same 2,000 paired duplicate-group bootstrap replicates for differences in accuracy and macro-F1. Intervals are unadjusted and descriptive; they do not capture policy/model selection, unknown benchmark exposure or inference uncertainty. Inspect selected-model category, platform and agreement slices, but do not tune on them.

Reproduce all 58 new fits, validation choices, test metrics and registered intervals on CPU from a prompt-free evidence archive. Include software tests for the transform, identity with binary label-log-probability differences, boundary rejection, failed-member handling, training-only scaling, and frozen selection integrity.

## Interpretation for the broader research

We are testing adaptation without additional language-model weight updates by the deploying team. The policy models themselves were trained by their creators. The ensemble and calibrators are still supervised learned models and require labels. Policy authoring, calibration and ensembling are distinct sources of change; this extension isolates the score representation with policy text fixed.

Competitive benchmark performance would support a practical route using released models, policy text, labeled evaluations and lightweight calibration/combining. It would not establish that fine-tuning is unnecessary, that this approach is easier or cheaper in total, or that it matches the best achievable task-specific model. We did not run a matched fine-tuning baseline or measure human effort, and benchmark reuse/pretraining exposure limit claims.

Progress is tracked in README.md, NOTES.md and progress.json. This original plan will remain unchanged after registration.
