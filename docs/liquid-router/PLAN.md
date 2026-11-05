# Liquid CPU benchmark-family router

Registered before model fitting or final classifier evaluation. The goal is a
compact Liquid encoder classifier that predicts benchmark/task families and emits
a small set of candidate safety checks. Guard-model dispatch and new guard
inference are deferred. This experiment does not claim semantic multilabel
annotation, harmfulness prediction, or end-to-end routing safety.

Use LiquidAI/LFM2.5-Encoder-350M at revision
`b886781f7c6f10ca9b7096e21b83e30a073c2f39`. Seven pooled categories: agent safety,
code safety, cyber safety, harmful requests, hate speech, prompt injection, and
skill safety. Source membership supplies a single weak routing target per input;
other applicable routes are unknown. Preserve ALLOW/BLOCK/REVIEW examples. Exclude empty original texts and record
their source IDs. Validate original weight loading and portable checkpoint
round trips before fitting.
Custom policy has no adequate fitting split and remains an unsupported-category
diagnostic. The source benchmark identity and gold decisions are never model
features. CPU inference receives text only.

Restore up to 512 original fitting examples per category by stable hash. Use up
to 128 archived validation examples per category, excluding the fixed suite.
Preserve all 983 fixed evaluation cases; score the supported categories and
report custom policy separately. Related known groups, normalized exact text,
and retrieved word5 Jaccard>=.90 groups exclude fitting/validation rows whenever
they touch held-out cases or the fixed calibration panel. Never move a held-out
case into fitting. Original tests are reused exploratory evidence, not a fresh
blind enterprise evaluation. NotInject, JBB, injection-context and skill-package
inputs provide additional-source diagnostics without new fitting examples.

Compare a TF-IDF linear control, frozen Liquid embeddings plus a linear head,
and a bounded full Liquid fine-tune: one seed 20261105, learning rate 5e-5, up to
three epochs, AdamW .01 decay, gradient clipping 1, microbatch one, effective
batch sixteen. Use class-balanced training weights and validation macro F1 for
checkpoint selection; ties favor earlier checkpoints and then the frozen model.
The full fine-tune starts from the fitted frozen-encoder linear head.
The model sees at most 256 tokens: first 96, middle 64, final 96. Report the
truncation rate. This bounded view is a routing compromise, not full-context
safety evaluation. Training never reads final inputs or labels.

Select temperature from {.5,1,2,3} by validation NLL. Choose the smallest global
candidate count in {1,2,3} attaining 95% reference-family coverage on validation;
if none does, use three and explicitly report target failure. Confidence below
.6 requests a general-guard fallback, never ALLOW. Softmax values estimate the
single reference benchmark family and are not independent semantic probabilities.
Unknown-category reliability is unproven; report the custom-policy diagnostic.
Freeze checkpoint hashes, temperature and candidate count before final inputs.
No category-to-best-guard assignment will be selected from final scores.

GPU use is local only, no paid resources. Because the RTX5090 minimum hardware
power cap is 400W, do not change power/clocks. Use a 20% software duty target,
microbatch one, four host threads, sampled temperature/power/memory telemetry,
extra cooldown above 60C or 180W, stop at 70C or sustained >250W. This limits
activity but is not an instantaneous hardware power guarantee. Stop after a
45-minute training budget and preserve the completed evidence. CPU evaluation
uses four threads, batch one. Measure native FP32 and dynamic INT8 linear-layer
inference on the same cases, including classification drift and latency.

Publish only metadata, registration, metrics, predictions, model/checkpoint
hashes, environment and resource records. Source text, tensors, features and
trained checkpoints remain ignored locally. Record failures and amendments.
