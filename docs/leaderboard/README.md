# A leaderboard that shows both kinds of mistakes

**Latest extension:** [Kev and Clef have now been tested](../decision-models/README.md).
The [expanded interactive leaderboard](../../published_runs/2026-10-29-leaderboard-decision-models/index.html)
has 20 entries per benchmark and preserves every earlier selection and score.
The remainder of this page describes the original 18-entry reanalysis.

For future article and paper updates, see the
[writing handoff and claim ledger](WRITING-NOTES.md). The frozen evidence below
remains the source of the numbers.

**The comprehensive comparison is complete.** It covers 197 eligible archived
configurations and produces 18 entries for each benchmark: individual models,
ensemble methods, and Jev. All calculations used saved outputs. There were no new
API calls, GPU rentals, language-model weight updates, or combiner fits.

The 197 count describes archived candidate records, not independent experiments
or different models. Some individual calibrators are shared across ensemble
cohorts. The full inventory preserves that provenance.

Open the [interactive leaderboard](../../published_runs/2026-10-29-leaderboard/index.html)
in a browser. On GitHub, download the HTML file and open it locally; the file works
offline. The [full tables](../../published_runs/2026-10-29-leaderboard/RESULTS.md)
and [CSV](../../published_runs/2026-10-29-leaderboard/leaderboard.csv) are alternatives.

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
method and component-model combination. We then froze these choices and scored
the official tests. The scoring objective was balanced accuracy, with two separate
operating-target views described below.

This was a new selection from existing evidence, not a new policy-writing search.
Eligible candidates include saved authored and transferred policies, native
decisions, cutoffs, and previously fitted calibrators or combiners. The ensemble
parameters were applied to the common validation examples without being retrained.
All 140 calibration and ensemble test replays matched their archived scores and decisions.

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

The complete table includes GPT-OSS Safeguard 20B, PolicyLM, Shieldstral, all five
Qwen sizes, and every ensemble family. Safeguard had nine unresolved test outputs;
they remain errors rather than being removed. Its binary MCC is left unavailable
instead of calculating it only on successful responses.

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
| WildGuard | 0 of 17 eligible entries | 0 of 18 entries |
| HateXplain | 16 of 18 entries | 2 of 18 entries |

Safeguard had no saved validation configuration satisfying the 5% limit, so it
has a visible gap in that view. We did not substitute a test-selected cutoff.

On HateXplain, the strongest observed catch rate among entries meeting the 5%
test limit was **43.10%**, from the mixed log-odds logistic ensemble. Conversely,
the two entries meeting the 90% catch target falsely blocked roughly **42–43%**
of compliant posts. These are expensive trade-offs for an operational workflow.

WildGuard's results are a warning about development-to-test transfer. The common
validation sample comes from WildGuardTrain, whose labels are model-generated;
the official test uses human annotations and a different example mixture.
WildGuard itself also trained on WildGuardTrain. Validation is therefore not an
independent measure of its generalization. Our results demonstrate failure of the
selected operating targets on this test; they do not isolate a single cause.
They also do not mean no other configuration could meet a target—the decision
procedure selected one configuration before testing, and that choice is what we
report.

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

The [plan](PLAN.md) is preserved as it stood at the selection freeze. Completion
and verification are recorded in
[progress.json](../../published_runs/2026-10-29-leaderboard/progress.json).
The [evidence bundle](../../published_runs/2026-10-29-leaderboard/README.md) provides
the frozen selection, input hashes, normalized prompt-free outputs, paired
comparisons, and a CPU-only reproduction command.

The four frontier API models remain visible in the coverage table, but unranked:
they were evaluated only on 32 fitting examples per reasoning condition, not the
full tests. CoPE, Safeguard, WildGuard, and the other Qwen sizes have no HateXplain
test results. Referenced models with no actual scored run do not receive a rank.

Metric definitions: scikit-learn's
[balanced accuracy](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html),
[macro-F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html), and
[MCC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.matthews_corrcoef.html).
