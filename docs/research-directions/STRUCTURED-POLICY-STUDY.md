# Structured policy authoring: proposed HateXplain study

26 October 2026. Status: source review and experimental design; no inference runs
or GPU rentals started. This refines the bounded HateXplain replication in the
[research directions](README.md), rather than adding another benchmark project.

The question is whether organizing a policy into explicit components changes how
reliably a model applies it, and which components matter for particular errors.
The intended contribution remains practical guidance for policy authors and the
engineers who implement their policies. A more elaborate document is not assumed
to be better.

## What the publisher examples establish

- The joint [OpenAI/ROOST Safeguard guide][guide] recommends task instructions,
  definitions, criteria for both violations and permitted cases, and examples on
  both sides of the decision boundary. It places the policy in a system message
  and the material to classify in a user message. Its length and performance
  recommendations are publisher guidance, not findings from our study.
- OpenAI's [Teen Safety Policy Pack][teen-pack] is the example collection linked
  from ROOST. Its [dangerous-content policy][teen-example] contains a goal, terms,
  permitted cases, numbered violation categories with examples, an output scheme,
  and ambiguity handling. Borrow its document organization, not its teen-specific
  rules or labels, for HateXplain.
- ROOST's [demonstration policy][roost-example] separates the overview, terminology,
  interpretation guidance, included and excluded cases, and response instructions.
  It is an example document, not evidence that this organization is optimal.

Sources were checked on 26 October 2026. The inspected Teen Safety Policy Pack
commit was `1eaec21630d4024cb8fea687a6871f788dc8249e`; the ROOST Model Community
commit was `1f3d37d47097699f1139528052e465b80ce7b172`.

## Separate the model interface, policy body, and submitted content

The authoring document can have common logical components without every model
receiving the same chat messages. A role statement such as "You evaluate submitted
posts under this policy" is task framing. It is not a universal API requirement
and has no special guaranteed effect simply because it begins with "You are".

| Model | Published interface | Constraint on this study |
|---|---|---|
| GPT-OSS Safeguard | Policy in the system message; content in a separate user message | Keep its chat template, output contract, and reasoning setting fixed during document comparisons. |
| Qwen, in our existing runner | Policy and evaluator instructions in the system message; content in the user message | Keep task instructions, output mapping, and thinking setting fixed. An optional role-framing comparison must be separate. |
| [Shieldstral][shieldstral] | Fixed system instruction; `<Instruct>`, `<Query>`, and `<Document>` in the user turn | Preserve those outer fields. Put the policy body in `<Instruct>` and ask one fixed yes/no question. |
| [PolicyLM][policylm] | A named category with violation, non-violation, and exception fields | Use one category and preserve native fields. Full-document Markdown/XML comparisons are not equivalent to changing these fields. |

Shieldstral recommends one policy question for individual decisions; it also
documents an aggregate unsafe-content question over categories. PolicyLM supports
multiple categories but recommends separating unrelated ones because joint context
can affect scores. One policy therefore does not mean one sentence or no subrules.
For this experiment, keep one hate-speech policy and one binary decision throughout.
Do not introduce a combined hate, spam, privacy, and violence policy.

CoPE is not added to the core panel. Its [documented interface][cope] is another
reason to keep packaging explicit: it takes POLICY and CONTENT in a user-turn
prompt and returns a binary label, rather than requiring an ordinary system policy.

Our existing policies already contain PURPOSE, BLOCK, ALLOW, and PRECEDENCE fields.
We have not isolated the contribution of that organization. Also, the existing
PolicyLM adapter uses only the name, block, allow, and precedence fields, whereas
the Qwen and Shieldstral adapters include purpose text. The earlier comparisons used
native interfaces; they are not a controlled study of identical complete prompts.
This field mapping was already documented before the original candidate search.
Only block, allow, and precedence were tuned; purpose and review remained fixed.
The [retrospective interface audit](POLICY-INTERFACE-AUDIT.md) verifies those facts
against archived source and manifests and distinguishes supported packaging from
optimal model-specific authoring. Do not rewrite the historical artifacts or
reclassify their results.

## Author-facing document outline

This is an original scaffold, not a finished policy or a ready-to-run prompt.
Definitions, exceptions, and examples must be grounded in the HateXplain annotation
guidance and training data before the experiment is registered.

```markdown
# Hate-speech moderation policy

## Scope
Classify the submitted post for hate speech.
This blocking rule permits offensive content that is not hate speech.

## Terms and distinctions
[Define hate speech, the relevant targets, and the distinction from other offense.]

## Conditions requiring BLOCK
[Write the criteria as explicit rules with stable identifiers.]

## Conditions permitting ALLOW
[State what does not satisfy the blocking rule.]

## Exceptions and priority
[Specify exceptions and which rule controls an apparent conflict.]

## Examples requiring BLOCK
[Two short training examples, their labels, and the relevant rule identifiers.]

## Examples permitting ALLOW
[Two short training examples, including an offensive-but-not-hateful boundary case.]
```

Keep the evaluator instructions and machine output format in a recorded, fixed
adapter wrapper. The document's BLOCK/ALLOW semantics remain explicit; adapters
may use native yes/no, A/B, or category scores with a fixed mapping. Submitted
content stays separate from policy examples and is treated as material to classify.
Do not change output format, request explanations, or add reasoning instructions
at the same time as a formatting edit.

The authoring source should preserve stable component IDs and exact text for scope,
terms, violation rules, permitted cases, exceptions, and examples. Save example
provenance, labels, and rule references. A canonical structured record is an editing
and audit aid; its use internally is not evidence that showing JSON to a model helps.

## A small, staged comparison

Retain PolicyLM 1.7B, Shieldstral 3B, and Qwen3.5-4B as the core panel. Safeguard's
guide motivates the design; adding Safeguard inference is an optional replication,
not a prerequisite. Do not expand the panel merely because more templates exist.

### 1. Presentation, with the same information

For models that can receive a policy document inside their native interface:

| ID | Version | Change from the common reference |
|---|---|---|
| S0 | Linear text | Keep the same section titles, sentences, examples, and order; remove Markdown heading/list markers and flatten layout. |
| S1 | Markdown reference | Use explicit headings, lists, and visible section boundaries. |
| S2 | Tagged document | Put the same content and section titles inside XML-style section delimiters. |
| S3 | Reordered Markdown | Keep wording intact but move permitted cases and exceptions before violation criteria. |

S0/S1/S2 compare the representation of the same information. S3 tests order as a
separate factor. Formatting changes tokenization and position, so report token
counts and do not describe any improvement as proof of a particular mechanism.
Keep substantive sentences byte-identical and save a normalized-content comparison.
XML-style delimiters are input text, not a guarantee of policy compliance.

PolicyLM does not participate in a purported whole-document syntax comparison by
silently collapsing S0/S1/S2 into the same native fields. It participates in the
component and transfer comparisons below. A later study of structure within its
fields would be a separately labeled comparison.

### 2. Components, with the presentation held fixed

Use the complete reference body and each model's frozen default renderer. Compare
four prespecified omissions, each against that reference:

- Remove the standalone definitions section.
- Remove the explicit exception/priority section.
- Remove the ALLOW examples, retaining the BLOCK examples.
- Remove all examples.

The last two comparisons estimate the contribution of the BLOCK examples and the
additional ALLOW examples within this particular set. They do not establish a
universal benefit from a polarity or number of examples. Use the same training-only
example IDs in every applicable condition. A limited repeat with a second training
example set can test whether a result depends on those particular examples.

These are changes in supplied information and length, not pure formatting effects.
Removing a section may leave related information elsewhere. Call this a section
omission, not proof that the model received no evidence about that concept. Hold
the intended policy and gold labels fixed: an omission measures incomplete
specification of the intended policy, not compliance with a newly authorized rule.
Do not select an incomplete policy as the production recommendation merely because
it achieves a higher aggregate score.

Optional, bounded follow-up: remove only an added evaluator-persona sentence in
Qwen's chat prompt while preserving the task, rules, and output instructions. Do
not remove Shieldstral's required system instruction or invent a system role for
PolicyLM. This isolates optional framing rather than breaking a native interface.

### 3. Revision and transfer

Run a small, equal training-guided revision budget within the common component
schema. Review intended scope, select using validation, and freeze before testing.
Apply each selected policy's substantive components to every core model, using
each recipient's already fixed renderer without a new rewrite or selection step.

Label this **policy-content transfer through native interfaces**. Literal prompt
or format transfer is a stronger claim and only applies when the body can be
preserved verbatim. If a component cannot be represented without substantive
rewriting, record that condition as unsupported instead of silently adapting it.

## Evaluation and records

Use the binary HateXplain mapping in the main proposal: hate -> BLOCK; offensive
and normal -> ALLOW. Preserve training/validation/test separation. Examples shown
in policies and revision feedback come only from the training partition. Compare
all prespecified variants on the final test after the complete set is frozen;
do not choose a test winner and treat it as a validation selection.

Report missed hate, false blocks of offensive content, false blocks of normal
content, cases fixed, cases newly broken, accuracy, macro-F1, invalid outputs, and
paired uncertainty. Keep scores and cutoffs where available, and check repeatability
before interpreting small changes. Keep model versions, truncation behavior,
thresholds, output mappings, and reasoning/decoding settings fixed within contrasts.

Record the authoring document, component inventory, rendered model input, token
counts, model and adapter versions, and component-to-field mapping for every arm.
Before inference, verify that no renderer drops a section, duplicates an example,
truncates material, or makes distinct format conditions identical. PolicyLM's native
input limits need explicit checking; longer documents are not automatically fairer.

For each result, explain which edit changed which decisions and what that means for
policy authors and engineers. This can support an empirically tested authoring
template and a method for revising it. It cannot establish that one template is
best for every model, that Markdown guarantees reliability, or that model training
and architecture caused an observed transfer difference.

Before execution: audit annotation guidance and split integrity, fill the policy
scaffold, pin native model interfaces, choose and register the metric objective,
example IDs, candidate budget, and affordable run matrix. Source review and document
preparation used no paid model calls.

[guide]: https://developers.openai.com/cookbook/articles/gpt-oss-safeguard-guide#structuring-policy-prompts
[teen-pack]: https://github.com/openai/teen-safety-policy-pack
[teen-example]: https://github.com/openai/teen-safety-policy-pack/blob/1eaec21630d4024cb8fea687a6871f788dc8249e/example_policies/dangerous-content/policy.md
[roost-example]: https://github.com/roostorg/model-community/blob/1f3d37d47097699f1139528052e465b80ce7b172/gpt-oss-safeguard/projects/demo/drug_policy.md
[shieldstral]: https://huggingface.co/mistralai/Shieldstral-1.0-3B#how-it-works
[policylm]: https://huggingface.co/musubilabs/policylm-1.7b#writing-a-policy
[cope]: https://huggingface.co/zentropi-ai/cope-b-a4b#input-format
