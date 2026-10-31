# Liquid classifier run log

2026-10-31T22:49:01.035911+00:00: Protocol commit164afe0; five unit tests passed.
Pinned provider model/code and tutorial inspected. GPU.ai L40S requested at$.80/hour,
two-hour auto-termination; initial upload has no test inputs or test labels.
Only training/validation lengths were examined before choosing the context setting.
Provider balance$10.43; cumulative project budget remaining$3.19998212744.

Smoke test passed: training estimate 1,457 seconds plus validation/setup/I/O;
peak allocated memory 29.83 GB. Frozen fitting/validation extraction completed.
The storage-retention clarification was recorded before inspecting validation scores.
All six fine-tuning runs remain in the search.

Independent input restoration passed for all 4,096 fitting and 1,536 validation
rows from the pinned publisher parquet. Both complete input-file hashes match
the registered experiment, not merely row counts.

2026-10-31T23:03:12.110205+00:00: All six training runs completed;
18 fine-tuned checkpoints and five frozen LR candidates entered validation selection.
All four fine-tuning profiles selected learning rate5e-5, epoch3, across all three
seeds. Primary cutoff.68; balanced cutoff.86. Frozen LR selected C.01, cutoff.58.
Pretest freeze commit: 317e7925506e4f9be5a8e798f198f438296bc8ab. No test text uploaded before this point.

After the pretest freeze, all 1,699 test inputs were also reconstructed from the
pinned source parquet in an independent check; the exact test input-file hash
matched the registration. No setting changed following this check.

Test scoring finished with no configuration changes. Accuracy-selected primary
fine-tune: 86.4038% accuracy, 85.4859% balanced accuracy, FP60/FN171. Frozen
control: 82.2248% accuracy, FP68/FN234. Three-seed fine-tune mean86.2272%.
Default-.5 primary fine-tune: 86.9335%, FP70/FN152; this remains a supplementary
control and does not replace the preregistered validation-selected headline.
Public metric verifier reproduced all16 selected rows and both paired profiles.
All selected checkpoint validation replays had maximum absolute difference0.
All retained examples scored; no split required truncation.

2026-10-31T23:11:16.480281+00:00: All three selected FP32
checkpoints collected and hash-verified as lossless gzip archives. GPU terminated;
temporary local/provider SSH keys removed; provider instance list empty.
Billed1,299 GPU-seconds, $0.29; cumulative accounted spend$17.09001787256/$20.
No API inference or RunPod resource used.
