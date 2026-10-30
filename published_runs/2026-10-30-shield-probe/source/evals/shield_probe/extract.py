"""Extract pinned frozen-model features; labels are never read by an encoder."""
import argparse
import json
from pathlib import Path
import sys
import time
import warnings
import numpy as np
from .common import (MODELS, keys, read, rows, write, digest, now, source_hashes,
                     content_mask)


class InputLimitError(ValueError):
    """A documented input limit; retain the case as unresolved."""


class Extractor:
    def __init__(self, checkpoint, policy, model):
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, Mistral3ForConditionalGeneration
        from evals.qwen_policy.run import render
        from evals.run import build_payload
        self.torch=torch;self.name=model;self.spec=MODELS[model]
        self.tokenizer=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True)
        cls=Qwen3_5ForConditionalGeneration if model=='qwen' else Mistral3ForConditionalGeneration
        self.model=cls.from_pretrained(checkpoint,dtype=torch.bfloat16,local_files_only=True,
                                      attn_implementation='sdpa').to('cuda').eval().requires_grad_(False)
        self.base=self.model.model.language_model
        if any(p.requires_grad for p in self.model.parameters()):raise ValueError('Unfrozen backbone')
        sentinel='__SAFEGUARD_PROBE_CONTENT_4f8e12__'
        if model=='qwen':
            self.messages=lambda text:[dict(role='system',content=render(policy)),dict(role='user',content=text)]
            self.serialize=lambda text:text.strip()
            self.template_kwargs={'enable_thinking':False}
            positive,negative='B','A'
        else:
            self.messages=lambda text:build_payload('shieldstral',self.spec['model'],policy,text)['messages']
            self.serialize=lambda text:json.dumps(text,ensure_ascii=False)
            self.template_kwargs={}
            positive,negative='yes','no'
        rendered=self.tokenizer.apply_chat_template(self.messages(sentinel),tokenize=False,
                        add_generation_prompt=True,**self.template_kwargs)
        target=self.serialize(sentinel)
        if rendered.count(target)!=1:raise ValueError('Ambiguous serialized content span')
        self.prefix,self.suffix=rendered.split(target)
        ids=[self.tokenizer.encode(t,add_special_tokens=False) for t in (positive,negative)]
        if any(len(t)!=1 for t in ids) or ids[0]==ids[1]:raise ValueError('Canonical labels must be distinct single tokens')
        self.label_ids=[t[0] for t in ids]

    def inputs(self,text):
        serial=self.serialize(text);rendered=self.prefix+serial+self.suffix
        expected=self.tokenizer.apply_chat_template(self.messages(text),tokenize=False,
                          add_generation_prompt=True,**self.template_kwargs)
        if rendered!=expected:raise ValueError('Content assembly differs from native chat template')
        enc=self.tokenizer(rendered,add_special_tokens=False,return_offsets_mapping=True,return_tensors='pt')
        mask=content_mask(enc.pop('offset_mapping')[0].tolist(),len(self.prefix),len(self.prefix)+len(serial))
        if not mask.any() and serial:raise ValueError('Empty content mask for nonempty text')
        ids=self.tokenizer.apply_chat_template(self.messages(text),tokenize=True,
                      add_generation_prompt=True,**self.template_kwargs)
        if hasattr(ids,'keys'):ids=ids['input_ids']
        if enc['input_ids'][0].tolist()!=ids:raise ValueError('Tokenization differs from native template')
        if enc['input_ids'].shape[1]>8192:raise InputLimitError('Token limit; no truncation')
        return {k:v.to('cuda') for k,v in enc.items()},mask

    def score(self,logits):
        return float(self.torch.softmax(logits[self.label_ids].float(),dim=0)[0].cpu())

    def one(self,text):
        torch=self.torch;enc,mask=self.inputs(text)
        with torch.inference_mode():
            out=self.base(**enc,use_cache=False,output_hidden_states=True,return_dict=True)
            logits=self.model.lm_head(out.last_hidden_state[:,-1,:])[0]
        depth=self.spec['layers'][-1]
        if len(out.hidden_states)!=depth+1 or not torch.equal(out.hidden_states[-1],out.last_hidden_state):
            raise ValueError('Unexpected hidden-state indexing or final normalization')
        mm=torch.as_tensor(mask,device='cuda');features={}
        for layer in self.spec['layers']:
            h=out.hidden_states[layer][0].float()
            features[f'{self.name}-l{layer}-mean']=(h[mm].mean(0) if mask.any() else torch.zeros_like(h[0])).cpu().numpy()
            features[f'{self.name}-l{layer}-last']=h[-1].cpu().numpy()
        pair=logits[self.label_ids].float();top=int(logits.argmax().cpu())
        return features,dict(native_score=self.score(logits),native_margin=float((pair[0]-pair[1]).cpu()),
            positive_token_id=self.label_ids[0],negative_token_id=self.label_ids[1],
            top_token_id=top,top_token_is_label=top in self.label_ids,
            tokens=int(enc['input_ids'].shape[1]),content_tokens=int(mask.sum()),windows=1,empty_content=not bool(self.serialize(text)),outer_whitespace_trimmed=self.name=='qwen' and text!=text.strip())

    def parity(self,texts):
        diffs=[]
        for text in texts:
            _,info=self.one(text);enc,_=self.inputs(text)
            with self.torch.inference_mode():
                output=self.model(**enc,use_cache=False,logits_to_keep=1,return_dict=True)
            diffs.append(abs(info['native_score']-self.score(output.logits[0,-1])))
        if max(diffs,default=0)>0.002:raise ValueError('Head extraction differs from full native forward')
        return dict(n=len(texts),max_absolute_difference=max(diffs,default=0),tolerance=.002,
                    label_token_ids=self.label_ids,tokenizer_class=type(self.tokenizer).__name__,
                    model_class=type(self.model).__name__)


def extract(state, model, stage):
    import torch
    from huggingface_hub import snapshot_download
    state = Path(state); manifest = read(state/'data-manifest.json')
    if digest(state/'policy.json') != manifest['policy_sha256']:
        raise ValueError('Policy changed')
    registration = read(state/'registration.json')
    if registration['sources'] != source_hashes():
        raise ValueError('Extraction code changed after registration')
    if stage == 'test':
        freeze = read(state/'freeze.json')
        if freeze['sources'] != source_hashes() or freeze['data_manifest_sha256'] != digest(state/'data-manifest.json'):
            raise ValueError('No valid pre-test freeze')
    spec = MODELS[model]
    checkpoint = snapshot_download(spec['model'],revision=spec['revision'],ignore_patterns=['consolidated.safetensors','*.pt','*.pth'])
    policy = read(state/'policy.json')
    engine = Extractor(checkpoint,policy,model)
    splitnames = ['fit','validation'] if stage=='development' else ['test']
    for split in splitnames:
        folder = state/'features'/model/split
        if (folder/'manifest.json').exists():
            raise ValueError('Immutable feature extraction exists')
        inp = state/'inputs'/(split+'.jsonl')
        meta_path = state/'metadata'/(split+'.jsonl.gz')
        for path in (inp,meta_path):
            if digest(path) != manifest['hashes'][str(path.relative_to(state))]:
                raise ValueError('Input or metadata changed')
        # Encoder input is explicitly label-free. Metadata is only hashed, not parsed.
        cases = rows(inp)
        if any(set(r) != {'id','prompt','prompt_sha256'} for r in cases):
            raise ValueError('Unexpected encoder input fields')
        folder.mkdir(parents=True,exist_ok=True)
        arrays = {k:np.full((len(cases),spec['width']),np.nan,dtype=np.float32) for k in keys(model)}
        records=[]; valid=[]; start=time.monotonic()
        if split=='fit':
            write(folder/'parity.json',engine.parity([r['prompt'] for r in cases[:16]]))
        torch.cuda.reset_peak_memory_stats()
        # Fail closed on an implementation failure; no wholesale silent ERROR population.
        for i,case in enumerate(cases):
            tick=time.monotonic()
            try:
                features, info = engine.one(case['prompt'])
            except InputLimitError:
                valid.append(False)
                records.append(dict(id=case['id'],seconds=time.monotonic()-tick,
                                    error='InputLimitError',native_score=None))
                continue
            if set(features) != set(arrays):
                raise ValueError('Missing representation')
            for k,a in features.items():
                if a.shape!=(spec['width'],) or not np.isfinite(a).all():
                    raise ValueError('Nonfinite or wrong-shaped representation')
                arrays[k][i]=a
            valid.append(True)
            records.append(dict(id=case['id'],seconds=time.monotonic()-tick,**info))
            if (i+1)%128==0:
                print(json.dumps(dict(model=model,split=split,completed=i+1,total=len(cases),
                                      seconds=time.monotonic()-start)),flush=True)
        for k,a in arrays.items():
            np.save(folder/(k+'.npy'),a,allow_pickle=False)
        write(folder/'records.json',records)
        artifacts={p.name:digest(p) for p in sorted(folder.iterdir()) if p.is_file()}
        write(folder/'manifest.json',dict(created_utc=now(),model=spec,split=split,
            ids=[r['id'] for r in cases],valid=valid,artifacts=artifacts,
            metadata_sha256=digest(meta_path),input_sha256=digest(inp),
            policy_sha256=digest(state/'policy.json'),sources=source_hashes(),
            seconds=time.monotonic()-start,peak_gpu_bytes=torch.cuda.max_memory_allocated(),
            checkpoint_files={str(p.relative_to(checkpoint)):digest(p) for p in sorted(Path(checkpoint).rglob('*'))
                              if p.is_file() and p.suffix in ('.json','.py','.safetensors')},
            torch_version=torch.__version__,gpu=torch.cuda.get_device_name(),
            freeze_sha256=digest(state/'freeze.json') if stage=='test' else None),exclusive=True)
        print(json.dumps(dict(model=model,split=split,complete=len(cases),seconds=time.monotonic()-start)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True)
    p.add_argument('--model',choices=list(MODELS),required=True)
    p.add_argument('--stage',choices=['development','test'],required=True)
    extract(**vars(p.parse_args()))
