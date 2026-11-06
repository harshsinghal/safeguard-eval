"""Unchanged operational repeat with durable device samples; primary result stays frozen."""
import argparse
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import subprocess
import sys
import threading
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.routed_guard.common import MODELS,ORDER,read,rows,write,digest,canonical,report_metrics,ROOT
from evals.routed_guard.experiment import verify,collect
from evals.routed_guard.server import http

class DeviceSampler:
    def __init__(self,path,base):self.path=Path(path);self.base=base;self.finish=threading.Event();self.samples=[];self.errors=[]
    def run(self):
        start=time.monotonic()
        with self.path.open("a") as output:
            while not self.finish.is_set():
                try:
                    line=subprocess.check_output(["nvidia-smi","--query-gpu=temperature.gpu,power.draw,utilization.gpu,memory.used","--format=csv,noheader,nounits"],text=True,timeout=5).splitlines()[0]
                    temp,power,util,memory=map(float,line.split(","))
                    try:model=http(self.base,"/health",timeout=1).get("active_model")
                    except Exception:model=None
                    r=dict(seconds=time.monotonic()-start,temperature_c=temp,power_w=power,utilization_pct=util,memory_mib=memory,active_model=model)
                    self.samples.append(r);output.write(canonical(r)+"\n");output.flush()
                except Exception as exc:self.errors.append(type(exc).__name__)
                self.finish.wait(.5)
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True);self.thread=threading.Thread(target=self.run,daemon=True);self.thread.start();return self
    def __exit__(self,*exc):self.finish.set();self.thread.join(timeout=8)


def run(state):
    state=Path(state);verify(state,test=True);public=state/"public";base=read(state/"gateway.private.json")["base"]
    if (public/"operational-repeat-registration.json").exists():raise ValueError("Preserve existing repeat")
    primary_hash=digest(public/"routed.jsonl")
    registration=dict(purpose="Retain device telemetry across native worker shutdown; no selection, policy, dtype or checkpoint change",
        created_utc=datetime.now(timezone.utc).isoformat(),selection_sha256=digest(state/"selection.json"),
        primary_routed_sha256=primary_hash,input_sha256=digest(state/"data/test.jsonl"),
        instrument_sha256=digest(__file__),limit_seconds=1800,
        limitation="Primary worker context telemetry was not flushed on graceful signal termination; primary full-run device peaks are unavailable",
        prior_live_device_observations=dict(temperature_c=51.,power_w=158.24,scope="Individual live observations, not full-run peaks"))
    write(public/"operational-repeat-registration.json",registration)
    inputs={r["id"]:r for r in rows(state/"data/test.jsonl")};planned=rows(public/"planned-routes.jsonl")
    destination=public/"operational-repeat-routed.jsonl";deadline=time.monotonic()+1800
    with DeviceSampler(public/"operational-repeat-device.jsonl",base) as sampler:
        try:
            for model in ORDER:
                jobs=[inputs[r["id"]] for r in planned if r["model"]==model]
                if jobs:collect(base,"/v1/moderate",jobs,destination,deadline=deadline)
        finally:http(base,"/v1/unload",{},timeout=30)
    if digest(public/"routed.jsonl")!=primary_hash:raise ValueError("Primary result changed")
    output=rows(destination);primary={r["id"]:r for r in rows(public/"routed.jsonl")};cases=rows(public/"metadata/test.jsonl")
    suite=ROOT/"benchmarks/enterprise-moderation/v0.1"
    result=dict(n=len(output),metrics=report_metrics(cases,output,read(suite/"tracks.json"),read(suite/"profiles.json")),
        primary_decision_changes=sum(r["prediction"]!=primary[r["id"]]["prediction"] for r in output),
        successful_guard_coverage=sum(r.get("status")=="ok" for r in output)/len(cases),
        device_samples=len(sampler.samples),sampler_errors=sampler.errors,
        sampled_peak_temperature_c=max(r["temperature_c"] for r in sampler.samples),
        sampled_peak_power_w=max(r["power_w"] for r in sampler.samples),
        sampled_peak_device_memory_mib=max(r["memory_mib"] for r in sampler.samples),
        hardware_power_or_clock_settings_changed=False,paid_compute_usd=0,
        interpretation="Supplementary operational repeat only; primary pilot unchanged. Device samples include other applications and may miss instantaneous peaks.")
    write(public/"operational-repeat-results.json",result)
    print(canonical({k:v for k,v in result.items() if k!="metrics"}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--state",required=True);run(p.parse_args().state)
