import json
from pathlib import Path
import argparse
p=argparse.ArgumentParser(description='Render injection benchmark tables and figures from the public archive.')
p.add_argument('--archive',required=True);p.add_argument('--out-dir',required=True);args=p.parse_args()
archive=Path(args.archive);doc=Path(args.out_dir);doc.mkdir(parents=True,exist_ok=True)
s=json.loads((archive/'summary.json').read_text())
names={'policylm':'PolicyLM 1.7B','shieldstral':'Shieldstral 3B','safeguard':'GPT-OSS Safeguard 20B','kev':'Kev 4B','clef':'Clef-Flash','jev':'Jev 1.14'}
order=list(names);pc=lambda x:'—' if x is None else f'{100*x:.2f}%';num=lambda x:'—' if x is None else f'{x:.3f}'
lines=['# Prompt-injection benchmark: results','', 'These are separate test collections, not a pooled security score. Every model uses the policy selected on validation; the brief baseline is retained for comparison. Model weights and decision rules are fixed.','']
v=json.loads((archive/'validation-summary.json').read_text())
lines += ['## Why each policy was selected','','These are validation results on 256 development examples, not held-out test scores. Each cell is the equal-source mean balanced accuracy. Selection and tie-breaking rules were registered before these results.','','| Model | Brief | Structured | Structured + fitting examples | Selected |','|---|---:|---:|---:|---|']
for m in order:
 lines.append(f'| {names[m]} | {pc(v[m]["brief"]["balanced_accuracy"])} | {pc(v[m]["structured"]["balanced_accuracy"])} | {pc(v[m]["examples"]["balanced_accuracy"])} | {s["selected"][m]} |')
lines += ['','The final tests below compare only the brief baseline and the policy selected here. No candidate was promoted because of its test score.','']
for ds,title in [('safeguard','xTRam1 Safe-Guard: 2,060 original test examples'),('deepset','Deepset: 116 original test examples')]:
 lines += ['## '+title,'','| Model | Selected policy | Accuracy | Balanced accuracy | Macro F1 | MCC | False blocks | Missed attacks | Unresolved |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
 for m in order:
  r=s['datasets'][ds]['metrics'][m+'/selected'];lines.append(f'| {names[m]} | {s["selected"][m]} | {pc(r["accuracy"])} | {pc(r["balanced_accuracy"])} | {pc(r["macro_f1"])} | {num(r["mcc"])} | {r["false_blocks"]}/{r["negatives"]} ({pc(r["false_positive_rate"])}) | {r["missed_violations"]}/{r["positives"]} ({pc(r["false_negative_rate"])}) | {r["unresolved"]} |')
 lines += ['','| Model | Brief policy BA | Selected policy BA | Change (points) | Paired 95% interval (points) |','|---|---:|---:|---:|---:|']
 for m in order:
  a=s['datasets'][ds]['metrics'][m+'/brief']['balanced_accuracy'];b=s['datasets'][ds]['metrics'][m+'/selected']['balanced_accuracy'];lo,hi=s['datasets'][ds]['uncertainty']['selected_minus_brief'][m]['balanced_accuracy']
  lines.append(f'| {names[m]} | {pc(a)} | {pc(b)} | {100*(b-a):+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] |')
 lines += ['']
lines += ['## NotInject: 339 benign lookalikes','','| Model | Benign allow rate | False blocks | Unresolved | Brief false-block rate | Selected false-block rate |','|---|---:|---:|---:|---:|---:|']
for m in order:
 a=s['datasets']['notinject']['metrics'][m+'/brief'];b=s['datasets']['notinject']['metrics'][m+'/selected']
 lines.append(f'| {names[m]} | {pc(b["specificity"])} | {b["false_blocks"]}/339 | {b["unresolved"]} | {pc(a["false_positive_rate"])} | {pc(b["false_positive_rate"])} |')
lines += ['','## JailbreakBench: 182 released attack attempts','','| Model | Overall detection | GCG detection (100) | PAIR detection (82) | Allowed attempts | Unresolved | Brief overall detection |','|---|---:|---:|---:|---:|---:|---:|']
for m in order:
 a=s['datasets']['jbb']['metrics'][m+'/brief'];b=s['datasets']['jbb']['metrics'][m+'/selected'];gcg=s['slices']['jbb']['attack_method=GCG'][m+'/selected'];pair=s['slices']['jbb']['attack_method=PAIR'][m+'/selected']
 lines.append(f'| {names[m]} | {pc(b["recall"])} | {pc(gcg["recall"])} | {pc(pair["recall"])} | {b["missed_violations"]} | {b["unresolved"]} | {pc(a["recall"])} |')
lines += ['','NotInject has only benign examples, and JBB only attack attempts. Neither receives a balanced-accuracy or macro-F1 score. A detector that blocks everything would catch every JBB attempt while failing NotInject completely. JBB rates describe detection of released attempts, not prevention of downstream attacks.','','## Interpretation and uncertainty','','Balanced accuracy gives equal weight to attack recall and benign allow rate. Accuracy retains the published class mixture. Unresolved outputs remain in denominators and cannot become artificial correct blocks; MCC is unavailable when predictions are unresolved. False-block and missed-attack columns count actual BLOCK/ALLOW errors; unresolved cases are shown separately.','','Intervals use 2,000 paired bootstrap draws of related-text groups. An interval spanning zero does not establish a directional improvement. These are exploratory comparisons without multiplicity correction. The small deepset test is particularly uncertain. Source annotations can be ambiguous without the original governing instructions; scores measure agreement with those labels.','','See the machine-readable summary for all baseline/selected metrics, absolute intervals, NotInject category/trigger slices, JBB method/category slices, and prespecified text-format slices. Character-format slices are text properties, not independently labeled attack categories.']
(doc/'RESULTS.md').write_text('\n'.join(lines)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
x=np.arange(len(order));labels=['PolicyLM','Shieldstral','Safeguard','Kev','Clef','Jev']
for ax,ds,title in zip(axes,['safeguard','deepset'],['xTRam1 Safe-Guard · 2,060 examples','Deepset · 116 examples']):
 a=[100*s['datasets'][ds]['metrics'][m+'/brief']['balanced_accuracy'] for m in order];b=[100*s['datasets'][ds]['metrics'][m+'/selected']['balanced_accuracy'] for m in order]
 ax.bar(x-.18,a,width=.35,color='#cbd5e1',label='Brief policy');ax.bar(x+.18,b,width=.35,color='#2563eb',label='Validation-selected policy')
 ax.set_xticks(x,labels,rotation=25,ha='right');ax.set_ylim(0,105);ax.set_ylabel('Balanced accuracy (%)');ax.set_title(title);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
 for i,v in enumerate(b):ax.text(i+.18,v+1,f'{v:.1f}',ha='center',fontsize=9)
axes[0].legend(loc='lower left',fontsize=9);fig.suptitle('Does the selected policy carry its improvement to the test set?',fontsize=15)
fig.savefig(doc/'policy-comparison.png',dpi=180);fig.savefig(doc/'policy-comparison.svg');plt.close(fig)
print('Wrote complete result tables and baseline-to-selected figure.')

fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
for ax,ds,title in zip(axes,['safeguard','deepset'],['xTRam1 Safe-Guard · 2,060 examples','Deepset · 116 examples']):
 for i,m in enumerate(order):
  a=s['datasets'][ds]['metrics'][m+'/brief']['balanced_accuracy'];b=s['datasets'][ds]['metrics'][m+'/selected']['balanced_accuracy']
  lo,hi=s['datasets'][ds]['uncertainty']['selected_minus_brief'][m]['balanced_accuracy']
  ax.hlines(i,lo*100,hi*100,color='#2563eb',linewidth=2)
  ax.plot((b-a)*100,i,'o',color='#172c49',markersize=6)
 ax.axvline(0,color='#94a3b8',linestyle='--',linewidth=1)
 ax.set_yticks(range(len(order)),[names[m] for m in order]);ax.invert_yaxis()
 ax.set_xlabel('Change in balanced accuracy (percentage points)')
 ax.set_title(title);ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
limits=[ax.get_xlim() for ax in axes];left=min(x[0] for x in limits);right=max(x[1] for x in limits)
for ax in axes:ax.set_xlim(left,right)
fig.suptitle('Policy selected on validation: test change and paired 95% interval',fontsize=14)
fig.savefig(doc/'policy-change.png',dpi=180);fig.savefig(doc/'policy-change.svg');plt.close(fig)
print('Wrote policy-change interval figure.')
