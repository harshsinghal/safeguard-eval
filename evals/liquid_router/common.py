"""Versioned routing labels, immutable registration, and text-free evidence."""
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = "LiquidAI/LFM2.5-Encoder-350M"
REVISION = "b886781f7c6f10ca9b7096e21b83e30a073c2f39"
SEED = 20261105
MAX_TOKENS = 256
CATEGORIES = ["agent_safety", "code_safety", "cyber_safety", "harmful_requests",
              "hate_speech", "prompt_injection", "skill_safety"]
TRACK_CATEGORY = {
    "agent_actions": "agent_safety", "agent_runs": "agent_safety",
    "source_code": "code_safety", "cyber_requests": "cyber_safety",
    "harmful_requests": "harmful_requests", "hate_speech": "hate_speech",
    "injection_deepset": "prompt_injection", "injection_xtram": "prompt_injection",
    "benign_lookalikes": "prompt_injection", "jailbreak_attempts": "prompt_injection",
    "injection_context": "prompt_injection", "skill_text": "skill_safety",
    "skill_packages": "skill_safety",
}

def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()

def digest(path):
    return sha(Path(path).read_bytes())

def read(path):
    return json.loads(Path(path).read_text())

def rows(path):
    import gzip
    b = Path(path).read_bytes()
    if str(path).endswith(".gz"):
        b = gzip.decompress(b)
    return [json.loads(line) for line in b.decode().splitlines() if line.strip()]

def write(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+"\n")

def jsonl(path, values):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(v, sort_keys=True, ensure_ascii=False, allow_nan=False)+"\n" for v in values))

def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

def bounded_tokens(ids, cap=MAX_TOKENS):
    if cap < 4:
        raise ValueError("Token cap too small")
    if len(ids) <= cap:
        return ids
    middle = cap // 4; first = (cap-middle)//2; last = cap-first-middle
    center = len(ids)//2
    return ids[:first]+ids[center-middle//2:center-middle//2+middle]+ids[-last:]

def code_hashes():
    paths = sorted((ROOT/"evals/liquid_router").glob("*.py"))
    paths += [ROOT/"docs/liquid-router/PLAN.md", ROOT/"docs/liquid-router/protocol.json"]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}

def check_registration(state, test=False):
    state = Path(state); r = read(state/"registration.json")
    if code_hashes() != r["code_hashes"]:
        raise ValueError("Registered code changed; record an amendment before continuing")
    for split in ("fit", "validation", "test") if test else ("fit", "validation"):
        p = state/"data"/(split+".jsonl")
        if digest(p) != r["input_hashes"][split]:
            raise ValueError("Registered inputs changed: "+split)
    return r

def rank_candidates(probabilities, count):
    import numpy as np
    p = np.asarray(probabilities, dtype=float)
    if p.shape != (len(CATEGORIES),) or not np.isfinite(p).all() or (p < 0).any() or abs(p.sum()-1)>1e-4:
        raise ValueError("Invalid category distribution")
    if not 1 <= count <= len(CATEGORIES):
        raise ValueError("Invalid candidate count")
    return [CATEGORIES[i] for i in np.argsort(-p, kind="stable")[:count]]
