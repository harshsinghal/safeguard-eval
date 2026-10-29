# Kev / Clef experiment log

2026-10-29: Plan and three policy variants registered before inference. Six CPU integrity tests pass. No weights will be trained. Initial budget remaining $7.07459444344. GPU.ai 48GB RTX6000 Ada offer $0.65/hour, six-hour automatic termination (maximum $3.90 rental); no disk charge in selected quote. Test data is withheld from the remote machine until validation selection is frozen.

Setup correction before any inference: added missing Pydantic 2.12.3 to Kev runtime; no protocol or policy change.

Active GPU: gpu-3f6d60a5 (GPU.ai), created 2026-10-29T19:43:26.979447Z, six-hour termination deadline approximately 2026-10-30T01:43:27Z. Instance and connection in instance.json; credentials in private local SSH files. Remote /root/decision-state; processes started by /root/development.sh. Kev development running, Clef follows. Test data not yet uploaded. Kev parity: six fit examples, maximum probability difference 0.003593742847442627, zero argmax changes. Published temperature retained: 2.406050072164233.

Implementation commit: 1c39a49. Kev fitting and validation complete. Kev validation balanced choices: brief policy, cutoff .56 (WildGuard); brief policy, cutoff .71 (HateXplain). Clef native-head parity also passed (six fitting rows, max probability difference .0010110735893249512, zero argmax flips), and Clef validation is running. advance.py is waiting in local exec session 18633; it will sync, freeze both selections, then upload test data and start test.sh automatically. No test inference has started at this note.

Both development stages complete. Validation selection frozen at 2026-10-29T20:34:34.413475+00:00. Test data uploaded only after this freeze; test inference started.

All 44,522 predictions verified against remote hashes. GPU terminated and provider usage reconciled; see billing.json and final-instance.json. Ephemeral SSH keys removed.
