"""Restore frozen inference inputs without reclustering or exporting reference labels."""
import argparse
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.enterprise_benchmark.sources import ROOT,rows,jsonl,sha
from evals.enterprise_benchmark.scoring import verify_bundle

def export(bundle,state,out):
    bundle,state,out=Path(bundle),Path(state),Path(out)
    verify_bundle(bundle)
    if out.exists():raise ValueError("Choose a new output directory")
    if out.resolve().is_relative_to(ROOT.resolve()):
        ignored=subprocess.run(["git","check-ignore","--quiet",str(out)],cwd=ROOT).returncode==0
        if not ignored:raise ValueError("Use an ignored work directory or a path outside the repository")
    pool={r["id"]:r for r in rows(state/"pool.jsonl")}
    result={}
    for split in ("evaluation","calibration"):
        inputs=[]
        for case in rows(bundle/(split+".jsonl")):
            source=pool[case["track"]+"::"+case["source_id"]]
            if source["expected"]!=case["expected"] or sha(source["prompt"])!=case["input_sha256"]:
                raise ValueError("Restored source differs: "+case["id"])
            inputs.append(dict(id=case["id"],policy_id=case["policy_id"],content=source["prompt"],
                input_sha256=case["input_sha256"],policy_sha256=case["policy_sha256"]))
        jsonl(out/(split+".jsonl"),inputs);result[split]=len(inputs)
    return result

if __name__=="__main__":
    import json
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("bundle","state","out"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.bundle,a.state,a.out)))
