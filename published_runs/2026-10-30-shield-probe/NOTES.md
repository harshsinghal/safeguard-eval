# Implementation notes

* A separate implementation preserves the earlier frozen PolicyLM/Qwen study.
* The same populations and overlap exclusions were verified before inference.
* Both models receive the existing Shieldstral p4 policy through their native
  templates. Qwen content honors its template's outer-whitespace trimming.
* Direct score controls condition on the canonical pair of label tokens; they
  are not a test of unconstrained generated-label compliance.
* Eleven tests cover fitting/scaling, missing cases, split separation, score
  combinations, mutation guards, complete selection/evaluation and reproduction.

* Pre-fit technical repair: Transformers 5.10.2 returns a BatchEncoding from
  `apply_chat_template(tokenize=True)` by default. Comparing that container to a
  token list triggered the first smoke guard. The contained token IDs matched
  exactly; normalize the return container before comparing. No token IDs, policy
  text, feature definitions or search choices changed, and no fitting had begun.

## Completed run and audit

Protocol commit: `7e148c7`; tokenizer-container repair: `e57d445`; pre-test
selection commit: `adb2aaf`. The frozen protocol and core extraction/fitting
sources were not edited after the pre-test freeze. The test input archive was
uploaded only after that freeze. Historical test findings had already been
examined in prior studies; this new freeze does not erase that history.

Both models produced valid features and native scores for all 4,096 fitting,
1,536 validation and 1,699 test prompts. Native-forward parity on 16 fitting
examples per model had a maximum absolute score difference of 0.0. No inputs
were truncated or dropped. Qwen had one empty fitting content span, represented
by a zero vector for content means, and two test prompts with native outer
whitespace trimming. Four fitting examples had a top vocabulary token outside
the canonical label pair; none did on validation or test. Those rows were kept
as valid conditional label-score examples.

All 75 regressions converged. A fresh CPU refit reproduced all parameter arrays
exactly and had maximum validation-score difference 0.0. A separate verifier
recomputed all 11 selection groups, three operating profiles, 30 registered
paired contrasts, category/adversarial slices and 2,000 group-bootstrap draws.
The source restoration utility reproduced development and test input hashes
exactly from the recorded source Parquet files. Raw text and vectors are excluded
from the published evidence.

## Findings to preserve in later writing

The primary combined representation did not beat the stronger single-model
feature head or the simpler output-score controls. Native Shieldstral scored
90.53% balanced accuracy, the Shieldstral head 90.39%, and the combined head
90.35%. The last comparison corrected six examples and introduced seven;
its −0.04-point difference had a paired interval from −0.48 to +0.39.

Qwen's layer/pooling search selected layer 24's last input vector, reaching
88.81%, versus 83.93% for the primary final-layer content mean. This changes two
representation choices at once. The selected combination scored 90.14%, so its
near-perfect 99.11% validation score did not establish superiority on test.
Neither this search nor inspecting linear coefficients establishes causal policy
reasoning in a particular layer.

The equal-log-odds average had higher observed AUROC than native Shieldstral
(0.9556 versus 0.9485), but not higher balanced accuracy at its frozen cutoff.
The primary combined head had log loss 0.729 compared with 0.268 for a simple
probability average. Better classification at one cutoff, better ranking and
better probabilistic scoring are distinct questions.

All 11 false-block-constrained selections exceeded 5% false blocks on test;
all 11 separate recall-constrained selections fell below 90% recall. These are
specific frozen selection procedures, not a search for every feasible test
cutoff. Do not replace them with thresholds chosen after seeing the test.

Native Shieldstral already fell from 98.73% validation to 90.53% test before
adding a learned head. The [dataset card](https://huggingface.co/datasets/allenai/wildguardmix)
describes GPT-4 training labels and human test annotation. Their different origins
and populations are plausible explanations, not causes isolated by this study.
The [Shieldstral paper](https://arxiv.org/html/2607.25857v1) describes public-data
training and held-out evaluation; we cannot independently audit checkpoint
training membership at the sample level. Do not infer either contamination or
its absence from this score gap.

## Runtime and cost

One L40S, BF16, batch size one; Torch 2.8.0+cu128 and Transformers 5.10.2. Qwen
used fallback Torch linear attention without optional `fla` kernels. Test-row
median/p95 extraction times were 33.4/39.6 ms for Shieldstral and 127.0/144.0 ms
for Qwen. Peak Torch allocations across recorded splits were about 7.87 GiB and
9.57 GiB respectively, with complete multimodal checkpoints loaded and text-only
inputs. These are instrumented extraction records, not minimum GPU requirements
or matched production inference measurements.

The provider billed 1,679 GPU-seconds at $0.80/hour, rounded to $0.37. The instance
was terminated and temporary provider/local SSH keys removed. Cumulative spend
is $14.54540555656 of the $20 cap. No RunPod resources were used. Source and
runtime records include the failed first smoke check and its repair.

The next policy-correction experiment is recorded but unrun. This study trained
new heads while keeping the language-model weights and policy fixed. It must
not be described as policy tuning alone, training-free moderation, or proof that
the learned head will follow future policy edits.
