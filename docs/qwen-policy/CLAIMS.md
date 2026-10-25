# Claims supported by the Qwen comparison

All claims concern the recorded deployments on WildGuardTest. Intervals are exploratory, unadjusted and conditional on selected prompts. This is an evidence map for future writing, not a claim of causal model-training effects.

| Claim | Evidence | Boundary |
|---|---|---|
| The two smallest specialists outperform nearby Qwen models here. | Selected Qwen minus specialist: 2B/PolicyLM −3.77 pp, interval [−5.59, −1.94]; 4B/Shieldstral −3.24 pp, [−4.59, −1.88]. Available calibrated comparisons also favor specialists. | Approximate parameter matches and different native interfaces; no isolated specialization effect. |
| Qwen 27B exceeds the recorded Safeguard deployment. | +1.65 pp, interval [+0.41, +2.94]; calibrated Qwen comparison also has a positive interval. | Safeguard used medium reasoning/MXFP4 and had historical output/repeatability issues; no universal model ranking. |
| Qwen 27B does not establish superiority over CoPE or WildGuard. | Versus CoPE +0.53 pp [−0.53, +1.59]; versus WildGuard +0.94 pp [−0.29, +2.30]. | Intervals crossing zero do not prove equivalence. |
| Prompt selection improves some Qwen deployments. | Initial-to-selected gains: 2B +3.12 pp, 4B +1.94, 9B +0.53, 27B +1.88, 35B-A3B 0.00. Intervals exclude zero for 2B/4B/27B. | Most selected texts were inherited; limited adaptive search, prior benchmark knowledge and conditional intervals. |
| The new tailored drafts usually did not improve validation accuracy. | Only 9B p3 strictly exceeds its best inherited candidate; 35B p4 ties p1 and wins on length. All 25 model/candidate records retained. | This is one prompt search, not evidence that more careful optimization cannot help. |
| Part of the 2B tuning gain can be reproduced by changing the initial cutoff. | Calibrated initial 82.93%, selected free labels 83.05%; paired residual +0.12 pp [−1.06, +1.12]. | Secondary paired contrasts added during final inference; controls do not prove semantic understanding absent or present. |
| The 4B selected wording still adds value beyond its calibrated initial prompt. | 87.58% versus 85.46%; secondary paired residual +2.12 pp [+1.12, +3.12]. | Same post-hoc contrast qualification; no inference or selection was altered. |
| Output formatting was reliable in the new runs. | All 83 runs / 70,634 outputs parse successfully; strict parser, no retries or label repair. | Valid output is not a correct classification. |
| The study met the cost constraint and released compute. | Provider bill $2.04, cumulative $7.91, terminated instance and deleted temporary SSH key. | GPU charges exclude assistant effort and local processing. |

Sources: [analysis](../../published_runs/2026-10-25-qwen/analysis.json), [all tables](../../published_runs/2026-10-25-qwen/DETAILS.md), [selection](../../published_runs/2026-10-25-qwen/selection.json), [verification](../../published_runs/2026-10-25-qwen/verification.json), [billing](../../published_runs/2026-10-25-qwen/billing.json), [methods](METHODS.md), and [notebook](NOTES.md).

Potential articles can separate three findings: nearby-size specialists versus instruction models; why more detailed prompts often failed; and why changing a rule and changing a decision cutoff can produce similar headline gains. A research report should retain all seven pairings and all three prompt-comparison roles, describe the previously observed benchmark, and separate primary results from secondary analysis.

Future work, not completed here: fresh policies and held-out categories; policy changes that reverse labels for identical inputs; direct parent instruction checkpoints to isolate specialization more closely; controlled thinking/quantization/runtime ablations; repeated independent prompt searches; human adjudication of ambiguous labels; and downstream moderation outcomes. This experiment does not establish that policy models are generally unnecessary, nor that general-purpose models cannot perform policy classification.
