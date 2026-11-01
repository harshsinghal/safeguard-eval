import copy
import numpy as np
import pytest
from evals.retrieved_examples.common import bank_from_fit,fixed_ids,retrieve,vote,augmented_policy,build_job
from evals.retrieved_examples.report import metrics,delta
import hashlib

def bank():
    return [dict(id=str(i),group=str(i),prompt='A complete illustrative request with enough words for the experiment '+str(i),
                 expected='ALLOW' if i<4 else 'BLOCK') for i in range(8)]

def test_library_excludes_conflicts_and_deduplicates():
    rr=bank();rr+=[dict(rr[0],id='duplicate'),dict(rr[1],id='conflict',expected='BLOCK')]
    out,stats=bank_from_fit(rr)
    assert stats['conflicting_groups']==1
    assert len({r['group'] for r in out})==len(out)

def test_query_label_unavailable_and_input_is_unchanged():
    rr=bank();by={r['id']:r for r in rr};text='input';q={'id':'target','prompt':text,'prompt_sha256':hashlib.sha256(text.encode()).hexdigest()}
    base={'instructions':'Apply policy','criteria':{'ALLOW':'safe','BLOCK':'harm'}}
    job=build_job(q,'jev','fixed_four',base,fixed_ids(rr),by)
    assert job['body']['content']==text and job['body']['policy']['criteria']==base['criteria']
    assert base['instructions']=='Apply policy'
    with pytest.raises(ValueError):build_job(dict(q,expected='BLOCK'),'jev','fixed_four',base,fixed_ids(rr),by)

def test_neighbors_are_deterministic_and_balance_uses_bank_only():
    rr=bank();x=np.array([[1.,0.]]*8);q=np.array([1.,0.])
    r=retrieve(q,x,rr,exclude_ids=['0'])
    assert [x['id'] for x in r['nearest_four']]==['1','2','3','4']
    assert [x['id'] for x in r['balanced_nearest']]==['1','2','4','5']
    assert vote([{'id':x} for x in ['5','1','6','2']],{r['id']:r for r in rr})=='BLOCK'
    assert fixed_ids(rr)==fixed_ids(list(reversed(rr)))

def test_examples_do_not_replace_policy_or_modify_decision_fields():
    p={'block':'block rule','allow':'allow rule','precedence':'exceptions'}
    out=augmented_policy(p,'policylm',bank()[:4])
    assert out['block']==p['block'] and out['allow']==p['allow']
    assert out['precedence'].startswith('exceptions  ')
    assert '\n' not in out['precedence']
    assert augmented_policy(p,'policylm',[])==p
    assert augmented_policy(p,'shieldstral',bank()[:4])['precedence'].startswith('exceptions\n\n')

def test_errors_stay_in_denominator_and_paired_improvements():
    meta=[{'expected':x,'group':str(i)} for i,x in enumerate(['ALLOW','ALLOW','BLOCK','BLOCK'])]
    p=np.array([0,-1,1,0]);m=metrics(meta,p)
    assert m['accuracy']==.5 and m['unresolved']==1 and m['misses']==1
    c=delta(meta,p,np.array([0,0,1,1]))
    assert c['corrected']==2 and c['introduced']==0 and c['accuracy_difference']==.5
