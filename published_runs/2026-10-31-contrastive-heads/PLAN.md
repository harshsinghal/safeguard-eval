# Frozen representations: ordinary and contrastive task classifiers

## Question and commitments

Can a small nonlinear classifier improve on logistic regression using the same
frozen features, and does adding supervised contrastive loss improve on that
same neural network? This is task-specific supervised training, not policy-only
optimization, backbone fine-tuning, or a demonstration of following new policies.
This plan is recorded before fitting or looking at this experiment's test scores.

## Populations and backends

Use the smart-ensemble study's exact group-disjoint populations for each task:
4,096 fitting examples, 1,536 validation examples, and the official labeled tests
(1,699 WildGuard prompts; 1,924 HateXplain posts). WildGuard measures prompt
harmfulness only. HateXplain maps hate to BLOCK and normal/offensive to ALLOW.
Retain all cases, including empty inputs. These tests have been examined in prior
studies; this follow-up is exploratory, not a fresh blind confirmation. No new
independent labels are available for a fresh confirmation set in this run.

Two backends per dataset:

- PolicyLM 1.7B at b3b2cd408a08a68ab6a30c1fc1e440204e44d57e: final native
  category-slot representation, 2,048 features, fixed prior policy (WildGuard p4,
  HateXplain p0). Reuse verified WildGuard features. Extract HateXplain using the
  same native cleaning, windowing and alignment; average window vectors.
- ModernBERT-base, 149M parameters, at
  8949b909ec900327062f0ebf497f51aef5e6f0c8: submitted text only, final-layer
  content-token mean, 768 features. Exclude padding and special tokens. Split
  overlength text into nonoverlapping 8,190-content-token windows and combine
  window means weighted by content-token counts; an empty input has a zero vector.

No layer, pooling, policy, or backbone search. The different policy conditioning,
architectures, size and pretraining prevent causal attribution to specialization.
Feature extraction may process test text without labels before the head freeze;
test feature files do not enter training or selection. Test scoring requires a
verified freeze. Source text and features remain private.

## Matched heads

Fit a StandardScaler on fitting features only, separately per backend/task.

1. Class-balanced L2 logistic regression: C in [.0001,.001,.01,.1,1], lbfgs,
   max_iter=3000, tol=1e-6. Nonconvergence is a failed candidate, not silent success.
2. MLP: input -> Linear(256) -> GELU -> Dropout(.1) -> Linear(64) -> GELU ->
   Linear(1). Class-balanced binary cross-entropy on logits.
3. Identical MLP, initialization and minibatch sequence, with the same classification
   loss plus 0.1 times supervised contrastive loss on the L2-normalized 64-vector.
   Temperature .1. Same-label nonself examples are positives; all nonself examples
   enter the denominator. Average positives per anchor; class-balance the anchors.
   Anchors without a positive peer are omitted from contrastive loss only.

MLPs: AdamW lr=.001, weight decay in [.001,.01], batch size 128, random shuffled
batches without augmentation or hard-negative mining. Train 20 epochs and retain
checkpoints at 5,10,20. Three paired seeds: 20261031,20261101,20261102. No best-seed
selection. Same search size for ordinary and contrastive MLPs. CPU deterministic
training with four Torch threads. If the fixed feature representation loses
needed information, a more expressive head cannot recover it from nothing.

## Validation selection and test

For each task/backend/head, choose hyperparameters and one shared cutoff by
mean validation balanced accuracy across the three seeds (LR is deterministic).
Cutoffs: 0..1 in .01 steps, plus 1.000000001. Ties: mean minimum class recall,
mean macro-F1, cutoff closest to .5, smaller cutoff, lexicographic candidate ID.
Also preselect an ordinary-accuracy profile, a <=5% false-block profile and a
>=90% harmful-recall profile. Constraints must hold in every seed on validation.
Report these separately; do not conflate accuracy optimization with balancing
the two errors. Never refit on validation or select a random seed from test.

Freeze source hashes, policies, feature manifests, trained parameters, validation
predictions and all selections before test scoring. Fixed seed 20261031 is the
primary point result and paired-bootstrap target; report all three seeds and
their mean/range to disclose training variation. No seed ensembling. Select the
overall candidate by validation, not by the best observed test result.

Report ordinary/balanced accuracy, macro-F1, MCC, both error counts/rates, coverage,
AUROC, average precision, Brier and log loss. Retain dataset slices. Primary
contrasts per task/backend: MLP minus LR and contrastive MLP minus ordinary MLP.
Use 2,000 paired duplicate-group bootstrap draws for fixed-seed comparisons.
Intervals are exploratory, unadjusted, and exclude model/search uncertainty;
seed variability is reported separately. Higher aggregate scores need not reduce
both errors. Existing native scores and other studies are contextual comparisons
with their original validation protocols, not matched search-budget controls.

## Cost, progress, and deliverables

Current cumulative accounted provider spend is $16.69001787256 of $20. Reserve
at most $1.60 for one GPU.ai instance at <=$.80/hour with a two-hour server-side
auto-termination cap and no storage surcharge. Use RunPod only if needed within
that same reservation. No API inference. Train cached-feature heads locally.
Collect and terminate the GPU promptly after extraction; reconcile billing and
remove temporary credentials. Keep a run log, immutable public evidence bundle,
readable results, source, tests and README experiment-map update. Do not update
paper or skill snapshots as part of this run.
