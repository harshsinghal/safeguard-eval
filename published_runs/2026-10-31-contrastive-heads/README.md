# Frozen features and contrastive task classifiers

[Readable study](READOUT.md) · [All results](RESULTS.md) ·
[CSV](results.csv) · [Protocol](PLAN.md) · [Amendment](AMENDMENTS.md) · [Reproduction](RUNNING.md)

PolicyLM 1.7B and ModernBERT-base representations are frozen. Small logistic,
ordinary neural and contrastive neural classifiers are trained separately for
WildGuard prompt harmfulness and HateXplain hate detection. No backbone is
fine-tuned. Both official tests have been used in earlier studies.

This bundle preserves every validation candidate, all four operating profiles,
all three selected neural training seeds, test predictions, paired intervals,
frozen configuration and parameter hashes, primary balanced classifier weights,
input identities, feature provenance, source, runtime and billing evidence.
Source text and embeddings are excluded. Remaining checkpoint weights are in
the author's private run directory; their hashes and predictions are included.

Verify a copy of this bundle without GPU/API calls:

```sh
PYTHONPATH=source python3 source/tools/verify_contrastive_heads.py --state .
```

The verifier writes a fresh verification.json; use a copy to preserve the original
checksums. requirements.txt records the CPU runtime. Independent refitting also
requires the private feature arrays or reproducing their extraction.

All package files except checksums.json itself are listed in checksums.json.
