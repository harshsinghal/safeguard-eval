"""Restore private inputs from pinned upstream files and public safe manifests."""
import argparse
import hashlib
import stat
from .common import *

def restore(state,checkout,cyber_sources):
    state=Path(state);checkout=Path(checkout);cyber_sources=Path(cyber_sources)
    manifest={m['id']:m for m in rows(state/'package-manifest.jsonl')}
    cyber={source:read(cyber_sources/(source+'.json')) for source in ('mitre','frr')}
    for task in TASKS:
        for split in ('fit','validation','test'):
            out=[]
            for meta_row in rows(state/f'metadata/{task}/{split}.jsonl'):
                r=dict(meta_row)
                if task=='cyber':
                    _,source,index=r['id'].split(':');r['prompt']=cyber[source][int(index)]['mutated_prompt']
                else:
                    m=manifest[r['id']];parts=[]
                    for f in sorted(m['files'],key=lambda x:(x['path']!='SKILL.md',x['path'])):
                        p=checkout/m['source_path']/f['path']
                        if not p.resolve().is_relative_to(checkout.resolve()) or not stat.S_ISREG(p.lstat().st_mode):raise ValueError('Unsafe file')
                        b=p.read_bytes()
                        if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=f['git_blob']:raise ValueError('Blob drift')
                        text=b.decode('utf-8-sig');parts.append('FILE '+f['path']+'\n'+text)
                        if f['path']=='SKILL.md':r['skill_text']=text
                    r['prompt']='\n\n'.join(parts)
                    if hash_value(r['skill_text'])!=r['skill_text_sha256']:raise ValueError('Skill hash drift')
                if hash_value(r['prompt'])!=r['prompt_sha256']:raise ValueError('Content drift')
                out.append(r)
            target=state/f'data/{task}/{split}.jsonl';jsonl(target,out)
            if digest(target)!=read(state/'registration.json')['files'][str(target.relative_to(state))]:raise ValueError('Restored data differs')
    print('Restored and verified private input hashes.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--checkout',required=True);p.add_argument('--cyber-sources',required=True);a=p.parse_args();restore(a.state,a.checkout,a.cyber_sources)
