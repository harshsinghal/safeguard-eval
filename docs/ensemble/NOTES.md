# Ensemble lab notebook

## 27 October 2026 — protocol and data preparation

The user approved the ensemble experiment. The study fixes the previously selected
policy/model pairs and compares equal averages, learned simplex weights, logistic
stacking and shallow random forests with raw, thresholded and calibrated singles.
Logistic stacking is primary. HateXplain's Qwen extension is reported separately.

The earlier cumulative $20 cap has $7.87880246544 remaining. GPU.ai has $13.80
account credit and no running instances. A 96 GB RTX PRO 6000 VM is available at
$1.99/hour with no disk surcharge. One rental is reserved for two hours ($3.98)
with a provider cutoff. RunPod remains the fallback; credit does not expand budget.

WildGuard's 8,192 cached final-fit rows leave 7,015 eligible after excluding earlier
development groups and known train/test overlap groups. HateXplain leaves 14,325
eligible official training rows after excluding earlier fitting, demonstrations,
validation and test groups. Each new development split contains 4,096 fitting and
1,536 validation rows. Whole duplicate groups are retained within one split.
The data manifest records exact strata, exclusions, policies and input hashes.

A preparation-only schema check found that some old frontier records omit prompt
hashes. Their IDs and groups remain available and are excluded; optional hashes
provide an additional exclusion where present. Preparation was rerun before any
ensemble fitting or inference. No original evidence was altered.

All 60 repository tests passed, including nine new checks for score alignment,
metadata/label mismatch, leakage, failed outputs, grouped sampling, weight bounds,
metrics and deterministic threshold selection. These are software tests, not
model results. The legacy fixture validation also passed.

Fresh GPU inference is development-only: 5,632 rows per HateXplain model plus
32 old fitting canary rows per model. Original model revisions, policy hashes,
renderers, native helpers and inference settings are pinned. The canary checks
adapter consistency and is excluded from ensemble fitting/selection. The official
test populations and old validation sets are not uploaded for new inference.

## 27 October 2026 — inference, freezes and test evaluation

The GPU.ai instance `gpu-3ebe6b31` became ready at 06:06:23 UTC on 28 October
(27 October locally). It had a two-hour provider termination limit. All 16,896
new development scores and 96 canary scores completed without an inference error.
Each model's 32 canary scores and decisions exactly matched the prior run.
The completed outputs were downloaded and verified against model revisions,
policy hashes, input hashes and ID/label/group metadata before shutdown.

The provider confirmed termination after 691 billed seconds. Reconciled cost is
$0.38, bringing cumulative spend to $12.50119753456 and leaving $7.49880246544.
The temporary provider SSH key and local private key were removed. RunPod was
available but unnecessary. Gated/private input text and raw responses remain in
the private work directory, outside the repository evidence package.

The three freezes preceded every ensemble test evaluation:

| Cohort | Freeze time (28 October UTC) | Test evaluation time |
|---|---|---|
| WildGuard specialists | 06:10:39 | 06:18:31 |
| HateXplain specialists | 06:18:02 | 06:18:31 |
| HateXplain mixed | 06:18:02 | 06:18:31 |

There are 35 candidates in each three-model cohort and 28 in the two-model
cohort. WildGuard's external comparator is one additional result, not a learned
candidate. All configurations, including candidates that lost validation
selection, are retained. No fitting source, candidate grid, selected policy or
test decision threshold was changed after the freezes.

Logistic regression was primary. Validation selected C=1 for WildGuard and
HateXplain specialists, and C=10 for the mixed HateXplain cohort. The separate
validation-selected ensemble was weighted averaging for WildGuard and random
forest for both HateXplain cohorts. The best individual on validation was
Shieldstral in both specialist cohorts and Qwen in the mixed cohort.

WildGuard primary accuracy was 90.76%, versus the calibrated individual's 90.88%.
The selected weighted average made identical test decisions to that individual;
99.41% of its fitted weight fell on Shieldstral. The registered equal raw average
reached 91.41%, but it was not the validation-selected ensemble.

HateXplain specialist logistic regression reached 75.57%, below Shieldstral's
79.57%; the selected specialist forest reached 79.31%. The mixed forest reached
79.73%, a small uncertain increase over the validation-selected Qwen individual
(79.16%) and only three correct answers ahead of Shieldstral. Compared with
Shieldstral, it traded 42 fewer false blocks for 39 more missed hateful posts.

Shieldstral's large improvement from its raw 0.5 cutoff (53.17%) to the selected
calibrated result (79.57%) is threshold tuning, not policy editing. A raw cutoff
of 0.98 achieved the same test accuracy. The calibrated cutoff was 0.48; those
two numbers apply to different score scales.

## Reporting decisions and departures

The protocol proposed inspecting complementary errors on development first.
We did not use a separate development error-overlap review as a gate before test
evaluation. The method grid stayed fixed and all registered methods were run;
the reported overlap analysis is a post-test diagnostic, not selection evidence.
This sequencing departure does not change the train/validation-only fitting or
the pre-test freezes. It should not be presented as a prospective finding.

An additional paired comparison of the mixed HateXplain forest with Shieldstral
was calculated after test evaluation, because the user specifically asked about
exceeding the maximum individual accuracy. It is labeled descriptive and stored
separately. The registered comparison remains against Qwen, selected on validation.

Unselected forest configurations reached 79.68% on the specialist HateXplain test
and 80.15% on the mixed test. They were not promoted into headline results after
seeing the test. Their candidate-level scores remain available in `results.json`.

Bootstrap intervals use 2,000 paired duplicate-group resamples and retain all
examples. They are unadjusted and exploratory. The official test scores were
already known from previous studies. All failures would count as incorrect;
this run had none. Metrics optimize accuracy with macro-F1 as tie-break, so
the chosen thresholds need not meet a different operational recall objective.

The original plan remains unchanged for hash verification. The completed
checklist lives in README.md and the status in progress.json. Figures are
generated directly from frozen JSON results; the plain-language readout explains
both the unsuccessful primary comparisons and the secondary positive result.

## Verification and archive completion

CPU reproduction ran from `/tmp` using the archived source and scores, without
model inference. It refit all 98 registered candidates across the three cohorts,
matched the frozen validation choices and thresholds, and reproduced every test
metric and all registered paired-bootstrap intervals. The result is recorded in
`published_runs/2026-10-27-ensemble/reproduction.json`.

All 63 repository software tests passed, including 12 ensemble checks. The legacy
72-case fixture validation passed. All nine private raw-response hashes matched
their completion manifests. Both figures were rendered and visually checked.
The public evidence package was scanned for credential patterns and private
prompt/response fields; none were found in the exported records. No model or
policy source from earlier studies was edited. The paper and existing articles
were left for a separate editorial review.
