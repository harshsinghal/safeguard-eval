# Concurrent task specialists with an any-block decision

Recorded 2 November 2026. **Experiment proposal, not a completed run.** No new
model was trained and no paid resource was provisioned for this proposal. A final
protocol must fix the combined labeling specification, data populations, training
budget, resource layout, and selection criteria before execution.

## The question

Can an inline moderation service run several compact task-specific encoders at
once, block as soon as one identifies a violation, and allow when every required
check passes? Measure the complete endpoint's accuracy and waiting time, then
increase the number of checks to understand capacity and operational cost.

This is a collection of separately enforced rules. It differs from our learned
score ensembles, where several models estimate one target and a fitted combiner
produces the decision. Here each specialist has authority to block for its own
defined category.

## Starting models

Reuse the selected **Liquid LFM2.5-Encoder-350M WildGuard fine-tune** from the
[completed study](../liquid-finetune/README.md). It reads text without a policy
document and outputs a harmful-request score. Its original checkpoint, cutoff,
split identities, and test results remain unchanged as the historical control.

Fine-tune a second copy of the same base encoder on HateXplain, preserving our
existing binary task: **hate speech is BLOCK; normal and offensive-but-not-hateful
content are ALLOW**. Use the existing group-disjoint fitting and validation
populations. Select the checkpoint and cutoff on validation, then freeze them
before final test inference. A bounded search comparable to the earlier Liquid
study would control development effort; exact runs and budget remain to be fixed.

Using one architecture initially helps isolate the effect of task specialization
and concurrent execution. It does not require that a future product use identical
architectures. Our earlier HateXplain experiment trained heads on frozen features;
it did not already produce this end-to-end Liquid HateXplain fine-tune.

The policy boundary still exists: it is embodied in the labeling instructions,
training examples, and selected cutoff. Removing policy text from inference does
not remove policy authoring or the need to test policy changes.

## Endpoint contract

The endpoint sends the same submitted text to every enabled specialist. It does
not receive the dataset identity as a routing hint. Each child response records
the model revision, task, score, cutoff, decision, and timing.

- Return **BLOCK** as soon as any required specialist returns a valid block.
- Return **ALLOW** only after every required specialist returns a valid allow.
- If a required check fails or times out and none has blocked, return an explicit
  **INCOMPLETE/REVIEW** status. Do not silently count it as allow.

For independent execution, block time is approximately the earliest completion
among blocking checks; allow time is approximately the slowest required check.
Both also include dispatch, queue, serialization, and aggregation overhead. Shared
hardware can increase the checks' durations, so this is not a claim of free
parallel speedup.

Record both the time the caller receives its answer and the time all outstanding
work actually finishes. Attempt cancellation after a block where supported, but
do not assume cancellation removes GPU work that has already been submitted.
Maintain complete audit traces for the accuracy run, even when the client could
receive a block early.

## Accuracy requires labels for the combined policy

[WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix) includes prompt
harmfulness labels. [HateXplain](https://huggingface.co/datasets/Hate-speech-CNERG/hatexplain)
labels posts as hate, offensive, or normal. They are different decisions on
different kinds of text. A non-hateful request can still seek harmful assistance.
Likewise, a quotation or educational request containing hateful words can be
benign in context. The scope of each rule must be explicit.

Randomly mixing the two tests does not create complete labels for the combined
rule. In particular, ALLOW under one rule does not establish ALLOW under the other.
Counting every additional block against the source dataset's label would conflate
false blocks with genuine violations of a second rule.

Keep three evaluations distinct:

1. **Native task accuracy.** Score each specialist on its own complete test, using
   the existing mappings: 1,699 labeled WildGuard prompts and 1,924 HateXplain posts.
2. **Cross-task behavior.** Run both specialists on both datasets and report scores,
   disagreements, and which component caused the block. The missing labels prevent
   this alone from establishing combined accuracy.
3. **Combined-policy accuracy.** Assemble a preselected mixed audit set with a
   judgment under each rule for every item. Resolve the text/context interpretation
   before annotation, keep annotators blind to model outputs, and adjudicate
   disagreements. The combined target is BLOCK if either rule is violated. Use a
   separate development portion for any joint cutoff selection and hold out the
   final audit portion. Preserve original benchmark labels; any revised interpretation
   belongs in a separate annotation layer with provenance.

A bounded human-adjudicated audit set is an alternative to relabeling both entire
tests. Model-generated cross-labels may support a clearly labeled diagnostic,
but must not be presented as independent human ground truth. Until cross-labels
exist, publish native-task accuracy and serving results without a headline combined
accuracy claim.

If joint cutoff tuning is included, use a fixed development objective for the
whole endpoint, such as best combined recall subject to a false-block limit. Keep
the unchanged individual-cutoff arm as a control. Never optimize cutoffs against
the final mixed test. A limit achieved on validation is not a guaranteed test or
production limit.

## Serving comparisons

| Arm | Purpose |
|---|---|
| Each classifier alone | Establish individual endpoint overhead and capacity. |
| Two specialists, sequential | Baseline with the same any-block rule and short-circuit behavior; record the chosen order. |
| Two specialists, concurrent | Measure latency benefit, contention, and completed work under the same decision rule. |
| Four, five, and ten specialist calls | Measure fan-out overhead and capacity as the number of required checks grows. |

For the last arm, replicas of the two trained classifiers simulate more checks.
They are **not four, five, or ten separately learned policies**. With identical
deterministic outputs, duplicating checks leaves the final label unchanged; it
adds work rather than evidence. If batching changes scores near a cutoff, record
that numerical drift rather than treating it as a new ensemble benefit.

Specify two different deployment scenarios rather than conflating them:

- **Shared device:** independently resident specialist instances on one GPU, with
  memory and compute contention. This is the main practical consolidation test.
- **Isolated resources:** separate workers with explicit GPU/CPU allocations. This
  can reduce contention but changes cost and capacity; it is a supplementary arm
  only if the approved budget supports it.

For five checks, predeclare the task-copy allocation, or measure both three-to-two
allocations. Record resident weights, worker processes, batching settings, and
actual inference invocations. Disable response memoization that could turn ten
nominal calls into one computation. Merely creating asynchronous HTTP requests
does not prove simultaneous execution on the accelerator.

Construct a seeded, shuffled traffic mix from both test populations without
training on them. A 50:50 source mixture is a transparent synthetic scenario;
report per-source results as well, and do not call it enterprise traffic prevalence.
Use complete eligible tests for native accuracy. Timing may use a preselected
representative subset, with lengths and source balance recorded. Repeated timing
requests do not become independent accuracy examples.

Measure both one incoming user request and multiple incoming requests under steady
and burst arrivals. Keep the input stream identical across serving arms. Separate
cold startup from warm service measurements, count timeouts, and include a latency
limit in the load test so overload does not look like successful throughput.

## Metrics and interpretation

- **Quality:** ordinary and balanced accuracy, false-block rate, missed-violation
  rate, and per-rule recall on appropriately labeled populations; paired uncertainty
  intervals for system comparisons.
- **Caller experience:** p50/p95/p99 completion time, separately for final blocks
  and final allows, plus incomplete responses. Allows must wait for all checks.
- **Capacity:** completed valid decisions per second within the waiting-time target,
  queue delay, failure rate, and GPU/CPU memory and utilization.
- **Work and cost:** child inferences per request, work continuing after an early
  block, device-hours, and cost at stated utilization and deployment topology.

An any-block system can catch additional violations while accumulating false
blocks. For illustration only, ten distinct checks each falsely blocking 1% of
truly all-clear inputs would jointly block about 9.6% if their errors were independent.
Errors are often correlated, and this calculation does not apply to identical
deterministic replicas. Measure the combined false-block rate directly.

The study can establish whether two learned tasks are operationally practical,
how the any-block rule changes errors, and how duplicated work scales on a specified
deployment. It cannot establish that ten independent policies have been learned,
that encoders always beat decoders, or that these tasks cover enterprise governance.
The [earlier serving study](../serving/README.md) already shows that an optimized
decoder with a short scoring output can be fast.

Before execution, register the remaining choices and reconcile the available
compute budget. Preserve the final protocol, code, training selections, annotation
provenance, timing traces, errors, costs, and resource termination evidence. Publish
the completed findings separately from this proposal.
