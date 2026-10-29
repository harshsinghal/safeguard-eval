"""Thin, audited wrappers around the publishers' pinned decision heads."""
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import sys

from evals.decision_models.study import MODELS

MAX_LENGTH = 16384


def request(content, policy):
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Missing content')
    if policy['type'] != 'choice' or set(policy['criteria']) != {'ALLOW','BLOCK'}:
        raise ValueError('Expected binary moderation Choice')
    # Explicit allowlist: caller metadata and labels cannot enter the model input.
    return dict(state={'content':content}, questions={'moderation':{
        'type':'choice','instructions':policy['instructions'],
        'criteria':{k:policy['criteria'][k] for k in ('ALLOW','BLOCK')}}})


def parse(keys, logits, probabilities):
    if len(keys)!=2 or set(keys)!={'ALLOW','BLOCK'} or len(logits)!=2 or len(probabilities)!=2:
        raise ValueError('Unexpected decision-head dimensions')
    if not all(math.isfinite(x) for x in logits+probabilities):
        raise ValueError('Non-finite decision-head result')
    if min(probabilities)<0 or max(probabilities)>1 or abs(sum(probabilities)-1)>1e-5:
        raise ValueError('Invalid probabilities')
    p=dict(zip(keys,probabilities))
    # Native tie order is criteria insertion order (ALLOW first).
    pred=max(('ALLOW','BLOCK'),key=p.__getitem__)
    return dict(prediction=pred,score=p['BLOCK'],probabilities=p,logits=dict(zip(keys,logits)))


class Adapter:
    def __init__(self, slug, vendor):
        import torch
        from huggingface_hub import snapshot_download
        self.torch=torch; self.slug=slug; self.vendor=Path(vendor)
        hashes=json.loads(Path(__file__).with_name('vendor-hashes.json').read_text())
        for rel,expected in hashes.items():
            if hashlib.sha256((self.vendor/rel).read_bytes()).hexdigest()!=expected:
                raise ValueError('Unpinned vendor source: '+rel)
        conf=MODELS[slug]
        path=snapshot_download(conf['id'],revision=conf['revision'],
            allow_patterns=['*.json','*.safetensors','*.pt','*.txt','*.jinja','*.model'])
        self.path=path
        if slug=='kev':
            sys.path.insert(0,str(self.vendor/'kev'))
            from kev.api import SystemOneRequest,to_record
            from kev.checkpoint import Checkpoint,LoadOptions
            self.request_type=SystemOneRequest; self.to_record=to_record
            ck=Checkpoint(path)
            if ck.meta.base!=conf['base'] or ck.meta.base_revision!=conf['base_revision']:
                raise ValueError('Unregistered Kev base weights')
            self.tokenizer,self.model=ck.load('cuda',LoadOptions(dtype=torch.bfloat16,merge=True,
                attn='sdpa',backend='torch',fused=False,cuda_graphs=False))
            self.temperature=ck.meta.temperature
        else:
            source=self.vendor/'joint_schema_model.py'
            spec=importlib.util.spec_from_file_location('clef_native',source)
            self.module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=self.module
            spec.loader.exec_module(self.module)
            self.model,self.processor=self.module.load_release_model(path,device='cuda',dtype=torch.bfloat16,
                attn_implementation='sdpa')
            self.tokenizer=self.processor.tokenizer
            self.temperature=1.0
        self.model.eval()
        for p in self.model.parameters(): p.requires_grad_(False)
        torch.set_grad_enabled(False)

    def encode(self, content, policy):
        req=request(content,policy)
        if self.slug=='kev':
            record,meta=self.to_record(self.request_type.model_validate(req))
            enc=self.model.encode(self.tokenizer,record,max_state=MAX_LENGTH,max_branch=MAX_LENGTH,strict=True)
            if enc['state_truncated'] or len(enc['ids'])>MAX_LENGTH:
                raise ValueError('Context overflow; truncation prohibited')
            return enc,meta[0]['keys'],len(enc['ids'])
        # The native encoder clips silently. Encode at a ceiling above any input
        # first, then enforce our registered limit on the complete serialization.
        enc=self.module.encode_record(self.tokenizer,req,max_length=10**8,processor=self.processor)
        n=len(enc.input_ids)
        if n>MAX_LENGTH: raise ValueError(f'Context overflow: {n}>{MAX_LENGTH}')
        return enc,list(enc.questions[0].option_ids),n

    def forward(self, encs):
        torch=self.torch
        with torch.inference_mode():
            if self.slug=='kev': result=self.model.forward_batch([e[0] for e in encs])
            else:
                batch=self.module.collate_records([e[0] for e in encs],
                    pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,device='cuda')
                result=self.model(batch)
            out=[]
            for e,questions in zip(encs,result):
                if len(questions)!=1: raise ValueError('Unexpected question count')
                z=questions[0].float(); p=z.softmax(dim=-1)
                out.append(parse(e[1],z.cpu().tolist(),p.cpu().tolist()))
            if len(out)!=len(encs): raise ValueError('Incomplete batch')
            return out
