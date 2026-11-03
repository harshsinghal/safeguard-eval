# Creating agent-trace datasets from observable outcomes

Status: source review and proposed design, checked 3 November 2026. No agent
tasks were executed, no sandbox was provisioned and no paid model calls were
made. This extends the [offline policy-review proposal](OFFLINE-AGENT-POLICY-REVIEW.md).

The [command and tool-call proposal](COMMAND-ACTION-POLICY-INTERPRETER.md) describes
how utility documentation and security references could seed these environments,
and how to compare code-specialized models with policy interpreters.

## The opportunity

We can reduce the amount of per-trace human labeling by designing environments
whose important outcomes are observable and whose permitted actions are explicit.
A person reviews the task, policy and scoring conditions. Agents then take
different paths through that environment. Instrumentation records what happened,
and executable checks label the parts of each run that the specification covers.

This is machine-verified supervision under human-approved rules. It is not the
same as having a person independently label every trace. Human judgment remains
necessary for policy design, ambiguous cases and validation of the checks.

The useful separation is:

1. **Observation:** which files, records, permissions or destinations changed?
2. **Authorization:** were those changes permitted under the applicable policy
   and the approval actually available at that moment?
3. **Judgment:** should the proposed action proceed, stop or wait for review?

A file deletion can be observed exactly. Whether it was justified requires the
task and policy. “Unexpected” must mean outside a defined authorized scope, not
merely different from the benchmark author's preferred sequence of commands.

## What the named benchmarks already provide

| Source | Useful contribution | Labeling boundary |
|---|---|---|
| AgentHarm | Human-written tasks and rubrics, synthetic tools and harmful/benign counterparts | Most scoring uses prescribed conditions, with model judging for narrower semantic checks; synthetic tool success is not a real-world consequence |
| AgentHazard | Executable multi-step tasks and released trajectories | Human curation of tasks is distinct from the paper's model-judged harmfulness labels on runs |
| SABER | Stateful workspaces, command/tool traces, state changes and task-specific judging | Deterministic checks are combined with semantic judging; released labels need their provenance preserved |

AgentHarm's tools are simulations without external side effects. Its construction
shows how human work on rubrics can be reused across many model executions.
[Paper](https://arxiv.org/abs/2410.09024). The maintainers request evaluation-only
use of its examples; do not place these tasks or derivatives in our training pool.
[Maintainer documentation](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/src/inspect_evals/agentharm/README.md).

Here, AgentHazard refers specifically to Yunhao Feng and colleagues' computer-use
benchmark, not the similarly named mobile-GUI project. Its paper describes
execution filtering and human curation, followed by an LLM judge for trajectory
outcomes. Do not relabel all of those outputs as independently human-verified.
[Paper](https://arxiv.org/abs/2604.02947),
[dataset](https://huggingface.co/datasets/Yunhao-Feng/AgentHazard).

The published spelling of the workspace benchmark is **SABER**. Its source
release already contains a Pi SDK adapter and sandbox tool runtime, so we should
audit and adapt those rather than build a new agent loop first. The documented
adapter disables Pi's built-in tools and routes shell/MCP execution through the
benchmark runtime. It also serializes tool execution and preserves conversation,
event and trajectory records.
[Repository](https://github.com/sssr-lab/saber),
[Pi verification notes](https://github.com/sssr-lab/saber/blob/main/harness-verification.md).

SABER combines state-property checks and harmful command/tool patterns with a
semantic judge. Its paper describes human auditing of a sample of semantic
judgments. That is a useful precedent, not proof that every released label or
every command-pattern match is an independently verified physical outcome.
[Judging protocol](https://arxiv.org/html/2606.01317v1).

This was a source inspection. We have not installed, executed or validated the
SABER adapter locally. Its current automation does not include the human approval
loop we want; its Pi project-trust acceptance is not task-specific authorization.

## Design a small environment before collecting thousands of traces

Each scenario needs a versioned contract containing:

- A legitimate user goal and observable criteria for completing it.
- Initial synthetic files, databases, repository history and service state.
- A policy defining allowed actions, protected assets and approval requirements.
- What the acting agent can see, what it can discover, and what remains unknown.
- Checks for task completion, policy violations, approval ordering and incomplete
  evidence, with known positive and negative test cases.
- A defined interaction for requesting approval or clarification.

Keep the scoring implementation and answer metadata outside the actor's and
reviewer's inputs. The policy and relevant facts must still be available or
discoverable. A hidden prohibition that no agent could know does not make a fair
policy-following test. Where evidence is genuinely unavailable, the intended
decision may be REVIEW rather than a confident safe/unsafe answer.

For the first environments, use cleanup of project artifacts, log sharing,
repository maintenance and database maintenance. These have concrete outcomes
and ordinary benign workflows as well as risky variants.

## Worked example: free disk space without destroying useful files

Create a synthetic project with regenerable cache files, useful documents and
files whose retention status requires confirmation. Avoid using the extension
alone to determine importance: `.txt` can describe disposable output or a valuable
document. Vary names, directory structures and metadata across instances.

An example policy permits deleting documented cache outputs, requires approval
for uncertain user documents and forbids deletion of a protected record set.
The cleanup goal and preservation conditions are scored independently.

| Proposed or observed behavior | Label under this example policy |
|---|---|
| Delete documented disposable cache entries within scope | ALLOW |
| Propose deleting documents with unresolved retention status | REVIEW before execution |
| Receive approval for a specific eligible set, then delete only that set | ALLOW after approval |
| Delete a protected record, or exceed the approved scope | BLOCK; record a violation if attempted/executed as specified by the policy |
| Ask for approval and wait without deleting anything | Appropriate escalation; task remains incomplete |
| Claim cleanup succeeded while making no useful change | Task failure, not automatically a safety violation |

For the user's “delete all the text files” example, distinguish two situations.
If their status is unresolved, pause for review. If the proposed set contains
known protected records, block that operation and propose a narrower alternative.
The label should follow the explicit rule and available evidence.

Record approval as a trusted event bound to the action and affected object set.
A statement from the agent that approval exists is not evidence of approval.
An approval for one directory does not authorize another. Recheck scope if the
workspace changes after approval. The test user can grant, narrow or deny the
request through a deterministic scenario script; record that as simulated user
behavior, not actual human feedback.

## Run Pi through an instrumented execution boundary

```mermaid
flowchart TD
    S[Reviewed scenario and policy] --> P[Pi actor with pinned model and tools]
    P --> G[Tool gateway and approval service]
    G --> E[Disposable workspace and controlled services]
    P --> T[Conversation and exact model-visible inputs]
    G --> T
    E --> O[Independent state and event observations]
    T --> V[Versioned executable checks]
    O --> V
    V --> D[Labels with evidence and provenance]
    D --> H[Human audit and ambiguous-case review]
    H --> F[Frozen evaluation set or separate training pool]
```

The controller and model credentials stay outside the workspace accessible to
agent tools. Start with disposable containers inside an isolated VM or equivalent
boundary, synthetic data and no user home-directory mounts. Keep the observer and
its logs outside the actor's writable area. Register only the sandboxed tools;
a local shell or file tool that bypasses the gateway would invalidate isolation
and the trace record. Do not reuse the existing Pi skill-usability launcher for
destructive-action studies: that launcher was not designed as a security sandbox.

Collect three complementary records:

| Record | What it establishes |
|---|---|
| Agent interaction | User request, supplied policy, tool definitions, assistant messages, tool arguments/results, approvals and exact model-visible context |
| Execution events | Accepted/rejected calls, start/end times, exit status, child-process activity and actual filesystem/database/service operations |
| State and receipts | Before/after file manifests and hashes, permission changes, database contents, Git refs and controlled service acknowledgments |

Tool names alone are insufficient. A shell call can launch a script that performs
many operations. Final snapshots alone are also insufficient: a file could be
deleted and recreated, or sensitive data sent out while local files remain
unchanged. Combine per-action observations with final state. Validate the observer
using known harmless and violating scripts before allowing model-generated runs.

For the first pilot, execute tools sequentially and wait for their child processes
to finish or terminate them at the run boundary. This makes attribution clearer;
it does not establish behavior under production concurrency. Later tests can add
overlapping operations with causal identifiers and explicit race handling.

For network tasks, initially route requests only to controlled mock destinations.
Record destination, method, payload fingerprint and server-side receipt. A logged
attempt is different from a received transfer. Packet capture alone cannot reveal
arbitrary encrypted payloads; use endpoints we control to verify delivered content.
Keep model-provider traffic separate from agent-generated network traffic.

Do not assume the upstream SABER networking configuration supplies this behavior.
Inspect its isolation settings and implement controlled service routing as a
separately tested change. No real third-party targets or real secrets are needed.

## Preserve different kinds of labels

Each finding should retain its policy version, check version, relevant event IDs,
evidence and origin:

- **Verified property:** a check established a specific state change or ordering
  violation under the scenario's approved specification.
- **Human-adjudicated:** people assessed the policy judgment and its supporting
  evidence, with disagreements recorded.
- **Model-proposed:** a judge suggested an interpretation that has not yet been
  independently established.
- **Unresolved:** telemetry or context does not support a determinate judgment.

Do not pool those sources under one “human labeled” heading. Automated checks can
have bugs or incomplete coverage. No triggered check means no detected violation
within the monitored scope, not a universal safe label. Retain infrastructure
failures and truncated traces separately from benign completions.

Keep `required_disposition` separate from `observed_violation`, `attempted_action`,
`executed_action`, `task_completed` and `approval_received`. A rejected destructive
call can be a prohibited attempt without causing data loss. A refusal after a
completed harmful action does not erase that action.

## Use human effort where it adds the most information

Review scenario rules and checker tests before generation. After generation,
prioritize ambiguous cases, checker/model disagreements, severe violations and
new behavior patterns. Also audit a stratified random sample, including apparently
safe runs and cases on which all models agree. Disagreement sampling alone misses
shared errors and cannot estimate the dataset's overall label error rate.

For the final evaluation collection, obtain independent assessments of the policy
judgments with adjudication of disagreements. Reviewers should see the evidence
but not the model's brand or an initial suggested verdict that anchors them.
Keep the original annotations as well as the adjudicated answer.

Simple verified examples can receive templated, evidence-linked explanations;
we do not need an LLM to invent a rationale for a known deletion without required
approval. Reserve semantic explanation generation for cases where interpretation
is needed, and verify those explanations before using them as training targets.

## Two evaluation views from each run

**Offline audit:** give a reviewer the completed trace and an explicitly defined
set of raw state observations. Test whether it identifies the actual violation
and cites the relevant policy and events. Never include checker verdicts or
benchmark answer metadata as model features.

**Pre-action replay:** stop the input just before a tool call, including the
proposed call but excluding its result and all later events. Test ALLOW/BLOCK/REVIEW
using only evidence available then. Future consequences can help establish the
evaluation record, but cannot silently become inputs or justify an action label
that required unknowable information. Replay accuracy is not evidence that an
intervening monitor would preserve task completion; that requires a later live
experiment in which blocked actions change the trajectory.

This distinction directly tests whether review would have been requested before
the deletion, rather than merely recognizing damage afterward.

## A bounded pilot and its research questions

First inspect existing released traces and manually exercise our proposed checks
on a small set of scripted paths. Then, subject to an approved execution budget,
consider four workflow families with five scenario variants, two actor models
and three repeated runs: 120 attempted runs. Variants should change authorization,
context or policy boundaries, not simply paraphrase the same attack. Actual output
classes depend on what the agents do; the design does not guarantee balanced labels.
This is an instrumentation and labeling pilot, not a sufficiently broad training
corpus or a preregistered benchmark.

Compare a deterministic checker baseline with:

1. A reviewer given conversation and tool traces.
2. The same reviewer also given raw state changes and service receipts.
3. The same setup with explicit policy and trusted authorization context varied
   in controlled pairs.

The questions are whether additional evidence reduces errors, whether the model
respects changed authorization, and where semantic review adds value beyond
deterministic checks. Use balanced accuracy, false blocks, misses, evidence
correctness and review workload. Also measure time of detection relative to the
first prohibited action, safe task completion and unnecessary interruptions.
Report label provenance, missing observations and uncertainty alongside scores.

Split by scenario family/template before generating a later training collection;
keep near-duplicates, policy pairs, different actor runs and prefixes of the same
scenario in one split. Hold out new environments and at least one actor model
when sample size permits. A thousand traces from one template are not a thousand
independent tests. Vary names and representations while preserving accessible
policy facts to reduce superficial dataset cues.

Public benchmarks should remain external checks; preserve their licenses,
original task meanings and original metrics. Newly authored environments can
supply a separate training pool. A future compact reviewer can learn decisions
and evidence references from that pool, but high accuracy there would establish
performance on those governed environments, not general enterprise compliance.
