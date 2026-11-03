# Reproduce the artifact-screening study

Start with [methods and limitations](METHODS.md) and the [registered plan](PLAN.md).
The public evidence bundle contains labels, IDs, hashes, policies, selections and
predictions. It excludes artifact text, model weights, credentials and private
infrastructure details.

## Recalculate without models or downloads

Use Python 3.12 and install the numerical dependencies recorded in the bundle's
`runtime/local-environment.json`. From the repository root:

```sh
python scripts/reproduce_malicious_artifacts.py --run published_runs/2026-11-03-malicious-artifacts
python scripts/verify_malicious_artifacts_metrics.py --run published_runs/2026-11-03-malicious-artifacts
```

This checks the release manifest and reruns the reporting pipeline
in a temporary directory. It makes no inference calls and does not download or
execute benchmark artifacts. Results are compared with the published JSON.
The second command independently checks the test metrics with scikit-learn and
direct error counts, including the brief-policy controls and record alignment.

## Restore the exact input populations

Restoration additionally needs PyArrow. Choose a new directory outside Git:

```sh
python scripts/restore_malicious_artifacts_inputs.py \
  --run published_runs/2026-11-03-malicious-artifacts \
  --output /absolute/path/to/new-artifact-inputs
```

This downloads pinned public snapshots, reads regular archive members in memory,
verifies source hashes, recreates grouping and deterministic sampling, and checks
all input/metadata hashes against registration. It does not install or execute
the downloaded code or skills. The source archives contain malicious artifacts;
keep them as research data rather than installing them as dependencies.

## Run new inference or training

Treat this as a separate, budgeted run. Inspect the model cards and dependency
versions in `runtime/`. Native PolicyLM, Shieldstral, Kev, Clef and the encoder
do not all share one compatible runtime. Kev and Clef also need the pinned
publisher code verified by `evals/decision_models/vendor-hashes.json`.

The execution sequence is:

1. Prepare data and task policies. Register immutable hashes and spending limits.
2. Run the three policy candidates on validation through each model's native
   adapter. Fit the TF-IDF and Liquid candidates using fitting examples only.
3. Freeze **all** model selections and learned artifacts before releasing test
   inputs. `evals.malicious_artifacts.study freeze` rejects incomplete evidence.
4. Run brief and selected policies on the same test records; use only the
   validation-selected trained classifiers. Keep failures in the report.
5. Collect outputs and selected checkpoints, reconcile API/GPU spending, and
   terminate the GPU. Preserve the original run when making changes.

Modules: [data](../../evals/malicious_artifacts/data.py),
[policies](../../evals/malicious_artifacts/policies.py),
[native/API inference](../../evals/malicious_artifacts/infer.py),
[trained baselines](../../evals/malicious_artifacts/learned.py),
[selection](../../evals/malicious_artifacts/study.py),
[reporting](../../evals/malicious_artifacts/report.py).

The public release is sufficient to verify the recorded decisions and metrics.
Its supplementary source audit includes five transitive adapter dependencies
outside the explicit registration list. Their local and GPU hashes were checked
against pre-test Git commit `e75f593`; no dependency changed during the run.
Fresh GPU execution also requires restoring inputs, installing the recorded
runtimes and supplying credentials where appropriate. Hosted Jev's resolved
version is recorded but is not an immutable checkpoint we can redistribute.
The fine-tuned encoder weights are retained privately in lossless gzip files;
their recorded hashes refer to the original checkpoint bytes. Rerunning training may
produce small hardware/runtime differences despite the recorded seed.
