"""Restore pinned benchmark inputs as inert private data; never execute artifacts."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
SEED=20261105
def sha(x):
    return hashlib.sha256(x if isinstance(x,bytes) else x.encode()).hexdigest()
def read(path):
    b=Path(path).read_bytes()
    if str(path).endswith(".gz"):b=gzip.decompress(b)
    return json.loads(b)
def rows(path):
    b=Path(path).read_bytes()
    if str(path).endswith(".gz"):b=gzip.decompress(b)
    return [json.loads(x) for x in b.decode().split("\n") if x.strip()]
def dump(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
def jsonl(path,rr):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in rr))

class Restore:
    def __init__(self,state):
        self.state=Path(state)
        self.log=read(self.state/"source-manifest.json") if (self.state/"source-manifest.json").exists() else {}
        self.pool=rows(self.state/"pool.jsonl") if (self.state/"pool.jsonl").exists() else []
        self.status=read(self.state/"restore-status.json") if (self.state/"restore-status.json").exists() else {}
    def fetch(self,key,url,expected=None,max_bytes=100*1024*1024):
        p=self.state/"sources"/key
        if not p.resolve().is_relative_to((self.state/"sources").resolve()):raise ValueError("Unsafe cache path")
        if urllib.parse.urlsplit(url).hostname not in ("huggingface.co","raw.githubusercontent.com","api.github.com"):raise ValueError("Unapproved source host")
        if not p.exists():
            headers={"User-Agent":"SafeguardEvalBenchmarkResearch/1.0"}
            if "huggingface.co/datasets/allenai/wildguardmix/" in url:
                from huggingface_hub import get_token
                token_path=os.environ.get("HF_TOKEN_FILE")
                token=Path(token_path).read_text().strip() if token_path else get_token()
                if token and token.startswith("HF_TOKEN="):token=token.split("=",1)[1].strip().strip(chr(34)).strip(chr(39))
                if token:headers["Authorization"]="Bearer "+token
            request=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(request,timeout=120) as response:b=response.read(max_bytes+1)
            if len(b)>max_bytes:raise ValueError("Source exceeds byte limit: "+key)
            if expected and sha(b)!=expected:raise ValueError("Source checksum mismatch: "+key)
            p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+".partial")
            tmp.write_bytes(b);tmp.replace(p)
        b=p.read_bytes()
        if expected and sha(b)!=expected:raise ValueError("Cached source mismatch: "+key)
        self.log[key]={"url":url,"sha256":sha(b),"bytes":len(b)}
        return p
    def add(self,track,meta,text,legacy=False,**extra):
        from evals.prompt_injection.common import hash_value
        expected=meta.get("prompt_sha256")
        actual=hash_value(text) if legacy else sha(text)
        if expected and expected!=actual:raise ValueError("Restored input mismatch: "+meta["id"])
        role="calibration" if meta["split"] in ("validation","dev") else "evaluation"
        row=dict(id=track+"::"+meta["id"],source_id=meta["id"],track=track,split=role,
            expected=meta["expected"],source_group=str(meta.get("group",meta["id"])),
            prompt=text,input_sha256=sha(text),source_metadata={k:v for k,v in meta.items() if k!="prompt"},**extra)
        if meta.get("clipped"):return
        self.pool.append(row)
    def metadata(self,path):
        return rows(ROOT/path)
    def wildguard(self):
        import pyarrow.parquet as pq
        rev="d29c47f41c8b51348b5c8e8c81c039b3132b66d1"
        base=f"https://huggingface.co/datasets/allenai/wildguardmix/resolve/{rev}/"
        parts={}
        for split,part in [("evaluation","test/wildguard_test.parquet"),("calibration","train/wildguard_train.parquet")]:
            path=self.fetch("wildguard/"+Path(part).name,base+part)
            parts[split]=pq.read_table(path).to_pylist()
        for split in ("test","validation"):
            for m in self.metadata(f"published_runs/2026-10-31-contrastive-heads/metadata/wildguard/{split}.jsonl.gz"):
                m=dict(m,split=split)
                source=parts["evaluation" if split=="test" else "calibration"]
                index=m.get("source_index",int(m["id"].rsplit("-",1)[1]))
                raw=source[index];self.add("harmful_requests",m,raw["prompt"])
    def hatexplain(self):
        rev="01d742279dac941981f53806154481c0e15ee686"
        hashes=read(ROOT/"docs/hatexplain/data-manifest.json")["source_hashes"]
        raw=read(self.fetch("hatexplain/dataset.json",f"https://raw.githubusercontent.com/hate-alert/HateXplain/{rev}/Data/dataset.json",hashes["dataset.json"]))
        for split in ("test","validation"):
            for m in self.metadata(f"published_runs/2026-10-31-contrastive-heads/metadata/hatexplain/{split}.jsonl.gz"):
                self.add("hate_speech",dict(m,split=split)," ".join(raw[m["id"]]["post_tokens"]))
    def injections(self):
        import pyarrow.parquet as pq
        manifest=read(ROOT/"docs/prompt-injection/preparation/source-manifest.json")
        maps={}
        for key,entry in manifest.items():
            if not (key.endswith(".parquet") or key in ("jbb/GCG.json","jbb/PAIR.json")):continue
            p=self.fetch("injection/"+key,entry["url"],entry["sha256"])
            if key.endswith(".parquet"):
                ds,part=key.split("/");part=part.removesuffix(".parquet")
                for i,r in enumerate(pq.read_table(p).to_pylist()):
                    maps[f"{ds}:{part}:{i}"]=r["prompt"] if ds=="notinject" else r["text"]
            else:
                method=Path(key).stem
                for i,r in enumerate(read(p)["jailbreaks"]):
                    if isinstance(r.get("prompt"),str) and r["prompt"].strip():
                        maps[f"jbb:{method}:{i}"]=r["prompt"]
        tracks={"deepset":"injection_deepset","safeguard":"injection_xtram","notinject":"benign_lookalikes","jbb":"jailbreak_attempts"}
        for split in ("test","validation"):
            for m in self.metadata(f"published_runs/2026-11-02-prompt-injection/metadata/{split}.jsonl.gz"):
                self.add(tracks[m["dataset"]],m,maps[m["id"]])
    def artifacts(self):
        import pyarrow.parquet as pq
        from evals.malicious_artifacts.data import member_bytes
        root=ROOT/"published_runs/2026-11-03-malicious-artifacts"
        manifest=read(root/"source-manifest.json")["files"]
        entry=manifest["sources/skills/primary.parquet"]
        raw={r["benchmark_id"]:r for r in pq.read_table(self.fetch("skills/primary.parquet",entry["url"],entry["sha256"])).to_pylist()}
        code=[]
        for split in ("test","validation"):
            for m in rows(root/f"metadata/skills/{split}.jsonl"):
                if not m["clipped"]:self.add("skill_text",m,raw[m["id"].split(":",1)[1]]["skill_text"],legacy=True)
            code += [m for m in rows(root/f"metadata/code/{split}.jsonl") if not m["clipped"]]
        packages={m["package"] for m in code}
        entries={Path(key).name:entry for key,entry in manifest.items() if key.startswith("sources/omc/packages/") and Path(key).name in packages}
        def fetch_package(name):
            e=entries[name];return name,self.fetch("code/"+name,e["url"],e["sha256"])
        with ThreadPoolExecutor(max_workers=4) as pool:
            restored=dict(pool.map(fetch_package,sorted(packages)))
        for m in code:
            b=member_bytes(restored[m["package"]],m["member"])
            if sha(b)!=m["file_sha256"]:raise ValueError("Archive member drift")
            self.add("source_code",m,b.decode("utf-8"),legacy=True)
    def cyber(self):
        root=ROOT/"published_runs/2026-11-03-cyber-skill-guardrails"
        manifest=read(root/"source-manifest.json");rev=manifest["purple_revision"]
        tree=read(self.fetch("cyber/tree.json",f"https://api.github.com/repos/meta-llama/PurpleLlama/git/trees/{rev}?recursive=1"))
        candidates=[r["path"] for r in tree["tree"] if r["path"].endswith(".json")]
        data={}
        for kind,pattern in [("mitre","mitre_benchmark_100_per_category_with_augmentation.json"),("frr","mitre_frr.json")]:
            paths=[p for p in candidates if p.endswith("/"+pattern)]
            if len(paths)!=1:raise ValueError("Ambiguous cyber source "+kind+": "+repr(paths))
            data[kind]=read(self.fetch("cyber/"+kind+".json",f"https://raw.githubusercontent.com/meta-llama/PurpleLlama/{rev}/"+paths[0],manifest["source_files"]["sources/"+kind+".json"]))
        for split in ("test","validation"):
            for m in rows(root/f"metadata/cyber/{split}.jsonl"):
                _,source,index=m["id"].split(":")
                self.add("cyber_requests",m,data[source][int(index)][m.get("input_field","mutated_prompt")],legacy=True)
    def skill_packages(self):
        root=ROOT/"published_runs/2026-11-03-cyber-skill-guardrails"
        rev=read(root/"source-manifest.json")["skill_revision"]
        packages={r["id"]:r for r in rows(root/"package-manifest.jsonl")}
        meta=[m for split in ("test","validation") for m in rows(root/f"metadata/skills/{split}.jsonl")]
        needed={}
        for m in meta:
            package=packages[m["id"]]
            for f in package["files"]:
                rel=package["source_path"]+"/"+f["path"]
                needed[rel]=f
        def one(item):
            rel,f=item
            path=self.fetch("malskill/"+rel,f"https://raw.githubusercontent.com/lxyeternal/MalSkillBench/{rev}/"+urllib.parse.quote(rel),max_bytes=4*1024*1024)
            b=path.read_bytes()
            if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=f["git_blob"]:raise ValueError("Package Git blob drift")
            return rel,b.decode("utf-8-sig")
        with ThreadPoolExecutor(max_workers=4) as pool:texts=dict(pool.map(one,sorted(needed.items())))
        for m in meta:
            p=packages[m["id"]]
            text="\n\n".join("FILE "+f["path"]+"\n"+texts[p["source_path"]+"/"+f["path"]] for f in sorted(p["files"],key=lambda f:(f["path"]!="SKILL.md",f["path"])))
            self.add("skill_packages",m,text,legacy=True)
    def stepguard(self):
        from evals.stepguard.data import parse
        url="https://huggingface.co/datasets/ninty-seven/stepguard_data/resolve/aadeae009800d8fbcd145575f1d1a6b37abb0950/sft3k/agentguard_sft3k_sharegpt.jsonl"
        source=self.fetch("stepguard/sft3k.jsonl",url,"6429dc6f958e2b1fe242f2528dc6087c62e60e903263cf57dd88bc949752c90d")
        raw=rows(source)
        for task,track in [("action","agent_actions"),("trajectory","agent_runs")]:
            for split in ("test","validation"):
                for m in self.metadata(f"reports/stepguard-native/metadata/{task}/{split}.jsonl"):
                    r=parse(raw[m["source_index"]-1],m["source_index"])
                    if r["expected"]!=m["expected"]:raise ValueError("StepGuard source labels changed")
                    self.add(track,m,r["prompt"],legacy=True)
    def synthetic(self):
        for track,path in [("custom_policy","evals/religious_iconography.jsonl"),("injection_context","evals/injection/challenge.jsonl")]:
            for m in rows(ROOT/path):self.add(track,m,m["prompt"])
    def run(self,only=None):
        methods=["wildguard","hatexplain","injections","artifacts","cyber","skill_packages","stepguard","synthetic"]
        for name in methods:
            if only and name not in only:continue
            if self.status.get(name,{}).get("status")=="ready":continue
            start=len(self.pool)
            try:
                getattr(self,name)();self.status[name]={"status":"ready","rows":len(self.pool)-start}
            except Exception as exc:
                self.pool=self.pool[:start]
                self.status[name]={"status":"unavailable","error_type":type(exc).__name__,"reason":str(exc)[:300]}
            dump(self.state/"restore-status.json",self.status)
            dump(self.state/"source-manifest.json",self.log)
            jsonl(self.state/"pool.jsonl",self.pool)
            print(json.dumps({"source_family":name,**self.status[name]}),flush=True)
        return self.status

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--state",type=Path,required=True)
    p.add_argument("--only",nargs="*");a=p.parse_args();Restore(a.state).run(a.only)
