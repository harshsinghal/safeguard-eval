# Code embeddings and general LLMs for artifact screening

## Question and scope

Can code-trained frozen embeddings support a useful task classifier for source
files and agent-skill text? Does a broader instruction search help general Qwen
models on the same tasks? Compare representations, head complexity and policy
wording; do not assume that networking or file deletion alone is malicious.

This is a follow-up to the frozen malicious-artifact study. Its aggregate test
results motivated this study. Reuse the exact fitting, validation and test
populations and bounded input views. No test examples or individual test errors
are used for authoring or selection. This is repeated evaluation on an existing
benchmark, not fresh independent confirmation.

## Registered panel

- Jina embeddings v2 base code: 161M bidirectional encoder; masked mean pooling,
  L2 normalization, no instruction prefix. Pin model and remote-code revisions.
- Jina code embeddings 0.5B: Qwen2.5-Coder-derived; last non-padding token,
  L2 normalization. Publisher passage prefixes: `Candidate code snippet:` for
  code and `Candidate answer:` for skill documentation. This is a fixed transfer
  of a retrieval representation to classification, not a native malware model.
- Qwen3.5 4B and 9B: native chat template, thinking disabled, normalized yes/no
  next-token scores, fixed 0.5 decision. Serial inference, no score calibration.
- Previous frozen eight-system outputs remain references; do not rerun or edit
  them. Report differences in training-label access and search budgets.

Jina v2 is Apache-2.0; Jina code 0.5B is CC-BY-NC-4.0. This research evaluation
does not establish commercial deployment permission for the latter.

## Inputs and development

Use the prior 8,000-source-byte view (6,000 head + 2,000 tail when clipped), with
no new token truncation. Code fitting/validation/test: 632/240/160; skills:
1,024/256/1,384. Preserve package/similarity grouping and publisher skill source
holdout. Skills include five fitting/test structural-family overlaps covering
205 test items; the test is not family-disjoint. File labels are largely
model-assisted. Only visible text is judged; never execute benchmark artifacts.

Inspect six stable-hash-selected fitting items per task (three per class) to
check development context. Record IDs, not raw text. Author three new policy
variants before validation: behavior checklist, contrasting benign/malicious
examples, and scope/authority guidance. Combine with the prior brief, structured
and evidence policies: six candidates per task and Qwen size. Examples are
short authored descriptions, not copied benchmark rows or executable payloads.
Do not fabricate multilabel behavior ground truth from binary malware labels.

## Frozen-feature classifiers

Train separate heads for each task and each embedding model. Fit StandardScaler
on fitting embeddings only. Never update the embedding model's weights.

- Logistic regression: L2, liblinear, balanced class weights, C in 0.1/1/10,
  max_iter 2,000, seed 20261103, cutoff 0.5.
- MLP: one ReLU hidden layer of 128 or 256 units; Adam learning rate 0.001,
  batch 64; alpha 0.0001 or 0.01; checkpoint after 10/30/60 epochs. Three seeds:
  20261103/20261104/20261105. Fitting sets are balanced. No internal holdout,
  early stopping or automatic learning-rate tuning. Select configuration by
  mean validation balanced accuracy across seeds, then mean macro F1, smaller
  hidden layer, earlier epoch, larger alpha. Report first seed as the primary
  single-classifier result and all three test seeds/range; never pick a seed
  using test results and never silently report a seed ensemble.

Linear settings: validation balanced accuracy, macro F1, smaller C.
Qwen policy: validation balanced accuracy, macro F1, shorter serialized policy,
then policy ID. Recompute all six validation policies for each size in the same
runtime. Freeze every model's selection before releasing any new test input.
Test selected Qwen policy and brief baseline (reuse if selected); test selected
linear head and all three MLP seeds. No post-test repair or policy selection.

## Reporting and constraints

Report accuracy, balanced accuracy, macro F1, MCC, false-block count/rate,
miss count/rate, unresolved, and full/clipped slices. Use the prior grouping
for 2,000-draw bootstrap intervals. Compare paired predictions with the previous
Qwen 4B and task-trained references; intervals are exploratory and unadjusted.
Do not merge code and skills into one rank. Different architectures and training
data prevent a causal claim that bidirectional attention or code pretraining
alone caused any advantage. No timing leaderboard: record runtime and bill only.

New spending ceiling: $4 from the remaining $11.768416426 benchmark allocation
(overlapping the retrieval-series allowance). GPU.ai first, RunPod fallback,
with provider-side termination. No paid model API is needed. Use a four-hour
RTX6000 Ada reservation at no more than $0.65/hour ($2.60 maximum); do not extend
or switch providers beyond the total ceiling. Keep large models on the GPU
host; retain compact features/selected heads privately and prompt-free public
evidence. Publish the plan, selections, results, failures, bill and cleanup.
