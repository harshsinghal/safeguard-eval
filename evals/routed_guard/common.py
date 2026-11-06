"""Pinned model catalog, shared policy contract, and test-blind selection."""
import hashlib
import json
import math
from pathlib import Path
from collections import defaultdict
from evals.liquid_router.common import TRACK_CATEGORY
from evals.enterprise_benchmark.scoring import track_metrics

ROOT=Path(__file__).resolve().parents[2]
SEED=20261105
MODELS={
    "policylm":dict(model="musubilabs/policylm-1.7b",revision="b3b2cd408a08a68ab6a30c1fc1e440204e44d57e",parameters_billion=1.7,backend="native",block_cutoff=.335),
    "shieldstral":dict(model="mistralai/Shieldstral-1.0-3B",revision="003ec7e2b0bab5f0e6307edbaf186fa5822b76f5",parameters_billion=3.,backend="transformers",block_cutoff=.5),
    "kev":dict(model="jaredpalmer/kev-4b",revision="6cfce5c2fa4b4bd64026336ab649c5ca78857d52",parameters_billion=4.,backend="native",code_revision="2074cc44256200bb37540103fa4572901faa10f3",base="Qwen/Qwen3.5-4B-Base",base_revision="1001bb4d826a52d1f399e183466143f4da7b741b"),
    "clef":dict(model="Cloudflare/clef-flash",revision="f0b7d3cd65296abfe459e6c228b618f5d8b26d2f",parameters_billion=9.,backend="native"),
}
ORDER=tuple(MODELS)

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()
def digest(path):return sha(Path(path).read_bytes())
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
def write(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+".tmp");temp.write_text(json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+"\n");temp.replace(p)
def jsonl(path,records):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text("".join(canonical(r)+"\n" for r in records))
def policy_hash(policy):return sha(canonical(policy))
def labels_for(policy_id):
    # The contract is independent of the reference classes observed in a panel.
    return ("ALLOW","BLOCK","REVIEW") if policy_id in ("custom_policy-v0","injection_context-v0") else ("ALLOW","BLOCK")

def choice_request(content,policy,policy_id):
    if not isinstance(content,str) or not content.strip():raise ValueError("Empty input")
    criteria={"ALLOW":policy["allow"],"BLOCK":policy["block"]}
    if "REVIEW" in labels_for(policy_id):criteria["REVIEW"]=policy["review"]
    instructions="\n\n".join(str(policy.get(k,"")) for k in ("purpose","precedence","review"))
    return dict(state={"content":content},questions={"moderation":dict(type="choice",instructions=instructions,criteria=criteria)})

def typed_result(keys,logits):
    if set(keys) not in ({"ALLOW","BLOCK"},{"ALLOW","BLOCK","REVIEW"}) or len(keys)!=len(logits):raise ValueError("Decision-head contract mismatch")
    if not all(math.isfinite(float(x)) for x in logits):raise ValueError("Nonfinite decision output")
    exp=[math.exp(float(x)-max(logits)) for x in logits];total=sum(exp)
    probabilities={k:e/total for k,e in zip(keys,exp)}
    return dict(prediction=max(keys,key=probabilities.get),probabilities=probabilities,score=probabilities["BLOCK"])

def choose_model(router_result,selection):
    default=selection["default_model"]
    if default not in MODELS:raise ValueError("Unknown default guard")
    if router_result is None or router_result.get("fallback_required",True):return default,"router_fallback"
    categories=router_result.get("candidate_categories") or []
    model=selection.get("category_models",{}).get(categories[0] if categories else "",default)
    if model not in MODELS:raise ValueError("Unknown routed guard")
    return model,"category_route"

def report_metrics(cases,predictions,tracks,profiles):
    by_id={r["id"]:r for r in predictions}
    if len(by_id)!=len(predictions) or set(by_id)-{r["id"] for r in cases}:raise ValueError("Unknown/duplicate prediction IDs")
    for r in cases:
        if r["id"] in by_id and any(by_id[r["id"]].get(k)!=r[k] for k in ("input_sha256","policy_sha256")):
            raise ValueError("Unbound input/policy prediction")
    metrics={t:track_metrics([r for r in cases if r["track"]==t],by_id,spec["labels"]) for t,spec in tracks.items()}
    complete=all(m["n"] and not m["missing_reference_classes"] for m in metrics.values())
    blended={}
    for name,p in profiles.items():
        if not complete:blended[name]=None
        elif "task_weights" in p:blended[name]=100*sum(p["task_weights"][t]*m["macro_recall"] for t,m in metrics.items())
        else:
            score=0.
            for d,w in p["domain_weights"].items():
                members=[m["macro_recall"] for t,m in metrics.items() if tracks[t]["domain"]==d]
                score+=w*sum(members)/len(members)
            blended[name]=100*score
    n=len(cases)
    return dict(n=n,accuracy=sum(m["correct"] for m in metrics.values())/n,profiles=blended,tasks=metrics,
        error_rate=sum(m["error_rate"]*m["n"] for m in metrics.values() if m["n"])/n,
        scope="Pilot subset of fixed suite; class-balanced task scoring; errors/missing outputs count wrong")

def select_mapping(cases,predictions,tracks):
    # Only the calibration cases may enter this function. Caller binds their hashes.
    scores={};family_scores={}
    for model in ORDER:
        rr={r["id"]:r for r in predictions[model]}
        if set(rr)!={r["id"] for r in cases}:raise ValueError("Incomplete calibration outputs")
        task={t:track_metrics([r for r in cases if r["track"]==t],rr,spec["labels"]) for t,spec in tracks.items()}
        available={t:m["macro_recall"] for t,m in task.items() if m["n"] and m["macro_recall"] is not None}
        if not available:raise ValueError("No calibration task support")
        scores[model]=sum(available.values())/len(available)
        for category in sorted(set(TRACK_CATEGORY.values())):
            values=[v for t,v in available.items() if TRACK_CATEGORY.get(t)==category]
            if not values:raise ValueError("Missing family calibration: "+category)
            family_scores.setdefault(category,{})[model]=sum(values)/len(values)
    best=lambda values:max(ORDER,key=lambda m:(values[m],-ORDER.index(m)))
    return dict(default_model=best(scores),category_models={c:best(s) for c,s in family_scores.items()},
        calibration_model_scores=scores,calibration_category_scores=family_scores,
        selection="Equal available-task mean of reference-class recall on calibration; tie order "+",".join(ORDER),
        fallback_below=.6,unavailable_calibration_tasks=sorted(set(tracks)-{r["track"] for r in cases}))

def code_hashes():
    paths=list((ROOT/"evals/routed_guard").glob("*.py"))+[ROOT/"docs/routed-guard/PLAN.md",ROOT/"evals/decision_models/vendor-hashes.json"]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}
