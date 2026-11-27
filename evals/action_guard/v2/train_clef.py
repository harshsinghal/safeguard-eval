"""LoRA fine-tuning of Clef-Flash 9B on v2 requests, with a cartography log (design §5 step 14, P9).

Clef ships no training script, so this loop is written against its pinned module: cross-entropy on each
field's option logits from the joint schema head. LoRA on the language model's attention projections;
the head is trained in full. After each epoch every train item's probability of its gold decision is
logged (Swayamdipta et al. 2020): mean confidence and variability across epochs locate easy, ambiguous
and hard-to-learn items, and hard-to-learn items are the first place to look for label errors.

python -m evals.action_guard.v2.train_clef DATA OUTDIR [--epochs 3] [--lr 1e-4]
"""
import argparse
import json
import random
import time
from pathlib import Path

from .contract import FIELDS
from .guards import encode, forward, load_clef, load_jsonl

WEIGHTS = {"decision": 1.0, "missing": 0.5, "source": 0.25, "question": 0.5}
TARGETS = r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|in_proj_qkv|in_proj_z|out_proj)$"   # full and linear attention layers


def gold_index(enc_q, label):
    return list(enc_q.option_ids).index(label)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--accum", type=int, default=8)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from peft import LoraConfig, get_peft_model
    from safetensors.torch import save_file

    torch.manual_seed(a.seed)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    mod, model, processor = load_clef(trainable=True)
    for p in model.parameters():
        p.requires_grad_(False)
    lm = model.language_model
    lm.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    lm.enable_input_require_grads()
    model.language_model = get_peft_model(lm, LoraConfig(r=a.rank, lora_alpha=2 * a.rank, lora_dropout=0.05,
                                                         target_modules=TARGETS, task_type="CAUSAL_LM"))
    n_lora = sum(p.numel() for p in model.language_model.parameters() if p.requires_grad)
    if n_lora == 0:
        raise SystemExit("LoRA matched no modules")
    model.head.float()
    for p in model.head.parameters():
        p.requires_grad_(True)
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)

    rows = load_jsonl(a.data)
    train = [r for r in rows if r["split"] == "train"]
    val = [r for r in rows if r["split"] == "val"]
    enc = {r["id"]: encode(mod, processor, r) for r in rows}
    total = a.epochs * len(train) // a.accum
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(1, total // 10)) * max(0.0, 1 - s / max(1, total)))
    log = (out / "train.log").open("a")
    reg = {"data": a.data, "n_train": len(train), "n_val": len(val), "epochs": a.epochs, "lr": a.lr, "accum": a.accum,
           "rank": a.rank, "seed": a.seed, "lora_params": n_lora, "weights": WEIGHTS, "targets": TARGETS}
    log.write(json.dumps({"start": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **reg}) + "\n")

    def run_eval(items):
        model.eval()
        res = {}
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            for r in items:
                e = enc[r["id"]]
                qs = forward(mod, model, processor, [e])[0]
                res[r["id"]] = {q.question_id: dict(zip(q.option_ids, z.float().softmax(-1).cpu().tolist())) for q, z in zip(e.questions, qs)}
        model.train()
        return res

    rng = random.Random(a.seed)
    step = 0
    model.train()
    for epoch in range(1, a.epochs + 1):
        order = train[:]
        rng.shuffle(order)
        t0, run_loss = time.time(), 0.0
        for i, r in enumerate(order):
            e = enc[r["id"]]
            with torch.autocast("cuda", dtype=torch.bfloat16):
                qs = forward(mod, model, processor, [e])[0]
            loss = 0.0
            for q, z in zip(e.questions, qs):
                y = torch.tensor([gold_index(q, r["label"][q.question_id])], device=z.device)
                loss = loss + WEIGHTS[q.question_id] * F.cross_entropy(z.float().view(1, -1), y)
            (loss / a.accum).backward()
            run_loss += float(loss)
            if (i + 1) % a.accum == 0 or i + 1 == len(order):
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
                step += 1
        tr = run_eval(train)
        va = run_eval(val)
        carto = {rid: p["decision"][next(r["label"]["decision"] for r in train if r["id"] == rid)] for rid, p in tr.items()}
        acc = lambda res, items: sum(max(res[r["id"]]["decision"], key=res[r["id"]]["decision"].get) == r["label"]["decision"] for r in items) / len(items)
        rec = {"epoch": epoch, "step": step, "loss": round(run_loss / len(order), 4), "train_acc": round(acc(tr, train), 4),
               "val_acc": round(acc(va, val), 4), "seconds": round(time.time() - t0, 1)}
        log.write(json.dumps(rec) + "\n")
        log.flush()
        print(rec, flush=True)
        with (out / "cartography.jsonl").open("a") as f:
            for rid, pg in carto.items():
                f.write(json.dumps({"epoch": epoch, "id": rid, "p_gold": round(pg, 4)}) + "\n")
        with (out / f"val-epoch{epoch}.jsonl").open("w") as f:
            for rid, p in va.items():
                f.write(json.dumps({"id": rid, "probabilities": p}) + "\n")
    model.language_model.save_pretrained(out / "adapter")
    save_file({k: v.contiguous() for k, v in model.head.state_dict().items()}, str(out / "adapter" / "head.safetensors"))
    (out / "registration.json").write_text(json.dumps(reg, indent=1))


if __name__ == "__main__":
    main()
