# Execution notes and amendments

The study began with a prepared protocol and no paid inference. The original preparation registration remains in `preparation/registration.json`.

1. **Budget authorization, before inference.** The user allocated up to $15 from the earlier remaining allowance. The GPU has a six-hour automatic termination limit at $0.65/hour; Jev and the original Safeguard API subcaps remain $1 and $3.50. Data, policies and selection rules did not change.
2. **API pacing, during fitting preflight.** Safeguard encountered repeated HTTP 429 responses. Its initial eight prediction records were archived. A single-worker retry used one-second pacing and 30-second waits after 429, with the same policy and generation settings. All request charges and unknown-charge upper bounds were retained.
3. **Self-host Safeguard, before validation.** Rate limiting persisted. The entire API fitting preflight was archived and excluded from classifier comparisons. Safeguard now uses the pinned open checkpoint from earlier studies, `8a11e17b25c973a24099d4016bf2e17dd7ec1574`, with vLLM 0.31.0 on the allocated GPU. Its full fitting population is rerun. System policy, binary output contract, medium reasoning and 2,048-token ceiling are unchanged. This is an operational fallback, not a model choice based on accuracy. Sixteen concurrent generation requests use the one local server; the four native decision-head/encoder runs remain serial. Jev remains API-only.

No final test predictions had been generated at these amendments. The test set is not used to repair wording or choose configurations. Exact source and registration snapshots are kept in the run evidence. GPU/API failures and negative findings will remain part of the record.

4. **Generation scheduling, from fitting-only runtime evidence.** A long generation could leave other request slots idle because the client waited for a whole group of 16. The client was allowed to finish its current request group. Remaining fitting requests and validation/test now refill those same 16 slots as responses finish. Checkpoint, prompt, reasoning settings and token ceiling are unchanged. Truncated or malformed classifications stay unresolved without retries; five transport/server failures halt the run. Completed fitting outcomes, including unresolved classifications, are retained without re-sampling. No classification accuracy or test outcome motivated this repair.

5. **Safeguard output budget, before policy selection.** Complete fitting collection found 13 of 256 outputs truncated at 2,048 tokens. All 256 outcomes and costs are retained as a pilot. The entire fitting split is rerun with an 8,192-token output allowance, the allowance used in earlier project studies; validation and test will use this same value. The context ceiling becomes 32,768 tokens and transport timeout 600 seconds. Policy text, labels, weights and medium reasoning remain unchanged. This decision uses fitting completion status, not held-out classification accuracy.

The 8,192-token rerun completed all 256 fitting records with two unresolved outputs. Those remain in the record; the output allowance is fixed for validation and test. All six models’ example policies were then authored and frozen from fitting data. Validation began only after that freeze.

All 4,608 validation decisions were collected before selection. Safeguard had ten unresolved validation outputs (nine token-limit truncations and one invalid binary response); the other five models had none. The fixed rule selected examples for PolicyLM, Safeguard and Jev, structured for Shieldstral, and brief for Kev and Clef. This evidence is committed before test requests are issued.

## Completion and verification

All six models completed the registered final population. The ten distinct test
configurations produced 26,970 records covering the same 2,697 examples; Kev and
Clef reuse brief predictions because brief was selected. All records matched
the frozen policy and request hashes. No setting was changed in response to
held-out outcomes.

Safeguard's brief run had 37 unresolved outputs: 33 token-limit truncations and
four invalid binary answers. Its selected example-bearing run had 20 unresolved
outputs, all token-limit truncations. No transport failures occurred. The other
five models had no unresolved test outputs. These outcomes remain in the metrics.
The two selected NotInject failures are unresolved, separate from four false
blocks; neither is counted as a correct allow.

The prompt-free archive reproducer matched every published dataset metric and
all 2,000-draw paired group-bootstrap intervals exactly. Policy restoration also
matched all six frozen candidate-file hashes. Raw execution logs and responses
are retained privately; public artifacts contain no raw source prompts or model
reasoning.

The GPU was terminated and verification completed at 2026-11-02 22:44 UTC.
GPU.ai reported 8,883 GPU-seconds and $1.60. Jev accounting was $0.173527200;
Safeguard's excluded API preflight added $0.075251000, including $0.070400000 in
conservative unknown-charge allowances. Total accounted cost was $1.848778200
against the authorized $15, leaving $13.151221800 of that allocation unused.
Temporary local/provider SSH keys were removed and zero active instances were
confirmed. RunPod was not used.
