# Screening malicious code and agent skills

**Policy edits helped in some cases, but a good code score did not establish a
useful malicious-skill detector.** We compared eight systems across policy
models, general-purpose LLMs, decision models and trained classifiers. The two
benchmarks ask different questions and have separate leaderboards.

The code test contains **160 source files**, equally divided between benign and
malicious. The skill test contains **1,384 source-held-out records**: 545 benign
and 839 malicious. Every model receives the same bounded text view. No downloaded
program or skill was executed.

## The results at a glance

These are **balanced accuracies**: equal weight for catching malicious artifacts
and allowing benign ones. They are validation-selected systems, not the best
configuration found by searching the test results.

| System | Code files | Agent-skill text |
|---|---:|---:|
| PolicyLM-1.7B | 86.88% | 61.86% |
| Shieldstral-1.0-3B | 76.25% | 52.44% |
| Qwen3.5-4B | 86.88% | 54.17% |
| Kev-4B | 78.75% | 53.51% |
| Clef-Flash | 88.75% | 55.24% |
| Jev-1.14 (API) | 90.00% | 57.21% |
| Fine-tuned Liquid encoder 350M | 91.25% | 65.06% |
| Character TF-IDF + logistic regression | 88.12% | 70.19% |

[Full results](RESULTS.md) include ordinary accuracy, macro F1, MCC, error counts,
uncertainty intervals and results for complete versus clipped input views.

The small fine-tuned encoder had the highest code point estimate, only two
correct cases ahead of Jev. That small gap does not establish a reliable winner.
On skills, the simple lexical classifier had the highest point estimate, ahead
of the neural models, but its false-block rate was 47.34%. Neither result supports
choosing a model family without testing the intended task and error budget.

## What policy editing changed

On code, PolicyLM rose from **70.00% to
86.88%** after validation selected the evidence-focused
policy. False blocks changed from **48 to 6**;
misses changed from **0 to 15**. The higher
aggregate score came from 42 fewer false blocks while introducing 15 misses. The
paired interval for the balanced-accuracy gain is **+9.45 to +24.11 percentage
points** in this sampled test.

The edit asked the model to trace an observable chain—such as a sensitive source
leading to an unrelated external destination—and distinguish live behavior from
quoted examples and legitimate administration. It also required visible evidence
before blocking. This changes the decision standard; it is not merely adding
headings or making the policy longer.

Other models did not need the same policy. Qwen and Jev selected the brief code
rule; Shieldstral and Clef selected structured rules. Kev selected the evidence
variant but its test balanced accuracy was unchanged. On skills, all six selected
structured rules, yet Jev's score slipped slightly from its brief control.
Validation improvement does not guarantee improvement under a source shift.
See [the actual policy changes and native interfaces](POLICY-CHANGES.md).

## Why the error counts matter

On skill text, Jev blocked **0 of 545 benign records** but missed **718 of 839
malicious records**. Shieldstral also made no false blocks, while missing 798
malicious records. Those are conservative decision patterns, not strong evidence
of protection.

The character TF-IDF classifier took the opposite trade-off: it missed only
**103 malicious skills**, but blocked **258 benign skills**. The fine-tuned
Liquid classifier reached **65.06% balanced accuracy**,
with **288 false blocks and 143 misses**.
A headline score needs both error types beside it.

Liquid and TF-IDF each learn from **632 code fitting examples** or **1,024 skill
fitting examples**, with a separate classifier per task. The six prompted models
instead choose among three prespecified policies using validation. The trained
systems receive no policy at inference, and have not been shown to follow a newly
edited rule without retraining. Their different label use prevents treating this
as an architecture-only comparison.

## What a moderation team can take from this

Test the actual decision you intend to deploy. Detecting a malicious source file,
judging a skill before installation, detecting prompt injection, and deciding
whether an employee may investigate malware are different tasks. A legitimate
incident-response request can contain a malicious artifact.

Version the policy, model revision, adapter, input-view rule and decision cutoff
together. Keep benign lookalikes in the benchmark and inspect the misses as well
as the false blocks. A fixed task also deserves a simple trained baseline;
model family or parameter count alone does not settle the choice.

These are bounded screening results. The code test is small and its labels are
largely model-assisted. The skill test holds out sources but shares five attack
families with fitting, covering 205 test records. Some input views omit the middle
of the artifact, and auxiliary package files are not supplied. We cannot attribute
all misses to a single cause or claim that a correctly classified artifact is safe
to execute. [Methods and limitations](METHODS.md) explain these boundaries.

## Evidence and cost

The original [registered plan](PLAN.md), [pre-test freeze](preparation/README.md), policy files,
validation results, prediction records and source hashes are published. No new
cutoff fitting, calibration, retrieval or ensemble was added. The Liquid training
comparison uses one seed, two learning rates and three epochs per rate.
The plan preserves its pre-execution status; this readout records the completed run.

All reported test metrics were independently checked, and the exact data
populations were restored and hash-verified. The readout preserves the Unicode
JSONL repair, lossless checkpoint-storage amendment and recovery of eight cached
Jev responses after a local storage interruption. No predictions were lost or
replaced by new API calls in that recovery.

Total accounted GPU/API cost: **$1.382805**, below the
**$6 study cap**. GPU.ai compute cost $1.07; Jev cost $0.312805
for 4,416 requests. The GPU was terminated and temporary access keys removed.
These costs include setup, validation, training and final inference; they are
not production per-request estimates.

[Reproduce the results](RUNNING.md) · [Frozen evidence bundle](../../published_runs/2026-11-03-malicious-artifacts/README.md) · [Dataset directory](../datasets/README.md) · [Model directory](../models/README.md)
