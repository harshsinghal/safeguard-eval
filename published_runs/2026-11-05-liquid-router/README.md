# Liquid benchmark-family classifier evidence

This archive contains the locally registered protocol, source and data hashes,
metadata, frozen checkpoint hashes, CPU predictions, quality/latency results,
grouped uncertainty intervals, integrity checks, preflight failures and GPU
resource records. Source text and weights remain private in ignored work/.

[Readout](../../docs/liquid-router/README.md) ·
[CPU inference](../../docs/liquid-router/RUNNING.md)

Files ending in .gz use deterministic gzip compression. artifact-index.json
binds each archived file to its original public-relative path and both hashes.
The metadata and prediction files are JSON Lines after decompression.

Use tools/verify_liquid_router_evidence.py to verify every artifact, restore a
text-free public evidence tree in a new ignored work directory, and reproduce
the paired precision report without source prompts, model weights, GPU or API
keys. The registered code lives in evals/liquid_router/ at the enclosing commit.

The seven-category headline covers 935 supported inputs; 48 custom-policy
inputs remain an unsupported-category diagnostic. These are reused source tests
and weak benchmark-membership labels, not a fresh enterprise routing audit.
The selected one-route policy missed its validation coverage target on test.
No guard backend was dispatched. Per-track accuracy is interpretable; raw
fixed-seven-label per-track macro scores include zero-support categories.
