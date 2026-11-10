"""Validate suite integrity, split separation, policies, weights and private exports."""
import argparse
from collections import Counter
import json
from pathlib import Path
from .sources import rows,read,sha,ROOT
from .scoring import verify_bundle,item_weights,score

def validate(bundle,private_inputs=None):
    bundle=Path(bundle);manifest=verify_bundle(bundle)
    evals=rows(bundle/"evaluation.jsonl");cal=rows(bundle/"calibration.jsonl")
    tracks=read(bundle/"tracks.json");profiles=read(bundle/"profiles.json");policies=read(bundle/"policies.json")
    allrows=evals+cal
    if len({r["id"] for r in allrows})!=len(allrows):raise ValueError("Case ID overlap")
    if {r["group"] for r in evals}&{r["group"] for r in cal}:raise ValueError("Group leakage")
    if {r["input_sha256"] for r in evals}&{r["input_sha256"] for r in cal}:raise ValueError("Input leakage")
    for r in allrows:
        if r["expected"] not in tracks[r["track"]]["labels"]:raise ValueError("Unexpected label")
        if r["policy_id"] not in policies:raise ValueError("Missing policy")
        if r["policy_sha256"]!=sha(json.dumps(policies[r["policy_id"]],ensure_ascii=False,sort_keys=True,separators=(",",":"))):raise ValueError("Policy hash drift")
        if set(r)&{"prompt","content","text","rationale","target_reason"}:raise ValueError("Raw source text in public case manifest")
    if private_inputs:
        for split,rr in (("evaluation",evals),("calibration",cal)):
            actual=rows(Path(private_inputs)/(split+".jsonl"))
            lookup={r["id"]:r for r in rr}
            if {r["id"] for r in actual}!=set(lookup):raise ValueError("Private export population differs")
            for r in actual:
                if set(r)!={"id","policy_id","content","input_sha256","policy_sha256"}:raise ValueError("Unexpected inference input fields")
                expected=lookup[r["id"]]
                if sha(r["content"])!=expected["input_sha256"] or r["input_sha256"]!=expected["input_sha256"] or r["policy_sha256"]!=expected["policy_sha256"]:raise ValueError("Private input drift")
    weights=item_weights(evals,tracks,profiles)
    totals={p:sum(w[p] for w in weights.values()) for p in profiles}
    if not manifest["missing_tracks"] and any(abs(w-1)>1e-10 for w in totals.values()):raise ValueError("Profile weights do not sum to one")
    oracle=[dict(id=r["id"],prediction=r["expected"],input_sha256=r["input_sha256"],policy_sha256=r["policy_sha256"]) for r in evals]
    perfect=score(bundle,oracle)
    if not manifest["missing_tracks"] and any(abs(v-100)>1e-9 for v in perfect["profiles"].values()):raise ValueError("Oracle does not score 100")
    baselines={}
    for label in ("ALLOW","BLOCK","REVIEW"):
        pp=[dict(r,prediction=label) for r in oracle]
        result=score(bundle,pp)
        baselines["always_"+label]=dict(accuracy=result["accuracy"],profiles=result["profiles"])
    for relative,expected in manifest["sources"].items():
        if sha((ROOT/relative).read_bytes())!=expected:raise ValueError("Builder source drift: "+relative)
    return dict(valid=True,evaluation_cases=len(evals),calibration_cases=len(cal),tracks=len(tracks),
        evaluation_groups=len({r["group"] for r in evals}),calibration_groups=len({r["group"] for r in cal}),
        missing_tracks=manifest["missing_tracks"],profile_weight_sums=totals,trivial_baselines=baselines,
        private_inputs_checked=bool(private_inputs),moderation_model_inference=False)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--bundle",required=True,type=Path);p.add_argument("--private-inputs",type=Path)
    a=p.parse_args();print(json.dumps(validate(a.bundle,a.private_inputs),indent=2))
