"""No-network cost scenarios; these are estimates, never measured inference costs."""
import argparse
import json
from pathlib import Path

from evals.frontier_api.run import payload, reserve_usd
from evals.wildguard.run import digest, read_rows


def estimate(registry_path, data_paths):
    r = json.loads(Path(registry_path).read_text())
    rows = {}
    for split, path in data_paths.items():
        if digest(path) != r['data_hashes'][split]:
            raise ValueError('Wrong population for estimate')
        rows[split] = read_rows(path)
        if len(rows[split]) != r['data_counts'][split]:
            raise ValueError('Wrong count')
    policies = [json.loads((Path(registry_path).parent / c['path']).read_text())
                for c in r['candidates'][:3]]
    # Conservative relative to the three inherited prompts, but new drafts may be longer.
    policy = max(policies, key=lambda p: len(json.dumps(p)))
    scenarios = dict(short=dict(lower=128, higher=512), moderate=dict(lower=512, higher=2048),
                     long=dict(lower=2048, higher=8192))
    result = {'assumptions': dict(input_tokens='UTF-8 bytes / 4 + 32 per request; not provider tokenization',
        policy='longest of shared p0/p1/p2; new candidate lengths unknown', final_policies_max=3,
        repetitions=256, pilot_n=r['pilot_n'], cache_discount=0, retries=0, scope='4 models / 8 arms'),
        'arms': {}}
    for arm, a in r['arms'].items():
        m = r['models'][a['model_key']]
        total_input = upper = n = 0
        stage_costs = {}
        populations = [('fit', rows['fit'], 5), ('validation', rows['validation'], 5),
                       ('audit', rows['audit'], 3), ('test', rows['test'], 3),
                       ('pilot', rows['fit'][:r['pilot_n']], 1), ('repeat', rows['test'][:256], 1)]
        for stage, population, repeats in populations:
            tokens = bound = 0
            for row in population:
                request = payload(r, arm, policy, row['prompt'])
                tokens += len(json.dumps(request['messages'], ensure_ascii=False).encode()) / 4 + 32
                bound += reserve_usd(request, m)
            total_input += tokens * repeats
            upper += bound * repeats
            n += len(population) * repeats
            stage_costs[stage] = dict(requests=len(population)*repeats, estimated_input_tokens=tokens*repeats)
        price = m['price_per_token']
        estimates = {}
        for name, outputs in scenarios.items():
            output = 8 if a['effort'] == 'none' else outputs['lower' if arm.endswith('-lower') else 'higher']
            estimates[name] = total_input * price['prompt'] + n * output * price['completion'] + n * price['request']
        result['arms'][arm] = dict(requests=n, stages=stage_costs, cost_scenarios_usd=estimates,
                                   conservative_request_reservations_usd=upper)
    result['totals_usd'] = {s: sum(v['cost_scenarios_usd'][s] for v in result['arms'].values()) for s in scenarios}
    result['total_requests_max'] = sum(v['requests'] for v in result['arms'].values())
    result['conservative_request_reservations_usd'] = sum(v['conservative_request_reservations_usd'] for v in result['arms'].values())
    result['paid_requests'] = 0
    result['pilot_cost_scenarios_usd'] = {}
    for name, outputs in scenarios.items():
        cost = 0
        for arm, a in r['arms'].items():
            p = r['models'][a['model_key']]['price_per_token']
            n = result['arms'][arm]['stages']['pilot']['requests']
            tokens = result['arms'][arm]['stages']['pilot']['estimated_input_tokens']
            output = 8 if a['effort'] == 'none' else outputs['lower' if arm.endswith('-lower') else 'higher']
            cost += tokens*p['prompt'] + n*output*p['completion'] + n*p['request']
        result['pilot_cost_scenarios_usd'][name] = cost
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry', type=Path, default=Path('evals/frontier_api/registry.json'))
    for split in ('fit', 'validation', 'audit', 'test'):
        p.add_argument('--' + split, type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    result = estimate(args.registry, {s: getattr(args, s) for s in ('fit', 'validation', 'audit', 'test')})
    args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('total_requests_max', 'totals_usd', 'paid_requests')}))
