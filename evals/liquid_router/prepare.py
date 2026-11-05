"""Restore fitting inputs from archived FIT splits, not the benchmark pool."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
from .common import *

META = {
    "harmful_requests": "published_runs/2026-10-31-contrastive-heads/metadata/wildguard/fit.jsonl.gz",
    "hate_speech": "published_runs/2026-10-31-contrastive-heads/metadata/hatexplain/fit.jsonl.gz",
    "injection": "published_runs/2026-11-02-prompt-injection/metadata/fit.jsonl.gz",
    "source_code": "published_runs/2026-11-03-malicious-artifacts/metadata/code/fit.jsonl",
    "skill_text": "published_runs/2026-11-03-malicious-artifacts/metadata/skills/fit.jsonl",
    "cyber_requests": "published_runs/2026-11-03-cyber-skill-guardrails/metadata/cyber/fit.jsonl",
    "agent_actions": "reports/stepguard-native/metadata/action/fit.jsonl",
    "agent_runs": "reports/stepguard-native/metadata/trajectory/fit.jsonl",
}

class Cache:
    def __init__(self, state, existing):
        from evals.enterprise_benchmark.sources import Restore
        self.restore = Restore(Path(state)/"restore")
        self.existing = Path(existing)
        self.old = read(self.existing/"source-manifest.json")
        self.used = {}
        self.excluded = []

    def fetch(self, key, url=None, expected=None):
        if key in self.old:
            entry = self.old[key]; old = self.existing/"sources"/key
            if old.exists():
                if digest(old) != entry["sha256"]:
                    raise ValueError("Cached input drift: "+key)
                self.used[key] = entry
                return old
            url = url or entry["url"]; expected = expected or entry["sha256"]
        if not url:
            raise ValueError("Missing pinned source: "+key)
        p = self.restore.fetch(key, url, expected)
        self.used[key] = self.restore.log[key]
        return p

def record(track, meta, prompt, role):
    from evals.prompt_injection.common import hash_value
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Missing text")
    if meta.get("prompt_sha256") not in (sha(prompt), hash_value(prompt)):
        raise ValueError("Source input hash mismatch: "+meta["id"])
    return dict(id="lr-"+sha(track+"\0"+meta["id"])[:24], track=track,
        category=TRACK_CATEGORY.get(track), role=role, text=prompt,
        input_sha256=sha(prompt), source_id=meta["id"],
        group=(TRACK_CATEGORY.get(track) or track)+"::"+str(meta.get("source_group", meta.get("group",meta["id"]))),
        expected=meta.get("expected"), label_provenance="benchmark_task_membership")

def restore_fit(cache, limit=512):
    import pyarrow.parquet as pq
    candidates=[]
    for track, path in META.items():
        for m in rows(ROOT/path):
            if m.get("clipped"):
                continue
            t = {"deepset":"injection_deepset", "safeguard":"injection_xtram"}[m["dataset"]] if track=="injection" else track
            candidates.append((t,m))
    by=defaultdict(list)
    for t,m in candidates:
        by[TRACK_CATEGORY[t]].append((t,m))
    chosen=[]
    for category, rr in sorted(by.items()):
        chosen.extend(sorted(rr,key=lambda tm:sha(str(SEED)+tm[0]+tm[1]["id"]))[:limit])
    wg=pq.read_table(cache.fetch("wildguard/wildguard_train.parquet")).to_pylist()
    hx=read(cache.fetch("hatexplain/dataset.json"))
    inj={}
    for ds in ("deepset","safeguard"):
        inj[ds]=pq.read_table(cache.fetch("injection/"+ds+"/train.parquet")).to_pylist()
    skills={r["benchmark_id"]:r for r in pq.read_table(cache.fetch("skills/primary.parquet")).to_pylist()}
    cyber={s:read(cache.fetch("cyber/"+s+".json")) for s in ("mitre","frr")}
    sg=rows(cache.fetch("stepguard/sft3k.jsonl"))
    manifest=read(ROOT/"published_runs/2026-11-03-malicious-artifacts/source-manifest.json")["files"]
    entries={Path(k).name:v for k,v in manifest.items() if k.startswith("sources/omc/packages/")}
    packages=sorted({m["package"] for t,m in chosen if t=="source_code"})
    def get_package(name):
        e=entries[name]
        return name,cache.fetch("code/"+name,e["url"],e["sha256"])
    with ThreadPoolExecutor(max_workers=2) as executor:
        package_paths=dict(executor.map(get_package,packages))
    from evals.malicious_artifacts.data import member_bytes
    from evals.stepguard.data import parse
    result=[]
    for track,m in chosen:
        if track=="harmful_requests":
            prompt=wg[m["source_index"]]["prompt"]
        elif track=="hate_speech":
            prompt=" ".join(hx[m["id"]]["post_tokens"])
        elif track.startswith("injection_"):
            ds,part,i=m["id"].split(":"); prompt=inj[ds][int(i)]["text"]
        elif track=="skill_text":
            prompt=skills[m["id"].split(":",1)[1]]["skill_text"]
        elif track=="source_code":
            raw=member_bytes(package_paths[m["package"]],m["member"])
            if sha(raw)!=m["file_sha256"]:
                raise ValueError("Code member checksum mismatch")
            prompt=raw.decode("utf-8-sig")
        elif track=="cyber_requests":
            _,source,index=m["id"].split(":"); prompt=cyber[source][int(index)][m.get("input_field","mutated_prompt")]
        else:
            index=m["source_index"]; prompt=parse(sg[index-1],index)["prompt"]
        if not isinstance(prompt,str) or not prompt.strip():
            cache.excluded.append(dict(track=track,id=m["id"],reason="empty_original_fitting_text"))
            continue
        result.append(record(track,m,prompt,"fit"))
    return result

def purge_overlap(records):
    """Known groups + normalized exact + approximate word5 near groups; held-out wins."""
    from datasketch import MinHash, MinHashLSH
    parent=list(range(len(records)))
    def root(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]]; i=parent[i]
        return i
    def union(a,b):
        a,b=root(a),root(b)
        if a!=b:
            parent[max(a,b)]=min(a,b)
    seen={}; index=MinHashLSH(threshold=.75,num_perm=64); sets={}; edges=0
    for i,r in enumerate(records):
        for key in ("g:"+r["group"],"x:"+sha(normalize(r["text"]))):
            if key in seen: union(i,seen[key])
            else: seen[key]=i
        words=re.findall(r"(?u)\w+",normalize(r["text"]))
        ss={" ".join(words[j:j+5]).encode() for j in range(max(0,len(words)-4))}
        if not ss: continue
        signature=MinHash(num_perm=64,seed=SEED); signature.update_batch(sorted(ss))
        for key in index.query(signature):
            other=sets[key]
            if len(ss&other)/len(ss|other)>=.90:
                union(i,int(key)); edges+=1
        key=str(i); sets[key]=ss; index.insert(key,signature)
    members=defaultdict(list)
    for i,r in enumerate(records): members[root(i)].append(r)
    kept=[]; excluded=[]
    precedence={"fit":0,"validation":1,"protected":2,"test":3}
    for rr in members.values():
        highest=max(precedence[r["role"]] for r in rr)
        group="lrg-"+sha("|".join(sorted(r["id"] for r in rr)))[:24]
        for r in rr:
            r["audit_group"]=group
            # Protected calibration and test cases jointly exclude development.
            if r["role"] in ("test","protected") or precedence[r["role"]]==highest:
                kept.append(r)
            else:
                excluded.append({k:v for k,v in r.items() if k!="text"})
    return kept,dict(excluded=excluded,near_edges=edges,method="known groups; NFKC/casefold/whitespace exact; 64-permutation word5 MinHash(.75) with exact Jaccard>=.90",limitation="Approximate retrieval can miss duplicates; no semantic or pretraining decontamination claim")

def prepare(state, existing):
    state=Path(state)
    if (state/"registration.json").exists(): raise ValueError("Already registered")
    cache=Cache(state,existing); fit=restore_fit(cache)
    benchmark=ROOT/"benchmarks/enterprise-moderation/v0.1"
    pool=rows(Path(existing)/"pool.jsonl")
    lookup={(r["track"],r["source_id"]):r for r in pool}
    held=[]
    for split,role in (("evaluation","test"),("calibration","protected")):
        for m in rows(benchmark/(split+".jsonl")):
            raw=lookup[(m["track"],m["source_id"])]
            held.append(record(m["track"],dict(raw["source_metadata"],source_group=raw["source_group"],prompt_sha256=raw["input_sha256"]),raw["prompt"],role))
    by=defaultdict(list)
    for r in pool:
        if r["split"]=="calibration" and r["track"] in TRACK_CATEGORY:
            by[TRACK_CATEGORY[r["track"]]].append(r)
    validation=[]
    protected_ids={r["id"] for r in held}
    for category,rr in sorted(by.items()):
        for r in sorted(rr,key=lambda r:sha(str(SEED)+r["id"])):
            v=record(r["track"],dict(r["source_metadata"],source_group=r["source_group"],prompt_sha256=r["input_sha256"]),r["prompt"],"validation")
            if v["id"] not in protected_ids: validation.append(v)
            if sum(x["category"]==category for x in validation)>=128: break
    retained,audit=purge_overlap(fit+validation+held)
    parts={s:sorted([r for r in retained if r["role"]==s],key=lambda r:r["id"]) for s in ("fit","validation","test")}
    for split in ("fit","validation"):
        counts=Counter(r["category"] for r in parts[split])
        if any(counts[c]<20 for c in CATEGORIES): raise ValueError("Insufficient "+split+" support: "+str(counts))
    report={"categories":CATEGORIES,"track_categories":TRACK_CATEGORY,"model":MODEL,"revision":REVISION,
        "seed":SEED,"max_tokens":MAX_TOKENS,"label_scope":"One benchmark-family reference per example; other applicable categories unannotated. Candidate routes are not semantic multilabel ground truth.",
        "source_hashes":{p:digest(ROOT/p) for p in META.values()},"sources":cache.used,
        "frozen_suite_manifest_sha256":digest(benchmark/"manifest.json"),
        "splits":{s:dict(n=len(rr),categories=dict(Counter(r["category"] or "unsupported_custom_policy" for r in rr)),
            original_decisions=dict(Counter(r["expected"] for r in rr)),groups=len({r["audit_group"] for r in rr})) for s,rr in parts.items()},
        "overlap_audit":audit,"source_exclusions":cache.excluded,"unsupported_category":"custom_policy; no training data; preserve as unknown/fallback diagnostic"}
    for s,rr in parts.items():
        jsonl(state/"data"/(s+".jsonl"),rr)
        jsonl(state/"public/metadata"/(s+".jsonl"),({k:v for k,v in r.items() if k!="text"} for r in rr))
    write(state/"public/data-audit.json",report)
    registration=dict(code_hashes=code_hashes(),input_hashes={s:digest(state/"data"/(s+".jsonl")) for s in parts},
        audit_sha256=digest(state/"public/data-audit.json"),protocol=read(ROOT/"docs/liquid-router/protocol.json"))
    write(state/"registration.json",registration); write(state/"public/registration.json",registration)
    print(json.dumps(report["splits"],indent=2),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--state",required=True); parser.add_argument("--existing",required=True)
    args=parser.parse_args(); prepare(args.state,args.existing)
