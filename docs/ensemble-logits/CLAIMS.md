# What the combined studies support

The intended audience is a policy, trust-and-safety or GRC team working with engineers to adapt a released model. The relevant question is whether that team can obtain useful task performance without operating a language-model fine-tuning pipeline.

## Central message

**Policy authoring, evaluation and lightweight calibration can be a practical route to adapting released models without additional language-model weight updates. Ensembles can sometimes improve that route, but must earn their place through measured error trade-offs.**

“Without additional language-model fine-tuning by the deploying team” is accurate. “Only a policy document is needed” is not: the process also uses labeled examples, model-specific adapters, calibration, tests and, for the ensemble, supervised learning of a small combiner.

| Proposed statement | Evidence and appropriate scope |
|---|---|
| Written policy can change outcomes with frozen model weights. | In the original WildGuard study, selected Shieldstral policy accuracy rose from 87.93% to 90.82% at a fixed threshold. Calibrating the initial policy reached 90.11%, so not all the apparent gain should be attributed to wording. PolicyLM also showed a policy effect. See the [original results](../../published_runs/2026-10-24-wildguard/README.md). |
| The model and policy must be evaluated together. | The [transfer study](../policy-transfer/READOUT.md) and [HateXplain structure study](../hatexplain/READOUT.md) recorded asymmetric transfer and differing effects of the same component changes. These do not establish a universal policy format. |
| Threshold calibration is a substantive part of implementation. | In the [first ensemble study](../ensemble/READOUT.md), Shieldstral's HateXplain accuracy rose from 53.17% to 79.57% through calibration/threshold selection, while missed hateful posts increased. This is not a policy-editing gain. |
| A frozen-policy-model workflow can be competitive with a released task-specific model. | The new log-odds WildGuard ensemble achieved 91.29% versus the released WildGuard model's 90.35%. No language-model weights were updated in our adaptation process. The comparison is exploratory and does not measure the best achievable fine-tuned baseline. |
| Combining complementary scores can improve some configurations. | Log-odds logistic improved over probability-feature logistic in all three cohorts. The mixed HateXplain ensemble reached 80.82%, above the strongest observed individual at 79.57%. The specialist-only HateXplain ensemble remained below that individual. |
| Logits explain all earlier ensemble failures. | Unsupported. We tested reconstructed log-odds, not full original logits. Representation helped these linear combiners, but did not make specialist-only ensembling consistently superior. |
| Policy models are always easier, cheaper or better than fine-tuning. | Not measured. No matched fine-tuning baseline, equal end-to-end development budget, human-effort study or production serving-cost comparison was performed. Running multiple models adds inference work. |
| Fine-tuning is unnecessary, or no supervised learning is involved. | Unsupported. Creators trained the policy models; the deploying team trained calibrators/combiners and used labeled data to select policies and thresholds. |

## Wording for a research abstract or executive summary

> We study adaptation of released policy models without additional language-model weight updates. Policy authoring, validation-based calibration and lightweight score combination produced task performance competitive with a released specialist classifier on WildGuardTest. Results varied across benchmarks: a mixed specialist/general-purpose ensemble improved HateXplain accuracy, while a specialist-only ensemble did not exceed its strongest individual. These exploratory findings motivate evaluating policy text, model interface and decision logic as one versioned system.

Do not claim statistical equivalence merely because accuracies are close. No equivalence/non-inferiority margin or independent confirmatory test was registered. Report the actual differences and descriptive intervals instead. On WildGuard, +0.94 percentage points versus the external model has an unadjusted interval of +0.06 to +1.77; the tests were reused, so this is not proof of general superiority.

## Evidence boundaries to retain in future writing

The new representation comparison holds policy text fixed. Policy effects come from the earlier policy-editing and transfer experiments, not from the log-odds result itself. Model architectures, training histories and exposures differ. PolicyLM's documented training sources include a dataset containing WildGuardMix; exact split overlap is unverified, as recorded in [model exposure notes](../wildguard/MODEL_EXPOSURE.md). The task-specific WildGuard comparator is the released checkpoint, not a newly optimized baseline under an equal budget.

All official tests in this extension were observed previously. Every new setting was selected on training/validation, but that alone does not remove the broader adaptive reuse. The correct characterization is an exploratory demonstration of a workflow and its measured trade-offs. The measurements concern binary classification on these datasets, not production governance, multilingual reliability or human-review routing.
