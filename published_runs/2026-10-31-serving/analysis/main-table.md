| Configured system | Runtime | One request: median | 32 in flight: valid requests/s | 32 in flight: p95 | GPU-only $/million |
|---|---|---:|---:|---:|---:|
| PolicyLM 1.7B | native; reference | 34.7 ms | 31.0 | 1127.4 ms | $7.18 |
| Shieldstral 3B | vLLM; prefix cache on | 18.8 ms | 237.0 | 171.3 ms | $0.94 |
| Qwen3.5 4B | vLLM; prefix cache on | 65.1 ms | 42.3 | 865.5 ms | $5.25 |
| WildGuard 7B | vLLM; prefix cache on | 504.3 ms | 36.3 | 967.3 ms | $6.12 |
| Kev 4B | native; optimized kernels | 58.6 ms | 61.2 | 638.2 ms | $3.63 |
| Clef-Flash 9B | native; optimized kernels | 73.2 ms | 10.8 | 3214.3 ms | $20.54 |
| Fine-tuned Liquid encoder 350M | native; reference | 14.5 ms | 358.4 | 103.1 ms | $0.62 |
