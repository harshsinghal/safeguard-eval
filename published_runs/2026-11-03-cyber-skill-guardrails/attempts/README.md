# Invalid integration attempts

These files document errors discovered and repaired before final-test inference.
They are excluded from the model leaderboard.

- `llamaguard-transformers-5.17-errors.jsonl`: three attempted rows failed on a
  runtime/configuration incompatibility. The model-card runtime replaces it.
- `llamaguard-wrong-label-position/`: 1,142 invalid readouts scored candidate
  labels before the native completion's initial blank line. These allow-only
  results say nothing about the model's classification ability. The corrected
  adapter advances through native whitespace and scores the actual safety label.

The tokenizer batch-shape preflight failed before recording any predictions.
See the [amendments](../amendments/) for all repairs and timestamps.
