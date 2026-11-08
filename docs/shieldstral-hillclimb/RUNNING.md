# Reproduce the Shieldstral hill-climb round

The round uses the pinned Shieldstral weights, Python environment and local
GPU controls from the [first round](../shieldstral-policy/RUNNING.md).
Keep the original Liquid and Shieldstral working directories available.
The second round reuses the original frozen and mixed development logits
and their reused-suite logits. It loads the mixed adapter for FIT mining
and fresh transfer inference.

From the repository root, fetch the public sources into a new ignored
state directory. The loader checks the revisions and records source hashes.

```sh
state=work/shieldstral-hillclimb-reproduction
mkdir -p "$state/sources"
git clone https://github.com/Lordog/R-Judge.git "$state/sources/r-judge"
git -C "$state/sources/r-judge" checkout --detach 83ce301da3ad50dd8b397e772863f5411c3d3dc2
git clone https://github.com/paul-rottger/hatecheck-data.git "$state/sources/hatecheck"
git -C "$state/sources/hatecheck" checkout --detach 3490854f969111a32c55c05f0d9788b471337fa9
curl -fLsS https://raw.githubusercontent.com/hate-alert/HateXplain/01d742279dac941981f53806154481c0e15ee686/Data/dataset.json -o "$state/sources/hatexplain.json"

timeout 36m python -Bu -m evals.shieldstral_hillclimb.mine work/liquid-router-v0 work/shieldstral-policy-v1 "$state"
python -Bu -m evals.shieldstral_hillclimb.data work/liquid-router-v0 work/shieldstral-policy-v1 "$state"
for stage in larger targeted select evaluate; do
    timeout 36m python -Bu -m evals.shieldstral_hillclimb.study "$stage" "$state" || exit
done
```

The two fitted adapters are stored in `larger/adapter` and
`targeted/adapter` inside the ignored state directory. Select and evaluate
run in that order. Evaluate checks the stored selection and checkpoint
hashes before reading the final cohorts. The published verifier recomputes
selection and results with the same Python environment and no model load.

```sh
python -B tools/verify_shieldstral_hillclimb.py published_runs/2026-11-07-shieldstral-hillclimb
```
