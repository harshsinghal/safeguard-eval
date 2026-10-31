# Execution and artifact notes

The scientific search, populations, loss, seeds and selection objectives remain
as registered. The fitting-only smoke test estimated about 1,457 seconds for
training microbatches, excluding validation, setup and checkpoint I/O. Peak
allocated memory on the longest training case was 29.83 GB on a 48 GB L40S.

## Local checkpoint storage

Before any validation scores or test results were inspected, the local disk
check showed about 11 GiB available. Each full-precision fine-tuned checkpoint
is about 1.4 GB. The registered plan's local-weight retention is clarified as
follows: retain the primary seed's accuracy- and balanced-selected checkpoints
in full precision, deduplicating if both profiles select the same file. Retain
additional selected weights when space permits. All selected checkpoints are
reloaded and their validation predictions verified on the GPU before test
inference. Every candidate's checkpoint hash and validation predictions, and
every selected seed's test predictions, are retained regardless of which large
weight files are copied locally. Record the exact retained-weight inventory.

This is a storage change, not a change to training, model selection, test
coverage or seed reporting. The other large weight files are removed when the
temporary GPU instance is terminated. They can be recreated by rerunning the
registered training procedure, subject to the recorded reproducibility limits.

Final retention outcome: all four profiles selected the same epoch/rate, so
there were only three distinct selected checkpoints. All three were retained
locally as lossless gzip archives; their decompressed hashes exactly matched
the original FP32 weight files. No selected weights were discarded. The other
15, unselected checkpoint files were removed with the GPU; all their hashes
and validation scores remain in the record.
