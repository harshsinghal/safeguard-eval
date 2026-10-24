"""Post-freeze train/test overlap audit; never filters the official main score."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path

from evals.wildguard.data import normalized,shingles,SEED
from evals.wildguard.run import read_rows,digest


def audit(train,test,freeze,out):
    from datasketch import MinHash,MinHashLSH
    f=json.loads(Path(freeze).read_text())
    if f.get('status')!='frozen':raise ValueError('Freeze required')
    cert=json.loads(Path(test).with_suffix('.provenance.json').read_text())
    if cert['freeze_sha256']!=digest(freeze) or cert['data_sha256']!=digest(test):raise ValueError('Test provenance mismatch')
    train_rows=read_rows(train);test_rows=read_rows(test)
    if any(r['split']=='test' for r in train_rows) or {r['split'] for r in test_rows}!={'test'}:raise ValueError('Wrong partitions')
    exact=defaultdict(list)
    for row in train_rows:exact[normalized(row['prompt'])].append(row)
    index=MinHashLSH(threshold=.65,num_perm=64);lookup={};sets={}
    for i,(text,rows) in enumerate(exact.items()):
        features=shingles(text);h=MinHash(num_perm=64,seed=SEED);h.update_batch([s.encode() for s in sorted(features)])
        index.insert(str(i),h);sets[i]=features;lookup[i]=rows
    results=[]
    for row in test_rows:
        text=normalized(row['prompt']);matches=exact.get(text,[]);kind='exact' if matches else None
        if not matches:
            features=shingles(text);h=MinHash(num_perm=64,seed=SEED);h.update_batch([s.encode() for s in sorted(features)])
            for key in index.query(h):
                i=int(key)
                if len(features&sets[i])/len(features|sets[i])>=.85:matches+=lookup[i]
            if matches:kind='near'
        results.append(dict(id=row['id'],overlap=kind,train_partitions=sorted({r['split'] for r in matches}),train_ids=sorted({r['id'] for r in matches})))
    result=dict(train_sha256=digest(train),test_sha256=digest(test),freeze_sha256=digest(freeze),
        counts=dict(Counter(r['overlap'] or 'none_detected' for r in results)),rows=results,
        caveat='Approximate lexical near-duplicate retrieval, not a semantic contamination test. The full official test remains the primary evaluation.')
    Path(out).write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('train','test','freeze','out'):p.add_argument('--'+key,required=True)
    a=p.parse_args();r=audit(a.train,a.test,a.freeze,a.out);print(json.dumps(r['counts']))
