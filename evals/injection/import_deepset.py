import json,hashlib,urllib.request,difflib
from pathlib import Path
import pyarrow.parquet as pq
p=Path(__file__).resolve().parent; rev='4f61ecb038e9c3fb77e21034b22511b523772cdd';base=f'https://huggingface.co/datasets/deepset/prompt-injections/resolve/{rev}/'
files={'dev':'data/train-00000-of-00001-9564e8b05b4757ab.parquet','test':'data/test-00000-of-00001-701d16158af87368.parquet'}
rows=[];seen={};removed=[]; hashes={}
# Keep official test intact where possible; purge matching development cases.
for split in ['test','dev']:
 f=Path(__import__('tempfile').gettempdir())/('safeguard-deepset-'+split+'.parquet');f.write_bytes(urllib.request.urlopen(base+files[split]).read());hashes[split]=hashlib.sha256(f.read_bytes()).hexdigest()
 for i,r in enumerate(pq.read_table(f).to_pylist()):
  norm=' '.join(r['text'].casefold().split()); ident=f'deepset-{split}-{i:03}'
  near=next((k for k in seen if norm==k or (split=='dev' and seen[k]['split']=='test' and difflib.SequenceMatcher(None,norm,k,autojunk=False).ratio()>=.9)),None)
  if near is not None:removed.append(dict(id=ident,duplicate_of=seen[near]['id'],label_conflict=r['label']!=seen[near]['label']));continue
  seen[norm]=dict(id=ident,split=split,label=r['label'])
  rows.append(dict(id=ident,group=ident,prompt=r['text'],expected='BLOCK' if r['label'] else 'ALLOW',split=split,tradition='not_applicable',challenge='upstream_binary',rationale='Original upstream binary label, unchanged; may disagree with our explicit policy.',source=f'deepset/prompt-injections@{rev}',annotation_status='upstream_label_unadjudicated',policy_id='prompt-injection-binary-v1',source_row=i,source_split='train' if split=='dev' else 'test'))
(p/'deepset.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
meta=dict(dataset='deepset/prompt-injections',revision=rev,source_url='https://huggingface.co/datasets/deepset/prompt-injections',authors='deepset / upstream contributors',license_note='Top-level card declares Apache-2.0; nested dataset_info declares CC-BY-4.0. Attribution retained; this is not a claim that the discrepancy is resolved.',parquet_sha256=hashes,removed=removed,dedup_rule='Keep test first; exact normalized duplicates removed within/across splits; dev/test SequenceMatcher >=0.90 removed from dev. Does not guarantee semantic deduplication.',counts={s:sum(r['split']==s for r in rows) for s in files})
(p/'provenance.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta,indent=2))
