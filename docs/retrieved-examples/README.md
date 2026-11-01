# Relevant examples, unchanged decision rules

**Status: inference in progress under a separately authorized $20 experiment budget.**

This experiment asks whether a moderation model makes fewer mistakes when its
policy includes labeled examples similar to the request it is judging. We compare
PolicyLM 1.7B, Shieldstral 3B, Kev 4B and Jev 1.14 on WildGuard prompt harmfulness.
Model weights and decision cutoffs stay fixed. This is an accuracy study, with
no calibration or serving-latency comparison.

| Condition | What changes |
|---|---|
| Policy only | Existing policy, without examples |
| Four fixed examples | The same two benign and two harmful fitting examples for every request |
| Four nearest examples | The four most similar eligible fitting prompts, with their labels |
| Balanced nearest examples | Two nearest benign and two nearest harmful fitting prompts |
| Nearest-neighbor voting | A shared control using the four neighbors' labels without a moderation model |

The example library contains **1,814 distinct fitting groups**, including 756
benign and 1,058 harmful examples. It comes from 4,096 recorded fitting rows.
Examples must have 8–80 words and at most 400 characters so that four complete
examples can fit the models' policy interfaces. This excludes 2,138 rows by
length/content eligibility and collapses 144 additional eligible duplicates.
The study tests retrieval from that documented subset, not the entire dataset.

E5-small-v2 provides frozen text embeddings. Labels help balance demonstrations
when requested, but validation and test labels never choose neighbors or enter
the model request. Validation contains 1,536 prompts; the official test contains
the same 1,699 labeled prompts used in earlier work. Every condition will be
reported, including regressions. Validation nominates a condition before test
evaluation; a better-looking test condition does not replace that nomination.

Different models need different example delivery. Jev and Kev use native Choice
instructions. Shieldstral keeps its Instruct/Query/Document separation. PolicyLM
receives illustrations within its native category description; this is an
experimental few-shot format whose compatibility is checked on fitting cases.

The main comparisons are changes within each model. Scores from earlier studies
with calibrated cutoffs do not establish a matched baseline here. Reusing the
public test makes this an exploratory follow-up, not a fresh blind evaluation.

[Registered plan](PLAN.md) · [Research notes](NOTES.md) · [Run and reproduce](RUNNING.md)

No final-test accuracy improvement has been measured in this new study yet.
The user authorized a fresh $20 budget; earlier study spending is accounted
separately. Native compatibility checks and validation precede the frozen test.
