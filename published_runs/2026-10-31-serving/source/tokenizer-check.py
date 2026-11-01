import hashlib,json
from pathlib import Path
from transformers import AutoTokenizer
from evals.wildguard.run import WILDGUARD_FORMAT
p=Path('/root/serving-state');t=AutoTokenizer.from_pretrained('allenai/wildguard',revision='cbba4823f3e8020e5a74a5e29bf85072def6f2ff',use_fast=False)
records=[]
for part in ['tune','measure']:
 for line in (p/'inputs'/f'{part}.jsonl').read_text().splitlines():
  r=json.loads(line);ids=t(WILDGUARD_FORMAT.format(prompt=r['prompt']),add_special_tokens=True)['input_ids']
  assert ids[0]==t.bos_token_id
  records.append(dict(id=r['id'],prompt_sha256=r['prompt_sha256'],tokens=len(ids),token_ids_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()))
label='fast' if t.is_fast else 'slow'
out=dict(tokenizer_class=type(t).__name__,is_fast=t.is_fast,bos_token_id=t.bos_token_id,records=records)
(p/'runtime'/f'wildguard-tokenizer-{label}.json').write_text(json.dumps(out,indent=2)+'\n')
print(label,type(t).__name__,len(records),'input token hashes recorded')
