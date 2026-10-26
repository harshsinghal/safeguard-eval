"""Paired descriptive comparisons; choices are read from the pre-test freeze."""
import argparse
from pathlib import Path

from evals.policy_transfer.common import (BASE, REGISTRY, digest, load_run, locate,
    now, read, sources, write)
from evals.policy_transfer.study import policy_path
from evals.wildguard.metrics import paired_interval


def analyze(state, out):
    state=Path(state)
    f=read(state/'freeze.json'); selection=read(state/'source-selection.json')
    if (f['sources']!=sources() or f['registry_sha256']!=digest(REGISTRY)
            or f['source_selection_sha256']!=digest(state/'source-selection.json')):
        raise ValueError('Frozen study changed')
    reg=read(REGISTRY); pool=selection['pool']
    canonical={e['text_sha256']:e['id'] for e in pool}
    own={s:canonical[e['text_sha256']] for s,e in selection['selected'].items()}
    chosen={s:canonical[e['text_sha256']] for s,e in f['recipient_choice'].items()}
    baseline=read(BASE)['id'];matrix={};contrasts={};substitution={}
    for split in ('audit','test'):
        predictions={};matrix[split]={};contrasts[split]=[]
        for slug in reg['models']:
            predictions[slug]={};matrix[split][slug]={}
            for entry in pool:
                p=policy_path(state,entry);folder=locate(state,slug,entry['id'],split)
                rows,summary,manifest=load_run(folder,slug,p,split)
                if manifest['freeze_sha256']!=digest(state/'freeze.json'):
                    raise ValueError('Final run used wrong freeze')
                predictions[slug][entry['id']]=rows
                matrix[split][slug][entry['id']]=summary
        for recipient in reg['models']:
            rr=predictions[recipient]
            for source in reg['models']:
                policy_id=own[source]
                contrasts[split].append(dict(source=source,recipient=recipient,policy_id=policy_id,
                    vs_baseline=paired_interval(rr[policy_id],rr[baseline]),
                    vs_recipient_own=paired_interval(rr[policy_id],rr[own[recipient]])))
        large='qwen-27b'
        substitution[split]={s:paired_interval(predictions[s][chosen[s]],predictions[large][chosen[large]])
                             for s in reg['models'] if s!=large}
    result=dict(created_utc=now(),freeze_sha256=digest(state/'freeze.json'),
        registry_sha256=digest(REGISTRY),source_selected=own,pool_selected=chosen,
        pool=pool,matrix=matrix,contrasts=contrasts,substitution_vs_qwen27b=substitution,
        interpretation='Exploratory paired accuracy differences; unadjusted descriptive intervals; no test-based selection.')
    write(out,result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();analyze(a.state,a.out)
