# Shared Shieldstral adapter for moderation benchmarks

Register before fitting. This is a local, text-only research pilot on the RTX
5090. Model `mistralai/Shieldstral-1.0-3B` revision
`003ec7e2b0bab5f0e6307edbaf186fa5822b76f5`. No provider/API spend.

## Cohorts and interventions

Reuse the pinned Liquid router archive's FIT and validation records with their
original binary moderation labels, under the fixed enterprise policies and
existing Shieldstral renderer. Benchmark names, reference labels and reviewer
rationales are excluded from the model input. Keep the 983-case enterprise
evaluation and its 192-case calibration cohort out of fitting. Audit input
hashes, normalized exact text and existing overlap groups. Upstream near-
duplicate grouping is approximate. Require full documents for scored cases.
Training selects up to 32 examples per task and class from FIT by stable hash,
with no silent truncation and a 2,048-token training limit. Validation uses its
binary task cohorts and evaluation uses the fixed binary contracts. The two
three-way policy tasks are outside this binary pilot.

Compare base weights, one shared mixed-task LoRA, and a matched-example and
matched-step LoRA where 72 fitted records are replaced by 36 two-policy pairs.
The latter condition is exploratory if independently reviewed contrasts are
unavailable. In that case use mechanically labeled authored fixtures with
separate workflow and policy templates for the fresh transfer diagnostic. All
variants use the same evaluation wrapper, wording and procedures. No final
suite case is used to author the fixtures. Use full-vocabulary cross entropy
only at the answer position. LoRA on language attention q/k/v/o projections
only, rank 8, alpha 16, no dropout, BF16 base, AdamW with learning rate 1e-4,
zero weight decay and gradient norm cap 1. One epoch per condition,
microbatch at most two and effective batch eight. Seed 20261107. The smoke
test runs one optimizer step using a long FIT example, checks single-token
target and adapter reload, and is discarded for the comparison.

## Selection and scoring

Use the final checkpoint of each fixed one-epoch fit. Select one global
cutoff for each system on validation by maximizing the equal-task mean of
balanced accuracy on tasks with both classes. Search 0.05 through 0.95 in
steps of 0.05, breaking ties by distance to 0.5, then lower cutoff. Freeze
checkpoint and cutoff hashes before opening final evaluation for inference.
Retain 0.5 controls and an operating-point analysis targeting at most 10%
false blocks, averaged equally across validation tasks containing ALLOW.
At that operating point maximize equally weighted BLOCK recall across
validation tasks containing BLOCK and report achieved false-block rates on
test for each model. Measure recall at the base system's test false-block
rate as a separately labeled descriptive ROC statistic, not a selected cutoff.

Primary is equal-task balanced accuracy over the fixed binary tasks with
both reference classes. Report per-task confusion matrices, exact counts,
both error rates, score coverage and single-class panels separately.
Unscored over-limit records count as errors. Report paired group-bootstrap
95% intervals on this suite, conditional on the fixed training seed. An
adapter supports a cross-task improvement claim only if the primary paired
lower bound exceeds zero, at least three primary tasks improve and none loses
more than five points of balanced accuracy or ten points of BLOCK recall.
Report the matched contrast condition separately. Fixtures test policy
changes and cannot substitute for an independently reviewed new-source set.

## GPU and artifacts

Use BF16 SDPA, gradient checkpointing, serial stages, a 50% per-process
allocator cap, 25% operation-duty target, and no device setting changes.
Sample total device load. Cool down at 60 C or 200 W; abort at 70 C,
at sustained 250 W, or after three minutes without recovery. Bound each
execution stage to 35 minutes. Keep prompts and weights in ignored local
storage. Archive hashes, predictions, telemetry, failures and cleanup
observations. Publish code and prompt-free evidence.
