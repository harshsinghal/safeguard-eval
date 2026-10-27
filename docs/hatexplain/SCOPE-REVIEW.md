# Policy eligibility review before validation

Review by the coordinating Codex assistant; AI-assisted, not independent human adjudication. No validation or test results were inspected.

- **p0 — eligible:** Registered complete reference policy; dataset mapping and fixed scope reviewed.
- **policylm-p1 — excluded:** Defines normal as non-offensive but includes profanity and personal insults, and replaces the instruction against assuming missing context. Does not faithfully preserve the original definitions and context constraint.
- **policylm-p2 — excluded:** Same substantive text as rejected PolicyLM p1; retains its contradictory definition and missing context constraint.
- **shieldstral-p1 — eligible:** Punctuation changes only; all intended rules, exceptions, covered groups and examples retained. Same substantive text as Qwen p1.
- **shieldstral-p2 — eligible:** Adds a clarification that context distinguishes an identity attack from a descriptor or unrelated insult. Retains the original identity groups, prohibitions, exceptions, examples and instruction not to assume missing context.
- **qwen-4b-p1 — eligible:** Punctuation changes only; intended scope and all substantive clauses retained. Same substantive text as Shieldstral p1.
- **qwen-4b-p2 — excluded:** Exact substantive duplicate of Qwen p1. Exclude from selection so a second stochastic measurement of the same input cannot win by chance.

Qwen p1 and Shieldstral p1 converge to the same punctuation edits. This limits the diversity of the transfer pool. If both win source selection, duplicate transfer runs will be reported as replicas. The original plan preferred deduplication; preserving separate source IDs in the fixed runner is an implementation deviation, not independent evidence for two different policies.
