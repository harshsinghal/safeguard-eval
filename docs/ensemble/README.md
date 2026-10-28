# Can a panel of policy models make better decisions?

The ensemble experiment is complete. **Combining models did not consistently improve on a calibrated individual model.** An equal average was promising on WildGuardTest. On HateXplain, the specialist ensemble fell short, while adding Qwen produced only a small, uncertain accuracy gain.

Start with the [plain-language readout](READOUT.md). The [full results](RESULTS.md) show every registered method family, error counts, uncertainty, learned weights and individual-model controls. The [evidence package](../../published_runs/2026-10-27-ensemble/README.md) includes all candidate results and a CPU reproduction command.

The [original plan](PLAN.md) remains unchanged so its registered hash can be checked. The completed checklist is below; [notes](NOTES.md) and [machine-readable progress](progress.json) record execution.

- [x] Audit cached scores and exclude earlier policy-development groups.
- [x] Prepare and hash 4,096 fitting and 1,536 validation examples per benchmark.
- [x] Implement score alignment, calibration, weighted averaging, logistic regression and random forest.
- [x] Score missing HateXplain development examples with pinned checkpoints and policies.
- [x] Freeze all three cohorts before evaluating the official tests.
- [x] Evaluate 1,699 WildGuardTest prompts and 1,924 HateXplain posts, retaining all methods.
- [x] Package prompt-free evidence and explain the outcomes.
- [x] Refit and reproduce all metrics and intervals on CPU.
- [x] Terminate compute and reconcile billing: $0.38; cumulative $12.50 of $20.

No language-model weights or policies were changed for this study. The trained components are small supervised combiners and score calibrators. Official tests were reused from earlier work, so these results are exploratory. This study evaluates binary ALLOW/BLOCK classification, not REVIEW routing.
