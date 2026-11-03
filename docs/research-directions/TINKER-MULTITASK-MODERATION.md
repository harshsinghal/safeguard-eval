# Tinker: a path from policy experiments to a trained moderation model

Status: source review and proposed experiments, checked 3 November 2026. No Tinker
training, model upload, paid API call or new spending was started. These are
opportunities to test, not measured Tinker results or a provider endorsement.

## Recommendation

Tinker is a plausible platform for training one model across several moderation
tasks while keeping our data, evaluation and policy decisions under our control.
Start with Qwen3.5-4B, supervised learning and short categorical outputs. Compare
one shared adapter with separate task adapters. Add distillation and reinforcement
learning only after establishing that baseline.

The main question is whether training across tasks reduces both false blocks and
missed violations without sacrificing a task that a specialist already handles
well. Our existing benchmark suite makes that question testable. A good average
alone would not answer it.

## What the platform provides

We write the training loop, choose examples and define the learning objective.
Tinker runs the model computations and manages training infrastructure. Its public
SDK exposes forward/backward computation, optimizer steps, sampling and saved
training states. This removes GPU orchestration from our experiment; it does not
choose a defensible dataset or policy boundary for us.
[SDK overview](https://tinker-docs.thinkingmachines.ai/).

The documented standard path is LoRA: train relatively small adapter matrices
while the original model weights remain frozen. Those adapters still change the
model's behavior through learned parameters. Thinking Machines' 15 October update
also announces full fine-tuning in beta. Treat that as access to confirm, rather
than assuming the standard LoRA SDK offers unrestricted full-weight training.
[LoRA documentation](https://tinker-docs.thinkingmachines.ai/tinker/lora-primer/),
[beta announcement](https://thinkingmachines.ai/news/one-year-of-tinker/).

| Capability | Opportunity for this research |
|---|---|
| Supervised fine-tuning | Learn the correct moderation decision from our labeled fitting examples, with loss on the answer rather than reproducing the submitted content |
| Decision-model recipe | Return probabilities over supplied labels, allowing the same error and score analysis used in our existing studies |
| Custom probability losses | Fit reviewed soft targets or directly test a probability-scoring objective |
| Prompt distillation | Teach a fixed policy to a model so it can use a shorter instruction at inference |
| Model distillation | Train a smaller student from selected teachers' outputs, subject to licenses and provider terms |
| DPO and RL | Learn from reviewer preferences or an explicitly defined reward; evaluate whether this adds value over supervised training |
| Checkpoint export | Keep or merge the adapter for deployment outside Tinker, subject to the model license and serving compatibility |

These are documented mechanisms, not claims that they improve our moderation
scores. Sources: [supervised token losses](https://tinker-docs.thinkingmachines.ai/tinker/losses/),
[decision recipe](https://tinker-docs.thinkingmachines.ai/cookbook/recipes/decisions/),
[custom losses](https://tinker-docs.thinkingmachines.ai/tinker/losses/custom/),
[prompt distillation](https://tinker-docs.thinkingmachines.ai/cookbook/recipes/prompt-distillation/),
[model distillation](https://tinker-docs.thinkingmachines.ai/cookbook/recipes/distillation/),
[DPO](https://tinker-docs.thinkingmachines.ai/cookbook/preferences/dpo-guide/),
[RL](https://tinker-docs.thinkingmachines.ai/cookbook/rl/).

The decision recipe uses a normal language model's answer-token probabilities,
restricted to the supplied choices. It is a useful functional alternative to a
decision API, not evidence that it reproduces Jev's undisclosed architecture or
Kev/Clef's custom heads. A one-token answer still requires processing the input;
its latency on long skill packages needs measurement. Probabilities also require
calibration checks before being treated as reliable confidence.

Custom losses operate on exposed token log-probabilities. I found no documented
standard interface for arbitrary hidden-state extraction, replacing attention
with a bidirectional encoder, attaching an unrestricted neural head, or uploading
any Hugging Face architecture. Our Jina/Liquid/custom-head experiments therefore
remain a separate route.

## Which models fit our purpose?

The current catalog includes Qwen3.5-4B and 9B. The former is my first candidate
because we have relevant frozen-model comparisons; the latter tests capacity.
Nemotron-3.5-Lightning-30B-A3B is a later efficiency candidate. Its active parameter
count is not its weight-storage requirement. I did not find PolicyLM, Shieldstral,
Kev, Clef, Liquid, Gemma or GPT-OSS Safeguard in the listed training models. Listed
GPT-OSS releases are distinct from Safeguard. Availability should be checked with
the account's server capabilities before a run; some catalog entries retain
retirement notices.
[Model catalog](https://tinker-docs.thinkingmachines.ai/tinker/models/models_and_pricing/).

Thinking Machines also offers its own open-weight Inkling family. Inkling-Small
has 276B total and 12B active parameters; it is not a small dense deployment like
PolicyLM. It could be a teacher or quality comparison, but I would not start there
when our first question concerns a compact, self-hostable classifier.
[Inkling](https://thinkingmachines.ai/news/introducing-inkling/),
[Inkling-Small](https://thinkingmachines.ai/news/inkling-small/).

## Two different products we could train

**An adaptable policy interpreter** receives the policy, trusted task context and
submitted content, then scores whether that content violates that policy. This
fits our central research theme: policy owners can change rules without a new
training run. It needs training examples with varied policies and exceptions,
including reviewed cases where the same content changes label when the policy
changes. Testing held-out policies is essential. Training on several familiar
benchmark names alone would not demonstrate general policy interpretation.

**A classifier for fixed rules** learns a stable set of decisions from labeled
examples and can receive a short task instruction. Prompt distillation could
remove much of the repeated policy text. This might reduce input cost, but a
material rule change can require another training and validation cycle. It would
not make policy governance disappear; it moves part of that specification into
training data and adapter weights.

The first pilot should keep the policy explicit. That lets us compare prompting
with training while preserving the policy owner's ability to inspect the rule.

## Mapping the existing evidence to a training study

Use [the dataset inventory](../datasets/README.md) and each frozen study's split
manifests. Never treat all sources as interchangeable instances of a single
undefined label called unsafe.

| Task | Existing evidence | Training and evaluation boundary |
|---|---|---|
| Harmful user requests | WildGuardMix, prompt harmfulness only | Preserve the task; response harm and refusal were not evaluated |
| Hate speech | HateXplain, hate versus non-hate | Offensive but non-hate content remains an important allowed boundary |
| Injection detection | Deepset and xTRam1 | Harmful intent and instruction-boundary attacks are different; retain source ambiguity notes |
| False-alarm and jailbreak stress tests | NotInject and JailbreakBench attack artifacts | Keep these evaluation-only; report false-block rate or detection rate, not invented balanced accuracy on a one-class collection |
| Malicious source code | OMCBench | Separate package/repository groups; vulnerability is not automatically malicious intent |
| Agent skill text and packages | ProtectSkills/MaliciousSkillBench and lxyeternal/MalSkillBench | Distinct datasets; preserve source/template/author grouping and full-file versus document-only views |
| Cyber-assistance requests | CyberSecEval MITRE/FRR adaptation | Source and label are confounded; do not make this our primary evidence of generalization |

These tasks can overlap. A request can be both hateful and an injection; a
non-hate label does not establish that it is free of malicious code. A practical
first interface is one shared model answering a specified policy question with
ALLOW/BLOCK scores. Simultaneous multi-category detection would need appropriate
multi-label annotations, rather than treating categories as mutually exclusive
or unannotated categories as negative.

Our cyber Jina result illustrates why data work comes first. Matching all 330
source labels is not proof of recognizing all malicious intent when the classes
come from different collections. More training, including RL, could strengthen
that shortcut. For stronger evidence we need independently labeled examples with
benign and harmful cases from the same sources, plus unseen sources.
[Latest study](../cyber-skill-guardrails/README.md).

Dataset availability also does not automatically confer commercial training or
redistribution rights. MalSkillBench's research restriction and unclear terms on
some injection sources must carry into a proposed training-data manifest.

## A small sequence that would answer useful questions

1. **Establish the matched baseline.** Use Qwen3.5-4B with its frozen weights,
   explicit policies and Tinker's categorical scorer. This separates the effect
   of a new interface from the effect of training. Keep the earlier specialist
   and decision-model results as external references, with their own interfaces.
2. **Compare separate learning with shared learning.** Fit a task-specific LoRA
   for each initial task and a single LoRA on a balanced mixture. Start with
   harmful requests, hate speech and injection; then add the artifact tasks.
   Match exposure per task where feasible and report total training/search cost.
   Measure gains and negative transfer separately for every task.
3. **Train the shared model to follow policy changes.** Add fitting-only,
   expert-reviewed exceptions and policy contrasts. Test previously unseen
   content and separately held-out policies. Compare with fixed-rule training.
4. **Test distillation if the shared model remains weak.** Use complementary
   teachers or our ensemble to propose targets on training data only. Validate
   disagreements against source labels and policy-owner review. Generate teacher
   targets out of fold if the teacher or ensemble was fitted on the same rows.
   Teacher confidence is not ground truth, and distillation rights need checking.
5. **Only then test an RL increment.** Start from the supervised checkpoint,
   keep a matched supervised continuation control, and use a preregistered reward
   for correct decisions with declared costs for false blocks and misses. Report
   additional training tokens, cost and all task regressions.

These steps are a proposal, not a registered run. A bounded protocol, exact data
rights, budget and model access would be settled before execution.

RL is possible, but it is not inherently superior for this problem. With known
binary labels, supervised learning already supplies direct feedback about the
right answer. Cost-sensitive losses and task balancing can also be implemented
without RL. Preference learning becomes more interesting when reviewers compare
competing explanations or nuanced policy applications. RL may be more useful
later for sequential actions such as escalating to another model under a review
budget. Neither method supplies missing truth or fixes ambiguous labels.

## How we would judge success

Select using development data only. Report balanced accuracy, macro F1, MCC,
false-block rate and missed-violation rate for each binary benchmark, with paired
uncertainty and source slices. Add Brier score, probability calibration and
precision-recall analysis when using probabilities. Keep one-class stress tests
separate. An equal-task summary and the weakest task should accompany all
per-task results, rather than allowing a large, easy dataset to dominate.

Record the SDK, renderer, resolved base-model identity, policy, adapter and
checkpoint for every arm. If the service does not expose an immutable base
revision, disclose that reproducibility limit instead of assuming that a shared
model name makes a Tinker run identical to our earlier self-hosted checkpoint.

Register acceptable per-task regressions and operational error limits before
selection. A review band needs an explicit coverage/error tradeoff; it must not
earn free accuracy by abstaining on every hard case. The existing binary labels
do not themselves define a third REVIEW ground-truth class.

Retain the old tests for historical comparability and report that they have been
evaluated before. This is not a claim that our earlier training used test labels.
For a stronger generalization claim, add a fresh source- or family-held-out
evaluation. Deduplicate across the entire training/evaluation mixture, preserve
original test membership, and do not convert observed test mistakes into new
training examples while continuing to call that set held out.

## Cost, export and enterprise use

The published standard-context training rates are $0.737 per million tokens for
Qwen3.5-4B and $1.463 for Qwen3.5-9B. As an illustration, 20,000 examples averaging
1,000 processed tokens over three epochs would imply 60 million training tokens:
**$44.22** for 4B or **$87.78** for 9B. This is arithmetic, not a quote or a complete
experiment budget. Evaluation, teacher calls, RL sampling, repeated searches and
storage are additional. Policy text and package length matter to token counts.
Checkpoint storage is listed at $0.10/GB/month; recheck rates and actual billing
before execution. [Pricing](https://thinkingmachines.ai/tinker/pricing/).

Tinker documents downloading adapters, merging them into model weights and
building PEFT adapters for external serving. Actual adapter support depends on
the model family and inference engine. Export therefore gives us a route to
self-hosting, not a promise that every checkpoint runs unchanged in any server.
Production sampling is beta; the separately priced serverless offering currently
lists only Inkling and Inkling-Small and cautions against intensive production
use. [Deployment](https://tinker-docs.thinkingmachines.ai/cookbook/deployment/basics/),
[serverless scope](https://tinker-docs.thinkingmachines.ai/tinker/models/models_and_pricing/#serverless-inference-beta).

Thinking Machines states that customer content is not used to improve its own
models and advertises enterprise access and network controls. That does not mean
training data never reaches the provider or that zero retention is automatic.
Sensitive enterprise training would require the applicable retention, residency,
subprocessor and contractual arrangements to match the intended use.
[Service commitment](https://thinkingmachines.ai/legal/terms/),
[security announcement](https://thinkingmachines.ai/news/one-year-of-tinker/).

There is a relevant precedent for the earlier Glean discussion: Glean reports
using Tinker for LoRA training of Waldo through DPO followed by RL. That model
plans enterprise searches; it is not evidence for our moderation hypothesis.
[Glean's account](https://www.glean.com/blog/waldo-launch).

This direction extends the project from asking which policy/model combination
works to asking whether we can teach a compact model to apply several policies
well. Policy owners still define the boundaries and resolve disagreements;
engineers still build the training, evaluation and deployment system. Tinker
could take over much of the training infrastructure between those responsibilities.
