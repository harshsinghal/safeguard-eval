# Reproduction and progress

## Progress

- [x] Pin sources and official model checkpoints.
- [x] Audit eligibility, exact/near duplicates, template and author grouping.
- [x] Implement native interfaces, paired input views and learned controls.
- [x] Check input/cache contracts and label-free model payloads.
- [ ] Publish registration; run validation within the existing $6 cap.
- [ ] Publish validation selection before test inference.
- [ ] Run test, independently check metrics, publish failures and limits.
- [ ] Reconcile provider/API charges; verify resource termination.

## Local verification

Use Python 3.12 with numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1 and joblib.

```sh
python -m unittest evals.cyber_skill_guardrails.test_contracts
python -m evals.cyber_skill_guardrails.report --state RUN_DIRECTORY --public
```

The second command requires the final public prediction bundle. Public reproduction
does not require raw benchmark text, model downloads or an API key.

To restore inference inputs, check out the two upstream revisions in PLAN.md.
Save the MITRE augmented JSON as mitre.json and MITRE FRR JSON as frr.json in a
private directory. Clone MalSkillBench without installing anything. Keep the public
registration, metadata and package manifest in RUN_DIRECTORY, then run:

```sh
python -m evals.cyber_skill_guardrails.restore --state RUN_DIRECTORY \
  --checkout MALSKILLBENCH_CHECKOUT --cyber-sources PRIVATE_CYBER_DIRECTORY
```

Restoration checks every package Git blob and every final input hash. Respect the
upstream license; raw skill text and model weights are excluded from this repository.

Paid reruns require a new explicit budget. Use provider termination limits, log
unknown API charges conservatively, and stop resources after collecting evidence.
Models use separate compatible environments; dependency snapshots accompany results.
