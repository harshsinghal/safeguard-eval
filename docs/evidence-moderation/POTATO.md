# Potato annotation workspace

Potato 2.14.0 is installed in the isolated ignored `work/potato-env` environment.
The local projects contain the registered 100 development and 100 evaluation
prompts with their original text and IDs.

- [Development workspace](http://127.0.0.1:9001/?reviewer=harsh)
- [Reserved evaluation workspace](http://127.0.0.1:9002/?reviewer=harsh)

Choose an entity label, highlight its text, then use the relationship and event
panels to connect actions to their arguments. Existing draft links can be clicked
to locate their spans. Hover over entity labels to read their definitions. The
policy decision panel includes an expandable copy of the pilot policy. Next
saves the current work. Use draft until evidence and policy decisions have been
checked, then explicitly choose reviewed or needs_adjudication.

## Draft provenance

Stock `fastino/gliner2.5-multi-v1`, revision
`7b005274e82da37dcf1f5fd9d6a2ef413c6a004c`, generated 2,729 span suggestions across
the 100 development prompts. It used the expanded schema, threshold 0.5,
160-word windows with 32-word overlap, four CPU threads and the local GPU. All
predicted spans were checked against exact source offsets. Inference took 11.14
seconds after loading, with peak PyTorch allocation about 1,493 MiB. There were
zero paid API calls and no clock or power-setting changes. The inference worker
exited after completion.

These suggestions are unreviewed and have no measured accuracy on this schema.
Some long inputs have many noisy spans. The broad stock checkpoint was selected
because our earlier fine-tune covered only three narrow entity categories.
Original source safety labels are excluded from the UI and predictions.

The first development case uses the existing assistant-authored worked example
in place of its model span suggestions. It displays three spans, two directed
links and one transmission event. The original model output is preserved in
`work/potato-evidence-v1/span-drafts.jsonl`. Remaining development cases have span
suggestions only. Policy decisions are blank. Evaluation cases have no automatic
suggestions. The project contains zero independently reviewed gold annotations.

The visual panels support spans, relations and action events. Per-action scope,
polarity and credential form currently use the frame-details text field. Record
the action text and offsets there to disambiguate repeated actions. Potato's
native export is preserved; conversion into our stricter evidence JSON contract
will require validating these attributes and reconciling event/relationship
edits. The pilot JSON validator does not directly consume Potato's native export.

## Storage and operation

Both servers bind to `127.0.0.1`. Local reviewer names identify separate saved
annotation folders. The setup uses username-in-URL login for this local workspace.
Keep the services on loopback. The server processes are deliberately left running
for review and hold no inference model or GPU allocation.

Data and saved annotations live under these ignored paths.

```text
work/potato-evidence-v1/development/data.jsonl
work/potato-evidence-v1/development/annotations/<reviewer>/user_state.json
work/potato-evidence-v1/evaluation/data.jsonl
work/potato-evidence-v1/evaluation/annotations/<reviewer>/user_state.json
```

The `codex-persistence-check` reviewer is a technical save/reload check and must
be excluded from human annotation datasets. It contains a draft on the authored
example. Spans, links and events were verified through Potato's native API and
on disk. Both configurations pass strict validation. Browser inspection verified
the highlighted example and its link/event arcs. An ignored overlap configuration
key from the online guide was removed after validation; this Potato version
handles overlapping spans directly.

Stop the local servers with the following command.

```bash
systemctl --user stop potato-evidence-development potato-evidence-evaluation
```

The services are transient and do not start at boot. After a reboot or stop,
start either project from the repository root with the following command,
changing development to evaluation for the second project.

```bash
work/potato-env/bin/potato start work/potato-evidence-v1/development/config.yaml --host 127.0.0.1
```

The setup generator refuses to overwrite existing projects. Preparation and
source hashes are in `local_runs/potato-evidence-v1`. Draft-generation code is
`tools/draft_potato_spans.py`; project generation is `tools/setup_potato_evidence.py`.
The annotation UI follows Potato's documented span, relation and event support.
[Potato documentation](https://potatoannotator.readthedocs.io/en/latest/annotation-types/text/span_linking/)
