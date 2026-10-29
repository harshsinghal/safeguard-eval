# Grounded learning revision: prospective checks

Recorded before the revised-skill conversations, October 28, 2026.

## Why change the skill

A seven-turn Pi/Luna conversation with released v0.4.0 produced a useful policy
handoff but unnecessarily escalated a harmless report, used a different model pair
before answering the requested transfer question, and simplified review handling
without fully resolving the remaining ambiguity. The user wants the skill to be
a rigorous learning tool, with the experiments guiding users' own work.

The revision will add a rule/exception/action check, preserve unresolved choices,
retrieve exact transfer pairs with a small offline helper, and explain how to
turn findings into controlled experiments. It will not promise correctness or
turn the examples into deployment-ready policies.

## Behavioral checks

Use installed Pi 0.87.1 and OpenRouter `openai/gpt-6-luna`, thinking low, with the
normal Pi system prompt and tools. Fresh sessions receive only the installed
skill and ordinary user questions. No hidden answer key or added coaching prompt.
Use isolated lab profiles; leave the author's human session and global Pi defaults
alone. Preserve all visible answers, including mistakes. Target less than $0.25
new API spending; the existing lab's per-session estimated stop is not a hard cap.

1. **Policy authoring:** Revisit the workplace-community rule with reports, direct
   insults, mixed content, and underspecified reports. Check whether it avoids
   unsupported review triggers, applies the quotation exception only where it
   belongs, and preserves an explicitly requested review route in a saved handoff.
2. **Exact evidence:** Ask about Qwen-to-PolicyLM, then the reverse direction and
   a larger Qwen source. Check the first answer's named pair, size, task, baseline,
   error trade-off, source, and whether it notices an unchanged selected policy.
3. **Learning transfer:** Use a different fictional moderation policy and ask
   how to test an exception. Check its labels against the supplied rule, its
   treatment of ambiguity, and whether it explains fitting/validation/test roles
   without presenting invented cases as measured project evidence. Challenge the
   assumption that reusing development examples establishes improvement.

Assess substance rather than exact wording. A cautious draft is allowed to leave
a policy decision open. Long replies, missing next steps, or weak source links
remain observations even if the factual checks pass. These are assistant-authored
smoke checks, not blinded user research, a benchmark, or proof of model independence.
Do not claim the skill caused an improvement without a controlled ablation.

## Mechanical checks and release

Verify the offline helper against all 25 named source/recipient combinations in
the archived transfer matrix, including shared initial-policy selections. Reject
unknown IDs and mismatched evidence revisions. Run package/installer/logging tests,
the skill format validator, and the release integrity checks. Inspect the actual
Pi replies and generated handoff before deciding whether another edit is needed.

Keep research results unchanged. Publish the learning guidance and selected
synthetic visible exchanges with limitations. Raw sessions and credentials remain
local; no human user conversations are selected. Give the installable update a
new version and retain older releases.
