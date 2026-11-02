# Running the injection study

The study completed at an accounted cost of $1.848778200 under the user-authorized $15 allocation, with the GPU terminated. See [the completed readout](README.md), [the frozen pre-test plan](PLAN.md), and [execution amendments](NOTES.md). The plan deliberately retains its pre-run wording; current status is recorded in the readout and progress file.

## Prepare without paid inference

The implementation used for this run is preserved in commit `cc7cf1f`; subsequent result-publication edits do not change the frozen inference code. Source hashes are in the run registration.

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

Paid commands require a private `authorization.json` with `approved: true` and `experiment_cap_usd: 15`. **Create this only after actual user authorization**, recording its source and time. This file is a guard, not a substitute for permission. The recorded study authorization is $15; a reproduction requires its own authorization. Recheck GPU/API prices, available balance and existing resources before provisioning. Set provider-side automatic termination, with at most $3.90 reserved for a six-hour $0.65/hour GPU. API caps are $1 for Jev and $3.50 for Safeguard. Do not change these caps merely to get a run to finish.

The recorded run used GPU.ai; the project owner also authorized RunPod as a fallback within the same budget. This is provenance, not a provider endorsement. A reproduction may use a compatible host chosen for its own cost and data-handling requirements. The sequential open-model runs were exercised on a 48 GB RTX6000 Ada. Do not publish SSH details, credentials, provider resource IDs, weights, raw source text or API responses.

The native engines inherit previously exercised, pinned implementations, but use separate Python environments:

| Model | Known environment to use for the smoke check |
|---|---|
| PolicyLM | Torch 2.11.0 CUDA 12.8; Transformers 4.57.6; huggingface_hub 0.36.2 |
| Shieldstral | Torch 2.11.0 CUDA 12.8; Transformers 5.10.2; torchvision 0.26.0 |
| Kev | Torch 2.8.0 CUDA 12.8; Transformers 5.17.0; PEFT 0.21.2; flash-linear-attention 0.5.2; compatible causal-conv1d 1.7.0 wheel |
| Clef | Torch 2.11.0 CUDA 12.8; Transformers 5.10.2; torchvision 0.26.0 |
| Safeguard | vLLM 0.31.0, published MXFP4 checkpoint, TRITON_ATTN, eager mode, medium reasoning, 8,192 output tokens; 16 concurrent requests |

Also install NumPy, SciPy, scikit-learn, safetensors, accelerate and Pillow as required; retain the actual environment freezes. Download and verify publisher source with `python -m evals.decision_models.fetch_sources --destination /private/path/vendor` and review it before execution. Keep native decision-head/encoder inference serial for this accuracy study; Safeguard uses the separately documented 16-request generation server. Do not silently substitute a generic chat template or classification head.

## Fitting, validation and final testing

For each split, use the same six registered systems. The commands are deliberately stage-gated.

```sh
# Use each model's matching environment for the open models.
python -m evals.prompt_injection.infer --state "$STATE" --slug policylm --split fit --vendor /private/path/vendor
# Repeat for shieldstral, kev and clef.

python -m evals.prompt_injection.api --state "$STATE" --slug jev --split fit --keyfile /private/path/openrouter-key.txt
# Start a localhost-only vLLM server with the pinned Safeguard checkpoint.
# The full server invocation is in the execution artifacts.
python -m evals.prompt_injection.local_safeguard --state "$STATE" --split fit --concurrency 16

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

Jev uses its native Decisions API. The initial Safeguard/Groq API preflight was rate-limited and is retained only as operational evidence; the benchmark uses the pinned self-hosted Safeguard checkpoint throughout. Credential values are read from a local file and never printed. A durable SQLite ledger reserves costs before each request; unknown transport charges retain a conservative upper bound. Pending reservations must be reconciled before resuming. Retries do not replace malformed model output with repeated samples. Results are resumable only for matching request hashes. Repeated failures halt the run for inspection.

Before final testing, collect and inspect fitting/validation execution failures, freeze all policies, and archive the selection evidence. Do not inspect test examples to repair a policy or decide which arm to report. Additional revisions require another registered study.

## Publish and stop billing

Collect prompt-free predictions, source hashes, metadata, selected IDs, exact costs, environment records and failure/amendment notes. Raw example-bearing policies remain private; publish their hashes and source IDs so they can be restored from the pinned development records. Original brief/structured policy text is in `policies.py`. The four final test collections must be reported separately, with baseline changes and both types of classification errors.

Terminate the GPU, verify provider status and billing, remove temporary access keys, reconcile both API ledgers, and update `docs/COMPUTE.md`. Publish the readout and safe evidence with a README link. This is an accuracy study, not a controlled latency or cost-per-request benchmark.

## Reproduce the published tables without inference

Use the completed prompt-free archive and its checksum
verifier. This step needs NumPy but no GPU, model download, API key or raw prompt
text. It recomputes the metrics and paired bootstrap intervals rather than
copying the published table.

```sh
python scripts/reproduce_prompt_injection.py \
  --archive published_runs/2026-11-02-prompt-injection \
  --out /tmp/injection-reproduced.json
```

To reconstruct the exact model-specific policy candidates, prepare the pinned
data privately using the steps above, then run:

```sh
python scripts/restore_prompt_injection_policies.py \
  --archive published_runs/2026-11-02-prompt-injection \
  --data-state "$STATE" \
  --out /private/path/restored-policies
```

The script requires the original fitting-data hash and verifies each restored
policy against the frozen file hash. Keep these files private because their
labeled examples quote source datasets whose redistribution terms differ.

To regenerate the Markdown tables and both figures from the same public archive,
install Matplotlib (the recorded renderer used 3.11.2) and run:

```sh
python scripts/render_prompt_injection.py \
  --archive published_runs/2026-11-02-prompt-injection \
  --out-dir /tmp/injection-report
```
