# Author output-contract amendment

26 October 2026, before any validation or test inference.

The initial Qwen-4B editor echoed the input envelope instead of emitting a revised
policy. Its original two attempts per recipient produced no usable candidates.
Those six calls and their outputs remain in `private-author/`; no failed call is
presented as a policy revision or classifier result. The completed baseline fitting
runs remain valid and are retained without rerunning them.

Amend the editor's output contract to return only the four editable sections as
arrays of strings, enforced with JSON Schema. The implementation reconstructs the
fixed scope, examples, name, and clause IDs from p0. This removes the need for the
editor to reproduce metadata and demonstrations. An explicit user instruction
clarifies that it must revise rules rather than echo the input. Preserve the same
editor checkpoint, fitting-feedback selection, native-interface guidance,
temperature, output-token cap, word budget, and policy scope.

Run two amended revision attempts per recipient, starting from the same original
baseline; the second uses fitting feedback from the first valid revision or p0 if
none exists. Thus actual authoring can include up to twelve calls: six failed
initial calls and six amended calls. This is an explicit deviation from the
original six-call budget, not an unreported retry or a validation-driven search
extension. No validation results or test data have been used to make this change.
Keep all failures. There are no further automatic editor retries.

The classifier inputs, adapters, source, dataset, selection objective, comparison
matrix and fixed decision settings are unchanged. The amendment and repair script
hashes are recorded before the amended calls and bound into the eligibility review
that the final freeze hashes. Initial implementation hashes remain intact.

The common Qwen editor's limited ability and this single amended search remain
limitations. Performance changes cannot be interpreted as the best achievable
policy for any recipient model.
