from pathlib import Path
import json
from transformers import AutoTokenizer
path='/root/.cache/huggingface/hub/models--allenai--wildguard/snapshots/cbba4823f3e8020e5a74a5e29bf85072def6f2ff'
slow=AutoTokenizer.from_pretrained(path,use_fast=False,local_files_only=True)
fast=AutoTokenizer.from_pretrained(path,use_fast=True,local_files_only=True)
assert not slow.is_fast and fast.is_fast
# Server uses this tokenizer only to decode output IDs. Verify vocabulary identity.
assert slow.get_vocab()==fast.get_vocab()
fast.save_pretrained('/root/wildguard-tokenizer')
Path('/root/tokenizer-verification.json').write_text(json.dumps(dict(slow_class=type(slow).__name__,fast_class=type(fast).__name__,vocabulary_identical=True,bos_token_id=slow.bos_token_id,input_tokenization='original slow tokenizer',output_decoding='converted fast tokenizer, same vocabulary'),indent=2))
print('WildGuard tokenizer vocabulary verified')
