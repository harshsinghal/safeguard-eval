# Claim-to-evidence map

Use this map when drafting articles or a paper. The [full report](../../published_runs/2026-10-24-wildguard/README.md) is the source of rounded figures; JSON and compressed predictions preserve exact values.

| Candidate claim | Assessment | Evidence and qualification |
|---|---|---|
| Changing the written policy improved Shieldstral at a fixed threshold. | Supported in this deployment and benchmark. | `shieldstral-test-p0` versus `shieldstral-test-p4`: +2.884 points, paired 95% interval [2.001, 3.826]. All 1,699 rows; weights and inference settings fixed. |
| Changing the written policy improved PolicyLM at a fixed threshold. | Supported as an exploratory within-model result. | `policylm-test-p0` versus `policylm-test-p4`: +1.766 points [0.471, 3.119]. No adjustment for multiple exploratory comparisons. |
| Tuning improved all four models. | Not supported. | CoPE's selected-policy gain is small and uncertain; Safeguard's selected policy has a slightly lower test score. Keep both findings. |
| A tuned policy model definitively outperforms WildGuard. | Not established. | Preselected `shieldstral-test-p4` versus `wildguard-test-p0`: +0.471 points [−0.235, 1.236], 25 paired wins and 17 losses. |
| Policy tuning is better than fine-tuning. | Not tested as a general causal claim. | Different pretrained/fine-tuned models, no matched base-model or newly run weight-training control, unknown training exposure. The intervention is **no additional weight updates**. |
| Shieldstral's improvement is entirely a semantic-policy improvement. | Not supported. | Initial-policy threshold calibration reaches 90.112%; tuned policy reaches 90.818%. Residual difference +0.706 [−0.059, 1.530] is uncertain. |
| The validation-selected policy always ranks first on test. | False in this run. | PolicyLM shared p2 has 87.169% test accuracy; validation-selected p4 has 86.816%. Selection remains p4. |
| Tuned Shieldstral is a better adversarial-prompt detector than WildGuard. | Not supported by the reported slice. | Adversarial source rows: 87.437% versus 87.688%; the overall gain comes from the vanilla slice. These labels do not measure downstream attack success. |
| The dataset has been shown free of contamination. | Not established. | One exact and one lexical-near train/test match; neither appears in our optimizer samples. Semantic overlap and original model-training exposure are unverified. |
| The optimizer did not use official-test feedback to revise policies. | Supported by the recorded workflow. | Freeze/selection commit `e190b01` pushed before pinned test download; frozen policy hashes and source hashes verified in final runs. All later analyses leave policies unchanged. |
| Safeguard is intrinsically less reliable than the other models. | Not established. | This pinned MXFP4/vLLM deployment has repetitive-output failures. Root cause and cross-runtime reproducibility remain unresolved. |
| Near-perfect internal scores demonstrate new generalization for WildGuard. | False interpretation. | Internal fitting/validation/audit partitions come from its original training dataset. Only official test is the main cross-model evaluation. |
| These results establish performance on image generation moderation or production prompt-injection defense. | Not tested. | The study is prompt-harmfulness classification on WildGuardTest; earlier image-prompt and injection demonstrations are separate experiments. |

## Artifact pointers

- [Primary comparison and slices](../../published_runs/2026-10-24-wildguard/primary-comparison.json).
- [All model/policy comparisons, controls and sensitivities](../../published_runs/2026-10-24-wildguard/analysis.json).
- [All policy candidates and selection scores](../../published_runs/2026-10-24-wildguard/selection.json), [candidate ledger](../../published_runs/2026-10-24-wildguard/SEARCH.md), [policy registry](../../evals/wildguard/registry.json).
- [Frozen thresholds and full validation grid](../../published_runs/2026-10-24-wildguard/calibration.json).
- [Data overlap](../../published_runs/2026-10-24-wildguard/train-test-overlap.json), [optimizer-sample overlap](../../published_runs/2026-10-24-wildguard/optimizer-overlap.json), [known model exposure](MODEL_EXPOSURE.md).
- [Protocol and amendments](PLAN.md), [implemented methods](METHODS.md), [chronological decisions and failures](NOTES.md).

The official test is now observed. New policy revisions need a fresh confirmatory holdout; comparisons against this test after further tuning must be described as exploratory.
