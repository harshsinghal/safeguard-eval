# Kev and Clef decision-model evidence

Completed 29 October 2026. Read the [plain-language findings](../../docs/decision-models/README.md) and [expanded leaderboard](../2026-10-29-leaderboard-decision-models/README.md).

Both models ran with frozen weights through their native decision heads. Three policy variants per model and task were selected on validation before test inference. All 44,522 predictions are retained; zero outputs were unresolved. The GPU was terminated after $0.87 in recorded charges.

## Evidence map

- [Registered plan](PLAN.md), [registration and dataset hashes](registration.json), [validation selection freeze](freeze.json), and [run log](RUN-LOG.md).
- `policies/`: the three actual policies and provenance of the four fitting examples selected for each model/task. These example policies include quoted benchmark content that can be offensive.
- `predictions/`: compressed JSONL for both models, both tasks, and every stage/candidate. Raw input prompts are omitted; row IDs, labels, duplicate groups, input hashes, native decisions, logits, probabilities, token lengths and batch timings remain.
- [Policy contrasts](policy-contrasts.json): native and validation-threshold results, fitting summaries, and paired unadjusted group-bootstrap intervals. The tuned contrast changes both wording and cutoff.
- `kev/` and `clef/`: parity checks, policy freezes, and development/test runtime metadata. Exact installed dependencies are in [Kev's manifest](kev-freeze.txt) and [Clef's manifest](clef-freeze.txt).
- [Verification](verification.json), [billing](billing.json), and [termination](termination.json). API secrets, private SSH keys, and account credentials are excluded.
- `source/`: frozen study/adapter code and analysis code. [Pinned model-card references](model-card-references.json) and the source-hash manifest identify upstream releases.

## Reproduce

For CPU-only reproduction of selection and test metrics, use the [expanded leaderboard bundle](../2026-10-29-leaderboard-decision-models/README.md). It includes every normalized input needed; no model download or paid inference is required.

To repeat native GPU inference, use the repository's [inference guide](../../docs/decision-models/RUNNING.md). Reconstruct the existing hash-verified benchmark splits, inspect the pinned source, and use separate runtimes for the two models. The original run used BF16 on a 48GB RTX6000 Ada; this is not a minimum-memory or production-latency claim.

These public tests were previously used. Training exposure is incompletely known, earlier models had different search budgets, and the experiment does not establish a general architecture advantage. This bundle is a study archive, not a new model release.
