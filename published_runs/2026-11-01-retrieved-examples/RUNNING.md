# Reproduce the retrieved-example comparison

## Recompute published numbers without inference

The public verifier needs Python 3.9+
and NumPy (the recorded analysis used 2.0.2). It checks file hashes and recomputes
validation selections, test metrics and paired intervals from saved predictions.
No API credentials, model download or source dataset text is needed:

```bash
python3 tools/verify_retrieved_examples.py --archive published_runs/2026-11-01-retrieved-examples
```

## Rerun inference with restored source data

Install the repository's research dependencies in a fresh environment. Retrieval
uses NumPy, PyTorch, Transformers and Hugging Face Hub. Native runtimes preserve
the earlier pinned PolicyLM and Kev dependency environments; Shieldstral uses
Transformers' native text forward path and canonical yes/no label logits.

The completed compatibility checks require single-request PolicyLM and
Shieldstral execution. The native PolicyLM schema also requires single-line
category fields; the renderer uses spaces between examples for that model.
These technical amendments and their rejected attempts are recorded in
[the notes](NOTES.md). Exact dependency locks will accompany the run archive;
Kev needs Pydantic in addition to Torch, Transformers, PEFT and its fused kernels.

| Model | Where examples go | Where the target goes | Decision rule |
|---|---|---|---|
| PolicyLM | Single-line `exception_override`, after existing exceptions | Native message input | BLOCK score at least 0.5 |
| Shieldstral | `Instruct`, after existing policy clauses | `Document`; the yes/no `Query` is unchanged | Normalized yes/no BLOCK score at least 0.5 |
| Kev | Native Choice question's `instructions` | `state.content` | Native argmax, with ALLOW first on ties |
| Jev | Native Choice question's `instructions` | `state.content` | API's returned choice |

Each demonstration serializes only `example_content` and its training `label`.
An explicit prefix says the examples are data, not instructions, and the policy
remains authoritative. Angle and bracket characters inside examples are escaped
to avoid turning a training prompt into a tokenizer control delimiter. The target
is never concatenated with the demonstrations in the content field. PolicyLM's
category-field examples are an experimental conditioning format, not an official
few-shot API. The same four examples are used across models for a given condition
and target; their native wrappers differ.

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
python -m evals.retrieved_examples.native --state /private/new-study --model shieldstral --batch-size 1 --split smoke
python -m evals.retrieved_examples.native --state /private/new-study --model shieldstral --batch-size 1 --split validation
python -m evals.retrieved_examples.native --state /private/new-study --model kev --vendor /private/decision-vendor --split smoke
python -m evals.retrieved_examples.native --state /private/new-study --model kev --vendor /private/decision-vendor --split validation
```

The API path reads a credential file without printing its contents. The cap is a
study-wide reservation limit, not permission to spend; ensure it fits an explicitly
authorized remaining budget. Unknown charges remain reserved and stop further
requests until reconciled. Each target/condition is an independent Choice request.

```bash
python -m evals.retrieved_examples.jev --state /private/new-study --split smoke --keyfile /private/keys/openrouter --cap 1.00
python -m evals.retrieved_examples.jev --state /private/new-study --split validation --keyfile /private/keys/openrouter --cap 1.00
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
amendments. The [published archive](../../published_runs/2026-11-01-retrieved-examples/README.md) contains the exact source and runtime locks.

The optional figure uses Matplotlib 3.9.4 and the archived results; it makes no
inference calls:

```bash
python3 tools/plot_retrieved_examples.py --results published_runs/2026-11-01-retrieved-examples/results.json --output /tmp/retrieval-accuracy.png
```
