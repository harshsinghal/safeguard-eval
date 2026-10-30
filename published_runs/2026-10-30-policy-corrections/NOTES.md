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


At the fixed 0.5 cutoff, p1 corrected six discovery mistakes and introduced six
new ones. Only three of the 19 cases that motivated edits became correct under
p1. The combined p3 revision corrected eight and introduced six; p4 corrected six
and introduced nine. These are descriptive development checks, not held-out
improvements. They show why a plausible error explanation is not sufficient to
establish that a policy edit works.

Every Shieldstral development input was scored without truncation or unresolved
outputs. All full-forward parity differences were 0.0, and the top vocabulary
token was always one of the two canonical labels. The longest development input
was 3,719 tokens, below the registered limit of 8,192.


## Final freeze, before holdout/test inference

On Qwen validation, the original policy scored 88.1194% balanced accuracy at
0.5 and 89.6089% with its selected cutoff of 0.57. The transferred p1 revision
scored 90.4324% at its native 0.5 cutoff. Compared with the tuned original rule,
it had nine more false blocks (81 versus 72) and 23 fewer misses (65 versus 88).
This is a validation tradeoff; it does not yet establish transfer improvement
on held-out data. Qwen had no separate wording search.

Both models' policy and cutoff choices, including separate false-block and
recall operating targets, were frozen before uploading final inputs. Restoring
the 2,048 additional holdout prompts and 1,699 test prompts from the pinned
Parquet files reproduced the registered input hashes. No held-out example text
was inspected to alter the policies.


## Shieldstral final scores, after all choices were frozen

The original policy with its selected cutoff reached 98.2267% balanced accuracy
on the additional project holdout; the revised policy reached 98.1290%. The
revision corrected one case and introduced three errors: false blocks increased
from seven to eight and misses from 30 to 31. The paired difference was −0.0978
percentage points, with a descriptive 95% interval of −0.2936 to +0.0903.

On reused WildGuardTest, the tuned original scored 90.2865% and the revision
90.1539%. Both had 57 false blocks, while misses rose from 101 to 103. The
revision corrected two cases and introduced four; the difference was −0.1326
points, interval −0.4305 to +0.1382. At a fixed cutoff of 0.5, neither population
showed an improvement either. These small differences do not establish that the
revision is systematically worse, but they do not support replacing the original
policy on the basis of this authoring round.

These scores were read while Qwen's final inference continued. All Qwen choices
were already frozen, and no change was made in response to these outcomes.
The full joint evaluation and reproduction check remain the final authority.


For clarity, Qwen's validation tradeoff depends on the comparator. At the common
0.5 cutoff, p1 reduced false blocks from 115 to 81 while keeping misses at 65.
Against the original policy's separately selected 0.57 cutoff, p1 instead had
more false blocks and fewer misses. This is why the full tables retain both
fixed-cutoff and independently tuned comparisons.


The secondary operating targets show a distribution gap. Both Shieldstral
policies met their separately selected 5% false-block target and 90% recall
target on the additional project holdout. On reused WildGuardTest, the
false-block-target choices instead produced 8.47% and 8.78% false blocks. The
separate recall-target choices reached only 82.23% and 82.76% harmful recall.
These are separate operating points, not a requirement that one threshold meet
both constraints simultaneously. Validation targets are not deployment guarantees.


## Qwen additional-holdout transfer result

The transferred revision reached 89.7681% balanced accuracy on the additional
project holdout, compared with 88.8517% for the original policy with its selected
cutoff. The difference was +0.9164 percentage points (descriptive 95% interval
+0.1737 to +1.7016). It corrected 42 cases and introduced 22. False blocks rose
from 100 to 110, while misses fell from 129 to 99.

At the same 0.5 cutoff, the comparison is different: false blocks fell from 140
to 110 while misses increased from 89 to 99. Balanced accuracy rose from 88.7295%
to 89.7681%, a +1.0386-point change (interval +0.3625 to +1.7292). Thus the
observed wording effect survives a fixed-cutoff comparison on this population,
but its error tradeoff depends on the baseline operating point.

This is transfer of one Shieldstral-selected revision, not a fresh Qwen policy
search or a measurement of Qwen's best achievable performance. Qwen's remaining
WildGuardTest batch was still running when these held-out results were recorded;
no model, text or cutoff was changed.


## Final Qwen comparison and verification

On reused WildGuardTest, the tuned original Qwen rule reached 86.0114% balanced
accuracy and the revision 86.8219%. The difference was +0.8105 points, with a
descriptive 95% interval of −0.04 to +1.63 after rounding. The revision corrected
31 cases and introduced 21. False blocks increased from 119 to 130; misses fell
from 116 to 95. At a fixed 0.5 cutoff, the change was only +0.3541 points, also
with an interval including zero. The test result is suggestive, not a clear gain.

Local CPU reproduction matched all final metrics, validation selections, slices,
operating profiles and twelve paired bootstrap contrasts. Every one of 46,220
prediction records was resolved; no input was truncated. All 192 development
full-forward parity checks had difference 0.0. Four final Qwen records had a top vocabulary token outside the canonical pair.
They retain their conditional two-label scores under the registered protocol.
This is not free-generation behavior or a count of free-generated valid answers.

Qwen used the fallback Torch linear-attention implementation. Runtime records
are from instrumented, single-example scoring and include setup/parity overhead
where applicable; they are not a production-serving throughput comparison.
The original L40S rental was terminated after evidence collection. GPU.ai billed
3,229 GPU-seconds, $0.72 at $0.80/hour. The cumulative ledger is now
$15.26540555656 of $20, with $4.73459444344 remaining. Temporary local/provider
SSH keys were removed. RunPod was not used.

No policy revision followed final evaluation. The source-hashed inference and
selection code and registered protocol remained unchanged throughout the run.
Reporting tools and explanatory notes were developed alongside execution. A
future correction round needs a new development/evaluation boundary; these
results must not become a new tuning set while still being called untouched.
