# Reproduce the retrieved-example comparison

Install the repository's research dependencies in a fresh environment. Retrieval
uses NumPy, PyTorch, Transformers and Hugging Face Hub. Native runtimes preserve
the earlier pinned PolicyLM and Kev dependency environments; Shieldstral uses
Transformers' native text forward path and canonical yes/no label logits.

Restore the licensed WildGuard text using the existing contrastive-head study's
data manifests. Do not put source prompts or embeddings in a public repository.
Preparation verifies that study's data hashes and group separation. The following
paths are placeholders for private local directories:

```bash
python -m pytest tests/test_retrieved_examples.py -q
python -m evals.retrieved_examples.prepare --state /private/new-study --prior /private/contrastive-heads-state
python -m evals.retrieved_examples.retrieve --state /private/new-study --split smoke
python -m evals.retrieved_examples.retrieve --state /private/new-study --split validation
```

The registration includes exact model revisions, code hashes, policy hashes,
dataset identities, eligible bank membership and fixed-example IDs. Retrieval
manifests save neighbor IDs and cosine similarities. Private job files contain
only the target text and its model-specific policy, with fitting demonstrations.
They contain no target labels, category metadata or assistant responses.

On a disposable GPU with pinned native runtime and reviewed Kev source:

```bash
python -m evals.retrieved_examples.native --state /private/new-study --model policylm --split smoke
python -m evals.retrieved_examples.native --state /private/new-study --model policylm --split validation
python -m evals.retrieved_examples.native --state /private/new-study --model shieldstral --split smoke
python -m evals.retrieved_examples.native --state /private/new-study --model shieldstral --split validation
python -m evals.retrieved_examples.native --state /private/new-study --model kev --vendor /private/decision-vendor --split smoke
python -m evals.retrieved_examples.native --state /private/new-study --model kev --vendor /private/decision-vendor --split validation
```

The API path reads a credential file without printing its contents. The cap is a
study-wide reservation limit, not permission to spend; ensure it fits an explicitly
authorized remaining budget. Unknown charges remain reserved and stop further
requests until reconciled. Each target/condition is an independent Choice request.

```bash
python -m evals.retrieved_examples.jev --state /private/new-study --split smoke --keyfile /private/keys/openrouter --cap 0.60
python -m evals.retrieved_examples.jev --state /private/new-study --split validation --keyfile /private/keys/openrouter --cap 0.60
python -m evals.retrieved_examples.report freeze --state /private/new-study
python -m evals.retrieved_examples.retrieve --state /private/new-study --split test
```

Then run each model with `--split test` and the identical runtime/decision rule.
The evaluator requires every expected ID and condition; missing results are not
silently discarded. It reconstructs all metrics and paired group-bootstrap
intervals from predictions:

```bash
python -m evals.retrieved_examples.report evaluate --state /private/new-study
```

Export evidence before terminating the GPU; verify provider-side termination and
reconcile billed usage. Publish only prompt-free manifests, retrieval records,
predictions, source snapshots and results. Preserve failed attempts and technical
amendments. A published archive will be linked here when inference is complete.
