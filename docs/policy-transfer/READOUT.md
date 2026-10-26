# A policy that works for one model can fail on another

The clearest result is that **policy text and the model need to be evaluated together**.
A policy selected for Qwen 2B improved Shieldstral. A policy selected for Shieldstral
made PolicyLM and Qwen 2B substantially worse. Transfer was useful, but uneven.

This is a small exploratory study, not a general verdict on specialist versus
general-purpose models. It also exposed a second issue: an automated policy editor
can improve agreement with benchmark labels while changing the intended policy.

## What we did

We kept five models' weights fixed and gave each the same starting harmful-request
policy. Each model's decision settings stayed fixed too. We used a sample of up to
32 of each model's mistakes on 1,024 training examples to create four revisions.
The same Qwen3.5-27B model wrote all revisions, using a fresh context containing only
that source model's feedback. “Tuned for PolicyLM” therefore means **tested and
selected using PolicyLM**, not written by PolicyLM.

Each model chose among its starting policy and four revisions using 512 separate
validation examples from the training dataset. PolicyLM, Shieldstral and Qwen 2B
found a better validation candidate.
Qwen 4B and 27B kept the starting policy. This left four distinct policy texts.

We then gave every model the same four-policy pool. Each recipient chose its policy
using validation again, and we locked those choices before the new test run. We
also tested the other combinations so that unsuccessful transfers remain visible.

## What happened on the test set

Every cell below uses the same **1,699 labeled WildGuardTest prompts**. Accuracy is
agreement with the dataset's prompt-harmfulness labels. We classified the request
alone; we did not grade the accompanying assistant response or generate images.

| Recipient model | Initial policy | Its own search choice | Its choice from the shared pool |
|---|---:|---:|---:|
| PolicyLM 1.7B | 85.05% | 85.05% | 85.05% |
| Shieldstral 3B | 87.82% | 90.52% | 90.76% |
| Qwen3.5 2B | 80.11% | 81.17% | 81.17% |
| Qwen3.5 4B | 85.58% | 85.58% | 85.58% |
| Qwen3.5 27B | 89.35% | 89.35% | 89.35% |

The last column uses choices made **before testing**. PolicyLM chose its own revised
policy; Qwen 4B kept the initial one. Shieldstral, Qwen 2B and Qwen 27B chose the
policy selected for Qwen 2B. Shieldstral's two leading policies tied on validation,
so the registered shorter-text tie-break chose the Qwen 2B policy.

![Complete test matrix and changes from the initial policy](../../published_runs/2026-10-25-policy-transfer/figures/policy-transfer.png)

The gold outlines mark validation choices. They do not mark the highest test score.

## A successful transfer did not work in reverse

With the policy selected for Qwen 2B, Shieldstral rose from
87.82% to 90.76%.
The same text can therefore be useful beyond the model used during its development.

In the direct reverse comparison, the Shieldstral-selected policy reduced Qwen 2B
from 80.11% to
75.10%.
On PolicyLM, that Shieldstral policy reduced accuracy from
85.05% to
74.57%.

A document's good score with one interpreter gives us a reason to try it elsewhere.
It does not replace testing it with the intended deployment model. This experiment
supports validating the combination; it does not identify a universal best policy.

## The same accuracy can hide a different moderation experience

PolicyLM scored **85.05% with both its initial and its own revised policy**. In total,
the revised policy caught 12 more harmful prompts and incorrectly blocked 12 more benign
prompts. Those changes cancel in the accuracy calculation.

The transferred Shieldstral policy was much more aggressive on PolicyLM: it blocked
404 of the 945 benign prompts, compared with 142 under the initial policy. It also
caught more harmful prompts. A platform would experience those two consequences
separately, which is why the evidence includes harmful recall, false blocks, F1 and
failed or unparseable outputs alongside accuracy.

## Did a small specialist beat the large general-purpose model?

Using their frozen choices from the same pool, Shieldstral 3B scored
**90.76%**, and Qwen 27B scored **89.35%**.
The difference, Shieldstral minus Qwen, is **+1.41 percentage points**;
the unadjusted paired 95% interval runs from +0.06 to +2.77 points.
This is a narrow, exploratory edge for these chosen configurations.

This fresh search also does not replace the earlier results. In the
[previous Qwen study](../qwen-policy/READOUT.md), Qwen 27B reached **91.29%** with a
different selected policy. Those earlier shared policies were excluded here to keep
source feedback isolated. The present comparison evaluates this bounded search
procedure and its chosen configurations, rather than each model's best known score.

This does not settle whether policy-specific training is necessary or whether small
models generally replace larger ones. The models differ in architecture, training,
and native interfaces. We did not train matched base/specialist pairs. Also, this
search found no successful new 27B-specific revision: Qwen 27B's own source choice
was the original policy. Transfer of a newly improved large-model policy to a small
specialist remains a follow-up question.

## A high score is not approval of the policy

Before the test run, a text review found that Shieldstral's selected draft had omitted
an explicit sexual-content category present in the starting policy. Its broad
harmfulness language may still cause the model to block such content, but the policy
no longer states the same rule explicitly. The draft also introduced potentially
conflicting language about benign adversarial framing and jailbreak attempts.

We retained that candidate unchanged under the registered procedure. Its score
measures agreement with benchmark labels; it does not certify that the editor
preserved a platform's intended rules. Policy owners need to review scope and
exceptions, while engineers test how the selected model applies them. The
[policy-change notes](POLICY-CHANGES.md) separate textual changes from claims about
why a score moved.

## How much should we infer?

The fitting, validation and internal audit examples came from the same grouped
WildGuard training data used in our earlier studies: 1,024 fitting, 512 validation,
and 512 audit examples. The editor saw up to 32 fitting mistakes per source model.
The official test uses all 1,699 rows with prompt-harmfulness labels, excluding the
same 26 null-label rows as before. This is not an unseen-category test.

We had already seen WildGuardTest results in earlier work, so this extension is
exploratory. Training labels are largely model-produced; official test labels are
human annotations. We used one editor, four rewrites per model, and one benchmark.
We did not audit the models' upstream training-data exposure.
A repeat check of the initial policies changed 17 of 8,495 labels relative to the
earlier runs, with no changes for PolicyLM. Close scores should be read with that
variation in mind. The paired intervals resample the stored prompt groups (each
official test prompt has its own group). They are descriptive, without adjustment
for the many comparisons or variation across repeated searches and runs. A fresh
benchmark, repeated searches and a policy-scope review are needed before making
stronger deployment claims.

The practical finding is narrower and useful: **version and validate the policy
text together with the model that will apply it**. Recheck a transferred policy,
inspect false blocks and missed harmful requests, and keep policy owners involved
when an edit made to increase accuracy changes a rule.

## Evidence and cost

The study made **81,084 new classifications and 20 policy-editing calls**, and reused
7,680 verified initial-policy fitting/validation predictions. It retained all 20
drafts and every evaluated combination. The source code, predictions, policies,
selection records and uncertainty calculations are available in the
[evidence bundle](../../published_runs/2026-10-25-policy-transfer/).

The GPU.ai rental cost **$2.32**, including setup, authoring and inference.
Cumulative project spend is **$10.78 of the authorized $20**.
The GPU is terminated. These are experiment costs, not production serving estimates.

See the [registered plan](PLAN.md), [lab notebook](NOTES.md),
[exact policy changes](POLICY-CHANGES.md), and [reproduction instructions](RUNNING.md).
