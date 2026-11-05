# Moderate-load RTX 5090 model reproduction

Status: **completed and audited; Shieldstral only. Qwen deferred at the owner’s request**.

This bounded deployment replication runs pinned Shieldstral-1.0-3B on one local
RTX 5090. Qwen3.5-2B and Qwen3.5-4B were initially planned and are now deferred. Existing published studies
and their frozen selections remain unchanged. This is fresh inference, not
metric reproduction from cached predictions.

## Fresh results

All **352 fresh classifications completed with zero inference errors**: 108
development and 244 test records. Thresholds were selected on development and
frozen before any of this model's test inference. The three comparisons used
the same pinned model; no weights were changed.

| Test | Correct / cases | Accuracy | Macro-F1 |
|---|---:|---:|---:|
| Religious-iconography demo | 18/48 | 37.50% | 0.2931 |
| Synthetic injection challenge | 54/80 | 67.50% | 0.6138 |
| Deepset injection test | 90/116 | 77.59% | 0.7715 |

The two injection test accuracies match the earlier published runs exactly.
All 80 synthetic-challenge and all 116 Deepset decisions are identical to those
historical predictions. The iconography run agrees on 47/48 decisions, scoring
18/48 versus the earlier 19/48. Only case ri-15-review crosses the lower score
boundary: its score moves from 0.05340 to 0.04209, changing REVIEW to ALLOW.
All three selected thresholds/bands match the historical ones. Deepset used
the bounded 64-row development sample rather than rerunning all 541 development
examples, so this is a bounded deployment replication.
See [case-level historical comparison](historical-comparison.json).

The results reproduce important limitations as well as successes. Iconography
allowed 12 of 16 proposed BLOCK cases. The synthetic challenge allowed 4 of 20
BLOCK cases; Deepset allowed 23 of 60. These scores describe the recorded
policies, adapters, labels and deployment. Three-way review routing uses a
calibrated binary-score band.

## GPU operation and cleanup

Fresh inference took **254.5 seconds**, including enforced rests and model setup.
Half-second monitoring recorded **49 C maximum**, **99.73 W maximum sampled
power**, **84.28 W mean sampled power**, and **9,390 MiB maximum total device
memory** (including desktop applications). PyTorch's peak tensor allocation was
about 7.28 GiB. Measured inference time was 21.90 seconds, or 8.6% of the full
run wall time. The first request includes kernel setup; later native forwards
were roughly 20–30 ms. These timings include a deliberately throttled run and
are not production throughput measurements.

Batch size was one, with a minimum half-second rest and at least three times
the measured operation duration between requests. No clock or power-limit
settings were changed. The 65 C temperature guard was not reached.
After process exit, the device returned to **1,151 MiB**, **34 C**, and about
**41 W**, with no Python GPU compute process. Desktop GPU applications remained
running. See [telemetry summary](gpu-summary.json), [monitor samples](shieldstral-3b/gpu-monitor.csv),
and [independent cleanup observation](cleanup.json).

Provider/API charges were **$0**; local electricity and engineering time were
not metered. No cloud resource was created. Qwen downloads were stopped when
the owner deferred Qwen, and no Qwen inference ran.

## Provenance, verification and setup notes

The model revision is 003ec7e2b0bab5f0e6307edbaf186fa5822b76f5.
The local environment used Python 3.12.16, Torch 2.8.0+cu128, Transformers 5.10.2
and the stock NVIDIA 615.78.08 driver on an RTX 5090.
[Runtime metadata](shieldstral-3b/runtime.json) retains the complete package
versions. [Registration](registration.json), [pre-test freeze](shieldstral-3b/freeze.json),
per-split manifests, logits, scores, requests and summaries bind the evidence.
The [checksum inventory](SHA256SUMS) covers the bundle and its reproduction code.

The [offline audit](verification.json) rechecked all 352 records, development
selection, pre-test ordering, source/input identities, normalized logits,
decisions and every saved metric. The initial post-run verifier incorrectly
required zero tensor bytes before the inference process exited. Its immutable
completion record retains 8,519,680 bytes of small buffers before exit; the
independent device observation confirms actual process-exit cleanup. The
[verification amendment](verification-amendment.json) records that correction.
No inference, prediction, score, threshold or frozen source was changed.
Use the offline verification tool below rather than the historical runner's
over-strict report subcommand. The tool prints JSON without changing the bundle by default; an optional
--report NEW_PATH saves a new audit record.

The sandbox initially hid GPU device files; approved host execution exposed
the working 5090 without driver changes. Initial NVIDIA dependency downloads
timed out. The cached CUDA-enabled Torch wheel was retained; remaining
dependencies installed from PyPI with a longer timeout. These setup failures
preceded inference. Model weights and environments remain local and are not
part of the public bundle.

The original protocol follows. Existing frozen studies were not edited.

## Registered protocol

Use the existing religious-iconography demo (24 development, 48 test cases),
synthetic instruction-boundary challenge (20 development, 80 test cases), and
Deepset prompt-injection test (116 test cases). For a bounded development
budget, select 32 ALLOW and 32 BLOCK Deepset development examples by ascending
SHA256 of case ID, retaining source order after selection. This 64-row
calibration subset differs from the original 541-row development study.
Include every test row; do not filter by output or observed correctness.

Models and dataset/policy/source hashes are recorded in registration.json.
Model revisions come from the existing WildGuard and Qwen study manifests.
Use BF16 Transformers SDPA, with no quantization, weight training, retries,
prompt search, constrained decoding or silent input truncation.
Oversized inputs and invalid outputs count as errors.

Shieldstral retains the repository's document/query/instruction adapter and
canonical yes/no first-token normalization. Select its abstention band on
development macro-F1 using the existing .05–.95 grid and tie rules.
Deepset uses the existing binary threshold selection. Freeze selections and
development-prediction hashes before that model's test inference.
Qwen uses strict free-generated labels, with thinking disabled and at most
eight output tokens. Deepset retains the existing A/B wrapper; the two
three-way demos use a fixed A/B/R wrapper recorded in source. Complete output
and an EOS stop are required. This is a new three-way Qwen deployment, not
an exact replication of the earlier WildGuard binary experiment.

## Moderate GPU operation

Run one model and one request at a time; no clock or power-limit changes.
Allocate at most 65% of VRAM to the process. Rest for at least three times
each measured GPU operation, with a minimum 0.5-second pause. This targets
a maximum 25% inference duty cycle, not an instantaneous wattage guarantee.
Pause at 65 C and resume at 60 C; abort if cooling takes more than 180 seconds.
Record GPU temperature, power and memory before and after each request.
Stock power limit is 575 W; the driver's minimum settable cap is 400 W.
Model loading and external desktop GPU activity are outside duty accounting.
Release model memory after each run and verify cleanup.

## Reporting and limitations

Accuracy counts errors as wrong. Report two-class macro-F1 for Deepset and
three-class macro-F1 for the demos, confusion matrices, false blocks, escapes,
review routing and failures. Save exact requests, model outputs, selected
thresholds, runtime versions and per-case timings. No ranking or significance
claim is preregistered; these are descriptive results on already-public tests.

The two synthetic tasks have AI-authored labels without independent human
adjudication. Deepset label/context and licensing caveats remain those in
evals/injection/README.md. Public-test training exposure is unknown. Transformers,
batch size, hardware and the bounded development subset differ from the
historical deployments. Report changes as system-level replication findings,
not proof of an intrinsic model difference or production protection.

Provider/API charges: $0 (local electricity and engineering time unmeasured).
No cloud resource is created.

## Commands

Audit this completed bundle from the repository root. This uses the Python
standard library and does not load a model, contact an API or use the GPU:

    python3 -B tools/verify_local_gpu_reproduction.py --out published_runs/2026-11-04-local-5090

For a new inference run, choose an output directory that does not exist and
use the recorded environment. The final command captures host GPU cleanup
after the preceding inference process has returned:

    venv/bin/python -m evals.local_gpu_reproduction register --out /absolute/path/new-local-run
    venv/bin/python -m evals.local_gpu_reproduction run --out /absolute/path/new-local-run --model shieldstral-3b
    venv/bin/python tools/verify_local_gpu_reproduction.py --out /absolute/path/new-local-run --capture-cleanup --report /absolute/path/new-local-run/verification.json

GPU commands require host GPU device access outside the agent sandbox.
Outputs are immutable; preserve failed attempts and register technical amendments.
