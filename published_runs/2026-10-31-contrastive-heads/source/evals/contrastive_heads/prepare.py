import argparse
import hashlib
import shutil
from collections import Counter
from .common import *

def prepare(state, work):
    state,work=Path(state),Path(work)
    if state.exists(): raise ValueError('Use a new state directory')
    state.mkdir(parents=True); data_hashes={}; populations={}
    base=work/'smart-ensemble-run/state'
    for ds in DATASETS:
        metas=[]; populations[ds]={}
        for split in ['fit','validation','test']:
            meta=rows(base/'metadata'/ds/(split+'.jsonl.gz')); metas.append(meta)
            src=base/('sealed-inputs' if split=='test' else 'inputs')/ds/(split+'.jsonl')
            if not src.exists(): src=base/'inputs'/ds/(split+'.jsonl')
            byid={r['id']:r for r in rows(src)}
            if set(byid)!={r['id'] for r in meta}: raise ValueError('Input population mismatch')
            inputs=[]
            for r in meta:
                p=byid[r['id']]['prompt']
                if hashlib.sha256(p.encode()).hexdigest()!=r['prompt_sha256']: raise ValueError('Prompt mismatch')
                inputs.append(dict(id=r['id'],prompt=p,prompt_sha256=r['prompt_sha256']))
            for rel,rr in [(f'metadata/{ds}/{split}.jsonl.gz',meta),(f'inputs/{ds}/{split}.jsonl',inputs)]:
                write_rows(state/rel,rr);data_hashes[rel]=digest(state/rel)
            populations[ds][split]=dict(n=len(meta),groups=len({r['group'] for r in meta}),labels=dict(Counter(r['expected'] for r in meta)))
        assert_disjoint(*metas)
        pp=state/'policies'/ds/'policylm.json';pp.parent.mkdir(parents=True,exist_ok=True)
        # The WG cached features used this exact earlier policy.
        source=(work/'activation-probe-run/state/policy.json') if ds=='wildguard' else base/'policies'/ds/'policylm.json'
        shutil.copy2(source,pp);data_hashes[str(pp.relative_to(state))]=digest(pp)
    # Strictly verify every reused feature, then realign to the canonical metadata order.
    for split in ['fit','validation','test']:
        old=work/'activation-probe-run/state/features/policylm'/split
        m=read(old/'manifest.json');key='policylm-l28-slot.npy'
        if digest(old/key)!=m['artifacts'][key] or digest(state/'policies/wildguard/policylm.json')!=m['policy_sha256']:
            raise ValueError('Cached feature/policy hash mismatch')
        oldmeta=rows(work/'activation-probe-run/state/metadata'/(split+'.jsonl.gz'))
        if digest(work/'activation-probe-run/state/metadata'/(split+'.jsonl.gz'))!=m['metadata_sha256']:
            raise ValueError('Cached metadata changed')
        if m['ids']!=[r['id'] for r in oldmeta] or not all(m['valid']): raise ValueError('Cached feature validity')
        meta=rows(state/'metadata/wildguard'/(split+'.jsonl.gz'));index={r['id']:i for i,r in enumerate(oldmeta)}
        order=[index[r['id']] for r in meta]
        for r,i in zip(meta,order):
            if any(r[k]!=oldmeta[i][k] for k in ['id','expected','prompt_sha256','group']): raise ValueError('Cache alignment')
        folder=state/'features/wildguard/policylm'/split;folder.mkdir(parents=True)
        np.save(folder/'features.npy',np.load(old/key,allow_pickle=False)[order],allow_pickle=False)
        write(folder/'manifest.json',dict(ids=[r['id'] for r in meta],metadata_sha256=digest(state/'metadata/wildguard'/(split+'.jsonl.gz')),
            artifacts={'features.npy':digest(folder/'features.npy')},cached_from='2026-10-30-activation-probe',
            original_manifest_sha256=digest(old/'manifest.json'),original_features_sha256=digest(old/key),model=MODELS['policylm']))
    write(state/'registration.json',dict(created_utc=now(),sources=sources(),data_hashes=data_hashes,
        populations=populations,models=MODELS,seeds=SEEDS,prior_accounted_usd=16.69001787256,
        max_new_gpu_usd=1.6,total_cap_usd=20,prior_smart_freeze_sha256=digest(base/'freeze.json')))
    shutil.copy2(ROOT/'docs/contrastive-heads/PLAN.md',state/'PLAN.md')
    write(state/'progress.json',dict(prepared=True,extracted=False,trained=False,frozen=False,evaluated=False,published=False))
    print(populations)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--work',required=True)
    prepare(**vars(p.parse_args()))
