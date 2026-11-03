"""Restore pinned public inputs privately; emit only counts and provenance."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import urllib.request
import re
import unicodedata

SOURCES = {
    'deepset': ('deepset/prompt-injections', '4f61ecb038e9c3fb77e21034b22511b523772cdd', {
        'train': 'data/train-00000-of-00001-9564e8b05b4757ab.parquet',
        'test': 'data/test-00000-of-00001-701d16158af87368.parquet'}),
    'safeguard': ('xTRam1/safe-guard-prompt-injection', 'a3a877d608f37b7d20d9945671902df895ecdb46', {
        'train': 'data/train-00000-of-00001.parquet', 'test': 'data/test-00000-of-00001.parquet'}),
    'notinject': ('leolee99/NotInject', '847ae76cf8fea5ed325429e569ae8cfef022d2e0', {
        k: f'data/NotInject_{k}-00000-of-00001.parquet' for k in ('one','two','three')}),
}
JBB_REV = '909e68c01d94222b8ad2e397a017e2e12e2adb73'
JBB_PATHS = {k: f'attack-artifacts/{k}/{mode}/vicuna-13b-v1.5.json'
             for k,mode in [('GCG','white_box'),('PAIR','black_box')]}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def dump(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def fetch(state):
    state=Path(state);manifest={}
    def get(rel,url):
        dest=state/'sources'/rel; dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'SafeguardEvalResearch/1.0'})
            with urllib.request.urlopen(req,timeout=90) as r: data=r.read()
            dest.write_bytes(data)
        manifest[rel]={'url':url,'sha256':sha(dest.read_bytes()),'bytes':dest.stat().st_size}
    for ds,(repo,rev,parts) in SOURCES.items():
        base=f'https://huggingface.co/datasets/{repo}/resolve/{rev}/'
        for part,rel in parts.items(): get(f'{ds}/{part}.parquet',base+rel)
        get(f'{ds}/README.md',base+'README.md')
    for method,rel in JBB_PATHS.items():
        get(f'jbb/{method}.json',f'https://raw.githubusercontent.com/JailbreakBench/artifacts/{JBB_REV}/{rel}')
    get('jbb/README.md',f'https://raw.githubusercontent.com/JailbreakBench/artifacts/{JBB_REV}/README.md')
    get('jbb/LICENSE',f'https://raw.githubusercontent.com/JailbreakBench/artifacts/{JBB_REV}/LICENSE')
    dump(state/'source-manifest.json',manifest)
    print(json.dumps({'downloaded_files':len(manifest)}))

def inspect(state):
    import pyarrow.parquet as pq
    state=Path(state);summary={}
    for ds,(_,_,parts) in SOURCES.items():
        for part in parts:
            t=pq.read_table(state/'sources'/ds/(part+'.parquet'))
            info={'n':len(t),'columns':t.column_names}
            if 'label' in t.column_names:info['labels']=dict(Counter(t['label'].to_pylist()))
            summary[f'{ds}/{part}']=info
    for method in JBB_PATHS:
        x=json.loads((state/'sources/jbb'/f'{method}.json').read_text())
        info={'type':type(x).__name__,'keys':list(x) if isinstance(x,dict) else None}
        if isinstance(x,dict):
            info['list_fields']={k:{'n':len(v),'first_keys':list(v[0]) if v and isinstance(v[0],dict) else None}
                                 for k,v in x.items() if isinstance(v,list)}
        summary['jbb/'+method]=info
    dump(state/'source-summary.json',summary);print(json.dumps(summary,indent=2))

def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())

def jsonl(path, records):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records))

def prepare(state):
    import numpy as np
    import pyarrow.parquet as pq
    from sklearn.feature_extraction.text import HashingVectorizer
    state=Path(state)
    if (state/'data-audit.json').exists(): raise ValueError('Already prepared; do not overwrite')
    records=[]; goals=[]; missing_jbb=[]
    def add(ds,part,i,text,y,**extra):
        if not isinstance(text,str) or not text.strip():raise ValueError('Missing source text')
        records.append(dict(id=f'{ds}:{part}:{i}',dataset=ds,original_split=part,
            split='development' if part=='train' else 'test',prompt=text,
            prompt_sha256=sha(text.encode()),expected='BLOCK' if y else 'ALLOW',**extra))
    for ds,(_,_,parts) in SOURCES.items():
        for part in parts:
            rr=pq.read_table(state/'sources'/ds/(part+'.parquet')).to_pylist()
            for i,r in enumerate(rr):
                if ds=='notinject':add(ds,part,i,r['prompt'],0,category=r['category'],trigger_group=part)
                else:add(ds,part,i,r['text'],int(r['label']))
    for method in JBB_PATHS:
        rr=json.loads((state/'sources/jbb'/f'{method}.json').read_text())['jailbreaks']
        for i,r in enumerate(rr):
            if not isinstance(r.get('prompt'),str) or not r['prompt'].strip():
                missing_jbb.append(dict(method=method,index=i,reason='No released attack prompt'))
                continue
            add('jbb',method,i,r['prompt'],1,attack_method=method,behavior_index=r['index'],
                category=r['category'],original_attack_succeeded=bool(r['jailbroken']))
            goals.append((len(records)-1,r['goal']))
    texts=[normalize(r['prompt']) for r in records]+[normalize(g) for _,g in goals]
    n=len(texts);parent=list(range(n))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(i,j):
        a,b=root(i),root(j)
        if a!=b:parent[max(a,b)]=min(a,b)
    exact={}
    for i,t in enumerate(texts):
        if t in exact:union(i,exact[t])
        else:exact[t]=i
    # Hashing is data-independent. Test labels are not involved in this text-only
    # exclusion audit. Whole connected components are kept out of development.
    v=HashingVectorizer(analyzer='char',ngram_range=(5,5),n_features=2**20,
        alternate_sign=False,norm='l2',lowercase=False,dtype=np.float32)
    x=v.transform(texts);near_edges=0
    for start in range(0,n,128):
        sims=(x[start:start+128] @ x.T).tocoo()
        keep=(sims.data>=.90)&(sims.col>sims.row+start)
        for ii,jj in zip(sims.row[keep],sims.col[keep]):
            i=int(ii)+start;j=int(jj)
            if min(len(texts[i]),len(texts[j]))>=20:
                union(i,j);near_edges+=1
    for k,(idx,_) in enumerate(goals):union(idx,len(records)+k)
    # GCG and PAIR versions of the same goal are related, including for CIs.
    behaviors={}
    for i,r in enumerate(records):
        if r['dataset']=='jbb':
            k=r['behavior_index']
            if k in behaviors:union(i,behaviors[k])
            else:behaviors[k]=i
    groups={}
    for i,r in enumerate(records):groups.setdefault(root(i),[]).append(r)
    held={root(i) for i,r in enumerate(records) if r['split']=='test'}
    excluded=[];dev=[];test=[]
    for gid,rr in groups.items():
        group=sha('|'.join(sorted(r['id'] for r in rr)).encode())[:20]
        for r in rr:
            r['group']=group
            t=r['prompt']
            r['slices']={'non_ascii':any(ord(c)>127 for c in t),
                'format_characters':any(unicodedata.category(c)=='Cf' for c in t),
                'punctuation_run':bool(re.search(r'[^\w\s]{6,}',t)),
                'long_message':len(t)>2000}
            if r['split']=='test':test.append(r)
            elif gid in held:excluded.append({k:v for k,v in r.items() if k!='prompt'})
            else:dev.append(r)
    # Assign each entire group once. Sample up to 64 distinct groups for each
    # source/label in each split, without looking at model outputs.
    chosen={s:[] for s in ('fit','validation')};seen=set()
    for split in chosen:
        half=0 if split=='fit' else 1
        for ds in ('deepset','safeguard'):
            for label in ('ALLOW','BLOCK'):
                rr=[r for r in dev if r['dataset']==ds and r['expected']==label and
                    int(sha(('20261102:'+r['group']).encode()),16)%2==half]
                rr.sort(key=lambda r:sha(('sample:'+r['id']).encode()))
                count=0
                for r in rr:
                    if r['group'] in seen:continue
                    seen.add(r['group']);r['split']=split;chosen[split].append(r);count+=1
                    if count==64:break
    chosen['test']=test
    for split,rr in chosen.items():
        rr.sort(key=lambda r:r['id'])
        jsonl(state/'data'/f'{split}.jsonl',rr)
        jsonl(state/'metadata'/f'{split}.jsonl',({k:v for k,v in r.items() if k!='prompt'} for r in rr))
    for a,b in [('fit','validation'),('fit','test'),('validation','test')]:
        assert not {r['group'] for r in chosen[a]} & {r['group'] for r in chosen[b]}
    audit=dict(near_duplicate_rule='NFKC/casefold/whitespace exact; >=0.90 cosine of hashed character 5-gram counts, minimum 20 characters; connected components; JBB goals included',
        near_edges=near_edges,excluded_development=len(excluded),missing_jbb=missing_jbb,
        excluded_by_source=dict(Counter(r['dataset'] for r in excluded)),
        development_unused=len(dev)-sum(len(chosen[s]) for s in ('fit','validation')),
        splits={s:{ds:dict(n=sum(r['dataset']==ds for r in rr),
            labels=dict(Counter(r['expected'] for r in rr if r['dataset']==ds)))
            for ds in sorted({r['dataset'] for r in rr})} for s,rr in chosen.items()},
        test_duplicate_groups=sum(sum(r['split']=='test' for r in rr)>1 for rr in groups.values()),
        test_cross_source_groups=sum(len({r['dataset'] for r in rr if r['split']=='test'})>1 for rr in groups.values()),
        files={str(p.relative_to(state)):sha(p.read_bytes()) for p in sorted((state/'data').glob('*.jsonl'))})
    jsonl(state/'excluded-development.jsonl',excluded);dump(state/'data-audit.json',audit)
    print(json.dumps(audit,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['fetch','inspect','prepare']);p.add_argument('--state',required=True)
    a=p.parse_args();globals()[a.command](a.state)
