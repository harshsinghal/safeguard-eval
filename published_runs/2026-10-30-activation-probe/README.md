# Frozen-representation classifier study

[Readable findings](READOUT.md) · [Protocol](PLAN.md) · [All metrics](test-results.json) ·
[CSV](results.csv) · [Implementation notes](NOTES.md) · [Reproduction guide](RUNNING.md)

This immutable bundle tests Qwen3.5-0.8B and PolicyLM-1.7B representations on
WildGuard prompt harmfulness. The primary method concatenates their final-layer
features before supervised logistic regression. A separately registered secondary
search chooses earlier layers/pooling on validation. Language-model weights and
policy text stay frozen; the small classifiers are trained with labels.

The bundle includes all validation candidates, the pre-test freeze, fitted
coefficients/scalers, selected test outputs, operating profiles, confidence
intervals, source and runtime records. It contains no source prompts or pooled
embedding vectors. Restore authorized source inputs with the supplied utility
and regenerate private features to repeat fitting.

From this directory, with the listed CPU dependencies:

```sh
PYTHONPATH=source python3 -m evals.activation_probe.study reproduce --state .
PYTHONPATH=source python3 source/tools/verify_activation_probe.py --state .
```

These commands check saved outputs without GPU inference. The original private
cache also reproduced every candidate fit with identical coefficients and
validation probabilities; see `refit-reproduction.json`. Full inference can
differ numerically across hardware/library versions. Match the recorded runtime
when attempting to regenerate features.

`feature-provenance/` records feature hashes, identities and runtime measurements;
it is not the feature cache. `source/runtime/policylm-development-extract.py`
preserves the earlier extractor used for PolicyLM development before the
Qwen-only empty-input amendment; the corresponding original plan is alongside it.
The final extractor has the same PolicyLM path.
Published benchmark test results had been examined before this follow-up; its
new pre-test freeze does not make the public test a pristine blind evaluation.

The historical WildGuard and specialist-score-ensemble controls use the same
test prompts but their prior validation selections. They are context, not an
equal-search-budget causal comparison. This study has its own 1,536-row
validation protocol and is separate from the common-validation leaderboard.

Compute was terminated and billing reconciled; see [billing](billing.json).
Model and dataset references are in the protocol. Their publishers' terms remain
applicable. Checksums cover all immutable files except the checksum file itself.
