# Implementation and interpretation notes

* Protocol committed before new feature extraction as `7161578`.
* Reused 4,096 fitting rows (3,823 duplicate groups), 1,536 validation rows
  (1,424 groups), and 1,699 test rows. All three source prediction-file hashes
  match the immutable first ensemble archive. Source text hashes and split
  disjointness also passed.
* Qwen3.5-0.8B has 24 text blocks, hidden width 1,024, and a hybrid attention
  architecture. PolicyLM has 28 bidirectional blocks, hidden width 2,048, and a
  native category classification head. Their layer numbers and coordinates are
  not interchangeable; concatenation preserves the two representation spaces.
* PolicyLM's released helper performs normalization/cleaning and windowing. The
  extractor hooks its encoder instead of replacing its input construction. It
  retains native score aggregation while separately averaging pooled feature
  vectors over windows and variants. The linear probe therefore does not copy
  the upstream nonlinear head or its maximum-window aggregation rule.
* Qwen uses the same policy's purpose/rules/exception text in the existing chat
  renderer. PolicyLM receives the native category's violation, non-violation and
  exception fields. These are fixed native interfaces, not identical token strings.
* The experimental claim is predictive usefulness of representations. It cannot
  locate causal policy reasoning in a layer or establish why specialization works.
* TaskTracker studied task drift using activation differences. With one fixed
  policy, subtracting a constant policy-only vector adds no information to an
  intercept-bearing linear classifier. This study tests direct representations.
* No HateXplain run or automatic replication is included in this pilot.

Technical amendments before extraction/fitting:

* Source hashing includes transitive policy-renderer dependencies.
* Over-limit Qwen input is explicitly unresolved rather than truncated; other
  implementation errors abort the job for investigation rather than silently
  turning an entire run into failed predictions.
* First GPU smoke check failed before any complete feature cache or classifier
  fit. In pinned `inference/bidirlm/modeling_bidirlm.py`, the optional hidden-state
  path takes `[0]` from an already batched reconstruction (line 439), then indexes
  the resulting 2-D tensors as 3-D at line 467. No upstream weights or files were
  edited. Read-only hooks capture outputs of blocks 14 and 21, while block 28's
  normalized output comes from the ordinary encoder result. Packed single-row
  intermediate states are aligned with the release's existing MNTP shift and
  final-position removal. The native classifier computation remains intact and
  must pass the same score-parity check. This repair does not add candidates.
* Qwen's development run encountered one empty training prompt, `wgtrain-018478`,
  before its first complete feature cache. A mean over zero content tokens is
  undefined. Before fitting, the protocol was amended to use a zero content
  vector for genuinely empty input and still compute the ordinary final-input
  representation. No label informed this convention. No policy or candidate
  family changed. The Qwen extraction was restarted; PolicyLM's completed caches
  were retained, because its extraction path did not change.
* Fresh native PolicyLM scores differ slightly from the older archive: mean
  absolute score differences are 0.0032804 on fitting and 0.0035564 on validation;
  12/4,096 and 3/1,536 decisions differ at 0.5. The old runtime used torch 2.11.0
  and another GPU, versus torch 2.8.0 here. We have not isolated the cause.
  Hook-on versus hook-off parity is exact on the same current runtime. Use fresh
  native scores as the in-study control; do not attribute cross-runtime changes
  to representation learning.

Execution outcomes, any further repairs, billing and interpretation are appended
after they are observed. They are never assumed from the hypothesis.
