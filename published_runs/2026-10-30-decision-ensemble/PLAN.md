# WildGuard ensemble of native decision-model scores

Registered October 30, 2026, before fitting or evaluating this extension. This
is a local exploratory protocol, not an external preregistration. Earlier public
test results are already known. Preserve this plan; record amendments separately.

## Question

Can combining the native BLOCK scores from Jev, Kev, and Clef improve harmful
prompt classification over a validation-selected individual decision model?
Does using scores help compared with combining only their discrete decisions?
Also test a self-hostable ensemble containing only Kev and Clef.

This experiment changes the score combiner. It does not update language-model
weights, author new policies, rerun model inference, or request self-reported
confidence from a chat model. Native classification probabilities were already
saved in the October 29 studies. They are not assumed to be calibrated estimates
of real-world risk.

## Inputs and scope

Use the immutable October 29 Jev and Kev/Clef archives, with their exact model
revisions and native interfaces. Reuse the shared WildGuard partitions:

| Stage | Examples | Purpose |
|---|---:|---|
| Fitting | 1,024 WildGuardTrain prompts | Fit calibrators and combiners only |
| Validation | 512 other WildGuardTrain prompts | Select available policies, model hyperparameters, and decision cutoffs |
| Test | 1,699 labeled WildGuardTest prompts | Evaluate frozen choices; no tuning or refitting |

The task is prompt harmfulness only: BLOCK harmful requests and ALLOW benign
requests. WildGuardTrain supplies model-generated labels while the official test
uses human annotations. Training/validation distribution and annotation differences
are material limitations. These are the same populations used for the decision
studies, not fresh ensemble-development data. Source-model training exposure is
incompletely known. The test is held out of this combiner's fitting and selection,
but it is not newly unseen by this research project.

Brief and detailed policy variants have complete saved fitting, validation, and
test scores for every model. Example-bearing policies have no fitting scores and
are excluded from the new ensemble feature pool. Do not fabricate those scores
or train on their validation/test examples. Keep the previously selected three-policy
individual configurations as separate historical comparisons. This bounds the
experiment; it does not test each decision model's best possible policy.

For each model, select between brief and detailed using the existing leaderboard's
balanced-accuracy validation procedure over native decisions and score cutoffs.
Use that selected policy's native BLOCK score as its one continuous feature in
all new combinations. This policy choice is shared between cohorts; there is no
ensemble-specific policy search. Validation is reused for this bounded policy
selection and subsequent combiner/cutoff selection, which can overfit validation.

Check row IDs, prompt hashes, gold labels, group IDs and metadata across every
input. Do not inner-join away missing examples. Enforce disjoint fitting,
validation and test groups and text hashes. No text, subcategory, adversarial
status, label, or other metadata becomes a feature. Preserve unresolved outputs
as errors; an ensemble requires all its component scores. Exclude incomplete
fitting rows explicitly and report the count.

## Registered methods

Two cohorts: **all three** (Jev, Kev, Clef) and **open weights only** (Kev, Clef).
Fit the same bounded candidates for each:

1. **Primary:** logistic regression on the native probability scores, standardized
   with fitting-only statistics; L2 regularization, C in [0.01, 0.1, 1, 10, 100].
2. Equal mean of raw probabilities; equal mean of independently calibrated
   probabilities; learned nonnegative weights summing to one on those calibrated
   probabilities, with regularization [0, 0.01, 0.1] toward equal weights.
3. Logistic regression on reconstructed log-odds with the same C grid; equal mean
   log-odds followed by sigmoid. Jev returns some exact 0/1 scores, so clip every
   model's probabilities to [1e-6, 1−1e-6] before this transform. Freeze this rule
   before fitting and report clipping counts. Do not describe reconstructed,
   clipped log-odds as raw head logits.
4. Random forest: 300 trees, max_depth [2, 4], min_samples_leaf [20, 80].
5. Decision-only controls: majority of native ALLOW/BLOCK choices (ties BLOCK for
   the two-model cohort), and logistic regression on these binary choices using
   the same C grid. The fixed vote is not threshold-tuned; decision-only logistic
   regression receives the same cutoff search as score-based logistic regression.

Controls for each selected component policy: native/raw-score decisions and
single-feature logistic calibration on probabilities and clipped log-odds,
using the same C grid. Choose the strongest eligible individual on validation,
not whichever single has the highest test score. Do not include WildGuard or
specialist-policy-model scores as ensemble features.

Probability calibration for averaging uses C=1 sigmoid models. Learn averaging
weights from five-fold, stratified, group-disjoint out-of-fold fitting predictions;
then fit the deployable calibrators on all fitting rows. Logistic and forest fits
use fitting rows only. No refit on validation or test. Use seed 20261030 for the
new fits and splits. Reuse the previous leaderboard's seed 20261029 for paired
bootstrap resampling, making comparison procedures consistent.

## Selection, freeze, and comparisons

Use balanced accuracy as the primary objective. Apply the existing deterministic
leaderboard cutoff grid and tie-breaks. Select one configuration for each method,
each individual, the strongest individual, and the strongest score-ensemble method
on validation. Report all registered methods, including negative results. The
validation-selected best method is secondary to the predeclared logistic primary.

Also freeze separate selections for the 5% compliant-error limit and 90%
violation-catch target, with explicit infeasibility and test target failures.
These profiles must not affect the balanced selection.

Before reading this extension's test scores, save a freeze binding the plan,
source code, software versions, input hashes, policies, fitted models,
coefficients/calibrators, all validation results, and selections. Evaluation must
reject changed inputs or selections. Never replace a frozen choice after viewing
test results.

Primary paired comparisons: all-three probability logistic versus (a) its strongest
calibrated individual and (b) the released WildGuard model. Secondary comparisons:
the same primary versus decision-only logistic and fixed majority; open-only
probability logistic versus its best individual and the all-three primary; the
validation-selected best score ensemble versus the best individual. Keep the
previous balanced Jev, Kev, Clef, CoPE, Qwen 27B, and specialist equal-log-odds
ensemble as historical references, without selecting among them on the new test.

Report balanced accuracy, ordinary accuracy, macro-F1, MCC, recall, specificity,
false blocks, misses, unresolved outputs, AUROC, average precision, and score
calibration diagnostics (Brier score and log loss). Show train/validation/test
denominators, policy identities, fitted weights/coefficients, and category slices.
Inspect score correlations and overlapping errors as descriptive diagnostics,
not grounds for another search after test evaluation.

Use 2,000 paired duplicate-group bootstrap draws for selected results and paired
differences. Intervals are exploratory and unadjusted for multiple comparisons;
they omit policy-search, label, repeated-inference and model-training uncertainty.
The comparison is between configured systems, not a causal architecture study.

## Reproducibility and cost

Provide a prompt-free archive with input scores, metadata, source snapshots,
selection/fitted objects, results, checksums, and CPU-only reproduction commands.
Verify that reproduction recovers policies, fits, cutoffs, scores, and metrics.
Preserve all older archives unchanged.

Added GPU/API cost is **$0**. No cloud instance or provider credential is needed.
The latest recorded cumulative spend remains $13.79540555656 of the authorized
$20. Local CPU and researcher/assistant time are not priced by this ledger.
This study does fit small supervised models; it is not a training-free approach.
