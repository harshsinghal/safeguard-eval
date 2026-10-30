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


class QwenExtractor:
    def __init__(self, checkpoint, policy):
        import torch
        from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
        from evals.qwen_policy.run import render
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(checkpoint, local_files_only=True)
        model = Qwen3_5ForConditionalGeneration.from_pretrained(
            checkpoint, dtype=torch.bfloat16, local_files_only=True,
            attn_implementation='sdpa').to('cuda').eval().requires_grad_(False)
        self.model = model
        self.base = model.model.language_model
        sentinel = '__SAFEGUARD_PROBE_CONTENT_4f8e12__'
        rendered = self.tokenizer.apply_chat_template(
            [dict(role='system',content=render(policy)),dict(role='user',content=sentinel)],
            tokenize=False, add_generation_prompt=True, enable_thinking=False)
        if rendered.count(sentinel) != 1:
            raise ValueError('Ambiguous content span')
        self.prefix, self.suffix = rendered.split(sentinel)

    def one(self, text):
        torch = self.torch
        rendered = self.prefix+text+self.suffix
        enc = self.tokenizer(rendered, add_special_tokens=False, return_offsets_mapping=True,
                             return_tensors='pt')
        mask = content_mask(enc.pop('offset_mapping')[0].tolist(),len(self.prefix),len(self.prefix)+len(text))
        if not mask.any():
            raise ValueError('Empty content token mask')
        length = enc['input_ids'].shape[1]
        if length > 8192:
            raise InputLimitError('Registered token limit exceeded; no truncation')
        with torch.inference_mode():
            out = self.base(**{k:v.to('cuda') for k,v in enc.items()}, use_cache=False,
                            output_hidden_states=True, return_dict=True)
        if len(out.hidden_states) != 25 or not torch.equal(out.hidden_states[-1],out.last_hidden_state):
            raise ValueError('Unexpected hidden-state indexing or final normalization')
        mm = torch.as_tensor(mask, device='cuda')
        feature = {}
        for layer in MODELS['qwen']['layers']:
            h = out.hidden_states[layer][0].float()
            feature[f'qwen-l{layer}-mean'] = h[mm].mean(0).cpu().numpy()
            feature[f'qwen-l{layer}-last'] = h[-1].cpu().numpy()
        return feature, dict(tokens=length,content_tokens=int(mask.sum()),windows=1)


class PolicyExtractor:
    def __init__(self, checkpoint, policy):
        import torch
        sys.path.insert(0,str(Path(checkpoint)/'inference'))
        from policylm_infer import PolicyLM, Policy, Category
        self.torch = torch
        self.native = PolicyLM.from_pretrained(checkpoint,device='cuda',dtype='bfloat16',
                                               max_batch_rows=1,max_chars=None)
        self.native.model.eval().requires_grad_(False)
        self.name = policy['name']
        self.policy = Policy([Category(self.name,violation_rule=policy['block'],
            not_violation_rule=policy['allow'],exception_override=policy['precedence'])])
        self.native.check_policy(self.policy)
        compiled = self.native._compile(self.policy)
        if len(compiled.calls) != 1:
            raise ValueError('Expected one explicit policy category')
        self.prefix_length = len(compiled.calls[0].prefix)
        self.active = True
        self.captured = []
        self.native.model.base.register_forward_pre_hook(self.pre, with_kwargs=True)
        self.native.model.base.register_forward_hook(self.post, with_kwargs=True)

    def pre(self, module, args, kwargs):
        if self.active:
            kwargs['output_hidden_states'] = True
        return args, kwargs

    def post(self, module, args, kwargs, out):
        if not self.active:
            return
        torch = self.torch
        ids = kwargs['input_ids']
        if ids.shape[0] != 1 or len(out.hidden_states) != 29:
            raise ValueError('Changed native batching or depth')
        if out.last_hidden_state.shape[:2] != ids.shape or not torch.equal(out.hidden_states[-1],out.last_hidden_state):
            raise ValueError('Native hidden-state alignment changed')
        slot = (ids[0] == self.native.model.label_token_id)
        if int(slot.sum()) != 1:
            raise ValueError('Expected exactly one category slot')
        attention = kwargs['attention_mask'][0].bool()
        content = attention.clone(); content[:self.prefix_length] = False
        if not content.any():
            raise ValueError('Empty native content')
        features = {}
        for layer in MODELS['policylm']['layers']:
            h = out.hidden_states[layer][0].float()
            features[f'policylm-l{layer}-slot'] = h[slot][0].cpu().numpy()
            features[f'policylm-l{layer}-mean'] = h[content].mean(0).cpu().numpy()
        self.captured.append((features,int(attention.sum()),int(content.sum())))

    def one(self, text):
        self.captured = []
        with self.torch.inference_mode():
            result = self.native.classify(text,self.policy)
        if not self.captured:
            raise ValueError('No hidden states captured')
        feats = {k:np.stack([f[k] for f,_,_ in self.captured]).mean(0) for k in keys('policylm')}
        return feats, dict(native_score=float(result.categories[self.name].score),
            windows=len(self.captured),tokens=sum(t for _,t,_ in self.captured),
            content_tokens=sum(t for _,_,t in self.captured),variants=result.variants,cleaned=result.cleaned)

    def parity(self, texts):
        diffs = []
        for text in texts:
            _, info = self.one(text)
            self.active = False
            try:
                with self.torch.inference_mode():
                    native = float(self.native.classify(text,self.policy).categories[self.name].score)
            finally:
                self.active = True
            diffs.append(abs(native-info['native_score']))
        if max(diffs,default=0) > 1e-6:
            raise ValueError('Extraction changes native scores')
        return dict(n=len(diffs),max_absolute_difference=max(diffs,default=0),tolerance=1e-6)


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
    checkpoint = snapshot_download(spec['model'],revision=spec['revision'])
    policy = read(state/'policy.json')
    engine = QwenExtractor(checkpoint,policy) if model == 'qwen' else PolicyExtractor(checkpoint,policy)
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
        if model=='policylm' and split=='fit':
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
