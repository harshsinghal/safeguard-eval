# Selections fixed before final inference

All eight systems were selected on validation before any final test inference.
The [freeze](freeze.json) pins the selected policies, classifier configurations
and evidence hashes. [Validation scores](validation-summary.json) are development
results, not held-out performance. The [plan](../PLAN.md) sets the selection rules.

The frozen selections are evidence for PolicyLM and Kev, structured for Shieldstral
and Clef, and brief for Qwen and Jev on code. Every prompted model selects structured
on skills. Both trained baselines choose C=10 for TF-IDF and learning rate 5e-5,
epoch 3 for Liquid, separately for each task.

Source pins, input hashes, exclusions and overlap checks accompany the freeze.
Original text and model weights remain private. The registration retains two
pre-test amendments: Unicode JSONL parsing and lossless checkpoint storage.
