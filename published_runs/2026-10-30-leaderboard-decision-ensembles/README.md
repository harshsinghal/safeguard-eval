# Integrated leaderboard: decision-model ensembles alongside earlier studies

Open the [full tables](RESULTS.md), [CSV](leaderboard.csv), or [interactive comparison](index.html).
Download the HTML to use it locally; GitHub displays its source. Read the
[experiment's findings](../../docs/decision-ensemble/README.md) and the
[metric guide](../../docs/leaderboard/METRICS.md) for interpretation.

This comparison contains **38 WildGuard entries and 20 HateXplain entries**,
drawn from **261 candidate records**. It combines the prior 20-entry comparison
with 18 WildGuard decision-model combination methods. It adds no inference,
refitting, policy search, or GPU/API charges.

## What was added

We include seven score-combination families—raw and calibrated probability
averages, log-odds averaging, learned weights, probability and log-odds logistic
regression, and random forests—and two controls using decisions only: logistic
regression and majority voting. Each appears for Jev/Kev/Clef and for open-only
Kev/Clef. These are 52 additional candidate records grouped into 18 methods,
not 52 different models or independent replications. The decision-model
combinations have not been evaluated on HateXplain.

The new rows copy the [source study](../2026-10-30-decision-ensemble/README.md)'s
frozen validation choices. Their combiners were originally fitted on 1,024
WildGuardTrain examples, with settings selected on 512 validation examples and
tested on 1,699 WildGuardTest examples. No underlying language-model weights
were updated. The source experiment used brief/detailed policies only because
example-bearing policies had no fitting scores.

| Selected system | WildGuard balanced accuracy | False blocks | Missed harmful prompts |
|---|---:|---:|---:|
| Earlier specialist equal log-odds ensemble | 91.08% | 52 | 93 |
| WildGuard 7B reference | 89.81% | 51 | 113 |
| Jev + Kev + Clef: primary probability logistic ensemble | 89.32% | 69 | 106 |
| Jev 1.14 individual reference | 88.69% | 47 | 133 |
| Kev + Clef: primary probability logistic ensemble | 87.52% | 63 | 138 |

The primary three-model result is only 0.63 balanced-accuracy points above Jev,
with a paired 95% interval of −0.43 to +1.58. The new ensemble did not establish
a clear gain. Its two decision-only controls also illustrate a different
operational trade-off: they meet the validation-selected 5% false-block limit
on test, while the primary score ensembles do not.

The equal log-odds combination of the three decision models observed 89.74% on
test. It remains a secondary result. The method selected as best on validation
was a weighted average, with 89.08% on test. Neither replaces the registered
primary method after test inspection. “Best method” aliases are not additional
leaderboard entries.

## What stayed fixed

The [prior archive](../2026-10-29-leaderboard-decision-models/README.md)'s model
entries, candidate pools, policies, cutoffs, test results, and confidence
intervals remain unchanged. Displayed ranks can move. The new study's individual
calibration controls stay in its report rather than being pooled into prior
individual-model selections. In particular, the earlier Clef individual row
uses its example-bearing policy; the new combinations use detailed Clef.

The integration verifies **119 existing operating-point rows unchanged** and
**51 added eligible operating-point rows against the source study**. Ineligible
profiles remain visible gaps. [extension-provenance.json](extension-provenance.json)
records these checks; [registry.json](registry.json) and
[selection.json](selection.json) identify each configuration.

This is retrospective publication of already-known results. It is not another
blind evaluation. Historical search budgets, policy pools, and fitting sizes
differ. The two tests have been reused across this research. Confidence intervals
are descriptive and unadjusted. The table measures classification, not matched
serving cost, latency, or enterprise deployment quality.

## Reproduce without inference

Install [requirements.txt](requirements.txt) in a Python environment. From this folder:

```sh
PYTHONPATH=source python -m evals.leaderboard.build reproduce --bundle .
```

This recomputes validation selections, test metrics, subgroup results, 2,000-draw
bootstrap intervals, and all paired comparisons, requiring exact equality with
the saved results. No model weights, API keys, GPUs, or prompt-text downloads
are needed. [checksums.json](checksums.json) covers the public bundle.

To rebuild the integration from its two source archives, run from the repository
root with a new destination:

```sh
python -m evals.leaderboard.extend_decision_ensembles --bundle /tmp/safeguard-combined-leaderboard
```

The script rejects changed source evidence, reordered populations, altered
validation selections, and altered prior results. The [integration procedure](PLAN.md)
records its scope. The underlying experiment has its own separately preserved
[registered protocol](../2026-10-30-decision-ensemble/PLAN.md).
