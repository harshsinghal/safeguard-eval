# Technical amendments before test scoring

## ModernBERT fast-tokenizer compatibility

The initial extraction stopped before producing any feature files: the fast
tokenizer does not implement `prepare_for_model(..., return_special_tokens_mask=True)`
for an unwrapped token-ID sequence. The repair calls the supported tokenizer
encoding interface with its own special-token mask and overflow windows.

All content tokens remain included, with nonoverlapping windows, excluded special
tokens/padding, and the same content-token-weighted final-layer mean. An assertion
checks that window content counts equal the original unwrapped token count.
Empty content still receives a zero vector. No labels, classifier settings or
selection rules change. The source registration is versioned; the original failure
log and registration are preserved. The cached PolicyLM training results do not
depend on the repaired extractor. No new test classification had been scored.
