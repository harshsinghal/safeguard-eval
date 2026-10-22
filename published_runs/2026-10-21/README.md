# First live policy-model comparison — October 21, 2026

Four policy models were evaluated on the same fictional religious-iconography rule, using one rented GPU.ai RTX PRO 6000 Blackwell Server Edition (96 GB). **These are agreements with AI-drafted labels on a 48-case synthetic test split, not validated safety accuracy or a general model ranking.** Each test class has 16 cases. The 24 development cases were used separately.

## Test results

| Model | Draft-label matches | Macro-F1 | Sent to review | Clear BLOCK → ALLOW | Clear ALLOW → BLOCK | Errors |
|---|---:|---:|---:|---:|---:|---:|
| [GPT OSS Safeguard 20B](safeguard-test/summary.json) | 40/48 (83.3%) | 0.815 | 8/48 | 0/16 | 0/16 | 0/48 |
| [PolicyLM 1.7B](policylm-test/summary.json) | 36/48 (75.0%) | 0.750 | 19/48 | 0/16 | 1/16 | 0/48 |
| [CoPE-B-A4B](cope-test/summary.json) | 32/48 (66.7%) | 0.536 | 0/48 | 0/16 | 0/16 | 0/48 |
| [Shieldstral 1.0 3B](shieldstral-test/summary.json) | 19/48 (39.6%) | 0.330 | 3/48 | 12/16 | 2/16 | 0/48 |

## Interpretation

Safeguard matched 40/48 draft labels: all 32 clear ALLOW/BLOCK cases and 8/16 expected-REVIEW cases. The other eight ambiguous cases received automatic decisions (three ALLOW and five BLOCK).

CoPE-B correctly separated all 32 clear ALLOW/BLOCK cases, but sent none of the 16 expected-REVIEW cases to review. Its score confidence did not represent the ambiguity defined by the platform. That is why a binary classifier plus an uncertainty band must be evaluated separately from an explicit three-action policy decision.

PolicyLM matched 36/48 draft test labels and held 19/48 cases. Its relatively high match rate comes with substantial review workload. Shieldstral matched 19/48 in this setup and allowed 12/16 clear BLOCK cases. This result concerns this custom rule, prompt framing, and score mapping; it does not contradict or reproduce the model authors' benchmarks.

Inspect [case-level predictions](#artifacts) before drawing conclusions. The prompts deliberately include direct and indirect religious references, mundane uses of similar names/shapes, explicit exclusions, contradictory requests, and missing references. The reference labels have not been independently adjudicated, and some ambiguities are stated explicitly in the prompt.

## Frozen development procedure

- Policy and dataset were fixed before live inference. No test-driven prompt or label edits were made.
- Each binary model ran all 24 development cases. The fixed grid was 0.05, 0.10, …, 0.95, with lower < upper. Selection maximized development macro-F1; ties favored automatic coverage, narrower bands, then lower bounds. The chosen thresholds were frozen before that model's test run.
- Safeguard was prompted directly for ALLOW/BLOCK/REVIEW, with medium reasoning effort, temperature 0, and an 8,192-token completion ceiling. It was self-hosted here, **not called through Groq**; Groq remains the original interactive-demo provider.
- Shieldstral and CoPE used first-token label log probabilities with explicit vLLM `logprob_token_ids`, obtained from each served tokenizer. Both label alternatives were required; no missing probability was fabricated. The score uses the strongest matching token variant per binary label and renormalizes those two alternatives.
- PolicyLM used its pinned native helper, CUDA BF16, and default input cleaning. Its block/allow/precedence category translation differs from the chat adapters; it does not have a semantic REVIEW class.
- The initial development summaries reflect the exploratory 0.2/0.8 band. The separate `calibration.json` files contain the selected-band development metrics and every grid candidate. Test summaries use the frozen selected band.

| Model | ALLOW below | BLOCK at or above | Revision |
|---|---:|---:|---|
| GPT OSS Safeguard 20B | explicit label | explicit label | `8a11e17b25c973a24099d4016bf2e17dd7ec1574` |
| PolicyLM 1.7B | 0.15 | 0.9 | `b3b2cd408a08a68ab6a30c1fc1e440204e44d57e` |
| CoPE-B-A4B | 0.05 | 0.1 | `b28a1c734eff80d82e5df7964c7dfd0de8509900` |
| Shieldstral 1.0 3B | 0.05 | 0.15 | `003ec7e2b0bab5f0e6307edbaf186fa5822b76f5` |

## Runtime and cost

One instance was reused sequentially at $1.69/hour, with a server-side two-hour termination limit ($3.38 maximum at the quoted rate). The requested overall budget was below $10. Termination was confirmed, and GPU.ai metered **701 seconds at $0.33** for this instance. Evidence is recorded in [billing.json](billing.json). No Vast.ai or other provider was used.

The HTTP models used vLLM 0.31.0 / PyTorch 2.13.0, eager execution, a 16,384-token context limit, GPU-memory utilization 0.85, and at most four sequences (the evaluation itself was sequential). CoPE and Shieldstral used BF16 weights; Safeguard used its MXFP4 checkpoint with BF16 activations, the MARLIN MoE backend, TRITON_ATTN, and the `openai_gptoss` reasoning parser. PolicyLM used Transformers 4.57.6 / PyTorch 2.11.0+cu128 through its native helper. Dependency snapshots are in [environment/](environment/).

Startup repairs: the base image lacked a C compiler and Ninja; these were installed. Safeguard's initial FlashInfer initialization could not locate the CUDA compiler, so the successful launch selected TRITON_ATTN and set CUDA_HOME to the installed CUDA toolkit. These failures occurred before classification, are included in rental time, and are not hidden as model decision errors.

Per-case timing in summaries includes HTTP overhead for served models and excludes model loading. PolicyLM is a native call, and vLLM prefix caching was enabled. There was one run per model and no latency-controlled repetition; these timings are diagnostic, not a hardware speed leaderboard.

## Artifacts

Each directory contains exact requests, predictions (with raw HTTP choices where applicable), a policy snapshot, manifest, and summary. Binary development directories also include calibration results. Dataset/policy/runner hashes are recorded. Remote code was copied rather than Git-cloned, so manifests have an empty Git commit; matching runner source snapshots are retained in [source_snapshots/](source_snapshots/). PolicyLM ran before the explicit-token-ID option was added, hence its separate matching runner snapshot. That option affects only the HTTP binary adapters.

- GPT OSS Safeguard 20B: [development](safeguard-dev/) · [test predictions](safeguard-test/predictions.jsonl) · [test summary](safeguard-test/summary.json)
- PolicyLM 1.7B: [development](policylm-dev/) · [test predictions](policylm-test/predictions.jsonl) · [test summary](policylm-test/summary.json)
- CoPE-B-A4B: [development](cope-dev/) · [test predictions](cope-test/predictions.jsonl) · [test summary](cope-test/summary.json)
- Shieldstral 1.0 3B: [development](shieldstral-dev/) · [test predictions](shieldstral-test/predictions.jsonl) · [test summary](shieldstral-test/summary.json)

## Limits and next steps

This small public synthetic set is not representative of platform traffic. It has balanced labels, uneven cultural coverage, two tiny non-English slices, deliberate contrasts, and no independent annotation. Related groups stay within a split, but these are not secret, contamination-free test data. The adapters, policy translation, score calibration, and model are all part of the tested system. No statistical superiority claim is warranted.

Next: independently adjudicate labels; add licensed, deduplicated real prompts from DiffusionDB with random controls; include naturally occurring ambiguity; evaluate alternate policies and policy edits; and rerun with frozen, model-appropriate prompts and a separate untouched test set. Keep semantic review and operational failure routing separate.
