# Running or reproducing the transfer experiment

The [prospective plan](PLAN.md) defines the comparisons and limits. The initial
protocol and implementation were committed as `2eb3ea9` before new authoring results.
`progress.json` and [the notebook](NOTES.md) track execution; the plan itself stays
unchanged so its registered hash remains useful.

## Recompute recorded results

Once the evidence bundle is present, run from the repository root:

```sh
python3 docs/policy-transfer/reproduce.py --bundle published_runs/2026-10-25-policy-transfer
```

This needs Python and the standard library, no GPU, API key, or gated source text.
It checks compressed and decompressed prediction hashes, verifies completeness,
recomputes every metric, checks source and recipient policy selection, and reproduces
the accuracy matrices and paired intervals. All model failures remain in the data.
The bundle includes the exact policies and input/source hashes. The raw requests,
responses, authoring traces, and gated source examples remain in a private archive.

## Repeat paid inference

Obtain your own authorized access to WildGuardMix and reconstruct the prior study's
samples using [its data reproduction instructions](../../published_runs/2026-10-24-wildguard/REPRODUCING.md).
Compare the resulting byte hashes with `evals/policy_transfer/registry.json`.
Use the recorded checkpoint revisions; changing a model or dataset revision is a
new experiment. Do not expose access tokens in command-line arguments or logs.

The runner expects a private state directory with:

- `data/fit.jsonl` and `data/validation.jsonl`: the registered 1024/512-row files.
- `baseline/<model-slug>-<split>/`: the original p0 manifest, policy, summary, and
  predictions, whose exact hashes are registered. Public predictions can be
  decompressed from the evidence bundle. Historical runs are reused, not rerun.
- `checkpoints.json`: for each registered model slug, its `model`, `revision`, and
  local snapshot `path`. PolicyLM's snapshot includes its pinned inference helper.

The provided orchestrator assumes an isolated Linux GPU host with the repository at
`/root/safeguard-eval`, vLLM installed in `/root/vllmenv`, and the native PolicyLM
dependencies in `/root/policyenv`. The environment captures identify the exact
versions. The bootstrap uses vLLM 0.31.0, SentencePiece 0.2.2 and protobuf 7.36.2;
PolicyLM uses transformers 4.57.6, huggingface_hub 0.36.2 and torch 2.11.0+cu128.
Local snapshots are served offline, bound to 127.0.0.1. Qwen uses text input only.
Paths are operational assumptions; adapt them explicitly for a different host.

```sh
python -m evals.policy_transfer.orchestrate --state /root/transfer-state --phase author
python -m evals.policy_transfer.orchestrate --state /root/transfer-state --phase search
python -m evals.policy_transfer.orchestrate --state /root/transfer-state --phase transfer
```

The author phase produces 20 drafts and private traces. Search scores all candidates
and records source winners. Transfer scores the winner pool on validation, then
creates `freeze.json`. Verify and archive that freeze before placing the registered
`audit.jsonl` and `test.jsonl` into the state directory. Then run:

```sh
python -m evals.policy_transfer.orchestrate --state /root/transfer-state --phase final
python -m evals.policy_transfer.analyze --state /root/transfer-state --out /tmp/transfer-analysis.json
```

Completed runs can be reused only when their inputs, implementations, settings and
complete populations still match. Partial run directories are not silently resumed
or overwritten. A repair or changed environment must be documented as a separate
attempt. The run index distinguishes reused historical baselines from new inference.

Always provision within an explicit budget and configure termination before starting
work. Collect and verify artifacts, terminate the instance, and reconcile provider
billing. GPU.ai was selected for this execution because it had capacity; RunPod is
an authorized fallback under the same cumulative spending limit. Provider account
credit is separate from the user's spending authorization.

Greedy decoding does not promise bit-identical results after hardware, batching or
runtime changes. The CPU reproduction verifies the recorded experiment exactly;
repeating GPU inference is a replication with possible numerical variation.
