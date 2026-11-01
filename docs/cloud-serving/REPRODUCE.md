# Reproduce the L4 serving pilot

## Audit saved results without renting a GPU

The frozen bundle links the registration, policy, per-request traces, environment,
launch commands, fitting selections, failures and bill. The audit recomputes the
metrics and verifies input identities, selections, output consistency and hashes.
It does not claim an independent GPU rerun.

```bash
python3 tools/verify_cloud_serving.py --root published_runs/2026-11-01-cloud-serving
```

The audit uses NumPy and httpx. Plots additionally use matplotlib:

```bash
python3 tools/plot_cloud_serving.py \
  --source published_runs/2026-11-01-cloud-serving/results.json \
  --out docs/cloud-serving/figures
```

## Restore the inputs

The 64 fitting prompts are the first 64 records in the preceding serving study's
96-prompt fitting file. Restore that file with
[`restore_serving_inputs.py`](../../tools/restore_serving_inputs.py), following
the [prior reproduction guide](../serving/REPRODUCE.md) and dataset terms. Rename
the restored `inputs/tune.jsonl` to `private-fit.jsonl` in a fresh state directory.
Copy this pilot's `registration.json` and `policy.json` into that directory.

The harness uses the pinned tokenizer to render the fitting inputs and generate
synthetic documents deterministically. The synthetic documents do not inherit
the fitting examples' text or labels. Their full input token hashes and length
counts appear in `input-manifest.json`; private fitting text and token sequences
are excluded from the public bundle.

On a dedicated GPU machine with the recorded dependencies, run:

```bash
python -m evals.serving.cloud_lengths --state /root/cloud-state --action prepare
```

Compare the generated `input-freeze.json` and `input-manifest.json` to the archive
before inference. Keep original frozen files intact; write any new run elsewhere.

## Repeat inference

The captured setup script and package freezes describe the actual environments.
It uses dedicated `/root/vllmenv` and `/root/sglangenv` paths on a disposable GPU
machine, not a user's everyday Python environment. `runtime/sglang-python.txt`
identifies the second environment. Both engines require a compatible NVIDIA
driver and CUDA toolchain; the rented base image's advertised CUDA version alone
does not establish compatibility with the installed wheels.

```bash
python -m evals.serving.cloud_lengths --state /root/cloud-state --action vllm
python -m evals.serving.cloud_lengths --state /root/cloud-state --action sglang
```

Run engines serially. The controller launches each engine with both registered
chunk sizes, uses fitting requests to select one, and then restarts that engine
for its length measurements. A failed setup is recorded rather than counted as
zero latency. Use provider-side termination limits, export results before the
deadline, terminate the rental and reconcile the bill. Recheck current capacity,
prices and your budget before starting a new paid run.

## How the numbers are calculated

Latency runs from client request construction through HTTP transport to parsing a
complete classification on loopback. Throughput is valid classifications divided
by the whole timed pass, including any failed requests' elapsed time. Invalid or
unfinished outputs and changed prompt-token counts are errors. There are no
automatic request retries.

For each length/concurrency point, the readout averages the two passes'
throughputs and latency percentiles. A mean of two p95 values is not a pooled
percentile or a confidence interval. Each pass has only 64 requests; especially
at concurrency 32, the short run does not establish steady-state production tail
latency. Graphs show the recorded operating points, not an engine's capacity
under every tuning choice.

The projected GPU cost per million is `hourly GPU rate / 3600 / valid requests
per second * 1,000,000`, calculated per pass and then averaged. It assumes
sustained measured utilization, excludes cloud/network/engineering overhead, and
uses the experiment provider's rate. Actual rental cost includes setup and idle
time and is recorded separately. Startup measurements include differing cache
and compilation states; they are descriptive, not a controlled cold-start ranking.
