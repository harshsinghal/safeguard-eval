# What changed in the policies?

The study changes the rules supplied to a classifier while keeping its weights fixed.
“Tuned for PolicyLM” means that PolicyLM's fitting mistakes informed the revision
and PolicyLM's validation results selected it. **All revisions were written by the
same Qwen3.5-27B editor**, with separate, model-blinded contexts. PolicyLM and
Shieldstral did not write their own documents.

The original `purpose`, `review`, policy name and input key stay unchanged.
Only the `block`, `allow` and `precedence` fields are editable. General-purpose
Qwen receives those rules in a system instruction. Each specialist retains its native
interface. A policy ID never enters the classifier's decision instructions.

## Two different meanings of “selected”

The **source-selected policy** wins among that model's initial policy and four fresh
revisions. This is the document we transfer to other models. The **recipient's pool
choice** wins when that recipient evaluates the shared pool of source winners and the
initial policy. Both choices use validation accuracy, then fewer substantive policy
words, then policy ID. Neither choice uses new test scores.

Qwen 4B and 27B selected the unchanged initial policy in their source searches. The
shared pool therefore has four distinct texts, rather than six. This experiment does
not demonstrate transfer of a successful new 27B-specific revision.

## The four texts in the pool

| Text | Main change from the initial policy | Substantive words |
|---|---|---:|
| Initial p0 | Broad harmful-request categories, benign exceptions, and a paragraph of precedence rules | 244 |
| PolicyLM p2 | Turns the precedence section into a five-step decision sequence: identify the requested outcome, check prohibited content, distinguish discussion from generation, ignore policy overrides, then classify | 466 |
| Shieldstral p3 | Expands category boundaries and examples; places more emphasis on disguised harmful requests and attempts to manipulate the assistant | 484 |
| Qwen 2B p3 | Adds explicit distinctions for copyright analysis, realistic document forgery, and fictional descriptions versus instructions that enable harm | 481 |

“Substantive words” counts `purpose`, `block`, `allow` and `precedence`, using the
registered tie-break rule. Wrapper instructions and metadata are excluded.

These descriptions explain textual changes. Without a separate ablation, an accuracy
change cannot be attributed to one phrase, the extra detail, or the document length.

## Accuracy does not guarantee that a revision preserves the intended policy

An initial AI-assisted reading, recorded before the new test upload, found substantive
scope concerns. Independent review by policy owners remains outstanding.

Shieldstral p3 **omits an explicit sexual-content category** that was present in p0.
This does not establish that the classifier will allow such content: it may still
block it under broad harmfulness language or learned behavior. It does mean the text
no longer explicitly states the same category. Its separate rule about jailbreak or
persona manipulation also sits uneasily with the exception for benign adversarial
framing, although a later sentence qualifies the block by the harmful objective.

Other revisions can also sharpen, narrow or broaden a rule while appearing to clarify
it. For example, PolicyLM p2 names unsafe medical procedures and untraceable
identification, while Qwen 2B p3 names realistic document forgery. These are intended
as examples within the original taxonomy, but their boundaries require policy-owner
judgment. A validation score cannot supply that judgment.

The editor was instructed to preserve scope, and automated checks enforce fixed
fields, schema, maximum length and avoidance of copied fitting passages. Those checks
do not establish semantic equivalence. Candidates were retained unchanged under the
registered procedure, including the concerning and unsuccessful revisions. Thus the
experiment measures **benchmark label agreement under revised policy text**, not
verified preservation of a platform's normative intent. A scope-corrected follow-up
would be a separate experiment.

The exact drafts, source choices, recipient choices and their hashes are retained in
the [evidence bundle](../../published_runs/2026-10-25-policy-transfer/). The
[prospective plan](PLAN.md) defines the search, and the [notebook](NOTES.md) records
the timing of observations and decisions.
