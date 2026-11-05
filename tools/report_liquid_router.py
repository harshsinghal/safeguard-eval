"""Reproduce text-free paired CPU precision comparisons and grouped intervals."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.liquid_router.common import CATEGORIES,SEED,read,rows,write


def summarize(state):
    state=Path(state)
    meta=rows(state/"public/metadata/test.jsonl")
    lookup={r["id"]:r for r in meta}
    results={}
    predictions={}
    for precision in ("fp32","int8"):
        result=read(state/"public"/precision/"results.json")
        pp=rows(state/"public"/precision/"predictions.jsonl")
        if len(pp)!=len(meta) or {r["id"] for r in pp}!=set(lookup):raise ValueError("Incomplete CPU predictions")
        if any(r["input_sha256"]!=lookup[r["id"]]["input_sha256"] for r in pp):raise ValueError("Input drift")
        predictions[precision]={r["id"]:r for r in pp}
        eligible=[r for r in pp if r["reference_category"] in CATEGORIES]
        groups=sorted({lookup[r["id"]]["audit_group"] for r in eligible})
        group_index={g:i for i,g in enumerate(groups)}
        counts=np.zeros(len(groups));correct=np.zeros(len(groups));covered=np.zeros(len(groups))
        for r in eligible:
            j=group_index[lookup[r["id"]]["audit_group"]]
            counts[j]+=1;correct[j]+=r["candidate_categories"][0]==r["reference_category"]
            covered[j]+=r["reference_category"] in r["candidate_categories"]
        rng=np.random.default_rng(SEED);accuracy=[];coverage=[]
        for _ in range(1000):
            sample=rng.integers(0,len(groups),size=len(groups));den=counts[sample].sum()
            accuracy.append(float(correct[sample].sum()/den));coverage.append(float(covered[sample].sum()/den))
        result["grouped_bootstrap_95pct"]=dict(replicates=1000,seed=SEED,
            accuracy=np.quantile(accuracy,[.025,.975]).tolist(),candidate_coverage=np.quantile(coverage,[.025,.975]).tolist(),
            interpretation="Exploratory intervals over observed duplicate/scenario groups on reused source tests")
        result["macro_category_candidate_coverage"]=float(np.mean([v["candidate_coverage"] for v in result["metrics"]["per_category"].values()]))
        result["by_original_moderation_label"]={label:dict(n=len(rr),reference_route_coverage=float(np.mean([
            r["reference_category"] in r["candidate_categories"] for r in rr])))
            for label in ("ALLOW","BLOCK","REVIEW")
            for rr in [[r for r in eligible if lookup[r["id"]]["expected"]==label]] if rr}
        result["unsupported_top_category_counts"]=dict(Counter(r["candidate_categories"][0] for r in pp if r["reference_category"] is None))
        results[precision]=result
    left=predictions["fp32"];right=predictions["int8"]
    pairs=[(left[k],right[k]) for k in sorted(left)]
    maximum=max(abs(a["category_probabilities"][c]-b["category_probabilities"][c]) for a,b in pairs for c in CATEGORIES)
    results["paired_precision"]=dict(n=len(pairs),top1_changed=sum(a["candidate_categories"][0]!=b["candidate_categories"][0] for a,b in pairs),
        candidate_set_changed=sum(set(a["candidate_categories"])!=set(b["candidate_categories"]) for a,b in pairs),
        fallback_changed=sum(a["fallback_required"]!=b["fallback_required"] for a,b in pairs),
        maximum_absolute_probability_change=maximum)
    write(state/"public/comparison.json",results)
    print(__import__("json").dumps({p:dict(accuracy=results[p]["metrics"]["accuracy"],macro_f1=results[p]["metrics"]["macro_f1"],
        coverage=results[p]["metrics"]["candidate_coverage"],p50_ms=results[p]["cpu"]["warm_latency_seconds"]["p50"]*1000) for p in ("fp32","int8")},indent=2))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--state",required=True);summarize(p.parse_args().state)
