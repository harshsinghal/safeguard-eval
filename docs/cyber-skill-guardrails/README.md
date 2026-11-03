# Cyber requests and agent skill packages: what we found

These two experiments extend the research from harmful prompts and isolated
code files to **requests for cyber assistance** and **complete textual agent
packages**. They test policy wording, model choice and the evidence supplied to
the model. The results show why a single accuracy number is only the start of
the decision.

## Two questions, two test sets

The cyber study asks whether a model can separate CyberSecEval’s attack-assistance
requests from benign requests that change system state. We evaluate 330 requests,
165 per class. This is our classification adaptation of Meta’s MITRE/FRR sources,
not Meta’s original generation or refusal score. Some attack-source requests are
dual-use or look legitimate in isolation; the scores measure agreement with the
source labels.

The skill study screens 512 eligible MalSkillBench packages, 256 per class. Each
input includes SKILL.md and all companion text files within the common size limit.
We also remove the companion files while keeping the same selected policy. No
package is installed or executed.

## How the configured systems compare

These are test scores after validation selection. Accuracy equals balanced
accuracy on both balanced full test sets. The [complete tables](RESULTS.md) also
show false blocks, misses, macro F1, MCC, uncertainty and all controls.

| Configured system | Cyber requests: balanced accuracy | Skill packages: balanced accuracy |
|---|---:|---:|
| PolicyLM 1.7B | 70.91% | 61.72% |
| Shieldstral 3B | 83.33% | 58.01% |
| Qwen3.5 4B | 60.91% | 85.55% |
| Kev 4B | 84.55% | 73.24% |
| Clef-Flash 9B | 78.48% | 90.82% |
| Jev 1.14 (API) | 83.33% | 95.51% |
| Llama Guard 4 12B, custom policy | 77.27% | 70.70% |
| Jina v2 code + logistic | 99.70% | 79.49% |
| Jina v2 code + neural head | 100.00% | 81.64% |

The Jina rows train a small classifier using fitting labels while keeping the
embedding model frozen. They are fixed-task systems, not policy-only alternatives.
The neural row uses the first registered seed; all three seeds are reported.
Llama Guard’s default taxonomy and the narrower Prompt Guard injection diagnostic
are separate controls in the full results.

The primary Jina neural head matches **all 330 cyber labels**; the linear head
makes one error. This deserves caution. The two labels come from different source
collections, so a trained head may learn remaining corpus or writing-style cues.
This result does not establish perfect recognition of malicious intent. Its
[100%, 100%] resampling interval reflects a sample with no observed errors, not
zero uncertainty about future traffic. The neural head scores **81.64%** on the
separate skill task, illustrating the limits of a single headline result.

A shared score can also hide different behavior. Shieldstral and Jev both reach
**83.33%** on cyber requests. Shieldstral makes **18 false blocks and 37 misses**;
Jev makes **7 false blocks and 48 misses**. The preferred system depends on which
error is more costly in the intended workflow.

The observed ordering also changes with the task. PolicyLM scores **70.91%** on
cyber requests versus Qwen’s **60.91%**. On skill packages, Qwen scores **85.55%**
versus PolicyLM’s **61.72%**. These are the tested policies and native decision
rules, not an intrinsic ranking of the model families.

## Policy text changes outcomes—and the error tradeoff

PolicyLM gives a clear example. Its cyber score rises from **50.91% with the
brief policy to 70.91% with the selected policy**. False blocks fall from **119
to 35**, while misses rise from **43 to 61**. The weights and the publisher’s
decision preset remain fixed. More explicit allowances and contrasting cases
change how the model applies the boundary, but do not improve every error type.

Clef’s structured skill policy raises its score from **80.86% to 90.82%**. Here
misses fall from **96 to 39**, while false blocks rise from **2 to 8**. Policy
changes can move the error tradeoff in either direction.

For Llama Guard on cyber requests, the selected custom policy raises balanced
accuracy from **72.42% with its default taxonomy to 77.27%**. It reduces misses
from 81 to 61 while increasing false blocks from 10 to 14. The default taxonomy
and our custom task definition have different coverage, so this is more than a
cosmetic formatting change.

The skill comparison shows another tradeoff. Llama Guard’s brief policy scores
**66.60%**; its selected policy with contrasting cases scores **70.70%**. False
blocks fall from **69 to 37**, but misses rise from **102 to 113**. A team that
places a high cost on missed malicious packages could reasonably dislike that
change despite the higher aggregate score.

Its default taxonomy scores **70.31%** on skills. The custom-versus-default
difference has a paired interval that includes zero, so this sample does not
establish an improvement over the default taxonomy for that task.

We did not retune cutoffs or replace a selected policy after seeing test results.
The report keeps improvements and regressions. Three prespecified candidates are
a limited authoring search, not a claim to have found each model’s best possible
policy. [What changed in the policies](METHODS.md#what-we-changed-in-the-policies).

## The package can contain evidence that its description does not

Jev scores **95.51%** on full packages versus **88.09%** on SKILL.md alone. The
more direct comparison is the **177 packages that actually have companion files**.
Among their 128 malicious packages, Jev misses **6 with all files versus 42 with
SKILL.md alone**. It falsely blocks none of the 49 benign packages in either view.
Balanced accuracy on that subset rises from **83.59% to 97.66%**.

The 335 remaining packages contain only SKILL.md, giving identical requests in
the two passes. Two Jev decisions still change near its decision boundary, under
the same reported API model version and provider. We report that repeat variability
rather than attributing every change to file context. The full results show the
paired comparison and repeat check for every model. Llama Guard also benefits:
its full-package score is **70.70%**, compared with **62.11%** on SKILL.md alone,
with no decision changes in its identical single-file controls.

This is a different dataset from the ProtectSkills/MaliciousSkillBench used in
our earlier artifact studies. A higher score across those collections is not
evidence that full files caused an improvement. The paired comparison within this
new test set is the relevant evidence.

## What this means for a team building a screen

- **Define the decision before choosing the model.** A harmful assistance request, an instruction-boundary attack and a malicious package are different targets. Prompt Guard’s injection task does not cover all of them.
- **Evaluate changes against both error types.** A policy edit can reduce unnecessary blocks while allowing more harmful-source cases. The preferred tradeoff belongs to the policy owner and the product team.
- **Give the model the evidence the task requires.** For packages with helper files, SKILL.md alone can hide relevant behavior. This study does not resolve external dependencies or execute that behavior.
- **Check the native interface end to end.** Our Llama Guard integration needed the publisher’s compatible runtime and the correct safety-label position after native whitespace. Those pre-test faults were repaired and archived; their invalid outputs are excluded from model scores.
- **Keep the learning resource visible.** A trained head uses labeled examples; an authored policy expresses editable rules. A score comparison does not make their capabilities or development requirements identical.

## How far these results go

The cyber labels inherit source-task assumptions, including ambiguous dual-use
cases and possible style differences. We removed an obvious JSON-wrapper shortcut
before final testing and preserved all original split assignments. That repair
does not prove that all shortcuts or label disagreements disappeared.

The skill test is restricted to text-only packages within 20 KB. Its malicious
half contains 251 generated, three wild and two tool-test packages. It cannot
establish reliable performance across the wild ecosystem, new attack families,
binary payloads or runtime execution. Public-model training exposure is unknown.
Grouped intervals are exploratory and do not establish a universal winner.

Both experiments cost **$2.115** against the registered **$6 cap**. This includes GPU setup,
validation, preserved failed attempts and API calls. The GPU was terminated and
temporary access keys removed. The bill is not a production inference-price or
latency measurement.

[Full results](RESULTS.md) · [Methods](METHODS.md) · [Registered plan](PLAN.md) ·
[Pre-test selections](preparation/README.md) · [Reproduction instructions](RUNNING.md) ·
[Frozen evidence](../../published_runs/2026-11-03-cyber-skill-guardrails/README.md)
