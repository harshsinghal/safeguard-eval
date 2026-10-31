# Fine-tuning a Liquid encoder on WildGuard

[Readable findings](READOUT.md) · [Full results](RESULTS.md) · [CSV](results.csv) ·
[Registered plan](PLAN.md) · [Execution notes](AMENDMENTS.md) · [Reproduction](RUNNING.md)

This study compares a trained linear classifier on frozen Liquid encoder features
with end-to-end supervised fine-tuning of that same encoder and a linear head.
The input is a submitted prompt. No policy text is supplied. Fitting uses 4,096
WildGuardTrain prompts, validation 1,536, and test all 1,699 labeled prompts in
the official WildGuardTest population. That public test has been used previously.

The bundle includes every validation candidate, all four operating profiles,
all selected fine-tuning seeds, predictions, metrics, paired intervals, split
identities, source snapshots, parameter hashes, runtime and billing evidence.
The small frozen classifier weights are included. Text, embeddings, credentials
and large fine-tuned checkpoints are not. See checkpoint-inventory.json for
the local weight retention record.

Verify a copy without GPUs or API calls:

```sh
PYTHONPATH=source python3 source/tools/verify_liquid_finetune.py --state .
```

Verification writes a new verification.json; use a copy to preserve the original
checksums. Every package file except checksums.json itself is listed there.
