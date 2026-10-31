"""Label-blind frozen feature extraction; no head fitting or test metrics."""
import argparse
import time
import json
from .common import *

def modernbert(checkpoint, cases):
    import torch
    from transformers import AutoModel, AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(checkpoint,local_files_only=True)
    model=AutoModel.from_pretrained(checkpoint,local_files_only=True,torch_dtype=torch.bfloat16,
        attn_implementation='sdpa').to('cuda').eval().requires_grad_(False)
    features=np.zeros((len(cases),768),dtype=np.float32);counts=np.zeros(len(cases),dtype=np.int64)
    windows=[];records=[]
    for i,case in enumerate(cases):
        ids=tokenizer(case['prompt'],add_special_tokens=False,truncation=False)['input_ids']
        records.append(dict(id=case['id'],content_tokens=len(ids),windows=(len(ids)+8189)//8190,empty=not bool(ids)))
        for start in range(0,len(ids),8190):
            chunk=ids[start:start+8190]
            enc=tokenizer.prepare_for_model(chunk,add_special_tokens=True,return_special_tokens_mask=True,
                                            return_attention_mask=True,truncation=False)
            windows.append((len(enc['input_ids']),i,len(chunk),enc))
    windows.sort(key=lambda v:(v[0],v[1]));at=0;tick=time.monotonic()
    while at<len(windows):
        end=at+1
        while end<len(windows) and end-at<32 and windows[end][0]*(end-at+1)<=8192: end+=1
        batch=windows[at:end]
        enc=tokenizer.pad([v[3] for v in batch],padding=True,return_tensors='pt')
        specials=enc.pop('special_tokens_mask').bool().to('cuda')
        enc={k:v.to('cuda') for k,v in enc.items()}
        with torch.inference_mode(): h=model(**enc,return_dict=True).last_hidden_state.float()
        mask=enc['attention_mask'].bool() & ~specials
        sums=(h*mask.unsqueeze(-1)).sum(1).cpu().numpy()
        for k,(_,i,n,_) in enumerate(batch):
            if int(mask[k].sum())!=n: raise ValueError('Content pooling mismatch')
            features[i]+=sums[k];counts[i]+=n
        at=end
        if at%128<32 or at==len(windows):print(json.dumps(dict(completed_windows=at,total_windows=len(windows),seconds=time.monotonic()-tick)),flush=True)
    valid=counts>0;features[valid]/=counts[valid,None]
    return features,records

def extract(state,backend):
    import torch
    from huggingface_hub import snapshot_download
    state=Path(state);reg=check_registration(state)
    spec=MODELS[backend];checkpoint=snapshot_download(spec['model'],revision=spec['revision'])
    start=time.monotonic();engine=None
    for ds in DATASETS:
        if backend=='policylm' and ds=='wildguard':continue
        if backend=='policylm':
            from evals.activation_probe.extract import PolicyExtractor
            from evals.hatexplain.policy import native_fields
            p=read(state/'policies'/ds/'policylm.json');fields=native_fields(p,'markdown')
            engine=PolicyExtractor(checkpoint,dict(name=p['name'],block=fields['violation_rule'],
                allow=fields['not_violation_rule'],precedence=fields['exception_override']))
        for split in ['fit','validation','test']:
            folder=state/'features'/ds/backend/split
            if (folder/'manifest.json').exists():raise ValueError('Immutable extraction exists')
            inp=state/'inputs'/ds/(split+'.jsonl');cases=rows(inp)
            if any(set(r)!={'id','prompt','prompt_sha256'} for r in cases):raise ValueError('Encoder saw unexpected fields')
            folder.mkdir(parents=True,exist_ok=True);tick=time.monotonic();torch.cuda.reset_peak_memory_stats()
            if backend=='modernbert':features,records=modernbert(checkpoint,cases)
            else:
                if split=='fit':write(folder/'parity.json',engine.parity([r['prompt'] for r in cases[:16]]))
                features=[];records=[]
                for i,case in enumerate(cases):
                    ff,info=engine.one(case['prompt']);features.append(ff['policylm-l28-slot']);records.append(dict(id=case['id'],**info))
                    if (i+1)%256==0:print(json.dumps(dict(dataset=ds,split=split,completed=i+1,total=len(cases))),flush=True)
                features=np.stack(features)
            if features.shape!=(len(cases),spec['width']) or not np.isfinite(features).all():raise ValueError('Invalid features')
            np.save(folder/'features.npy',features.astype(np.float32),allow_pickle=False)
            write(folder/'records.json',records)
            artifacts={p.name:digest(p) for p in folder.iterdir() if p.is_file()}
            write(folder/'manifest.json',dict(created_utc=now(),ids=[r['id'] for r in cases],
                metadata_sha256=digest(state/'metadata'/ds/(split+'.jsonl.gz')),input_sha256=digest(inp),
                model=spec,artifacts=artifacts,sources=sources(),seconds=time.monotonic()-tick,
                peak_gpu_bytes=torch.cuda.max_memory_allocated(),gpu=torch.cuda.get_device_name(),torch_version=torch.__version__),exclusive=True)
            print(json.dumps(dict(dataset=ds,backend=backend,split=split,n=len(cases),seconds=time.monotonic()-tick)),flush=True)
    print('COMPLETE',backend,time.monotonic()-start,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--backend',choices=BACKENDS,required=True)
    extract(**vars(p.parse_args()))
