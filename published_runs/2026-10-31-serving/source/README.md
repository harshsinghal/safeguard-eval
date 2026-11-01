# Source and execution map

The implementation changed during compatibility repairs and bounded serving
extensions. A single final source hash would hide that history. This directory
preserves the exact uploaded snapshots and their registrations.

| Phase | Executed work | Source overlay |
|---|---|---|
| Original runtime | Shieldstral, PolicyLM, Liquid, Kev and Clef original profiles; initial Qwen score-gate attempt | `source-phase1.tar.gz` |
| Compatibility/kernel phase | Accepted Qwen original profile; discarded WildGuard fast-tokenizer fitting attempt | `phase2-source.tar.gz` |
| WildGuard tokenizer repair | Accepted WildGuard tuning and original measurements, then Kev/Clef optimized-kernel extension; the tokenizer guard remains in later clients | `tokenizer-repair-source.tar.gz` over phase 2 |
| Native batch / cached curve extension | PolicyLM 32,768-token budget fitting attempt (rejected); added vLLM cached C8/C64 passes | `phase3-source.tar.gz` over the repaired client |

`repository-evals-base.tar.gz` contains the evaluation dependencies from the
recorded base Git commit. Extract that archive inside a `safeguard-eval/`
subdirectory; the phase overlays already contain that directory prefix and
should be extracted one level above it. State-directory members in the overlays
are historical registrations, not restored prompt files. Apply the phase overlays in the order above to inspect
the effective serving implementation. The original decision adapter remains in
the base; phase 2 adds an optional publisher-fused runtime argument, defaulting to
the previous behavior. `dependencies-and-tools.tar.gz` additionally preserves the
final analysis/restoration tools and source. Some archived registrations describe
their phase's hashes rather than the final repository's hashes; compare them with
the corresponding immutable overlay.

vLLM servers always ran in the pinned vLLM environment. Accepted WildGuard
clients and the final added cached curves ran from the Transformers 4.57.6 client
environment; the model server did not change. Kev/Clef native kernel extensions
used their separate recorded environments. PolicyLM's enlarged-token-budget run
used the same model environment as its reference run. Adding HTTPX and tokenizer
packages to that environment did not change its Torch or Transformers versions.

`repair.sh` records the final serial supervisor and tokenizer-package repair;
its process IDs and paths belong to this historical run, so it is not a fresh
provisioning command. `tokenizer-check.py` reproduces the input-token hash audit.

Setup and controller logs record compiler repairs, installation attempts,
readiness and measured-pass completion. Server readiness times include different
amounts of cached download/compilation work and exclude some first-request JIT
warm-up; do not treat them as a standardized cold-start benchmark.

The controller stops child servers, but only the provider API termination ends
GPU billing. The bill includes setup, downloads, compilation, failed attempts,
warm-up, inference and artifact collection. No timing table includes setup time
inside a warm request latency.
