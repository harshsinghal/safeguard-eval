"""Build human-readable tables from the verified public summaries."""
from pathlib import Path
import json
repo=Path(__file__).resolve().parents[1];archive=repo/'published_runs/2026-10-31-serving';docs=repo/'docs/serving';w=archive/'analysis'
labels={'policylm':'PolicyLM 1.7B','shieldstral':'Shieldstral 3B','qwen-4b':'Qwen3.5 4B','wildguard':'WildGuard 7B','kev':'Kev 4B','clef':'Clef-Flash 9B','liquid':'Fine-tuned Liquid encoder 350M'}
series={k:json.loads((archive/'analysis'/k/'summary.json').read_text()) for k in ['reference','optimized','policy-batching']}
allfast=series['optimized']+series['policy-batching']
(archive/'analysis/optimized-summary.json').write_text(json.dumps(allfast,indent=2)+'\n')
def row(slug,c,cache,kind='reference'):
 return next(r for r in series[kind] if r['model']==slug and r['concurrency']==c and r['cache']==cache)
main=['| Configured system | Runtime | One request: median | 32 in flight: valid requests/s | 32 in flight: p95 | GPU-only $/million |','|---|---|---:|---:|---:|---:|']
for slug,label in labels.items():
 kind='policy-batching' if slug=='policylm' and any(r['model']==slug for r in series['policy-batching']) else 'optimized' if any(r['model']==slug for r in series['optimized']) else 'reference'
 spec=json.loads((archive/('optimized' if kind=='optimized' else 'policy-batching' if kind=='policy-batching' else 'reference')/'registration.json').read_text())['models'][slug]
 cache=spec['backend']=='vllm'
 one=row(slug,1,cache,kind);loaded=row(slug,32,cache,kind)
 runtime='vLLM; prefix cache on' if cache else 'native; larger token budget' if kind=='policy-batching' else 'native; optimized kernels' if kind=='optimized' else 'native; reference'
 main.append(f"| {label} | {runtime} | {one['p50_ms']:.1f} ms | {loaded['requests_per_second']:.1f} | {loaded['p95_ms']:.1f} ms | ${loaded['gpu_usd_per_million']:.2f} |")
(w/'main-table.md').write_text('\n'.join(main)+'\n')
controls=['| Same model, changed serving setting | C32 reference requests/s | C32 changed requests/s | Throughput ratio |','|---|---:|---:|---:|']
for slug in ['shieldstral','qwen-4b','wildguard']:
 a=row(slug,32,False);b=row(slug,32,True)
 controls.append(f"| {labels[slug]}: prefix cache off → on | {a['requests_per_second']:.1f} | {b['requests_per_second']:.1f} | {b['requests_per_second']/a['requests_per_second']:.2f}× |")
for slug in ['policylm','kev','clef']:
 kind='policy-batching' if slug=='policylm' else 'optimized'
 if not any(r['model']==slug for r in series[kind]):continue
 a=row(slug,32,False);b=row(slug,32,False,kind)
 name='1,024 → 32,768 internal batch tokens' if slug=='policylm' else 'reference → optimized kernels'
 controls.append(f"| {labels[slug]}: {name} | {a['requests_per_second']:.1f} | {b['requests_per_second']:.1f} | {b['requests_per_second']/a['requests_per_second']:.2f}× |")
(w/'control-table.md').write_text('\n'.join(controls)+'\n')
lines=['# All measured serving profiles','', 'One L40S at $0.80/hour. Each row pools three passes of 384 requests. “Valid” means a parsed classification, not a correct label. Cost is a sustained-load GPU-only projection. The rates include each finite pass’s ramp-up and drain.','']
for kind in series:
 lines+=['## '+{'reference':'Reference runtimes','optimized':'Decision-model kernel extension','policy-batching':'PolicyLM internal token-budget extension'}[kind],'']
 if kind=='policy-batching' and not series[kind]:
  gate=json.loads((archive/kind/'policylm/parity-check-p8.json').read_text())
  attempt=json.loads((archive/kind/'policylm/tune-p8.json').read_text())
  lines += [f"No configuration was accepted, and no measurement pass was run. At maximum batch 8, the 32,768-token budget produced {attempt['requests_per_second']:.2f} requests/s on the 96 fitting prompts, below the original profile. Its 32-input batching check changed {gate['decision_changes']} labels but shifted a score by {gate['max_score_difference']:.5f}, exceeding the preregistered 0.02 limit. Maximum batch 32 ran out of GPU memory during fitting-only warm-up. The main comparison therefore retains PolicyLM’s original 1,024-token budget. These are fitting outcomes, not held-out speed results.", '']
 for slug,label in labels.items():
  rr=[r for r in series[kind] if r['model']==slug]
  if not rr:continue
  frozen=json.loads((archive/kind/slug/'freeze.json').read_text())
  param='scheduled tokens per iteration' if rr[0]['backend']=='vllm' else 'maximum outer batch rows'
  lines+=[f'### {label}', '', f"Fitting-selected setting: **{frozen['parameter']} {param}**.", '', '| Prefix cache | In flight | Median ms | p95 ms | Valid/s | Repeat range /s | GPU $/million | Errors |','|---|---:|---:|---:|---:|---:|---:|---:|']
  for r in sorted(rr,key=lambda r:(r['cache'],r['concurrency'])):
   lines.append(f"| {'On' if r['cache'] else 'Off / native'} | {r['concurrency']} | {r['p50_ms']:.1f} | {r['p95_ms']:.1f} | {r['requests_per_second']:.2f} | {r['repeat_rate_min']:.2f}–{r['repeat_rate_max']:.2f} | ${r['gpu_usd_per_million']:.2f} | {r['errors']} |")
  lines+=['']
lines+=['## Output agreement','', 'The table reports the largest number of changed decisions in any 384-request pass compared with that runtime’s first single-request pass. Historical differences compare its first single-request pass with the matched archived predictions. Neither is an accuracy score. Qwen probabilities are auxiliary; its generated label determines the decision.','', '| Runtime | Model | Most label changes in one pass | Largest score change | Historical label changes / 384 |','|---|---|---:|---:|---:|']
for kind in series:
 audit=json.loads((archive/'analysis'/kind/'repeat-parity.json').read_text())
 for slug,a in audit.items():
  if not a.get('complete'):continue
  h=a.get('historical',{});deltas=[r['max_score_difference'] for r in a['runs'] if r['max_score_difference'] is not None];delta_text=f'{max(deltas):.5f}' if deltas else 'Not exposed'
  lines.append(f"| {kind} | {labels[slug]} | {max(r['decision_changes'] for r in a['runs'])} | {delta_text} | {h.get('decision_changes','—')} |")
lines+=['', 'Full per-pass and cross-runtime agreement records are in the evidence bundle. A zero on this sample does not prove bitwise equivalence on other inputs. Some numerical differences cross a decision cutoff; evaluate classification quality again before replacing a production runtime.','', '## Input and output work','', '| Model | Median full input tokens | p95 full input tokens | Median generated tokens |','|---|---:|---:|---:|']
for slug,label in labels.items():
 r=row(slug,1,False);f=lambda x:'Not exposed' if x is None else f'{x:g}'
 lines.append(f"| {label} | {f(r['input_tokens_median'])} | {f(r['input_tokens_p95'])} | {f(r['output_tokens_median']) if r['backend']=='vllm' else 'Native scores'} |")
lines+=['', 'These token counts include different policy/template contracts and different tokenizers. Native PolicyLM’s helper does not expose a comparable per-request token count through this interface. GPU memory reservation is not a measurement of the minimum GPU needed.','']
(docs/'RESULTS.md').write_text('\n'.join(lines))
print('Generated tables and detailed results from verified summaries.')
