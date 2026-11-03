"""Single-GPU native classifiers behind an explicit dynamic batch queue."""
import argparse
import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import sys
import time
import torch
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from evals.ensemble.common import read, digest


class Native:
    def __init__(self,state,slug,max_batch):
        self.state=Path(state);self.slug=slug
        self.spec=read(self.state/'registration.json')['models'][slug]
        self.policy=read(self.state/'policies'/(slug+'.json')) if slug!='liquid' else None
        from huggingface_hub import snapshot_download
        if slug in ('clef','kev'):
            from evals.decision_models.adapters import Adapter
            self.adapter=Adapter(slug,'/root/decision-vendor',serving_fused=self.spec.get('serving_fused',False))
        elif slug=='policylm':
            path=snapshot_download(self.spec['model'],revision=self.spec['revision'])
            sys.path.insert(0,str(Path(path)/'inference'))
            from policylm_infer import PolicyLM, Policy, Category
            self.native=PolicyLM.from_pretrained(path,device='cuda',dtype='bfloat16',max_batch_rows=max_batch,
                max_batch_tokens=self.spec.get('native_max_batch_tokens','auto'),max_chars=None)
            self.category=Policy([Category(self.policy['name'],violation_rule=self.policy['block'],not_violation_rule=self.policy['allow'],exception_override=self.policy['precedence'])])
            self.native.check_policy(self.category)
        else:
            from transformers import AutoTokenizer
            from evals.liquid_finetune.runner import load_model
            checkpoint=self.state/'liquid-epoch3.pt'
            assert digest(checkpoint)==self.spec['checkpoint_sha256']
            self.model=load_model().eval()
            loaded=torch.load(checkpoint,map_location='cpu',weights_only=True)
            self.model.load_state_dict(loaded['model'] if 'model' in loaded else loaded)
            del loaded
            self.tok=AutoTokenizer.from_pretrained(self.spec['model'],revision=self.spec['revision'],trust_remote_code=True)
            self.tok.padding_side='right'

    def infer(self,texts):
        with torch.inference_mode():
            if self.slug in ('clef','kev'):
                encoded=[self.adapter.encode(t,self.policy) for t in texts]
                results=self.adapter.forward(encoded)
                for r,e in zip(results,encoded):r['input_tokens']=e[2]
            elif self.slug=='policylm':
                native=self.native.classify_batch(texts,self.category)
                results=[dict(score=float(r.categories[self.policy['name']].score),windows=r.windows if hasattr(r,'windows') else None) for r in native]
            else:
                encoded=self.tok(texts,padding=True,truncation=False,return_tensors='pt')
                assert encoded['input_ids'].shape[1]<=8192
                encoded={k:v.cuda() for k,v in encoded.items() if k in ('input_ids','attention_mask')}
                with torch.autocast('cuda',dtype=torch.bfloat16):scores=torch.sigmoid(self.model(**encoded)).float().cpu().tolist()
                sizes=encoded['attention_mask'].sum(1).cpu().tolist()
                results=[dict(score=p,input_tokens=n) for p,n in zip(scores,sizes)]
            for r in results:r['prediction']='BLOCK' if r['score']>=self.spec['threshold'] else 'ALLOW'
            return results


def serve(state,slug,max_batch):
    torch.set_num_threads(4)
    model=Native(state,slug,max_batch);queue=asyncio.Queue()
    async def worker():
        while True:
            first=await queue.get();items=[first]
            # Collect arrivals for up to 2ms without blocking the ASGI event loop.
            await asyncio.sleep(.002)
            while len(items)<max_batch and not queue.empty():items.append(queue.get_nowait())
            started=time.perf_counter()
            try:
                out=await asyncio.to_thread(model.infer,[x[0] for x in items])
                assert len(out)==len(items)
                for (_,future,received),result in zip(items,out):
                    result.update(batch_size=len(items),queue_seconds=started-received,batch_seconds=time.perf_counter()-started)
                    if not future.cancelled():future.set_result(result)
            except Exception as exc:
                for _,future,_ in items:
                    if not future.cancelled():future.set_exception(exc)
    @asynccontextmanager
    async def lifespan(app):
        task=asyncio.create_task(worker())
        yield
        task.cancel()
    app=FastAPI(lifespan=lifespan)
    class Request(BaseModel):prompt:str
    @app.get('/health')
    async def health():return {'status':'ready'}
    @app.post('/classify')
    async def classify(request:Request):
        future=asyncio.get_running_loop().create_future()
        await queue.put((request.prompt,future,time.perf_counter()))
        return await future
    uvicorn.run(app,host='127.0.0.1',port=8000,access_log=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--state',required=True);ap.add_argument('--model',required=True);ap.add_argument('--max-batch',type=int,required=True)
    args=ap.parse_args();serve(args.state,args.model,args.max_batch)
