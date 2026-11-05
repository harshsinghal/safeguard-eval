"""Verify fixed-cohort identity and exact bounded-view split independence."""
import argparse
from collections import defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.liquid_router.common import CATEGORIES,MODEL,REVISION,TRACK_CATEGORY,bounded_tokens,check_registration,digest,read,rows,sha,write

def verify_cohort(actual,fixed):
    def mapping(rr):
        result={}
        for r in rr:
            key=(r["track"],r["source_id"])
            if key in result:raise ValueError("Duplicate cohort item")
            result[key]=(r["input_sha256"],r["expected"])
        return result
    if mapping(actual)!=mapping(fixed):raise ValueError("Fixed evaluation cohort drift")
    if any(sha(r["text"])!=r["input_sha256"] for r in actual):raise ValueError("Evaluation text drift")
    if any(r["category"]!=TRACK_CATEGORY.get(r["track"]) for r in actual):raise ValueError("Routing category drift")
    return len(actual)

def verify(state,benchmark):
    state=Path(state);registration=check_registration(state,test=True)
    if registration["audit_sha256"]!=digest(state/"public/data-audit.json"):raise ValueError("Audit drift")
    data={s:rows(state/"data"/(s+".jsonl")) for s in ("fit","validation","test")}
    count=verify_cohort(data["test"],rows(Path(benchmark)/"evaluation.jsonl"))
    for a,b in (("fit","validation"),("fit","test"),("validation","test")):
        if {r["audit_group"] for r in data[a]} & {r["audit_group"] for r in data[b]}:raise ValueError("Cross-split audit groups")
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(MODEL,revision=REVISION,local_files_only=True)
    views=defaultdict(set)
    for split,rr in data.items():
        for r in rr:
            ids=tokenizer(r["text"],add_special_tokens=True,truncation=False)["input_ids"]
            views[tuple(bounded_tokens(ids))].add(split)
    conflicts=sum(len(roles)>1 for roles in views.values())
    if conflicts:raise ValueError("Identical bounded views across splits: "+str(conflicts))
    return dict(fixed_evaluation_hashes_match=count,cross_split_identical_bounded_views=conflicts,
        audit_groups_disjoint=True,registered_data_hashes_match=True,
        scope="Input-only integrity audit; no classifier predictions or final performance used")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--state",required=True)
    p.add_argument("--benchmark",default="benchmarks/enterprise-moderation/v0.1");p.add_argument("--report")
    a=p.parse_args();result=verify(a.state,a.benchmark)
    if a.report:write(a.report,result)
    print(__import__("json").dumps(result,indent=2))
