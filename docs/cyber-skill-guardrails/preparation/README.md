# Configurations frozen before test inference

Freeze timestamp: 2026-11-03T20:00:06.855719+00:00

Cyber uses the corrected base-request cohort (768 fitting / 254 validation / 330 test). Skills use 1,024 / 256 / 512. Every retained item stays in its original split. No test inference has begun at this publication.

| Task | System | Validation-selected configuration |
|---|---|---|
| cyber | policylm | contrasts |
| cyber | shieldstral | contrasts |
| cyber | kev | structured |
| cyber | clef | brief |
| cyber | jev | contrasts |
| cyber | qwen | brief |
| cyber | llamaguard | structured |
| cyber | promptguard | native |
| cyber | jina-v2-lr | C0.1 |
| cyber | jina-v2-mlp | h128-a0.01-e10 |
| skills | policylm | contrasts |
| skills | shieldstral | contrasts |
| skills | kev | structured |
| skills | clef | structured |
| skills | jev | structured |
| skills | qwen | contrasts |
| skills | llamaguard | contrasts |
| skills | promptguard | native |
| skills | jina-v2-lr | C0.1 |
| skills | jina-v2-mlp | h128-a0.01-e10 |
| skills | jina-v2-md-lr | C0.1 |
| skills | jina-v2-md-mlp | h256-a0.01-e10 |

The first neural seed is primary; all three registered seeds will be reported. Prompt Guard and the Llama Guard default taxonomy are fixed controls. The SKILL.md-only prompted comparison retains the same full-package-selected policy. Learned SKILL.md heads are selected independently from fitting/validation.

[Full validation scores](validation-summary.json) · [Evidence hashes](freeze.json) · [Registration and amendments](registration.json).
