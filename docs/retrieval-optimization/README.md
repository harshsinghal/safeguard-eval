# Making retrieved examples useful to each moderation model

**Status: registered; execution in progress.** No new accuracy result is available
yet. This follows the [first retrieval study](../retrieved-examples/README.md),
which found modest uncertain gains for decision models and regressions for the
two specialists.

The sequence separates four questions: where examples belong in each native
interface; whether stronger embeddings find better cases; whether a reranker,
diversity or a relevance gate improves selection; and whether a larger fitting
library helps. It keeps model weights and output cutoffs fixed. Policy-only
remains an eligible final selection.

See the [registered plan](PLAN.md), [registration hashes](registration.json), and
[research notes](NOTES.md). All choices use training/validation data before a
published freeze. Final scores will concern the same reused WildGuardTest and
will be identified as exploratory.
