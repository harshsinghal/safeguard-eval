# Reproducing the Qwen comparison

The public archive contains prediction records without the source prompts, labels needed to score them, all candidate policies, model and dataset revisions, runtime metadata, and the code used for inference and analysis. Full requests and responses remain private because WildGuardMix source access is gated. No credentials are published.

## CPU-only metric reproduction

From the repository root, with Python 3.9 or newer and no third-party packages:

```sh
python3 -m evals.qwen_policy.reproduce \
  --evidence published_runs/2026-10-25-qwen \
  --prior published_runs/2026-10-24-wildguard \
  --out /tmp/qwen-reproduced \
  --intervals
```

Use a new output directory. This decompresses every public prediction archive, verifies hashes and population completeness, recomputes every run's accuracy/F1/error/category metrics, and reproduces all paired intervals and calibration comparisons against the immutable prior policy-model predictions. It needs neither GPU access nor source dataset text. The intervals use 2,000 group-bootstrap replicates with the recorded seed. The public `SHA256SUMS` inventory covers the artifact files.

## Rerunning inference

Obtain authorized access to the dataset and reproduce the prior study's exact data splits; see its [reproduction guide](../2026-10-24-wildguard/REPRODUCING.md). Use the source snapshot, recorded model revisions, dependency lock and job files. Preserve physical-newline JSONL parsing (`split("\n")`, not `splitlines()`); source strings may contain Unicode line separators. The Qwen checkpoints themselves are public and were downloaded without a token. No model weights were modified.

The public GPU environment capture has trailing whitespace normalized, and operational script snapshots omit extra blank lines at EOF; their originals are retained privately. The recorded vLLM service uses BF16, greedy decoding, explicit non-thinking mode, eight maximum generated tokens, 32 concurrent requests, a 32,768-token context limit, eager execution and text-only input. The complete generated answer must be A or B with a successful stop. Extra explanations, refusals, incomplete answers and transport failures count as errors; token scores do not repair them. The optional score is derived from the largest reported token probability for each stripped A/B variant and normalized over those two label weights. It is not a calibrated estimate of real-world harmfulness.

`source/jobs/` records every pilot, shared, tailored and final run. `selection.json` contains all fitting/validation scores; `freeze.json` pins all final settings, policies, revisions, source hashes, dataset hashes and validation-derived threshold controls. Final inference checks the inputs and settings against the freeze. Test and audit data were uploaded only after the freeze was published. The freeze’s `new_qwen_test_inference_started: false` flag records its creation-time state; inference subsequently ran, and the freeze remains an immutable historical record.

A new inference run may differ with hardware, batch context or library changes even under greedy decoding. Public CPU reproduction verifies the recorded experiment exactly; it does not promise bitwise reproducibility of future GPU outputs. Historical specialist predictions used their original native interfaces and deployment settings. This is an exploratory system comparison: previous WildGuardTest results were known, and model pretraining exposure is unverified.

## Figure and archived sources

With `matplotlib==3.9.4`, render the PNG, editable-text SVG and plotted-data CSV into a new directory:

```sh
python3 -m evals.qwen_policy.plot --analysis published_runs/2026-10-25-qwen/analysis.json --out /tmp/qwen-figures
```

The published figure was visually checked. The archived Python/JSON sources match the implementations used for successful reproduction byte-for-byte. To use the archived package instead of the checkout, run outside the repository with `PYTHONPATH` set to the absolute `source` directory and pass absolute evidence/prior/output paths. Source and artifact hashes are recorded in `SHA256SUMS`. `reproduction.json` records the successful CPU check.
