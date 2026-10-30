# Can training mistakes help us write a better policy?

Status: experiment registered; inference is starting. No results yet.

The previous representation study found no clear improvement over Shieldstral's
direct score. This experiment changes the policy text while keeping the model
weights fixed. Shieldstral supplies the discovery errors and selects a revision;
Qwen 4B tests whether the same revision transfers without rewriting it.

The discovery set contains 4,096 previously used fitting examples. At the native
0.5 cutoff, Shieldstral made 18 false blocks and 40 missed violations. Reviewing
these 58 cases motivated clarifications from 19 of them. The other 39 had
insufficient context, underspecified intent or a possible mismatch between the
label and policy. They remain in every evaluation with their original labels;
we did not add rules simply to force agreement with them. This is agent-assisted
interpretation, not an independent human label audit.

We froze four revisions: clarify permitted cases, clarify prohibited cases,
combine both additions, and add two short contrasting example pairs. All
original policy clauses remain. The additions distinguish a request's topic or
tone from the action being requested, and make consent, discrimination and
confidentiality boundaries more explicit. See the [readable policy edits](POLICY-EDITS.md), exact
[authoring record](authoring.json) and [policies](policies).

The data audit excludes 9,225 recorded previously used training IDs and their
duplicate groups, plus test overlaps and conflicting-label groups. New validation
has 1,536 unique groups; the additional project holdout has 2,048. These come
from unused portions of WildGuardTrain, whose labels are model-derived. We also
report the already examined, human-labeled WildGuardTest separately.

We compare policy edits at a fixed cutoff, cutoff changes alone, and their
combination. A bounded validation search chooses the revision and thresholds;
holdout/test text and outputs do not guide those choices. See the
[registered plan](PLAN.md), [discovery summary](discovery-summary.json) and
[progress record](progress.json).

The same cumulative $20 cap applies. This run reserves at most $2.40; remaining
authorization before it begins is $5.4546. Compute will be terminated and billed
usage reconciled before reporting completion.


Shieldstral validation selected the permitted-case clarification (p1). It scored
98.43% balanced accuracy, versus 98.29% for the original policy after cutoff
selection: two fewer false blocks and the same 23 missed violations. This small
validation gain is not a held-out result. The revision is frozen in commit
`22c0a62`; Qwen receives it unchanged, and no final inputs have been uploaded yet.
