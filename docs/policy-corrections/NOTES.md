# Policy-correction research notes

This record explains decisions made during execution. The source-hashed
[protocol](PLAN.md) remains unchanged. Results are reported separately so an
outcome cannot silently become a design decision.

## Why a new holdout was needed

The preceding representation study had already exposed its validation and test
outcomes. Editing a policy using those mistakes and reporting the same test as
fresh would blur development and evaluation. We therefore audited recorded
training-data use before inspecting discovery error text. The audit examined
1,428 evidence files, found 9,225 previously used training IDs, and excluded their
recorded duplicate groups. Test overlaps and conflicting-label groups were also
excluded. Preparing a full assignment inventory was distinguished from actually
evaluating or reviewing its examples.

This left enough unused groups for 1,536 validation examples and an additional
2,048-example project holdout. Each contains one example per recorded group.
These are from WildGuardTrain, whose labels are model-derived. The official,
human-labeled WildGuardTest remains a separate, reused historical comparison.
Project-level non-use does not establish that a released checkpoint never saw
these public data during its own development.

## What the error review could and could not justify

We inspected all 58 errors from the original Shieldstral policy on the fixed
4,096-example discovery set: 18 false blocks and 40 missed violations. The review
found 19 cases that motivated general clarifications. For the other 39, missing
context, underspecified intent or a possible policy/label disagreement gave
insufficient grounds for changing the policy. Every original label remains in
the experiment. These judgments are agent-assisted authoring decisions, not an
independent expert adjudication of the dataset.

The original policy here, p0, is the earlier study's selected p4 policy
(`wg-p4-shieldstral-taxonomy-priority`); the local p0–p4 names restart for this
experiment. Four revisions were frozen before new inference: add permitted-case boundaries;
add prohibited-case boundaries; combine both; add two contrastive example pairs
to the combination. The exact clauses and motivating source IDs are recorded
in [authoring.json](authoring.json). We preserved the original clauses and did
not copy discovery prompts into the policy. Preserving intended scope is an
author judgment; adding a clarification can still change how a model understands
the boundary. This is not a pure formatting experiment.

## What this experiment changes

Only the policy and the score cutoff vary. Both model checkpoints, their native
input adapters and their weights stay fixed. The revised policy is selected
using Shieldstral validation results, then transferred unchanged to Qwen. Qwen
can select its own cutoff but cannot rewrite or choose another revision.

The four comparisons for each interpreter are the original policy at cutoff
0.5, original policy with a selected cutoff, revised policy at 0.5, and revised
policy with a selected cutoff. This separates changes in policy text from
changes in the strictness of the decision rule. A revised policy can lose to
the original; the protocol does not suppress that result.

## Implementation checks before inference

The first local preparation attempt assumed the historical assignment inventory
contained labels. It did not; preparation was corrected to check the pinned
Parquet labels directly before populations were frozen. A test originally
searched the Python representation of an adapter payload rather than its actual
message content; the test was corrected. Four focused tests then passed,
including a complete synthetic staged selection and mutation checks.

The source, candidate policies and discovery review were registered in commits
`016d671` and `5c347b4` before new inference. Development input restoration from
the source Parquet reproduced the exact registered input hashes. The GPU run
uses native-template tokenization checks and compares the first 16 scores in
each development batch with a full-model forward pass. The original discovery
scores are also compared with the earlier experiment before selecting a revision.

## Relation to prompt optimization research

[ProTeGi](https://arxiv.org/abs/2305.03495) motivates learning prompt revisions
from errors, but it also defines a particular search procedure. Our experiment
uses one bounded, agent-assisted authoring round. It is not a ProTeGi replication,
a new optimization algorithm, or evidence that this set of edits is optimal.


## Shieldstral selection, before Qwen inference

Validation selected p1, the permitted-case clarification. Balanced accuracy was
98.4282%, compared with 98.2922% for the original policy with its selected cutoff
of 0.51. p1 retains the native 0.5 rule. It has two false blocks and 23 misses on
validation; the original tuned rule has four and 23. The best discovery result
was p3, but discovery did not select the revision. The examples in p4 did not
improve validation. No wording was changed after this feedback.

The fresh original-policy discovery scores exactly match the cached scores
(maximum absolute difference 0.0). The selection and all supporting scores were
frozen before Qwen validation. This small validation difference is a selection
outcome, not yet evidence that the revision improves held-out decisions.
