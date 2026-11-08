"""Run the second-round fit, selection and protected evaluation."""
import argparse
import gc
from pathlib import Path

import torch
from peft import PeftModel

from evals.liquid_router.common import digest, jsonl, read, rows, write
from evals.shieldstral_policy.data import BUNDLE, enterprise
from evals.shieldstral_policy.runtime import MODEL, REVISION, Budget, load_base, tokenizer
from evals.shieldstral_policy.study import encoded, file_hashes, fit, score
from .analysis import SYSTEMS, choose, report
from .data import check


def prior_scores(prior, registration, stage, name):
    freeze = read(prior / "freeze.json")
    if digest(prior / "freeze.json") != registration["prior_freeze_sha256"]:
        raise ValueError("Prior freeze changed")
    original = "mixed" if name == "incumbent" else name
    path = prior / stage / f"{original}.jsonl"
    if stage == "development" and digest(path) != freeze["validation_hashes"][original]:
        raise ValueError("Prior validation scores changed")
    if stage == "evaluation":
        import gzip
        from evals.liquid_router.common import ROOT

        artifact = ROOT / "published_runs/2026-11-07-shieldstral-policy/evaluation" / f"{original}.jsonl.gz"
        if gzip.decompress(artifact.read_bytes()) != path.read_bytes():
            raise ValueError("Prior reused-suite evidence changed")
    return rows(path)


def checkpoints(state, prior, registration):
    paths = {"incumbent": prior / "development/mixed/adapter",
             **{s: state / s / "adapter" for s in SYSTEMS[2:]}}
    mining = read(state / "mining/manifest.json")
    if (registration["mining_sha256"] != digest(state / "mining/manifest.json")
            or file_hashes(paths["incumbent"]) != mining["prior_checkpoint"]):
        raise ValueError("Incumbent checkpoint changed")
    for system in SYSTEMS[2:]:
        if file_hashes(paths[system]) != read(state / system / "training.json")["checkpoint_files"]:
            raise ValueError(f"{system} training checkpoint changed")
    return paths


def scoring(stage, base, tok, data, policies, output, system, paths, budget):
    adapter = None
    if system in paths:
        adapter = PeftModel.from_pretrained(base, paths[system]).eval()
    score(base, tok, data, policies, output / f"{system}-{stage}.jsonl", budget)
    if adapter is not None:
        base = adapter.unload()
        del adapter
        gc.collect()
        torch.cuda.empty_cache()
    return base


def runtimes(path, budget):
    budget.before(force=True)
    write(path, {**budget.summary(),
                 "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024 ** 2})


def run(stage, state, source, prior):
    prepared, registration = check(state, final=stage == "evaluate")
    policies = read(BUNDLE / "policies.json")
    tok = tokenizer()
    if stage in SYSTEMS[2:]:
        with (state / f"{stage}-device.jsonl").open("x") as device:
            budget = Budget(device)
            budget.before(force=True)
            fit(load_base(), tok, encoded(tok, rows(prepared / f"{stage}.jsonl"), policies, verify=True),
                state / stage, budget)
            runtimes(state / f"{stage}-runtime.json", budget)
        return
    paths = checkpoints(state, prior, registration)
    output = state / stage
    output.mkdir(exist_ok=False)
    if stage == "select":
        splits = {split: rows(prepared / f"{split}.jsonl") for split in ("calibration", "selection")}
        all_dev = [r for rr in splits.values() for r in rr]
        with (output / "device.jsonl").open("x") as device:
            budget = Budget(device)
            budget.before(force=True)
            base = load_base()
            for s in SYSTEMS[2:]:
                base = scoring("dev", base, tok, encoded(tok, all_dev, policies), policies, output, s, paths, budget)
            runtimes(output / "runtime.json", budget)
        scores = {s: prior_scores(prior, registration, "development", s) for s in SYSTEMS[:2]}
        scores.update({s: rows(output / f"{s}-dev.jsonl") for s in SYSTEMS[2:]})
        partition = {}
        for split, expected in splits.items():
            keys = {r["id"] for r in expected}
            partition[split] = {s: [r for r in rr if r["id"] in keys] for s, rr in scores.items()}
            for s in SYSTEMS:
                if {r["id"] for r in partition[split][s]} != keys:
                    raise ValueError("Missing selection or calibration cases")
                jsonl(output / f"{s}-{split}.jsonl", partition[split][s])
        frozen = choose(**partition)
        frozen.update(model=MODEL, revision=REVISION, registration_sha256=digest(prepared / "registration.json"),
                      checkpoint_hashes={s: file_hashes(p) for s, p in paths.items()},
                      selection_hashes={p.name: digest(p) for p in sorted(output.glob("*.jsonl"))})
        write(state / "freeze.json", frozen)
        return

    frozen = read(state / "freeze.json")
    if (frozen["registration_sha256"] != digest(prepared / "registration.json")
            or frozen["checkpoint_hashes"] != {s: file_hashes(p) for s, p in paths.items()}
            or any(digest(state / "select" / name) != h for name, h in frozen["selection_hashes"].items())):
        raise ValueError("Frozen selection inputs changed")
    if digest(prior / "prepared/fresh.jsonl") != read(prior / "prepared/registration.json")["files"]["fresh.jsonl"]:
        raise ValueError("Prior policy fixtures changed")
    regression = encoded(tok, [*enterprise(source, registration), *rows(prior / "prepared/fresh.jsonl")], policies)
    transfer = encoded(tok, rows(prepared / "fresh.jsonl"), policies)
    with (output / "device.jsonl").open("x") as device:
        budget = Budget(device)
        budget.before(force=True)
        base = load_base()
        for s in SYSTEMS:
            base = scoring("transfer", base, tok, transfer, policies, output, s, paths, budget)
            if s in SYSTEMS[2:]:
                base = scoring("regression", base, tok, regression, policies, output, s, paths, budget)
            else:
                jsonl(output / f"{s}-regression.jsonl", prior_scores(prior, registration, "evaluation", s))
        runtimes(output / "runtime.json", budget)
    datasets = {stage: {s: rows(output / f"{s}-{stage}.jsonl") for s in SYSTEMS}
                for stage in ("regression", "transfer")}
    write(state / "results.json", report(**datasets, fresh_metadata=rows(prepared / "fresh-metadata.jsonl"), frozen=frozen))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage", choices=(*SYSTEMS[2:], "select", "evaluate"))
    p.add_argument("state", type=Path)
    p.add_argument("--source", type=Path, default=Path("work/liquid-router-v0"))
    p.add_argument("--prior", type=Path, default=Path("work/shieldstral-policy-v1"))
    run(**vars(p.parse_args()))
