# What the experiments found

Source IDs below resolve to pinned repository links in [sources.json](sources.json).
Use [results.json](results.json) for machine-extracted numeric anchors. Do not mix
the best result from one study with a differently configured comparison in another.
For dataset origins, split construction, and label mappings, read
[datasets.md](datasets.md). For the consolidated manuscript, use [paper.md](paper.md).

## What was classified

**WildGuard:** prompt harmfulness on 1,699 labelled WildGuardTest rows. The 26 rows
without that label were excluded. There were 754 harmful and 945 benign prompts.
The model classified the request alone; it did not judge the accompanying assistant
response, generate images, or receive the gold label or category. Fitting and
validation examples came from grouped WildGuard training data. This was not a test
of entirely unseen categories. Training labels and official test labels also have
different origins. Sources: `wildguard-methods`, `wildguard-results`.

**HateXplain:** 1,924 official test posts, mapped to BLOCK for hate speech (594) and
ALLOW for offensive or normal speech (1,330). This task deliberately distinguished
identity-based hate from other offensive speech. It was not a general “block all
toxicity” policy, nor a test of rationale extraction. Source: `hatexplain-results`.

The language-model weights stayed fixed during these experiments. Policy editing,
threshold selection, and fitting a score combiner are different interventions.

## 1. Editing policy text on WildGuard

The first study tried 11 policy texts across four specialist models. It inspected
errors on 1,024 fitting examples and selected candidates using 512 validation
examples. **Selected policy** means the candidate chosen by that recorded procedure
for that model, before testing. It does not mean an objectively best policy or the
highest test score. A starting policy can remain the selected policy.

At the fixed primary settings, Shieldstral went from **87.93% to 90.82%** accuracy:
57 decisions became correct and eight became wrong. PolicyLM went from **85.05% to
86.82%**. CoPE changed from 90.46% to 90.76%; Safeguard from 89.82% to 89.64%, with
nine failed outputs in the selected run counted as incorrect.

WildGuard's fixed-task baseline scored **90.35%**. Shieldstral's small lead over it
was uncertain: the paired interval for the difference included zero. Also, changing
the initial Shieldstral policy's decision cutoff alone raised accuracy to 90.11%.
Much of the apparent improvement therefore depended on the decision setting, not
only the words. The policy-only gain over that calibrated initial control was
uncertain. Sources: `wildguard-results`, `wildguard-analysis`, `wildguard-claims`.

Several clauses changed together. The study supports testing the policy as an
operational input; it does not identify a magic sentence or prove fine-tuning
unnecessary.

## 2. General-purpose models with policies

The Qwen3.5 comparison used the same prompt-harmfulness task, model-specific system
instructions, explicit output labels, and thinking disabled. Selected configurations
scored 83.05% (2B), 87.58% (4B), 89.58% (9B), 91.29% (27B), and 90.29% (35B-A3B).
These results do not show that small specialists always beat larger generalists.
Nor are parameter counts a measured latency or cost comparison.
Sources: `qwen-results`, `qwen-edits`.

## 3. Transferring policies between models

A separate search gave five models four revisions each. Qwen3.5-27B authored the
revisions using only the source model's fitting feedback in each editing context.
“Tuned for PolicyLM” means tested and selected using PolicyLM, not written by it.
Each model selected among its baseline and revisions on validation. Four distinct
selected texts remained. The study tested the complete recipient/policy matrix
and also froze each recipient's validation choice from that pool.

Transfer worked in one direction and failed in another:

| Policy transfer | Recipient's initial accuracy | With transferred policy |
|---|---:|---:|
| Qwen-2B-selected text → Shieldstral | 87.82% | 90.76% |
| Shieldstral-selected text → Qwen 2B | 80.11% | 75.10% |
| Shieldstral-selected text → PolicyLM | 85.05% | 74.57% |

PolicyLM's own revision left its accuracy at 85.05%, yet caught 12 more harmful
requests and falsely blocked 12 more benign ones. Unchanged accuracy did not mean
unchanged behavior. Sources: `transfer-readout`, `transfer-analysis`.

In this bounded search, Shieldstral's pool-selected result exceeded Qwen 27B's
90.76% versus 89.35%. But the earlier Qwen experiment reached 91.29% with a different
policy. These are different comparisons, not evidence that size no longer matters.

One selected draft also omitted an explicit category and introduced conflicting
language. Its score did not certify preservation of the intended rules. Policy
owners must review scope alongside the engineering evaluation. The omission is a
warning about optimizing only benchmark agreement, not a recommended edit.
Source: `transfer-edits`.

## 4. Structured policy and omissions on HateXplain

The shared policy separated scope, definitions, BLOCK rules, ALLOW rules,
precedence, and four training examples. Native adapters mapped the components to
each model; final inputs were checked against frozen hashes. The source-selection
objective was validation macro-F1, rather than WildGuard's accuracy objective.

The accepted Qwen revision made seven punctuation edits. Shieldstral's selected
revision made those edits and added a sentence clarifying that context determines
whether a term attacks an identity or merely describes someone. PolicyLM retained
the starting policy after a proposed revision failed scope review: it blurred the
definition of normal speech and removed a constraint on assuming missing context.
See `hatexplain-edits` and `hatexplain-scope` for the exact changes. The scope review
was AI-assisted, not an independent human policy adjudication.

The omission tests were particularly instructive. Removing the same four examples
raised Shieldstral's accuracy from **52.4% to 61.0%**, but lowered Qwen's from
**72.5% to 61.8%**. Presenting the same clauses as linear prose instead of the
reference headings raised Shieldstral to 57.3% and lowered Qwen to 70.6%.
These presentation tests did not apply the same manipulation to PolicyLM's native
fields. Removing PolicyLM's definitions produced 28 more correct decisions overall,
while missing 36 more hateful posts and falsely blocking 64 fewer allowed posts.

These are fixed-setting comparisons, not optimal deployment scores. Later
calibration substantially changed results. They show why examples, definitions,
and presentation need testing with the intended interpreter. They do not show that
examples or definitions are generally harmful. Sources: `hatexplain-readout`,
`hatexplain-results`, `hatexplain-analysis`.

## 5. Combining models and calibrating their scores

The ensemble study fit small combiners on 4,096 examples and selected settings on
1,536 validation examples per cohort. Groups used for earlier policy development
were excluded. Only model scores entered the combiner, not prompt text or gold
test labels. It compared equal and learned averages, logistic regression, and
random forests, with calibrated individual-model controls.

For HateXplain, Shieldstral's individual accuracy rose from **53.17% at the raw 0.5
cutoff to 79.57% with validation-selected calibration**. False blocks fell from
885 to 177, but missed hateful posts rose from 16 to 216. This was a changed
decision boundary, not a new policy or improved understanding of every case.
Sources: `ensemble-readout`, `ensemble-results`.

The extension transformed saved float64 class probabilities into log-odds,
`log(p) - log(1-p)`, then fitted logistic regression. It collected no new model
inference and no new raw vocabulary logits. The transformation preserves more of
the useful score spread near zero and one, but does not create new information or
make different models' scores automatically comparable.

| Task / input models | Selected log-odds ensemble accuracy | Relevant comparator |
|---|---:|---|
| WildGuard / PolicyLM, Shieldstral, CoPE | 91.29% | WildGuard fixed-task baseline: 90.35% |
| HateXplain / PolicyLM, Shieldstral | 78.79% | Selected individual Shieldstral: 79.57% |
| HateXplain / PolicyLM, Shieldstral, Qwen 4B | 80.82% | Highest registered individual test accuracy: 79.57% |

On WildGuard, the ensemble caught 26 more violations and falsely blocked ten more
allowed prompts than WildGuard: 16 net additional correct decisions. On HateXplain,
the mixed ensemble falsely blocked 34 fewer allowed posts than that Shieldstral
control but missed ten more hateful posts: 24 net additional correct decisions.
The mixed cohort's validation-selected individual baseline was Qwen at 79.16%;
79.57% is a descriptive test hurdle, not a baseline selected by inspecting test
results. Sources: `logits-results`, `logits-claims`.

There was no universal ensemble win. The earlier equal-probability WildGuard
average reached 91.41% on test, but was not the validation-selected overall winner;
the new procedure is not the highest score ever observed. Avoid selecting a method
after seeing its test score.

## What these studies support

They support versioning and testing the **policy, interpreter, adapter, and decision
rule together**, and examining which mistakes change. Competitive classification
was possible without additional language-model fine-tuning in these settings.
However, the combiner used supervised fitting and labelled data; we did not compare
equal-budget fine-tuning strategies or prove less total engineering effort.

Later studies reused official tests whose earlier outcomes were already known.
Their selections were frozen before each new test run, but the extensions remain
exploratory. Paired intervals do not include uncertainty from repeated policy
searches, inference variation, or every upstream training-data exposure.

Earlier image-prompt and injection demos are separate (`early-demo`,
`injection-results`). The frontier API pilot was limited to fitting examples and
cannot establish that all frontier models fail at moderation (`frontier-pilot`).
Enterprise access control, employee intent, multilingual deployment, image
moderation, and activation analysis were not validated by these two benchmarks.
The enterprise track is a proposal (`enterprise-track`).
