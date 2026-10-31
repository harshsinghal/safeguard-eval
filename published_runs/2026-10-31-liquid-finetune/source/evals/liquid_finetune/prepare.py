import argparse
import shutil
from collections import Counter
from .common import *


def prepare(state, previous):
    state, previous = Path(state), Path(previous)
    state.mkdir(parents=True, exist_ok=False)
    hashes = {}; populations = {}; metas = []
    old = read(previous/'registration.json')
    for split in ['fit','validation','test']:
        for kind,extension in [('inputs','.jsonl'),('metadata','.jsonl.gz')]:
            src = previous/kind/'wildguard'/(split+extension)
            if digest(src) != old['data_hashes'][str(src.relative_to(previous))]:
                raise ValueError('Earlier data hash changed')
            dst = state/kind/(split+extension); dst.parent.mkdir(exist_ok=True)
            shutil.copy2(src,dst); hashes[str(dst.relative_to(state))] = digest(dst)
        data = load_inputs(state,split)
        meta = aligned_metadata(state,split,[r['id'] for r in data]); metas.append(meta)
        if any(a['prompt_sha256'] != b['prompt_sha256'] for a,b in zip(data,meta)):
            raise ValueError('Content alignment mismatch')
        populations[split] = dict(n=len(meta),labels=dict(Counter(r['expected'] for r in meta)),
                                 groups=len({r['group'] for r in meta}))
    assert_disjoint(*metas)
    write(state/'registration.json',dict(created_utc=now(),sources=sources(),data_hashes=hashes,
        populations=populations,model=MODEL,revision=REVISION,seeds=SEEDS,rates=RATES,epochs=EPOCHS,
        prior_registration_sha256=digest(previous/'registration.json'),
        prior_accounted_usd=16.80001787256,max_new_gpu_usd=1.6,total_cap_usd=20))
    shutil.copy2(ROOT/'docs/liquid-finetune/PLAN.md',state/'PLAN.md')
    print(populations,flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--previous',required=True)
    prepare(**vars(p.parse_args()))
