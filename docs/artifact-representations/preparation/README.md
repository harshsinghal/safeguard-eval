# Choices frozen before test inference

The candidate search used fitting and validation only. Test data had not been released to the GPU host.

Freeze timestamp: 2026-11-03T16:25:56.723736+00:00

| Task | System | Selected configuration |
|---|---|---|
| code | qwen4 | brief |
| code | qwen9 | behavior |
| code | jina-v2-lr | C0.1 |
| code | jina-v2-mlp | h128-a0.01-e30 |
| code | jina-code-lr | C0.1 |
| code | jina-code-mlp | h128-a0.01-e30 |
| skills | qwen4 | scope |
| skills | qwen9 | contrasts |
| skills | jina-v2-lr | C0.1 |
| skills | jina-v2-mlp | h128-a0.01-e60 |
| skills | jina-code-lr | C10 |
| skills | jina-code-mlp | h256-a0.01-e30 |

For MLPs, configuration selection uses the three-seed mean validation score;
the first registered seed is the primary individual test classifier. The other
seeds are retained as sensitivity results. No test-selected seed or ensemble.

[Full validation scores](validation-summary.json) · [Frozen evidence hashes](freeze.json) · [Registration](registration.json)
