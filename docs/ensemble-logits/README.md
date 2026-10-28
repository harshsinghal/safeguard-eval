# Log-odds ensemble follow-up

The log-odds logistic ensemble scored **91.29% on WildGuardTest**, **78.79% with HateXplain specialists**, and **80.82% with HateXplain specialists plus Qwen**. Each improved on the preceding probability-feature logistic ensemble. The specialist-only HateXplain result remained below calibrated Shieldstral's 79.57%.

Start with the [plain-language readout](READOUT.md). The [complete results](RESULTS.md) retain every new configuration, individual controls, error counts, paired intervals and learned equations. The [claim-to-evidence guide](CLAIMS.md) explains what this contributes to the case for adaptation without additional language-model fine-tuning.

The [plan](PLAN.md) remains unchanged after registration. [Notes](NOTES.md), [progress](progress.json) and the [evidence package](../../published_runs/2026-10-28-ensemble-logits/README.md) record execution and reproduction.

- [x] Register the bounded representation comparison and preserve the prior study.
- [x] Verify prior checksums and reuse the exact development splits.
- [x] Implement and test log-odds transformation and matching individual controls.
- [x] Freeze all three cohorts before this extension's official-test evaluation.
- [x] Evaluate all registered configurations and paired uncertainty.
- [x] Document positive results, negative results and error trade-offs.
- [x] Reproduce the new configurations and all results on CPU.

No policies or language-model weights changed. This is a supervised calibration/combining experiment using existing scores; no GPU/API calls were made. Added paid compute is **$0** and cumulative spending remains **$12.50 of $20**. Reused official tests and unadjusted intervals make the findings exploratory.
