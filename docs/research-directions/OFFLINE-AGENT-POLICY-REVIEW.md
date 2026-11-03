# From guard models to an offline reviewer of agent runs

Status: source review and proposed research direction, checked 3 November 2026.
No inference, training, GPU rental or paid API call was started. The study below
is a proposal, not a registered protocol or a completed experiment.

The subsequent [environment and labeling design](AGENT-TRACE-DATASET-ENVIRONMENTS.md)
adds AgentHarm, AgentHazard and SABER, including SABER's published Pi adapter. It
proposes deriving labels from observable outcomes under reviewed rules, while
retaining independent human assessment for ambiguous policy judgments.

## Recommendation

Build and evaluate an offline policy reviewer before training another guard model.
Give it a completed agent run, the applicable policy and trusted context. Ask it
to identify violations, cite the relevant events and explain the decision briefly.
Use its findings to prioritize human review.

This changes the question from “is this text harmful?” to “what happened, which
rule applies, and what evidence supports that judgment?” Offline review allows
more context and computation without delaying an employee's request. It still
needs a throughput and cost budget, and it cannot prevent an action that already
occurred. ALLOW/BLOCK/REVIEW would describe policy dispositions, not enforcement
actions performed by the reviewer.

The central hypothesis is that a model combining explicit policies with evidence
from an entire interaction can produce more useful judgments than an isolated
prompt classifier. A second hypothesis is that a smaller model can learn this
task from reviewed examples. Neither follows automatically from our existing
classification results.

## What the existing guard families teach us

### Granite Guardian: evaluate a criterion in its context

IBM's Granite Guardian 4.1-8B accepts custom criteria through its Bring Your Own
Criteria interface. It supports thinking and no-thinking modes, documents and
tool definitions, with a prescribed scoring schema. Its documented uses include
monitoring and spot checks. The native binary score needs an explicit mapping to
our policy disposition; the meaning of “yes” depends on the criterion. IBM also
warns that generated reasoning may not faithfully describe the decision process.
[Model card](https://huggingface.co/ibm-granite/granite-guardian-4.1-8b),
[repository](https://github.com/ibm-granite/granite-guardian).

The earlier Granite Guardian paper describes supervised training of instruction
models using human annotations and synthetic safety examples, including difficult
benign cases, jailbreaks and retrieval-related risks. That is a useful recipe:
teach the distinction between a violation and a legitimate request that shares
its vocabulary. These historical training details should not be assumed to
describe every stage of the newer 4.1 release.
[Technical report](https://arxiv.org/abs/2412.07724).

### Qwen3Guard: preserve ambiguity and improve the labels

Qwen3Guard offers generative and streaming variants in 0.6B, 4B and 8B sizes.
The generative interface reports Safe, Unsafe or Controversial, categories and,
for responses, refusal information. Controversial captures policy-dependent
boundaries; it is not automatically our REVIEW label or calibrated uncertainty.
The streaming variant uses token-level classification heads.
[Official repository](https://github.com/QwenLM/Qwen3Guard).

Its report describes supervised specialization of Qwen3 instruction models,
cross-fitted disagreement analysis and teacher-assisted label refinement. The
lesson is to investigate ambiguous or inconsistent training labels, not merely
increase model size. Its RL application uses the guard as a reward for training
an assistant; that is not evidence that the guard itself was trained with RL.
[Technical report](https://arxiv.org/abs/2510.14276).

### Llama Guard: clear categories and a deliberately constrained output

Llama Guard 4 is a 12B dense model derived by pruning Llama 4 Scout and then
post-training it for safety. It produces safe/unsafe judgments and category IDs.
Its taxonomy includes Code Interpreter Abuse, but that does not establish broad
competence at reviewing malicious software or complete enterprise agent runs.
It is a useful classification control, with its documented prompt template, rather
than a model we should require to generate an unsupported explanation format.
[Model card](https://huggingface.co/meta-llama/Llama-Guard-4-12B).

### GPT-OSS Safeguard: connect a written rule to a short justification

OpenAI's Safeguard guide describes custom policies with definitions, decision
criteria, exceptions and examples. It explicitly supports a decision followed by
a short rationale citing policy rules. It also discusses triage and offline
analysis. This is close to the proposed reviewer. Test policy bundling rather
than assuming that adding more rules preserves accuracy.
[Policy and rationale guide](https://developers.openai.com/cookbook/articles/gpt-oss-safeguard-guide).

Our desired explanation is a concise, checkable justification. We do not need a
transcript of private internal reasoning. A convincing explanation can accompany
a wrong decision, so label quality and explanation quality need separate tests.

## What this means for our existing evidence

Our studies support testing the combination of policy, model interface and input
evidence. They do not yet establish reliable agent-run review or explanation.
For example, the completed skill-package study found Jev at 95.51% accuracy with
companion files versus 88.09% with SKILL.md alone. That motivates supplying the
evidence an auditor needs; it does not predict its accuracy on traces.
[Completed study](../cyber-skill-guardrails/README.md).

Keep the limitations attached to those results: most malicious skill examples
were generated, and the cyber-assistance comparison has source/label confounding.
We have tested Llama Guard 4 classification in that study. Granite Guardian and
Qwen3Guard are proposed additions here, not completed rows in our leaderboard.

## Define the job before choosing the model

Consider an agent that uploads a file. The same tool call could be permitted for
a public document sent to an approved destination, prohibited for confidential
data sent outside an allowed boundary, or unresolved when the record omits the
authorization needed to decide. Network access by itself is not a violation.

The reviewer should receive:

- The policy version, rule IDs, exceptions and what constitutes sufficient
  evidence for a violation or for escalation.
- Trusted task context, such as the user's authorized scope and approved
  destinations. A claim inside a retrieved document is not authorization.
- The ordered user messages, assistant outputs, tool calls, arguments and
  results, with stable event IDs and source boundaries.
- Relevant code or skill files and a manifest of missing or truncated material.

Distinguish a malicious request, a safe refusal, a proposed action, an attempted
tool call and an observed outcome. A harmful request followed by a safe refusal
must not become an agent violation merely because the harmful words appear in
the transcript. When a tool result is missing, the reviewer must not invent a
successful action.

The output should identify the evaluated event or behavior, a disposition,
applicable categories and rule IDs, supporting event IDs, a brief justification,
and any missing information. Separate the severity of a potential incident from
certainty that it occurred. A run can have several findings and more than one
category; it need not have one mutually exclusive harm label.

Illustrative output, not a model result:

> **REVIEW — external data transfer.** Rule DATA-2 requires approval before
> sending confidential material to an external destination. Event 12 contains
> an upload request, but the record provides neither the file's classification
> nor the required approval. The tool result is also absent, so completion is
> unconfirmed.

Review the recorded material as untrusted data. The reviewer should not execute
submitted skills, follow instructions in tool outputs or open embedded URLs as
part of judging them. Keep the first implementation read-only.

## First experiment: can current models do the reviewing?

Start with three reviewers, before any weight updates:

| Candidate | Proposed role |
|---|---|
| GPT-OSS Safeguard 20B | Policy interpreter producing a decision and short rule-linked rationale |
| Granite Guardian 4.1-8B | Custom-criterion reviewer using its native scoring interface; compare thinking on/off |
| Qwen3.8-27B | General-purpose reviewer; compare thinking on/off under a fixed policy and output contract |

Qwen3.8-27B supports a thinking toggle. Its coding and agent capabilities make
it a plausible candidate, not an established superior judge.
[Qwen model card](https://huggingface.co/Qwen/Qwen3.8-27B).

Use Qwen3Guard-Gen-8B and our existing Llama Guard 4 configuration as native
classification controls. Do not silently change their templates to demand the
same JSON or three-way decision. Record unsupported outputs as capability
differences. A two-stage system that adds a separate explainer must be labeled
and costed as such.

Within each compatible model, compare a decision-only final answer with a
decision plus short evidence-based justification. Separately compare thinking
settings while holding the policy and final-answer requirements fixed. Visible
explanation length and internal reasoning budget are different variables.
Freeze token budgets and parsing rules on development data; count truncations,
refusals and malformed answers rather than silently excluding them.

### Data: retain familiar tasks and add actual interactions

Use our existing benchmark manifests for classification regression checks. They
cover harmful prompts, hate speech, injection, code and skills, but their labels
do not provide ground truth for enterprise authorization or REVIEW decisions.

R-Judge is a more direct starting point: 569 multi-turn interaction records with
human safety labels and risk descriptions. It separates safety judgment from
identification of the risk. Its original explanation scoring uses an automated
judge, which we should supplement with independent human assessment. Keep labels
and reference descriptions out of model inputs. This proposal reserves it for
external evaluation, not prompt optimization or training, subject to a data and
license audit. Its public status means unknown pretraining exposure remains a
limitation.
[Paper](https://aclanthology.org/2024.findings-emnlp.79/),
[dataset and evaluation code](https://github.com/Lordog/R-Judge).

Add a small, independently annotated enterprise collection with development and
held-out cases. Pair similar traces with different trusted authorization or
policy exceptions, and add cases where the correct decision is REVIEW because
essential evidence is absent. Include harmless security analysis, quoted attacks,
safe refusals and instructions that try to manipulate the reviewer itself.

Group related runs, templates and scenario variants before splitting; do not
put turns or nearly identical variants of one run on opposite sides of the split.
Keep policy-change pairs together. Document annotator disagreement and adjudicate
the labels before scoring. Hold out policy variants and scenario families where
feasible. Existing benchmark tests remain historical comparison sets; the new
collection tests the added capability.

### Success: useful decisions and verifiable explanations

| Question | Measurement |
|---|---|
| Does it identify violations? | Balanced accuracy, macro F1, false blocks and misses by task and risk category, with counts and uncertainty |
| Does it find the actual problem? | Correct rule selection, supporting evidence, missed critical events and unsupported factual claims |
| Is REVIEW useful? | Review rate, violations captured at a fixed review capacity, errors among automatically resolved cases, and missing-context detection |
| Does it help a person? | In a later reviewer study, correctness and review time with and without the model's findings |
| Can it process real workloads? | Cost per run, failure rate and completion time by trace length and category count |

For binary benchmark labels, report review/abstention coverage separately and
retain all examples in the accounting. Do not credit every REVIEW as correct or
compare accuracy on a selectively easier subset with a full-coverage baseline.
For the enterprise collection, score the independently annotated three-way
decision and its evidence requirements. A model's self-reported confidence is not
a calibrated probability.

Human raters should assess explanations without seeing the model identity.
An automated judge can assist, but a model should not be the sole authority
both generating and validating its own training targets and evaluation scores.
Choose acceptance criteria and development selection rules before the final run.

## Then train, if the baseline exposes a worthwhile gap

1. **Build a reviewed training set.** Use models to propose decisions, rule
   references and concise reasons on fitting examples. Have people resolve
   disagreements and verify evidence. Retain difficult benign cases and missing
   context, not just clear violations. Check source licenses and teacher terms.
2. **Supervised fine-tune a smaller Qwen model.** A 4B or 9B candidate could learn
   the output contract and policy application from those examples. Keep the policy
   explicit and vary it during training so the model cannot succeed by memorizing
   a fixed blacklist. Compare against the same model with prompting alone.
3. **Consider DPO only after that baseline.** Preference pairs can favor the
   correct, evidence-supported answer over a plausible but wrong one. Both the
   disposition and its justification must inform the preference. Test whether
   DPO adds value instead of assuming that fluent explanations imply improvement.
4. **Consider RL later.** Use verifiable objectives where possible. A reward
   based solely on another model's approval risks teaching agreement with that
   judge rather than better policy application.

A normal generative model can learn this input/output task; a new encoder-decoder
architecture is not a prerequisite. Compact classification models can remain
useful controls or eventual first-pass detectors, but their output heads do not
automatically supply explanations.

The [Tinker survey](TINKER-MULTITASK-MODERATION.md) describes relevant supervised,
distillation and preference-training support for Qwen candidates. Training platform
support does not imply that all proposed guard teachers are available there.

## What this study could and could not establish

It could show whether context and bounded reasoning improve judgments, whether
explanations help reviewers locate a real issue, and whether supervised training
can transfer that capability to a smaller deployable model. It could also show
negative results: more reasoning may add cost without reducing errors, or a good
classifier may produce misleading reasons.

It would not establish universal enterprise compliance, infer missing permissions,
prove that a rationale reveals the model's internal process, or validate inline
blocking. Those are separate requirements. Policy owners still define the rule
and exceptions; engineers preserve evidence and implement the interface; reviewers
resolve disputed decisions. This extends our central finding that policy authoring
and AI engineering are coupled.
