"""GPU actions. Training cannot read test data; test inference reads no labels."""
import argparse
import contextlib
import gc
import math
import random
import time
import numpy as np
import torch
from torch import nn
from .common import *


def seed_all(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def mean_pool(hidden, mask):
    weights = mask.unsqueeze(-1).to(torch.float32)
    return (hidden.float()*weights).sum(1)/weights.sum(1).clamp_min(1)


class Classifier(nn.Module):
    def __init__(self, backbone):
        super().__init__(); self.backbone = backbone
        self.dropout = nn.Dropout(.1)
        self.head = nn.Linear(backbone.config.hidden_size,1)
        nn.init.normal_(self.head.weight,std=.02); nn.init.zeros_(self.head.bias)

    def forward(self, input_ids, attention_mask, features=False):
        hidden = self.backbone(input_ids=input_ids,attention_mask=attention_mask,
                               use_cache=False,return_dict=True).last_hidden_state
        pooled = mean_pool(hidden,attention_mask)
        return pooled if features else self.head(self.dropout(pooled)).squeeze(-1).float()


def load_model(seed=SEEDS[0]):
    from transformers import AutoModelForMaskedLM
    seed_all(seed)
    mlm = AutoModelForMaskedLM.from_pretrained(MODEL,revision=REVISION,
        trust_remote_code=True,dtype=torch.float32,attn_implementation='sdpa')
    body = mlm.lfm2
    model = Classifier(body).cuda(); del mlm
    if not all(p.requires_grad for p in model.parameters()):
        raise ValueError('Unexpected frozen parameter')
    return model


def tokenize(state, split):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL,revision=REVISION,trust_remote_code=True)
    tok.padding_side = 'right'; tok.truncation_side = 'right'
    data = load_inputs(state,split)
    encoded=[]; lengths=[]
    for r in data:
        ids=tok(r['prompt'],add_special_tokens=True,truncation=False)['input_ids']
        if not ids:
            raise ValueError('Tokenizer returned an empty sequence')
        lengths.append(len(ids));encoded.append(ids[:MAX_LENGTH])
    report=dict(n=len(data),ids=[r['id'] for r in data],max_length=MAX_LENGTH,
        truncated=int(sum(n>MAX_LENGTH for n in lengths)),original_max=max(lengths),
        quantiles=np.quantile(lengths,[0,.5,.9,.95,.99,1]).tolist(),
        token_count_before=sum(lengths),token_count_after=sum(map(len,encoded)),
        input_sha256=digest(Path(state)/'inputs'/(split+'.jsonl')))
    return tok,encoded,report


def batch(tok, encoded, indices):
    return {k:v.cuda() for k,v in tok.pad(
        [{'input_ids':encoded[int(i)],'attention_mask':[1]*len(encoded[int(i)])} for i in indices],
        padding=True,return_tensors='pt').items() if k in ['input_ids','attention_mask']}


def optimizer_for(model, rate):
    decay=[]; nodecay=[]
    for name,p in model.named_parameters():
        (nodecay if p.ndim<2 or name.endswith('bias') or 'norm' in name else decay).append(p)
    if len({id(p) for p in decay+nodecay}) != len(list(model.parameters())):
        raise ValueError('Not all parameters are in the optimizer')
    return torch.optim.AdamW([dict(params=decay,weight_decay=.01),
                              dict(params=nodecay,weight_decay=0.)],lr=rate)


def infer(model,tok,encoded,features=False):
    model.eval(); order=sorted(range(len(encoded)),key=lambda i:(len(encoded[i]),i))
    output=np.zeros((len(encoded),1024) if features else (len(encoded),),dtype=np.float32)
    start=time.monotonic()
    with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16):
        for begin in range(0,len(order),8):
            ids=order[begin:begin+8]
            values=model(**batch(tok,encoded,ids),features=features)
            if not features:values=torch.sigmoid(values)
            output[ids]=values.float().cpu().numpy()
    torch.cuda.synchronize()
    if not np.isfinite(output).all():raise ValueError('Nonfinite model output')
    return output,time.monotonic()-start


def smoke(state):
    state=Path(state);check_registration(state)
    tok,x,report=tokenize(state,'fit');model=load_model();opt=optimizer_for(model,RATES[0])
    y=labels(aligned_metadata(state,'fit',report['ids']))
    order=np.random.default_rng(SEEDS[0]).permutation(len(x))
    times=[];memory=[]
    tests=[order[i:i+8].tolist() for i in range(0,80,8)]
    tests.append([max(range(len(x)),key=lambda i:len(x[i]))]+order[:7].tolist())
    for indices in tests:
        model.train();opt.zero_grad(set_to_none=True);torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize();start=time.monotonic()
        with torch.autocast('cuda',dtype=torch.bfloat16):
            logits=model(**batch(tok,x,indices))
            loss=nn.functional.binary_cross_entropy_with_logits(logits,torch.as_tensor(y[indices],device='cuda',dtype=torch.float32))
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True);opt.step()
        torch.cuda.synchronize();times.append(time.monotonic()-start)
        memory.append(torch.cuda.max_memory_allocated())
    estimate=float(np.mean(times[2:10]))*512*3*6
    write(state/'smoke.json',dict(created_utc=now(),fit_tokenization=report,seconds=times,
        peak_allocated_bytes=memory,estimated_microbatch_training_seconds=estimate,
        estimate_excludes_validation_checkpointing_and_setup=True,parameter_count=sum(p.numel() for p in model.parameters())))
    print('SMOKE',dict(estimated_training_seconds=round(estimate),peak_gb=round(max(memory)/1e9,2)),flush=True)
    if estimate>5400:raise RuntimeError('Training estimate exceeds bounded run; stop before bulk fitting')


def extract(state):
    state=Path(state);check_registration(state)
    if (state/'freeze.json').exists():raise ValueError('Frozen study')
    model=load_model()
    for split in ['fit','validation']:
        tok,x,report=tokenize(state,split)
        aligned_metadata(state,split,report['ids'])
        features,seconds=infer(model,tok,x,features=True)
        folder=state/'features'/split;folder.mkdir(parents=True,exist_ok=False)
        np.save(folder/'features.npy',features,allow_pickle=False)
        write(folder/'manifest.json',dict(**report,seconds=seconds,features_sha256=digest(folder/'features.npy')))
        print('EXTRACTED',split,len(x),round(seconds,2),flush=True)


def train(state,rate,seed):
    state=Path(state);check_registration(state)
    if (state/'freeze.json').exists():raise ValueError('Frozen study')
    if rate not in RATES or seed not in SEEDS:raise ValueError('Unregistered training configuration')
    folder=state/'fits'/f'ft-lr{rate:g}-s{seed}';folder.mkdir(parents=True,exist_ok=False)
    tok,x,tr=tokenize(state,'fit');_,xv,vr=tokenize(state,'validation')
    y=labels(aligned_metadata(state,'fit',tr['ids']));aligned_metadata(state,'validation',vr['ids'])
    model=load_model(seed);opt=optimizer_for(model,rate)
    steps=math.ceil(len(x)/32)*EPOCHS;warmup=math.ceil(steps*.1)
    schedule=torch.optim.lr_scheduler.LambdaLR(opt,
        lambda step:step/warmup if step<warmup else max(0.,(steps-step)/(steps-warmup)))
    # Samples from early and late encoder blocks prove the backbone actually moved.
    names=[n for n,_ in model.named_parameters() if n.startswith('backbone.layers.') and n.endswith('weight')]
    tracked=[names[0],names[-1],'head.weight'];paramdict=dict(model.named_parameters())
    initial={n:paramdict[n].detach().cpu().clone() for n in tracked}
    generator=torch.Generator().manual_seed(seed);history=[];start=time.monotonic();step=0
    for epoch in range(1,EPOCHS+1):
        model.train();order=torch.randperm(len(x),generator=generator).tolist();losses=[]
        opt.zero_grad(set_to_none=True)
        for begin in range(0,len(order),8):
            indices=order[begin:begin+8]
            # Each accumulation window receives an equal per-example loss.
            window_start=(begin//32)*32;window_n=min(32,len(order)-window_start)
            with torch.autocast('cuda',dtype=torch.bfloat16):
                logits=model(**batch(tok,x,indices))
                loss=nn.functional.binary_cross_entropy_with_logits(logits,
                    torch.as_tensor(y[indices],device='cuda',dtype=torch.float32))
            if not torch.isfinite(loss):raise ValueError('Nonfinite fitting loss')
            (loss*len(indices)/window_n).backward();losses.append(float(loss.detach()))
            if (begin+len(indices))%32==0 or begin+len(indices)==len(order):
                torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
                opt.step();schedule.step();opt.zero_grad(set_to_none=True);step+=1
        s,seconds=infer(model,tok,xv)
        path=folder/f'epoch-{epoch}.pt'
        torch.save({k:v.detach().cpu() for k,v in model.state_dict().items()},path)
        changes={n:float(torch.linalg.vector_norm(paramdict[n].detach().cpu()-initial[n])) for n in tracked}
        if not all(v>0 and math.isfinite(v) for v in changes.values()):raise ValueError('Weights did not change')
        row=dict(epoch=epoch,steps=step,mean_fit_batch_loss=float(np.mean(losses)),
            validation_scores=s.tolist(),checkpoint=str(path.relative_to(state)),checkpoint_sha256=digest(path),
            encoder_and_head_delta_l2=changes,validation_seconds=seconds,elapsed_seconds=time.monotonic()-start)
        history.append(row);write(folder/'history.json',dict(rate=rate,seed=seed,epochs=history,
            fit_tokenization=tr,validation_tokenization=vr,parameter_count=sum(p.numel() for p in model.parameters()),
            trainable_parameter_count=sum(p.numel() for p in model.parameters() if p.requires_grad)))
        print('TRAINED',rate,seed,epoch,'loss',round(row['mean_fit_batch_loss'],5),'seconds',round(row['elapsed_seconds'],1),flush=True)


def test_inference(state):
    state=Path(state);f=check_freeze(state,checkpoints=True);check_registration(state,test=True)
    folder=state/'test-output';folder.mkdir(parents=True,exist_ok=False)
    tok,x,report=tokenize(state,'test');model=load_model()
    features,seconds=infer(model,tok,x,features=True)
    np.save(folder/'frozen-features.npy',features,allow_pickle=False)
    out=dict(tokenization=report,frozen_feature_seconds=seconds,
             frozen_feature_sha256=digest(folder/'frozen-features.npy'),checkpoints={})
    # Re-run validation after loading weights, before each checkpoint's test pass.
    _,xv,_=tokenize(state,'validation')
    for path,h in sorted(f['selected_checkpoints'].items()):
        params=torch.load(state/path,map_location='cpu',weights_only=True)
        model.load_state_dict(params,strict=True);del params
        sv,_=infer(model,tok,xv)
        original=read(state/Path(path).parent/'history.json')
        expected=next(r['validation_scores'] for r in original['epochs'] if r['checkpoint']==path)
        max_error=float(np.max(np.abs(sv-np.asarray(expected))))
        if max_error>1e-6:raise ValueError('Reloaded checkpoint differs from validation predictions')
        s,seconds=infer(model,tok,x)
        out['checkpoints'][path]=dict(sha256=h,scores=s.tolist(),seconds=seconds,
                                     validation_reload_max_abs_error=max_error)
        write(folder/'scores-progress.json',out)
        print('TEST INFERENCE',path,round(seconds,2),flush=True)
    write(folder/'scores.json',out,exclusive=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['smoke','extract','train','test_inference'])
    p.add_argument('--state',required=True);p.add_argument('--rate',type=float);p.add_argument('--seed',type=int)
    a=p.parse_args()
    if not torch.cuda.is_available():raise RuntimeError('This registered runtime requires CUDA')
    torch.set_num_threads(4)
    if a.action=='train':train(a.state,a.rate,a.seed)
    else:globals()[a.action](a.state)
