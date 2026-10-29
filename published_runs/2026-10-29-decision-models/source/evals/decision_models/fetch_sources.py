"""Fetch publisher source at immutable revisions, verifying recorded SHA-256s."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

KEV='2074cc44256200bb37540103fa4572901faa10f3'
CLEF='f0b7d3cd65296abfe459e6c228b618f5d8b26d2f'


def fetch(destination):
    destination=Path(destination)
    hashes=json.loads(Path(__file__).with_name('vendor-hashes.json').read_text())
    for rel,expected in hashes.items():
        url=(f'https://raw.githubusercontent.com/jaredpalmer/kev/{KEV}/'+rel.removeprefix('kev/')) if rel.startswith('kev/') else (
            f'https://huggingface.co/Cloudflare/clef-flash/resolve/{CLEF}/'+rel)
        p=destination/rel
        data=p.read_bytes() if p.exists() else urllib.request.urlopen(url,timeout=60).read()
        if hashlib.sha256(data).hexdigest()!=expected: raise ValueError('Source checksum mismatch: '+rel)
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    print(f'Verified {len(hashes)} pinned source files. Review them before executing.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--destination',required=True);a=p.parse_args();fetch(a.destination)
