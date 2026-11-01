# Reproduce the serving measurements

## Recompute the published tables without a GPU

From the repository root, with Python, NumPy and HTTPX installed:

```sh
python tools/report_serving.py \
  --state published_runs/2026-10-31-serving/reference \
  --output /tmp/serving-reference
python tools/report_serving.py \
  --state published_runs/2026-10-31-serving/optimized \
  --output /tmp/serving-optimized
```

The script checks every saved pass against its individual request timings,
verifies the request population and hashes, aggregates all three repeats, and
checks decisions and scores against a single-request reference. Gzipped traces
are supported. The historical comparison reapplies the registered cutoff where
appropriate; Qwen uses its generated label and WildGuard its official output.
It is an agreement check, not a new accuracy evaluation.

The archive includes failed setup attempts. A model's `complete.json` identifies
finished measurements; a leftover failure file is not the final status. The
optimized-native extension has its own registration and traces.

## Restore the workload

The source is `allenai/wildguardmix`, revision
`d29c47f41c8b51348b5c8e8c81c039b3132b66d1`. Obtain the original WildGuardTrain and
WildGuardTest parquet files from that revision, respecting its access terms.
Source file hashes are checked by the restoration tool. The published manifest
contains dataset row IDs and prompt hashes; the archive does not duplicate the
prompt text.

```sh
python tools/restore_serving_inputs.py \
  --protocol published_runs/2026-10-31-serving/reference \
  --output /tmp/serving-new-run \
  --train /path/to/wildguard_train.parquet \
  --test /path/to/wildguard_test.parquet
```

Restoration recreates 96 fitting and 384 measurement inputs with exact file
hashes. Neither expected labels nor other dataset fields enter the server.
Unlike a model-quality experiment, this study uses test text to measure serving
speed; it does not use test labels to optimize a classifier.

## Run a new GPU experiment

A fresh run incurs compute charges. The supplied source is a research harness,
not an unattended provisioning product. Select your own provider, set a spending
limit and provider termination deadline, and collect results before terminating
the machine. The published bill is historical, not a promise of future prices.

1. Reproduce the recorded environments on a compatible Linux NVIDIA GPU. The
   archive includes installation scripts and exact installed-package inventories.
   These paths assume environments under `/root`; adapt them in `study.py` for a
   different layout. Compilation requires a C++ compiler and matching CUDA
   headers, compiler and runtime. Read [the implementation notes](AMENDMENTS.md)
   before treating a healthy HTTP endpoint as evidence that inference works.
2. Copy the registration and policies into a **new** state directory, alongside
   the restored inputs. Keep original timing traces and selection files separate.
   Record any change of GPU, model revision, precision, adapter or software.
3. For Kev and Clef, retrieve the publisher sources at the revisions recorded in
   `evals/decision_models/study.py`; verify every file in
   `evals/decision_models/vendor-hashes.json`. The wrappers expect these under
   `/root/decision-vendor`. Do not silently use a newly released native head.
4. For Liquid, supply the study's selected fine-tuned encoder/head checkpoint,
   whose SHA-256 is in the registration. Its 1.4 GB FP32 weights were retained
   locally rather than put in Git. The public fine-tuning recipe permits a new
   training run, but that would be a new checkpoint and requires a new serving
   registration. The released base encoder alone is not our measured classifier.
5. Run models serially; the harness uses one loopback port and one GPU. Start with
   a fitting-only smoke run before the complete sweep. A full invocation is:

```sh
/root/vllmenv/bin/python -m evals.serving.study \
  --state /root/serving-new-run --model all
```

The controller tries the two registered settings, saves output-consistency checks,
selects on fitting throughput, and then measures the frozen choice. It resumes
from completed passes; use a new directory for a genuinely new experiment.
The native-kernel extension also needs the 32 fitting reference outputs under
`runtime-reference/` and its separately pinned environments.

The controller stops its child server on exit and has a five-hour alarm. This
**does not terminate a rented GPU**. The provider deadline is a backstop; the
operator must terminate the instance promptly, verify its status, and reconcile
the bill. The benchmark enables vLLM development cache controls on localhost;
do not expose that configuration as a public production service.

## What replication cannot establish

Identical inputs and settings do not ensure identical timing on a shared host or
new driver. Score rounding can also change with batching or kernels. Preserve
new timings, output differences, failures and costs as a separate result.
The short closed-loop workload does not measure burst tolerance, long documents,
network latency, multi-tenant scheduling, uptime or a production p99 guarantee.
