# Selections fixed before final inference

All eight systems were selected on validation before any final test inference.
The [freeze](freeze.json) pins the selected policies, classifier configurations
and evidence hashes. [Validation scores](validation-summary.json) are development
results, not held-out performance. The [plan](../PLAN.md) sets the selection rules.

The frozen selections are evidence for PolicyLM and Kev, structured for Shieldstral
and Clef, and brief for Qwen and Jev on code. Every prompted model selects structured
on skills. TF-IDF selects C=10 on both tasks. Liquid selects learning rate 5e-5,
epoch 3 on both tasks, with a separate trained classifier for each.

Source pins, input hashes, exclusions and overlap checks accompany the freeze.
Original text and model weights remain private. The registration retains two
pre-test amendments: Unicode JSONL parsing and lossless checkpoint storage.
