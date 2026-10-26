# Experiment notes

2026-10-25 (Los Angeles): Protocol and implementation registered before new inference.
The original 35 tests and eight transfer tests pass. Exact dataset and baseline
artifact hashes were verified; fit and validation groups do not overlap.

The earlier selected policies are not reused for authoring. The five original p0
fitting/validation runs are reused as fixed inputs; all twenty drafts are fresh.
A single pinned Qwen3.5-27B editor is held constant and blinded to the recipient name.
This procedural choice makes the feedback isolated and reproducible, but introduces
an editor-family confound that is explicitly documented in the protocol.

GPU.ai still has capacity and $17.46 account credit. The remaining user-authorized
project budget is only $11.53880246544. One $1.99/hour RTX PRO 6000 was requested
with a five-hour automatic lifetime; RunPod is available if needed. No audit or
test dataset is included in the initial GPU upload.
