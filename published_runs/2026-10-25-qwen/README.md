# Qwen instruction models versus policy specialists

**The smallest specialists outperform their nearby-size Qwen comparators. Larger Qwen configurations are competitive on headline accuracy, with most nearby-size differences uncertain.** Qwen 27B's selected prompt is 1.65 percentage points above the recorded Safeguard deployment, with an exploratory paired interval of +0.41 to +2.94 points. Its +0.53-point difference from CoPE has an interval of −0.53 to +1.59.

Start with the [plain-language readout](../../docs/qwen-policy/READOUT.md). This report and [complete tables](DETAILS.md) retain every registered comparison, including p0-versus-p0, shared-p2-versus-shared-p2, separately selected prompts, failed candidates, calibration controls, audit results and slices.

Five Qwen3.5 checkpoints were run on GPU.ai with fixed weights, BF16 and explicit non-thinking mode. Each classified the same 1,699 labeled official-test requests used in the earlier study. Four custom-policy models and the fixed WildGuard baseline retain their original archived predictions and deployments. No historical evidence was changed.

| General-purpose model | Initial accuracy | Selected-prompt accuracy | Selected harmful F1 |
|---|---:|---:|---:|
| Qwen3.5-2B | 79.93% | 83.05% | 81.49% |
| Qwen3.5-4B | 85.64% | 87.58% | 85.87% |
| Qwen3.5-9B | 89.05% | 89.58% | 88.11% |
| Qwen3.5-27B | 89.41% | 91.29% | 90.24% |
| Qwen3.5-35B-A3B | 90.29% | 90.29% | 89.07% |

| Qwen | Specialist | Qwen accuracy | Specialist accuracy | Difference (pp) | Paired 95% interval (pp) |
|---|---|---:|---:|---:|---:|
| Qwen3.5-2B | PolicyLM-1.7B | 83.05% | 86.82% | -3.77 | [-5.59, -1.94] |
| Qwen3.5-4B | Shieldstral-3B | 87.58% | 90.82% | -3.24 | [-4.59, -1.88] |
| Qwen3.5-9B | WildGuard-7B | 89.58% | 90.35% | -0.77 | [-2.18, +0.59] |
| Qwen3.5-27B | CoPE-B-A4B | 91.29% | 90.76% | +0.53 | [-0.53, +1.59] |
| Qwen3.5-27B | Safeguard-20B | 91.29% | 89.64% | +1.65 | [+0.41, +2.94] |
| Qwen3.5-35B-A3B | CoPE-B-A4B | 90.29% | 90.76% | -0.47 | [-1.71, +0.71] |
| Qwen3.5-35B-A3B | Safeguard-20B | 90.29% | 89.64% | +0.65 | [-0.77, +2.06] |

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
