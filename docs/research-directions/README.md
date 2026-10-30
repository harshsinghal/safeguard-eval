# Research directions for choosing policy models

Recorded 25 October 2026. Status: research proposals; experiments have not started.

The next research question is how a team chooses a model for its policies, content,
and operating constraints. The unit of evaluation is the model together with its
policy text, decision thresholds, and escalation rules. Policy authors define the
intended rules and exceptions; engineers implement and test how the system applies
them. Neither responsibility can be replaced by a benchmark ranking.

The [enterprise AI governance track](ENTERPRISE-AI-GOVERNANCE.md) extends these
questions to employee requests made to connected enterprise assistants. It focuses
on permitted uses, trusted context, and controls before retrieval and disclosure.

## What the existing studies establish

Our [policy tuning](../wildguard/RESULTS.md),
[general purpose model comparison](../qwen-policy/READOUT.md), and
[policy transfer](../policy-transfer/READOUT.md) studies show that policy wording,
the model interpreting it, and the decision threshold can change outcomes. A useful
policy revision for one model can hurt another. A higher benchmark score does not
certify that an edit preserves the intended policy.

These are comparisons of complete classifier configurations. They do not isolate
the causal effect of architecture or specialized training. Training data, model
interfaces, and output mechanisms also differ.

## Six proposed research directions

### 1 Following platform rules and policy updates

Test whether a model follows the supplied policy when a rule or exception changes.
Keep content fixed while changing a policy clause; also include paraphrases that
preserve meaning and unaffected cases whose correct decisions should stay fixed.
Use new platform rules alongside familiar moderation categories.

Measure correct decision changes, unintended changes elsewhere, exception handling,
and stability under equivalent wording. Policy owners review scope before scoring.
This would help teams choose models that can support changing platform policies,
beyond recognizing familiar harmful content.

### 2 Matching the content and context

Compare performance on marketplace listings, short chat messages, discussion
threads, and image prompts. Where supported, evaluate actual images separately
from text that describes an image. Include relevant languages, code switching,
slang, quotations, satire, and attempts to evade moderation.

Report missed violations and false blocks by meaningful content slice, with sample
sizes and uncertainty. Test whether added conversation context helps or hurts.
Functional testing methods such as
[CheckList](https://aclanthology.org/2020.acl-main.442/) and
[HateCheck](https://aclanthology.org/2021.acl-long.4/) provide useful precedents.

### 3 Automating decisions within a review budget

Compare models at a fixed false-block limit, missed-violation tolerance, and human
review capacity. Fit score thresholds on development data and freeze them before
testing. Check whether scores actually identify difficult cases; raw scores from
different models are not interchangeable calibrated probabilities.

Report outcomes per 10,000 submissions at stated prevalence assumptions, alongside
performance on representative traffic. Include the severity of missed cases and
the quality of human review. A system that sends everything to review has not
achieved useful automation.

### 4 Combining a specialist with escalation

Compare a small specialist, a larger general purpose model, and a system that routes
selected cases between them or to a human. Determine whether their errors are
complementary and whether routing can identify the cases that benefit.

Evaluate complete workflows at matched quality and review constraints. Count every
stage's errors, latency, cost, and failures. A second model is useful only when it
resolves enough mistakes to justify its additional burden.

### 5 Supporting policy authors and maintenance

Give policy authors the same requirements, development examples, and editing budget
with different models. Measure authoring time, revisions, held-out performance, and
unintended changes in policy scope. Introduce a policy update and inspect regressions
on previously correct cases.

Study whether clause references or explanations help reviewers make accurate
decisions. Fluent explanations should be checked against the actual policy and
content. The outcome would show how much engineering assistance and ongoing policy
maintenance a model requires.

### 6 Measuring deployment cost and reliability

Measure memory, throughput, tail latency, failures, and decision repeatability under
realistic message lengths, policy-category counts, and traffic. Include preprocessing,
policy caching, batching, and escalation in the workload definition. Parameter count
alone is not a serving-cost measurement.

Record deployment requirements such as self-hosting, version pinning, data handling,
license constraints, and available evidence for reviewing decisions. Apply essential
capability requirements before comparing accuracy among eligible configurations.

## How architecture informs model selection

Architecture and interfaces guide eligibility and the measurements to run. They do
not supply an accuracy ranking.

- [PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b) uses a bidirectional
  encoder and a classification head, scoring multiple policy categories. Its native
  interface provides scores rather than written reasons.
- [Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B) combines a
  Ministral model with a vision encoder and reads yes/no scores for policy questions.
  Our completed comparisons evaluated text, not its image capability.
- [CoPE-B-A4B](https://huggingface.co/zentropi-ai/cope-b-a4b) uses a Gemma-based
  mixture-of-experts architecture. Its roughly 3.8B active parameters are distinct
  from its roughly 25.2B total parameters. The version we tested is text-only;
  a separate multimodal variant exists.

Model capabilities above were checked against the linked publisher documentation
on 25 October 2026. New experiments must pin the exact versions they evaluate.

## Suggested priority and deliverables

Start with policy adaptability and automation under review constraints, then add
content-specific tests and escalation. These are recommendations, not a registered
execution order. The enterprise track is a separate candidate study, with a different
task and labeling scheme from WildGuard prompt harmfulness.

Produce a selection guide organized by policy, content, tolerated errors, and review
capacity. Preserve exact policies, unsuccessful revisions, evaluation inputs,
configuration changes, and costs so the findings can support articles and a paper.
For each selected configuration, explain where it works and which cases require
another workflow.

## Parked direction

The proposed mechanistic interpretability comparison remains parked at the user's
request. It was not run. The user later authorized a separate predictive study:
[frozen Qwen and PolicyLM representations with logistic regression](../activation-probe/README.md).
That experiment is complete, but it does not locate causal policy reasoning in
layers. PolicyLM's bidirectional encoder and Qwen3.5's different architecture
remain important limits on mechanistic comparisons.

Recording these directions does not start model runs, GPU rentals, or new spending.

## Jev and local decision models

The [29 October source review and proposal](JEV-AND-LOCAL-DECISION-MODELS.md)
separates Jev's documented decision interface from its undisclosed internals,
identifies local candidates including Kev, Laya, and GLiClass, and proposes
testing whether models follow changed policies. It distinguishes adapting
policy text from training model weights. The subsequent
[Kev and Clef comparison](../decision-models/README.md) has now completed with
frozen weights on WildGuard and HateXplain. The user excluded additional
fine-tuning from this next step. Other proposed directions remain unrun.

The [leaderboard writing handoff](../leaderboard/WRITING-NOTES.md) records the
completed comparison, its interpretation limits, and material to carry into
the research paper, magazine article, media article, and learning skill.

## Teaching series parked for later

The proposed [eight-week student curriculum](STUDENT-CURRICULUM.md) was recorded on
29 October 2026. It follows governance from organizational intent through
moderation, language models, labeling, policy authoring, evaluation, and operation.
The outline includes companion readings, exercises, and a six-week option. The
articles have not yet been written; the user asked to revisit them later.
