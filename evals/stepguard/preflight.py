"""Use native tokenization/rendering without weights or reference answers."""
import argparse
from collections import Counter
import importlib.util
import sys
from .common import *
from .policies import save
from .requests import safeguard_payload, jev_payload


def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


class CounterEngine:
    def __init__(self, state, model, vendor):
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer
        self.model=model
        if model=='jev':
            return
        spec=MODELS[model]
        path=Path(snapshot_download(spec['model'],revision=spec['revision'],token=False,
            allow_patterns=['tokenizer*','tokenizer/*','*.jinja','config.json','threshold_manifest.json','inference/*.py','inference/bidirlm/*']))
        self.tok=AutoTokenizer.from_pretrained(path/'tokenizer' if model=='policylm' else path,trust_remote_code=False)
        self.tok.truncation_side='right'
        if model=='policylm':
            self.module=load_module('stepguard_policy_count', path/'inference/policylm_infer.py')
            self.helper=self.module.PolicyLM._from_components(None,self.tok,read(path/'config.json'),read(path/'threshold_manifest.json'))
        elif model=='kev':
            sys.path.insert(0,str(Path(vendor)/'kev'))
            from kev.api import SystemOneRequest, to_record
            from kev.model import encode
            self.request_type=SystemOneRequest;self.to_record=to_record;self.encode_native=encode
        elif model=='clef':
            self.module=load_module('stepguard_clef_count', Path(vendor)/'joint_schema_model.py')
        write(Path(state)/f'tokenizers/{model}-manifest.json',dict(model=spec,
            files={str(p.relative_to(path)):digest(p) for p in path.rglob('*')
                if p.is_file() and p.suffix in ('.json','.jinja','.py','.model','.txt')
                and ('tokenizer' in str(p.relative_to(path)) or p.name in ('config.json','threshold_manifest.json')
                     or str(p.relative_to(path)).startswith('inference/'))}))

    def count(self, content, policy):
        if self.model=='jev':
            body=jev_payload(content,policy)
            return dict(tokens=None,bytes=len(canonical(body).encode()),eligible=True)
        if self.model=='policylm':
            m=self.module
            p=m.Policy([m.Category(policy['name'],violation_rule=policy['block'],not_violation_rule=policy['allow'],exception_override=policy['precedence'])])
            compiled=self.helper._compile(p)
            variants=m.text_variants(content)
            sizes=[self.helper._windows(v,compiled.calls[0].budget) for v in variants]
            windows=max(map(len,sizes))
            n=max(len(compiled.calls[0].prefix)+len(w[2]) for spans in sizes for w in spans)
            return dict(tokens=n,windows=windows,variants=len(variants),cleaned=variants[0]!=content or len(variants)>1,
                eligible=windows==1 and len(variants)==1,policy_tokens=compiled.report.tokens)
        if self.model in ('kev','clef'):
            from evals.decision_models.adapters import request
            req=request(content,policy)
            if self.model=='kev':
                rec,meta=self.to_record(self.request_type.model_validate(req))
                enc=self.encode_native(self.tok,rec,max_state=10**8,max_branch=10**8,strict=True)
                n=len(enc['ids'])
            else:
                enc=self.module.encode_record(self.tok,req,max_length=10**8)
                n=len(enc.input_ids)
        else:
            if self.model=='shieldstral':
                from evals.run import build_payload
                messages=build_payload('shieldstral',MODELS[self.model]['model'],policy,content)['messages']
                kwargs={}
            else:
                messages=safeguard_payload(content,policy)['messages'];kwargs={'reasoning_effort':'medium'}
            enc=self.tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,**kwargs)
            n=len(enc['input_ids'] if hasattr(enc,'keys') else enc)
        return dict(tokens=n,eligible=n<=16384)


def run(state,vendor,models=None):
    state=Path(state)
    if (state/'registration.json').exists():raise ValueError('Already registered')
    from evals.decision_models.fetch_sources import fetch
    fetch(vendor);save(state)
    all_rows=[r for t in TASKS for s in SPLITS for r in data(state,t,s)]
    fits={};summary={};lengths=[];policy_lengths={}
    relevant=('common.py','preflight.py','policies.py','requests.py','adapters.py','run.py','native.py','vendor-hashes.json')
    signature=hash_value(dict(sources={p:h for p,h in sources().items() if Path(p).name in relevant},
        rows=[r['prompt_sha256'] for r in all_rows]))
    for model in models or MODEL_NAMES:
        engine=CounterEngine(state,model,vendor);fits[model]=set();summary[model]={};policy_lengths[model]={}
        for task in TASKS:
            catalog=read(state/f'policies/{task}/{model}.json')
            policy_lengths[model][task]={pid:engine.count('{}',p).get('policy_tokens',engine.count('{}',p)['tokens']) for pid,p in catalog.items()}
            rr=[r for r in all_rows if r['task']==task];counts=[];errors=Counter()
            for r in rr:
                values={};valid=True
                for pid,p in catalog.items():
                    try:
                        value=engine.count(r['prompt'],p)
                    except ValueError as exc:
                        value=dict(eligible=False,error_type=type(exc).__name__);errors[str(exc)]+=1
                    values[pid]=value;valid=valid and value['eligible']
                if valid:fits[model].add(r['id'])
                counts.extend(v['tokens'] for v in values.values() if v.get('tokens') is not None)
                lengths.append(dict(id=r['id'],task=task,model=model,candidates=values))
            summary[model][task]=dict(n=len(rr),eligible=sum(r['id'] in fits[model] for r in rr),
                max_tokens=max(counts) if counts else None,errors=dict(errors))
        print(canonical(dict(model=model,coverage=summary[model])),flush=True)
        write(state/f'preflight/{model}.json',dict(signature=signature,fit=sorted(fits[model]),summary=summary[model],
            policy_lengths=policy_lengths[model],lengths=[r for r in lengths if r['model']==model]))
    if not all((state/f'preflight/{m}.json').exists() for m in MODEL_NAMES):return
    lengths=[]
    for model in MODEL_NAMES:
        saved=read(state/f'preflight/{model}.json')
        if saved['signature']!=signature:raise ValueError('Stale preflight cache')
        fits[model]=set(saved['fit']);summary[model]=saved['summary'];policy_lengths[model]=saved['policy_lengths'];lengths.extend(saved['lengths'])
    primary=set.intersection(*(fits[m] for m in PRIMARY));short=primary & fits['policylm']
    write(state/'eligibility.json',dict(primary=sorted(primary),policylm=sorted(short),
        model_eligible={m:sorted(ids) for m,ids in fits.items()}))
    jsonl(state/'input-lengths.jsonl',lengths)
    write(state/'policy-token-lengths.json',policy_lengths)
    write(state/'context-audit.json',dict(created_utc=now(),models=summary,primary_n=len(primary),short_n=len(short),
        by_task_split={t:{s:dict(total=len(data(state,t,s)),primary=sum(r['id'] in primary for r in data(state,t,s)),
            short=sum(r['id'] in short for r in data(state,t,s))) for s in SPLITS} for t in TASKS},
        policy_selection_note='Jev tie lengths use reported input_tokens on the lexically first common validation ID; native tokenizer is not public.',
        conditions='Complete input and every registered policy must fit; no clipping. PolicyLM must use one native window and one cleaning variant.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--vendor',required=True)
    p.add_argument('--models',nargs='+',choices=MODEL_NAMES)
    run(**vars(p.parse_args()))
