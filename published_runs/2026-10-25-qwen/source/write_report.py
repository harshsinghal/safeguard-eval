import json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]/'safeguard-eval';pub=repo/'published_runs/2026-10-25-qwen';a=json.loads((pub/'analysis.json').read_text());s=json.loads((pub/'selection.json').read_text());entries={(e['split'],e['model'],role):e for e in a['entries'] for role in e['roles']};models=list(s['selected'])
rows=[]
for m in models:
 q=entries[('test',m,'selected')]['metrics'];initial=entries[('test',m,'initial')]['metrics'];rows.append(f"| {m.split('/')[-1]} | {100*initial['accuracy']:.2f}% | {100*q['accuracy']:.2f}% | {100*q['harmful_f1']:.2f}% |")
table='| General-purpose model | Initial accuracy | Selected-prompt accuracy | Selected harmful F1 |\n|---|---:|---:|---:|\n'+'\n'.join(rows)+'\n'
blog='''# Can a general-purpose model do the job of a policy model?

We ran the comparison. General-purpose Qwen models can classify requests using a written moderation policy, but the results give us a reason to keep specialized models in the picture. At the two smallest sizes, the specialists won. The larger Qwen configurations produced scores around 90–91%, close to several specialists.

That makes this a useful experiment even though it does not deliver a dramatic new leaderboard winner. We now have evidence about where a general-purpose model works, where it struggles, and how much changing the instructions actually helps.

We used five Qwen3.5 checkpoints: 2B, 4B, 9B, 27B and 35B-A3B. Each received the policy as a system instruction and one request to classify. Its job was to return ALLOW or BLOCK. The model weights stayed fixed throughout.

Here are the results on **all 1,699 labeled WildGuardTest prompts**:

'''+table+'''
Accuracy means agreement with the dataset's label. Harmful F1 balances catching harmful requests with avoiding incorrect harmful labels. Every configuration saw the same test examples. All Qwen outputs were valid classifications, so these differences come from decisions rather than refusals or broken formatting.

The nearby-size comparisons tell the main story. Qwen 2B's **83.05%** trails PolicyLM-1.7B's **86.82%**. Qwen 4B's **87.58%** trails Shieldstral 3B's **90.82%**. Those gaps remain below zero in our paired uncertainty intervals, including after the available threshold controls. The smaller specialized models were more accurate in these deployments.

Qwen 9B reaches **89.58%**, compared with WildGuard 7B's **90.35%**. That difference is small enough that our interval includes no difference. Qwen 27B has the best Qwen score, **91.29%**: nine more correct answers than CoPE at **90.76%**, and 28 more than Safeguard at **89.64%**. Its advantage over CoPE remains uncertain; its advantage over this recorded Safeguard deployment has a positive interval. Qwen 35B-A3B scores **90.29%**, with uncertain differences from both CoPE and Safeguard. These are exploratory, unadjusted comparisons, not a claim of universal superiority.

![Paired comparison of Qwen and nearby-size specialist models](../../published_runs/2026-10-25-qwen/figures/qwen-comparison.png)

What does “selected prompt” mean? We tried five candidate instruction sets for each model and chose the one with the highest **validation accuracy**. We made that choice before running the new Qwen test evaluations. It means “best on the selection set under our rule,” not “best possible prompt” or “the prompt that looked best on the final test.”

The workflow had three stages:

1. **Use 1,024 fitting examples to understand mistakes.** We evaluated three existing rule sets, inspected fitting errors, and drafted two additional candidates per model.
2. **Use 512 separate validation examples to choose among the five candidates.** We looked at aggregate scores, without using individual validation mistakes to rewrite the prompts. Ties favored shorter text.
3. **Freeze the choices and run the test.** We evaluated the initial prompt, the common checklist, and the selected prompt on the full official test and a separate 512-example internal audit. Identical configurations were run once.

We tuned the language of the policy. Some edits clarified benign cases: imaginary conflict, ordinary discussion and vague wording should not automatically trigger a block. Others made harmful outcomes more explicit, such as sensitive health information or requests to endorse a harmful belief. We also tried shorter formulations. Some candidates therefore changed the stated scope of a rule, as well as its wording. This was an attempt to better match the benchmark's labeling conventions, not just a formatting exercise.

A policy document and a system prompt both communicate instructions. In this experiment, we placed the substantive policy rules into Qwen's system message. The meaningful difference was the model interpreting those rules and its native interface. The [prompt-change ledger](PROMPT-CHANGES.md) links every exact version and explains why it was written.

More writing did not reliably help. Only the 9B tailored candidate strictly beat that model's best inherited prompt on validation, by just **two examples out of 512**. The 35B model's new prompt tied an earlier one and won because it was shorter. The other three models selected existing prompts. Every unsuccessful draft is retained.

On the final test, selection improved 2B by **3.12 percentage points**, 4B by **1.94**, 9B by **0.53**, and 27B by **1.88**. The 35B model's accuracy did not change. The 9B improvement remains uncertain in the paired interval. “Tuning helped” is therefore a model-specific observation, not a guarantee.

There is another useful wrinkle. We also froze a separate control that kept the words unchanged and adjusted only the score cutoff for BLOCK. For 2B, that brought the initial prompt from **79.93% to 82.93%**, almost the selected prompt's **83.05%**. Much of the apparent prompt-tuning gain can therefore be reproduced by changing how readily it blocks. For 4B, the selected wording still beat the calibrated initial prompt by about **2.12 points**. The detailed paired contrasts for this question were added during final inference and are labeled secondary; none changed the frozen prompts, cutoffs or primary results.

The test task here was **general prompt harmfulness**: should an assistant treat the request as harmful or unharmful? We did not evaluate the assistant's answer, an image, or the original religious-iconography policy. Fitting and test examples cover the same broad categories, such as privacy, abuse, violence and deception. This measures performance on different requests within that setting; categories themselves were not held out. Training-source labels are model-generated, while official-test labels are human annotations, which also helps explain why validation and test scores can differ.

This study supports general-purpose models as useful baselines for policy classification. It also shows that a small specialist can be a strong choice on this task. It does not settle whether policy models are generally necessary: size matches are approximate, architectures and training data differ, Qwen ran without thinking, and the historical Safeguard run used a different reasoning/quantization setup. We already knew the earlier specialist test results, and the models' original exposure to WildGuard is not fully known.

A stronger next experiment would test newly written platform rules, including changes that reverse the correct decision for the same request. That would directly probe whether a model follows the supplied policy rather than relying on a familiar harmfulness judgment. It remains future work.

All five Qwen checkpoints ran on GPU.ai. The 83 runs produced **70,634 classification outputs** across repeated evaluations, cost **$2.04**, and brought cumulative GPU spend to **$7.91**. The GPU is terminated. Exact prompts, scores, revisions, costs and unsuccessful candidates are documented; source dataset text and raw traces remain private.

For a deeper look, start with the [complete results](../../published_runs/2026-10-25-qwen/README.md), then the [methods](METHODS.md), [lab notebook](NOTES.md), and [CPU-only reproduction guide](../../published_runs/2026-10-25-qwen/REPRODUCING.md).
'''
(repo/'docs/qwen-policy/READOUT.md').write_text(blog)
pairs=[]
names={'policylm':'PolicyLM-1.7B','shieldstral':'Shieldstral-3B','wildguard':'WildGuard-7B','cope':'CoPE-B-A4B','safeguard':'Safeguard-20B'}
for p in a['paired_comparisons']:
 if p['role']!='selected':continue
 d=p['qwen_minus_policy'];pairs.append(f"| {p['model'].split('/')[-1]} | {names[p['comparator']]} | {100*p['qwen_metrics']['accuracy']:.2f}% | {100*p['policy_model_metrics']['accuracy']:.2f}% | {100*d['delta']:+.2f} | [{100*d['ci95'][0]:+.2f}, {100*d['ci95'][1]:+.2f}] |")
report='''# Qwen instruction models versus policy specialists

**The smallest specialists outperform their nearby-size Qwen comparators. Larger Qwen configurations are competitive on headline accuracy, with most nearby-size differences uncertain.** Qwen 27B's selected prompt is 1.65 percentage points above the recorded Safeguard deployment, with an exploratory paired interval of +0.41 to +2.94 points. Its +0.53-point difference from CoPE has an interval of −0.53 to +1.59.

Start with the [plain-language readout](../../docs/qwen-policy/READOUT.md). This report and [complete tables](DETAILS.md) retain every registered comparison, including p0-versus-p0, shared-p2-versus-shared-p2, separately selected prompts, failed candidates, calibration controls, audit results and slices.

Five Qwen3.5 checkpoints were run on GPU.ai with fixed weights, BF16 and explicit non-thinking mode. Each classified the same 1,699 labeled official-test requests used in the earlier study. Four custom-policy models and the fixed WildGuard baseline retain their original archived predictions and deployments. No historical evidence was changed.

'''+table+'''
| Qwen | Specialist | Qwen accuracy | Specialist accuracy | Difference (pp) | Paired 95% interval (pp) |
|---|---|---:|---:|---:|---:|
'''+ '\n'.join(pairs)+'''

![Qwen versus nearby-size specialists](figures/qwen-comparison.png)

The 2B/4B Qwen deficits persist under the available validation-selected threshold controls. WildGuard and Safeguard retain their historical explicit labels where no comparable score control exists. Qwen 27B's calibrated selected score is 91.17%, versus CoPE's calibrated 90.94%; this difference remains uncertain. Full controls are in [DETAILS.md](DETAILS.md) and [analysis.json](analysis.json).

## Prompt tuning and selection

Each model had five candidates: three inherited shared texts and two fitting-error-derived drafts. Selection used 512 validation rows after inspection of 1,024 fitting rows; prompts and cutoffs were frozen before new Qwen test/audit inference. Categories were not held out. The selected policies are p2 for 2B, p1 for 4B/27B, a tailored p3 for 9B, and a tailored p4 for 35B-A3B. The latter won a shorter-text tie-break, not an accuracy improvement. Only one tailored draft strictly improved on the best inherited validation accuracy.

Test gains over the initial prompt are +3.12, +1.94, +0.53, +1.88 and 0.00 percentage points for 2B, 4B, 9B, 27B and 35B-A3B respectively. The paired intervals exclude zero for 2B, 4B and 27B, but are exploratory and conditional on selection. For 2B, calibrating the initial prompt alone reaches 82.93%, almost the selected prompt's 83.05%. The secondary paired prompt-versus-cutoff contrasts were added during final inference and are explicitly documented; primary outcomes and all selections stayed frozen.

The [candidate ledger](../../docs/qwen-policy/PROMPT-CHANGES.md), [selection record](selection.json), [freeze](freeze.json) and [notebook](../../docs/qwen-policy/NOTES.md) retain exact changes and failed edits. Policy wording, explicit scope boundaries and benign exceptions were tuned; weights and the Qwen output wrapper were fixed.

## Scope and limits

All 1,699 labeled official-test rows are included: 945 ALLOW, 754 BLOCK; 903 vanilla and 796 adversarial. The task is prompt harmfulness, with no REVIEW class or assistant-response scoring. Twenty-six null-label test rows are excluded. The same broad taxonomy appears in fitting and test data. The 512-row internal audit is separate from fitting/validation and uses training-source labels. All 83 runs have complete populations and zero output errors.

Parameter matching is approximate. Qwen's full checkpoints also contain vision-related weights, although only text is evaluated. CoPE has 25.2B total/3.8B active parameters; Safeguard about 20.9B total/3.6B active. Each is compared with dense Qwen 27B for total size and Qwen 35B-A3B for approximate active size. The two large Qwen results are reused across these comparisons. This is neither a compute-matched comparison nor an isolated test of specialized training.

Previous WildGuardTest results were known, and original model-training exposure is unverified. This follow-up is exploratory. All intervals use 2,000 paired group-bootstrap replicates, are unadjusted for multiple comparisons, and exclude runtime and annotation uncertainty. Historical Safeguard used medium reasoning/MXFP4; Qwen uses non-thinking/BF16. No controlled speed ranking is claimed. The repeated-input diagnostic found 1/256 changed labels for 2B, 4/256 for 35B-A3B, and none for the other sizes under different batch contexts.

## Evidence, cost and reproduction

The study completed **83 runs and 70,634 classification outputs**, including repeated evaluations of the same examples. GPU.ai charged **$2.04** for 3,690 GPU seconds; cumulative spend is **$7.91**. Instance `gpu-e4319df3` is terminated and its temporary provider/local SSH key was removed. Full raw traces are retained in a private validated archive; public predictions exclude source prompts and generated text.

- [Protocol](../../docs/qwen-policy/PLAN.md), [methods](../../docs/qwen-policy/METHODS.md), [writing and claims map](../../docs/qwen-policy/CLAIMS.md).
- [Run index](run-index.json), [population verification](verification.json), [analysis](analysis.json), [score reproduction](reproduction.json).
- [Reproduction guide](REPRODUCING.md), [source snapshot](source/), [runtime](runtime/), [checksums](SHA256SUMS).
- [Study history](study-history.json), [billing](billing.json), [termination](final-instance.json), [private archive checksum](private-archive.json).

The source dataset is [AllenAI WildGuardMix](https://huggingface.co/datasets/allenai/wildguardmix), revision `d29c47f41c8b51348b5c8e8c81c039b3132b66d1`; upstream access conditions and ODC-BY attribution apply. Qwen model revisions and complete checkpoint parameter counts are recorded in [model-revisions.json](model-revisions.json). The [prior specialist study](../2026-10-24-wildguard/README.md) remains unchanged.
'''
(pub/'README.md').write_text(report)
for p in (root/'figure-reviewed').iterdir():shutil.copyfile(p,pub/'figures'/p.name)
shutil.copyfile(repo/'evals/qwen_policy/plot.py',pub/'source/evals/qwen_policy/plot.py')
p=repo/'README.md';text=p.read_text();old='Compare how policy models apply written rules to text. The repository contains a controlled WildGuard policy-tuning study, earlier image-prompt and prompt-injection demonstrations, and the original GPT-OSS Safeguard 20B interactive demo powered by Groq.'
new='Compare how specialized policy models and general-purpose instruction models apply written rules to text. The repository includes WildGuard policy-tuning and nearby-size Qwen comparisons, earlier image-prompt and prompt-injection demonstrations, and the original GPT-OSS Safeguard 20B demo powered by Groq.'
assert old in text;text=text.replace(old,new);marker='## WildGuard: tuning policies with frozen model weights'
section='''## General-purpose Qwen versus policy models

We tested five Qwen3.5 checkpoints using the policy as a system instruction, with five prompt candidates per model and validation selection before new test inference. On all **1,699 labeled WildGuardTest prompts**, selected-prompt accuracy was **83.05% (2B), 87.58% (4B), 89.58% (9B), 91.29% (27B), and 90.29% (35B-A3B)**. Weights stayed fixed.

**The smallest specialists won their nearby-size comparisons.** PolicyLM-1.7B scored 86.82% and Shieldstral-3B scored 90.82%. Larger Qwen results were competitive, with most nearby-size gaps uncertain. Qwen 27B exceeded the recorded Safeguard deployment, while its advantage over CoPE remained uncertain. This exploratory comparison does not isolate the effect of specialized training.

The new study completed **83 runs for $2.04**, bringing cumulative GPU spend to **$7.91**. The GPU is terminated. Read the [plain-language explanation](docs/qwen-policy/READOUT.md), [full results and figure](published_runs/2026-10-25-qwen/README.md), [exact prompt changes](docs/qwen-policy/PROMPT-CHANGES.md), and [reproduction guide](published_runs/2026-10-25-qwen/REPRODUCING.md).

'''
assert marker in text;text=text.replace(marker,section+marker);text=text.replace('bringing cumulative experiment spend to **$5.87**.','bringing cumulative experiment spend at that stage to **$5.87**.');p.write_text(text)
p=repo/'evals/qwen_policy/README.md';text=p.read_text().replace('Results are pending.','Results are complete: see the [plain-language readout](../../docs/qwen-policy/READOUT.md) and [reproducible evidence](../../published_runs/2026-10-25-qwen/README.md).');p.write_text(text)
print('Wrote readout and result reports')
