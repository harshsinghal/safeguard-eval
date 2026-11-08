# Recovering hate-speech and pending-action performance with one Shieldstral adapter

Compare frozen Shieldstral, the prior mixed adapter, and two fresh rank-8
adapters trained from the same pinned base. Retain the prior renderer, loss,
optimizer, seed and 2,048-token training cap. Train one epoch with 864
examples and 108 optimizer steps per new adapter. Compare training token
counts and report differences. Use the prior local GPU limits and $0
provider budget.

## Data and intervention

Both adapters draw from the audited Liquid archive FIT split. The larger
mix uses 48 examples per class in each of nine tasks, by stable hash. The
targeted mix replaces 12 examples per class in completed runs, cyber
requests, harmful requests, both injection tasks and source code. Keep
skill text unchanged. Add 36 examples per class for hate speech and
pending actions. Use 36 unanimously labeled HateXplain examples per class,
20 StepGuard pending-action examples per class and 16 authored approval
pairs with deterministic labels. Within each archival target class,
prioritize incumbent errors and then low correct-label scores. Prefer
distinct archived groups for the additions. Mine scores only on FIT.
Authored pairs use simulated tools and simple explicit approval rules.
These pairs have agent-authored labels, with no independent human review.

Divide the 850 previously used development cases by archived group into
disjoint calibration and selection splits. Use a fixed stratified split
seed. Use the binary enterprise suite and the old numeric policy pairs as
reused regression checks. Use fixed, hash-selected samples from the
pinned HateCheck and R-Judge releases and separate authored pending-action
workflows for transfer checks. Retain eight cases per HateCheck
functionality and 64 per R-Judge label, preferring scenario coverage.
Use the original labels. Exclude normalized exact duplicates and check
for exact overlap with archived inputs. Unknown pretraining exposure and
unmeasured near-duplicate overlap with new sources remain possible.
Keep all transfer inputs and outcome scores out of model and cutoff
selection. ToolSafety action annotation and live-agent blocking are
separate follow-up experiments.

## Selection

Calibrate a global balanced-accuracy cutoff and task-specific cutoffs
targeting at most 10% false blocks on the calibration split. Choose
thresholds from distinct scores and the all-ALLOW threshold. For the
global cutoff, maximize the mean balanced accuracy over binary tasks.
For task cutoffs, maximize violation recall within the budget, then
prefer fewer false blocks and the higher threshold. Evaluate fixed 0.5
decisions and actual false-block rates alongside calibrated results.
For fresh sources transfer the corresponding task cutoff from the archive.

A new candidate can be nominated only if, on selection, its global
equal-task score exceeds the incumbent, no non-target task loses more
than five points in balanced accuracy, and both priority tasks match or
exceed the incumbent's recall at their calibration-derived cutoffs,
with at least one strict gain and neither exceeding 20% false blocks.
Choose the highest global score among eligible candidates, breaking ties
in favor of the balanced mix. Otherwise retain the incumbent.

Freeze the nomination and cutoffs before inference on the reused and
transfer sets. A nominated candidate passes the round only with a
positive lower paired bootstrap bound on reused-suite mean balanced
accuracy versus the incumbent, no non-target task losing more than five
points in balanced accuracy, and neither priority task losing more than
five points of recall against either the incumbent or frozen base at
calibration-derived cutoffs with actual false blocks at most 20%.
Require both outcomes correct for an authored transfer pair. Report
external results independently and report all variants even when none
qualifies. No held-out result changes the nomination. One seed and a
small transfer panel make this a pilot.
