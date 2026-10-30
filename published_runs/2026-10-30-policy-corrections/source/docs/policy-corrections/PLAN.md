# Policy corrections from training errors

Status: registered before inspecting discovery prompt text, drafting corrections,
or running new inference. This follows the completed Shieldstral representation
study. It tests policy edits, not new heads or changes to model weights.

## Question and fixed interpreters

Can a bounded set of corrections derived from training mistakes improve
Shieldstral's harmful-prompt decisions beyond adjusting its score cutoff? Do
the selected corrections also help Qwen without rewriting them for Qwen?

Use the preceding study's pinned Shieldstral-1.0-3B and Qwen3.5-4B checkpoints,
BF16, native adapters and canonical two-label scores. Reuse its exact Shieldstral
p4 policy as p0. No generated reasoning, backbone training, new classifier head,
or activation steering. Conditional yes/no and B/A scores are not calibrated
risks or unconstrained generated-answer performance.

## Discovery, validation and holdouts

Discovery uses the preceding study's 4,096 fitting prompts and cached native
Shieldstral scores at cutoff 0.5. This fixed checkpoint was not fitted by us on
these examples; grouped out-of-fold head fitting is unnecessary for this arm.
Prior policy authoring may have used some discovery examples. Do not call them
fresh, and do not use prior validation/test error texts to write these edits.

Before authoring, audit recorded prior use across repository evidence and local
experiment outputs. Exclude every known used training ID and its entire recorded
duplicate group from the new selection/holdout pools. Exclude groups overlapping
the official test and conflicting-label groups as well. Merely preparing the full
training-assignment inventory is not counted as evaluating every row; disclose
that inventory and its exclusion from the usage census. Preserve the census,
hashes and exact exclusions. This is a record-based audit, not proof of no
upstream checkpoint exposure or of no unrecorded human inspection.

Choose one deterministic representative per remaining duplicate group. Draw a
stratified 1,536-example validation sample from unused original validation groups
and a separate 2,048-example holdout from unused original audit groups. Stratify
by label, category and adversarial flag using fixed seed 20261030 and independent
salts. Stop for a recorded protocol amendment if these counts are unavailable.
Only aggregate assignment metadata may be inspected before evaluation; no
holdout text, scores or example-level error review enters authoring or selection.

Also evaluate the same 1,699 labeled WildGuardTest prompts for historical context.
This test has already been inspected in previous studies and is exploratory here.
The additional holdout is unused in recorded project development, but comes from
WildGuardTrain, with its model-derived labels and different mixture. It does not
replace human-labeled WildGuardTest or establish an out-of-distribution benchmark.
Keep all four populations disjoint by IDs, exact hashes and recorded groups.
Approximate lexical duplicate detection can miss semantic paraphrases.

## One bounded authoring round

Inspect all discovery errors, separating false blocks and missed violations.
Record an error taxonomy, ambiguous labels and which source IDs motivate each
edit. Describe patterns without treating model explanations as causal evidence.
Keep source labels unchanged; do not resolve ambiguous labels in our favor.
Review a deterministic sample of up to 16 correctly classified examples per
class as counterchecks if needed. Publish no source prompt text.

Author exactly four candidates before new validation inference:

* p1: clarification addressing false blocks, at most 150 added words.
* p2: clarification addressing missed violations, at most 150 added words.
* p3: the exact union of the p1 and p2 additions.
* p4: p3 plus two short allowed/prohibited example pairs, at most 120 added words.

Append clarifications to existing ALLOW/BLOCK/PRECEDENCE fields so both adapters
receive them. Preserve all original clauses and the intended harmfulness scope;
document any uncertainty about benchmark intent. Examples are newly authored
illustrations of discovery patterns, not copied benchmark rows. This is a single
agent-assisted authoring round, not a replication of ProTeGi or a search for a
universally optimal policy. Freeze exact texts, provenance and code before any
new inference. No second editing round after viewing validation.

Run Shieldstral p0–p4 on discovery and fresh validation. Discovery results explain
what changed; only validation selects the correction. Choose the best revision
from p1–p4 by balanced accuracy with the shared 0.01 cutoff grid and deterministic
leaderboard tie rules. Select p0's cutoff separately. Keep the selected revision
even if it loses to p0, and report that outcome. A deploy/no-deploy recommendation
may retain p0; never hide an unsuccessful revision.

Freeze that selected policy before Qwen validation. Qwen receives only p0 and
the Shieldstral-selected revision, with no Qwen-driven wording or candidate
selection. Choose their respective cutoffs on the same fresh validation sample.
Then freeze all thresholds before any new holdout/test inference. Upload
label-free holdout/test inputs only after that final freeze.

## Comparisons and reporting

For each model report the same four primary configurations:

1. Original policy at 0.5.
2. Original policy with validation-selected cutoff (cutoff-only control).
3. Selected revision at 0.5 (policy change at a common cutoff).
4. Selected revision with its validation-selected cutoff (joint intervention).

The primary contrast is 4 versus 2 on the additional holdout for Shieldstral;
the corresponding Qwen contrast is a prespecified transfer check. Also report
3 versus 1 and 2 versus 1 for each model, and the same contrasts on WildGuardTest.
The revision is selected jointly with its cutoff; its fixed-0.5 result is not an
independently selected policy winner. Retain all discovery/validation candidates,
including unsuccessful edits. Never choose a replacement from test scores.

Use balanced accuracy, both error counts/rates, ordinary accuracy, macro-F1,
MCC, AUROC/AP, Brier/log loss, coverage, category/adversarial slices and corrected
versus newly introduced errors. Report 2,000 paired duplicate-group bootstrap
intervals with the existing seed, descriptive and unadjusted for model selection,
multiple comparisons or prior public-test use. Separately freeze a <=5%
false-block profile and >=90% harmful-recall profile for p0 and the same selected
revision; these profiles change thresholds, not the chosen policy.

No source-label changes, silent omissions or truncation. Over-limit inputs
(8,192 tokens) are unresolved and remain errors in denominators. Technical
failures stop the run for an explicit repair, rather than erasing difficult cases.
Verify score parity with the native forward pass, exact identities and immutable
hashes. CPU reproduction must reproduce selections, metrics and paired contrasts.

## Budget and completion

Prior cumulative spend is $14.54540555656 of the authorized $20. Reserve at most
$2.40 for one rental of up to three hours at <=$0.80/hour including disk; set
provider auto-termination. GPU.ai first, RunPod fallback within the same cap.
Prepare and test locally before renting. Download evidence, terminate compute,
confirm termination, remove temporary credentials and reconcile actual billing.

Publish policy diffs, the error-to-edit rationale, data audit, selections, full
metrics, prompt-free predictions, failures, runtime/cost records and source.
Keep raw source text private. Update the README with an experiment-named entry;
do not overwrite old evidence or merge this new validation protocol into the
common-validation leaderboard. Articles and skill releases can be refreshed in
a later explicit revision.

References: [preceding representation study](../shield-probe/README.md),
[training-error proposal](../research-directions/TRAINING-ERROR-CORRECTIONS.md),
[WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix),
[Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B),
[ProTeGi](https://arxiv.org/abs/2305.03495).
