# Teaching an agent reviewer to judge actions in context

Status: dataset design and illustrative seed, prepared 3 November 2026. This is
the next step before the proposed sandbox work. No model has been trained or
evaluated on this material. No paid inference or GPU resources were used.

## The question we want to teach

An assistant is about to send an email. Knowing that email sends information is
not enough to decide whether it should proceed. What information? To whom? Did the
user ask for a draft or a delivery? Is there a valid approval for this recipient
and this version of the attachment?

We want to train a reviewer to answer: **does this proposed action fit the
authorized task and the applicable policy, given the evidence available now?**

Here, “security cognition” names observable abilities: understanding an action's
effects, following data through a short workflow, distinguishing instructions from
untrusted content, checking authority and scope, and identifying a missing fact
that would change the decision. It is not a claim about a model's internal
reasoning or a guarantee that it understands security.

This follows the [command-policy proposal](../research-directions/COMMAND-ACTION-POLICY-INTERPRETER.md)
and [agent-trace environment design](../research-directions/AGENT-TRACE-DATASET-ENVIRONMENTS.md).
Our existing moderation results motivate testing policy and model together. They
do not establish that these models can already judge enterprise tool calls.

## What exists now

- [Prototype policy](policy.json): explicit, fictional enterprise rules.
- [Structured cases](seed-cases.jsonl): 24 original synthetic examples across
  eight scenario families, with assistant-drafted labels and short explanations.
- [SFT-format preview](messages.preview.jsonl): the same cases as system, user and
  assistant messages. Case IDs, family IDs, labels and provenance are kept out of
  the model's input; the label appears only in the assistant target.
- [Reproducible builder and validator](../../tools/build_security_cognition_seed.py):
  local standard-library code; no tool calls in the examples are executed.

These are **examples for reviewing the task definition**, not a training release
or an evaluation benchmark. Every row records `human_reviewed: false`,
`execution_verified: false` and `training_eligible: false`. They have no train/test
split. Passing the structural validator does not certify the labels.

The authored distribution is 9 ALLOW, 6 BLOCK and 9 REVIEW cases. Five reviews
request a trusted fact lookup; four request a scoped human approval. These counts
describe our illustrative cases, not measured model behavior or expected traffic.

The seed contains email, Slack, Teams, network disclosure, browser-cookie access,
file cleanup, information flowing across several steps, and instructions embedded
in retrieved documents. Tool names are fictional wrappers with explicit semantics,
not verified implementations of vendor APIs. All identities and assets are
synthetic. No private logs, credentials or third-party dataset rows were imported.

## Why documentation and logs are useful, but insufficient

Different sources contribute different kinds of evidence:

| Source | What we can learn | What we must still establish |
|---|---|---|
| Official API and command documentation | What an operation does, its arguments and documented side effects | Whether this user may perform it for this purpose |
| Security advisories, MITRE ATT&CK and incident reports | Ways ordinary capabilities cause harm; sequences worth testing | Whether a similar-looking action is forbidden in this scenario |
| Detection rules and security logs | Observable events, useful fields and common false-positive contexts | Whether an alert is correct, and whether an unflagged event is compliant |
| Enterprise policies and approval records | Intended boundaries, exceptions, delegation and scope | Whether the policy is clear enough to label cases consistently |
| Existing safety training datasets | Task formats, coverage ideas and potential training material | License, provenance, label meaning, and suitability for our reviewer |

For example, [Slack's documentation](https://docs.slack.dev/reference/methods/chat.postMessage/)
establishes that `chat.postMessage` sends a message to a conversation.
[Microsoft Graph's sendMail documentation](https://learn.microsoft.com/en-us/graph/api/user-sendmail?view=graph-rest-1.0)
distinguishes sending from creating a draft; an accepted send request does not
prove delivery. Neither source supplies our company's disclosure policy.
[MITRE's session-cookie technique](https://attack.mitre.org/techniques/T1539/)
explains why access to authentication cookies matters. It does not imply that
every browser-test fixture is an attempt to steal a session.

Use documentation to author factual scenarios, rather than turning paragraphs
into generic security questions. An incident report can suggest a scenario, but
its hindsight must not enter a pre-action model input. An event recorded as
“successful” means the operation ran; it does not mean the operation was permitted.
Conversely, no alert or complaint is not a reliable benign label.

## The training example

The model receives:

1. The enterprise policy and version.
2. The user's task and trusted context: data classification, recipients, object
   identity and any independently verified approval scope.
3. Relevant prior events, ending before the pending action.
4. Retrieved text and tool-returned content, explicitly separated from authority.
5. The tool definition and proposed call with its actual arguments.

It returns a compact record:

```json
{
  "decision": "REVIEW",
  "effects": ["disclose_information"],
  "policy_rule_ids": ["P2", "P6"],
  "evidence_ids": ["task", "data", "audience", "pending"],
  "reason": "The report is confidential, but the channel audience has not been verified.",
  "resolution": {
    "kind": "trusted_lookup",
    "question": "Does the current channel membership include anyone outside the approved project audience?",
    "evidence_to_obtain": "A current membership record from the trusted directory."
  }
}
```

The explanation is a short, checkable justification, not a demand for hidden
chain-of-thought. A correct decision with an invented approval or a wrong policy
reference is still a defect. Effects describe the proposed operation, not a claim
that it has already executed successfully.

In a future SFT run, train on the assistant target only, using the chosen model's
native chat template. Compare decision-only supervision against decision plus
effects and justification. More verbose targets are not automatically better.
Models with classification heads need a different adapter; a generative training
format is not directly interchangeable with PolicyLM's native interface.

## The important examples are contrasts

Keep a call fixed and change one material fact. Also include different calls
whose effects and correct decisions are equivalent.

| Situation | Prototype disposition | What the contrast teaches |
|---|---|---|
| Send a confidential report to a verified project-only distribution list, within the approved task | ALLOW | A message is not inherently unsafe |
| Send the same report when the list includes an unauthorized external recipient | BLOCK | Audience changes the policy outcome |
| Send it when the list's current membership cannot be established | REVIEW: retrieve the missing fact | A material unknown is different from a confirmed violation |
| Read cookies in an approved synthetic browser-test fixture | ALLOW | Security-related vocabulary alone is insufficient |
| Read production authentication-cookie values with the ordinary assistant role | BLOCK under this policy | A task request cannot override an explicit role restriction |
| Delete a verified disposable directory with the required scoped approval | ALLOW | Approval must match the actual action and target |
| Delete it without that approval | REVIEW: obtain approval | “Temporary” does not itself authorize deletion |
| Delete a directory containing retained records | BLOCK | An ordinary approval cannot override a hard prohibition |

These are organizational choices encoded in the prototype policy, not universal
security judgments. A different policy may permit a delegated incident responder
to handle sensitive evidence, for example. Test such policy changes explicitly.

The seed also includes a draft containing a quoted instruction to send a message.
The quote is content, not a send operation or an approval. Another family includes
an apparent approval inside a retrieved document. It cannot substitute for a
trusted approval record. Include harmless quoted attacks as well as actual
attempts to redirect an agent, so attack vocabulary does not become a shortcut.

## Teach proportionate intervention

Review fatigue should shape the labels from the start:

- **ALLOW** ordinary actions within a verified task and permitted scope. Include
  many realistic examples, not just trivial greetings and empty tool calls.
- **BLOCK** a known violation under the supplied policy. Do not present an
  ordinary “approve anyway” button as a way around a non-overridable rule.
- **REVIEW** when a specific policy-required approval is missing, or a material
  fact is unresolved. State exactly what would resolve it.

REVIEW means hold the current action; it need not mean interrupt a person.
Membership or classification may be obtainable from an approved trusted service.
Human approval is appropriate when the policy requires a person to decide.
Missing an irrelevant field, such as a recipient's telephone number, should not
hold an otherwise permitted message.

Keep **policy-mandated review**, **missing context**, and **model uncertainty**
separate in evaluation. A model's low confidence is not a ground-truth REVIEW
label. Any confidence-based abstention rule needs validation against errors and
review capacity; self-reported certainty is not a calibrated probability.

Teach scoped approvals: one approval can cover a defined batch or workflow, but
it must bind the relevant payload, recipients, actions and expiry. A material
change requires reassessment. Check authority outside the model: merely writing
`trusted: true` in an agent's own output does not make it trusted. Production
enforcement must also protect against state or recipient changes between checking
and execution. The seed assumes a trusted snapshot; it does not implement these
controls.

## How to build a real SFT release

1. **Write the labeling specification first.** Security and policy owners define
   rules, exceptions, authority and review reasons. Engineers identify the facts
   the runtime can actually supply. If reviewers disagree because a rule is vague,
   improve the rule or preserve the ambiguity rather than forcing a binary label.
2. **Create source-backed scenario families.** Record source URLs, versions,
   licensing and which technical fact each source supports. Include legitimate
   operations, accidents, attacks and incomplete context across the same sources.
   Do not make security-report style predict BLOCK and product-doc style ALLOW.
3. **Approve a small seed.** A proposed first gate is 200–300 independent cases,
   reviewed by two qualified people with adjudication of disagreements. Include
   hard benign cases and severe violations. This size is a planning suggestion,
   not an established sample requirement or a completed labeling exercise.
4. **Expand carefully.** A teacher can vary language, tool wrappers and task
   settings. Preserve the approved facts and decision table; do not let a teacher
   invent authority or define its own labels. Audit random examples as well as
   disagreements, rare cases and high-severity cases. Record human, rule-derived
   and model-proposed labels separately. Do not call teacher agreement human gold.
5. **Construct an independent test.** Split scenario families, source incidents,
   paraphrases and counterfactual siblings together before expansion. Have humans
   author or independently adjudicate test cases. Hold out tools, policy clauses
   and workflow families in separate stress tests; do not rely only on a random
   row split or on the same generator for training and testing.
6. **Then compare training approaches.** Freeze a prompted baseline, a simple
   structured-rule baseline, decision-only SFT, and SFT with the auxiliary targets.
   A rule engine should handle genuinely explicit rules; the model must earn its
   complexity on interpreting language, effects and context. Use validation for
   prompt/checkpoint/threshold choices and a frozen test for final reporting.

There is no reason to commit to hundreds of thousands of examples first. Use
learning curves after a small reviewed pilot to determine whether more examples,
better labels or missing context are the limiting factor. Start with SFT; RL and
preference tuning can follow only if their rewards and comparisons are reliable.

Keep enterprise-specific rules as an explicit input even if the model learns
general security concepts. Otherwise, changing a company's approval or disclosure
rule may require retraining, and we cannot distinguish memorized restrictions
from policy interpretation. Hold content and tool calls fixed while changing an
authorized policy clause to test this ability. We can separately study a fixed-
policy classifier, but should label it as a different deployment choice.

When real logs eventually become available, confirm permitted use, remove actual
secrets and identifiers, preserve relationships through consistent replacements,
and obtain the context needed to adjudicate them. Detection alerts, absent alerts
and tool success codes should not be converted directly into labels. Untrusted
source text must remain data during generation and review.

## Existing work to learn from

[StepGuard-Data](https://huggingface.co/datasets/ninty-seven/stepguard_data)
publishes 3,000 SFT and 4,000 RL examples spanning individual actions and complete
trajectories. Its targets distinguish safety from the presence of a risk source;
an attack can be present while the action under review remains safe. This is a
particularly useful precedent for avoiding blanket refusals. Its binary labels
do not directly provide our enterprise ALLOW/BLOCK/REVIEW judgments. The card
states Apache 2.0 terms for contributor-owned material and separate rights for
third-party material. We have reviewed the card, not imported or audited its rows.

[ToolSafety](https://aclanthology.org/2025.emnlp-main.714/) supplies training
examples for direct, indirect and multi-step tool-related harms. Its
[dataset preview](https://huggingface.co/datasets/jinjinyien/ToolSafety) trains a
tool-using assistant, including refusals. Our target is an independent reviewer
of a pending action. Adapting such material requires a new task mapping and label
review, not simply concatenating its assistant responses into our training set.

[ToolSafe](https://arxiv.org/abs/2601.10156), a separate project, studies detection
before execution using interaction history and feedback. It is a useful design
reference, not evidence that our proposed reviewer will achieve its results.

Before importing any dataset, inspect its actual files, license and restrictions,
provenance, benchmark overlap and label semantics. Preserve evaluation-only
sources such as AgentHarm for evaluation; see the
[environment proposal](../research-directions/AGENT-TRACE-DATASET-ENVIRONMENTS.md).
No third-party training material is included in this seed.

The [Shieldstral adaptation proposal](SHIELDSTRAL-PLAN.md) applies this design to
an existing policy model. It compares frozen policies, policy tuning and native
yes/no LoRA training, starting with StepGuard action-level examples. ToolSafety
needs an adjudicated action-label mapping. Enterprise policy contrasts and review
labels remain separate extensions; no training has started.

Before that training, the [StepGuard model-comparison proposal](STEPGUARD-BENCHMARK-PLAN.md)
would compare existing policy and decision models on the released safety labels.
It separates pending-action judgment from completed-run auditing, initial from
tuned policies, and complete-context comparisons from broader coverage results.
This is a proposed benchmark; no model inference has started.

## What success would mean

Do not optimize a single three-class accuracy number. Report:

- Known policy violations incorrectly allowed, with a separate severe-case slice.
- Permitted actions incorrectly blocked, and permitted actions unnecessarily held.
- Policy-required review recall, and whether a review asks for the right fact or
  approval. Review cases incorrectly allowed are distinct from known-violation misses.
- Automatic-decision coverage, errors among automatically decided cases, and
  unnecessary human referrals at a stated review budget.
- Correct decision changes when authority, destination or policy changes, and
  stability when wording changes but meaning does not.
- Unsupported evidence, wrong policy references and incorrect effect descriptions.

Report counts, denominators and uncertainty. A deliberately enriched development
set is not representative traffic; estimate operational review volume only with
stated prevalence assumptions or a separately collected representative sample.
Eventually measure interruptions and completion per task, not only per tool call.
Ten repeated approval requests can overwhelm a user even when each looks
reasonable in isolation.

A document-based seed can test judgments under specified facts. It cannot yet
establish actual side effects, resistance to forged telemetry, live enforcement,
or a reduction in human approval fatigue. Those require the later instrumented
environment and user studies. The staged approach lets us settle what the model
should learn before investing in those systems.

## Reproduce the draft

From the repository root:

```bash
python3 tools/build_security_cognition_seed.py
python3 tools/build_security_cognition_seed.py --check
```

The builder recreates the two JSONL files from explicit authored scenarios. The
check verifies reproducibility, input/target separation, references, disposition
structure and draft provenance. It does not use a model or certify safety.
External compute cost: **$0**. No infrastructure was provisioned; there is no
experiment resource to terminate. Training and sandbox work remain unrun.
