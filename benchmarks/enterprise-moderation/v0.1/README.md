# Enterprise Moderation Suite candidate v0.1

983 evaluation cases, 192 calibration cases, 14 tasks from 13 sources.

[Methods, scoring equation and usage](../../../docs/enterprise-benchmark/README.md) · [Assembly evidence](assembly-report.json) · [Coverage](coverage.json) · [Review queue](review-queue.jsonl)

| Task | Evaluation | Calibration | Reference classes |
|---|---:|---:|---|
| Harmful user requests | 63 | 16 | ALLOW, BLOCK |
| Hate versus offensive/normal speech | 63 | 16 | ALLOW, BLOCK |
| Deepset instruction-boundary attacks | 62 | 16 | ALLOW, BLOCK |
| xTRam1 injection collection | 62 | 16 | ALLOW, BLOCK |
| Benign injection lookalikes | 63 | 0 | ALLOW |
| Released jailbreak-attempt detection | 62 | 0 | BLOCK |
| Injection/context ambiguity | 61 | 16 | ALLOW, BLOCK, REVIEW |
| Static source-file screening | 62 | 16 | ALLOW, BLOCK |
| Static agent-skill text | 62 | 16 | ALLOW, BLOCK |
| Complete textual skill packages | 62 | 16 | ALLOW, BLOCK |
| Cyber abuse versus legitimate administration | 63 | 16 | ALLOW, BLOCK |
| Pending agent actions in context | 125 | 16 | ALLOW, BLOCK |
| Completed agent-run audits | 125 | 16 | ALLOW, BLOCK |
| Configurable image-prompt policy | 48 | 16 | ALLOW, BLOCK, REVIEW |

Model-facing IDs are opaque. Full source inputs and embeddings are private; this bundle contains case metadata, reference labels, policies, weights, provenance and audits.

This is a source-label candidate awaiting independent review, not a validated enterprise-incident test. No moderation model or quantization/runtime sweep has run. Both score profiles, case identities and policies are versioned before model evaluation.
