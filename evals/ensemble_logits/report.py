"""Readable tables and figures from frozen log-odds results; no model selection."""
import argparse
from pathlib import Path
import joblib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import expit

from evals.ensemble.common import COHORTS,read,write,align,metrics
from evals.ensemble.learn import classify,validity
from evals.ensemble.study import score_inputs,paired
from evals.ensemble_logits.learn import predict,log_odds
from evals.ensemble_logits.study import verify_freeze

TITLES={'wildguard-specialists':'WildGuard · specialists','hatexplain-specialists':'HateXplain · specialists','hatexplain-mixed':'HateXplain · specialists + Qwen'}
LABELS={'prior_probability_logistic':'Previous probability logistic','primary':'New log-odds logistic',
    'best_single':'Individual selected with expanded controls','prior_best_single':'Previously selected individual',
    'prior_best_ensemble':'Previously selected ensemble','secondary':'Equal log-odds average'}


def build(state,destination):
    state,destination=Path(state),Path(destination);destination.mkdir(parents=True,exist_ok=True)
    lines=['# Log-odds ensemble: complete results','',
        'All configurations and thresholds were selected on validation before this extension was tested. Policies, model weights and examples stayed fixed. Earlier official test results were already known, so all comparisons remain exploratory. Differences and confidence intervals below are in percentage points.','']
    all_results={};equations={}
    for cohort in COHORTS:
        freeze=verify_freeze(state,cohort);r=read(state/'cohorts'/cohort/'results.json');all_results[cohort]=r
        selection=read(state/'cohorts'/cohort/'selection.json');sel=r['selection'];candidates=r['all_candidates']
        lines += [f'## {TITLES[cohort]}','',f"Fit: {freeze['fit_n']:,}; validation: {freeze['validation_n']:,}; test: {r['n']:,}.",'',
            '| Method | Accuracy | Macro-F1 | Violation recall | False blocks | Missed violations |',
            '|---|---:|---:|---:|---:|---:|']
        for role in ['prior_probability_logistic','primary','best_single','prior_best_single','prior_best_ensemble','secondary']:
            m=candidates[sel[role]]['metrics']
            lines.append(f"| {LABELS[role]} | {100*m['accuracy']:.2f}% | {100*m['macro_f1']:.2f}% | {100*m['violation_recall']:.2f}% | {m['false_blocks']} | {m['missed_violations']} |")
        if 'wildguard-baseline' in candidates:
            m=candidates['wildguard-baseline']['metrics']
            lines.append(f"| WildGuard external baseline | {100*m['accuracy']:.2f}% | {100*m['macro_f1']:.2f}% | {100*m['violation_recall']:.2f}% | {m['false_blocks']} | {m['missed_violations']} |")
        lines += ['','### Primary comparisons','',
            '| New log-odds logistic versus… | Accuracy difference | 95% interval | Macro-F1 difference | Cases corrected | Cases made wrong |',
            '|---|---:|---:|---:|---:|---:|']
        for reference,c in r['contrasts']['primary'].items():
            lo,hi=c['accuracy_ci95'];label=LABELS.get(reference,'WildGuard external baseline')
            lines.append(f"| {label} | {100*c['accuracy_delta']:+.2f} | {100*lo:+.2f} to {100*hi:+.2f} | {100*c['macro_f1_delta']:+.2f} | {c['cases_fixed']} | {c['cases_broken']} |")
        lines += ['','Intervals use 2,000 paired duplicate-group bootstrap replicates. They are unadjusted, exclude search/inference uncertainty, and do not turn the reused tests into confirmatory evidence.','',
            '### Individual controls selected on validation','',
            '| Model | Selected configuration | Accuracy | Macro-F1 | Violation recall |','|---|---|---:|---:|---:|']
        for name,cid in sel['per_model'].items():
            m=candidates[cid]['metrics']
            lines.append(f"| {name} | `{cid}` | {100*m['accuracy']:.2f}% | {100*m['macro_f1']:.2f}% | {100*m['violation_recall']:.2f}% |")
        lines += ['',f"Highest individual accuracy across all registered configurations on this test: **{100*r['highest_observed_test_single']['accuracy']:.2f}%**. This is a descriptive hurdle, not a test-selected baseline for fitting.",'',
            '### Every new configuration','',
            '| Configuration | Validation accuracy | Threshold | Test accuracy | Macro-F1 | False blocks | Missed violations |',
            '|---|---:|---:|---:|---:|---:|---:|']
        for c in selection['candidates']:
            m=candidates[c['id']]['metrics']
            lines.append(f"| `{c['id']}` | {100*c['validation']['accuracy']:.2f}% | {c['selected_threshold']:.2f} | {100*m['accuracy']:.2f}% | {100*m['macro_f1']:.2f}% | {m['false_blocks']} | {m['missed_violations']} |")
        selected_record=next(c for c in selection['candidates'] if c['id']==sel['primary'])
        par=selected_record['logistic_parameters'];w=np.array(par['coefficients'])/np.array(par['feature_scales'])
        b=par['intercept']-float(w@np.array(par['feature_means']))
        equation=dict(features=freeze['features'],coefficients_on_unstandardized_log_odds=w.tolist(),intercept=b,
            decision_threshold=selected_record['selected_threshold'],form='score = sigmoid(intercept + sum(coefficient_i * log(p_i/(1-p_i))))',
            caution='Conditional fitted coefficients, not causal importance or normalized voting weights.')
        # Check the exported equation against the actual frozen estimator.
        test,_=score_inputs(state,freeze['dataset'],freeze['features'],'test');_,X,_,_=align(test,freeze['features'])
        model=next(c for c in joblib.load(state/'cohorts'/cohort/'models.joblib') if c['id']==sel['primary'])
        np.testing.assert_allclose(expit(b+log_odds(X)@w),predict(model,X),rtol=1e-10,atol=1e-12)
        equations[cohort]=equation
        lines += ['','### The learned equation','',
            'Let each input be that model’s reconstructed log-odds. These coefficients absorb the training-only standardization:', '',
            '| Term | Coefficient |','|---|---:|',f'| Intercept | {b:.6f} |']
        lines += [f'| {name} | {value:.6f} |' for name,value in zip(freeze['features'],w)]
        lines += ['',f"Apply sigmoid to the sum and BLOCK when the result is at least **{equation['decision_threshold']:.2f}**. Negative coefficients are permitted. A coefficient is conditional on the other model scores, not a causal measure of the model’s quality.",'']
    (destination/'RESULTS.md').write_text('\n'.join(lines)+'\n');write(destination/'equations.json',equations)
    # User-requested maximum-single hurdle: explicitly descriptive, after test.
    cohort='hatexplain-mixed';r=all_results[cohort];f=read(state/'cohorts'/cohort/'freeze.json')
    test,_=score_inputs(state,f['dataset'],f['features'],'test');meta,X,_,valid=align(test,f['features'])
    new=joblib.load(state/'cohorts'/cohort/'models.joblib');old=joblib.load(state/'reference'/cohort/'models.joblib')
    by_id={c['id']:c for c in new+old};a=by_id[r['selection']['primary']];b=by_id[r['selection']['per_model']['shieldstral']]
    aa=classify(predict(a,X),validity(a,valid),a['threshold']);bb=classify(predict(b,X),validity(b,valid),b['threshold'])
    write(destination/'descriptive-comparison.json',dict(role='Post-test descriptive comparison; not used for selection',
        comparison='HateXplain mixed log-odds logistic vs individually validation-selected Shieldstral',result=paired(meta,aa,bb)))
    fig,axes=plt.subplots(1,2,figsize=(12,4.9),sharey=True)
    for ax,reference,title,color in zip(axes,['prior_probability_logistic','best_single'],['Versus previous logistic ensemble','Versus validation-selected individual'],['#246B9E','#238678']):
        for i,(cohort,r) in enumerate(all_results.items()):
            c=r['contrasts']['primary'][reference];x=100*c['accuracy_delta'];lo,hi=np.array(c['accuracy_ci95'])*100
            ax.errorbar(x,i,xerr=[[x-lo],[hi-x]],fmt='o',color=color,capsize=4,markersize=7)
            ax.annotate(f'{x:+.2f} pp',(x,i),xytext=(0,10),textcoords='offset points',ha='center',fontsize=10)
        ax.axvline(0,color='#6B7280',linestyle='--',linewidth=1);ax.set_title(title,fontsize=12,pad=15)
        ax.set_yticks(range(3),[TITLES[c] for c in COHORTS]);ax.set_ylim(2.6,-.6)
        ax.set_xlim(-2.4,5.2);ax.set_xlabel('Difference in test accuracy (percentage points)');ax.grid(axis='x',alpha=.15)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Log-odds helped the logistic ensemble; the gain over one model varied',fontsize=15,fontweight='bold',y=.98)
    fig.text(.02,.02,'Frozen policies and model weights. Bars: unadjusted 95% paired group-bootstrap intervals.\nExploratory follow-up on previously observed official tests; no additional model inference.',fontsize=10,color='#475569')
    fig.tight_layout(rect=(0,.14,1,.91),w_pad=2)
    figures=destination/'figures';figures.mkdir(exist_ok=True)
    for ext in ['png','svg']:fig.savefig(figures/f'log-odds-comparison.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--state',required=True);p.add_argument('--destination',required=True)
    a=p.parse_args();build(a.state,a.destination)
