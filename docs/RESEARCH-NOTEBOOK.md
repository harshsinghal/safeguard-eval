# Maintaining the living research notebook

The [main README](../README.md) is the chronological entry point to the research.
It should explain what question each experiment addressed, what changed, what
happened, and what a practitioner can learn. Detailed methods and evidence live
in linked study folders; the original application lives in [DEMO.md](../DEMO.md).

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
