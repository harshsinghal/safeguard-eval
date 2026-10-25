# Prompt search ledger

The policy text is rendered as a system instruction. We changed the rule wording and, in some candidates, its explicit scope. Model weights and the output wrapper stayed fixed. Candidate IDs are version labels; they are not a ranking.

| Model | Candidate | Parent | Fitting accuracy | Validation accuracy | Selected |
|---|---|---|---:|---:|---|
| Qwen3.5-2B | [wg-p0-taxonomy](../../evals/qwen_policy/../wildguard/policies/p0.json) | inherited shared text | 82.91% | 84.18% |  |
| Qwen3.5-2B | [wg-p1-concrete-harm](../../evals/qwen_policy/../wildguard/policies/p1.json) | inherited shared text | 83.79% | 86.72% |  |
| Qwen3.5-2B | [wg-p2-boundary-checklist](../../evals/qwen_policy/../wildguard/policies/p2.json) | inherited shared text | 86.04% | 87.70% | yes |
| Qwen3.5-4B | [wg-p0-taxonomy](../../evals/qwen_policy/../wildguard/policies/p0.json) | inherited shared text | 90.33% | 89.45% |  |
| Qwen3.5-4B | [wg-p1-concrete-harm](../../evals/qwen_policy/../wildguard/policies/p1.json) | inherited shared text | 91.80% | 91.02% | yes |
| Qwen3.5-4B | [wg-p2-boundary-checklist](../../evals/qwen_policy/../wildguard/policies/p2.json) | inherited shared text | 91.11% | 90.43% |  |
| Qwen3.5-9B | [wg-p0-taxonomy](../../evals/qwen_policy/../wildguard/policies/p0.json) | inherited shared text | 92.38% | 92.38% |  |
| Qwen3.5-9B | [wg-p1-concrete-harm](../../evals/qwen_policy/../wildguard/policies/p1.json) | inherited shared text | 93.16% | 93.36% |  |
| Qwen3.5-9B | [wg-p2-boundary-checklist](../../evals/qwen_policy/../wildguard/policies/p2.json) | inherited shared text | 91.60% | 93.75% |  |
| Qwen3.5-27B | [wg-p0-taxonomy](../../evals/qwen_policy/../wildguard/policies/p0.json) | inherited shared text | 92.48% | 91.80% |  |
| Qwen3.5-27B | [wg-p1-concrete-harm](../../evals/qwen_policy/../wildguard/policies/p1.json) | inherited shared text | 94.04% | 94.53% | yes |
| Qwen3.5-27B | [wg-p2-boundary-checklist](../../evals/qwen_policy/../wildguard/policies/p2.json) | inherited shared text | 93.16% | 93.55% |  |
| Qwen3.5-35B-A3B | [wg-p0-taxonomy](../../evals/qwen_policy/../wildguard/policies/p0.json) | inherited shared text | 92.87% | 92.97% |  |
| Qwen3.5-35B-A3B | [wg-p1-concrete-harm](../../evals/qwen_policy/../wildguard/policies/p1.json) | inherited shared text | 92.87% | 94.53% |  |
| Qwen3.5-35B-A3B | [wg-p2-boundary-checklist](../../evals/qwen_policy/../wildguard/policies/p2.json) | inherited shared text | 93.07% | 93.75% |  |
| Qwen3.5-2B | [qwen-2b-p3-grounded-boundaries](../../evals/qwen_policy/policies/qwen-2b-p3-grounded-boundaries.json) | wg-p2-boundary-checklist | 84.77% | 86.91% |  |
| Qwen3.5-2B | [qwen-2b-p4-compact-evidence](../../evals/qwen_policy/policies/qwen-2b-p4-compact-evidence.json) | wg-p2-boundary-checklist | 83.69% | 85.94% |  |
| Qwen3.5-4B | [qwen-4b-p3-deliverable-and-exceptions](../../evals/qwen_policy/policies/qwen-4b-p3-deliverable-and-exceptions.json) | wg-p1-concrete-harm | 89.26% | 89.65% |  |
| Qwen3.5-4B | [qwen-4b-p4-content-and-request](../../evals/qwen_policy/policies/qwen-4b-p4-content-and-request.json) | wg-p1-concrete-harm | 89.55% | 88.87% |  |
| Qwen3.5-9B | [qwen-9b-p3-social-and-sensitive-boundaries](../../evals/qwen_policy/policies/qwen-9b-p3-social-and-sensitive-boundaries.json) | wg-p1-concrete-harm | 92.29% | 94.14% | yes |
| Qwen3.5-9B | [qwen-9b-p4-compact-substance](../../evals/qwen_policy/policies/qwen-9b-p4-compact-substance.json) | wg-p1-concrete-harm | 91.70% | 92.77% |  |
| Qwen3.5-27B | [qwen-27b-p3-evidence-and-sensitive-data](../../evals/qwen_policy/policies/qwen-27b-p3-evidence-and-sensitive-data.json) | wg-p1-concrete-harm | 93.16% | 92.77% |  |
| Qwen3.5-27B | [qwen-27b-p4-compact-substance-and-endorsement](../../evals/qwen_policy/policies/qwen-27b-p4-compact-substance-and-endorsement.json) | wg-p1-concrete-harm | 92.38% | 92.58% |  |
| Qwen3.5-35B-A3B | [qwen-35b-a3b-p3-action-object-boundaries](../../evals/qwen_policy/policies/qwen-35b-a3b-p3-action-object-boundaries.json) | wg-p2-boundary-checklist | 91.31% | 92.38% |  |
| Qwen3.5-35B-A3B | [qwen-35b-a3b-p4-compact-content-and-purpose](../../evals/qwen_policy/policies/qwen-35b-a3b-p4-compact-content-and-purpose.json) | wg-p2-boundary-checklist | 93.16% | 94.53% | yes |

## What the ten new drafts changed

**qwen-2b-p3-grounded-boundaries** — Fitting p2: 82 false blocks and 61 misses. Clarify ordinary competition/metaphor, public versus confidential facts, and harmless fiction while covering practical fictional harm, substantial protected works and harmful transformations.

**qwen-2b-p4-compact-evidence** — Compact alternative from the same fitting errors: reduce overlapping instructions and require identifiable prohibited output, while distinguishing endorsement from discussion.

**qwen-4b-p3-deliverable-and-exceptions** — From p1 fitting errors (41 false blocks, 43 misses): distinguish neutral history, prevention and ordinary creative scenarios from usable harmful deliverables; retain mixed-request and disguised-harm checks.

**qwen-4b-p4-content-and-request** — Tests a broader prompt-harmfulness interpretation for fitting misses containing harmful assertions or endorsements, while preserving analysis/quotation exceptions and reducing suspicion-based false blocks.

**qwen-9b-p3-social-and-sensitive-boundaries** — P1 fitting has 26 false blocks and 44 misses, including 13 social-group and six private-information cases. Clarifies group portrayals, requests to validate harmful beliefs and sensitive-attribute scope, while retaining benign fiction/context limits.

**qwen-9b-p4-compact-substance** — Concise alternative from p1 fitting mistakes: preserve the taxonomy, distinguish harmful requests from the possibility of a safe refusal, and reduce invented-context false blocks.

**qwen-27b-p3-evidence-and-sensitive-data** — Parent p1; fitting false blocks often infer sexual content, criminal concealment or harmful intent from vague fiction, while missed privacy examples concern real-person health and medication. Tests explicit evidence boundaries and broader sensitive-data coverage.

**qwen-27b-p4-compact-substance-and-endorsement** — Parent p1; tests a shorter rule and direct harmful-endorsement scope alongside the evidence boundary. Training contains conversational endorsements and degrading portrayals missed by an output-method-only reading; no source-specific exceptions.

**qwen-35b-a3b-p3-action-object-boundaries** — Parent p2; fitting errors include false blocks on underspecified requests, benign transformations, security/safety discussion and imaginary relationships, with misses on privacy, realistic forgery and disguised harmful content. Tests action-and-object evidence without entity-specific rules.

**qwen-35b-a3b-p4-compact-content-and-purpose** — Parent p2; tests shorter scope that includes direct harmful endorsements and abusive input, motivated by fitting conversational misses. Benign quoted analysis and unsupported hidden-intent inferences remain excluded; this is an explicit scope hypothesis.

## How to read selection

2B chose the inherited checklist (p2); 4B and 27B chose the inherited prose prompt (p1). The 9B tailored p3 improved validation accuracy by two examples over p2. The 35B-A3B tailored p4 tied p1 on validation accuracy and won because it was shorter. Only one tailored draft strictly improved on its model’s best inherited validation accuracy. Selection was mechanical and happened before new Qwen test inference.

Training examples guided the drafts; individual validation mistakes did not. Some training labels have ambiguous or missing context. We kept those labels, avoided source-specific exceptions, and documented that optimizing agreement can move a policy toward a dataset’s annotation conventions. The final test is separate from prompt selection, but its benchmark and prior specialist results were already known.
