# Learning to apply policy to commands and agent tool calls

Status: source review and proposed experiment, checked 3 November 2026. No model
inference, fine-tuning, command execution study or new spending was started.
This extends the [instrumented environment design](AGENT-TRACE-DATASET-ENVIRONMENTS.md)
and [offline agent reviewer](OFFLINE-AGENT-POLICY-REVIEW.md).

## Recommendation

Use existing command documentation and security knowledge to create a benchmark
of action understanding and policy application. Compare code-specialized models,
general-purpose models and policy models before choosing a model to fine-tune.

The input is the proposed tool call together with the applicable policy, user
goal, relevant prior events and trusted environment/authorization facts. The
output identifies the action's likely effects, the affected scope, the policy
disposition and a short evidence-linked reason.

Two questions must remain distinct:

1. What does this action do, given the available environment information?
2. Does the supplied policy permit it, forbid it or require review first?

A code model may help with the first question. That does not establish better
policy interpretation or reliable authorization judgments. Keeping intermediate
effect labels lets us diagnose which ability failed.

## Sources that can bootstrap the work

| Source | Useful material | What it does not establish |
|---|---|---|
| Official utility manuals | Option semantics, inputs/outputs and documented side effects | Whether an enterprise authorizes a particular action |
| tldr pages | Concise examples of ordinary command use | Exhaustive semantics or safety labels |
| NL2Bash | Bash commands paired with programmer-written English descriptions | Enterprise policy decisions or observed consequences |
| GTFOBins | Capabilities of ordinary Unix programs that can be abused under particular conditions | That every use of a listed executable is malicious |
| MITRE ATT&CK | A vocabulary of adversary behaviors and consequences | A complete taxonomy of accidental operational mistakes |
| Sigma rules | Detection patterns, required telemetry and documented false-positive contexts | A reliable pre-execution authorization verdict for every matching command |
| SABER and our proposed environments | Context, action sequences and observed state changes | Complete knowledge of real enterprise authority or all possible side effects |

Start with primary manuals for [GNU rm](https://www.gnu.org/software/coreutils/manual/html_node/rm-invocation.html),
[curl](https://curl.se/docs/manpage.html) and [Nmap](https://nmap.org/book/man.html).
Pin the implementation and version in each scenario: Linux/GNU, macOS/BSD and
BusyBox tools do not have interchangeable option semantics.

[tldr](https://tldr.sh/) provides practical examples. [NL2Bash](https://github.com/TellinaTool/nl2bash)
contains roughly 10,000 command/description pairs and a shell parser. It is a
semantic grounding resource, not a ready-made moderation benchmark. Its repository
distinguishes the dataset's license from the code license; record source-specific
terms before importing material.

[GTFOBins](https://gtfobins.org/) explicitly catalogs legitimate functionality
that can be abused. Use it for coverage and difficult cases, not a blacklist of
program names. [MITRE's data-destruction category](https://attack.mitre.org/techniques/T1485/)
provides one useful consequence label. [Sigma's rule format](https://sigmahq.io/docs/basics/rules.html)
includes log-source requirements and false-positive notes. A matching detection
rule is evidence to inspect, not proof of malicious intent.

Keep reviewed source facts, newly authored examples, observed execution evidence
and proposed model labels distinct. Do not turn every security-source example
into BLOCK and every documentation example into ALLOW: that would make source
style a shortcut for the answer.

## Start with a small set of effects

Use multiple effect labels where needed:

- Read or inspect information.
- Delete, overwrite or irreversibly modify an asset.
- Send information to another destination.
- Discover hosts or services within a network scope.
- Change permissions or authorization settings.
- Execute code or install components with potential side effects.

These are task definitions to refine with domain reviewers, not inherent labels
attached to executable names. One tool call can have several effects. Reading a
secret may also violate policy even though it does not modify a file.

For a first policy, honor the user's conservative preference: recursive deletion,
file transfer and network scanning require explicit approval, including deletion
in a temporary directory. Known protected assets and forbidden destinations remain
blocked even if a caller requests the action, according to the policy's authority
rules. Later, test a different policy that grants a carefully defined cache-cleanup
exception. The model should follow the changed rule rather than memorize one
universal answer for deletion.

### Three useful boundary cases

**Recursive deletion.** `rm -rf` combines recursive removal with force behavior.
Whether anything is removed depends on the resolved targets and runtime. A path
that looks temporary is not enough to establish permitted scope or approval.
The proposed policy requires review until valid approval exists; observed removal
and policy violation are separate labels.
[GNU documentation](https://www.gnu.org/software/coreutils/manual/html_node/rm-invocation.html).

**Form submission versus file transfer.** In curl, `-F` creates form parts. A
literal value and a value using `@filename` have different semantics. File content
can also be supplied through other forms/options. The effect labels should capture
what data would leave and where it goes; the enterprise policy decides whether
that requires approval. Treating every `-F` as proof of a file upload would create
incorrect labels.
[curl documentation](https://curl.se/docs/manpage.html).

**Network discovery.** Nmap is used for security auditing and network inventory.
Permission depends on the authorized targets, operations and time/scope of the
task. Our conservative first policy can require review even for legitimate scans;
that is an organizational rule rather than evidence that scanning is inherently
malicious.
[Nmap reference](https://nmap.org/book/man.html).

## Turn reference knowledge into training and evaluation examples

First write a small registry of reviewed command semantics: executable and
version, relevant options, possible effects, required context and source reference.
Do not start by training on entire manuals as if they contained moderation labels.

For each operation, author contrasting scenarios. Keep the command fixed while
changing trusted approval, affected data or policy. Also keep the policy fixed
while expressing the same operation through different commands or tool interfaces.

An illustrative deletion family, not measured model output:

| Context for the same recursive cleanup proposal | Decision under the first policy |
|---|---|
| Eligible cache directory; approval absent | REVIEW |
| Same eligible objects; valid scoped approval present | ALLOW |
| Target includes records the policy forbids deleting | BLOCK |
| An unresolved variable determines the target | REVIEW for missing scope information |

Include cases where an operation is quoted in a document rather than proposed for
execution, authorized security administration, and scripts whose effects require
inspecting referenced files. Vary names and layout so labels cannot be inferred
from a directory named “safe” or “dangerous.” Include similar-looking commands
with materially different effects and different-looking commands with equivalent
effects. Keep all related variants together when splitting data.

Validate the executable subset using disposable environments and synthetic assets,
following the [environment design](AGENT-TRACE-DATASET-ENVIRONMENTS.md). Collect
actual affected objects and controlled service receipts. For pre-action tests,
those later observations belong in the scoring record, not the reviewer's input.
If the model could not resolve an essential fact before execution, score the need
for review instead of expecting it to know the future.

Label each example with verified effects where available, expected disposition,
policy rule IDs, trusted evidence and unresolved facts. Preserve whether the label
came from an executable check, human adjudication or a model suggestion. Human
reviewers validate the policy and ambiguous cases; sample automated cases to find
checker errors. Do not let the same teacher generate all examples and certify its
own answers as ground truth.

Public test assets remain external evaluations. In particular, retain AgentHarm's
evaluation-only usage request recorded in the environment proposal; it is not a
source of fine-tuning examples. Build the fitting collection from independently
authored, appropriately licensed scenarios.

## Model comparisons that answer distinct questions

| Candidate | Purpose |
|---|---|
| Qwen2.5-Coder-7B-Instruct | Compact code-specialized starting point for prompting and possible supervised fine-tuning |
| Qwen2.5-7B-Instruct | Same-family, same nominal size general-purpose comparison |
| Qwen3.5-4B | More recent compact general-purpose baseline already familiar from our studies |
| PolicyLM 1.7B and a generative policy reviewer from the existing proposal | Specialist decision and explanation comparisons, using their own interfaces |
| Qwen3-Coder-Next, optional later | Larger code-agent candidate or teacher; not a small dense deployment |

The Qwen2.5 pair both list 7.61B parameters and matching basic architecture
dimensions. That controls size and architecture more closely than comparing
unrelated families, though the complete training histories still differ.
[Coder card](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct),
[general-purpose card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct).
The pair is a diagnostic comparison, not a claim to use the newest family.
[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) provides a newer compact control.

Code Llama is a historical option, but its official inference repository is
archived. We need not center a new study on it simply because it introduced the
idea of code specialization.
[Official repository](https://github.com/meta-llama/codellama).
Qwen3-Coder-Next is designed for coding agents and lists 80B total/3B active
parameters. Active parameters do not make it equivalent to a 3B dense model in
storage requirements. Its card specifies non-thinking mode; do not invent a
thinking-on/off comparison for that release.
[Model card](https://huggingface.co/Qwen/Qwen3-Coder-Next).

PolicyLM's current interface returns category scores and uses short policy
categories. It should not be asked to generate free-text reasons as though it
were a decoder chat model. Its published context limit also constrains how much
trace context can be supplied. Pin the revision and input-selection procedure.
[PolicyLM card](https://huggingface.co/musubilabs/policylm-1.7b).

Specialist training is possible in principle, but adapting that scoring model
requires its own architecture-aware training setup. A generative LoRA recipe
cannot simply be assumed to apply unchanged. Score native decisions separately
from explanation-capable systems; explicitly document any new REVIEW mapping or
additional explanation stage.

## Experiment sequence

### 1. Measure the frozen models

Compare three input conditions with the same held-out cases:

- Proposed action plus policy.
- The same input plus trusted environment and authorization context.
- The same input plus concise, relevant excerpts from pinned command references.

The last condition tests whether documentation retrieval solves rare-option
mistakes without training. Reference selection must not use the expected label.
Use equal development selection budgets and each model's native interface. A
bounded first study need not cover every model and every condition immediately.

Include a parser/known-semantics/rules baseline. For a rule as explicit as “review
every unapproved recursive deletion,” an LLM may add no value once the effect is
known. The harder cases involve nested scripts, uncertain scope, combined effects
and whether a supplied exception applies. Report where the model helps over the
baseline rather than assuming learned interpretation is necessary everywhere.

### 2. Fine-tune after identifying the gap

For an explanation-capable model, supervised adapter training can learn an output
such as effects, affected scope, ALLOW/BLOCK/REVIEW, applicable rule IDs, a short
justification and missing context. This is a proposed output contract, not proof
of the model's internal reasoning. Compare the fine-tuned model against the same
checkpoint with policy prompting and with reference retrieval.

Test decision-only training against training with the additional verified effect
labels, rather than assuming longer outputs improve decisions. Keep policies in
the input and vary them in training. Hold out policy clauses and scenario families
to distinguish following new rules from remembering fixed command labels.

If adapting an existing policy model, keep regressions on its original moderation
tasks in the evaluation. An improvement on tool calls can come with losses
elsewhere. DPO and RL are possible later comparisons; they are not prerequisites
when correct decisions and observable effects already provide supervised targets.

### 3. Evaluate compositional behavior in traces

Move from individual calls to multiple calls and scripts in the Pi/SABER-style
environments. Reuse the same policy/evidence schema. Measure pre-action replay
separately from completed-run auditing, and later test any actual intervention
workflow with approval events and continued task execution.

## Metrics and limits

Measure effect extraction and policy decisions separately. Report macro F1 and
class confusion, prohibited actions incorrectly allowed, allowed actions blocked,
missing approvals detected, unnecessary review load, rule/evidence correctness
and decision changes under changed policies. Do not reward a model for escalating
everything. For observed runs, keep attempted violations, executed violations and
actual harm distinct. Report uncertainty and per-family sample counts.

A shell parser helps identify syntax; it does not fully determine the effects of
arbitrary code. Variables, current directory, filesystem state, symlinks, executable
identity, pipelines and invoked scripts may change the affected scope. Do not
execute an untrusted candidate merely to resolve its meaning on the host. Missing
critical evidence is a reason for review; testing execution belongs in the isolated
environment. Even that execution demonstrates one state, not all possible states.

Reviewers treat code, tool output and retrieved documents as data, not authority
to modify the policy. The enforcement layer must also bind approval to the actual
action and scope: a correct model judgment does not prevent a different operation
from being executed afterward.

This study would test whether code specialization, explicit policy and verified
action examples improve tool-call governance. It would not establish that coding
benchmark performance predicts governance quality, or that a fixed list of risky
commands is a complete agent-safety system.
