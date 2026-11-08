# Shieldstral hill-climb round for hate speech and pending actions

[Registered plan](PLAN.md) · [Reproduce locally](RUNNING.md) · [Evidence archive](../../published_runs/2026-11-07-shieldstral-hillclimb/README.md)

## Held-out results

Neither candidate advanced. The targeted adapter improved the reused
suite mean and pending actions. Its hate-speech recall and complete
skill-package performance fell. The incumbent remains the comparison
checkpoint for the next round.

| System | Reused suite balanced accuracy | Unsafe pending actions caught | Safe pending actions blocked | Hate posts caught | Benign posts blocked |
|---|---:|---:|---:|---:|---:|
| Frozen Shieldstral | 70.75% | 26/62 | 6/63 | 21/31 | 6/32 |
| Incumbent mixed | 79.46% | 0/62 | 0/63 | 16/31 | 6/32 |
| Larger balanced | 80.58% | 17/62 | 0/63 | 15/31 | 5/32 |
| Targeted | **82.18%** | **34/62** | 1/63 | 14/31 | 5/32 |

The headline uses each system's newly calibrated global cutoff. The
counts use the independently calibrated task cutoffs. The task cutoffs
target 10% false blocks on calibration. Their realized false-block
rates vary on evaluation. The targeted gain against the incumbent was
2.72 percentage points with a paired group bootstrap 95% interval from
0.22 to 5.17 points. The larger gain was 1.11 points with an interval
from −1.08 to 3.27. At the shared 0.5 cutoff the incumbent, larger and
targeted systems scored 79.07%, 82.05% and 82.05%, respectively.

On the targeted run, global pending-action balanced accuracy rose
from 56.32% to 80.03%. Skill text rose from 41.94% to 56.45%, and source
code rose from 85.48% to 90.32%. Complete skill packages fell from
83.87% to 75.81%, and hate speech fell from 70.01% to 64.82%.
The full per-task breakdown is in the [scorecard](../../published_runs/2026-11-07-shieldstral-hillclimb/results.json).

| System | HateCheck balanced accuracy | R-Judge balanced accuracy | Safe R-Judge runs blocked | New approval pairs correct |
|---|---:|---:|---:|---:|
| Frozen Shieldstral | 77.90% | 42.97% | 32/64 | 0/12 |
| Incumbent mixed | 58.68% | 58.59% | 41/64 | 0/12 |
| Larger balanced | 66.32% | 56.25% | 41/64 | 0/12 |
| Targeted | 64.24% | 57.03% | 38/64 | **12/12** |

These are transferred task cutoffs, frozen without access to these
sources. At a shared 0.5 cutoff, the larger mix got three approval
pairs right and the targeted mix got all 12. On the old numeric policy
pairs at the global cutoffs, the incumbent got 11 of 12 right and the
targeted mix got seven. The narrow approval gain therefore coexists
with a regression on the older policy-change test.

## Frozen selection

The incumbent remained the nominee. The larger mix reached 87.65%
equal-task balanced accuracy on selection, the targeted mix 86.74% and
the incumbent 86.00%. The two candidates lost 12.5 and 17.5 points on
complete skill packages, respectively, exceeding the five-point
retention limit. The targeted mix also lost 10.90 points on skill text.

At the calibration-derived pending-action cutoffs, the incumbent caught
0 of 19 unsafe actions with zero false blocks on 15 safe actions. The
larger mix caught 5 of 19 with one false block. The targeted mix caught
9 of 19 with zero false blocks. On hate speech, the incumbent and
targeted mix each caught 12 of 23 with one false block on 41 benign
posts. The larger mix caught 11 of 23 at the same false-block count.
Selection was frozen before transfer or reused-suite inference.

## Compared training mixes

Both new rank-8 adapters start from frozen Shieldstral-1.0-3B revision
`003ec7e2b0bab5f0e6307edbaf186fa5822b76f5`. Each uses one epoch,
864 examples and 108 optimizer steps. The larger balanced mix takes 96
examples from each of nine tasks. The targeted mix retains all nine tasks,
keeps 96 skill-text examples, and moves 144 examples from six background
tasks into hate speech and pending actions. The larger mix uses 625,084
unpadded input tokens and the targeted mix uses 639,088.

We scored 682 FIT-only examples with the prior mixed adapter. The targeted
mix adds 72 existing HateXplain examples with unanimous original labels,
40 StepGuard pending actions and 32 authored approval examples. At the
incumbent's original cutoff, 34 of the added HateXplain examples and 23
of the added StepGuard examples were mistakes. The authored records use
the same action with verified versus denied approval for the exact
target. Their labels follow the stated rule. They have no independent
human review. The targeted intervention changes example allocation,
hard-example selection and the addition of approval pairs together.

## Evaluation scope

The calibration and selection partitions contain 426 and 424 records
from the previous development archive, split by group. We reused archived
base and incumbent scores on these records and the 898 reused evaluation
records. The latter include 874 binary suite cases and 24 older numeric
policy-contrast cases. The balanced-accuracy headline gives equal weight
to the ten reused tasks that contain both labels.

The separate transfer panel contains eight samples from each of
[HateCheck's 29 functionalities](https://aclanthology.org/2021.acl-long.4/),
128 completed records spanning 33 [R-Judge](https://aclanthology.org/2024.findings-emnlp.79/)
scenario groups, and 12 approval pairs from tool families held out from
the authored fit pairs. The new tools share the same verified and denied
approval vocabulary as the fit pairs. Transfer cutoffs come from the archive
calibration split. HateCheck uses the original hate policy with disability
added to its covered identities. R-Judge uses the source profile and
recorded turns without its label or risk description. The source panels
have distinct formatting and case mixtures. Exact overlap checks used
the archived split inputs. Public pretraining exposure and cross-source
near duplicates are unknown.

This round measures offline text judgments. Live prevention, legitimate
workflow completion and ToolSafety per-call review remain open.

## GPU interruptions

The first targeted fit stopped after 98 completed steps when the shared
device crossed the sustained power limit. It had no saved adapter. A
second launch stopped before model loading because available memory
fell below the 16 GiB preflight requirement. The evidence retains both
attempts. The completed targeted run used the same data, seed,
hyperparameters and GPU limits. A readiness check delayed subsequent
stages until the shared device had stable power and memory headroom.

The completed GPU stages used about 34.7 minutes of wall time, excluding
readiness waits and interrupted attempts. The completed fits each used
about 8.76 GiB peak PyTorch allocated memory. Sampled peaks on completed
stages were 50 C and 230.23 W. The interrupted fit sampled 334.98 W
during shared device contention. Measurements include other GPU
activity. All study GPU processes exited. Provider spend was $0.

The offline verifier reproduced the nomination, all scorecards and
paired intervals from archived scores. The benchmark and split test
suites passed 37 checks. The saved checkpoints match their recorded
checksums, and their 208 LoRA tensors per checkpoint are finite.
