# Reproduce the code-embedding study

The [plan](PLAN.md) defines the complete search. These commands use a private
state directory: raw artifact text, features and learned weights do not belong
in Git. Restore the original artifact inputs with the previous study's
[restoration script](../../scripts/restore_malicious_artifacts_inputs.py), and
provide its unchanged policies and registration/freeze files as the prior state.
Do not execute or install the restored artifacts.

```sh
python -m evals.artifact_representations.study register \
  --state /private/new-study --prior /private/prior-artifact-state

python -m evals.artifact_representations.embeddings \
  --state /private/new-study --slug jina-v2 --split development
python -m evals.artifact_representations.embeddings \
  --state /private/new-study --slug jina-code --split development

python -m evals.artifact_representations.heads \
  --state /private/new-study --slug jina-v2 --split validation
python -m evals.artifact_representations.heads \
  --state /private/new-study --slug jina-code --split validation

python -m evals.artifact_representations.qwen \
  --state /private/new-study --slug qwen4 --split validation
python -m evals.artifact_representations.qwen \
  --state /private/new-study --slug qwen9 --split validation

python -m evals.artifact_representations.study freeze --state /private/new-study
```

Only after saving the freeze should test inputs be released to the GPU host.
Run embedding extraction with `--split test`, then the two head commands and
two Qwen commands with `--split test`. Each test command verifies registration,
source hashes and selected evidence. Restored heads must reproduce their stored
validation scores before classifying test items.

```sh
python -m evals.artifact_representations.report \
  --state /private/new-study --prior /private/prior-artifact-state
```

The published prediction bundle supports reporting without model execution via
`--public`; this bypasses raw-input/weight verification, not prediction alignment.
Model and remote-code revisions are pinned in `common.py`. Runtime package
versions, hardware, spending and termination evidence accompany completed runs.
The budget file is a record of this study's authorization, not permission for
someone else's agent to rent hardware. Set a new explicit budget for replication.

The completed [public bundle](../../published_runs/2026-11-03-artifact-representations/README.md)
contains the two metric-only reproduction commands. A separate
[vector stability diagnostic](../../scripts/audit_artifact_vectors.py) was added
after the negative skill results, using 16 fixed-hash validation items per task
and representation. It reloads each model and compares single-item vectors with
the original stored batch-four features. It never refits a head, changes a
selection, or edits predictions. Run it in the model's recorded runtime with
`--state /private/new-study --slug jina-v2` (or `jina-code`).
