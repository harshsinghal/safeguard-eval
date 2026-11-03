"""Missing development scores only, through the pinned HateXplain adapters."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import sys
import time

from evals.ensemble.common import ROOT, HX_POLICIES, read, rows, write, digest, now
from evals.hatexplain.orchestrate import server
from evals.hatexplain.policy import native_fields, payload
from evals.wildguard.run import post, score_ids, parse as specialist_parse
from evals.qwen_policy.run import parse as qwen_parse


def run(state,slug):
    state=Path(state); registration=read(state/'inference-registration.json'); manifest=read(state/'data-manifest.json')
    if registration['data_manifest_sha256']!=digest(state/'data-manifest.json'):
        raise ValueError('Development registration changed')
    for relative,expected in registration['sources'].items():
        if digest(ROOT/relative)!=expected:raise ValueError('Inference source changed: '+relative)
    for relative,expected in manifest['data_hashes'].items():
        if relative.startswith('data/') and digest(state/relative)!=expected:raise ValueError('Changed data')
    for slug,pid in [(slug,HX_POLICIES[slug])]:
        policy_path=state/'policies/hatexplain'/(pid+'.json');policy=read(policy_path)
        if digest(policy_path)!=manifest['policies']['hatexplain/'+slug]['sha256']:raise ValueError('Changed policy')
        spec=manifest['hx_models'][slug];adapter=spec['adapter'];model=spec['model']
        with server(slug,state) as checkpoint:
            native=None;category=None;ids=[];base='http://127.0.0.1:8000'
            if adapter=='policylm':
                sys.path.insert(0,str(Path(checkpoint)/'inference'))
                from policylm_infer import PolicyLM,Policy,Category
                native=PolicyLM.from_pretrained(checkpoint,device='cuda',dtype='bfloat16',max_batch_rows=1,max_chars=None)
                fields=native_fields(policy,'markdown');category=Policy([Category(policy['name'],**fields)])
                rendered=dict(name=policy['name'],fields=fields)
                check=repr(native.check_policy(category))
            else:
                check=None
                if adapter=='shieldstral':ids=score_ids(base,model,adapter)
                else:
                    for label in ('A','B',' A',' B'):
                        tok=post(base,'/tokenize',dict(model=model,prompt=label,add_special_tokens=False))['tokens']
                        if len(tok)==1:ids+=tok
                        elif label in ('A','B'):raise ValueError('Classification labels must be single tokens')
                    ids=sorted(set(ids))
                rendered=payload(model,adapter,policy,'markdown','[SUBMITTED POST]',ids)
            for split in ['canary','fit','validation']:
                out=state/'new-runs'/slug/split
                if out.exists():raise ValueError('Immutable run exists; do not overwrite')
                data=state/'data/hatexplain'/(split+'.jsonl');cases=rows(data)
                if len({r['id'] for r in cases})!=len(cases) or {r['split'] for r in cases}!={split}:raise ValueError('Bad development partition')
                out.mkdir(parents=True)
                write(out/'manifest.json',dict(created_utc=now(),model=model,slug=slug,revision=spec['revision'],adapter=adapter,
                    split=split,policy_id=pid,policy_sha256=digest(policy_path),dataset_sha256=digest(data),
                    registration_sha256=digest(state/'inference-registration.json'),settings=manifest['hx_settings'],
                    ids=[r['id'] for r in cases],native_check=check))
                write(out/'rendered-policy.json',rendered)
                def one(case):
                    r={k:v for k,v in case.items() if k!='prompt'};start=time.monotonic();response=None
                    request=dict(policy=rendered,content=case['prompt']) if native else payload(model,adapter,policy,'markdown',case['prompt'],ids)
                    r['request_sha256']=hashlib.sha256(json.dumps(request,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
                    try:
                        if native:
                            score=float(native.classify(case['prompt'],category).categories[policy['name']].score)
                            if not math.isfinite(score) or not 0<=score<=1:raise ValueError('Invalid score')
                            r.update(score=score,prediction='BLOCK' if score>=.5 else 'ALLOW');response=dict(score=score)
                        else:
                            response=post(base,'/v1/chat/completions',request)
                            r.update(qwen_parse(response) if adapter=='qwen' else specialist_parse(response,adapter))
                    except Exception as e:r.update(prediction='ERROR',error_type=type(e).__name__)
                    r['latency_seconds']=time.monotonic()-start
                    if response and 'usage' in response:r['usage']=response['usage']
                    return r,dict(id=case['id'],request=request,response=response)
                start=time.monotonic();done=[]
                with (out/'predictions.jsonl').open('x') as predictions,(out/'private-raw.jsonl').open('x') as traces:
                    with ThreadPoolExecutor(max_workers=1 if native else 32) as pool:
                        for r,trace in pool.map(one,cases):
                            done.append(r);predictions.write(json.dumps(r)+'\n');traces.write(json.dumps(trace,ensure_ascii=False)+'\n')
                summary=dict(n=len(done),errors=sum(r['prediction']=='ERROR' for r in done),wall_seconds=time.monotonic()-start,
                    predictions_sha256=digest(out/'predictions.jsonl'),raw_sha256=digest(out/'private-raw.jsonl'))
                write(out/'completion.json',summary)
                print(slug,split,summary,flush=True)
                if summary['errors']>max(2,.01*len(cases)):raise RuntimeError('Excess inference failures')
            if native:
                del native
                import gc,torch
                gc.collect();torch.cuda.empty_cache()
    print('ALL DEVELOPMENT INFERENCE COMPLETE',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--slug',required=True,choices=list(HX_POLICIES))
    run(**vars(p.parse_args()))
