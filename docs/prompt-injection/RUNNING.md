# Running the injection study

No paid inference has run yet. The code has local contract tests, but its new end-to-end GPU/API execution still needs a smoke check. See [the plan](PLAN.md) for the selection rules and the budget request.

## Prepare without paid inference

Use Python 3.12 in a local virtual environment. The preparation environment used `pyarrow==26.0.0`, `numpy==2.5.4`, `scipy==1.18.1` and `scikit-learn==1.9.1`. Keep `STATE` outside Git: it contains licensed dataset text and later request logs.

```sh
export STATE=/absolute/private/path/prompt-injection-state
python -m evals.prompt_injection.data fetch --state "$STATE"
python -m evals.prompt_injection.data inspect --state "$STATE"
python -m evals.prompt_injection.data prepare --state "$STATE"
python -m unittest evals.prompt_injection.test_contracts -v
python -m evals.prompt_injection.study register --state "$STATE"
python -m evals.prompt_injection.study jobs --state "$STATE" --split fit
```

`inspect` prints schemas and counts, not held-out text. `prepare` preserves original texts for inference; normalization is restricted to the duplicate audit. Its hashes and counts are recorded in the preparation directory. Running `register` records source-code hashes; changing code afterward requires a documented amendment, not overwriting the registration without a record.

## Authorize and provision before inference

Paid commands require a private `authorization.json` with `approved: true` and `experiment_cap_usd: 8`. **Create this only after actual user authorization**, recording its source and time. This file is a guard, not a substitute for permission. This study's request remains pending. Recheck GPU/API prices, available balance and existing resources before provisioning. Set provider-side automatic termination, with at most $2.60 reserved for a four-hour $0.65/hour GPU. API caps are $1 for Jev and $3.50 for Safeguard. Do not change these caps merely to get a run to finish.

GPU.ai is preferred; RunPod is a fallback within the same budget. A 48 GB RTX6000 Ada is sufficient for the sequential open-model runs. Do not publish SSH details, credentials, provider resource IDs, weights, raw source text or API responses.

The native engines inherit previously exercised, pinned implementations, but use separate Python environments:

| Model | Known environment to use for the smoke check |
|---|---|
| PolicyLM | Torch 2.11.0 CUDA 12.8; Transformers 4.57.6; huggingface_hub 0.36.2 |
| Shieldstral | Torch 2.11.0 CUDA 12.8; Transformers 5.10.2; torchvision 0.26.0 |
| Kev | Torch 2.8.0 CUDA 12.8; Transformers 5.17.0; PEFT 0.21.2; flash-linear-attention 0.5.2; compatible causal-conv1d 1.7.0 wheel |
| Clef | Torch 2.11.0 CUDA 12.8; Transformers 5.10.2; torchvision 0.26.0 |

Also install NumPy, SciPy, scikit-learn, safetensors, accelerate and Pillow as required; retain the actual environment freezes. Download and verify publisher source with `python -m evals.decision_models.fetch_sources --destination /private/path/vendor` and review it before execution. Keep inference serial for this accuracy study. Do not silently substitute a generic chat template or classification head.

## Fitting, validation and final testing

For each split, use the same six registered systems. The commands are deliberately stage-gated.

```sh
# Use each model's matching environment for the open models.
python -m evals.prompt_injection.infer --state "$STATE" --slug policylm --split fit --vendor /private/path/vendor
# Repeat for shieldstral, kev and clef.

python -m evals.prompt_injection.api --state "$STATE" --slug jev --split fit --keyfile /private/path/openrouter-key.txt
python -m evals.prompt_injection.api --state "$STATE" --slug safeguard --split fit --keyfile /private/path/openrouter-key.txt

# All six fitting outputs are required before creating the example policies.
python -m evals.prompt_injection.study author --state "$STATE"
python -m evals.prompt_injection.study jobs --state "$STATE" --split validation
# Repeat the six inference commands with --split validation.

# All validation candidates for all six models are required here.
python -m evals.prompt_injection.study freeze --state "$STATE"
python -m evals.prompt_injection.study jobs --state "$STATE" --split test
# Repeat the six inference commands with --split test.

python -m evals.prompt_injection.report --state "$STATE" --out "$STATE/report"
```

The API code routes Jev to its Decisions interface and Safeguard to Groq through OpenRouter, without provider fallback. Credential values are read from a local file and never printed. A durable SQLite ledger reserves costs before each request; unknown transport charges retain a conservative upper bound. Pending reservations must be reconciled before resuming. Retries do not replace malformed model output with repeated samples. Results are resumable only for matching request hashes. Repeated failures halt the run for inspection.

Before final testing, collect and inspect fitting/validation execution failures, freeze all policies, and archive the selection evidence. Do not inspect test examples to repair a policy or decide which arm to report. Additional revisions require another registered study.

## Publish and stop billing

Collect prompt-free predictions, source hashes, metadata, selected IDs, exact costs, environment records and failure/amendment notes. Raw example-bearing policies remain private; publish their hashes and source IDs so they can be restored from the pinned development records. Original brief/structured policy text is in `policies.py`. The four final test collections must be reported separately, with baseline changes and both types of classification errors.

Terminate the GPU, verify provider status and billing, remove temporary access keys, reconcile both API ledgers, and update `docs/COMPUTE.md`. Publish the readout and safe evidence with a README link. No result, latency claim or cost-per-request conclusion should be inferred from this preparation-only record.
