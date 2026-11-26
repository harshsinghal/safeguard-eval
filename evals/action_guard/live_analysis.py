"""Live-run readout tables: per-arm summary, per-model breakdown, and paired deltas against the no-guard arm.

Pairs are (task, model, repeat). Bootstrap CIs resample pairs (2,000 draws, seed 0).

python -m evals.action_guard.live_analysis work/action-guard/live > docs/action-guard/scores/live.txt
"""
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from .live_report import score_run

ARMS = ["none", "rbase", "jev", "shieldstral", "ft-ordinal", "ft-staged"]


def load(run_dir):
    runs = {}
    for f in sorted(Path(run_dir).glob("*.server.jsonl")):
        task, model, arm, _, rep = f.name.removesuffix(".server.jsonl").split("__")
        r = score_run(f)
        r["model"], r["arm"], r["repeat"] = model, arm, rep
        r["compute_s"] = [json.loads(l).get("guard_compute_seconds") for l in f.read_text().splitlines()
                          if '"event": "gate"' in l]
        r["compute_s"] = [s for s in r["compute_s"] if s is not None]
        runs[(arm, task, model, rep)] = r
    return runs


def ok(r):
    return r["success"] and r["harmful"] == 0


def boot(diffs, n=2000):
    rng = random.Random(0)
    m = [statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(n)]
    m.sort()
    return m[int(0.025 * n)], m[int(0.975 * n)]


def main(run_dir):
    runs = load(run_dir)
    arms = [a for a in ARMS if any(k[0] == a for k in runs)]
    print("arm          runs  benign  risky_safe  harmful runs_w_harm  review/run  needless  blocked_legit  compute_med  compute_p95")
    for a in arms:
        rs = [r for k, r in runs.items() if k[0] == a]
        L = [r for r in rs if r["legitimate"]]
        R = [r for r in rs if not r["legitimate"]]
        c = sorted(s for r in rs for s in r["compute_s"])
        print(f"{a:12s} {len(rs):4d}  {100*sum(r['success'] for r in L)/len(L):5.1f}   {100*sum(r['success'] for r in R)/len(R):5.1f}"
              f"      {sum(r['harmful'] for r in rs):4d}  {sum(r['harmful']>0 for r in rs):4d}"
              f"        {sum(r['review'] for r in rs)/len(rs):5.2f}     {sum(r['needless_stops'] for r in rs):4d}"
              f"      {sum(r['blocked_legit_calls'] for r in rs):4d}"
              f"         {c[len(c)//2] if c else 0:6.3f}       {c[int(.95*(len(c)-1))] if c else 0:6.3f}")

    print("\nper model: benign success / risky safe")
    models = sorted({k[2] for k in runs})
    print("arm          " + "  ".join(f"{m[:26]:>26s}" for m in models))
    for a in arms:
        cells = []
        for m in models:
            rs = [r for k, r in runs.items() if k[0] == a and k[2] == m]
            L = [r for r in rs if r["legitimate"]]
            R = [r for r in rs if not r["legitimate"]]
            cells.append(f"{100*sum(r['success'] for r in L)/len(L):5.1f} / {100*sum(r['success'] for r in R)/len(R):5.1f}" if L and R else "-")
        print(f"{a:12s} " + "  ".join(f"{c:>26s}" for c in cells))

    print("\npaired vs none (task x model x repeat), mean difference in percentage points, 95% bootstrap CI")
    base = {k[1:]: r for k, r in runs.items() if k[0] == "none"}
    for a in arms:
        if a == "none":
            continue
        for label, sel in (("benign success", True), ("risky safe", False)):
            d = [100 * (int(runs[(a, *p)]["success"]) - int(b["success"]))
                 for p, b in base.items() if b["legitimate"] == sel and (a, *p) in runs]
            lo, hi = boot(d)
            print(f"{a:12s} {label:15s} n={len(d):3d}  {statistics.fmean(d):+6.1f}  [{lo:+6.1f}, {hi:+6.1f}]")

    print("\nbenign failures by template (arm: key=count)")
    for a in arms:
        f = defaultdict(int)
        for k, r in runs.items():
            if k[0] == a and r["legitimate"] and not r["success"]:
                f[r["key"]] += 1
        print(f"{a:12s} " + ", ".join(f"{k}={v}" for k, v in sorted(f.items(), key=lambda x: -x[1])))

    print("\nharm by template (arm: key=harmful calls)")
    for a in arms:
        f = defaultdict(int)
        for k, r in runs.items():
            if k[0] == a and r["harmful"]:
                f[r["key"]] += r["harmful"]
        print(f"{a:12s} " + (", ".join(f"{k}={v}" for k, v in sorted(f.items(), key=lambda x: -x[1])) or "none"))


if __name__ == "__main__":
    main(sys.argv[1])
