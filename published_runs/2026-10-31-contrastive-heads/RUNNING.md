# Reproducing the task-classifier study

The [registered plan](PLAN.md) specifies the populations, backends, heads, seeds,
selection objectives and limits. The [amendment](AMENDMENTS.md) records the
ModernBERT tokenizer repair. No base-model weights are trained.

## Check the published decisions without a GPU

The evidence bundle contains every validation candidate's outputs, all selected
test predictions, selections, metadata, source and runtime records. It excludes
submitted text, embeddings and credentials. From the repository root:

```sh
python3 tools/verify_contrastive_heads.py \
  --state /absolute/path/to/a-copy-of-the-published-bundle
```

Use a copy because verification writes a fresh `verification.json`. The command
reselects every validation profile, recomputes test metrics and independently
checks confusion counts/accuracy, and reproduces paired bootstrap intervals.
It does not call inference APIs or rent hardware. Use the recorded CPU package
versions; exact reproduction was checked in the author's environment.

## Refit from private cached features

An authorized dataset user can reproduce extraction from the pinned original
sources and the published sample identities. WildGuard input restoration is
documented in the [parent representation study](../../docs/activation-probe/RUNNING.md).
HateXplain source identity and text reconstruction are recorded in
[the dataset manifest](../../docs/hatexplain/data-manifest.json): join the publisher's
`post_tokens` with one ASCII space, using the archived post IDs and majority
labels. Match every prompt SHA-256 and split-file hash in the registration.

The original preparation command reuses the earlier private workspace:

```sh
python3 -m evals.contrastive_heads.prepare \
  --state /absolute/path/new-state --work /absolute/path/prior-research-work
```

This verifies and reuses the parent study's WildGuard PolicyLM final-category-slot
features. To recreate those features, first follow the parent study's extraction
instructions with the pinned PolicyLM revision and policy. The current extractor
adds HateXplain PolicyLM features and ModernBERT features on both datasets:

```sh
python3 -m evals.contrastive_heads.extract --state /absolute/path/new-state --backend modernbert
python3 -m evals.contrastive_heads.extract --state /absolute/path/new-state --backend policylm
```

Extraction used CUDA, Torch 2.8.0 and Transformers 4.57.6. The full GPU environment
is recorded. Extraction inputs have only ID, submitted text and text hash;
labels are held separately. Test text can be encoded before head selection, but
neither its features nor its labels are read by the training command. Retain
all content windows and empty examples. Embeddings can expose information about
source text and are intentionally not published.

## Train, freeze, evaluate

Run the training command once for each of the four dataset/backend combinations:
`wildguard` or `hatexplain`, and `policylm` or `modernbert`.

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=2 python3 -m evals.contrastive_heads.study train \
  --state /absolute/path/new-state --dataset wildguard --backend policylm
# Repeat for the other three combinations before freezing.
python3 -m evals.contrastive_heads.study freeze --state /absolute/path/new-state
python3 -m evals.contrastive_heads.study evaluate --state /absolute/path/new-state
python3 tools/verify_contrastive_heads.py --state /absolute/path/new-state --refit
```

The last command reruns all 20 logistic fits and 48 neural training trajectories
(144 epoch checkpoints), compares parameters and validation predictions, and
checks the results. It requires the private feature cache. The public bundle
preserves all candidate parameter hashes and the primary balanced-setting weights;
the remaining candidate weights remain in the private run directory. No
best-seed selection or seed ensembling is performed.

The primary cutoff balances class recall. The separate accuracy profile maximizes
ordinary accuracy on validation. Neither is tuned against test results. The
5% false-block and 90% recall profiles are separate selections and must be checked
on test; they are not deployment guarantees. Three seeds describe training
variation. Bootstrap intervals describe sampling variation conditional on the
fixed primary outputs; they do not cover all sources of research uncertainty.
