"""Fitting-only Shieldstral scoring compatibility check; not a capacity curve."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import time
import httpx

from evals.run import build_payload
from evals.serving.cloud_lengths import server, rows, sha, write, write_rows


def normalized_score(entries):
    values={}
    for label,logp in entries:
        label=label.strip().lower().strip('\"\'').rstrip('.')
        if label in ('yes','no') and isinstance(logp,(int,float)) and math.isfinite(logp):
            values[label]=max(values.get(label,-math.inf),logp)
    if set(values)!={'yes','no'}: raise ValueError('Both binary alternatives required')
    high=max(values.values());yes=math.exp(values['yes']-high);no=math.exp(values['no']-high)
    return yes/(yes+no)


def run(state):
    from transformers import AutoTokenizer
    reg=json.loads((state/'registration.json').read_text());spec=reg['model']
    tok=AutoTokenizer.from_pretrained(spec['model'],revision=spec['revision'])
    policy=json.loads((state/'policy.json').read_text())
    label_ids=[]
    for word in ('yes','no',' yes',' no'):
        ids=tok.encode(word,add_special_tokens=False)
        if len(ids)==1: label_ids.extend(ids)
    label_ids=sorted(set(label_ids));assert len(label_ids)>=2
    data=[]
    for r in rows(state/'private-fit.jsonl')[:32]:
        messages=build_payload('shieldstral',spec['model'],policy,r['prompt'])['messages']
        ids=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=False)
        data.append(dict(id=r['id'],token_ids=ids,input_sha256=sha(ids),full_tokens=len(ids)))
    write(state/'input-manifest.json',[{k:v for k,v in r.items() if k!='token_ids'} for r in data])
    write(state/'tokenizer.json',dict(tokenizer=type(tok).__name__,label_token_ids=label_ids,
                                    label_tokens=[tok.decode([x]) for x in label_ids]))
    for engine in ('vllm','sglang'):
        out=state/engine;out.mkdir(exist_ok=True)
        try:
            with server(state,engine,2048):
                with httpx.Client(timeout=180,limits=httpx.Limits(max_connections=16)) as http:
                    def one(row):
                        start=time.perf_counter();result={k:v for k,v in row.items() if k!='token_ids'}
                        try:
                            if engine=='vllm':
                                endpoint='/v1/completions'
                                request=dict(model=spec['model'],prompt=row['token_ids'],max_tokens=1,
                                    temperature=0,top_p=1,logprobs=20,logprob_token_ids=label_ids,
                                    add_special_tokens=False)
                            else:
                                endpoint='/generate'
                                request=dict(input_ids=row['token_ids'],sampling_params=dict(
                                    max_new_tokens=1,temperature=0,top_p=1),return_logprob=True,
                                    token_ids_logprob=label_ids,top_logprobs_num=20,
                                    logprob_start_len=-1,return_text_in_logprobs=True)
                            response=http.post('http://127.0.0.1:8000'+endpoint,json=request)
                            response.raise_for_status();value=response.json()
                            if engine=='vllm':
                                entries=list(value['choices'][0]['logprobs']['top_logprobs'][0].items())
                                count=value['usage']['prompt_tokens']
                            else:
                                alternatives=(value['meta_info']['output_token_ids_logprobs'][0]
                                              + value['meta_info']['output_top_logprobs'][0])
                                entries=[(entry[2],entry[0]) for entry in alternatives]
                                count=value['meta_info']['prompt_tokens']
                            if count!=row['full_tokens']: raise ValueError('Changed input token count')
                            score=normalized_score(entries)
                            result.update(prediction='BLOCK' if score>=.5 else 'ALLOW',score=score,
                                          label_logprobs=entries, prompt_tokens=count)
                        except Exception as exc:
                            result.update(prediction='ERROR',error=type(exc).__name__+': '+str(exc)[:300])
                        result['seconds']=time.perf_counter()-start
                        return result
                    # Warm-up is fitting-only, distinct from timed capacity claims (none here).
                    for row in data[:4]: one(row)
                    serial=[one(row) for row in data]
                    with ThreadPoolExecutor(max_workers=16) as pool: batch=list(pool.map(one,data))
                    write_rows(out/'serial.jsonl',serial);write_rows(out/'batch.jsonl',batch)
                    errors=sum(r['prediction']=='ERROR' for r in serial+batch)
                    changes=sum(a['prediction']!=b['prediction'] for a,b in zip(serial,batch))
                    diffs=[abs(a['score']-b['score']) for a,b in zip(serial,batch) if 'score' in a and 'score' in b]
                    result=dict(n=32,errors=errors,label_changes=changes,max_score_difference=max(diffs,default=None))
                    result['accepted']=errors==0 and changes<=1 and result['max_score_difference']<=.02
                    write(out/'result.json',result);print(engine,json.dumps(result),flush=True)
        except Exception as exc:
            write(out/'failed.json',dict(error=str(exc)));print(engine,str(exc),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);a=p.parse_args();run(a.state)
