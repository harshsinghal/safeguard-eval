# Serving implementation notes

Before any successful timing pass, the first vLLM startup failed because the
isolated environment's `ninja` binary was not on PATH. The controller now exports
that environment's bin directory alongside its explicit CUDA_HOME. The interrupted
second startup and original failure logs are retained. Text-only serving is also
explicit for Shieldstral and Qwen, since this workload contains no images; their
text policies and output handling are unchanged. No results were used to make
these setup fixes.

The GPU image also lacked the C++ compiler component required by FlashInfer JIT
(`cc1plus`). Installed build-essential, ninja-build and Python development headers
before restarting the untouched tuning grid. Failed startup logs remain available.

The image selected GCC 12 but initially had only the GCC 11 C++ component.
Installing `g++-12` aligned the host compiler used by NVCC. A direct CUDA compile
smoke check precedes the restarted benchmark. This is an environment repair, not
a change to policies, weights, scoring or the tuning objective.

The dependency resolver installed CUDA 13.4 compiler components beside Torch
CUDA 13.0 runtime headers. FlashInfer correctly rejected that mismatch. Pinned
NVCC, CRT and NVVM to 13.0.88, matching the runtime major/minor, and retained
the failure logs. The initial CUDA smoke compiled a trivial kernel but did not
exercise FlashInfer; its success was insufficient as a serving readiness check.
No successful timed passes occurred before these repairs.

FlashInfer then required conventional CUDA linker paths not supplied by the pip
package layout: `lib64 -> lib` and `libcudart.so -> libcudart.so.13`. Added these
links in the isolated vLLM environment and tested the actual sampling kernel.
All these setup costs are included in billing, and none in warm serving timings.

The server then became healthy, but the cache-reset control returned 404. vLLM
requires `VLLM_SERVER_DEV_MODE=1` for this control. Enabled it on the benchmark
server, bound only to loopback, so each measured pass can explicitly reset its
cache. This development control is not a production deployment recommendation.
The initial control failure occurred before warm-up or timed requests.

Qwen's fitting-only consistency check flagged a maximum auxiliary score change of
0.031209 at both scheduling budgets, with **zero decision changes in 32 cases**.
The submitted inputs and policy were unchanged; the difference appeared when
changing batch composition. Qwen's registered primary decision is its freely
generated A/B label, not a threshold on that auxiliary probability. After review,
retain and flag the score discrepancy, and allow timing of this label interface.
Do not describe its scores as equivalent or assume an ensemble/calibrator can be
moved without revalidation. No measurement-population or ground-truth accuracy
results were used in this decision. Other models' score gates remain unchanged.

WildGuard's startup rejected `--tokenizer-mode slow` because vLLM 0.32 does not
register that server mode. Remove the redundant flag: the benchmark client still
uses the pinned **slow tokenizer** and sends explicit token IDs with one BOS, so
the server does not tokenize the submitted text. This preserves the historical
WildGuard input preparation. Check output agreement against its cached baseline.

The native decision-model logs revealed missing optional optimized kernels. Keep
the original reference-runtime measurements and add a separate kernel experiment,
with unchanged weights, policies, thresholds and request serialization. Do not
alter an environment while it is being measured. Kev's pinned publisher fused
implementation requires flash-linear-attention 0.5.2; use that exact version in a
separate Torch 2.8 environment, with causal-conv1d 1.7.0's matching CUDA 12 wheel.
Clef uses flash-linear-attention 0.6.0 in a separate Torch 2.11 environment; no
matching prebuilt causal-conv1d 1.7.0 wheel was available, so retain its PyTorch
convolution. CUDA graphs are not added to the native wrappers in this extension.

Before measurement, compare 32 fitting inputs against the reference runtime,
in addition to the within-runtime batching gate. Flag maximum score change above
0.02 or more than one decision change. Retain failures. Repeat the same batch-size
selection and measurement protocol only for configurations that pass. These are
bounded optimization attempts, not the publishers' maximum performance claims.
The kernel extension also warms all 96 fitting inputs at the upcoming concurrency
to exercise batch-shape JIT compilation. Measurement texts remain unused for
warm-up. Some unseen shapes may still add first-use overhead; retain all repeats.

The large shared-policy cache benefit observed for Shieldstral motivates one
additional operational sweep: fill in cached concurrency 8 and 64 for the three
vLLM systems, using their already frozen token budgets, policies and output
contracts. The original cached conditions were 1 and 32. Register this extension
before running the added conditions; no settings or thresholds are selected from
the measurement results. This makes the latency/throughput curve more useful for
deployment planning. Keep its source and completion markers separate.
