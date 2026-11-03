import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile
from evals.malicious_artifacts.common import view,hash_value
from evals.malicious_artifacts.data import member_bytes,sample
from evals.malicious_artifacts.policies import policies
from evals.malicious_artifacts.infer import jobs,prediction
from evals.malicious_artifacts.common import jsonl,rows
from evals.malicious_artifacts.report import intervals

class Contracts(unittest.TestCase):
    def test_unicode_line_separators_are_not_records(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rows.jsonl';original=[dict(text='a\u2028b\u2029c\u0085d'),dict(text='next')]
            jsonl(p,original);self.assertEqual(rows(p),original)

    def test_view_preserves_edges_and_utf8(self):
        source='start'+'界'*5000+'finish';bounded,clipped=view(source)
        self.assertTrue(clipped);self.assertTrue(bounded.startswith('start'));self.assertTrue(bounded.endswith('finish'))
        self.assertLess(len(bounded.encode()),8100)
        self.assertEqual(view('short'),('short',False))

    def test_archive_is_inert_and_rejects_links(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'sample.tar'
            with tarfile.open(p,'w') as t:
                info=tarfile.TarInfo('code.py');payload=b'raise RuntimeError("never execute")';info.size=len(payload);t.addfile(info,io.BytesIO(payload))
                link=tarfile.TarInfo('link');link.type=tarfile.SYMTYPE;link.linkname='/etc/passwd';t.addfile(link)
            self.assertEqual(member_bytes(p,'code.py'),payload)
            with self.assertRaises(ValueError):member_bytes(p,'link')
            with self.assertRaises(ValueError):member_bytes(p,'../code.py')
            self.assertEqual(list(Path(d).iterdir()),[p])

    def test_request_has_no_metadata_or_labels(self):
        with tempfile.TemporaryDirectory() as d:
            r=dict(id='test',prompt='artifact',prompt_sha256=hash_value('artifact'),expected='BLOCK',group='secret-group',split='validation')
            jsonl(Path(d)/'data/code/validation.jsonl',[r])
            p=policies('code','kev')['brief'];_,jj,n=jobs(d,'kev','code','validation','brief',p)
            self.assertEqual(set(jj[0]['body']),{'content','policy'})
            self.assertEqual(jj[0]['body']['content'],'artifact')
            result=prediction(jj[0],dict(prediction='ALLOW',score=.2),'kev')
            self.assertNotIn('body',result);self.assertNotIn('prompt',result)

    def test_fixed_candidates_native_fields(self):
        for task in ('code','skills'):
            for slug in ('policylm','shieldstral','qwen','jev','kev','clef'):
                pp=policies(task,slug);self.assertEqual(set(pp),{'brief','structured','evidence'})
                if slug in ('jev','kev','clef'):self.assertEqual(set(pp['brief']['criteria']),{'ALLOW','BLOCK'})

    def test_sampling_and_paired_intervals(self):
        rr=[dict(id=str(i),expected='BLOCK' if i%2 else 'ALLOW',prediction='BLOCK' if i%2 else 'ALLOW',group=str(i//2)) for i in range(20)]
        self.assertEqual(sample(rr,10),sample(list(reversed(rr)),10))
        ci=intervals(rr,rr,draws=100)
        self.assertEqual(ci['balanced_accuracy_ci95'],[1.,1.]);self.assertEqual(ci['policy_delta_ci95'],[0.,0.])

if __name__=='__main__':unittest.main()
