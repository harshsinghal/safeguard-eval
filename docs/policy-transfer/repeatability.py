"""Post hoc replication check of the initial policy; never used for selection."""
import argparse
import gzip
import json
from pathlib import Path


def read(path):return json.loads(Path(path).read_text())


def rows(folder):
    return [json.loads(x) for x in gzip.decompress((folder/'predictions.jsonl.gz').read_bytes()).decode().split('\n') if x]


def compare(new,wildguard,qwen):
    result={}
    for slug in ('policylm','shieldstral','qwen-2b','qwen-4b','qwen-27b'):
        prior=Path(qwen if slug.startswith('qwen') else wildguard)/'runs'/(slug+'-test-p0')
        current=Path(new)/'new-runs/runs'/(slug+'--wg-p0-taxonomy--test')
        a=read(prior/'manifest.json');b=read(current/'manifest.json')
        assert all(a[k]==b[k] for k in ('revision','policy_sha256','dataset_sha256'))
        old={r['id']:r for r in rows(prior)};fresh={r['id']:r for r in rows(current)}
        assert old.keys()==fresh.keys()
        assert all(all(old[i][k]==fresh[i][k] for k in ('expected','group','split')) for i in old)
        changed=[i for i in old if old[i]['prediction']!=fresh[i]['prediction']]
        result[slug]=dict(n=len(old),changed_predictions=len(changed),changed_ids=sorted(changed),
            old_accuracy=sum(r['prediction']==r['expected'] for r in old.values())/len(old),
            new_accuracy=sum(r['prediction']==r['expected'] for r in fresh.values())/len(fresh))
    return dict(scope='Post hoc check of already registered p0 test replications; no extra GPU runs and no selection changes.',models=result)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for field in ('new','wildguard','qwen','out'):p.add_argument('--'+field,required=True)
    a=p.parse_args();result=compare(a.new,a.wildguard,a.qwen)
    with Path(a.out).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({m:v['changed_predictions'] for m,v in result['models'].items()}))
