"""Verify prompt-free Shieldstral training and held-out evidence offline."""
import argparse
import gzip
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals.liquid_router.common import digest, read, rows
from evals.shieldstral_policy.analysis import same_cases, select, summarize
from evals.shieldstral_policy.data import BINARY_EXCLUDED, BUNDLE, EVAL_LIMIT, code_hashes
from evals.shieldstral_policy.study import SYSTEMS


def equal(actual, expected, description):
    if actual != expected:
        raise ValueError(f"{description} mismatch")


def metadata_signature(records):
    keys = ("id", "input_sha256", "policy_sha256", "audit_group", "track", "expected")
    return sorted(tuple(r[k] for k in keys) for r in records)


def validate_logits(records):
    for row in records:
        if row["score"] is None:
            if row.get("error") != "input_exceeds_context_limit" or row["tokens"] <= EVAL_LIMIT:
                raise ValueError("Unexplained missing score")
            continue
        yes, no = row["yes_no_logits"]
        high = max(yes, no)
        weight = math.exp(yes - high)
        if not math.isclose(row["score"], weight / (weight + math.exp(no - high)), abs_tol=1e-7):
            raise ValueError("Stored yes/no score disagrees with logits")


def verify(bundle, scratch):
    for line in (bundle / "SHA256SUMS").read_text().splitlines():
        checksum, relative = line.split("  ", 1)
        path = bundle / relative
        if not path.resolve().is_relative_to(bundle.resolve()):
            raise ValueError("Checksum file escapes bundle")
        equal(digest(path), checksum, relative)
    prepared = read(bundle / "registration.json")
    frozen = read(bundle / "freeze.json")
    equal(prepared["code"], code_hashes(), "Registered source code")
    equal(digest(BUNDLE / "manifest.json"), prepared["enterprise_manifest_sha256"], "Fixed benchmark manifest")
    equal(digest(bundle / "registration.json"), frozen["registration_sha256"], "Freeze registration hash")

    for name in ("mixed", "contrast", "validation", "fresh"):
        metadata = gzip.decompress((bundle / "metadata" / f"{name}.jsonl.gz").read_bytes())
        equal(sha256(metadata).hexdigest(), prepared["files"][f"{name}-metadata.jsonl"], f"{name} metadata")
    mixed, contrast = [rows(bundle / "metadata" / f"{name}.jsonl.gz") for name in ("mixed", "contrast")]
    equal(len(mixed), len(contrast), "Training example count")
    equal(len([r for r in contrast if r["track"] == "policy_contrast"]), 72, "Contrast example count")
    validation = rows(bundle / "metadata/validation.jsonl.gz")
    fresh = rows(bundle / "metadata/fresh.jsonl.gz")
    final = [r for r in rows(BUNDLE / "evaluation.jsonl") if r["track"] not in BINARY_EXCLUDED]
    signatures = lambda rr: sorted((r["id"], r["input_sha256"], r["policy_sha256"], r["track"], r["expected"]) for r in rr)
    (scratch / "evaluation").mkdir()
    (scratch / "freeze.json").write_bytes((bundle / "freeze.json").read_bytes())
    results = []
    for system in SYSTEMS:
        path = bundle / "development" / f"{system}.jsonl.gz"
        equal(sha256(gzip.decompress(path.read_bytes())).hexdigest(), frozen["validation_hashes"][system], f"{system} validation hash")
        rr = rows(path)
        equal(metadata_signature(rr), metadata_signature(validation), "Validation cohort")
        validate_logits(rr)
        equal(select(rr), normalize_cutoff(frozen["cutoffs"][system]), f"{system} cutoffs")

        path = bundle / "evaluation" / f"{system}.jsonl.gz"
        rr = rows(path)
        validate_logits(rr)
        equal(signatures([r for r in rr if r["track"] != "policy_contrast"]), signatures(final), "Fixed evaluation cohort")
        equal(metadata_signature([r for r in rr if r["track"] == "policy_contrast"]),
              metadata_signature(fresh), "Policy-contrast transfer cohort")
        (scratch / "evaluation" / f"{system}.jsonl").write_bytes(gzip.decompress(path.read_bytes()))
        results.append(rr)
        if system == "base":
            continue
        training = read(bundle / "development" / f"{system}-training.json")
        equal(training["checkpoint_files"], frozen["checkpoints"][system], "Checkpoint hash record")
        steps = rows(bundle / "development" / f"{system}-steps.jsonl.gz")
        equal(len(steps), math.ceil(len(mixed) / 8), "Training step count")
        equal(steps[-1]["examples_seen"], len(mixed), "Fit examples seen")
    for result in results[1:]:
        same_cases(results[0], result)
    equal(json.loads(json.dumps(summarize(scratch))), read(bundle / "results.json"), "Complete scorecard")
    return {"systems": len(results), "validation_cases": len(validation),
            "binary_benchmark_cases": len(final), "fresh_fixture_cases": len(fresh),
            "examples_per_adapter": len(mixed), "passed": True}


def normalize_cutoff(cutoff):
    key = "validation_low_false_block_operating_point"
    return dict(cutoff, **{key: tuple(cutoff[key]) if cutoff[key] is not None else None})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    with TemporaryDirectory() as tmp:
        print(json.dumps(verify(args.bundle, Path(tmp)), indent=2))
