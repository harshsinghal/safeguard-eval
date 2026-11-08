"""Recompute the selection and final readout from prompt-free run evidence."""
import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals.liquid_router.common import ROOT, digest, read, rows, sha
from evals.shieldstral_hillclimb.analysis import SYSTEMS, choose, report
from evals.shieldstral_hillclimb.data import hashes


def equal(actual, expected, label):
    if actual != expected:
        raise ValueError(f"{label} mismatch")


def signature(records):
    fields = ("id", "input_sha256", "policy_sha256", "audit_group", "track", "expected")
    return sorted(tuple(r[k] for k in fields) for r in records)


def verify(bundle):
    for line in (bundle / "SHA256SUMS").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        path = bundle / relative
        if not path.resolve().is_relative_to(bundle.resolve()):
            raise ValueError("Checksum path escapes bundle")
        equal(digest(path), checksum, relative)
    reg = read(bundle / "registration.json")
    freeze = read(bundle / "freeze.json")
    equal(reg["code"], hashes(), "Registered code")
    equal(digest(bundle / "registration.json"), freeze["registration_sha256"], "Frozen registration")
    metadata = {}
    for cohort in ("larger", "targeted", "calibration", "selection", "fresh"):
        p = bundle / "metadata" / f"{cohort}.jsonl.gz"
        equal(sha(gzip.decompress(p.read_bytes())), reg["files"][f"{cohort}-metadata.jsonl"], cohort)
        metadata[cohort] = rows(p)
    for candidate in SYSTEMS[2:]:
        equal(len(metadata[candidate]), 864, "Fit count")
        equal(len(rows(bundle / candidate / "steps.jsonl.gz")), 108, "Step count")
        equal(read(bundle / candidate / "training.json")["checkpoint_files"],
              freeze["checkpoint_hashes"][candidate], "Checkpoint hash")
        equal(Counter(r["expected"] for r in metadata[candidate]), {"ALLOW": 432, "BLOCK": 432}, "Training labels")
    for name, checksum in freeze["selection_hashes"].items():
        equal(sha(gzip.decompress((bundle / "select" / f"{name}.gz").read_bytes())), checksum, name)
    splits = {stage: {s: rows(bundle / "select" / f"{s}-{stage}.jsonl.gz") for s in SYSTEMS}
              for stage in ("calibration", "selection")}
    for stage, scores in splits.items():
        for s, rr in scores.items():
            equal(signature(rr), signature(metadata[stage]), f"{stage} {s} identities")
    chosen = choose(**splits)
    equal(json.loads(json.dumps(chosen)), {k: freeze[k] for k in chosen}, "Selection")

    final = {stage: {s: rows(bundle / "evaluate" / f"{s}-{stage}.jsonl.gz") for s in SYSTEMS}
             for stage in ("regression", "transfer")}
    for s, rr in final["transfer"].items():
        equal(signature(rr), signature(metadata["fresh"]), f"Transfer {s} identities")
    for s, old in (("base", "base"), ("incumbent", "mixed")):
        archived = ROOT / "published_runs/2026-11-07-shieldstral-policy/evaluation" / f"{old}.jsonl.gz"
        equal(final["regression"][s], rows(archived), f"Reused {s} predictions")
    result = report(**final, fresh_metadata=metadata["fresh"], frozen=freeze)
    equal(json.loads(json.dumps(result)), read(bundle / "results.json"), "Final results")
    return {"systems": len(SYSTEMS), "examples_per_fit": len(metadata["larger"]),
            "calibration": len(metadata["calibration"]), "selection": len(metadata["selection"]),
            "reused_cases": len(final["regression"]["base"]), "transfer_cases": len(metadata["fresh"]),
            "nomination": result["nomination"], "promoted": result["promoted"], "passed": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("bundle", type=Path)
    print(json.dumps(verify(p.parse_args().bundle), indent=2))
