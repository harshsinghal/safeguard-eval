# Runtime record

These files describe the actual environments used for the StepGuard comparison.
They do not constitute a latency benchmark or a portable installer. The shell
scripts are captured Linux launch recipes with study-specific `/root/` paths;
restore inputs and establish your own authorization, budget and termination
controls before adapting them.

| Workload | Main packages | Execution |
|---|---|---|
| PolicyLM | Torch 2.11.0+cu128; Transformers 4.57.6 | Released helper, BF16, one window and one cleaning variant, fixed precision preset |
| Shieldstral / Clef Flash | Torch 2.11.0+cu128; Transformers 5.10.2 | Native scoring, one record at a time; Clef uses its Torch fallback |
| Kev | Torch 2.8.0+cu128; Transformers 5.17.0; PEFT 0.21.2; FLA 0.5.2 | Native choice head and fused kernels, one record at a time |
| GPT-OSS Safeguard | Torch 2.13.0; Transformers 5.17.0; vLLM 0.31.0 | Publisher MXFP4, BF16 activations, medium reasoning; amended concurrency ceiling 64 |
| Jev | OpenRouter Decisions API | Resolved `typesafe/jev-1.14-20261014`; native Choice requests |

The `*-freeze.txt` files contain full GPU-environment package inventories.
`serving-configuration.json` records the GPU, driver, model runtime and rental
rates. `run-safeguard.sh` is the **amended** command used for scored validation
and test; `live-test-server-audit.json` checks its live server flags. The
[amendment](../amendments/safeguard-batching.json) retains the earlier incomplete
pass rather than presenting it as another scored trial.

The per-model validation/test JSON files are execution summaries.
`final-prediction-audit.json` checks complete populations and actual Safeguard
input-token counts against preflight, and lists unresolved outputs without
publishing raw responses. `duplicate-label-audit.json` checks exact input
duplicates, conflicting labels and cross-split heuristic groups.

`setup.sh` records the environment setup, including the disposable container's
system-Python bootstrap. `pre-inference-notes.json` records the initial tokenizer
compatibility issue and lifecycle checks. `remote-watchdog.py` uses only a
provider-injected pod-scoped credential; no credential value is included here.
The independent local deletion watcher and the completion watcher remove the
pod and its disk. Actual cleanup is documented in [cleanup.json](../cleanup.json).

Raw inference/server logs and responses remain private. Different native
batching and kernel choices prevent treating these execution durations as a
controlled comparison of model latency or throughput.
