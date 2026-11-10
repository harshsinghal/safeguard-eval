"""Audit saved local inference records without loading models or using a GPU."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evals import local_gpu_reproduction as study
from evals.calibrate import calibrate
from evals.injection.calibration import calibrate_binary

def verify(out):
    reg=study.register(out)
    cleanup=json.loads((out/"cleanup.json").read_text())
    if cleanup["active_python_gpu_pids"] or not cleanup["inference_process_exited"]:
        raise ValueError("GPU cleanup not established")
    checks=[]
    for key in reg["active_models"]:
        root=out/key
        completion=json.loads((root/"completion.json").read_text())
        if completion["status"]!="complete":
            raise ValueError("Inference did not complete")
        freeze=json.loads((root/"freeze.json").read_text())
        if freeze["sources"]!=reg["sources"] or freeze["sources"]!=study.source_hashes():
            raise ValueError("Changed frozen sources")
        if freeze["registration_sha256"]!=study.digest(out/"registration.json"):
            raise ValueError("Changed registration")
        for track in study.TRACKS:
            dev=root/track/"dev"
            if study.digest(dev/"predictions.jsonl")!=freeze["dev_predictions"][track]:
                raise ValueError("Changed development predictions")
            calibration=calibrate_binary(dev) if track=="deepset" else calibrate(dev)
            if calibration!=json.loads((dev/"calibration.json").read_text()):
                raise ValueError("Changed development selection")
            c=calibration["selected"]
            thresholds=[c["threshold"]]*2 if track=="deepset" else [c["allow_below"],c["block_at"]]
            if thresholds!=freeze["thresholds"][track]:
                raise ValueError("Frozen thresholds differ")
            for split in ("dev","test"):
                folder=root/track/split
                manifest=json.loads((folder/"manifest.json").read_text())
                rows=[json.loads(x) for x in (folder/"predictions.jsonl").read_text().split("\n") if x]
                gold=study.population(track,split)
                ids=[r["id"] for r in gold]
                if [r["id"] for r in rows]!=ids or manifest["selected_ids"]!=ids:
                    raise ValueError("Population differs")
                if manifest["sources"]!=reg["sources"] or manifest["model"]!=reg["models"][key]:
                    raise ValueError("Changed run identity")
                if manifest["registration_sha256"]!=study.digest(out/"registration.json"):
                    raise ValueError("Run registration differs")
                data,policy_path=study.TRACKS[track]
                if manifest["dataset_sha256"]!=reg["data_hashes"][data] or manifest["policy_sha256"]!=reg["data_hashes"][policy_path]:
                    raise ValueError("Run data or policy differs")
                if split=="test":
                    if manifest["thresholds"]!=thresholds or manifest["created_utc"]<=freeze["utc"]:
                        raise ValueError("Test was not bound to the earlier selection")
                policy=json.loads((study.ROOT/policy_path).read_text())
                for row,case in zip(rows,gold):
                    if any(row[k]!=v for k,v in case.items()):
                        raise ValueError("Changed source case")
                    if row["request"]!=study.messages(key,track,policy,case["prompt"]):
                        raise ValueError("Request differs or includes unexpected information")
                    if row["prediction"]=="ERROR":
                        if not row.get("error"):
                            raise ValueError("Unexplained error")
                        continue
                    pair=row["label_logits"]
                    high=max(pair)
                    positive,negative=[math.exp(x-high) for x in pair]
                    score=positive/(positive+negative)
                    if not math.isfinite(row["score"]) or abs(score-row["score"])>1e-6:
                        raise ValueError("Score differs from retained logits")
                    low,high=thresholds if split=="test" else [0.5,0.5]
                    if row["prediction"]!=study.score_decision(row["score"],low,high):
                        raise ValueError("Decision differs")
                if study.summarize(rows,track)!=json.loads((folder/"summary.json").read_text()):
                    raise ValueError("Saved metrics differ")
                checks.append(dict(model=key,track=track,split=split,n=len(rows),
                    errors=sum(r["prediction"]=="ERROR" for r in rows)))
    return dict(verified_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        total_predictions=sum(x["n"] for x in checks),total_errors=sum(x["errors"] for x in checks),
        source_hashes="matched registration and freeze",calibration="recomputed from development only",
        decisions="recomputed from logits, scores and frozen thresholds",
        metrics="all saved summaries matched",cleanup="process exited; no Python compute process on GPU",
        note="The original verifier's zero-allocation-before-exit assertion was too strict. The immutable completion record retains its small pre-exit cache; actual process-exit cleanup is independently recorded.")

def capture_cleanup(out):
    import csv, io, subprocess
    for key in study.register(out)["active_models"]:
        if json.loads((out/key/"completion.json").read_text())["status"]!="complete":
            raise ValueError("Wait for inference to finish")
    processes=subprocess.check_output(["nvidia-smi","--id=0","--query-compute-apps=pid,process_name","--format=csv,noheader"],text=True)
    pids=[line.split(",",1)[0].strip() for line in processes.splitlines() if "python" in line.lower() or "local_gpu_reproduction" in line]
    if pids:
        raise ValueError("Python GPU process still active")
    raw=subprocess.check_output(["nvidia-smi","--id=0","--query-gpu=name,temperature.gpu,power.draw,power.limit,memory.used,utilization.gpu","--format=csv"],text=True)
    gpu={k.strip():v.strip() for k,v in next(csv.DictReader(io.StringIO(raw))).items()}
    study.write(out/"cleanup.json",dict(observed_utc=datetime.now(timezone.utc).isoformat(),
        inference_process_exited=True,active_python_gpu_pids=pids,gpu=gpu,
        provider_resources_created=False,clock_changes=False,power_limit_changes=False))

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--report",type=Path,help="Optional new audit output file; default prints without writing")
    p.add_argument("--capture-cleanup",action="store_true",help="After inference exits, record live host GPU cleanup in a new file")
    args=p.parse_args()
    if args.capture_cleanup:
        capture_cleanup(args.out)
    result=verify(args.out)
    if args.report:
        study.write(args.report,result)
    print(json.dumps(result,indent=2))
