"""Human-readable results generated from frozen evaluations."""
import csv
from pathlib import Path
from .common import read


def render(state):
 state=Path(state);r=read(state/'results.json');fits=read(state/'fitting.json')
 lines=['# Can complementary models reduce moderation errors?','','A predeclared, training-selected logistic ensemble across specialist, general-purpose and decision models. The backbone weights and policies stayed fixed. Official public tests were reused; Jev test calls were refreshed after the ensemble freeze. These are exploratory results.','']
 fields=['dataset','method','profile','components','threshold','balanced_accuracy','accuracy','macro_f1','mcc','false_blocks','missed_violations','false_positive_rate','false_negative_rate','auroc','brier','unresolved','test_target_met']
 output=[]
 for ds,data in r['datasets'].items():
  params=fits[ds]['parameters'];primary=params['primary'];m=data['methods']['primary']['balanced']['metrics']
  lines += [f'## {ds}', '',f"{data['n']:,} test examples: {data['positives']:,} BLOCK and {data['negatives']:,} ALLOW. Fitting: 4,096; validation: 1,536.",'',f"Training selection retained **{', '.join(primary['names'])}**. The final validation cutoff was {data['methods']['primary']['balanced']['threshold']}. Test balanced accuracy: **{m['balanced_accuracy']:.2%}**, with **{m['false_blocks']} false blocks and {m['missed_violations']} misses**.",'','### Registered comparisons','','| Method | Components | Balanced accuracy | Accuracy | False blocks | Misses |','|---|---|---:|---:|---:|---:|']
  for method,profiles in data['methods'].items():
   for profile,item in profiles.items():
    if item is None:continue
    names=params[item['candidate']]['names'];mm=item['metrics']
    row={k:mm.get(k) for k in fields};row.update(dataset=ds,method=method,profile=profile,components='+'.join(names),threshold=item['threshold'],test_target_met=item['test_target_met']);output.append(row)
   item=profiles['balanced'];mm=item['metrics'];names=params[item['candidate']]['names']
   lines.append(f"| {method} | {', '.join(names)} | {mm['balanced_accuracy']:.2%} | {mm['accuracy']:.2%} | {mm['false_blocks']} | {mm['missed_violations']} |")
  lines += ['','### Primary paired differences','','Positive differences favor the selected mixed ensemble. These intervals are unadjusted and conditional on saved outputs.','','| Primary versus | Balanced-accuracy change, points (95% interval) | Errors corrected | New errors | False blocks change | Misses change |','|---|---:|---:|---:|---:|---:|']
  for p in data['paired_comparisons']:
   ci=p['ci95'];lines.append(f"| {p['b']} | {100*p['balanced_accuracy_difference']:+.2f} ({100*ci[0]:+.2f}, {100*ci[1]:+.2f}) | {p['corrected']} | {p['introduced']} | {p['false_blocks_difference']:+} | {p['misses_difference']:+} |")
  lines += ['','### Learned equation','','For each listed component, clip its BLOCK score to [0.000001, 0.999999] and compute log(score / (1-score)). The final score is sigmoid(intercept + the weighted sum of those log-odds). These coefficients are conditional on the other correlated model scores; they are not percentages or causal importance.','',f"Intercept: `{primary['logodds_intercept']:.9g}`.",'','| Component | Log-odds coefficient |','|---|---:|']
  for name,coef in primary['logodds_coefficients'].items():lines.append(f'| {name} | {coef:.9g} |')
  lines += ['','### Training selection path','','| Step | Candidate components | OOF balanced accuracy | Accepted? |','|---:|---|---:|---|']
  for step in fits[ds]['paths']['primary']:
   lines.append(f"| {step['step']} | {', '.join(step['names'])} | {step['oof']['balanced_accuracy']:.2%} | {'Yes' if step['accepted'] else 'No: gain below 0.2 points'} |")
  lines += ['','The OOF values were used to search subsets and regularization; they are not independent final accuracy estimates. Full rejected candidates, error overlaps, folds, parameters and component ablations are preserved in fitting.json.','']
  lines += ['### Operating targets','','| Primary selection profile | Validation target met | Test target met | False-block rate | Miss rate |','|---|---|---|---:|---:|']
  for profile in ['false_block_limit','catch_target']:
   x=data['methods']['primary'][profile]
   if x is None:lines.append(f'| {profile} | No eligible cutoff | — | — | — |')
   else:lines.append(f"| {profile} | Yes | {'Yes' if x['test_target_met'] else 'No'} | {x['metrics']['false_positive_rate']:.2%} | {x['metrics']['false_negative_rate']:.2%} |")
  lines += ['']
 lines += ['## Limits','','This is a bounded configured-system comparison, not an architecture or training-data causal study. Different families are not guaranteed to make complementary errors. Scores are not interchangeable calibrated probabilities. The same public tests and development histories have informed earlier research; no fresh independently labeled test was created. WildGuardTrain model-derived labels differ from the human-labeled test. Jev canary scores varied even for identical requests, so all new Jev development and test outputs were collected in this study; intervals do not capture API variability. No policy optimization, new representation head, second-pass routing, or backbone fine-tuning was performed.','']
 (state/'RESULTS.md').write_text('\n'.join(lines)+'\n')
 with (state/'results.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(output)
