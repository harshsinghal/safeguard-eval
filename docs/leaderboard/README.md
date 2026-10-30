# A leaderboard that shows both kinds of mistakes

New to these measures? Read the [metric guide](METRICS.md) for false blocks,
misses, balanced accuracy, macro-F1, MCC, uncertainty, and selection rules.

The current comparison brings together **policy models, general-purpose LLMs,
decision models, and their tested combinations**. It contains **38 WildGuard
entries and 20 HateXplain entries**, drawn from **261 eligible candidate records**.
These are configured systems, not 261 unique models or independent experiments.

Open the [interactive leaderboard](../../published_runs/2026-10-30-leaderboard-decision-ensembles/index.html)
in a browser. On GitHub, download the HTML file and open it locally; it works
offline. The [full tables](../../published_runs/2026-10-30-leaderboard-decision-ensembles/RESULTS.md)
and [CSV](../../published_runs/2026-10-30-leaderboard-decision-ensembles/leaderboard.csv)
are alternatives. The [integration record](../../published_runs/2026-10-30-leaderboard-decision-ensembles/README.md)
explains exactly what was added and verifies that earlier results are unchanged.

The newest addition is the [decision-score ensemble study](../decision-ensemble/README.md):
seven score-combination methods and two decision-only controls, tested with
Jev/Kev/Clef and with open-only Kev/Clef. These 18 new entries concern WildGuard
only. Individual calibration controls and “best method” selection aliases remain
in the study report rather than becoming duplicate leaderboard entries.

This integration used saved outputs and frozen selections. It made no API calls,
rented no GPUs, and fitted no models. The source studies did fit supervised
calibrators and combiners on labeled examples, with language-model weights fixed.
For future article and paper updates, see the
[writing handoff and claim ledger](WRITING-NOTES.md).

The useful change is that we now ask two questions together: how much violating
content does the system catch, and how much compliant content does it correctly
allow? **Balanced accuracy averages those two rates**, giving each class equal
weight. The leaderboard also shows macro-F1, MCC, ordinary accuracy, error counts,
uncertainty, and the exact policy and cutoff behind each entry.

## What “best” means here

We did not take the largest test score ever observed for each model. That would
reward choosing after seeing the answers.

Instead, we collected saved configurations with matching validation and full-test
outputs. For each individual model, we selected its configuration on the same
validation examples as its competitors. We did the same within each ensemble
method and component-model combination. Each source analysis froze its choices
before its test-scoring stage. The current integration preserves them, even though
those test results are now known. The scoring objective was balanced accuracy, with two separate
operating-target views described below.

The original leaderboard selected configurations from existing evidence; the
current integration adds the new study's selections without another policy search.
Eligible candidates include saved authored and transferred policies, native
decisions, cutoffs, and previously fitted calibrators or combiners. The ensemble
parameters were applied to the common validation examples without being retrained.
The original analysis verified 140 fitted-candidate test replays. The new
decision-ensemble study separately reproduced its fits and outputs. This
integration verifies every earlier result and every added method against its
source; it does not train or reselect the individual models.

The common validation sets contain **512 WildGuardTrain prompts** and **1,920
HateXplain posts**. Tests contain **1,699 WildGuardTest prompts** and **1,924
HateXplain posts**. The development data and test populations are distinct, but
we had already examined these public tests in earlier studies. This is a
retrospective, exploratory comparison.

## WildGuard: several configurations are close

The highest observed balanced score came from an equal average of the three
specialists' log-odds, with its cutoff selected on validation. The specialists are
PolicyLM, Shieldstral, and CoPE. Among individual models, CoPE had the highest
observed balanced accuracy. The largest dense Qwen model was close behind.

| Selected configuration | Balanced accuracy | Violations caught | Compliant prompts correctly allowed |
|---|---:|---:|---:|
| Equal log-odds average: three specialists | 91.08% | 87.67% | 94.50% |
| Log-odds logistic ensemble: three specialists | 91.00% | 88.46% | 93.54% |
| CoPE | 90.58% | 86.87% | 94.29% |
| Qwen3.5 27B | 90.16% | 84.35% | 95.98% |
| WildGuard 7B | 89.81% | 85.01% | 94.60% |
| Jev 1.14 | 88.69% | 82.36% | 95.03% |

These ranks are more precise than the evidence warrants if read as a permanent
ordering of models. The leading ensemble's advantage over CoPE was **0.50
percentage points**, with a paired 95% interval of **−0.07 to +1.11**. CoPE's
advantage over Qwen 27B was **0.41 points**, with an interval of **−0.55 to +1.43**.
Neither comparison resolves a clear difference.

The leading ensemble exceeded the released WildGuard model by **1.27 balanced
accuracy points**, with an unadjusted interval of **+0.33 to +2.21**. It missed
93 violations versus WildGuard's 113, while making 52 false blocks versus 51.
This is encouraging evidence for this configured system on this reused test. It
does not establish that ensembling generally beats fine-tuning.

The complete table also includes GPT-OSS Safeguard 20B, PolicyLM, Shieldstral,
all five Qwen sizes, Kev, Clef, and the tested ensemble families. Safeguard had
nine unresolved test outputs;
they remain errors rather than being removed. Its binary MCC is left unavailable
instead of calculating it only on successful responses.

## Decision-score ensembles: more information did not guarantee a gain

The newest study kept native BLOCK scores from Jev, Kev, and Clef and fitted
small combiners on 1,024 WildGuardTrain prompts. Validation chose the detailed
policy for Jev and Clef, and the brief policy for Kev. Policies with examples
lacked fitting scores, so they were excluded from this experiment's feature pool.
The earlier individual-model leaderboard entries retain their original pools.

| Configuration | Balanced accuracy | False blocks | Missed harmful prompts |
|---|---:|---:|---:|
| Jev: selected individual control | 88.69% | 47 | 133 |
| Jev + Kev + Clef: primary probability logistic ensemble | 89.32% | 69 | 106 |
| Jev + Kev + Clef: logistic combination of decisions only | 89.05% | 39 | 134 |
| Kev + Clef: primary probability logistic ensemble | 87.52% | 63 | 138 |
| Kev + Clef: validation-selected random forest | 88.10% | 102 | 98 |

The primary three-model ensemble caught 27 additional violations but made 22
additional false blocks compared with Jev. Its **+0.63-point** balanced-accuracy
difference had a paired 95% interval of **−0.43 to +1.58**. The score-based method
also did not establish a clear advantage over combining the decisions alone.

All nine method families remain visible for each cohort. Equal log-odds
averaging of the three models observed **89.74%** on test. It was not the
registered primary, nor the method selected as best on validation: that selection
was a weighted average, which reached **89.08%**. Ranking these frozen methods by
test outcome is descriptive; it does not justify declaring the highest test row
the preselected winner. The [source report](../decision-ensemble/README.md)
preserves the primary analysis, individual controls, and paired comparisons.

## HateXplain: Jev is competitive, and the mixed ensemble leads

The policy for this task blocks hate speech and allows offensive-but-not-hateful
and normal posts. It is not a policy to block all offensive language.

| Selected configuration | Balanced accuracy | Hate posts caught | Non-hate posts correctly allowed |
|---|---:|---:|---:|
| Log-odds logistic ensemble: specialists + Qwen | 79.35% | 79.29% | 79.40% |
| Random forest: specialists + Qwen | 78.65% | 82.49% | 74.81% |
| Jev 1.14 | 78.40% | 79.12% | 77.67% |
| Shieldstral 3B | 77.02% | 77.27% | 76.77% |
| Qwen3.5 4B | 76.21% | 75.42% | 76.99% |
| PolicyLM 1.7B | 63.69% | 47.98% | 79.40% |

Here the mixed ensemble contains PolicyLM, Shieldstral, and Qwen 4B. Its advantage
over Jev was **0.95 points**, with a paired interval of **−1.03 to +2.94**. The
ensemble's lead over Shieldstral was **2.33 points**, with an interval of **+0.94
to +3.79**. These are unadjusted descriptive comparisons, with the limitations of
reused tests and unequal development histories.

The table does not support a claim that a specialist always beats a larger
general-purpose model. PolicyLM was substantially weaker on this task. Different
tasks and configured systems produced different outcomes.

## Why some numbers changed from our earlier reports

Earlier work often selected policies and cutoffs for ordinary accuracy. This
analysis selects them for balanced accuracy on a common validation population.
The resulting configuration can therefore differ. Original findings remain in
their archives; the leaderboard does not replace them with whichever test score
looks better now.

For Jev on HateXplain, validation now selected the **detailed policy without the
four examples**, with a **0.75** BLOCK cutoff. The earlier accuracy-oriented
procedure selected the policy with examples and a 0.90 cutoff. The new choice
caught **79.12%** of hateful posts, compared with **59.93%** for the earlier
configuration. False blocks increased from **134 to 297**. Ordinary accuracy fell
from **80.67% to 78.12%**, while balanced accuracy rose from **74.93% to 78.40%**.

That is a different operational trade-off, not a contradiction. Someone deciding
which metric to optimize is also deciding which mistakes the workflow tolerates.

Selection can also disappoint. On WildGuard, the newly selected Jev detailed
policy/cutoff achieved 88.69% balanced accuracy, below the 89.88% of the earlier
example-bearing policy's native decision. We retain that result. We cannot swap
back after looking at test performance and describe the replacement as a
validation-selected success.

## Operating requirements tell a different story

The two additional views ask practical questions. Each has its own configuration
selected on validation; the headline balanced configuration is not reused blindly.

- **False-block limit:** catch as many violations as possible while falsely
  blocking at most 5% of compliant validation examples. Unresolved compliant
  responses also consume that allowance.
- **Catch target:** minimize false blocks while catching at least 90% of
  validation violations.

These are illustrative requirements, not universal recommendations. Whether they
hold on test is reported separately.

| Benchmark | 5% false-block limit met on test | 90% catch target met on test |
|---|---:|---:|
| WildGuard | 2 of 35 eligible entries | 0 of 37 eligible entries |
| HateXplain | 17 of 20 entries | 2 of 20 entries |

WildGuard has three validation gaps for the 5% limit: Safeguard and the two
fixed majority-vote controls. The three-model majority vote also has no feasible
90% catch configuration. These are visible gaps; we do not substitute test-chosen
cutoffs or invent continuous scores for fixed votes.

The two WildGuard entries meeting the 5% limit on test were logistic combinations
of decisions only. The Jev/Kev/Clef combination caught **82.23%** of violations
with **4.13%** false blocks; the Kev/Clef combination caught **72.28%** with
**4.55%** false blocks. Neither primary score ensemble met either operating target.
The more complex score input was not automatically the more useful operational
choice.

On HateXplain, the strongest observed catch rate among entries meeting the 5%
test limit was **43.10%**, from the mixed log-odds logistic ensemble. Conversely,
the two entries meeting the 90% catch target falsely blocked roughly **42–43%**
of compliant posts. These are expensive trade-offs for an operational workflow.

WildGuard's results are a warning about development-to-test transfer. The common
validation sample comes from WildGuardTrain, whose labels are model-generated;
the official test uses human annotations and a different example mixture.
WildGuard itself also trained on WildGuardTrain. Validation is therefore not an
independent measure of its generalization. Most selected operating targets
failed on test, but these results do not isolate a single cause. Other
configurations may meet a target; we report the configuration chosen by the
validation procedure.

## What practitioners should take away

Treat a leaderboard entry as a versioned system: policy, interpreter, adapter,
cutoff, and any calibration or ensemble layer. State the acceptable false-block
and missed-violation rates before selecting it. Check both error rates on
representative data, alongside category slices and unresolved responses.

This evidence supports trying policy authoring and lightweight score combination
without updating language-model weights. It does not show that these steps are
always sufficient, eliminate labeled-data work, or outperform a controlled,
equally resourced fine-tuning process. Historical model training exposure is not
fully known. Cost, latency, and engineering effort were not measured on a matched
basis across these deployments.

## Evidence and progress

The [original reanalysis plan](PLAN.md) and its
[original evidence bundle](../../published_runs/2026-10-29-leaderboard/README.md)
remain unchanged. The [Kev/Clef extension](../../published_runs/2026-10-29-leaderboard-decision-models/README.md)
added two individual models. The [current integration](../../published_runs/2026-10-30-leaderboard-decision-ensembles/README.md)
adds decision-model combinations and includes frozen selections, input hashes,
normalized prompt-free outputs, all paired comparisons, and a CPU-only
reproduction command. Dates and hashes remain in the archives for provenance;
study titles describe the questions tested.

The four frontier API models remain visible in the coverage table, but unranked:
they were evaluated only on 32 fitting examples per reasoning condition, not the
full tests. CoPE, Safeguard, WildGuard, and the other Qwen sizes have no HateXplain
test results. Referenced models with no actual scored run do not receive a rank.

Metric definitions: scikit-learn's
[balanced accuracy](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html),
[macro-F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html), and
[MCC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.matthews_corrcoef.html).
