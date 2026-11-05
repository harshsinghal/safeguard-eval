# StepGuard native-model evaluation

See the [registered protocol](../../docs/security-cognition/STEPGUARD-RUN-PLAN.md).
This evaluates **recorded behavior**, not whether the topic or user request is
harmful. The pending-action and completed-run tasks have different scopes.
Dataset text and reference rationales stay outside the repository. Never execute
the commands contained in an input record.

```sh
python -m evals.stepguard.data --state /private/stepguard-state
# Count native representations without loading weights. PolicyLM needs
# transformers==4.57.6; the other tokenizers used transformers==5.10.2.
/path/to/policyenv/bin/python -m evals.stepguard.preflight --state /private/stepguard-state --vendor /private/vendor --models policylm
/path/to/generalenv/bin/python -m evals.stepguard.preflight --state /private/stepguard-state --vendor /private/vendor --models shieldstral safeguard jev kev clef
python -m unittest evals.stepguard.test_contracts
python -m evals.stepguard.study register --state /private/stepguard-state
# Repeat in the appropriate native runtime for each model. Jev also requires
# --keyfile /private/openrouter-key-file; Safeguard uses a loopback vLLM server.
python -m evals.stepguard.infer --state /private/stepguard-state --model shieldstral --split validation --vendor /private/vendor
# Only after every model/task has complete validation predictions:
python -m evals.stepguard.study freeze --state /private/stepguard-state
python -m evals.stepguard.infer --state /private/stepguard-state --model shieldstral --split test --vendor /private/vendor
python -m evals.stepguard.report summarize --state /private/stepguard-state
python -m evals.stepguard.report export --state /private/stepguard-state --destination reports/stepguard-native
```

The register command records this study's existing authorization; **it does not
grant a new user permission to spend money**. A reproducer must establish their
own budget and shutdown controls. Registering changed code creates a new study,
not a reproduction of the published run.

No score threshold is fitted. All three candidates run on validation; the
initial and validation-selected candidates run on test. Test jobs require the
selection freeze and matching source/file hashes. Native model-specific formats,
checkpoint revisions and parser contracts are inherited from audited adapters.

The complete-input cohort has 2,998/3,000 source records. Two validation records
exceed the conservative Jev request-byte ceiling. The matched PolicyLM cohort
has 551 records because its published helper uses 2,000-character windows in
addition to a shared token budget. Window aggregation would be another study.

Seven offline contract tests cover reference-label leakage, candidate outcome
leakage, duplicate grouping, cache identity, the test gate, unresolved outputs
and frozen-policy scheduling. Runtime token counts must match the preflight.
