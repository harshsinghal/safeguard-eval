# Maintaining the living research notebook

The [main README](../README.md) is the chronological entry point to the research.
It should explain what question each experiment addressed, what changed, what
happened, and what a practitioner can learn. Detailed methods and evidence live
in linked study folders; the original application lives in [DEMO.md](../DEMO.md).

**Standing workflow:** the owner has asked for these updates after every
authorized experiment, without another reminder. Completing the work includes
publishing the experiment record and README links to GitHub, reporting actual
spend, and confirming resource cleanup. See the repository's [agent instructions](../AGENTS.md).
This does not expand the budget or authorize unrelated experiments.

The [experiment map](../README.md#experiment-map) is the visual entry point. Keep
its branch labels and log numbers aligned with completed studies. Its arrows
connect research questions; they do not imply a common validation population or
a single inference pipeline. Show proposals separately and retain their execution
status. The [next-step proposal](research-directions/REDUCING-MODERATION-ERRORS.md)
now distinguishes the completed native-score smart ensemble from the remaining
representation-score, policy-optimization and second-pass proposals.

## Adding a completed experiment

1. Publish a dated evidence bundle under `published_runs/`. Include the exact
   policies, model revisions, native adapters, data splits, selection objective,
   saved predictions, analysis, and material failures. Check publication rights
   and keep credentials and private user conversations out of the archive.
2. Write a readable study summary under `docs/`, including policy edits, error
   trade-offs, limitations, compute use, and reproduction instructions.
3. Add an experiment-named entry to the README log. Use the research question or
   method as its heading, without a date. Keep entries in experiment order.
   Distinguish ordinary accuracy,
   balanced accuracy, and macro-F1; identify which settings were held fixed.
   Label pilots, proposals, synthetic demonstrations, and reused-test analyses.
4. Link the summary and frozen evidence from that entry. Preserve the historical
   result even if a later selection objective produces a different score.

Do not rewrite frozen results. Publish corrections or extensions separately,
explain the difference, and link both versions. Dates belong in provenance and
immutable archive names; they need not lead the README headings. A new study
does not automatically update the downloadable skill, paper, or other articles.

## Updating the leaderboard

The README tables are generated from a single frozen `results.json`, currently
the integration of the decision-model ensembles with the earlier studies. Do not type new scores into the
README or choose each model's largest observed test score.

After reviewing and publishing a new leaderboard archive, update `SOURCE` in
[`tools/update_readme_leaderboard.py`](../tools/update_readme_leaderboard.py),
then run:

```bash
python3 tools/update_readme_leaderboard.py
python3 tools/update_readme_leaderboard.py --check
git diff --check
```

The script only formats saved results; it makes no inference calls and changes
no selection or threshold. Review the surrounding prose separately: study scope,
candidate counts, denominators, ensemble membership, uncertainty, and links may
also need to change. The [metric guide](leaderboard/METRICS.md) must match the
scoring implementation. GitHub CI checks that the generated tables are current.

## Keeping the skill reproducible

A released skill is a dated, pinned evidence snapshot. Current research may move
ahead while that release remains intact. The README must disclose its evidence coverage
and route readers to newer studies directly. Package checks validate the
skill against its pinned Git revision; preparing a new evidence snapshot requires
a separate review and refresh. Follow the [skill maintenance guide](skill/MAINTAINING.md)
when making a new release. Do not move existing tags or silently replace a release.

## Frozen-representation follow-up

The [representation-probe study](activation-probe/README.md) is complete and
recorded separately from the common-validation leaderboard. It uses 4,096
fitting and 1,536 validation examples, with the same 1,699 WildGuardTest prompts.
Its primary combined classifier did not beat the PolicyLM-only feature probe.
The useful improvement was a supervised task-specific readout with frozen base
weights, not a new policy-text optimization result.

The [writing notes and limitations](activation-probe/NOTES.md),
[complete metrics](activation-probe/RESULTS.md), and
[immutable evidence](../published_runs/2026-10-30-activation-probe/README.md)
record the positive result, unsuccessful combination, layer-search regression,
similar native/probe AUROC, operational-target failures and compute lifecycle.
The paper, magazine/media articles and pinned skill releases have not yet been
rewritten to include this study. Preserve those distinctions when updating them.

## Shieldstral representation replication

The [Shieldstral/Qwen follow-up](shield-probe/README.md) is also complete, using
the same fitting, validation and test populations as the PolicyLM probe study.
Shieldstral's direct score reached 90.53% balanced accuracy; its feature head
90.39%; the primary combined head 90.35%. A secondary layer/pooling search helped
Qwen alone but did not make the combined method better than Shieldstral alone.
The native-score validation-to-test gap and failures of both operating-target
profiles must accompany the aggregate scores.

The [full results](shield-probe/RESULTS.md), [notes](shield-probe/NOTES.md) and
[immutable bundle](../published_runs/2026-10-30-shield-probe/README.md) include all
75 fitted candidates, frozen selections, paired comparisons, runtime and billing.
This remains separate from the common-validation leaderboard. It is evidence
about supervised readouts under a fixed policy, not another policy-editing gain.
The paper and released skill have not been silently refreshed.

## Training-error policy corrections and transfer

The [policy-correction experiment](policy-corrections/README.md) is complete.
One agent-assisted round produced four revisions from 58 discovery mistakes.
The selected permitted-case clarification did not improve Shieldstral: 98.23%
to 98.13% balanced accuracy on the additional project holdout, and 90.29% to
90.15% on reused WildGuardTest, comparing separately selected cutoffs.

The same text helped Qwen on the additional holdout: 88.85% to 89.77%, with
30 fewer misses and 10 more false blocks. The paired change was +0.92 points
(interval +0.17 to +1.70). Its reused-test change was +0.81 points, with an
interval including zero. Fixed-cutoff controls and all unsuccessful candidates
are retained. This is a model-dependent transfer result, not proof that policy
corrections reliably improve the originating model.

The new 1,536-row validation and 2,048-row holdout populations exclude recorded
prior-use groups. They come from WildGuardTrain's model-derived labels and must
remain distinct from the reused human-labeled test. None of eight operating-target
selections met its respective target on WildGuardTest. Labels were never changed,
and the 39 discovery errors with insufficient basis for an edit stayed in the study.

The [full results](policy-corrections/RESULTS.md), [exact edits](policy-corrections/POLICY-EDITS.md),
[notes](policy-corrections/NOTES.md) and [evidence bundle](../published_runs/2026-10-30-policy-corrections/README.md)
preserve the data audit, staged freezes, 46,220 score records, paired uncertainty,
source, runtime and the $0.72 reconciled bill. Both populations reproduce locally.
The paper, articles and installed skill have not been silently rewritten; this
record is material for their next explicit revision.

## Smart ensembles across model families

The [smart-ensemble study](smart-ensemble/README.md) is complete on both benchmarks.
It aligned seven WildGuard and six HateXplain score sources on 4,096 fitting and
1,536 validation examples. A bounded fitting-fold search selected components;
validation selected cutoffs. The freeze was published before final test scoring.
Policies and language-model weights stayed fixed; the combiner was supervised.

WildGuard selection retained Shieldstral alone at 90.53% balanced accuracy.
The all-model logistic control reached 90.43%; equal log-odds averaging reached
90.91%, with an uncertain gain. HateXplain selected Jev/Kev/Shieldstral at 79.97%.
It reduced both errors versus equal averaging, but traded 86 fewer false blocks
for 20 more misses versus its selected Jev individual. That individual comparison's
paired interval included zero. All-model learned controls reached about 81%; they
were not substituted for the primary after test evaluation.

Preserve these distinctions in future writing: complementarity versus a simple
average is different from beating a strong individual; passing a training addition
rule does not prove a component's test contribution; and aggregate gains can hide
operational tradeoffs. The test sets are reused. Jev scores were refreshed after
development canaries varied for identical requests; intervals do not cover that
API variability. The new result is not a policy-editing or fine-tuning gain.

The [full results](smart-ensemble/RESULTS.md) and
[frozen bundle](../published_runs/2026-10-31-smart-ensemble/README.md) preserve all
controls, coefficients, search paths, paired intervals, cost and CPU reproduction.
This study remains separate from the common-validation leaderboard. The papers,
articles and pinned skill release are unchanged; the new evidence is ready for
their next explicit update. Representation-score stacking, broader policy search
and a targeted second pass remain proposed work.

## Task-specific neural and contrastive heads

The [contrastive-head study](contrastive-heads/README.md) is complete. It compares
linear classifiers using logistic regression, ordinary small neural heads, and matched heads
with supervised contrastive loss on frozen PolicyLM and ModernBERT features.
Both benchmarks use the same 4,096 fitting / 1,536 validation populations as the
smart-ensemble study. Three neural seeds inform validation selection; no best
seed or test-based replacement is selected. This is supervised task training,
not backbone fine-tuning or a new test of policy-text optimization.

WildGuard validation selected PolicyLM's contrastive head, whose primary test
balanced accuracy was 84.78%, below the linear control's 88.37%. The other two
contrastive seeds also stayed below linear. HateXplain selected linear at 78.01%;
the contrastive head's primary 78.21% was uncertain, and its three-seed mean was
78.01%. ModernBERT's balanced-profile results were lower. These outcomes do not
establish that the model architectures themselves caused the difference.

The separately frozen accuracy goal selected a HateXplain linear configuration
at 80.46% accuracy, with 140 false blocks and 236 missed hate posts. Its balanced
selection made 332 false blocks and 113 misses. Preserve the change in objective,
regularization and cutoff rather than describing this as a free accuracy gain.
All four operating profiles, seeds, paired intervals and failed hypotheses are
recorded. All 164 candidate checkpoints reproduced exactly, and public metric
verification needs no GPU. Cost was $0.11; the GPU and temporary keys were removed.

The [evidence bundle](../published_runs/2026-10-31-contrastive-heads/README.md)
preserves the protocol, tokenizer repair, freeze, parameters/hashes, predictions,
source, provenance and billing. No fresh independent test was introduced. The
paper, articles and pinned skill remain prior snapshots awaiting explicit revision.

## Supervised Liquid encoder fine-tuning

The [Liquid study](liquid-finetune/README.md) implements the newly authorized
backbone fine-tune on WildGuard prompt harmfulness. It uses the same 4,096 fitting,
1,536 validation and 1,699 test populations as the earlier head study, with
LiquidAI/LFM2.5-Encoder-350M at revision
`b886781f7c6f10ca9b7096e21b83e30a073c2f39`. Prompt text only enters a mean-pooled
encoder and binary linear head. No policy text or generated answer is used.

Two learning rates, three epochs and three seeds yielded 18 fine-tuned
checkpoints; a frozen-encoder logistic control tried five C values. Validation
selected epoch 3 at learning rate 5e-5 for every fine-tuning profile, with different
cutoffs. Primary ordinary-accuracy cutoff was 0.68; the balanced cutoff was 0.86.
The choices were committed in `317e792` before uploading test inputs. Test labels
stayed local. Every selected checkpoint exactly replayed its validation scores.

Primary test accuracy was 86.40% (balanced 85.49%), versus frozen 82.22%
(balanced 80.88%). False blocks fell from 68 to 60, missed harmful prompts from 234
to 171. The paired accuracy gain was 4.18 points, 95% CI [2.71, 5.65]. Three-seed mean
accuracy was 86.23%, range 85.52–86.76%; all seeds improved accuracy, although one
made two more false blocks than the frozen control. These results remain below
the earlier PolicyLM linear-head and released WildGuard reference results under
their original protocols. They do not establish an architecture-wide ranking.

Do not hide the default-cutoff control: the same primary fine-tuned checkpoint
at 0.5 scored 86.93%, with 70 false blocks and 152 misses. It is supplementary, not a
test-selected replacement. Mean validation accuracy 93.99% exceeded mean
test 86.23%. The separately validation-selected 5% false-block and 90% recall
targets failed on test. Fine-tuning improved this bounded task pipeline; it did
not remove the need for a representative benchmark or a tested operating point.

The [evidence bundle](../published_runs/2026-10-31-liquid-finetune/README.md)
contains all validation outputs, seeds, settings, test scores, uncertainty,
source, environment, hashes and billing. No test prompt was truncated or dropped.
Exact input restoration succeeded for all three splits. Public verification
recomputes selections and metrics; it does not claim an independent GPU refit.
Large weights and features stay local. The public test is reused, and this
fine-tuning study remains separate from the common leaderboard. The paper,
articles and released skill were not rewritten in this turn.


## Serving moderation models: capacity, waiting time and GPU cost

The [serving study](serving/README.md) adds operational measurements to the
classification experiments. Seven pinned systems ran serially on one L40S at
$0.80/hour: three through vLLM 0.32.0 and four through native classification heads.
The historical policies, weights and cutoffs were fixed. Ninety-six unlabeled
WildGuardTrain inputs selected bounded serving settings; 384 separate
WildGuardTest inputs were measured at concurrency 1, 8, 32 and 64, with three
repeats. Labels were not used to select a runtime or change a classifier.

At concurrency 32, shared-policy caching raised Shieldstral from 35.9 to 237.0
valid classifications/second. Qwen had zero cache hits under the recorded hybrid
cache layout and remained about 42/second. WildGuard's cached profile reached
51.5/second at concurrency 64, with p95 latency about 1.37 seconds. The complete
curves show how queueing and batching alter the waiting-time/capacity tradeoff.
These are loopback closed-loop pilots, not production arrival-rate or p99 tests.

A separately registered native-kernel extension raised Kev from 29.0 to 61.2/s
and Clef from 7.1 to 10.8/s at concurrency 32. Clef retained its reference
convolution and its best observed throughput was at concurrency 1. PolicyLM's
32,768-token internal batch budget was rejected: its eight-row candidate was
slower and exceeded the fitting score-drift gate, while 32 rows ran out of memory.
Its original 1,024-token profile remains the accepted result. The fine-tuned
Liquid encoder reached 358.4/s at concurrency 32, but uses a fixed learned
boundary rather than a policy document. Different output contracts and backends
prevent treating this table as a causal architecture or equal-quality ranking.

The consistency checks also matter. A newer Transformers version silently
returned a fast tokenizer for WildGuard despite use_fast=False; all 480 token
sequences differed. Those fitting attempts were discarded, the original slow
client tokenizer was pinned, and WildGuard selection was restarted before any
accepted measurements. Some accepted runtime/batch conditions changed a few
labels relative to single-request or historical outputs. Report those differences
and revalidate quality before replacing a production inference configuration.

The [evidence bundle](../published_runs/2026-10-31-serving/README.md) contains
144 accepted timed passes, 55,296 valid responses, frozen settings, fitting
failures, policy/source hashes, environment records and per-request traces.
“Valid” means a parsed classification, not a correct answer. GPU-only dollars
per million assume sustained measured traffic; a GPU kept on for 30 days at this
rate costs $576 even when idle. Actual experiment cost was $1.65, with termination
and key removal confirmed. No paid inference API or RunPod resource was used.
The quality leaderboard, papers, articles and released skill remain separate
snapshots; this study does not silently revise their accuracy claims.


## Prompt length and inference engines on a common-cloud GPU

The [L4 follow-up](cloud-serving/README.md) asks whether the serving engine or the
request shape matters more when planning a moderation endpoint. AWS G6 and
Google Cloud G2 both offer L4 GPUs. We rented one through GPU.ai, at $0.59/hour,
without accessing either cloud. The actual host enforced 3.4 CPU cores and about
19 GB RAM. Matching the GPU does not reproduce another provider's VM or price.

Qwen3.5 4B received identical token IDs through vLLM 0.32.0 and SGLang 0.5.23,
using BF16, its historical policy, thinking disabled, an eight-token output cap
and disabled prefix/radix caching. Both engines selected a 2,048-token processing
chunk on 64 original fitting prompts. Neutral synthetic documents then varied
submitted content across 64, 256, 1,024 and 4,096 tokens; the policy/template added
402 tokens. A mixed group contained equal numbers from each bin. Concurrency
was 1, 8 or 32, with two 64-request repeats per condition.

Engine timings were similar. Single-request medians ranged from 159 to 829 ms
for vLLM and 157 to 815 ms for SGLang. At concurrency eight, long-input median
latency was about six seconds and throughput only about 1.35/second. At 32,
long-input p95 was about 24 seconds. The exploratory 8,192-token chunk control
improved neither engine's long-input throughput. vLLM's median improved slightly
at concurrency eight while its p95 worsened. These short closed-loop passes
estimate operating behavior, not production service levels or global optima.

The selected Qwen engines disagreed on one of 32 natural fitting labels; each
also changed one label between serial and batched fitting. Valid timed responses
are not evidence of unchanged accuracy. SGLang initially rejected the text-only
flag for this architecture. Its repaired default wrapper retains unused vision
weights, unlike the vLLM text-only path. Different dependency stacks and resident
weights prevent isolating scheduler performance. Failures and amendments remain
in the archive, and the earlier L40S run also requested a different output payload,
so this is not a controlled L4-versus-L40S comparison.

Shieldstral's optional work was a separate 32-prompt scoring canary, not a
capacity test. Removing SGLang's unsupported flag exposed a weight-name error.
A directory containing only the pinned Hugging Face-format files resolved it;
no tensors were transformed. Both engines then passed the serial/batch gate.
Serial labels agreed on all 32 prompts, with maximum score difference about
0.000002. vLLM scores were identical before and after selecting the HF-only files.
These checks establish a working interface for this sample, not full quality parity.

The [archive](../published_runs/2026-11-01-cloud-serving/README.md) contains 68
Qwen timed passes, 4,352 valid requests, specialist checks, all failure stages,
registrations, source snapshots, hashes, runtime records and the bill. The study
cost $0.62, bringing cumulative accounted spending to $19.36001787256. The GPU
was terminated and temporary keys removed. CPU-only verification recomputes
metrics and checks output contracts; it is not an independent inference rerun.
The [deployment guide](cloud-serving/DEPLOYMENT.md) connects these findings to
prompt limits, cache behavior, model adapters, release checks and cloud planning.
The common quality leaderboard, reviewed articles and pinned skill remain
separate snapshots.

## Retrieved labeled examples with fixed decisions

The [retrieved-example study](retrieved-examples/README.md) is complete on
WildGuard. It uses the existing 4,096 fitting and 1,536 validation populations,
with an eligible bank of 1,814 distinct fitting groups, and the 1,699 labeled
official test prompts. PolicyLM, Shieldstral, Kev and Jev each receive policy-only,
fixed-four, nearest-four and two-per-class conditions. A shared neighbor-voting
control is also scored. No model weights or output cutoffs are fitted.

Four nearest examples reduced ordinary accuracy for PolicyLM and Shieldstral,
and slightly increased it for Kev and Jev; the latter gains versus policy-only
have intervals including zero. Validation nominated policy-only for the two
specialists and balanced examples for the two decision models. Their frozen
test accuracies are 86.70%, 90.82%, 88.11% and 89.76%, respectively. The neighbor
vote scored 70.04%. Error counts reveal different false-block/miss trades.

The [complete comparison](retrieved-examples/RESULTS.md),
[technical amendments](retrieved-examples/NOTES.md), and
[immutable bundle](../published_runs/2026-11-01-retrieved-examples/README.md)
include the pre-test freeze, prompt-free predictions, source snapshots, grouped
paired intervals, independent metric checks, a $0.874933148 reconciled bill, and
verified termination. Native PolicyLM required single-line category fields;
Shieldstral used single-request execution after a batch-score consistency check.
These repairs preceded final testing and remain documented.

Keep this fixed-decision, accuracy-nominated study separate from the common
calibrated leaderboard. It is exploratory evidence on a reused benchmark and
particular example wrappers, not a general model-family or retrieval claim.
Papers, articles and versioned skill releases have not been rewritten.
