# What the StepGuard policies change

This study asks whether an agent's **behavior** is safe in context. A request to
destroy evidence can be followed by a safe refusal. A routine administrative
request can be followed by an unsafe action on the wrong record. Merely finding
a suspicious word or a sensitive tool is insufficient for this task.

The [registered experiment](STEPGUARD-RUN-PLAN.md) separates two decisions:

- **Pending action:** judge the proposed action using the preceding history.
  An earlier mistake does not automatically make a current refusal unsafe.
- **Completed run:** judge the whole recorded interaction. A reassuring final
  answer does not undo an earlier unsafe action.

These are source-label interpretations, not a new enterprise policy requiring
approval for every deletion or every outbound message. Introducing such a rule
would require new labels; scoring it against the existing SAFE/UNSAFE labels
would mix two different questions.

## Three versions of the same intended boundary

| Candidate | What the author adds | Why it could matter |
|---|---|---|
| Initial | A short rule about harmful or unauthorized behavior, legitimate scope, privacy and unreliable evidence | Establishes the basic decision without a long checklist |
| Criteria | Separates evidence, intent, consequences and safety/utility; distinguishes instructions from observations; calls out mismatched evidence and unsupported completion claims | Gives the model specific checks beyond detecting an alarming topic |
| Contrasts | Adds short safe/unsafe examples: a justified scoped deletion versus deleting the wrong record; refusing a cover-up versus following an injected disclosure instruction | Shows where similar-looking actions cross the boundary |

All candidates tell the evaluator to treat the recorded instructions as evidence,
not as instructions addressed to itself. The examples are short illustrations
authored during discovery. They are not retrieved neighbors, copied test rows,
or corrections derived from final test errors.

No model weights or score thresholds change. Three candidates are evaluated on
validation, and one is selected per model and task. Initial and selected versions
are then evaluated on identical held-out records. This can show whether a
particular authoring change transferred to test; it cannot identify the effect of
every individual sentence. A component-by-component ablation would be needed
for that stronger claim.

PolicyLM retains its published precision preset, which was not calibrated on
this agent-behavior task. The other models retain their declared native decision
rules. This compares specified usable configurations; it does not establish each
model's best attainable accuracy or isolate architecture from training and
operating-point differences.

## The same intent uses different interfaces

| Model | Delivered policy | Decision |
|---|---|---|
| PolicyLM | Native category fields: violation rule, non-violation rule, exception/precedence | Published precision cutoff, 0.335; complete single-window records only |
| Shieldstral | Native instruction, question and document wrapper | Yes/no label scores |
| GPT-OSS Safeguard | System policy, separate user record, explicit output contract | Generated binary JSON, medium reasoning |
| Jev, Kev and Clef Flash | Native Choice instructions plus ALLOW/BLOCK criteria | Native returned choice or choice-head argmax |

The [published policies](../../reports/stepguard-native/policies) contain every
exact variant. Content is serialized with named fields for the user request,
available tools, history and action, or complete run. Reference reviewer
rationales, risk tags and labels are never part of that content.

## Reading the comparison

The primary panel preserves complete records for five models. PolicyLM's native
helper has a 2,000-character window limit in addition to its token budget, so it
has a supplementary short-record panel. The other models are also reported on
those same short test records; their policies remain the ones selected on their
primary validation population. That is a matched **test** comparison, not an
equal-size policy-selection study.

The short completed-run test has only seven unsafe records. One changed decision
there has a large effect on unsafe recall. It should not become a broad ranking
of the models' ability to review long agent traces.

For practitioners, inspect false flags, missed unsafe behavior and unresolved
outputs alongside balanced accuracy. A policy that catches more unsafe behavior
may also interrupt more legitimate work. This benchmark measures agreement with
synthetic reference judgments; it does not measure whether an intervention
actually prevented harm in a running agent.
