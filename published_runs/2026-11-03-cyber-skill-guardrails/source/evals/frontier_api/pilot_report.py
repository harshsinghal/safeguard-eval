"""Reproduce the fitting-only API pilot; no held-out leaderboard claims."""
import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean, median

from evals.frontier_api.run import identity
from evals.wildguard.metrics import metrics


def summarize(registry_path, runs, estimate_path):
    registry = json.loads(Path(registry_path).read_text())
    estimate = json.loads(Path(estimate_path).read_text())
    chosen = {}
    attempts = []
    for p in sorted(Path(runs).glob('*/manifest.json')):
        manifest = json.loads(p.read_text())
        if not (p.parent/'summary.json').exists():
            raise ValueError('Pilot inference is still running or an attempt is unfinished')
        summary = json.loads((p.parent/'summary.json').read_text())
        rows = [json.loads(s) for s in (p.parent/'predictions.jsonl').read_text().splitlines()]
        arm, index = manifest['arm'], manifest['pilot_index']
        if manifest['stage'] != 'pilot' or manifest['split'] != 'fit':
            raise ValueError('Report accepts only fitting pilot runs')
        attempts.append(dict(run=p.parent.name, arm=arm, index=index, complete=summary['complete'],
                             rows=len(rows), errors=summary.get('errors'),
                             provider=manifest['identity']['model']['provider_name']))
        if not summary['complete'] or manifest['identity'] != identity(registry, arm):
            continue
        if len(rows) != 1 or rows[0]['split'] != 'fit' or rows[0]['id'] != manifest['ids'][0]:
            raise ValueError('Wrong pilot population')
        key = (arm, index)
        if key in chosen:
            raise ValueError('Duplicate completed pilot observation')
        for name, value in metrics(rows).items():
            if summary[name] != value:
                raise ValueError('Metric mismatch')
        chosen[key] = rows[0]
    conditions = {}
    references = None
    for arm in registry['arms']:
        indices = sorted(i for a, i in chosen if a == arm)
        if indices != list(range(registry['pilot_n'])):
            raise ValueError('Incomplete registered pilot; report separately as partial')
        rows = [chosen[arm, i] for i in indices]
        ids = [(r['id'], r['expected'], r['group']) for r in rows]
        if references is not None and ids != references:
            raise ValueError('Mismatched pilot prompts/gold/groups')
        references = ids
        usages = [r['usage'] for r in rows if 'cost' in r.get('usage', {})]
        count = len(rows)
        cost = sum(float(u['cost']) for u in usages)
        upper = sum(r.get('cost_upper_bound_usd', 0) for r in rows)
        failures = Counter(r.get('error_type', 'none') for r in rows if r['prediction'] == 'ERROR')
        conditions[arm] = dict(n=count, valid=sum(r['prediction'] != 'ERROR' for r in rows),
            descriptive_fitting_metrics=metrics(rows), error_types=dict(failures),
            reported_cost_usd=cost, missing_cost=count-len(usages), unreported_cost_upper_bound_usd=upper,
            mean_latency_seconds=mean(r['latency_seconds'] for r in rows),
            median_latency_seconds=median(r['latency_seconds'] for r in rows),
            usage_available_n=len(usages),
            mean_input_tokens_when_reported=mean(u['prompt_tokens'] for u in usages) if usages else None,
            mean_output_tokens_when_reported=mean(u['completion_tokens'] for u in usages) if usages else None,
            reasoning_tokens_reported=sum((u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0) for u in usages),
            responses_reporting_positive_reasoning=sum((u.get('completion_tokens_details') or {}).get('reasoning_tokens', 0)>0 for u in usages),
            projected_full_cost_at_pilot_mean_usd=estimate['arms'][arm]['requests']*cost/count,
            projected_full_cost_at_pilot_mean_with_unknown_ceiling_usd=estimate['arms'][arm]['requests']*(cost+upper)/count)
    comparisons = {}
    for model in registry['models']:
        low = [chosen[model+'-lower', i] for i in range(registry['pilot_n'])]
        high = [chosen[model+'-higher', i] for i in range(registry['pilot_n'])]
        comparisons[model] = dict(different_decisions=sum(a['prediction'] != b['prediction'] for a,b in zip(low,high)),
            lower_only_correct=sum(a['prediction']==a['expected'] and b['prediction']!=b['expected'] for a,b in zip(low,high)),
            higher_only_correct=sum(b['prediction']==b['expected'] and a['prediction']!=a['expected'] for a,b in zip(low,high)))
    return dict(study='frontier-api-v1-pilot', complete=True, task='prompt harmfulness', split='fit',
        unique_prompts=registry['pilot_n'], planned_observations=len(chosen), total_attempts=sum(a['rows'] for a in attempts),
        conditions=conditions, comparisons=comparisons, attempts=attempts,
        reported_cost_usd=sum(v['reported_cost_usd'] for v in conditions.values()),
        unreported_cost_upper_bound_usd=sum(v['unreported_cost_upper_bound_usd'] for v in conditions.values()),
        projected_full_cost_at_pilot_mean_usd=sum(v['projected_full_cost_at_pilot_mean_usd'] for v in conditions.values()),
        projected_full_cost_with_unknown_ceiling_usd=sum(v['projected_full_cost_at_pilot_mean_with_unknown_ceiling_usd'] for v in conditions.values()),
        projection_limitations=['32 fitting prompts only; not representative of every policy or split',
            'Uses observed cache/routing behavior; future billing may differ',
            'Future tuned prompt lengths and reasoning demands are unknown',
            'Unreported costs are bounded, not assumed zero',
            'No policy search, validation selection, or held-out evaluation completed'])


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry', type=Path, required=True)
    p.add_argument('--runs', type=Path, required=True)
    p.add_argument('--estimate', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    args.out.write_text(json.dumps(summarize(args.registry, args.runs, args.estimate), indent=2)+'\n')
