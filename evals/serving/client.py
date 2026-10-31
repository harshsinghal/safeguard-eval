"""Closed-loop HTTP load, measuring complete, parsed classifications."""
import argparse
import concurrent.futures
import json
import math
from pathlib import Path
import random
import time
import urllib.request
import numpy as np

from evals.ensemble.common import read, rows, write, write_rows
from evals.wildguard import run as specialist
from evals.qwen_policy import run as general


def summarize(records, seconds):
    good = [r for r in records if r.get('prediction') in ('ALLOW', 'BLOCK')]
    lat = np.array([r['seconds'] for r in good])
    rate = len(good) / seconds
    return dict(requests=len(records), valid=len(good), errors=len(records)-len(good),
        wall_seconds=seconds, requests_per_second=rate,
        p50_ms=float(np.quantile(lat, .5)*1000) if len(lat) else None,
        p95_ms=float(np.quantile(lat, .95)*1000) if len(lat) else None,
        gpu_usd_per_million=.8/3600/rate*1e6 if rate else None)


class Client:
    def __init__(self, state, slug, base='http://127.0.0.1:8000'):
        self.state=Path(state); self.slug=slug; self.base=base
        self.spec=read(self.state/'registration.json')['models'][slug]
        self.policy=read(self.state/'policies'/(slug+'.json')) if (self.state/'policies'/(slug+'.json')).exists() else None
        self.ids=[]; self.tok=None
        if slug=='shieldstral': self.ids=specialist.score_ids(base,self.spec['model'],'shieldstral')
        if slug=='qwen-4b':
            for label in ('A','B',' A',' B'):
                tt=specialist.post(base,'/tokenize',dict(model=self.spec['model'],prompt=label,add_special_tokens=False))['tokens']
                if len(tt)==1:self.ids+=tt
            self.ids=sorted(set(self.ids));assert len(self.ids)>=2
        if slug=='wildguard':
            from transformers import AutoTokenizer
            self.tok=AutoTokenizer.from_pretrained(self.spec['model'],revision=self.spec['revision'],use_fast=False)

    def one(self, row):
        start=time.perf_counter(); result=dict(id=row['id'],prompt_sha256=row['prompt_sha256'])
        try:
            if self.spec['backend']=='native':
                req=dict(prompt=row['prompt']); endpoint='/classify'
            elif self.slug=='qwen-4b':
                req=general.payload(self.spec['model'],self.policy,row['prompt'],self.ids);endpoint='/v1/chat/completions'
            else:
                req=specialist.payload(self.slug,self.spec['model'],self.policy,row['prompt'])
                endpoint='/v1/completions' if self.slug=='wildguard' else '/v1/chat/completions'
                if self.slug=='wildguard':
                    req['prompt']=self.tok(req['prompt'],add_special_tokens=True)['input_ids']
                    req['add_special_tokens']=False
                else:req['logprob_token_ids']=self.ids
            resp=specialist.post(self.base,endpoint,req)
            if self.spec['backend']=='native': result.update(resp)
            else:
                result.update(general.parse(resp) if self.slug=='qwen-4b' else specialist.parse(resp,self.slug))
                result['usage']=resp.get('usage',{})
            if result.get('score') is not None:
                assert math.isfinite(result['score']) and 0<=result['score']<=1
                # Qwen's primary interface is a freely generated label, not a score cutoff.
                if self.slug!='qwen-4b':result['prediction']='BLOCK' if result['score']>=self.spec['threshold'] else 'ALLOW'
        except Exception as exc:
            result.update(prediction='ERROR',error=type(exc).__name__+': '+str(exc)[:300])
        result['seconds']=time.perf_counter()-start
        return result

    def run(self, data, concurrency, output, seed, cache=False):
        data=list(data);random.Random(seed).shuffle(data)
        if self.spec['backend']=='vllm':
            # Reset even between tuning/warmup/final passes. No repeated-content cache benefit.
            request=urllib.request.Request(self.base+'/reset_prefix_cache',data=b'',method='POST')
            with urllib.request.urlopen(request,timeout=60) as response: response.read()
        warm=rows(self.state/'inputs/tune.jsonl')[:16]
        for row in warm:self.one(row)
        start=time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
            output_rows=list(pool.map(self.one,data))
        seconds=time.perf_counter()-start
        write_rows(output.with_suffix('.jsonl'),output_rows)
        summary=summarize(output_rows,seconds)
        summary.update(model=self.slug,concurrency=concurrency,seed=seed,cache=cache)
        write(output.with_suffix('.json'),summary)
        print(json.dumps(dict(run=str(output.name),**summary)),flush=True)
        return summary
