# Evidence preparation for enterprise moderation

The pilot packet contains 200 complete prompts, split into 100 development and
100 evaluation cases. Each split includes six cases from each of the 14 existing
benchmark tasks and 16 authored controls. Schema, policy and selection rules are
registered. All 200 annotation records are pending. The packet is ready for
annotation review; model accuracy and moderation improvements remain unmeasured.

## Review the packet

- [Potato visual annotation workspace](POTATO.md), with development span drafts and editable links/events
- [Development review](../../work/evidence-moderation-v1/development-review.html)
- [Reserved evaluation review](../../work/evidence-moderation-v1/evaluation-review.html)
- [Annotation guide](ANNOTATION.md)
- [Enterprise policy](POLICY.md)
- [Machine-readable schema](schema.json)
- [Worked development example](example.json), an assistant-authored draft
- [Selection and experiment plan](PLAN.md)

The HTML files are local only (ignored by Git), self-contained and contain restricted source text.
Open them on this machine. They support editing, export and import of annotation
JSON, plus a Unicode offset helper. Save the case and export before closing.
Original benchmark labels are hidden. The Python validator checks references,
span grounding and review status. Semantic judgments require review.

## Coverage and interpretation

The source subset includes ordinary/benign-labeled requests, harmful requests,
hate speech, cyber requests, injection collections, custom policy examples,
source code, skill artifacts, pending agent actions and completed agent traces.
It uses the existing source inventory. The new authored pairs cover quotation,
negation, credential references and placeholders, claimed permission, code,
recipient ambiguity, action order, tool outputs, Unicode and long context.

| Split | Source prompts | Controls | Short | Medium | Long |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development | 84 | 16 | 78 | 16 | 6 |
| Evaluation | 84 | 16 | 77 | 14 | 9 |

Length bands retain source definitions; authored cases use a 2,000-character
boundary for long controls. Actual lengths range from 15 to 18,350 characters.
Source labels comprise 87 ALLOW, 73 BLOCK and eight REVIEW cases, plus 32 unlabeled
controls. These source labels are sampling descriptors, not answers under the
new policy. The four rules cover credentials, private information, destructive
operations and instruction boundaries. Other harms receive a separate
outside-scope annotation and need broader policy coverage in later experiments.

The schema retains the previous 12 entity and nine action categories and adds
software agents, physical locations and general groups. It also defines source
spans for actions, claims, conditions and contextual evidence. Frames preserve
roles, scope, polarity and explicit ordering. The public-data GLiNER checkpoint
has not yet been trained or measured against this expanded contract.

This source suite was used in prior studies. Evaluation is reserved within this
new experiment, not independent of all previous research. Source groups and
normalized duplicates stay together. One near-duplicate pair in the inventory
was connected by five-word shingle similarity before assignment. The 30 source
cases used in the previous Qwen graph pilot are excluded. Semantic paraphrases
and other hidden relationships may remain. The controls are assistant-authored,
and no independently human-reviewed gold labels are available yet.

## Reproduce and validate

From the repository root, use the shared environment with jsonschema installed.

```bash
venv/bin/python tools/prepare_evidence_moderation.py verify
venv/bin/python tools/prepare_evidence_moderation.py validate --annotations work/evidence-moderation-v1/development-annotations.json
```

Replace the annotation argument with a review export to validate edits. Preparing
an absent version uses the `prepare` stage, which refuses to overwrite existing
state. Preserve the registered version when changing schemas or selection rules.

Source and code hashes, grouping checks and safe case metadata are recorded in
[the local evidence directory](../../local_runs/evidence-moderation-v1/).
Verification checks source binding, group separation, split quotas, and blank
annotation validity. Targeted validator probes reject wrong offsets, dangling
links, invalid claim roles and unsupported BLOCK decisions. Browser rendering
and JavaScript syntax are checked locally. An initial static network-call scan
matched text inside a source prompt; the corrected check inspects executable
review code. The review interface's content policy disables network connections.

This preparation used local CPU work, zero paid API calls and zero model
inference. No GPU worker was started. Independent evaluation annotation and the
three-condition policy-model comparison remain the next experiment stages.
