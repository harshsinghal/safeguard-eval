"""Guard against label leakage, silent failure scoring, and unbounded API use."""
import tempfile
import unittest
from pathlib import Path
from .api import Budget,CAP,RESERVE,parse,payload
from .common import MODELS,measures,write,jsonl,read,rows
from .policies import initial,render,with_examples
from .data import normalize
from .report import intervals

class Contracts(unittest.TestCase):
    def test_native_rendering(self):
        p=with_examples([{'prompt':'line one\nline two','expected':'BLOCK'}])
        native=render(p,'policylm')
        self.assertNotIn('\n',native['block'])
        self.assertIn('\\n',native['block'])
        for slug in ('jev','kev','clef'):
            q=render(p,slug)
            self.assertEqual(set(q),{'type','instructions','criteria'})
            self.assertEqual(list(q['criteria']),['ALLOW','BLOCK'])

    def test_labels_and_metadata_never_enter_payload(self):
        for slug in ('jev','safeguard'):
            j={'body':{'content':'Hello there','policy':render(initial()['brief'],slug)},
               'expected':'SECRET_GOLD','dataset':'SECRET_DATASET','split':'SECRET_SPLIT'}
            body=payload(j,slug)
            self.assertNotIn('SECRET_',str(body))

    def test_strict_safeguard_parser(self):
        x={'model':MODELS['safeguard']['model'],'provider':'Groq',
           'choices':[{'finish_reason':'stop','message':{'content':'{"decision":"ALLOW"}'}}]}
        self.assertEqual(parse(x,'safeguard')['prediction'],'ALLOW')
        x['choices'][0]['finish_reason']='length'
        with self.assertRaises(ValueError):parse(x,'safeguard')
        x['choices'][0]['finish_reason']='stop';x['provider']='Another provider'
        with self.assertRaises(ValueError):parse(x,'safeguard')

    def test_unresolved_is_never_a_correct_block(self):
        m=measures([{'expected':'ALLOW','prediction':'ALLOW'},{'expected':'BLOCK','prediction':'ERROR'}])
        self.assertEqual(m['accuracy'],.5);self.assertEqual(m['balanced_accuracy'],.5)
        self.assertEqual(m['recall'],0);self.assertEqual(m['unresolved'],1);self.assertIsNone(m['mcc'])

    def test_one_class_has_no_fake_balanced_metrics(self):
        m=measures([{'expected':'ALLOW','prediction':'BLOCK'}])
        self.assertIsNone(m['balanced_accuracy']);self.assertIsNone(m['macro_f1'])
        self.assertEqual(m['false_positive_rate'],1)

    def test_budget_reservations_survive_reopening(self):
        with tempfile.TemporaryDirectory() as d:
            b=Budget(Path(d)/'ledger.sqlite','jev');b.reserve('one')
            self.assertAlmostEqual(Budget(b.path,'jev').totals()['total_accounted_usd'],RESERVE['jev'])
            b.settle('one',.0001,'reported')
            with self.assertRaises(ValueError):b.settle('one',.0001,'reported')
            with b.connect() as db:
                db.execute('INSERT INTO requests VALUES (?,?,NULL,?)',('full',CAP['jev'],'pending'))
            with self.assertRaises(RuntimeError):b.reserve('cannot-spend')

    def test_normalization_is_only_an_audit_utility(self):
        self.assertEqual(normalize('  Ａ B\n C '),'a b c')

    def test_bootstrap_pairing_and_single_class(self):
        rr=[{'id':str(i),'group':str(i),'expected':'ALLOW','prediction':'ALLOW'} for i in range(4)]
        systems={slug+'/'+arm:rr for slug in MODELS for arm in ('brief','selected')}
        result=intervals(rr,systems,repetitions=64)
        self.assertEqual(result['selected_minus_brief']['jev']['accuracy'],[0.,0.])
        self.assertIsNone(result['intervals']['jev/selected']['attack_recall'])

    def test_selection_gate_and_end_to_end_job_contract(self):
        from .study import register,author,jobs,freeze
        from .infer import load_jobs
        with tempfile.TemporaryDirectory() as d:
            s=Path(d)
            for name in ('source-manifest.json','data-audit.json'):write(s/name,{})
            for split in ('fit','validation','test'):
                rr=[dict(id=f'{split}-{i}',dataset='deepset' if i<2 else 'safeguard',
                         group=f'{split}-{i}',split=split,prompt='Example '+str(i),prompt_sha256=str(i),
                         expected='BLOCK' if i%2 else 'ALLOW') for i in range(4)]
                jsonl(s/f'data/{split}.jsonl',rr)
                jsonl(s/f'metadata/{split}.jsonl',({k:v for k,v in r.items() if k!='prompt'} for r in rr))
            register(s);jobs(s,'fit')
            with self.assertRaises(FileNotFoundError):jobs(s,'test')
            for slug in MODELS:
                jj=load_jobs(s,slug,'fit','brief')
                jsonl(s/f'predictions/{slug}/fit/brief.jsonl',
                    ({**{k:v for k,v in j.items() if k!='body'},'prediction':j['expected']} for j in jj))
            author(s);jobs(s,'validation')
            for slug in MODELS:
                for pid in read(s/f'policies/{slug}/candidates.json'):
                    jj=load_jobs(s,slug,'validation',pid)
                    jsonl(s/f'predictions/{slug}/validation/{pid}.jsonl',
                        ({**{k:v for k,v in j.items() if k!='body'},
                          'prediction':j['expected'] if pid=='examples' else 'ALLOW'} for j in jj))
            freeze(s)
            self.assertEqual(set(read(s/'freeze.json')['selected'].values()),{'examples'})
            jobs(s,'test')
            jj=load_jobs(s,'jev','test','examples')
            self.assertEqual(set(jj[0]['body']),{'content','policy'})
            self.assertEqual(len(jj),4)
            p=s/'policies/jev/candidates.json';p.write_text(p.read_text()+' ')
            with self.assertRaises(ValueError):load_jobs(s,'jev','test','examples')

if __name__=='__main__':unittest.main()
