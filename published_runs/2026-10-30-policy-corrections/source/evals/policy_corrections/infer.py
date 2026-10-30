"""Frozen native-interface label scores. No labels enter the model."""
import argparse
import json
from pathlib import Path
import time
from .common import (MODELS,POLICIES,read,rows,write,digest,now,sources,
                     check_registration,output_path)


class InputLimitError(ValueError):
    pass


class Scorer:
    def __init__(self,checkpoint,name):
        import torch
        from transformers import AutoTokenizer,Mistral3ForConditionalGeneration,Qwen3_5ForConditionalGeneration
        self.torch=torch;self.name=name
        self.tokenizer=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True)
        cls=Mistral3ForConditionalGeneration if name=='shieldstral' else Qwen3_5ForConditionalGeneration
        self.model=cls.from_pretrained(checkpoint,dtype=torch.bfloat16,local_files_only=True,
            attn_implementation='sdpa').to('cuda').eval().requires_grad_(False)
        self.base=self.model.model.language_model
        if any(p.requires_grad for p in self.model.parameters()):raise ValueError('Unfrozen model')
        pair=('yes','no') if name=='shieldstral' else ('B','A')
        ids=[self.tokenizer.encode(t,add_special_tokens=False) for t in pair]
        if any(len(x)!=1 for x in ids) or ids[0]==ids[1]:raise ValueError('Bad label tokens')
        self.ids=[x[0] for x in ids]

    def set_policy(self,policy):
        from evals.run import build_payload
        from evals.qwen_policy.run import render
        self.messages=(lambda text:build_payload('shieldstral',MODELS[self.name]['model'],policy,text)['messages']) if self.name=='shieldstral' else (
            lambda text:[dict(role='system',content=render(policy)),dict(role='user',content=text)])

    def inputs(self,text):
        kwargs={'enable_thinking':False} if self.name=='qwen' else {}
        messages=self.messages(text)
        rendered=self.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,**kwargs)
        encoded=self.tokenizer(rendered,add_special_tokens=False,return_tensors='pt')
        native=self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,**kwargs)
        if hasattr(native,'keys'):native=native['input_ids']
        if encoded['input_ids'][0].tolist()!=native:raise ValueError('Native tokenization mismatch')
        if encoded['input_ids'].shape[1]>8192:raise InputLimitError('No truncation permitted')
        return {k:v.to('cuda') for k,v in encoded.items()}

    def one(self,text,parity=False):
        torch=self.torch;enc=self.inputs(text)
        with torch.inference_mode():
            out=self.base(**enc,use_cache=False,output_hidden_states=False,return_dict=True)
            logits=self.model.lm_head(out.last_hidden_state[:,-1,:])[0]
            pair=logits[self.ids].float();score=float(pair.softmax(0)[0].cpu())
            delta=None
            if parity:
                full=self.model(**enc,use_cache=False,logits_to_keep=1,return_dict=True)
                other=float(full.logits[0,-1,self.ids].float().softmax(0)[0].cpu())
                delta=abs(score-other)
                if delta>.002:raise ValueError('Native score parity failed')
        return dict(score=score,margin=float((pair[0]-pair[1]).cpu()),top_token_id=int(logits.argmax().cpu()),
            top_token_is_label=int(logits.argmax().cpu()) in self.ids,
            tokens=int(enc['input_ids'].shape[1]),native_parity_difference=delta,
            outer_whitespace_trimmed=self.name=='qwen' and text!=text.strip())


def infer(state,model,stage):
    import torch
    from huggingface_hub import snapshot_download
    state=Path(state);check_registration(state);manifest=read(state/'data-manifest.json')
    if stage=='discovery-validation':
        if model!='shieldstral':raise ValueError('Only Shieldstral authors revisions')
        policies=POLICIES;splits=['discovery','validation']
    elif stage=='transfer-validation':
        if model!='qwen':raise ValueError('Only Qwen transfer')
        selection=read(state/'shield-selection.json')
        if selection['registration_sha256']!=digest(state/'registration.json'):raise ValueError('Selection registration changed')
        for p,h in selection['artifacts'].items():
            if digest(state/p)!=h:raise ValueError('Selection artifact changed')
        policies=['p0',selection['selected_revision']];splits=['validation']
    else:
        from .study import check_freeze
        f=check_freeze(state)
        policies=['p0',f['selected_revision']];splits=['holdout','test']
    spec=MODELS[model]
    ckpt=snapshot_download(spec['model'],revision=spec['revision'],ignore_patterns=['consolidated.safetensors','*.pt','*.pth'])
    engine=Scorer(ckpt,model)
    for policy in policies:
        engine.set_policy(read(state/'policies'/(policy+'.json')))
        for split in splits:
            dest=output_path(state,model,policy,split)
            if dest.exists():raise ValueError('Immutable output already exists')
            inp=state/'inputs'/(split+'.jsonl');meta=state/'metadata'/(split+'.jsonl.gz')
            rel=('sealed-inputs' if split in ('holdout','test') else 'inputs')+'/'+split+'.jsonl'
            if digest(inp)!=manifest['hashes'][rel] or digest(meta)!=manifest['hashes'][str(meta.relative_to(state))]:raise ValueError('Changed population')
            cases=rows(inp)
            if any(set(r)!={'id','prompt','prompt_sha256'} for r in cases):raise ValueError('Labels in inference input')
            result=[];start=time.monotonic();torch.cuda.reset_peak_memory_stats()
            for i,r in enumerate(cases):
                tick=time.monotonic()
                try:info=engine.one(r['prompt'],parity=stage!='final' and i<16)
                except InputLimitError:info=dict(score=None,error='InputLimitError')
                result.append(dict(id=r['id'],seconds=time.monotonic()-tick,**info))
                if (i+1)%256==0:print(json.dumps(dict(model=model,policy=policy,split=split,completed=i+1,total=len(cases),seconds=time.monotonic()-start)),flush=True)
            write(dest,dict(created_utc=now(),model=spec,policy_id=policy,policy_sha256=digest(state/'policies'/(policy+'.json')),
                split=split,ids=[r['id'] for r in cases],scores=[r['score'] for r in result],records=result,
                input_sha256=digest(inp),metadata_sha256=digest(meta),sources=sources(),
                registration_sha256=digest(state/'registration.json'),
                freeze_sha256=digest(state/'freeze.json') if stage=='final' else None,
                seconds=time.monotonic()-start,peak_gpu_bytes=torch.cuda.max_memory_allocated(),
                gpu=torch.cuda.get_device_name(),label_token_ids=engine.ids),exclusive=True)
            print('COMPLETE',model,policy,split,len(cases),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--model',choices=['shieldstral','qwen'],required=True)
    p.add_argument('--stage',choices=['discovery-validation','transfer-validation','final'],required=True)
    infer(**vars(p.parse_args()))
