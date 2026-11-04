# Comparing existing models on StepGuard safety judgments

Status: proposed offline benchmark, 4 November 2026. No inference, policy search,
fine-tuning or paid compute has started. This comparison comes before the
[Shieldstral fine-tuning proposal](SHIELDSTRAL-PLAN.md).

## Research question

Can our existing policy and decision models distinguish unsafe agent behavior
from legitimate activity, including safe handling of attacks, using the available
context? How much does policy authoring improve their agreement with the dataset's
reference judgments while model weights and decision rules stay fixed?

This would be a benchmark of **offline agent-safety judgment**. It would not yet
measure attack prevention, task completion, approval fatigue or latency in a live
agent. No tool calls from the records would be executed.

## Dataset and two separate tasks

[StepGuard-Data](https://huggingface.co/datasets/ninty-seven/stepguard_data)
publishes 3,000 SFT examples and a separate 4,000-example RL collection. Each
contains action-level and whole-trajectory cases, safe and unsafe labels, and
risk-source annotations. The released files are training subsets, not official
test splits. We would create a derived, grouped evaluation split and identify it
as such.

Begin with the SFT collection: the card lists 1,500 action-level and 1,500
trajectory-level records. Audit actual counts, duplicates and usable labels before
registering the population. Reserve the RL collection for a separately declared
extension; its name does not imply independence from SFT scenarios.

| Track | Question | Permitted input |
|---|---|---|
| Pending-action judgment, primary | Is the action under review unsafe in this context? | User task, tool definitions, preceding events and the candidate action; no result of that action or later events |
| Completed-run audit, secondary | Does the recorded run contain unsafe agent behavior? | The complete recorded run and its available tools; exclude the reference reviewer's annotations |

Keep separate leaderboards and policies for the two tracks. A later refusal does
not undo an earlier unsafe action in a complete run, while an earlier risky event
does not automatically make the specific pending action unsafe. Some candidate
actions may be final responses or refusals rather than external tool operations;
report those separately from the external-tool-call slice.

The [StepGuard paper](https://arxiv.org/html/2608.24777v1) describes synthesized
trajectories, related safe and unsafe branches, and automated annotation/quality
checks. It also distinguishes a risk source being present from unsafe behavior.
Consequently, agreement with its labels is not independent proof of enterprise
authorization or real execution outcomes.

Do not include the released StepGuard checkpoint in the main leaderboard on its
own training corpus. Any comparison with that model needs an independent common
test, such as an appropriate external action or trajectory benchmark, after
checking source overlap and the target task. Unknown upstream exposure of other
models remains a limitation even after we separate our own development data.

## Initial model panel

Use the existing audited integrations as starting points, then pin exact model,
tokenizer, code and provider versions before execution:

| Family | Proposed models | Input/output contract |
|---|---|---|
| Policy models | PolicyLM, Shieldstral, GPT-OSS Safeguard | Native category rules; instruction/query/document; native policy and structured decision, respectively |
| Decision models | Jev, Kev, Clef Flash | Native binary Choice task with explicit criteria |

The context preflight below refines this to a provisional **five-model primary
panel: Shieldstral, Safeguard, Jev, Kev and Clef Flash**. PolicyLM belongs in a
separate comparison on short complete inputs, with the other models scored on
exactly those same inputs. Do not reduce the primary panel's whole population to
PolicyLM's much smaller window. Final eligibility still requires native-input
token counts, not just the preliminary counts below.

The six-model panel matches our [prompt-injection registry](../../evals/prompt_injection/common.py).
An optional small general-purpose Qwen control would be a declared addition, not
an unrecorded expansion of the study. We do not need every historical model to
answer the first question.

Use SAFE/UNSAFE as the displayed labels. If an existing adapter internally calls
them ALLOW/BLOCK, record the mapping. A SAFE reference label is a judgment under
this corpus's criteria, not a general permission to execute an enterprise action.

## Model inputs and policy authoring

Create one canonical record containing the task, source-provided tool definitions,
history and action/run. Keep role boundaries and provenance explicit. Adapt that
record to each model's native interface; do not impose identical serialization
on incompatible models.

Exclude the reference reviewer's explanation, judgment, risk-source label and
unsafe-step annotation from the input. Risk-source labels are for reporting
slices only. Distinguish source-provided actor history from reviewer annotations;
any retained actor reasoning is part of this dataset condition and may not be
available in a deployed agent. Audit parsers on development records and preserve
the source-to-input mapping and hashes.

The initial policy should follow the dataset's criteria: judge the agent's actual
behavior, scope, evidence and consequences. Do not add a new enterprise rule that
requires approval for every deletion and then score against source labels that
permit some deletions. Changing the normative boundary requires new labels and a
separate enterprise-policy study.

Compare two conditions per model and per track:

1. **Initial policy:** a source-aligned task definition delivered through the
   native interface.
2. **Selected policy:** a revision chosen using development examples and validation
   results, with the same fixed model and output decision rule.

Proposed search limit: at most four candidate policies, including the initial
policy, for each model/track. Candidate edits can clarify which action is judged,
how history supplies context, why legitimate sensitive operations can be safe,
and why an attack followed by a safe response is not an unsafe execution. Preserve
the original criteria rather than tailoring exceptions to individual test cases.
Give each model the same candidate-evaluation allowance; log authoring procedure
and candidate sizes. If budget requires less, amend and freeze the design before
test execution.

## Development and final testing

Create discovery, validation and final-test partitions with an approximate
20/20/60 allocation of scenario groups, stratifying by label and track where
feasible. Exact counts depend on group structure, not a quota that splits related
examples apart. Put examples already inspected or discussed in discovery; use a
conservative inspected-prefix exclusion where needed.

Group related full runs, prefixes, branches, source scenarios, paraphrases and
near-duplicates together across both tracks. Source rows without family IDs need
an audited grouping method; ambiguous relationships stay together or outside the
primary evaluation. Do not call a random row split independent generalization.

Use discovery labels for drafting and error analysis. Select on validation
balanced accuracy, breaking exact ties by shorter native policy token length and
then stable candidate ID. Freeze all policies, adapters, model revisions, scoring
rules and test IDs before examining final test outputs. Run the initial and
selected policies on the same frozen test cases; report paired changes rather
than choosing a winner after observing test scores.

No learned ensemble, calibration or fitted cutoff in this first comparison.
Register each model's decision rule explicitly. The existing PolicyLM integration
uses the publisher precision preset of 0.335; Shieldstral uses yes/no argmax;
decision models use native Choice argmax; Safeguard supplies a parsed label.
These are comparisons of configured systems, not architecture alone. Changing a
native preset based on test scores is prohibited. Transport retries, parse
failures and unresolved results need a fixed handling rule before running.

The derived test must remain held out from any later fine-tuning study that uses
it for comparison. If we use its errors to design new training examples, record
that history and obtain a fresh test for the new claim.

## Context length is a substantive constraint

### Source-length preflight and proposed model roles

A tokenizer-only preflight on 4 November 2026 counted all 3,000 SFT source human
inputs with the pinned Qwen3.5-4B-Base tokenizer. It included the source task
instructions but excluded the reference reviewer target. Median length was
**1,280 tokens**, the 95th percentile **3,515**, the 99th percentile **4,918**,
and the maximum **12,038**. There were 2,998 inputs at or below 8,192 tokens and
all 3,000 were below 16,384. Thus most released records are relatively short;
the full-run task does not automatically require a 128K window.

These are preliminary source lengths, **not final model request lengths**. Added
policies, native schemas, chat formatting, tokenizer differences and generated
output headroom must be accounted for before registering coverage. Only
aggregate lengths were inspected in this preflight; no label-based selection or
model predictions were made. The earlier manual content inspection remains
subject to the discovery-only exclusion described above.

Reproduce from the repository root with the `tokenizers` package installed:

```sh
python3 tools/audit_stepguard_context.py --output docs/security-cognition/stepguard-context-audit.json
```

The [audit output](stepguard-context-audit.json)
records source and tokenizer revisions, file hashes and library version; the
[script](../../tools/audit_stepguard_context.py) does not load model weights.

| Model | Current published context evidence | Proposed role |
|---|---|---|
| Shieldstral-1.0-3B | [Card](https://huggingface.co/mistralai/Shieldstral-1.0-3B) recommends the 32K training range despite a theoretical 256K window | Primary policy-model comparison |
| GPT-OSS Safeguard-20B | [Configuration](https://huggingface.co/openai/gpt-oss-safeguard-20b/blob/main/config.json) permits 131,072 positions; runtime and output budgets still apply | Primary policy-model comparison |
| Jev 1.14 | [TypeSafe docs](https://docs.typesafe.ai/models) specify 32K for state plus one question by default; 262K is opt-in. [OpenRouter endpoint metadata](https://openrouter.ai/api/v1/models/typesafe/jev-1.14/endpoints) advertises 262,144, which is not itself a route-level acceptance or accuracy test | Primary API decision-model comparison; ordinary context should suffice |
| Kev-4B | [Card](https://huggingface.co/jaredpalmer/kev-4b) serves 65,536-token states but validates quality only through 8,192 tokens on its long-document study | Include; report results within and beyond the publisher-validated range separately |
| Clef Flash | [Reference implementation](https://huggingface.co/Cloudflare/clef-flash/blob/main/joint_schema_model.py) defaults to 16,384 and truncates state; [backbone config](https://huggingface.co/Cloudflare/clef-flash/blob/main/config.json) specifies 262,144, without establishing decision-head accuracy at that length | Include after exact-length checks; use our no-truncation wrapper |
| PolicyLM-1.7B | [Card](https://huggingface.co/musubilabs/policylm-1.7b) gives policy and message a shared 2,048-token budget | Supplementary short-input comparison; no automatic summary or window aggregation |

These are current publisher statements, not new performance measurements by us.
Recheck them against the exact checkpoint and runtime selected for execution.
The existing local decision wrappers and Shieldstral wrapper cap requests at
16,384 tokens; this is our implementation setting, not the models' universal
maximum. A provisional 16K input ceiling may cover the primary panel, with
separate output headroom reserved in Safeguard's serving context. Confirm this
after native serialization. Analyze accuracy by length, and
distinguish a model accepting input from its ability to use that input correctly.

### Complete-input comparison rules

Long histories may exceed some model interfaces. For example,
[PolicyLM's card](https://huggingface.co/musubilabs/policylm-1.7b) specifies a shared
2,048-token policy/message budget and describes windowing for long messages.
Our decision-model wrappers also enforce explicit length limits. Check the pinned
implementations rather than relying only on a model family's advertised window.

The primary comparison should use a predeclared common set whose complete
serialized records fit every included model in one input. Freeze its eligibility
before predictions, reserving policy space sufficient for every registered
candidate. Report exactly what fraction and which types of cases this excludes.
Also report each model's coverage and results on its broader supported population,
without ranking unequal populations as though they were the same test.

Do not silently truncate, summarize with another LLM, or drop overflow failures.
A native windowed pipeline can be a separately labeled condition, with its window
and aggregation rules disclosed: seeing all fragments separately is not the same
as jointly reasoning over the full history. If the common complete-context set is
too small, report that limitation and use a separately defined longer-context
panel. Do not manufacture a universal ranking from insufficient overlap.

## Metrics that answer the practical question

For each track, report balanced accuracy, ordinary accuracy, macro-F1, false-flag
rate on SAFE examples, miss rate on UNSAFE examples, unresolved-output rate and
coverage. Show sample counts and paired confidence intervals clustered by source
scenario. Report SAFE and UNSAFE correct-decision rates with failures counted as
incorrect, while retaining unresolved counts so errors are not disguised as
intentional policy review. Freeze precise metric definitions before the run.

The most informative slices are:

- Benign contexts with safe behavior.
- Risk or attack present, but the agent behaves safely.
- Risk present and the agent acts unsafely.
- Legitimate sensitive operations versus misuse, where an audited tag supports
  that distinction.
- External tool calls versus final responses/refusals; short versus long history.
- Individual risk-source categories, with small-cell counts shown explicitly.

If matched safe/unsafe branches are recoverable, report how often both members
are classified correctly. That helps distinguish context-sensitive judgment from
flagging every appearance of a sensitive tool. Do not presume that all generated
pairs survived into the released sample.

Example result columns: model/configuration, complete-context coverage, balanced
accuracy, safe false flags, unsafe misses, errors and change after policy tuning.
Keep native scores for later analyses, but do not fit a new method on the final
test as part of this run.

## Label quality and conclusions

Preserve the original labels for the primary comparison. A separate audit should
include a random sample plus disagreements and severe cases, with reviewers blind
to model identities where possible. Keep any amended/adjudicated labels and
results separate. Do not silently relabel disputed cases to improve a model's
score, and do not call model-assisted inspection human validation.

The result can show which configured models best reproduce StepGuard's safety
judgments, which types of mistakes they make, and whether policy edits help. It
cannot establish that a model prevents those actions in a running agent, follows
every enterprise policy, or achieves a particular human-review workload. REVIEW
is not a third label in this corpus. ToolSafety conversion, fine-tuning, ensembles
and live sandbox interventions remain separate proposed experiments.

## Next milestone and resources

Before any paid run: audit source files and grouping, validate input extraction
and context coverage, fix the model panel and register an affordable call plan.
If available context makes PolicyLM or another model ineligible for the main
panel, explain that with counts before choosing a reduced comparison.

This document records the design and a completed local tokenizer-only length
preflight. No inference budget has been allocated by this proposal, no GPU
resources were provisioned and no model predictions were generated. External
compute spending for the source review and length preflight: **$0**.
