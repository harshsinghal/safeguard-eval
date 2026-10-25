# Questions and evidence for the Qwen follow-up

This study extends the earlier policy-tuning story by asking whether a general-purpose instruction model can serve as the classifier. Final claims must come from complete frozen test runs, not pilot or validation ranks.

Potential article: **Does a moderation policy need a specialized model? A nearby-size Qwen comparison.** Explain that the policy is a system instruction in both cases; the model's training and native interface differ. Avoid treating document formatting as a fundamentally different method.

| Question | Evidence needed | Interpretation boundary |
|---|---|---|
| Can Qwen classify these requests with the original rules? | Matched p0 predictions, accuracy, F1, false blocks, missed harms and output failures | Same task and semantic rules; native templates differ |
| Does policy tuning help the general-purpose model? | Selected versus initial Qwen predictions, fitting history and validation selection | Limited search, existing shared candidates and known prior test results |
| Does specialist training appear useful at a nearby size? | Each registered Qwen/specialist pair under p0, shared p2 and separately selected prompts | Architecture, age, data exposure, parameter counts and deployment differ |
| Does a large model win only by blocking more? | Harmful recall, benign false-block rate and validation-only calibration controls | Accuracy alone does not settle operating-point tradeoffs |
| Does the result depend on ordinary versus adversarial wording? | Matched source-label slices | Does not measure downstream attack success |
| Does a generic model fail to return a classification? | Full raw traces privately, public output failures and strict parsing | Refusal, truncation and malformed output cannot be credited as BLOCK |
| Are model names misleading about size? | Language-model size, full checkpoint count, total/active MoE parameters | Similar active counts do not guarantee equal compute or memory |
| How much did the study actually cost? | Provider bill including setup/download time and retained failures | Assistant effort and local processing are not included in GPU dollars |

Use the original study as a fixed historical baseline. Do not replace its chosen policies with test-favored candidates. Present all seven registered nearby-size pairings, including negative outcomes, and note that the two large Qwen models are reused across two specialist comparisons.

A competitive Qwen result would support using general-purpose models for this particular classification deployment. It would not show that specialized policy models are unnecessary across arbitrary rules, languages, policy changes, latency budgets or adversarial settings. A stronger specialization study would include direct parent instruction checkpoints, a fresh benchmark, repeated prompt searches and controlled inference budgets.
