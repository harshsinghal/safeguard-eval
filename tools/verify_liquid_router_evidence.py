"""Verify and reproduce the public classifier evidence without prompts or models."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

def safe_relative(value):
    p=Path(value)
    if p.is_absolute() or not p.parts or ".." in p.parts:raise ValueError("Unsafe artifact path")
    return p

def restore(archive,out):
    archive=Path(archive).resolve();out=Path(out)
    if out.exists():raise ValueError("Choose a new output directory")
    for line in (archive/"SHA256SUMS").read_text().splitlines():
        expected,rel=line.split("  ",1);p=archive/safe_relative(rel)
        if not p.resolve().is_relative_to(archive):raise ValueError("Artifact escaped archive")
        if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError("Archive checksum mismatch: "+rel)
    entries=json.loads((archive/"artifact-index.json").read_text())
    out.mkdir(parents=True)
    for entry in entries:
        p=archive/safe_relative(entry["archive_path"])
        payload=p.read_bytes()
        if hashlib.sha256(payload).hexdigest()!=entry["sha256"]:raise ValueError("Payload checksum mismatch")
        data=gzip.decompress(payload) if entry["compressed"] else payload
        if hashlib.sha256(data).hexdigest()!=entry["uncompressed_sha256"]:raise ValueError("Uncompressed checksum mismatch")
        target=out/"public"/safe_relative(entry["original_public_path"]);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    comparison=out/"public/comparison.json";before=json.loads(comparison.read_text())
    from tools.report_liquid_router import summarize
    summarize(out)
    if json.loads(comparison.read_text())!=before:raise ValueError("Reproduced report differs")
    print("Verified all archive hashes and reproduced CPU precision comparisons from metadata and predictions")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--archive",default="published_runs/2026-11-05-liquid-router");p.add_argument("--out",required=True)
    a=p.parse_args();restore(a.archive,a.out)
