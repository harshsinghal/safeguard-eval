import copy
from concurrent.futures import ThreadPoolExecutor
import tempfile
from pathlib import Path
import unittest

from evals.jev.api import (CAP, RESERVE, RESOLVED, Ledger, billed_cost,
                           parse, payload, canonical)
from evals.jev.study import choose_examples, select_policy, select_threshold, threshold_rows
from evals.wildguard.metrics import metrics
from evals.jev.report import public_policy_record, archive_selection, align


def response():
    return dict(model=RESOLVED, provider='TypeSafe', answers={
        'brief':dict(type='choice',choice='BLOCK',probabilities={'ALLOW':.2,'BLOCK':.8},confidence=.6)},
        usage=dict(cost=.00001,input_tokens=238,output_tokens=20))


def row(i, gold='ALLOW', prediction='ALLOW', score=.2, split='validation'):
    return dict(id=str(i),expected=gold,prediction=prediction,score=score,split=split,
                group='g'+str(i),prompt_sha256='h'+str(i),agreement=3,
                prompt='These are eight neutral words in this synthetic example.')


class JevTests(unittest.TestCase):
    def test_native_choice_score_not_confidence(self):
        r=parse(response(),['brief'])['brief']
        self.assertEqual(r['score'],.8)
        self.assertEqual(r['confidence'],.6)
        self.assertEqual(r['prediction'],'BLOCK')

    def test_router_other_model_missing_question_invalid_distribution_rejected(self):
        for mutate in [lambda r:r.update(model='typesafe/jev-router'),
                       lambda r:r.update(provider='Other'),
                       lambda r:r['answers'].clear(),
                       lambda r:r['answers']['brief']['probabilities'].update(ALLOW=.4),
                       lambda r:r['answers']['brief']['probabilities'].update(BLOCK=float('nan')),
                       lambda r:r['answers']['brief'].update(choice='ALLOW'),
                       lambda r:r['answers']['brief'].update(type='noul')]:
            r=response();mutate(r)
            with self.assertRaises(ValueError):parse(r,['brief'])

    def test_payload_does_not_send_gold_metadata(self):
        pp={'brief':dict(type='choice',instructions='Classify.',criteria={'ALLOW':'Allowed','BLOCK':'Violation'})}
        body=payload('A neutral example.',pp)
        self.assertEqual(body['state'],{'content':'A neutral example.'})
        self.assertNotIn('expected',canonical(body))
        self.assertNotIn('split',canonical(body))
        with self.assertRaises(ValueError):payload('x'*40000,pp)

    def test_billing_missing_cost_never_treated_as_free(self):
        r=response();del r['usage']['cost']
        with self.assertRaises(ValueError):billed_cost(r)
        r=response();r['usage']['cost']=RESERVE*2
        with self.assertRaises(ValueError):billed_cost(r)

    def test_concurrent_budget_and_pending_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'ledger.db';ledger=Ledger(p,0,RESERVE*3.1)
            def reserve(i):
                try:ledger.reserve(str(i));return True
                except RuntimeError:return False
            with ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(reserve,range(8))),3)
            with self.assertRaises(RuntimeError):Ledger(p,0,RESERVE*3.1).assert_no_pending()
            self.assertLessEqual(ledger.totals()['total_accounted_usd'],RESERVE*3.1)

    def test_no_test_based_selection(self):
        rr=[row(1,split='test')]
        with self.assertRaises(ValueError):select_threshold(rr)
        with self.assertRaises(ValueError):select_policy({p:{} for p in ['brief','detailed','examples']},
            {p:rr for p in ['brief','detailed','examples']})

    def test_examples_are_training_only_balanced_and_group_distinct(self):
        fit=[row(i,'BLOCK' if i<4 else 'ALLOW', 'ALLOW' if i<4 else 'BLOCK',split='fit') for i in range(8)]
        selected=choose_examples(fit,fit)
        self.assertEqual(len(selected),4)
        self.assertEqual(sum(r['expected']=='BLOCK' for r in selected),2)
        self.assertEqual(len({r['group'] for r in selected}),4)
        self.assertEqual([r['id'] for r in selected],[r['id'] for r in choose_examples(fit[::-1],fit[::-1])])
        altered=copy.deepcopy(fit);altered[0]['split']='test'
        with self.assertRaises(ValueError):choose_examples(altered,fit)

    def test_examples_prioritize_errors_then_agreement(self):
        fit=[row(i,'BLOCK' if i<6 else 'ALLOW',split='fit') for i in range(12)]
        for r in fit:r['prediction']=r['expected']
        for i in [0,1,6,7]:fit[i]['prediction']='ALLOW' if i<6 else 'BLOCK'
        self.assertEqual({r['id'] for r in choose_examples(fit,fit)},{'0','1','6','7'})

    def test_failures_not_dropped_and_threshold_not_fit_to_test(self):
        rr=[row(1),row(2,'BLOCK','ERROR',None)]
        scored=threshold_rows(rr,.5)
        self.assertEqual(metrics(scored)['accuracy'],.5)
        self.assertEqual(metrics(scored)['errors'],1)
        clean=[row(1,score=.1),row(2,'BLOCK','BLOCK',.9)]
        self.assertEqual(select_threshold(clean)['selected']['threshold'],.5)

    def test_gated_demonstrations_are_not_published_and_selection_still_reproduces(self):
        pp={p:dict(type='choice',instructions='Assess.',criteria={'ALLOW':'No violation','BLOCK':'Violation'})
            for p in ['brief','detailed','examples']}
        pp['examples']['instructions']+='\n\nLabeled examples illustrating this policy:\nPRIVATE_EXAMPLE'
        examples=[dict(row(1,split='fit'),prompt='PRIVATE_EXAMPLE')]
        public,info,provenance=public_policy_record('wildguard',pp,examples)
        self.assertNotIn('PRIVATE_EXAMPLE',canonical(public)+canonical(provenance))
        rr={p:[row(1),row(2,'BLOCK','BLOCK',.8)] for p in pp}
        self.assertEqual(archive_selection(public,rr,info),select_policy(pp,rr))

    def test_comparators_must_have_identical_ids_text_and_labels(self):
        target=[row(1),row(2)]
        self.assertEqual([r['id'] for r in align(target[::-1],target)],['1','2'])
        with self.assertRaises(ValueError):align(target[:1],target)
        changed=copy.deepcopy(target);changed[0]['prompt_sha256']='other'
        with self.assertRaises(ValueError):align(changed,target)


if __name__=='__main__':unittest.main()
