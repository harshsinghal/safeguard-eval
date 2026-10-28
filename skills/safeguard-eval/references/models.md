# Model interfaces: one intent, different inputs

These are the interfaces used in the recorded experiments. For citations, resolve
the source IDs below through [sources.json](sources.json). They are not promises
about every future checkpoint or hosted provider API.

## The tested panel

| Model | How policy reached it | What the adapter read |
|---|---|---|
| PolicyLM 1.7B | Upstream `Policy` and `Category` helpers; `block` mapped to `violation_rule`, `allow` to `not_violation_rule`, `precedence` to `exception_override` | Native category scores, with a decision cutoff |
| Shieldstral 1.0 3B | Publisher's fixed system instruction; policy in `<Instruct>`, fixed BLOCK question in `<Query>`, content in `<Document>` | Normalized Yes/No label scores |
| CoPE-B-A4B | Task instruction, then POLICY, LABELS, CONTENT sections in a user message through its chat template | Normalized binary label scores |
| GPT-OSS Safeguard 20B | Policy in the system message, content in a separate user message, fixed JSON output instruction | Parsed classification; not part of the later continuous-score ensemble |
| Qwen3.5 instruction models | System classification instruction and policy, separate user content, fixed A/B mapping; thinking disabled | Label decisions; the later HateXplain Qwen-4B run also saved class scores |
| WildGuard 7B | Official fixed-task completion template; slow-tokenizer input IDs with one beginning-of-sequence token | Prompt harmfulness field from its fixed-task output |

Sources: `interface-audit`, `shared-adapters`, `wildguard-runner`, `qwen-runner`.

Qwen sizes in the generalist comparison were 2B, 4B, 9B, 27B, and 35B-A3B.
An “A” parameter count describes active parameters for a mixture-of-experts model;
do not equate it with total weights, memory use, or measured serving cost.

## Native packaging and good policy writing are separate

The early studies used these native adapters. They did not feed an identical raw
chat prompt to every model. PolicyLM did not separately consume the early `purpose`
or `review` fields; Qwen consumed `purpose` but not `review`. Those fields stayed
constant during the early candidate searches. Edited `block`, `allow`, and
`precedence` text reached all adaptive models.

This supports the within-model comparisons, but it does not isolate every wrapper
difference in cross-model comparisons. Nor does it establish a performance ceiling.
For example, PolicyLM's publisher recommends short rules separated by violation
type. Our WildGuard experiments grouped harms into one broad category. Supported
input is not the same as an exhaustive search over the best category structure.
See `interface-audit`.

The HateXplain study used a shared structured source, verified clause mappings,
and frozen rendered-input hashes. It tested presentation changes on Shieldstral
and Qwen; PolicyLM's native structured fields did not offer the same presentation
manipulation. It would be misleading to call that a three-model Markdown contest.
See `hatexplain-renderer`, `hatexplain-plan`, and `hatexplain-results`.

## How to adapt a new policy

Keep a common source for scope, definitions, violations, permitted cases,
exceptions, and examples. Then map those components to the chosen checkpoint's
supported interface. A schematic mapping is:

```text
Common rule: block a covered violation; allow the named exception.
PolicyLM:   violation_rule / not_violation_rule / exception_override
Shieldstral: policy body in Instruct + fixed question + separate Document
Safeguard:  policy in system role + content in user role
Qwen:       classification instruction + policy + explicit output labels
```

This is an explanation, not executable integration code. Read the pinned runner
for the historical implementation and current publisher documentation for a new
integration. Preserve label orientation: a high score must mean the same event
before it is combined with another model's score. Check token limits and the final
rendered input. Report unsupported clauses instead of dropping them.

A common authoring format can reduce duplication. It cannot guarantee identical
decisions. Fixed-taxonomy models may not accept arbitrary new rules at all.
Binary models do not gain a calibrated REVIEW class because a template mentions it.
Define review routing separately and test its workload and missed violations.

## What the model names do not establish

Models differ in training, architecture, score scales, and native interfaces.
Use the exact publisher card for architecture, base model, training disclosures,
and supported runtime. A small parameter count does not mean the checkpoint is
a drop-in chat model or that Ollama can load its native scoring interface.
These experiments did not fine-tune matched base/specialist pairs, isolate a causal
architectural advantage, or measure internal activations. Model size alone is not
a serving benchmark. PolicyLM's disclosed training sources include a dataset that
contains WildGuardMix; exact split overlap is unverified. The project did not audit
every model's upstream training exposure; see `model-exposure`.

The PolicyLM card's comparator table is publisher evidence, separate from our
experiments. Its inspected materials did not provide every competitor's rendered
input or a complete competitor harness. That limits independent verification; it
does not establish that those comparisons are invalid. See `interface-audit`.

For model downloads, provider articles, and guidance on authoring policies, use
[the provider reading guide](providers.md). It also separates untested discoveries
from this panel. For current publisher details, consult the model cards:
[PolicyLM](https://huggingface.co/musubilabs/policylm-1.7b),
[Shieldstral](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[CoPE](https://huggingface.co/zentropi-ai/cope-b-a4b),
[Safeguard](https://huggingface.co/openai/gpt-oss-safeguard-20b),
[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B), and
[WildGuard](https://huggingface.co/allenai/wildguard).

For local, API, and rented-GPU options—and what we actually tried locally—read
[running models](running-models.md). Serving convenience and classification
quality are separate questions; our size comparisons did not measure production
latency, throughput, retention guarantees, or cost per correct decision.
