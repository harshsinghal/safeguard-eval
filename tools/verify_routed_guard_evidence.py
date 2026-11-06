"""Recompute routing selection and whole-system scores without inference or prompts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals.routed_guard.common import ROOT,MODELS,choose_model,read,select_mapping,report_metrics
from tools.verify_liquid_router_evidence import safe_relative


def load(archive,relative,lines=False):
    p=Path(archive)/relative
    if not p.exists():p=p.with_name(p.name+".gz")
    data=gzip.decompress(p.read_bytes()) if p.suffix==".gz" else p.read_bytes()
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()] if lines else json.loads(data)


def verify_route(row,selection):
    if row.get("status")!="ok":
        if row.get("prediction")=="ALLOW":raise ValueError("Failed guard cannot ALLOW")
        return False
    if not row.get("guard_attempted") or not row.get("full_input_passed"):raise ValueError("Successful response omitted guard")
    router=None if row.get("router_error") else row.get("router")
    expected,_=choose_model(router,selection)
    if row.get("requested_model")!=expected:raise ValueError("Routing map mismatch")
    attempts=row.get("guard_attempts",[])
    if not attempts or attempts[0]!=expected or row.get("model")!=attempts[-1]:raise ValueError("Guard attempt trace mismatch")
    if row.get("model_revision")!=MODELS[row["model"]]["revision"]:raise ValueError("Guard revision mismatch")
    if row.get("selection_status")!="frozen":raise ValueError("Pilot used an unfrozen mapping")
    return True


def verify(archive):
    archive=Path(archive).resolve()
    for line in (archive/"SHA256SUMS").read_text().splitlines():
        expected,rel=line.split("  ",1);p=archive/safe_relative(rel)
        if not p.resolve().is_relative_to(archive):raise ValueError("Archive path escaped")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError("Checksum mismatch: "+rel)
    suite=ROOT/"benchmarks/enterprise-moderation/v0.1";tracks=read(suite/"tracks.json");profiles=read(suite/"profiles.json")
    cal=load(archive,"metadata/calibration.jsonl",True);cases=load(archive,"metadata/test.jsonl",True)
    calibration={m:load(archive,"calibration/"+m+".jsonl",True) for m in MODELS}
    selected=select_mapping(cal,calibration,tracks)
    freeze=load(archive,"selection-freeze.json");selection=freeze["selection"]
    if any(selection[k]!=v for k,v in selected.items()):raise ValueError("Calibration selection differs")
    controls={m:load(archive,"test-controls/"+m+".jsonl",True) for m in MODELS}
    routed=load(archive,"routed.jsonl",True);result=load(archive,"results.json")
    for model,predictions in controls.items():
        if report_metrics(cases,predictions,tracks,profiles)!=result["models"][model]:raise ValueError("Control score mismatch: "+model)
    if report_metrics(cases,routed,tracks,profiles)!=result["routed"]:raise ValueError("Routed score mismatch")
    traces=sum(verify_route(row,selection) for row in routed)
    if traces!=sum(row.get("status")=="ok" for row in routed):raise ValueError("Missing successful guard trace")
    repeat=load(archive,"operational-repeat-results.json")
    repeated=load(archive,"operational-repeat-routed.jsonl",True)
    if report_metrics(cases,repeated,tracks,profiles)!=repeat["metrics"]:raise ValueError("Operational repeat score mismatch")
    primary={r["id"]:r for r in routed}
    changed=sum(r["prediction"]!=primary[r["id"]]["prediction"] for r in repeated)
    if changed!=repeat["primary_decision_changes"]:raise ValueError("Operational repeat agreement mismatch")
    samples=load(archive,"operational-repeat-device.jsonl",True)
    if len(samples)!=repeat["device_samples"] or max(r["power_w"] for r in samples)!=repeat["sampled_peak_power_w"] or max(r["temperature_c"] for r in samples)!=repeat["sampled_peak_temperature_c"]:raise ValueError("Operational repeat telemetry mismatch")
    print(json.dumps(dict(verified=True,pilot_cases=len(cases),calibration_cases=len(cal),
        routed_accuracy=result["routed"]["accuracy"],profiles=result["routed"]["profiles"],
        valid_live_guard_traces=traces,default_guard=selection["default_model"]),indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive",default="published_runs/2026-11-05-routed-guard-pilot")
    verify(p.parse_args().archive)
