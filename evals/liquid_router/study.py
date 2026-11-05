"""Bounded local fitting, validation-only selection, freeze, and CPU evaluation."""
import argparse
from collections import Counter
import contextlib
import gc
import json
import math
import os
from pathlib import Path
import subprocess
import threading
import time
import numpy as np
from .common import *


def metrics(records, logits, candidate_count=1):
    from sklearn.metrics import accuracy_score,confusion_matrix,f1_score,recall_score
    known=[i for i,r in enumerate(records) if r["category"] in CATEGORIES]
    y=np.asarray([CATEGORIES.index(records[i]["category"]) for i in known])
    z=np.asarray(logits)[known]
    if z.shape!=(len(y),len(CATEGORIES)) or not np.isfinite(z).all():
        raise ValueError("Invalid logits")
    ranks=np.argsort(-z,axis=1,kind="stable"); predicted=ranks[:,0]
    per={c:dict(n=int(sum(y==j)),recall=float(np.mean(predicted[y==j]==j)) if np.any(y==j) else None,
        candidate_coverage=float(np.mean(np.any(ranks[y==j,:candidate_count]==j,axis=1))) if np.any(y==j) else None)
        for j,c in enumerate(CATEGORIES)}
    return dict(n=len(y),excluded_unsupported=len(records)-len(y),accuracy=float(accuracy_score(y,predicted)),
        macro_f1=float(f1_score(y,predicted,labels=list(range(len(CATEGORIES))),average="macro",zero_division=0)),
        macro_recall=float(recall_score(y,predicted,labels=list(range(len(CATEGORIES))),average="macro",zero_division=0)),
        candidate_coverage=float(np.mean(np.any(ranks[:,:candidate_count]==y[:,None],axis=1))),
        candidate_count=candidate_count,per_category=per,
        confusion_matrix=confusion_matrix(y,predicted,labels=list(range(len(CATEGORIES)))).tolist())


def choose_policy(records, logits):
    from scipy.special import logsumexp
    y=np.asarray([CATEGORIES.index(r["category"]) for r in records])
    temperature=min((.5,1.,2.,3.),key=lambda t:float(np.mean(logsumexp(logits/t,axis=1)-logits[np.arange(len(y)),y]/t)))
    ranks=np.argsort(-logits,axis=1,kind="stable")
    coverage={k:float(np.mean(np.any(ranks[:,:k]==y[:,None],axis=1))) for k in (1,2,3)}
    k=next((k for k in (1,2,3) if coverage[k]>=.95),3)
    return dict(temperature=temperature,candidate_count=k,fallback_below=.6,
        validation_candidate_coverage=coverage[k],coverage_target_met=coverage[k]>=.95,
        coverage_grid=coverage)


class ModerateGPU:
    """Sampled monitor plus synchronization and idle time, not hardware power limiting."""
    def __init__(self,state):
        self.state=Path(state); self.samples=[]; self.finish=threading.Event(); self.failure=None
        self.started=time.monotonic(); self.active=0.; self.latest=None

    def poll(self):
        over=0
        while not self.finish.is_set():
            try:
                out=subprocess.check_output(["nvidia-smi","--query-gpu=temperature.gpu,power.draw,utilization.gpu,memory.used","--format=csv,noheader,nounits"],text=True,timeout=5).strip().splitlines()[0]
                temp,power,util,memory=map(float,out.split(","))
                self.latest=dict(seconds=time.monotonic()-self.started,temperature_c=temp,power_w=power,utilization_pct=util,memory_mib=memory)
                self.samples.append(self.latest)
                over=over+1 if power>250 else 0
                if temp>=70 or over>=3:
                    self.failure="Thermal/power stop threshold reached"
            except Exception as exc:
                self.failure="GPU telemetry unavailable: "+type(exc).__name__
            self.finish.wait(.5)

    def __enter__(self):
        self.thread=threading.Thread(target=self.poll,daemon=True);self.thread.start()
        deadline=time.monotonic()+10
        while self.latest is None:
            if self.failure or time.monotonic()>deadline:raise RuntimeError(self.failure or "No telemetry")
            time.sleep(.05)
        return self

    def run(self,fn):
        import torch
        while self.latest and (self.latest["temperature_c"]>60 or self.latest["power_w"]>180):
            if self.failure:raise RuntimeError(self.failure)
            time.sleep(.5)
        if self.failure:raise RuntimeError(self.failure)
        torch.cuda.synchronize();start=time.monotonic()
        value=fn();torch.cuda.synchronize();duration=time.monotonic()-start
        self.active+=duration
        time.sleep(max(.01,duration*4))
        if self.failure:raise RuntimeError(self.failure)
        return value

    def __exit__(self,*exc):
        self.finish.set();self.thread.join(timeout=7)
        elapsed=time.monotonic()-self.started
        write(self.state/"public/gpu-resources.json",dict(samples=self.samples,
            elapsed_seconds=elapsed,active_operation_seconds=self.active,
            operation_duty_fraction=self.active/max(elapsed,1),
            sampled_peak_temperature_c=max((x["temperature_c"] for x in self.samples),default=None),
            sampled_peak_power_w=max((x["power_w"] for x in self.samples),default=None),
            stop_reason=self.failure,hardware_power_or_clock_settings_changed=False,
            paid_compute=False,limitation="Sampled telemetry may miss instantaneous peaks; software duty is not a hardware power cap"))


def infer(model,tokenizer,encoded,budget,features=False):
    import torch
    from .model import batch
    model.eval();head=model.head
    if features:model.head=torch.nn.Identity()
    output=[]
    try:
        with torch.inference_mode():
            for ids in encoded:
                def operation():
                    with torch.autocast("cuda",dtype=torch.bfloat16):
                        return model(**batch(tokenizer,[ids],"cuda")).float().cpu().numpy()[0]
                output.append(budget.run(operation))
    finally:model.head=head
    return np.asarray(output,dtype=np.float32)


def train(state):
    import joblib
    import platform
    import sklearn
    import torch
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from .model import batch,encode,load_initial
    state=Path(state);registration=check_registration(state)
    if (state/"freeze.json").exists() or (state/"public/training-history.json").exists():
        raise ValueError("Use a new state for another run")
    torch.set_num_threads(4)
    if not torch.cuda.is_available():raise RuntimeError("CUDA is required for this bounded fitting run; inference remains CPU")
    torch.manual_seed(SEED);np.random.seed(SEED)
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    fit=rows(state/"data/fit.jsonl");val=rows(state/"data/validation.jsonl")
    y=np.asarray([CATEGORIES.index(r["category"]) for r in fit])
    yv=np.asarray([CATEGORIES.index(r["category"]) for r in val])
    control=make_pipeline(TfidfVectorizer(ngram_range=(1,2),max_features=40000,sublinear_tf=True,dtype=np.float32),
        LogisticRegression(C=1.,class_weight="balanced",max_iter=1500))
    control.fit([r["text"] for r in fit],y)
    control_logits=control.decision_function([r["text"] for r in val])
    joblib.dump(control,state/"tfidf.joblib")
    write(state/"public/tfidf-validation.json",metrics(val,control_logits))
    print("TFIDF validation",json.dumps(metrics(val,control_logits)),flush=True)
    model,tokenizer=load_initial("cuda")
    encoded={};token_report={}
    for split,rr in (("fit",fit),("validation",val)):
        pairs=[encode(tokenizer,r["text"]) for r in rr]
        encoded[split]=[p[0] for p in pairs]
        token_report[split]=dict(n=len(rr),truncated=sum(n>MAX_TOKENS for _,n in pairs),
            original_token_quantiles=np.quantile([n for _,n in pairs],[0,.5,.9,.99,1]).tolist())
    history=[];best_score=-1.;best_path=None;best_logits=None
    start=time.monotonic()
    write(state/"public/environment.json",dict(python=platform.python_version(),torch=torch.__version__,
        transformers=__import__("transformers").__version__,sklearn=sklearn.__version__,
        cpu=platform.processor(),gpu=torch.cuda.get_device_name(0),model=MODEL,revision=REVISION,
        parameters=sum(p.numel() for p in model.parameters()),tokenization=token_report))
    with ModerateGPU(state) as budget:
        feature_fit=infer(model,tokenizer,encoded["fit"],budget,features=True)
        feature_val=infer(model,tokenizer,encoded["validation"],budget,features=True)
        linear=LogisticRegression(C=1.,class_weight="balanced",max_iter=1500).fit(feature_fit,y)
        with torch.no_grad():
            model.head.weight.copy_(torch.tensor(linear.coef_,device="cuda",dtype=torch.float32))
            model.head.bias.copy_(torch.tensor(linear.intercept_,device="cuda",dtype=torch.float32))
        del feature_fit,feature_val;gc.collect()
        logits=infer(model,tokenizer,encoded["validation"],budget)
        score=metrics(val,logits)
        path=state/"checkpoints/frozen"
        model.save(path,tokenizer,dict(kind="frozen_encoder_linear_head",candidate_count=1))
        best_score=score["macro_f1"];best_path=path;best_logits=logits
        history.append(dict(kind="frozen",validation=score,checkpoint=str(path.relative_to(state)),elapsed_seconds=time.monotonic()-start))
        write(state/"public/training-history.json",history)
        print("FROZEN validation",json.dumps(score),flush=True)
        optimizer=torch.optim.AdamW(model.parameters(),lr=5e-5,weight_decay=.01)
        counts=np.bincount(y,minlength=len(CATEGORIES));weights=torch.tensor(len(y)/(len(CATEGORIES)*counts),dtype=torch.float32,device="cuda")
        stop_budget=False
        for epoch in range(1,4):
            order=np.random.default_rng(SEED+epoch).permutation(len(fit));losses=[]
            model.train();optimizer.zero_grad(set_to_none=True)
            for position,index in enumerate(order):
                if time.monotonic()-start>2700:
                    stop_budget=True;break
                window_start=(position//16)*16;window_n=min(16,len(order)-window_start)
                def operation():
                    with torch.autocast("cuda",dtype=torch.bfloat16):
                        logits=model(**batch(tokenizer,[encoded["fit"][int(index)]],"cuda"))
                        # reduction=sum retains the intended class weight for microbatch one.
                        loss=torch.nn.functional.cross_entropy(logits,torch.tensor([y[index]],device="cuda"),weight=weights,reduction="sum")
                    if not torch.isfinite(loss):raise ValueError("Nonfinite training loss")
                    (loss/window_n).backward()
                    if (position+1)%16==0 or position+1==len(order):
                        torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
                        optimizer.step();optimizer.zero_grad(set_to_none=True)
                    return float(loss.detach())
                losses.append(budget.run(operation))
                if (position+1)%256==0:
                    print("TRAIN",epoch,position+1,"/",len(order),"loss",round(float(np.mean(losses[-256:])),4),"elapsed",round(time.monotonic()-start),flush=True)
            if stop_budget:
                history.append(dict(kind="budget_stop",epoch=epoch,completed_microbatches=len(losses),elapsed_seconds=time.monotonic()-start));break
            logits=infer(model,tokenizer,encoded["validation"],budget);score=metrics(val,logits)
            path=state/"checkpoints"/("epoch-"+str(epoch));model.save(path,tokenizer,dict(kind="full_finetune",epoch=epoch,candidate_count=1))
            history.append(dict(kind="full_finetune",epoch=epoch,validation=score,mean_fit_loss=float(np.mean(losses)),
                checkpoint=str(path.relative_to(state)),elapsed_seconds=time.monotonic()-start))
            if score["macro_f1"]>best_score:
                best_score=score["macro_f1"];best_path=path;best_logits=logits
            write(state/"public/training-history.json",history)
            print("EPOCH",epoch,json.dumps(score),flush=True)
        write(state/"public/training-history.json",history)
        policy=choose_policy(val,best_logits)
        config=read(best_path/"router.json");config.update(policy);write(best_path/"router.json",config)
        freeze=dict(checkpoint=str(best_path.relative_to(state)),policy=policy,
            validation=metrics(val,best_logits,policy["candidate_count"]),
            registration_sha256=digest(state/"registration.json"),code_hashes=code_hashes(),
            checkpoint_hashes={str(p.relative_to(best_path)):digest(p) for p in sorted(best_path.rglob("*")) if p.is_file()},
            elapsed_seconds=time.monotonic()-start,budget_stopped=stop_budget)
        write(state/"freeze.json",freeze);write(state/"public/selection-freeze.json",freeze)
        print("FROZEN SELECTION",freeze["checkpoint"],json.dumps(policy),flush=True)
    del optimizer,model;gc.collect();torch.cuda.empty_cache()


def evaluate(state,precision):
    import joblib
    import platform
    import psutil
    import resource
    import torch
    from .model import Router
    state=Path(state);check_registration(state,test=True);freeze=read(state/"freeze.json")
    if freeze["registration_sha256"]!=digest(state/"registration.json") or freeze["code_hashes"]!=code_hashes():
        raise ValueError("Freeze mismatch")
    checkpoint=state/freeze["checkpoint"]
    for rel,h in freeze["checkpoint_hashes"].items():
        if digest(checkpoint/rel)!=h:raise ValueError("Checkpoint changed")
    folder=state/"public"/precision
    if folder.exists():raise ValueError("Preserve completed output; choose a new run")
    records=rows(state/"data/test.jsonl");start=time.monotonic()
    router=Router(checkpoint,threads=4,int8=precision=="int8")
    load_seconds=time.monotonic()-start
    for _ in range(3):router.predict("Summarize the quarterly report.")
    probabilities=[];outputs=[];times=[]
    for i,r in enumerate(records):
        start=time.perf_counter();out=router.predict(r["text"]);elapsed=time.perf_counter()-start
        times.append(elapsed);probabilities.append([out["category_probabilities"][c] for c in CATEGORIES])
        outputs.append(dict(id=r["id"],track=r["track"],reference_category=r["category"],
            input_sha256=r["input_sha256"],**out,latency_seconds=elapsed))
        if (i+1)%128==0:print("CPU",precision,i+1,"/",len(records),flush=True)
    probabilities=np.asarray(probabilities)
    report=dict(precision=precision,metrics=metrics(records,probabilities,freeze["policy"]["candidate_count"]),
        per_track={t:metrics([r for r in records if r["track"]==t],probabilities[[i for i,r in enumerate(records) if r["track"]==t]],freeze["policy"]["candidate_count"])
            for t in sorted({r["track"] for r in records if r["category"] is not None})},
        fallback_rate=float(np.mean([r["fallback_required"] for r in outputs])),
        unsupported_custom_policy=dict(n=sum(r["category"] is None for r in records),
            fallback_rate=float(np.mean([out["fallback_required"] for r,out in zip(records,outputs) if r["category"] is None]))),
        cpu=dict(threads=4,batch_size=1,platform=platform.platform(),cpu_model=next((l.split(":",1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("model name")),platform.processor()),
            cold_load_seconds=load_seconds,rss_after_evaluation_bytes=psutil.Process().memory_info().rss,
            process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            warm_latency_seconds=dict(p50=float(np.quantile(times,.5)),p95=float(np.quantile(times,.95)),p99=float(np.quantile(times,.99)),mean=float(np.mean(times))),
            latency_scope="one serial pass across fixed cases, includes tokenization and dispatch; excludes cold load; mixed input lengths; no concurrency",torch=torch.__version__),
        truncation_rate=float(np.mean([r["truncated"] for r in outputs])))
    control=joblib.load(state/"tfidf.joblib")
    report["tfidf_control"]=metrics(records,control.decision_function([r["text"] for r in records]),freeze["policy"]["candidate_count"])
    jsonl(folder/"predictions.jsonl",outputs);write(folder/"results.json",report)
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("action",choices=["train","evaluate"])
    parser.add_argument("--state",required=True);parser.add_argument("--precision",choices=["fp32","int8"],default="fp32")
    a=parser.parse_args()
    if a.action=="train":train(a.state)
    else:evaluate(a.state,a.precision)
