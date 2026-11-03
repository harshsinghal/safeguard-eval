"""Pre-test source-format repair; never move a fitting/validation row into test."""
import argparse
from collections import Counter,defaultdict
from .common import *
from .data import group_records,normalized

def amend(state,pilot):
    state=Path(state);pilot=Path(pilot);source=read(state/'sources/mitre.json');rr=[]
    for split in ('fit','validation','test'):
        for old in rows(pilot/f'data/cyber/{split}.jsonl'):
            r=dict(old);r['input_field']='base_prompt' if r['source']=='mitre' else 'mutated_prompt'
            if r['source']=='mitre':r['prompt']=source[int(r['id'].rsplit(':',1)[1])]['base_prompt']
            assert isinstance(r['prompt'],str) and r['prompt'].strip()
            r['prompt_sha256']=hash_value(r['prompt']);r['input_bytes']=len(r['prompt'].encode())
            r['_group_keys']=['old:'+r['group'],'exact:'+hash_value(normalized(r['prompt']))];rr.append(r)
    audit=group_records(rr,[normalized(r['prompt']) for r in rr])
    assignments=defaultdict(set)
    for r in rr:assignments[r['group']].add(r['split'])
    bad={g for g,v in assignments.items() if len(v)>1}
    report=dict(audit={**audit,'original_selected_rows':len(rr),'cross_split_groups_removed':len(bad),
        'cross_split_rows_removed':sum(r['group'] in bad for r in rr),'new_rows_added':0,'assignment_changes':0},splits={})
    for split in ('fit','validation','test'):
        pool=[r for r in rr if r['split']==split and r['group'] not in bad]
        by={label:sorted([r for r in pool if r['expected']==label],key=lambda r:hash_value([SEED,r['id']])) for label in ('ALLOW','BLOCK')}
        n=min(map(len,by.values()));selected=sorted(by['ALLOW'][:n]+by['BLOCK'][:n],key=lambda r:r['id'])
        assert n>=50,'Insufficient cohort after leakage exclusions'
        jsonl(state/f'data/cyber/{split}.jsonl',selected);jsonl(state/f'metadata/cyber/{split}.jsonl',[meta(r) for r in selected])
        report['splits'][split]=dict(n=len(selected),groups=len({r['group'] for r in selected}),
            labels=dict(Counter(r['expected'] for r in selected)),sources=dict(Counter(r['source'] for r in selected)),
            categories=dict(Counter(r['category'] for r in selected)),max_input_bytes=max(r['input_bytes'] for r in selected))
    a=read(state/'data-audit.json');a['cyber']=report;write(state/'data-audit.json',a);print(canonical(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--pilot',required=True);a=p.parse_args();amend(a.state,a.pilot)
