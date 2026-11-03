"""Pinned static data preparation. Archive contents are NEVER extracted or executed."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import tarfile
import urllib.parse
import urllib.request
import zipfile
import numpy as np
import pyarrow.parquet as pq
from .common import *

SKILL_REV='d4b42ce5766a6e0359c987cf59c1007cb3795a90'
OMC_REV='f0722971eddb654c308106c9086ff69da5b0484b'

def download(url,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'SafeguardEval-static-research'})
        with urllib.request.urlopen(req,timeout=90) as response:blob=response.read(80*1024*1024+1)
        if len(blob)>80*1024*1024:raise ValueError('Download exceeds bound')
        path.write_bytes(blob)
    return dict(url=url,sha256=digest(path),bytes=path.stat().st_size)

def fetch(state):
    state=Path(state);manifest={}
    for name,rev,files,prefix in [
        ('skills',SKILL_REV,['README.md','primary.parquet','splits/source_disjoint.parquet','source_registry.csv'],
         'https://huggingface.co/datasets/ProtectSkills/MaliciousSkillBench/resolve/'),
        ('omc',OMC_REV,['README.md','data/file_labels.parquet','results/manifest.csv'],
         'https://raw.githubusercontent.com/False-Positive-Community/open-malicious-code-benchmark/')]:
        for rel in files:
            key=f'sources/{name}/{rel}';manifest[key]=download(prefix+rev+'/'+rel,state/key)
    packages=list(csv.DictReader((state/'sources/omc/results/manifest.csv').open()))
    def one(row):
        rel='packages/'+row['folder_name'];key='sources/omc/'+rel
        return key,download('https://raw.githubusercontent.com/False-Positive-Community/open-malicious-code-benchmark/'+OMC_REV+'/'+urllib.parse.quote(rel),state/key)
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i,(key,entry) in enumerate(pool.map(one,packages)):
            manifest[key]=entry
            if i%100==0:print('Static archives downloaded',i+1,'of',len(packages),flush=True)
    write(state/'source-manifest.json',dict(revisions={'skills':SKILL_REV,'omc':OMC_REV},files=manifest))

def member_bytes(path,name):
    """Read one regular member in memory; reject links, traversal, and large files."""
    parts=Path(name).parts
    if Path(name).is_absolute() or '..' in parts:raise ValueError('Unsafe member path')
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            member=z.getinfo(name)
            if member.is_dir() or (member.external_attr>>16)&0o170000==0o120000:raise ValueError('Not a regular member')
            if member.file_size>4*1024*1024:raise ValueError('Oversized member')
            return z.read(member)
    with tarfile.open(path,'r:*') as t:
        member=t.getmember(name)
        if not member.isfile() or member.size>4*1024*1024:raise ValueError('Not a bounded regular member')
        return t.extractfile(member).read()

def sample(rr,n):
    """Class-balanced deterministic sample, capped by the smaller class."""
    by={label:sorted([r for r in rr if r['expected']==label],key=lambda r:hash_value([SEED,r['id']])) for label in ('ALLOW','BLOCK')}
    count=min(n//2,*[len(x) for x in by.values()])
    return sorted(by['ALLOW'][:count]+by['BLOCK'][:count],key=lambda r:r['id'])

def record(uid,text,label,group,**meta):
    content,clipped=view(text)
    return dict(id=uid,prompt=content,prompt_sha256=hash_value(content),expected=label,group=group,
        original_sha256=hashlib.sha256(text.encode()).hexdigest(),original_bytes=len(text.encode()),
        input_bytes=len(content.encode()),clipped=clipped,**meta)

def skills(state):
    table=pq.read_table(state/'sources/skills/primary.parquet').to_pylist()
    split={r['benchmark_id']:r['split'] for r in pq.read_table(state/'sources/skills/splits/source_disjoint.parquet').to_pylist()}
    result=defaultdict(list);excluded=Counter()
    for row in table:
        s=split[row['benchmark_id']]
        if s=='excluded':excluded['publisher_excluded']+=1;continue
        if row['skill_text'] is None:excluded['original_text_withheld_'+s]+=1;continue
        r=record('skills:'+row['benchmark_id'],row['skill_text'],'BLOCK' if str(row['label'])=='1' else 'ALLOW',
            row['structural_family_id'] or row['normalized_hash'],dataset='skills',source=row['source_id'],
            categories=row['attack_category_codes'],release_status=row['release_status'])
        result[s].append(r)
    # Preserve official source holdouts; exclude exact bounded-view leakage from development.
    test_hashes={r['prompt_sha256'] for r in result['test']}
    for s in ('train','validation'):
        keep=[r for r in result[s] if r['prompt_sha256'] not in test_hashes]
        excluded['view_overlap_test_'+s]=len(result[s])-len(keep);result[s]=keep
    val_hashes={r['prompt_sha256'] for r in result['validation']}
    keep=[r for r in result['train'] if r['prompt_sha256'] not in val_hashes]
    excluded['view_overlap_validation_train']=len(result['train'])-len(keep);result['train']=keep
    return {'fit':sample(result['train'],1024),'validation':sample(result['validation'],256),'test':result['test']},dict(excluded)

class Union:
    def __init__(self,n):self.parent=list(range(n))
    def find(self,x):
        while self.parent[x]!=x:self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def join(self,a,b):
        a,b=self.find(a),self.find(b)
        if a!=b:self.parent[max(a,b)]=min(a,b)

def code(state):
    labels=pq.read_table(state/'sources/omc/data/file_labels.parquet').to_pylist()
    by=defaultdict(list);excluded=Counter();out=[]
    for r in labels:
        if r['file_label'] not in ('benign','malicious'):excluded['unknown_label']+=1;continue
        by[(r['project_name'],r['file_label'])].append(r)
    for (package,label),rr in sorted(by.items()):
        accepted=0
        for r in sorted(rr,key=lambda x:hash_value([SEED,x['file_sha256'],x['filename']])):
            if accepted==2:break
            try:raw=member_bytes(state/'sources/omc/packages'/package,r['filename'])
            except (KeyError,ValueError,tarfile.TarError,zipfile.BadZipFile) as exc:
                excluded['archive_'+type(exc).__name__]+=1;continue
            if hashlib.sha256(raw).hexdigest()!=r['file_sha256']:
                excluded['source_hash_mismatch']+=1;continue
            try:text=raw.decode('utf-8-sig')
            except UnicodeDecodeError:excluded['not_utf8']+=1;continue
            if len(text.strip())<80 or '\0' in text:excluded['short_or_binary']+=1;continue
            uid='code:'+hash_value([package,r['filename']])[:24]
            out.append(record(uid,text,'BLOCK' if label=='malicious' else 'ALLOW',package,dataset='code',
                source=r['ecosystem'],package=package,member=r['filename'],label_source=r['label_source'],
                package_label=r['package_label'],file_sha256=r['file_sha256']))
            accepted+=1
    # Conflicting exact views cannot support a deterministic text-only ground truth.
    byview=defaultdict(set)
    for r in out:byview[r['prompt_sha256']].add(r['expected'])
    bad={h for h,ss in byview.items() if len(ss)>1}
    excluded['conflicting_exact_view']=sum(r['prompt_sha256'] in bad for r in out)
    out=[r for r in out if r['prompt_sha256'] not in bad]
    # Group package members AND near-duplicate file views before partitioning.
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.neighbors import NearestNeighbors
    from sklearn.model_selection import GroupShuffleSplit
    union=Union(len(out));packages={};exact={}
    for i,r in enumerate(out):
        for key,index in [(r['package'],packages),(r['prompt_sha256'],exact)]:
            if key in index:union.join(i,index[key])
            else:index[key]=i
    vec=HashingVectorizer(analyzer='char',ngram_range=(5,5),n_features=2**18,alternate_sign=False,norm='l2',lowercase=False)
    features=vec.transform(r['prompt'] for r in out)
    neighbors=NearestNeighbors(radius=.06,metric='cosine',algorithm='brute').fit(features).radius_neighbors(features,return_distance=False)
    for i,nn in enumerate(neighbors):
        for j in nn:
            if j!=i:union.join(i,int(j))
    members=defaultdict(list)
    for i,r in enumerate(out):members[union.find(i)].append(r['id'])
    for i,r in enumerate(out):r['group']='code:'+hash_value(sorted(members[union.find(i)]))[:24]
    groups=[r['group'] for r in out]
    dev,te=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED).split(out,groups=groups))
    fi,va=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED+1).split(dev,groups=[groups[i] for i in dev]))
    result={'fit':sample([out[dev[i]] for i in fi],1024),'validation':sample([out[dev[i]] for i in va],256),
        'test':sample([out[i] for i in te],512)}
    return result,dict(excluded,eligible_files=len(out),groups=len(members),largest_group=max(map(len,members.values())))

def prepare(state):
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    report={}
    for task,fn in [('code',code),('skills',skills)]:
        splits,audit=fn(state);report[task]={'audit':audit,'splits':{}}
        for split,rr in splits.items():
            for r in rr:r['split']=split
            rr.sort(key=lambda r:r['id']);jsonl(state/f'data/{task}/{split}.jsonl',rr)
            jsonl(state/f'metadata/{task}/{split}.jsonl',[metadata(r) for r in rr])
            report[task]['splits'][split]=dict(n=len(rr),labels=dict(Counter(r['expected'] for r in rr)),
                clipped=sum(r['clipped'] for r in rr),groups=len({r['group'] for r in rr}),
                sources=dict(Counter(r['source'] for r in rr)))
        for a,b in [('fit','validation'),('fit','test'),('validation','test')]:
            if {r['prompt_sha256'] for r in splits[a]} & {r['prompt_sha256'] for r in splits[b]}:raise ValueError('Exact view leakage')
            if task=='code' and {r['group'] for r in splits[a]} & {r['group'] for r in splits[b]}:raise ValueError('Group leakage')
    write(state/'data-audit.json',report);print(canonical(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['fetch','prepare']);p.add_argument('--state',required=True)
    a=p.parse_args();globals()[a.action](a.state)
