"""One-step adapter, answer-slot parity and offline reload check."""
import argparse
from pathlib import Path
import time

from evals.liquid_router.common import ROOT, read, rows, write
from .runtime import ANSWERS, MODEL, REVISION, Budget, answer_scores, encode, load_base, logits, new_adapter, tokenizer


def smoke(source, output):
    import peft
    import torch
    import transformers

    output.mkdir(parents=True, exist_ok=False)
    policies = read(ROOT / "benchmarks/enterprise-moderation/v0.1/policies.json")
    tok = tokenizer()
    cases = rows(source / "data/fit.jsonl")
    chosen = None
    for row in cases:
        policy = policies[row["track"] + "-v0"]
        ids = encode(tok, row, policy)
        if 1700 <= len(ids) <= 2048 and (chosen is None or len(ids) > len(chosen[1])):
            chosen = row, ids, policy
    row, ids, policy = chosen
    for label in ANSWERS:
        encode(tok, dict(row, expected=label), policy, verify=True)

    with (output / "device.jsonl").open("x") as device:
        budget = Budget(device)
        budget.before(force=True)
        base = load_base()
        base.eval()
        with torch.inference_mode():
            direct = logits(base, tok, [ids])
            full = base(input_ids=torch.tensor([ids], device="cuda"), use_cache=False,
                        logits_to_keep=1).logits[:, -1].float()
            difference = float((answer_scores(direct) - answer_scores(full)).abs().item())
        if difference > 0.002:
            raise ValueError(f"Next-token score parity failed: {difference}")
        adapter = new_adapter(base)
        adapter.train()
        trainable = [p for p in adapter.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(trainable, lr=1e-4, weight_decay=0.0)
        budget.before(force=True)
        start = time.monotonic()
        target = torch.tensor([ANSWERS[row["expected"]]], device="cuda")
        loss = torch.nn.functional.cross_entropy(logits(base, tok, [ids]), target)
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(trainable, 1.0, error_if_nonfinite=True)
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        budget.rest(start)
        del optimizer, trainable
        base.gradient_checkpointing_disable()
        adapter.eval()
        with torch.inference_mode():
            trained = logits(base, tok, [ids])
        if torch.equal(trained, direct):
            raise ValueError("Optimizer step left every answer-position logit unchanged")
        checkpoint = output / "adapter"
        adapter.save_pretrained(checkpoint)
        base = adapter.unload()
        del adapter
        adapter = peft.PeftModel.from_pretrained(base, checkpoint).eval()
        with torch.inference_mode():
            reloaded = logits(base, tok, [ids])
        torch.testing.assert_close(trained, reloaded, rtol=0, atol=0)
        budget.before(force=True)
        write(output / "result.json", {
            "model": MODEL, "revision": REVISION, "tokens": len(ids), "track": row["track"],
            "input_sha256": row["input_sha256"], "answer_ids": ANSWERS,
            "scored_target_positions_per_row": 1, "native_score_difference": difference,
            "loss": float(loss.detach()), "gradient_norm": float(norm),
            "reloaded_logits_identical": True, "peak_allocated_mib": torch.cuda.max_memory_allocated() / 1024 ** 2,
            "torch": torch.__version__, "transformers": transformers.__version__,
            "peft": peft.__version__, **budget.summary(),
        })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    smoke(args.source, args.output)
