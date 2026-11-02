# Six-model injection benchmark evidence

This archive preserves the registered protocol, pinned sources, duplicate audit,
policy provenance and model outputs. The validation selections were committed
before final test inference. No cutoff search, calibration, ensemble or weight
fine-tuning is part of this study.

- [Readable study](../../docs/prompt-injection/README.md)
- [Registered design](../../docs/prompt-injection/PLAN.md)
- [Execution amendments](../../docs/prompt-injection/NOTES.md)
- [Validation selections](freeze.json)
- [Policy hashes](policy-freeze.json)
- [Validation measurements](validation-summary.json)

Raw prompts, requests, quoted fitting examples and model reasoning are not
redistributed. Download the pinned sources and run the preparation commands in
[the reproduction guide](../../docs/prompt-injection/RUNNING.md). To restore the
exact example-bearing policies privately:

```sh
python scripts/restore_prompt_injection_policies.py \
  --archive published_runs/2026-11-02-prompt-injection \
  --data-state /private/path/prepared-state \
  --out /private/path/restored-policies
```

All six reconstructed candidate files must match the frozen hashes. Compressed
predictions and metadata contain IDs, labels, hashes and decisions, without raw
source text. Model/runtime and split identities are retained.

Status: validation complete and policies frozen; final test inference has not started.
