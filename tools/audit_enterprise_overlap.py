"""Private-input near-duplicate audit; publish IDs and similarities, not text."""
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datasketch import MinHash,MinHashLSH
from evals.enterprise_benchmark.sources import rows,dump

def audit(inputs):
    def shingles(text):
        words=re.findall(r"(?u)\w+",unicodedata.normalize("NFKC",text).casefold())
        return {" ".join(words[i:i+5]).encode() for i in range(max(0,len(words)-4))}
    def signature(ss):
        m=MinHash(num_perm=64,seed=20261105)
        if ss:m.update_batch(sorted(ss))
        return m
    evaluation=rows(Path(inputs)/"evaluation.jsonl");calibration=rows(Path(inputs)/"calibration.jsonl")
    index=MinHashLSH(threshold=.75,num_perm=64);sets={}
    for r in evaluation:
        ss=shingles(r["content"])
        if ss:sets[r["id"]]=ss;index.insert(r["id"],signature(ss))
    pairs=[];candidates=0
    for r in calibration:
        ss=shingles(r["content"])
        if not ss:continue
        for key in index.query(signature(ss)):
            candidates+=1;other=sets[key];similarity=len(ss&other)/len(ss|other)
            if similarity>=.90:pairs.append(dict(calibration_id=r["id"],evaluation_id=key,word5_jaccard=similarity))
    return dict(method="64-permutation 5-word MinHash candidates at .75; exact Jaccard >= .90",
        seed=20261105,evaluation=len(evaluation),calibration=len(calibration),candidate_pairs=candidates,
        high_similarity_pairs=pairs,limitation="Approximate retrieval may miss near duplicates; this is not a semantic-contamination or model-training-exposure audit.")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--inputs",required=True,type=Path);p.add_argument("--report",type=Path)
    a=p.parse_args();result=audit(a.inputs)
    if a.report:
        if a.report.exists():raise ValueError("Choose a new report file")
        dump(a.report,result)
    print(json.dumps(result,indent=2))
