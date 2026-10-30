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

## Completion record

* All 7,331 fitting/validation/test messages were extracted successfully for each
  model. The empty Qwen fitting case has zero mean vectors and nonzero final-input
  vectors as specified. No records were dropped. PolicyLM used 7,432 native
  windows/variants, up to nine for one message; they stayed one message per row.
* All 70 registered fits converged. Pre-test choices and source/feature/parameter
  hashes were frozen and committed as `f2162df` before test input upload.
* Primary balanced accuracies: Qwen features 82.4383%, PolicyLM features
  88.4319%, combined features 87.0908%, native PolicyLM score 86.1807%.
* The primary combined classifier fell behind the validation-selected stronger
  single probe, PolicyLM, by 1.3411 points (paired interval −2.2057 to −0.4862).
  Combining features corrected 17 of that single probe's errors but introduced
  35 new errors. This does not support a gain from combination for this registered pilot,
  not all possible models, representations or ensembles.
* The PolicyLM feature probe reduced native-score false blocks from 97 to 72 and
  misses from 131 to 117. Its 2.2511-point gain has a descriptive interval of
  +1.2069 to +3.3454. This secondary explanatory contrast is saved separately from
  the pre-registered combined-method contrasts; no choices were changed.
* Native-score AUROC (0.9418) was slightly higher than the PolicyLM probe's
  (0.9403). Do not claim that this study established a more informative ranking
  hidden inside the network. The practical gain is at the selected decision rule.
* Layer search selected Qwen layer 12 mean and PolicyLM layer 21 category slot.
  Their individual test balanced accuracies were 83.1113% and 86.7987%; combining
  them reached 86.8509%. A higher validation score did not guarantee a higher
  test score. No other cached test layers were searched.
* All 70 fits were repeated with identical parameter arrays and validation
  probabilities. All three operating profiles, validation grids, test metrics,
  slices, 2,000-draw intervals and 18 primary combined-method contrasts were
  independently recomputed from saved outputs.
* Historical controls use the same test prompts but prior validation choices:
  WildGuard 89.8082%, specialist equal-log-odds ensemble 91.0816%. The new probes
  did not exceed either. Do not mix this separately selected follow-up into the
  common-validation leaderboard without a separately documented integration.
* GPU.ai instance `gpu-bdc4ea4b` was terminated after artifact download. The API
  billed 2,098 GPU-seconds at $0.65/hour, rounded to $0.38. Cumulative recorded
  spending is $14.17540555656 of $20. Temporary local/provider SSH keys were
  removed. No RunPod or paid classification-API resources were used.

## Implications and next questions

The strongest new result is a task-specific PolicyLM readout with frozen base
weights. It still needs labeled data, training, versioning and validation. Editing
the policy after fitting could change its feature distribution and behavior;
policy-switching was not tested. This extends the research into supervised
adaptation rather than proving policy authoring alone is sufficient.

A useful next replication would test the same four controls on HateXplain under
its hate-versus-non-hate policy. That experiment has not been run here. Another
separate study could examine whether a fitted readout follows a changed policy,
and whether gains persist across training sample sizes or independent evaluation
sets. These are future questions, not explanations established by this pilot.
