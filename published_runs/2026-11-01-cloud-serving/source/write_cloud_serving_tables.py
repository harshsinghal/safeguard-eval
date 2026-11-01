"""Render all registered L4 operating points from recomputed results."""
import argparse
import json
from pathlib import Path


def render(root):
    result=json.loads((root/'results.json').read_text())
    lines=['# L4 serving: all operating points','',
        'Qwen3.5 4B, BF16, one NVIDIA L4, fixed policy and identical input token IDs.',
        'Prefix/radix caches are disabled. These are neutral synthetic load documents,',
        'not a new moderation-accuracy evaluation. Each point averages two 64-request',
        'passes. The latency columns average the per-pass percentiles; they are not',
        'pooled percentiles or confidence intervals. GPU rental projections assume',
        'sustained measured utilization at $0.59/hour and are not AWS/GCP prices.','',
        'Submitted-content bins of 64, 256, 1,024 and 4,096 tokens produce full inputs',
        'of 466, 658, 1,426 and 4,498 tokens. The mixed group contains 16 from each bin.','',
        '| Engine | Content tokens | In flight | Valid/s | Median ms | p95 ms | GPU $/million | Errors / requests |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    def number(x,digits): return f'{x:.{digits}f}' if x is not None else 'unavailable'
    for engine,spec in result['engines'].items():
        for r in spec.get('curves',[]):
            lines.append('| '+engine+' | '+r['content_tokens']+' | '+str(r['concurrency'])+' | '+
                ' | '.join(number(r[k],digits) for k,digits in [('requests_per_second',2),('p50_ms',1),
                    ('p95_ms',1),('gpu_usd_per_million',2)])+' | '+str(r['errors'])+' / '+str(r['requests'])+' |')
    lines+=['','## Fitting and output checks','']
    for engine,spec in result['engines'].items():
        lines.append(f"- {engine}: {spec['status']}; selected chunk budget: {spec.get('parameter','none')} tokens.")
    if result['cross_engine']:
        c=result['cross_engine']
        lines+=['',f"The two selected engines differed on {c['label_differences']} of {c['fitting_n']} fitting labels, with {c['errors']} errors.",
                'This small canary is a consistency check, not proof of unchanged benchmark accuracy.']
    if result.get('long_input_control'):
        lines+=['','## Exploratory long-input control','',
                'The unselected 8,192-token chunk was measured after the primary curves.',
                'It does not replace either engine\'s original selection. All inputs have',
                '4,096 content tokens (4,498 full tokens). See [the control plan](LONG-INPUT-CONTROL.md).','',
                '| Engine | In flight | Chunk | Valid/s | Median ms | p95 ms | Label changes vs primary |',
                '|---|---:|---:|---:|---:|---:|---:|']
        for r in result['long_input_control']:
            lines.append(f"| {r['engine']} | {r['concurrency']} | 8192 | {r['requests_per_second']:.2f} | {r['p50_ms']:.1f} | {r['p95_ms']:.1f} | {r['label_changes_from_primary']} / {r['requests']} |")
    hf=result.get('shieldstral_hf_canary')
    if hf:
        lines+=['','## Shieldstral HF-only scoring check','',
            'Thirty-two fitting prompts, serial and with 16 in flight. These are',
            'score-consistency checks, not capacity or benchmark-accuracy results.','',
            '| Engine | Request errors | Batch label changes | Maximum batch score change | Accepted |',
            '|---|---:|---:|---:|---|']
        for engine in ('vllm','sglang'):
            r=hf[engine]
            lines.append(f"| {engine} | {r['errors']} / 64 | {r['label_changes']} / 32 | {r['max_score_difference']:.8f} | {r['accepted']} |")
        c=hf['cross_engine'];o=hf['original_vllm_comparison']
        lines+=['',f"Serial labels differed across engines on {c['label_differences']} / {c['n']} prompts; maximum score difference was {c['max_score_difference']:.8f}.",
            f"vLLM's scores before and after selecting the HF-only directory differed by at most {o['max_score_difference']:.8f}.",
            'Both earlier SGLang loading failures remain in the archive. No weights were transformed.']
    lines+=['','[Readable findings](README.md) · [Deployment implications](DEPLOYMENT.md) · [Reproduction](REPRODUCE.md)','']
    return '\n'.join(lines)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.write_text(render(a.root))
