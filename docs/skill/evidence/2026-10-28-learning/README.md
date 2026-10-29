# A careful tutor needs evidence and checks, not just more instructions

The v0.5 learning revision improved specific behaviors in Pi with Luna, but did
not eliminate mistakes. The useful outcome is a clearer learning method, an exact
transfer-result lookup, and a retained record of failures and retests. It is not a
claim that a skill can make every inexpensive backend a reliable policy expert.

## What prompted the revision

In the [v0.4 exploratory conversation](baseline-v0.4.md), the agent helped a
fictional workplace-community policy author draft a rule and plan tests. It also
proposed human review for a harmless report, used the wrong model pair as its first
example, and simplified review handling before all boundaries were resolved.
The user wanted a rigorous learning tool whose research examples help learners
design their own experiments. See the [plan written before testing](PLAN.md).

## What changed in the skill

The guide now asks the agent to distinguish recorded findings, interpretations,
teaching examples, proposed tests, and open policy choices. It checks an example
against the supplied rule, exception, and review condition. It explicitly preserves
the scope of a draft and avoids inferring a violation from missing detail.

A new learning guide connects three research questions to practical comparisons:
does an exception help, does a policy transfer, and is a gain actually due to a
different decision cutoff? It explains why examples used for editing become
development material, and why a new task needs its own labels and tests.

The offline `lookup_transfer.py` helper retrieves an exact source-selected-policy
and recipient-model comparison from the frozen matrix. It returns the baseline,
test denominator, error trade-off, source links, and selection status. It removes
the need to copy a nearby table row or calculate these values in prose. It cannot
ensure the language model explains the retrieved result correctly.

## How we tested

These are assistant-authored smoke checks using Pi 0.87.1, OpenRouter
`openai/gpt-6-luna`, and low thinking. Fresh isolated profiles used the normal Pi
system prompt and tools, the installed candidate skill, and the same local feedback
extension. No hidden answer key or additional teaching system prompt was supplied.
The [run inventory](conversation-runs.json) records the exact installed package
hashes, prompts, tool names, and reconciled usage. All candidates were labelled
0.5.0 while being developed; their hashes distinguish the iterations.

The first two iterations each used three conversations: four questions on
authoring, three on transfer, and four on a new gardening-forum policy. The final
iteration repeated the authoring and transfer conversations after narrower fixes.
This totals 29 prompts across eight new conversations. The original seven-turn
v0.4 conversation is retained separately. These prompts were available to the
skill author; this is iterative debugging, not an unseen or blinded evaluation.

## What we observed

| Check | Earlier failure | Later observation |
|---|---|---|
| Harmless reports and quotations | v0.4 escalated a vague report; candidate A still treated a clear attributed quotation as a review case | The final authoring run allowed both vague reports, removed the writer-added insult, and preserved the requested review route |
| Preserve the policy's scope | Candidate A broadened a ban on selling into promotion and buying; candidate B narrowed the insults rule to community members | Candidate B's gardening draft stayed within selling; the final authoring draft applied the insult rule to managers as well |
| Retrieve the requested transfer | v0.4 initially cited Shieldstral when asked about Qwen-to-PolicyLM | All revised transfer runs invoked the helper for the requested pairs and reported the recorded numerical comparisons correctly |
| Explain the direction and selection | Candidate A called the requested direction “the other way”; candidate B once called a selected policy “authored” by PolicyLM | Later answers named the direction and distinguished the editor, but the final answer still contained an imprecise sentence about one model selecting a policy for another |
| Turn a finding into a new experiment | A polished draft alone would not establish effectiveness | Both gardening conversations proposed a controlled policy comparison, rejected twelve reused examples as independent validation, and separated the benchmark task from the new forum |
| Link the evidence | Candidate B fabricated two URLs from its local install path | The final welcome read the registry and used valid pinned links. One final transfer citation still called a summary readout the exact comparison source instead of linking directly to the matrix |

Read the actual exchanges:

- Candidate A: [authoring](candidate-a-authoring.md), [transfer](candidate-a-transfer.md), [gardening experiment](candidate-a-experiment.md), [handoff](candidate-a-handoff.md).
- Candidate B: [authoring](candidate-b-authoring.md), [transfer](candidate-b-transfer.md), [gardening experiment](candidate-b-experiment.md), [handoff](candidate-b-handoff.md).
- Final focused check: [authoring](final-authoring.md), [transfer](final-transfer.md), [handoff](final-handoff.md).

## What remains unresolved

The final numerical lookups were correct, but free-form explanations remain
fallible. In the final transfer answer, “one model selecting a policy for another
model” is misleading shorthand: selection used the source model, followed by
evaluation on the recipient. A summary readout is also less direct evidence than
the actual matrix returned by the helper.

In the final authoring conversation, the agent initially left permission to quote
without explicitly asking for help open. The handoff later allowed sharing the
incident more broadly without clearly closing that choice with the owner. This is
less disruptive than the earlier invented review decision, but still illustrates
why policy scope needs review. The final handoff is a teaching draft, not an approved
policy or proof that the workflow preserves every user decision.

Some answers remain long, and useful follow-up prompts are inconsistent. Several
candidate tool calls used missing paths or an unnecessary edit; they recovered,
but these are additional reasons not to infer equal behavior across harnesses.
Correct numerical retrieval and understandable prose are separate checks.

The last changes were targeted at the observed failures. We did not run an ablation
without the skill, vary the backend, measure representative-user learning, or prove
that the skill caused the improvements. Repeated prompt tuning on these examples
limits generalization. Future checks should use new policy domains and readers,
retain mistakes, and inspect whether the agent preserves intent without needing a
more capable reviewer to intervene.

## Cost, provenance, and validation

The machine-readable inventory records OpenRouter billing for every new run and
the baseline separately. These are observed agent-conversation costs, not estimates
of moderation deployment cost. Initial billing lookups sometimes lagged completion;
missing records were not treated as zero. No GPU was rented for this work.
All 68 new model-response billing records were reconciled: the eight new
conversations cost **$0.033534725** (about 3.4 US cents). The earlier baseline cost
**$0.009961265** and is not included in that new-spending total.

Twenty-five mechanical tests passed, including package integrity, three-agent
installation layouts, update backups, local logging exports, and the lookup's
25 named source/recipient combinations. The skill-format validator also passed.
These checks establish specific invariants, not the correctness of every answer.

Only these fictional, assistant-authored visible exchanges and generated handoffs
are selected for publication. Native sessions, tool payloads, reasoning, credentials,
and human-user conversations are not included. Snapshots retain the evidence pin
used during testing; the release registry subsequently pins this readout as well.
