# Code embeddings and Qwen: frozen artifact experiment

This bundle records the registered follow-up on the original source-file and
agent-skill splits. [Readout](../../docs/artifact-representations/README.md),
[methods](../../docs/artifact-representations/METHODS.md),
[results](../../docs/artifact-representations/RESULTS.md).

The four Jina systems are task-trained heads on frozen embeddings. Qwen 4B/9B
select among six policies. All choices were frozen before new test inference;
the first registered neural seed is primary and all three are retained.

Raw benchmark text, embeddings, learned weights, credentials and private
infrastructure identifiers are excluded. Compact features and selected heads
are retained privately with hashes in the freeze. Restore data through the
[original input restorer](../../scripts/restore_malicious_artifacts_inputs.py).
See [running instructions](../../docs/artifact-representations/RUNNING.md) for
model execution. No benchmark artifact should be executed or installed.

Reproduce reported metrics and grouped intervals without GPU or API calls:

```sh
python scripts/reproduce_artifact_representations.py \
  --run published_runs/2026-11-03-artifact-representations
python scripts/verify_artifact_representations_metrics.py \
  --run published_runs/2026-11-03-artifact-representations
```

These commands require NumPy, SciPy and scikit-learn. The first verifies this
bundle and the prior reference bundle, then computes into a temporary directory.
The second independently checks every final arm against labels and direct
confusion counts. Model revisions, runtime versions, budget and cleanup are
recorded here. Earlier frozen studies remain unchanged.
