"""Generate all result tables from verified recorded analysis, without hand-entered scores."""
import json
from pathlib import Path
root=Path(__file__).resolve().parent;repo=root.parents[1]/'safeguard-eval';pub=repo/'published_runs/2026-10-25-qwen';a=json.loads((pub/'analysis.json').read_text());s=json.loads((pub/'selection.json').read_text())
pct=lambda x:f'{100*x:.2f}';models=list(s['selected']);names={'policylm':'PolicyLM-1.7B','shieldstral':'Shieldstral-3B','wildguard':'WildGuard-7B','cope':'CoPE-B-A4B','safeguard':'Safeguard-20B'}
short=lambda m:m.split('/')[-1]
entries={(e['split'],e['model'],role):e for e in a['entries'] for role in e['roles']}
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'
text='# Complete result tables\n\nAll figures below are computed from the archived predictions. Accuracy and F1 are percentages. Differences and intervals use percentage points. Intervals are exploratory, unadjusted and conditional on the chosen prompts.\n\n## Test: initial, shared and selected prompts\n\n'
rows=[]
for m in models:
 e=entries[('test',m,'selected')];mtr=e['metrics'];rows.append([short(m),pct(entries[('test',m,'initial')]['metrics']['accuracy']),pct(entries[('test',m,'shared')]['metrics']['accuracy']),pct(mtr['accuracy']),pct(mtr['harmful_f1']),e['policy_id']])
text+=table(['Qwen model','Initial accuracy','Shared accuracy','Selected accuracy','Selected harmful F1','Selected policy'],rows)
text+='\n## Selected prompts: error tradeoffs and prompt-tuning gain\n\n'
rows=[]
for m in models:
 e=entries[('test',m,'selected')];q=e['metrics'];d=e['vs_initial'];cm=q['confusion'];rows.append([short(m),cm['ALLOW']['BLOCK'],cm['BLOCK']['ALLOW'],q['errors'],pct(q['harmful_recall']),pct(q['benign_false_positive_rate']),pct(d['delta']),f"[{pct(d['ci95'][0])}, {pct(d['ci95'][1])}]"])
text+=table(['Model','False blocks','Missed harms','Output errors','Harm recall','False-block rate','Gain vs initial','Paired 95% interval'],rows)
text+='\n## All registered nearby-size comparisons\n\n'
rows=[]
for p in a['paired_comparisons']:
 d=p['qwen_minus_policy'];rows.append([short(p['model']),names[p['comparator']],p['role'],pct(p['qwen_metrics']['accuracy']),pct(p['policy_model_metrics']['accuracy']),pct(d['delta']),f"[{pct(d['ci95'][0])}, {pct(d['ci95'][1])}]",f"{d['a_correct_b_wrong']} / {d['a_wrong_b_correct']}"])
text+=table(['Qwen','Specialist','Prompt comparison','Qwen accuracy','Specialist accuracy','Difference','Paired 95% interval','Qwen-only / specialist-only correct'],rows)
text+='\n## Validation-selected score thresholds\n\nThese are separate controls. Primary results above use the free-generated label. Errors remain errors.\n\n'
rows=[]
for c in a['calibration_controls']:
 if c['available']:
  original=next(e for e in a['entries'] if e['split']=='test' and e['model']==c['model'] and e['policy_id']==c['policy_id']);rows.append([short(c['model']),c['policy_id'],c['threshold'],pct(original['metrics']['accuracy']),pct(c['metrics']['accuracy']),pct(c['metrics']['harmful_f1'])])
 else:rows.append([short(c['model']),c['policy_id'],'unavailable','—','—','—'])
text+=table(['Model','Policy','Threshold','Free-label accuracy','Threshold accuracy','Threshold harmful F1'],rows)
text+='\n## Comparisons after each available validation threshold\n\nWildGuard and Safeguard retain their historical explicit labels because no matching historical score control exists.\n\n'
rows=[]
for p in a['calibrated_paired_comparisons']:
 d=p['qwen_minus_policy'];rows.append([short(p['model']),names[p['comparator']],p['role'],p['qwen_threshold'],p['policy_model_threshold'] if p['policy_model_threshold'] is not None else 'explicit',pct(p['qwen_metrics']['accuracy']),pct(p['policy_model_metrics']['accuracy']),pct(d['delta']),f"[{pct(d['ci95'][0])}, {pct(d['ci95'][1])}]"])
text+=table(['Qwen','Specialist','Role','Qwen cutoff','Specialist cutoff','Qwen accuracy','Specialist accuracy','Difference','Paired 95% interval'],rows)
text+='\n## Prompt changes versus changing only the initial cutoff\n\nSecondary paired contrasts were added during final inference; prompts, cutoffs and primary outcomes stayed frozen.\n\n'
rows=[]
for c in a['prompt_vs_threshold_controls']:
 d=c['selected_free_vs_initial_threshold'];rows.append([short(c['model']),pct(c['initial_threshold_metrics']['accuracy']),pct(c['selected_free_metrics']['accuracy']),pct(d['delta']),f"[{pct(d['ci95'][0])}, {pct(d['ci95'][1])}]",pct(c['selected_threshold_metrics']['accuracy']) if 'selected_threshold_metrics' in c else 'unavailable'])
text+=table(['Model','Initial calibrated accuracy','Selected free-label accuracy','Difference','Paired 95% interval','Selected calibrated accuracy'],rows)
text+='\n## All candidate fitting and validation scores\n\nEach model has the same five-candidate budget. Individual validation mistakes were not used for editing.\n\n'
text+=table(['Model','Policy','Fitting accuracy (1,024)','Validation accuracy (512)','Selected'],[[short(r['model']),r['policy_id'],pct(r['scores']['fit']['accuracy']),pct(r['scores']['validation']['accuracy']),'yes' if s['selected'][r['model']]==r['policy_id'] else ''] for r in s['records']])
text+='\n## Internal audit (512 rows)\n\nThe audit was frozen and evaluated after selection; it was not used to revise prompts. It comes from the training source population and uses its labels.\n\n'
text+=table(['Model','Role','Accuracy','Harmful F1','Output errors'],[[short(m),role,pct(entries[('audit',m,role)]['metrics']['accuracy']),pct(entries[('audit',m,role)]['metrics']['harmful_f1']),entries[('audit',m,role)]['metrics']['errors']] for m in models for role in ['initial','shared','selected']])
text+='\n## Selected prompts: vanilla and adversarial test slices\n\nThese are source-provided prompt styles, not measures of downstream attack success.\n\n'
rows=[]
for m in models:
 q=entries[('test',m,'selected')]['metrics']['slices']['adversarial']
 for label,v in q.items():rows.append([short(m),label,v['n'],pct(v['accuracy']),pct(v['harmful_f1'])])
text+=table(['Model','Adversarial source flag','Rows','Accuracy','Harmful F1'],rows)
text+='\n## Repeated-input diagnostic\n\nPilot and search reuse some identical requests under different batch contexts. This diagnostic has no controlled repetition or seed sweep.\n\n'
text+=table(['Model','Common rows','Identical requests','Changed decisions'],[[short(r['model']),r['common_rows'],r['identical_request_rows'],r['changed_decisions']] for r in a['repeatability']])
text+='\nFull category metrics, all confusion matrices, paired discordances and calibration controls are in [analysis.json](analysis.json). Exact policies, predictions and run metadata are indexed in [run-index.json](run-index.json).\n'
(pub/'DETAILS.md').write_text(text)
print('Generated complete tables')
