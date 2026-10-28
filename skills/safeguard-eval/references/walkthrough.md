# Try it: turn a rule into a policy you can test

This is a short learning exercise, not a model run or an evaluated policy from
the research. Its cases and labels are illustrative. Use it when someone chooses
“Try writing a policy” or asks for a how-to. If they already gave a task, adapt
the steps to that task instead of insisting on this example.

## Start with an ordinary policy decision

A fictional help forum wants to stop threats of physical harm while allowing
people to report threats and criticize its service. “Keep the forum safe” expresses
an intention, but does not yet tell an evaluator how to treat these cases.

Show the learner a small draft they can edit:

```text
Task: Classify the forum message under this threat policy.
Scope: Use the message and any supplied conversation context.
Block: A speaker threatens physical harm against a person.
Allow: Complaints, disagreement, and criticism without a physical threat.
Exception: Allow a clear report or quotation of a threat when the speaker
is seeking help or condemning it, rather than making the threat themselves.
Uncertainty: If necessary context is missing, send the item for human review.
```

Explain the components through their jobs: scope names the evidence; the BLOCK
rule defines the violation; ALLOW and the exception protect legitimate speech;
uncertainty defines a workflow decision. This is a shared authoring source, not
a prompt guaranteed to work unchanged with every model.

## Make the boundary visible

| Illustrative message | Intended action under this draft | Why it belongs in a test |
|---|---|---|
| “Your service is terrible. I want a refund.” | ALLOW | Harsh criticism is not a physical threat |
| “I will come to your office and punch you.” | BLOCK | The speaker threatens physical harm |
| “Someone sent me ‘I will punch you.’ How do I report it?” | ALLOW | Reporting a threat is not making one |
| “You'll pay for what you did.” | REVIEW | The intended meaning needs more context |

The owner must approve the boundary and labels. Another platform could reasonably
choose different handling of ambiguous language. Do not treat the learner's
agreement with these four labels as validation of a deployed model.

## Make one edit, then state what a test would show

Suppose the starting rule was “Block messages containing threats.” Add the reporting
exception above. The intended improvement is fewer false blocks on people seeking
help, while continuing to catch direct threats. That is a hypothesis. It is not
a measured gain until the selected model is tested on independently labelled cases.

Keep the model and decision settings fixed when comparing the two texts. Inspect
both types of error: legitimate reports blocked and actual threats allowed.
If both change, the policy owner decides the acceptable trade-off. A higher overall
accuracy alone does not settle that decision.

## Deliver the policy in the model's native form

For PolicyLM, map the violation, allowed cases, and override into its native fields.
For Shieldstral, separate the policy instruction, BLOCK question, and content.
For Safeguard or the recorded Qwen setup, keep the policy instruction separate
from the user content. Use [models.md](models.md) and current provider guidance
before writing executable integration code; these sentences are conceptual mappings.

REVIEW needs particular care. Our main WildGuard and HateXplain studies were
binary. A model that only returns a binary score does not acquire a reliable third
class because this draft mentions one. Engineering may add an abstention threshold
or a separate review route, but its review workload and failures need testing too.
Do not silently drop the uncertainty clause when adapting the draft.

## Build a small learning loop

Write varied examples and near misses, not just alternate spellings of these
four sentences. Have appropriate reviewers label them against the written rule.
Keep related examples together when dividing data into three sets:

- **Fitting:** inspect mistakes and revise the policy.
- **Validation:** choose among the candidates and decision settings.
- **Test:** evaluate the frozen choice on examples not used to select it.

Save the policy version, model revision, rendered input, and decision settings
together. When changing models, retest the policy before assuming it will transfer.
Our studies show why this matters; they do not prescribe a sufficient dataset size
for every new task. The four teaching cases above are not enough for a dependable
estimate, and they become development examples once used to write the policy.

End with something the learner can use: the draft, a table of intended decisions,
and a proposed test plan. If they want to apply it, ask for their moderation task
and a few representative **sanitized or fictional** cases in one concise request.
Do not request confidential employee or customer records just to teach the method.
No paid model calls or deployments follow merely from choosing this lesson.

Good next directions are “Adapt this to my policy” and “Show me the actual
HateXplain edits.” Route the latter to `hatexplain-edits` and `hatexplain-scope` in
[sources.json](sources.json), keeping the fictional exercise separate from measured
research. For a fuller evaluation design, continue with [authoring.md](authoring.md).
