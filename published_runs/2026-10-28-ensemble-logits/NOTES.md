# Log-odds experiment notes

## 27 October 2026 — before fitting

The user authorized the logit-based follow-up and asked whether the work supports
a practical alternative to task-specific model fine-tuning. The plan separates
that operational proposition from unmeasured claims about total effort or cost.
Policies, checkpoint weights, adapters, examples and split assignments stay fixed.

The preceding archive passed its full 111-file integrity check. All 63 existing
software tests and the legacy 72-case validation passed before runner changes.
Seven new tests passed for log-odds identity, boundary rejection, failed-member
handling, training-only scaling, immutable selection and pre-test freeze gating.

The extension registers 58 new candidates: log-odds logistic combiners and
matching individual calibrators with the existing five-value regularization grid,
plus an equal-log-odds average. The original ensemble is unchanged. Previously
observed test results make this an exploratory extension even though the new
settings are selected only on training/validation and frozen before evaluation.

No paid services or model inference are used. Cumulative spend remains
$12.50119753456. Local CPU and researcher/assistant effort are not priced.

## 28 October 2026 — frozen evaluation

All three cohorts were frozen before the extension's test scores were evaluated.
The following times are UTC; registration began on 27 October local time.

| Cohort | Freeze | Evaluation completed |
|---|---|---|
| wildguard-specialists | 2026-10-28T07:00:29.099398+00:00 | 2026-10-28T07:01:02.410900+00:00 |
| hatexplain-specialists | 2026-10-28T07:00:29.318095+00:00 | 2026-10-28T07:01:02.258750+00:00 |
| hatexplain-mixed | 2026-10-28T07:00:29.643541+00:00 | 2026-10-28T07:01:02.413001+00:00 |

No valid score was zero, one or nonfinite. Log-odds were calculated directly
in float64 with no clipping. Failed outputs would remain errors; these saved
inputs had none. Policies, checkpoints, adapters and development examples were
unchanged. Every previously fitted reference reproduced its original metrics
during the new evaluation.

The selected log-odds logistic accuracy was 91.29% on WildGuard, 78.79% on
HateXplain specialists and 80.82% on HateXplain mixed. All improved on the prior
probability-feature logistic method. The specialist-only HateXplain result still
fell below Shieldstral's 79.57%. The equal-log-odds secondary comparison scored
90.94%, 77.34% and 78.74%, respectively; it was not a general improvement over
the strongest individual. All 58 new configurations are retained, including
settings that did not win validation selection.

The WildGuard expanded individual-control pool selected log-odds-calibrated
Shieldstral on validation, but it scored 90.76% on test, below the prior
probability-calibrated Shieldstral's 90.88%. Both comparisons are reported. The
new ensemble scored 91.29%; the earlier equal probability average reached
91.41%, so this is not a new highest score across the whole research history.
An unselected new regularization setting also reached 91.41%; it was not promoted.

On HateXplain, the mixed ensemble exceeded the validation-selected Qwen
individual by 32 correct answers. An explicitly descriptive post-test comparison
with Shieldstral, the strongest individual observed on that test, found 24 more
correct answers: +1.25 points, unadjusted paired interval +0.10 to +2.44. The
registered comparison remains against the individual selected on validation.
The mixed ensemble reduced false blocks by 34 but missed 10 more hateful posts
than Shieldstral. Macro-F1 improved by 0.96 points; its descriptive paired
interval includes zero.

The learned HateXplain PolicyLM coefficients are negative conditional on the
other model scores. They are not normalized voting weights and are not causal
importance estimates. The exported unstandardized equations were checked
numerically against the frozen estimators. No method or feature search was
expanded after evaluation, and no fitting source changed after registration.

The write-up separates policy editing (earlier studies), calibration and score
combining. It supports adaptation without additional language-model weight
updates by the deploying team, while retaining the need for labels, evaluation
and engineering. It does not claim that the policy models were never fine-tuned
by their creators, or that we measured less human effort than fine-tuning.
The original paper and magazine article were not changed in this experiment.

## Completion and verification

CPU reproduction ran from `/tmp` using only the archived source and score
records. It recreated all 58 new configurations (55 fitted logistic estimators
and three equal averages), matched validation selections, and reproduced all
test metrics, per-example predictions and registered paired intervals. The prior
98 configurations also reproduced their recorded metrics as unchanged references.

All 70 repository software tests passed, including seven new log-odds checks;
the legacy 72-case fixture validation passed. The scientific figure was rendered
and visually inspected. Exported equations matched the actual frozen model
numerically. The final evidence inventory and the unchanged preceding archive
were verified. The public records contain no source prompt/response text or
credential patterns. No GPU/API resource was created, and cumulative paid
spending remains $12.50119753456 of $20.
