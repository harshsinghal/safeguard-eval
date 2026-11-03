"""Read static artifacts, group before splitting, and publish no raw content."""
import argparse
from collections import Counter, defaultdict
import hashlib
import re
import stat
import unicodedata
import numpy as np
from .common import *

PURPLE_REV = 'f64eebd53003a87d9c2d2a3a712133534c214c8d'
SKILL_REV = '3548e2837adf58b96497f2c688f96beff26485da'
MAX_BYTES = 20000
EXCLUDED_FILES = {'_meta.json','_expected.json','_evidence.json','_source_inventory.txt'}

def normalized(text): return ' '.join(unicodedata.normalize('NFKC',text).lower().split())
def family(name): return re.sub(r'[^\w]+','',re.sub(r'__(CI|PI|MIXED)_B\d+$','',name),flags=re.UNICODE).lower()

class Union:
    def __init__(self,n): self.p=list(range(n))
    def find(self,i):
        while self.p[i] != i: self.p[i]=self.p[self.p[i]]; i=self.p[i]
        return i
    def join(self,i,j):
        a,b=self.find(i),self.find(j)
        if a != b: self.p[max(a,b)]=min(a,b)

def group_records(rr, near_text):
    from sklearn.feature_extraction.text import HashingVectorizer
    from sklearn.neighbors import NearestNeighbors
    u=Union(len(rr)); seen={}
    for i,r in enumerate(rr):
        for key in r.pop('_group_keys'):
            if key in seen: u.join(i,seen[key])
            else: seen[key]=i
    vec=HashingVectorizer(analyzer='char',ngram_range=(5,5),n_features=2**18,alternate_sign=False,norm='l2',lowercase=False)
    xx=vec.transform(near_text)
    nn=NearestNeighbors(radius=.06,metric='cosine',algorithm='brute',n_jobs=2).fit(xx)
    edges=0
    for start in range(0,len(rr),256):
        for k,near in enumerate(nn.radius_neighbors(xx[start:start+256],return_distance=False)):
            for j in near:
                i=start+k
                if int(j)>i: u.join(i,int(j));edges+=1
    components=defaultdict(list)
    for i,r in enumerate(rr):components[u.find(i)].append(r['id'])
    for i,r in enumerate(rr):r['group']=hash_value(sorted(components[u.find(i)]))[:24]
    return dict(groups=len(components),largest_group=max(map(len,components.values())),near_edges=edges)

def partition(rr, limits):
    from sklearn.model_selection import GroupShuffleSplit
    groups=[r['group'] for r in rr]
    dev,te=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED).split(rr,groups=groups))
    fi,va=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=SEED+1).split(dev,groups=[groups[i] for i in dev]))
    pools={'fit':[rr[dev[i]] for i in fi],'validation':[rr[dev[i]] for i in va],'test':[rr[i] for i in te]}
    out={}
    for split,pool in pools.items():
        by={label:sorted([r for r in pool if r['expected']==label],key=lambda r:hash_value([SEED,r['id']])) for label in ('ALLOW','BLOCK')}
        n=min(limits[split]//2,*map(len,by.values()))
        out[split]=sorted(by['ALLOW'][:n]+by['BLOCK'][:n],key=lambda r:r['id'])
    return out

def record(uid,prompt,label,**kw):
    return dict(id=uid,prompt=prompt,prompt_sha256=hash_value(prompt),expected=label,input_bytes=len(prompt.encode()),**kw)

def cyber(state):
    rr=[]
    for source,label in [('mitre','BLOCK'),('frr','ALLOW')]:
        for i,r in enumerate(read(state/f'sources/{source}.json')):
            text=r['mutated_prompt']
            assert isinstance(text,str) and text.strip()
            if source=='frr': assert r['is_malicious'] is False
            keys=['exact:'+hash_value(normalized(text))]
            if source=='mitre':
                for k in ('base_prompt','mutated_prompt_base'):
                    if isinstance(r.get(k),str) and r[k].strip(): keys.append('base:'+hash_value(normalized(r[k])))
            rr.append(record('cyber:'+source+':'+str(i),text,label,source=source,category=r.get('mitre_category','benign_system_change'),_group_keys=keys))
    labels=defaultdict(set)
    for r in rr:labels[hash_value(normalized(r['prompt']))].add(r['expected'])
    bad={k for k,v in labels.items() if len(v)>1}; before=len(rr)
    rr=[r for r in rr if hash_value(normalized(r['prompt'])) not in bad and r['input_bytes']<=MAX_BYTES]
    audit=group_records(rr,[normalized(r['prompt']) for r in rr]);audit.update(source_rows=before,eligible_rows=len(rr),conflicting_or_oversize=before-len(rr))
    return partition(rr,{'fit':768,'validation':256,'test':400}),audit

def inventory(text):
    out={}
    for line in text.split('\n'):
        m=re.match(r'^(GENERATED|WILD|TEST[-_A-Z]*)\s+(.+?)\s+<-\s+(.+)$',line)
        if not m:continue
        source,name,origin=m.groups();v=re.search(r'generated_malicious/(CI|PI|MIXED)/(B\d+)/',origin)
        out[name]=dict(source=source,origin_sha256=hash_value(origin),vector=v[1] if v else 'unknown',behavior=v[2] if v else 'unknown',author=origin.split('/')[1] if source=='WILD' else None)
    return out

def skills(state, checkout):
    checkout=Path(checkout);inv=inventory((checkout/'Dataset/Skills/malware/_source_inventory.txt').read_text())
    rr=[];excluded=Counter();manifest=[]
    for part,label in [('benign','ALLOW'),('malware','BLOCK')]:
        tree=read(state/f'sources/malskill-{part}-tree.json')['tree'];by=defaultdict(list)
        for f in tree:
            if f['type']=='blob' and '/' in f['path']:by[f['path'].split('/')[0]].append(f)
        for name,files in sorted(by.items()):
            if part=='malware' and name not in inv:raise ValueError('Missing provenance for '+name)
            info=inv[name] if part=='malware' else dict(source='BENIGN',vector='benign',behavior='benign',author=None)
            selected=[f for f in files if Path(f['path']).name not in EXCLUDED_FILES and not set(Path(f['path']).parts)&{'_runtime','__pycache__','.git'}]
            if sum(f['size'] for f in selected)>MAX_BYTES:excluded[part+':oversize_source']+=1;continue
            contents=[];failed=None;primary=None
            for f in sorted(selected,key=lambda x:(x['path'].split('/',1)[1]!='SKILL.md',x['path'])):
                rel=f['path'].split('/',1)[1];p=checkout/'Dataset/Skills'/part/f['path']
                if f.get('mode')!='100644' and f.get('mode')!='100755':failed='nonregular';break
                if not stat.S_ISREG(p.lstat().st_mode):failed='nonregular';break
                b=p.read_bytes()
                if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=f['sha']:raise ValueError('Blob hash mismatch')
                try:text=b.decode('utf-8-sig')
                except UnicodeDecodeError:failed='nonutf8';break
                if '\0' in text:failed='binary';break
                if rel=='SKILL.md':primary=text
                contents.append({'path':rel,'text':text})
            if failed or primary is None:excluded[part+':'+(failed or 'missing_skill')]+=1;continue
            full='\n\n'.join('FILE '+c['path']+'\n'+c['text'] for c in contents)
            # The same complete textual input must fit the strictest API wrapper.
            if len(full.encode())>MAX_BYTES or len(canonical(full).encode())>26000:excluded[part+':oversize_serialization']+=1;continue
            uid='skills:'+hash_value([part,name])[:24]
            keys=['family:'+family(name),'exact:'+hash_value(normalized(primary))]
            if info.get('author'):keys.append('wildauthor:'+info['author'])
            rr.append(record(uid,full,label,skill_text=primary,skill_text_sha256=hash_value(primary),source=info['source'],category=info['vector'],behavior=info['behavior'],file_count=len(contents),_group_keys=keys))
            manifest.append(dict(id=uid,source_path='Dataset/Skills/'+part+'/'+name,files=[{'path':f['path'].split('/',1)[1],'git_blob':f['sha'],'bytes':f['size']} for f in selected]))
    # Equal visible full packages with conflicting labels are ambiguous. Skill-only
    # conflicts are retained: hidden malicious scripts are the ablation's point.
    labels=defaultdict(set)
    for r in rr:labels[r['prompt_sha256']].add(r['expected'])
    bad={k for k,v in labels.items() if len(v)>1};excluded['conflicting_full_package']=sum(r['prompt_sha256'] in bad for r in rr)
    rr=[r for r in rr if r['prompt_sha256'] not in bad]
    audit=group_records(rr,[normalized(r['skill_text']) for r in rr]);audit.update(eligible_rows=len(rr),eligible_labels=dict(Counter(r['expected'] for r in rr)),excluded=dict(excluded))
    splits=partition(rr,{'fit':1024,'validation':256,'test':512})
    ids={r['id'] for subset in splits.values() for r in subset}
    jsonl(state/'package-manifest.jsonl',[m for m in manifest if m['id'] in ids])
    return splits,audit

def prepare(state,checkout):
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    report={}
    for task,fn in [('cyber',lambda:cyber(state)),('skills',lambda:skills(state,checkout))]:
        splits,audit=fn();report[task]={'audit':audit,'splits':{}}
        for split,rr in splits.items():
            for r in rr:r['split']=split
            jsonl(state/f'data/{task}/{split}.jsonl',rr);jsonl(state/f'metadata/{task}/{split}.jsonl',[meta(r) for r in rr])
            report[task]['splits'][split]=dict(n=len(rr),labels=dict(Counter(r['expected'] for r in rr)),groups=len({r['group'] for r in rr}),sources=dict(Counter(r['source'] for r in rr)),categories=dict(Counter(r['category'] for r in rr)),max_input_bytes=max(r['input_bytes'] for r in rr))
        for a,b in [('fit','validation'),('fit','test'),('validation','test')]:
            if {r['group'] for r in splits[a]}&{r['group'] for r in splits[b]}:raise ValueError('Group leakage')
            if {r['prompt_sha256'] for r in splits[a]}&{r['prompt_sha256'] for r in splits[b]}:raise ValueError('Input leakage')
    write(state/'data-audit.json',report)
    write(state/'source-manifest.json',dict(purple_revision=PURPLE_REV,skill_revision=SKILL_REV,source_files={str(p.relative_to(state)):digest(p) for p in sorted((state/'sources').glob('*')) if p.is_file()}))
    print(canonical(report))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--checkout',required=True);a=p.parse_args();prepare(a.state,a.checkout)
