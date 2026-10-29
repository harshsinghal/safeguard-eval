# Jev benchmark extension

The follow-up [Kev and Clef experiment](../decision-models/README.md) is complete:
two open decision models, the same benchmark populations, three policy variants
per model/task, and validation-selected cutoffs. The
[expanded leaderboard](../../published_runs/2026-10-29-leaderboard-decision-models/README.md)
keeps Jev's prior results unchanged.

Follow-up: the [balanced leaderboard](../leaderboard/README.md) compares the
archived configurations under common validation objectives. A separate
[architecture and local-model review](../research-directions/JEV-AND-LOCAL-DECISION-MODELS.md)
records what is documented about Jev and possible next experiments.

Status: complete. **Jev was competitive, while wording and thresholds still
changed its mistakes.** The selected policy scored 90.17% on WildGuardTest and
75.16% on HateXplain using native choices. Validation-selected thresholds changed
those scores to 89.94% and 80.67% respectively. On HateXplain, the higher accuracy
came with substantially lower hate-speech recall.

Start with the [plain-language readout](READOUT.md). The [full results](RESULTS.md)
separate policy edits from threshold tuning; [policy changes](POLICY-CHANGES.md)
describe exactly what was added. The [plan](PLAN.md), [notes](NOTES.md), and
[evidence archive](../../published_runs/2026-10-29-jev/README.md) preserve the
procedure and reproduction instructions.

- [x] Record the student curriculum for later.
- [x] Identify the native Jev interface and verify OpenRouter access.
- [x] Define the bounded policy and threshold comparison before inference.
- [x] Verify the existing data and prepare the evaluation harness.
- [x] Run fitting and validation; freeze both tasks.
- [x] Evaluate the frozen test populations.
- [x] Compare and document results; reconcile costs.
- [x] Reproduce metrics, validation choices, intervals, and billing from the archive on CPU.

The run used OpenRouter's Decisions API with the resolved model
`typesafe/jev-1.14-20261014`. **22,261 benchmark classifications cost $0.424208**
including the separate connectivity check; no GPU rental. Tests were reused from
earlier studies, and the comparison does not isolate architecture or establish a
universal winner. No language-model weights were changed.
