"""Turn logged agent trajectories into guard examples (curriculum stage 5).

Each gated step becomes one example: requester, request, prior events (earlier calls and
their outputs, outputs marked untrusted), pending call and dry run. Labels come from R-ref
under each training policy, using facts derived from live state at that step.
Failed calls are excluded: R-ref would label them ALLOW, which would teach leniency toward
broken but dangerous attempts. Reads are downsampled to keep risky steps visible.

python -m evals.action_guard.trajectories build --runs work/action-guard/trajectories --out work/action-guard/data/trajectories.jsonl
"""
import argparse
import hashlib
import json
from pathlib import Path

from . import tasks
from .dataset import TRAIN_POLICIES, dry_run, target
from .rules import reference
from .run_agents import USERS

READ_KEEP = 25  # percent of read steps kept, chosen by hash
HISTORY_STEPS = 6
OUTPUT_CHARS = 600
MAX_INPUT_CHARS = 9000  # ~3k tokens; with the policy this stays under the 4,096-token training cap. Never truncate the pending call.


def render_step(task, history, call, record):
    name, role = USERS[task["requester"]]
    email = name.split()[0].lower() + "@northwind.test"
    parts = [f"## Requester\n{name} ({role}, {task['requester']}, {email})", f"## Request\n{task['prompt']}"]
    if history:
        lines = []
        for h in history[-HISTORY_STEPS:]:
            out = h["error"] and f"error: {h['error']}" or json.dumps(h["result"], sort_keys=True)
            lines.append(f"- call: {json.dumps(h['call'], sort_keys=True)}\n  tool output (untrusted data): {out[:OUTPUT_CHARS]}")
        parts.append("## Prior events\n" + "\n".join(lines))
    parts.append("## Pending tool call\n" + json.dumps(call, sort_keys=True))
    parts.append("## Dry run\n" + dry_run(record))
    return "\n\n".join(parts)


def _keep(key):
    return int(hashlib.sha256(f"traj-read|{key}".encode()).hexdigest(), 16) % 100 < READ_KEEP


def build(runs_dir, out):
    n_in = kept = excluded = 0
    with open(out, "w") as fh:
        for f in sorted(Path(runs_dir).glob("*.server.jsonl")):
            events = [json.loads(l) for l in f.read_text().splitlines()]
            start = events[0]
            task = tasks.TASKS[start["task"]]
            history, queue = [], []
            for e in events:
                if e["event"] == "gate":
                    queue.append(e)
                elif e["event"] == "call":
                    # Sibling calls in one model turn are all gated, then executed: match by content (A5).
                    k = json.dumps(e["call"], sort_keys=True)
                    pending = next((g for g in queue if json.dumps(g["call"], sort_keys=True) == k), None)
                    if pending is None:
                        continue
                    queue.remove(pending)
                    n_in += 1
                    rec, key = pending["record"], f"{f.name}|{pending['step']}"
                    if not rec["error"] and (rec["verb"] != "read" or _keep(key)):
                        text = render_step(task, history, pending["call"], rec)
                        if len(text) > MAX_INPUT_CHARS:
                            excluded += 1
                            history.append({"call": e["call"], "result": e["result"], "error": e["error"]})
                            continue
                        for p in TRAIN_POLICIES:
                            d, rules = reference(p, rec, pending["facts"])
                            fh.write(json.dumps({"id": f"traj:{key}@{p}", "scenario_id": f"traj:{key}", "family": "traj:" + start["task"].rsplit("-", 1)[0],
                                                 "group": "trajectory", "dialect": "agent", "object": None, "policy": p, "split": "train",
                                                 "input": text, "record": rec, "facts": pending["facts"], "target": target(d, rules, rec)},
                                                sort_keys=True) + "\n")
                        kept += 1
                    history.append({"call": e["call"], "result": e["result"], "error": e["error"]})
    return {"steps_seen": n_in, "steps_kept": kept, "excluded_over_length": excluded, "examples": kept * len(TRAIN_POLICIES)}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--runs", required=True)
    b.add_argument("--out", required=True)
    a = ap.parse_args()
    print(json.dumps(build(a.runs, a.out)))


if __name__ == "__main__":
    main()
