"""Reconstruct exact prior ensemble populations without publishing source prompts."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
from .common import ROOT, MODELS, read, rows, write, write_rows, digest, now, assert_disjoint


def prepare(state, prior_work):
    state, prior = Path(state), Path(prior_work)
    if (state/'data-manifest.json').exists():
        raise ValueError('Immutable preparation already exists')
    source = ROOT/'published_runs/2026-10-27-ensemble'
    raw = rows(prior/'wildguard-run/data/train.jsonl')
    test = rows(prior/'policy-transfer-run/state/data/test.jsonl')
    lookup = {r['id']: r for r in raw+test}
    splits = {}; provenance = {}
    for split in ('fit', 'validation', 'test'):
        src = source/'scores/wildguard/policylm'/(split+'.jsonl.gz')
        saved = sorted(rows(src), key=lambda r: r['id'])
        population = []
        for r in saved:
            original = lookup[r['id']]
            for k in ('expected', 'group', 'prompt_sha256'):
                if r[k] != original[k]:
                    raise ValueError('Frozen population differs: '+k)
            import hashlib
            if hashlib.sha256(original['prompt'].encode()).hexdigest() != r['prompt_sha256']:
                raise ValueError('Source text hash differs')
            meta = {k: r[k] for k in ('id','expected','group','prompt_sha256','subcategory','adversarial')}
            population.append(dict(meta, split=split, prompt=original['prompt']))
        splits[split] = population
        write_rows(state/'private-data'/(split+'.jsonl'), population)
        write_rows(state/'inputs'/(split+'.jsonl'), [{k:r[k] for k in ('id','prompt','prompt_sha256')} for r in population])
        write_rows(state/'metadata'/(split+'.jsonl.gz'), [{k:v for k,v in r.items() if k!='prompt'} for r in population])
        write_rows(state/'native-archive'/(split+'.jsonl.gz'), saved)
        provenance[str(src.relative_to(ROOT))] = digest(src)
    assert_disjoint(*splits.values())
    if [len(splits[s]) for s in ('fit','validation','test')] != [4096,1536,1699]:
        raise ValueError('Unexpected population')
    policy = source/'policies/wildguard/shieldstral.json'
    shutil.copyfile(policy, state/'policy.json')
    manifest = dict(created_utc=now(), models=MODELS, policy_sha256=digest(policy),
                    source_hashes=provenance, protocol_sha256=digest(ROOT/'docs/shield-probe/PLAN.md'),
                    counts={s:dict(n=len(rr),groups=len({r['group'] for r in rr}),
                                  labels=dict(Counter(r['expected'] for r in rr))) for s,rr in splits.items()},
                    hashes={str(p.relative_to(state)):digest(p) for sub in ('inputs','metadata','native-archive')
                            for p in sorted((state/sub).glob('*'))})
    write(state/'data-manifest.json', manifest, exclusive=True)
    print(manifest['counts'])


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--state',required=True);p.add_argument('--prior-work',required=True)
    prepare(**vars(p.parse_args()))
