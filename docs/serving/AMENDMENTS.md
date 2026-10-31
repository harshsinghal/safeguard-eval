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
