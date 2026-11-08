"""Run fixed LoRA interventions, freeze validation selection, then score held-out data."""
import argparse
import gc
import json
import math
from pathlib import Path
from random import Random
import time

from evals.liquid_router.common import digest, read, rows, sha, write
from .data import BUNDLE, EVAL_LIMIT, TRAIN_LIMIT, checked_preparation, enterprise, keyed
from .runtime import ANSWERS, MODEL, REVISION, SEED, Budget, answer_scores, encode, load_base, logits, new_adapter, tokenizer

SYSTEMS = ("base", "mixed", "contrast")


def file_hashes(path):
    return {p.name: digest(p) for p in sorted(path.iterdir()) if p.is_file()}


def input_policy(row, policies):
    return row["policy"] if "policy" in row else policies[row["track"] + "-v0"]


def encoded(tok, cohort, policies, verify=False):
    output = []
    for row in cohort:
        policy = input_policy(row, policies)
        ids = encode(tok, row, policy, verify=verify)
        output.append((row, ids))
    return output


def fit(base, tok, data, output, budget):
    import torch

    torch.manual_seed(SEED)
    adapter = new_adapter(base)
    adapter.train()
    trainable = [p for p in adapter.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.0)
    ordered = sorted(data, key=lambda item: (len(item[1]), keyed(item[0])))
    if max(len(ids) for _, ids in ordered) > TRAIN_LIMIT:
        raise ValueError("A registered FIT example exceeded the training cap")
    chunks = [ordered[i:i + 8] for i in range(0, len(ordered), 8)]
    Random(SEED).shuffle(chunks)
    total = 0
    losses = []
    output.mkdir(exist_ok=False)
    with (output / "steps.jsonl").open("x") as log:
        for step, chunk in enumerate(chunks, 1):
            loss_total = 0.0
            for index in range(0, len(chunk), 2):
                batch = chunk[index:index + 2]
                budget.before()
                start = time.monotonic()
                targets = torch.tensor([ANSWERS[row["expected"]] for row, _ in batch], device="cuda")
                values = logits(base, tok, [ids for _, ids in batch])
                loss = torch.nn.functional.cross_entropy(values, targets, reduction="sum")
                if not math.isfinite(loss.item()):
                    raise ValueError("Nonfinite training loss")
                (loss / len(chunk)).backward()
                loss_total += loss.item()
                total += len(batch)
                if index + 2 >= len(chunk):
                    norm = torch.nn.utils.clip_grad_norm_(trainable, 1.0, error_if_nonfinite=True)
                    optimizer.step()
                    optimizer.zero_grad(set_to_none=True)
                torch.cuda.synchronize()
                budget.rest(start)
            losses.append(loss_total / len(chunk))
            log.write(json.dumps({"step": step, "examples_seen": total, "loss": losses[-1],
                                  "gradient_norm": float(norm)}) + "\n")
            log.flush()
            if step == 1 or step % 8 == 0 or step == len(chunks):
                print(f"{output.name}: step {step}/{len(chunks)}, {total} examples, loss {losses[-1]:.4f}", flush=True)
    adapter.save_pretrained(output / "adapter")
    write(output / "training.json", {
        "steps": len(chunks), "examples": total, "mean_step_loss": sum(losses) / len(losses),
        "trainable_parameters": sum(p.numel() for p in trainable),
        "checkpoint_files": file_hashes(output / "adapter"),
    })
    base.gradient_checkpointing_disable()
    base = adapter.unload()
    del optimizer, trainable, adapter
    gc.collect()
    torch.cuda.empty_cache()
    return base


def batches(data):
    current = []
    for row, ids in sorted(data, key=lambda item: (len(item[1]), item[0]["id"])):
        if current and (len(current) == 12 or (len(current) + 1) * len(ids) > 6144):
            yield current
            current = []
        current.append((row, ids))
    if current:
        yield current


def score(base, tok, data, policies, output, budget):
    import torch

    base.eval()
    with output.open("x") as log, torch.inference_mode():
        for batch in batches(data):
            usable = [(row, ids) for row, ids in batch if len(ids) <= EVAL_LIMIT]
            scores = {}
            if usable:
                budget.before()
                start = time.monotonic()
                values = logits(base, tok, [ids for _, ids in usable])
                pair = values[:, [ANSWERS["BLOCK"], ANSWERS["ALLOW"]]]
                probabilities = answer_scores(values).tolist()
                alternatives = pair.tolist()
                scores = {row["id"]: (p, a) for (row, _), p, a in zip(usable, probabilities, alternatives, strict=True)}
                torch.cuda.synchronize()
                budget.rest(start)
            for row, ids in batch:
                probability, alternatives = scores.get(row["id"], (None, None))
                policy = input_policy(row, policies)
                policy_hash = sha(json.dumps(policy, sort_keys=True, ensure_ascii=False, separators=(",", ":")))
                if row.get("policy_sha256", policy_hash) != policy_hash:
                    raise ValueError("Policy hash mismatch")
                result = dict(id=row["id"], track=row["track"], input_sha256=row["input_sha256"],
                              policy_sha256=policy_hash, audit_group=row["audit_group"],
                              expected=row["expected"], tokens=len(ids))
                if probability is None:
                    result.update(error="input_exceeds_context_limit", score=None)
                elif math.isfinite(probability) and all(map(math.isfinite, alternatives)):
                    result.update(score=probability, yes_no_logits=alternatives)
                else:
                    result.update(error="nonfinite_native_score", score=None)
                log.write(json.dumps(result, allow_nan=False) + "\n")
            log.flush()
    print(f"Scored {len(data)} cases in {output.name}", flush=True)


def assess(base, tok, data, policies, output, state, budget):
    import torch
    from peft import PeftModel

    for system in SYSTEMS:
        if system == "base":
            score(base, tok, data, policies, output / f"{system}.jsonl", budget)
            continue
        checkpoint = state / "development" / system / "adapter"
        adapter = PeftModel.from_pretrained(base, checkpoint).eval()
        score(base, tok, data, policies, output / f"{system}.jsonl", budget)
        base = adapter.unload()
        del adapter
        gc.collect()
        torch.cuda.empty_cache()
    return base


def develop(state):
    import torch
    from .analysis import select

    prepared, registration = checked_preparation(state)
    policies = read(BUNDLE / "policies.json")
    tok = tokenizer()
    output = state / "development"
    output.mkdir(exist_ok=False)
    validation = encoded(tok, rows(prepared / "validation.jsonl"), policies)
    with (output / "device.jsonl").open("x") as device:
        budget = Budget(device)
        budget.before(force=True)
        base = load_base()
        for system in SYSTEMS[1:]:
            data = encoded(tok, rows(prepared / f"{system}.jsonl"), policies, verify=True)
            base = fit(base, tok, data, output / system, budget)
        assess(base, tok, validation, policies, output, state, budget)
        freeze = {
            "model": MODEL, "revision": REVISION, "registration_sha256": digest(prepared / "registration.json"),
            "cutoffs": {s: select(rows(output / f"{s}.jsonl")) for s in SYSTEMS},
            "validation_hashes": {s: digest(output / f"{s}.jsonl") for s in SYSTEMS},
            "checkpoints": {s: file_hashes(output / s / "adapter") for s in SYSTEMS[1:]},
        }
        budget.before(force=True)
        write(output / "runtime.json", {**budget.summary(),
                                        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024 ** 2})
        write(state / "freeze.json", freeze)


def evaluate(source, state):
    import torch

    prepared, registration = checked_preparation(state, final=True)
    frozen = read(state / "freeze.json")
    if frozen["registration_sha256"] != digest(prepared / "registration.json"):
        raise ValueError("Freeze refers to different prepared data")
    for system in SYSTEMS:
        if digest(state / "development" / f"{system}.jsonl") != frozen["validation_hashes"][system]:
            raise ValueError("Validation evidence changed after freeze")
    for system in SYSTEMS[1:]:
        if file_hashes(state / "development" / system / "adapter") != frozen["checkpoints"][system]:
            raise ValueError("Checkpoint changed after freeze")
    policies = read(BUNDLE / "policies.json")
    tok = tokenizer()
    output = state / "evaluation"
    output.mkdir(exist_ok=False)
    data = encoded(tok, [*enterprise(source, registration), *rows(prepared / "fresh.jsonl")], policies)
    with (output / "device.jsonl").open("x") as device:
        budget = Budget(device)
        budget.before(force=True)
        assess(load_base(), tok, data, policies, output, state, budget)
        budget.before(force=True)
        write(output / "runtime.json", {**budget.summary(),
                                        "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024 ** 2})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("develop", "evaluate"))
    parser.add_argument("state", type=Path)
    parser.add_argument("--source", type=Path, default=Path("work/liquid-router-v0"))
    args = parser.parse_args()
    if args.stage == "develop":
        develop(args.state)
    else:
        evaluate(args.source, args.state)
