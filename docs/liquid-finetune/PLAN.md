# Fine-tuning a Liquid encoder for harmful-prompt classification

## Question

Can a compact Liquid encoder learn this particular harmful/benign boundary when
we update its weights using labeled WildGuard prompts? How does that pipeline
compare with a linear classifier on the same encoder's frozen representations?
This is supervised task-specific fine-tuning, distinct from our earlier policy
editing and frozen-backbone studies. No claim about the best possible accuracy.

## Data and model

Reuse the exact group-disjoint WildGuard populations from the contrastive-head
study: 4,096 fitting prompts, 1,536 validation prompts, and 1,699 labeled official
WildGuardTest prompts (945 benign, 754 harmful). The task is prompt harmfulness;
responses and refusal labels are not used. The 26 unlabeled test prompts remain
excluded, as in prior studies. Record IDs, text hashes, groups and source revision.
This is a bounded training subset, not all of WildGuardTrain. These public tests
have been used in earlier studies; this is not a new blind confirmation set.

Use LiquidAI/LFM2.5-Encoder-350M at
`b886781f7c6f10ca9b7096e21b83e30a073c2f39`. The provider describes it as a
bidirectional, masked-language-pretrained encoder for downstream fine-tuning.
Its custom model code has been inspected. Pin Transformers 5.12.0 and Torch
2.8.0. The checkpoint uses the LFM Open License v1.0.

Submitted prompt text only: no policy, examples, chat wrapper or generated
answer. Use the pinned tokenizer, its default special tokens, right padding,
and a maximum of 8,192 tokens. Right-truncate only beyond that limit, retain the
example, and report counts by split. Pool the final hidden states by the mean
of all nonpadding tokens, including special tokens, following the provider's
classification tutorial. No layer or pooling search. The training/validation
length audit found maxima of 2,464/2,378 tokens before this plan was frozen.

## Two pipelines

1. **Frozen encoder + linear head:** fit StandardScaler on fitting features only;
   unweighted L2 logistic regression, C in [.0001,.001,.01,.1,1], lbfgs,
   max_iter=3000, tol=1e-6. A nonconverging fit fails explicitly. No backbone
   weight updates. Frozen extraction uses FP32 weights with BF16 autocast.
2. **Fine-tuned encoder + linear head:** update all encoder parameters and a
   single binary linear head. Mean pooling -> dropout(.1) -> Linear(1024,1).
   Unweighted binary cross-entropy. AdamW, learning rates [2e-5,5e-5], weight
   decay .01 (excluding biases and normalization parameters), linear schedule
   with 10% warmup, gradient norm clip1.0. Three epochs, checkpoint each epoch.
   Microbatch8, accumulate4 (effective32), shuffled examples, dynamic padding,
   FP32 parameters/optimizer with BF16 autocast, SDPA attention. Seeds20261031,
   20261101,20261102; common head initialization and batch order across rates
   for each seed. No best-seed selection or seed ensemble. All backbone tensors
   are trainable; record gradients/parameter changes to verify actual tuning.

The frozen classifier is a strong linear control, not an optimizer-matched
ablation: its scaling, regularization and optimizer differ. A difference cannot
be attributed solely to architecture or to one changed weight tensor.

## Selection and test

For the fine-tuned pipeline choose one learning rate/epoch and shared cutoff
using mean validation **ordinary accuracy** across seeds. This is the primary
profile answering the user's accuracy question. Also preselect balanced accuracy,
<=5% false-block rate, and >=90% harmful recall profiles. For constraints require
every seed to meet the validation target. Frozen LR has one deterministic fit.
Cutoffs0..1 in .01 steps plus1.000000001. Ties: mean minimum class recall, mean
macro-F1, cutoff closest to.5, smaller cutoff, then candidate ID. No validation
refitting. Preserve fixed-.5 results for the selected checkpoints to make the
effect of cutoff selection visible without selecting on test.

Freeze source/data/parameter hashes and all selections before uploading test
inputs to the GPU. Test labels stay local. Only selected checkpoints are tested;
evaluate all three fine-tuned seeds and report mean/range plus the predeclared
primary seed20261031. Save scores for every retained case. Report ordinary and
balanced accuracy, macro-F1, MCC, FP/FN counts and rates, coverage, AUROC,
average precision, Brier and log loss, with dataset slices. Primary comparison:
accuracy-selected fine-tune versus accuracy-selected frozen LR. Also report
balanced-selected comparison. Use2,000 paired duplicate-group bootstrap draws;
intervals concern the fixed primary seed, not search/training uncertainty.
Historical models are contextual references with unequal searches, not a reranked
common-validation leaderboard. No test-driven retraining or threshold changes.

## Cost and execution

Prior accounted spend$16.80001787256 of$20; remaining$3.19998212744. Reserve no
more than$1.60 for one GPU.ai L40S at <=$.80/hour, no storage surcharge, two-hour
server termination cap. RunPod is fallback only within that same reservation.
No paid API inference. Test a fitting-only forward/backward pass for runtime and
memory before bulk training. A failed technical smoke test may be repaired with
an explicit amendment; never silently reduce the scientific search after seeing
test outcomes. If the fixed search cannot fit, stop with documented partial
results rather than exceeding the cap. Terminate promptly after verified artifact
collection, reconcile usage, and remove task SSH keys.

Publish source, registration, validation candidates, pretest freeze, predictions,
metrics, uncertainty, execution notes and billing. Keep source text, embeddings
and large checkpoints outside Git. Retain selected checkpoint weights locally
with hashes; archive all candidate checkpoint hashes. Add a readable experiment
entry and map branch. Paper, media and skill revisions are separate work.

Provider references:
- https://huggingface.co/LiquidAI/LFM2.5-Encoder-350M
- https://www.liquid.ai/blog/lfm2-5-encoders
- https://github.com/Liquid4All/cookbook/tree/main/examples/lfm-encoder-classification
