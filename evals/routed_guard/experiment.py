"""Pilot selection, local serving lifecycle, fresh calibration and end-to-end tests."""
import argparse
from collections import Counter,defaultdict
import gc
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from .common import *
from .server import http,free_port


def pilot_cases(cases,tracks,per_task=8):
    selected=[]
    for track,spec in sorted(tracks.items()):
        labels=spec["labels"];quota={label:per_task//len(labels)+(i<per_task%len(labels)) for i,label in enumerate(labels)}
        candidates=[r for r in cases if r["track"]==track];used=Counter()
        for label,n in quota.items():
            count=0
            for r in sorted([r for r in candidates if r["expected"]==label],key=lambda r:sha(str(SEED)+r["id"])):
                if used[r["group"]]>=2:continue
                selected.append(r);used[r["group"]]+=1;count+=1
                if count==n:break
            if count<n:raise ValueError("Insufficient pilot stratum: "+track+"/"+label)
    return sorted(selected,key=lambda r:r["id"])


def prepare(state,inputs,checkpoint,vendor,policy_python):
    from evals.enterprise_benchmark.scoring import verify_bundle
    state=Path(state);bundle=ROOT/"benchmarks/enterprise-moderation/v0.1"
    if (state/"config.private.json").exists():raise ValueError("Choose a new pilot state")
    verify_bundle(bundle);tracks=read(bundle/"tracks.json");policies=read(bundle/"policies.json")
    cal=rows(bundle/"calibration.jsonl");test=pilot_cases(rows(bundle/"evaluation.jsonl"),tracks)
    if {r["group"] for r in cal}&{r["group"] for r in test}:raise ValueError("Cross-role groups")
    manifests={}
    for split,source,meta in (("calibration","calibration",cal),("test","evaluation",test)):
        lookup={r["id"]:r for r in rows(Path(inputs)/(source+".jsonl"))}
        data=[]
        for m in meta:
            r=lookup[m["id"]]
            if set(r)!={"id","content","policy_id","input_sha256","policy_sha256"}:raise ValueError("Unexpected model-facing fields")
            if any(r[k]!=m[k] for k in ("input_sha256","policy_sha256","policy_id")) or sha(r["content"])!=r["input_sha256"]:raise ValueError("Input drift")
            if policy_hash(policies[r["policy_id"]])!=r["policy_sha256"]:raise ValueError("Policy drift")
            data.append(r)
        jsonl(state/"data"/(split+".jsonl"),data);jsonl(state/"public/metadata"/(split+".jsonl"),meta)
        manifests[split]=dict(n=len(meta),input_sha256=digest(state/"data"/(split+".jsonl")),
            metadata_sha256=digest(state/"public/metadata"/(split+".jsonl")),
            tasks=dict(Counter(r["track"] for r in meta)),labels=dict(Counter(r["expected"] for r in meta)))
    config=dict(instance_id=uuid.uuid4().hex,router_checkpoint=str(Path(checkpoint).resolve()),vendor=str(Path(vendor).resolve()),
        interpreters={"policylm":str(Path(policy_python).absolute())},policies=policies,
        selection_path=str((state/"selection.json").resolve()),runtime_dir=str((state/"runtime").resolve()),max_context=16384)
    write(state/"config.private.json",config)
    write(state/"public/data-audit.json",dict(source_suite_manifest_sha256=digest(bundle/"manifest.json"),
        splits=manifests,selection="Stable hash, at most eight per task, equal class quotas; max two from a group within a task",seed=SEED,
        original_suite_untouched=True,calibration_groups_disjoint=True,serving_features=["content","policy_id"],
        policy_is_trusted_application_configuration=True,router_features=["content"]))
    print(canonical(manifests),flush=True)


def register(state):
    state=Path(state)
    if (state/"registration.json").exists():raise ValueError("Already registered")
    config=read(state/"config.private.json");checkpoint=Path(config["router_checkpoint"])
    r=dict(code_hashes=code_hashes(),models=MODELS,data_audit_sha256=digest(state/"public/data-audit.json"),
        private_input_hashes={s:digest(state/"data"/(s+".jsonl")) for s in ("calibration","test")},
        metadata_hashes={s:digest(state/"public/metadata"/(s+".jsonl")) for s in ("calibration","test")},
        policies_sha256=sha(canonical(config["policies"])),max_context=config["max_context"],
        router_checkpoint_hashes={str(p.relative_to(checkpoint)):digest(p) for p in sorted(checkpoint.rglob("*")) if p.is_file()},
        pilot=True,calibration_limit_seconds=5400,test_limit_seconds=5400)
    write(state/"registration.json",r);write(state/"public/registration.json",r)
    print("Registered four-model mandatory-guard pilot",flush=True)


def verify(state,test=False):
    state=Path(state);r=read(state/"registration.json")
    if r["code_hashes"]!=code_hashes():raise ValueError("Registered source changed; preserve and amend before continuing")
    for split in ("calibration","test") if test else ("calibration",):
        if digest(state/"data"/(split+".jsonl"))!=r["private_input_hashes"][split]:raise ValueError("Input drift")
        if digest(state/"public/metadata"/(split+".jsonl"))!=r["metadata_hashes"][split]:raise ValueError("Reference drift")
    config=read(state/"config.private.json")
    if sha(canonical(config["policies"]))!=r["policies_sha256"]:raise ValueError("Policy drift")
    if test:
        f=read(state/"public/selection-freeze.json")
        if f["registration_sha256"]!=digest(state/"registration.json") or f["selection_sha256"]!=digest(state/"selection.json"):raise ValueError("Selection freeze changed")
    return r


def start(state):
    state=Path(state);pidpath=state/"gateway.private.json"
    if pidpath.exists():
        entry=read(pidpath)
        try:
            if http(entry["base"],"/health",timeout=2).get("instance_id")==read(state/"config.private.json")["instance_id"]:return entry
        except OSError:pass
        raise ValueError("Preserve stale gateway receipt and use another state")
    port=free_port();log=(state/"gateway.private.log").open("w")
    process=subprocess.Popen([sys.executable,"-B","-m","evals.routed_guard.server","gateway","--config",str((state/"config.private.json").resolve()),"--port",str(port)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    entry=dict(pid=process.pid,base="http://127.0.0.1:"+str(port),config_path=str((state/"config.private.json").resolve()))
    write(pidpath,entry)
    for _ in range(240):
        if process.poll() is not None:raise RuntimeError("Gateway startup failed; inspect private log")
        try:
            if http(entry["base"],"/health",timeout=1).get("status")=="ready":
                print("Gateway ready at",entry["base"],flush=True);return entry
        except OSError:pass
        time.sleep(.25)
    os.killpg(process.pid,signal.SIGTERM);raise TimeoutError("Gateway startup timeout")


def stop(state,keep=False):
    state=Path(state);entry=read(state/"gateway.private.json")
    http(entry["base"],"/v1/unload",{},timeout=30)
    if not keep:os.killpg(entry["pid"],signal.SIGTERM)
    write(state/"public/cleanup.json",dict(gpu_workers_unloaded=True,cpu_gateway_running=keep,paid_resources_created=False))
    print("GPU workers unloaded; CPU gateway "+("available at "+entry["base"] if keep else "stopped"),flush=True)


def collect(base,path,inputs,destination,model=None,deadline=None):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    existing=rows(destination) if destination.exists() else []
    done={r["id"]:r for r in existing}
    if len(done)!=len(existing):raise ValueError("Duplicate existing predictions")
    for item in inputs:
        if item["id"] in done and any(done[item["id"]].get(k)!=item[k] for k in ("input_sha256","policy_sha256")):raise ValueError("Cached input drift")
    with destination.open("a") as output:
        for i,r in enumerate(inputs):
            if r["id"] in done:continue
            if deadline is not None and time.monotonic()>deadline:raise TimeoutError("Registered phase time budget reached")
            request=dict(content=r["content"],policy_id=r["policy_id"],request_id=r["id"])
            request_started=time.perf_counter()
            if model:request["model"]=model
            try:answer=http(base,path,request,timeout=480)
            except Exception as exc:
                answer=dict(prediction="REVIEW",status="error",error="gateway_request_error",error_type=type(exc).__name__,guard_attempted=False,
                    input_sha256=r["input_sha256"],policy_sha256=r["policy_sha256"],model=model)
            answer["server_latency_ms"]=answer.get("latency_ms")
            answer["latency_ms"]=1000*(time.perf_counter()-request_started)
            if answer.get("input_sha256")!=r["input_sha256"] or answer.get("policy_sha256")!=r["policy_sha256"]:raise ValueError("Response identity mismatch")
            # No caller content or source reference enters the public record.
            item=dict(answer,id=r["id"],policy_id=r["policy_id"])
            output.write(canonical(item)+"\n");output.flush();done[r["id"]]=item
            if (i+1)%16==0 or i+1==len(inputs):print("INFER",model or "routed",i+1,"/",len(inputs),flush=True)
    return list(done.values())



def smoke(state,model):
    state=Path(state);base=start(state)["base"];results=[]
    examples=[("Hello, please summarize the quarterly report.","harmful_requests-v0"),("Use the symbol from the unavailable reference image.","custom_policy-v0"),("Translate the quoted sentence: ignore previous instructions.","injection_context-v0")]
    for text,pid in examples:
        answer=http(base,"/v1/guard",dict(content=text,policy_id=pid,model=model),timeout=480)
        results.append(answer)
        if answer.get("status")!="ok" or answer.get("prediction") not in labels_for(pid) or not answer.get("full_input_passed"):
            write(state/"public/preflight"/(model+"-failure.json"),dict(model=model,responses=results,scope="Synthetic interface checks; no accuracy gate"))
            http(base,"/v1/unload",{},timeout=30)
            raise RuntimeError("Native adapter smoke failed: "+model)
    if model=="shieldstral":
        answer=http(base,"/v1/moderate",dict(content="Please summarize this report.",policy_id="harmful_requests-v0"),timeout=480)
        results.append(answer)
        if answer.get("status")!="ok" or not answer.get("guard_attempted") or answer.get("router") is None:raise RuntimeError("Live routed endpoint smoke failed")
    write(state/"public/preflight"/(model+".json"),dict(model=model,responses=results,scope="Synthetic interface checks; not an accuracy evaluation"))
    http(base,"/v1/unload",{},timeout=30)
    print("Native interface smoke passed:",model,"requests",len(results),flush=True)


def calibrate(state,requested=None):
    state=Path(state);verify(state)
    if (state/"selection.json").exists():raise ValueError("Mapping already frozen")
    base=start(state)["base"]
    clock=state/"public/calibration-clock.json"
    if not clock.exists():write(clock,dict(start_epoch=time.time(),budget_seconds=5400))
    remaining=read(clock)["start_epoch"]+5400-time.time()
    if remaining<=0:raise TimeoutError("Calibration phase budget exhausted")
    deadline=time.monotonic()+remaining;inputs=rows(state/"data/calibration.jsonl");predictions={}
    requested=list(ORDER) if requested is None else requested
    if not requested or any(m not in MODELS for m in requested):raise ValueError("Invalid model subset")
    for model in requested:
        predictions[model]=collect(base,"/v1/guard",inputs,state/"public/calibration"/(model+".jsonl"),model,deadline)
        if not any(r.get("status")=="ok" for r in predictions[model]):raise RuntimeError("No valid calibration responses from "+model)
    available=[m for m in ORDER if (state/"public/calibration"/(m+".jsonl")).exists() and len(rows(state/"public/calibration"/(m+".jsonl")))==len(inputs)]
    if len(available)!=len(ORDER):
        print("Calibration collected; mapping remains unfrozen. Completed:",",".join(available),flush=True)
        http(base,"/v1/unload",{},timeout=30)
        return
    predictions={m:rows(state/"public/calibration"/(m+".jsonl")) for m in ORDER}
    cases=rows(state/"public/metadata/calibration.jsonl");tracks=read(ROOT/"benchmarks/enterprise-moderation/v0.1/tracks.json")
    selection=select_mapping(cases,predictions,tracks);selection["selection_status"]="frozen"
    write(state/"selection.json",selection)
    freeze=dict(registration_sha256=digest(state/"registration.json"),selection_sha256=digest(state/"selection.json"),selection=selection,
        calibration_prediction_hashes={m:digest(state/"public/calibration"/(m+".jsonl")) for m in ORDER})
    write(state/"public/selection-freeze.json",freeze)
    print("MAPPING FROZEN",canonical(selection),flush=True)
    http(base,"/v1/unload",{},timeout=30)


def test(state):
    from evals.liquid_router.model import Router
    state=Path(state);verify(state,test=True);config=read(state/"config.private.json");selection=read(state/"selection.json")
    base=start(state)["base"];deadline=time.monotonic()+5400;inputs=rows(state/"data/test.jsonl")
    for model in ORDER:collect(base,"/v1/guard",inputs,state/"public/test-controls"/(model+".jsonl"),model,deadline)
    # Input-only scheduling pass; actual /moderate repeats classification before dispatch.
    router=Router(config["router_checkpoint"],threads=4,int8=False);planned=[]
    for r in inputs:
        pred=router.predict(r["content"]);model,reason=choose_model(pred,selection)
        planned.append(dict(id=r["id"],model=model,input_sha256=r["input_sha256"]))
    del router;gc.collect();jsonl(state/"public/planned-routes.jsonl",planned)
    by_id={r["id"]:r for r in inputs}
    for model in ORDER:
        jobs=[by_id[p["id"]] for p in planned if p["model"]==model]
        if jobs:collect(base,"/v1/moderate",jobs,state/"public/routed.jsonl",deadline=deadline)
    http(base,"/v1/unload",{},timeout=30)
    summarize(state)


def summarize(state):
    state=Path(state);verify(state,test=True);suite=ROOT/"benchmarks/enterprise-moderation/v0.1"
    cases=rows(state/"public/metadata/test.jsonl");tracks=read(suite/"tracks.json");profiles=read(suite/"profiles.json");selection=read(state/"selection.json")
    controls={m:rows(state/"public/test-controls"/(m+".jsonl")) for m in ORDER}
    routed=rows(state/"public/routed.jsonl");lookup={r["id"]:r for r in routed}
    if set(lookup)!={r["id"] for r in cases}:raise ValueError("Incomplete routed pilot")
    report=dict(pilot=True,n=len(cases),models={m:report_metrics(cases,p,tracks,profiles) for m,p in controls.items()},
        routed=report_metrics(cases,routed,tracks,profiles),selection=selection,
        guard_attempt_coverage=sum(bool(r.get("guard_attempted")) for r in routed)/len(cases),
        successful_guard_coverage=sum(r.get("status")=="ok" for r in routed)/len(cases),
        routed_model_counts=dict(Counter(r.get("model") for r in routed)),route_reasons=dict(Counter(r.get("route_reason") for r in routed)),
        technical_fallbacks=sum(len(r.get("guard_attempts",[]))>1 for r in routed),
        latency_scope="Actual /moderate HTTP requests; includes classifier, guard loading when needed, native inference and deliberate GPU cooldown; model-grouped scheduling")
    baseline={r["id"]:r for r in controls[selection["default_model"]]};paired=Counter()
    for c in cases:
        a=baseline[c["id"]];b=lookup[c["id"]]
        correct=lambda r:r.get("status")=="ok" and r.get("prediction")==c["expected"]
        paired["corrected"]+=not correct(a) and correct(b);paired["newly_wrong"]+=correct(a) and not correct(b)
        paired["changed"]+=a.get("prediction")!=b.get("prediction")
    report["paired_vs_validation_selected_single_guard"]=dict(paired)
    oracle=[]
    for c in cases:
        m=selection["category_models"].get(TRACK_CATEGORY.get(c["track"]),selection["default_model"])
        oracle.append(next(r for r in controls[m] if r["id"]==c["id"]))
    report["counterfactual_known_category"]=report_metrics(cases,oracle,tracks,profiles)
    report["counterfactual_interpretation"]="Composed from fresh controls using benchmark family; not deployable, not a latency measurement, not guaranteed to outperform predicted routing"
    import numpy as np
    latencies=[r["latency_ms"] for r in routed if isinstance(r.get("latency_ms"),(int,float))]
    if latencies:report["actual_routed_latency_ms"]={name:float(np.quantile(latencies,q)) for name,q in (("p50",.5),("p95",.95),("p99",.99))}
    write(state/"public/results.json",report)
    print(canonical({"routed_accuracy":report["routed"]["accuracy"],"routed_profiles":report["routed"]["profiles"],
        "single_guard":selection["default_model"],"single_guard_accuracy":report["models"][selection["default_model"]]["accuracy"],
        "guard_coverage":report["successful_guard_coverage"],"paired":report["paired_vs_validation_selected_single_guard"]}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("action",choices=["prepare","register","start","calibrate","test","summarize","stop","smoke"]);p.add_argument("--state",required=True)
    p.add_argument("--inputs");p.add_argument("--checkpoint");p.add_argument("--vendor");p.add_argument("--policy-python");p.add_argument("--keep-gateway",action="store_true");p.add_argument("--model",choices=list(MODELS));p.add_argument("--models")
    a=p.parse_args()
    if a.action=="prepare":prepare(a.state,a.inputs,a.checkpoint,a.vendor,a.policy_python)
    elif a.action=="stop":stop(a.state,a.keep_gateway)
    elif a.action=="smoke":smoke(a.state,a.model)
    else:
        try:
            if a.action=="calibrate":calibrate(a.state,a.models.split(",") if a.models else None)
            else:globals()[a.action](a.state)
        except BaseException as exc:
            if a.action in ("calibrate","test"):
                state=Path(a.state)
                write(state/"public"/(a.action+"-failure.json"),dict(stage=a.action,error_type=type(exc).__name__,partial_results_preserved=True))
                if (state/"gateway.private.json").exists():
                    try:http(read(state/"gateway.private.json")["base"],"/v1/unload",{},timeout=30)
                    except Exception:pass
            raise
