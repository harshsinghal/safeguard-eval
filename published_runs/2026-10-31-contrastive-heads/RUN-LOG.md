# Contrastive-head experiment run log

- Registered protocol and code in commit 41f5e5c before classifier fitting.
- Exact smart-ensemble populations reused; previous WildGuard PolicyLM features verified against manifests and reordered by identity where needed.
- Public test was used previously; all current head selection uses fitting/validation only.
- GPU.ai L40S reserved at $0.80/hour with two-hour automatic termination; no API inference calls. Initial bootstrap polled before the asynchronous create operation had a resource ID; resumed against the same operation, no duplicate instance.
- Local deterministic CPU fitting uses Torch 2.8.0, three predeclared seeds, identical ordinary/contrastive network architectures and training schedules.

- ModernBERT fast-tokenizer special-mask incompatibility repaired before any ModernBERT features were produced; recorded in AMENDMENTS.md and registration-v1.json.
- All missing features collected and identity/hash checked. GPU gpu-c3df4537 terminated; 513 billed GPU-seconds, $0.11; temporary local/provider SSH keys removed.
- All 123 checkpoints in the first three completed task/backend combinations refitted exactly; maximum validation prediction difference 0.

- All four task/backend groups completed without failed candidates. Freeze published in commit fae8fd8579817e5f741555d925aaaeed7e0c1699 before test classification. Validation selected PolicyLM/contrastive for WildGuard and PolicyLM/LR for HateXplain, for both main objectives.

- Frozen test evaluation completed with 100% coverage. All 164 candidate checkpoints reproduced exactly, all 112 selected metric rows and all 12 paired intervals verified. An additional direct check confirmed exact equality of all 20 linear coefficient arrays, intercepts and validation predictions.
- Test results were not used to replace selections. WildGuard selected contrastive but linear control performed better; HateXplain selected linear, with small uncertain balanced-profile differences. Accuracy-optimized HateXplain selection traded fewer false blocks for more misses.
- Final GPU status and billed usage rechecked: terminated, $0.11; no active instances remain. Repository readout, full results, research notebook, experiment map and budget ledger updated. Papers and pinned skill snapshots remain unchanged.
