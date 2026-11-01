# Reproduce the staged retrieval study

## Recompute published results on CPU

The final public archive contains predictions, neighbor IDs and scores, selection
records, model revisions, source snapshots and checksums. It excludes dataset
text, vectors, request bodies and credentials. With Python 3.9+ and NumPy:

```bash
python3 tools/verify_retrieval_optimization.py --archive published_runs/2026-11-01-retrieval-optimization
```

The verifier checks artifact hashes, reconstructs both intermediate selections
and the final freeze, then reproduces final metrics and paired uncertainty. It
does not call inference providers or download models. It also reproduces the
validation retrieval/window diagnostics. The recorded local analysis used NumPy
2.0.2; an independent metric check used scikit-learn 1.6.1.

## Repeat inference with restored licensed data

Restore the earlier retrieved-example private state from its dataset manifests.
Keep each study in a separate directory. Example paths below are placeholders:

```bash
python3 -m pytest tests/test_retrieval_optimization.py -q
python3 -m evals.retrieval_optimization.study prepare --state /private/new-study --prior /private/prior-retrieval-state
```

Preparation pins the 4,096/1,536/1,699 populations, copies unchanged policies and
eligible exact-request caches, and registers source and data hashes. Test source
inputs may be held locally, but are not sent to development compute. No new test
feature or request is produced before the final freeze. Existing test use is
disclosed in the plan; this does not create a fresh holdout.

Use the archived runtime locks. PolicyLM and the embedding/reranking code use
the PolicyLM environment; Shieldstral and Kev use the Kev environment. The latter
needs the pinned and reviewed decision-model vendor source, Pydantic and its
native fused kernels. The earlier model adapters are reused unchanged.

All three self-hosted classifiers run one request at a time in this study.
Kev's fitting-only check rejected batch eight under the registered score-parity
tolerance, so its earlier batched predictions are excluded from reuse. Its
controls are recomputed serially. The [notes](NOTES.md) preserve this amendment,
the earlier Jev cache-variation check and bounded transport retries. The original
plan remains unchanged as a record of what was registered first.

Both example layouts use the model's native interface. The `native` configuration
name means our alternate labeled-case rendering; it does not mean that the
publisher has certified a few-shot recipe. For PolicyLM it puts BLOCK cases in
`violation_rule` and ALLOW cases in `not_violation_rule`, leaving
`exception_override` unchanged. The original JSON suffix uses that last field.
For Shieldstral both layouts use `Instruct`; for Kev and Jev both use Choice
`instructions`. The target remains in its separate content field in every arm.

First, construct development features and the formatting jobs. Repeat each
command for `smoke` and `validation`, in that order:

```bash
python -m evals.retrieval_optimization.features encode --state /private/new-study --split smoke
python -m evals.retrieval_optimization.study jobs --state /private/new-study --stage format --split smoke
python -m evals.retrieval_optimization.infer --state /private/new-study --stage format --split smoke --model policylm
python -m evals.retrieval_optimization.infer --state /private/new-study --stage format --split smoke --model shieldstral
python -m evals.retrieval_optimization.infer --state /private/new-study --stage format --split smoke --model kev --vendor /private/reviewed-vendor
python -m evals.retrieval_optimization.infer --state /private/new-study --stage format --split smoke --model jev --keyfile /private/keys/openrouter --cap 2
```

Jev calls can run on the local controller so its API key need not reach the GPU.
The durable request ledger reserves costs before sending and stops on an
unreconciled failure. A command-line cap is not spending authorization. GPU and
API charges must fit the authorized combined limit, including all failed attempts.

After all four validation populations are complete, select the format, then
construct and execute retriever-stage jobs with the same inference command:

```bash
python -m evals.retrieval_optimization.study select --state /private/new-study --stage format
python -m evals.retrieval_optimization.study jobs --state /private/new-study --stage retriever --split validation
# Run all four models for smoke and validation under stage retriever, then:
python -m evals.retrieval_optimization.study select --state /private/new-study --stage retriever
```

For selector jobs, first rerank each selected retriever's 20-candidate pools:

```bash
python -m evals.retrieval_optimization.features rerank --state /private/new-study --split validation
python -m evals.retrieval_optimization.study jobs --state /private/new-study --stage selector --split validation
python -m evals.retrieval_optimization.study jobs --state /private/new-study --stage coverage --split validation
```

Again produce corresponding fitting smoke jobs and execute all four models in
each stage before finalizing selection. The coverage stage changes only the
training library for two-nearest examples. Exact duplicate requests are cached,
with their origin recorded; aliases are not treated as independent observations.

Freeze and publish all selections before restoring test inputs and the original
test E5 vectors/exact-request caches to the evaluation worker:

```bash
python -m evals.retrieval_optimization.study freeze --state /private/new-study
python -m evals.retrieval_optimization.features encode --state /private/new-study --split test
python -m evals.retrieval_optimization.features rerank --state /private/new-study --split test
python -m evals.retrieval_optimization.study jobs --state /private/new-study --stage test --split test
# Execute each model with --stage test --split test, then:
python -m evals.retrieval_optimization.study evaluate --state /private/new-study
```

Restore original test caches only after checking their prior manifest hashes.
Workers also need the exact validation predictions, job manifests and intermediate
selection files referenced by the freeze. Any unsupported context or schema
stops execution; preserve the failure and document a technical amendment before
continuing. Never silently truncate inputs or discard missing predictions.

Collect artifacts, terminate rented compute, reconcile usage and confirm cleanup
before publishing the final archive. Preserve failed attempts in the study notes.

The optional chart uses Matplotlib (recorded version 3.9.4) and saved metrics:

```bash
python3 tools/plot_retrieval_optimization.py --results published_runs/2026-11-01-retrieval-optimization/results.json --output /tmp/retrieval-optimization.png
```
