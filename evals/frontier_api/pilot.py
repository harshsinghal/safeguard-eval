"""Interleave the same fitting-only pilot across all registered API conditions."""
import argparse
import json
from pathlib import Path
from statistics import mean

from evals.frontier_api.run import now, run


def pilot(args):
    registry = json.loads(args.registry.read_text())
    args.out.mkdir(parents=True, exist_ok=False)
    records = []
    stopped = None
    arms = list(registry['arms'])
    for index in range(registry['pilot_n']):
        # Rotate first condition to avoid always penalizing the same endpoint at a cap.
        order = arms[index % len(arms):] + arms[:index % len(arms)]
        for arm in order:
            candidate = next(c for c in registry['candidates'] if c['arm'] == arm and
                             json.loads((args.registry.parent/c['path']).read_text())['id'] == 'wg-p0-taxonomy')
            out = args.out / (str(index).zfill(2) + '-' + arm)
            run_args = argparse.Namespace(registry=args.registry, data=args.data,
                policy=args.registry.parent/candidate['path'], out=out, arm=arm, stage='pilot',
                freeze=None, dry_run=False, ledger=args.ledger, key_file=args.key_file, pilot_index=index)
            result = run(run_args)
            predictions = [json.loads(s) for s in (out/'predictions.jsonl').read_text().splitlines()]
            records.extend(dict(row, arm=arm) for row in predictions)
            if not result['complete']:
                stopped = result['stop_reason']
                break
            print(json.dumps(dict(completed=len(records), planned=len(arms)*registry['pilot_n'])), flush=True)
        if stopped:
            break
    summary = dict(created_utc=now(), complete=stopped is None, stop_reason=stopped,
                   planned=len(arms)*registry['pilot_n'], attempted=len(records), conditions={})
    for arm in arms:
        rows = [r for r in records if r['arm'] == arm]
        if not rows:
            summary['conditions'][arm] = {'n': 0}
            continue
        usages = [r.get('usage', {}) for r in rows]
        summary['conditions'][arm] = dict(n=len(rows), valid=sum(r['prediction'] != 'ERROR' for r in rows),
            billed_usd=sum(float(u.get('cost', 0)) for u in usages),
            missing_cost=sum('cost' not in u for u in usages),
            mean_latency_seconds=mean(r['latency_seconds'] for r in rows),
            mean_input_tokens=mean(u.get('prompt_tokens', 0) for u in usages),
            mean_output_tokens=mean(u.get('completion_tokens', 0) for u in usages),
            reported_reasoning_tokens=sum((u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0) for u in usages))
    (args.out/'pilot-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry', type=Path, default=Path('evals/frontier_api/registry.json'))
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--ledger', type=Path, default=Path('work/frontier-api/spend.jsonl'))
    p.add_argument('--key-file', type=Path, default=Path.home()/'workspace/KEYS/OPENROUTER_API.txt')
    print(json.dumps(pilot(p.parse_args()), indent=2))
