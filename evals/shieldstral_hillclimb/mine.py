"""Score eligible FIT examples from the two target tasks with the incumbent."""
import argparse
from pathlib import Path

from peft import PeftModel
from evals.liquid_router.common import digest, read, rows, write
from evals.shieldstral_policy.data import BUNDLE, TRAIN_LIMIT, verify_partition
from evals.shieldstral_policy.runtime import Budget, load_base, tokenizer
from evals.shieldstral_policy.study import encoded, file_hashes, score

TARGETS = ("hate_speech", "agent_actions")


def main(source, prior, state):
    parts = {s: rows(source / "data" / f"{s}.jsonl") for s in ("fit", "validation")}
    verify_partition(source, parts)
    checkpoint = prior / "development/mixed/adapter"
    freeze = read(prior / "freeze.json")
    if file_hashes(checkpoint) != freeze["checkpoints"]["mixed"]:
        raise ValueError("Prior adapter hash mismatch")
    policies = read(BUNDLE / "policies.json")
    tok = tokenizer()
    candidates = [(r, ids) for r, ids in encoded(
        tok, [r for r in parts["fit"] if r["track"] in TARGETS], policies) if len(ids) <= TRAIN_LIMIT]
    output = state / "mining"
    output.mkdir(exist_ok=False)
    with (output / "device.jsonl").open("x") as device:
        budget = Budget(device)
        budget.before(force=True)
        base = load_base()
        adapter = PeftModel.from_pretrained(base, checkpoint).eval()
        score(adapter.get_base_model(), tok, candidates, policies, output / "fit.jsonl", budget)
        budget.before(force=True)
        write(output / "runtime.json", budget.summary())
    write(output / "manifest.json", {
        "fit_sha256": digest(source / "data/fit.jsonl"),
        "scores_sha256": digest(output / "fit.jsonl"),
        "prior_freeze_sha256": digest(prior / "freeze.json"),
        "prior_checkpoint": freeze["checkpoints"]["mixed"],
        "source_code_sha256": digest(Path(__file__)),
    })


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for argument in ("source", "prior", "state"):
        p.add_argument(argument, type=Path)
    main(**vars(p.parse_args()))
