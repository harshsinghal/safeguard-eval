"""Portable CPU Liquid features and four independent correctness heads."""
from pathlib import Path
import math
import re
import time
import numpy as np
from evals.liquid_router.common import bounded_tokens
from evals.routed_guard.common import MODELS, ORDER, canonical, digest, labels_for, policy_hash, read

SEMANTIC_FIELDS = ('purpose', 'precedence', 'allow', 'block', 'review')
PROMPT_TOKENS, POLICY_TOKENS = 256, 192


def policy_text(policy, labels):
    return canonical(dict(policy={k:policy.get(k, '') for k in SEMANTIC_FIELDS}, decisions=list(labels)))


def encode_pair(tokenizer, content, policy, labels):
    if not isinstance(content, str) or not content.strip() or len(content.encode()) > 1024*1024:
        raise ValueError('Expected nonempty text <=1 MiB')
    prompt = tokenizer(content, add_special_tokens=False, truncation=False)['input_ids']
    rules = tokenizer(policy_text(policy, labels), add_special_tokens=False, truncation=False)['input_ids']
    sep = tokenizer.sep_token_id
    if sep is None: sep = tokenizer.eos_token_id
    if sep is None: raise ValueError('Tokenizer requires a separator')
    ids = bounded_tokens(prompt, PROMPT_TOKENS)+[sep]+bounded_tokens(rules, POLICY_TOKENS)+[sep]
    return ids, dict(prompt_tokens=len(prompt), policy_tokens=len(rules), used_tokens=len(ids),
                     prompt_truncated=len(prompt)>PROMPT_TOKENS, policy_truncated=len(rules)>POLICY_TOKENS)


def structure(content):
    # Features describe only caller input; no source labels, IDs, or guard outcomes.
    return np.array([math.log1p(len(content)), math.log1p(content.count('\n')),
        math.log1p(content.count('```')), math.log1p(len(re.findall(r'[{};]', content))),
        math.log1p(len(re.findall(r'https?://', content))),
        math.log1p(len(re.findall(r'(?im)^\s*(user|assistant|system|tool)\s*:', content))),
        float(content.lstrip().startswith(('{','['))),
        math.log1p(len(re.findall(r'(?i)\b(def|function|import|class|SELECT)\b', content))),
        math.log1p(len(re.findall(r'<[^>]+>', content))),
        math.log1p(content.count('"'))], dtype=np.float64)


class Features:
    def __init__(self, checkpoint=None, threads=4):
        import torch
        from evals.liquid_router.model import load_initial
        torch.set_num_threads(threads)
        if checkpoint is None:
            model, self.tokenizer = load_initial('cpu'); self.body = model.body
        else:
            from transformers import AutoModel, AutoTokenizer
            checkpoint = Path(checkpoint)
            self.tokenizer = AutoTokenizer.from_pretrained(checkpoint/'tokenizer', local_files_only=True)
            self.body, info = AutoModel.from_pretrained(checkpoint/'backbone', local_files_only=True,
                trust_remote_code=True, dtype=torch.float32, attn_implementation='sdpa', output_loading_info=True)
            if any(info.get(k) for k in ('missing_keys','unexpected_keys','mismatched_keys','error_msgs')):
                raise ValueError('Encoder did not load exactly')
        self.body.eval()
        for p in self.body.parameters(): p.requires_grad_(False)

    def one(self, content, policy, labels):
        import torch
        from evals.liquid_router.model import batch
        ids, trace = encode_pair(self.tokenizer, content, policy, labels)
        b = batch(self.tokenizer, [ids], 'cpu')
        with torch.inference_mode():
            hidden = self.body(**b, use_cache=False, return_dict=True).last_hidden_state.float()
            mask = b['attention_mask'].unsqueeze(-1).float()
            pooled = ((hidden*mask).sum(1)/mask.sum(1).clamp_min(1))[0].numpy()
        return np.concatenate([pooled.astype(np.float64), structure(content)]), trace

    def save(self, path):
        import inspect, shutil
        path = Path(path); path.mkdir(parents=True, exist_ok=False)
        self.body.save_pretrained(path/'backbone', safe_serialization=True)
        code = Path(inspect.getfile(type(self.body)))
        shutil.copyfile(code, path/'backbone'/code.name)
        self.tokenizer.save_pretrained(path/'tokenizer')


def probabilities(x, head):
    z = ((np.asarray(x)-head['mean'])/head['scale']) @ np.asarray(head['coef']).T + head['intercept']
    z = np.clip(z, -40, 40)
    return 1/(1+np.exp(-z))


def route(probs, config, policy_digest):
    p = np.asarray(probs, dtype=float)
    if p.shape != (len(ORDER),) or not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Invalid correctness estimates')
    default = config['default_model']
    if default not in ORDER: raise ValueError('Unknown default')
    if policy_digest not in config['supported_policy_hashes']:
        return default, 'unsupported_policy_default'
    candidates = [default]+[m for m in config['enabled_models'] if m!=default]
    if any(m not in ORDER for m in candidates): raise ValueError('Unknown guard')
    # Default wins exact ties, then stable catalog order.
    best = max(candidates, key=lambda m:(p[ORDER.index(m)], m==default, -ORDER.index(m)))
    if best!=default and p[ORDER.index(best)]-p[ORDER.index(default)] > config['switch_margin']:
        return best, 'competence_route'
    return default, 'competence_default'


class CompetenceRouter:
    def __init__(self, checkpoint, threads=4):
        checkpoint = Path(checkpoint); self.config = read(checkpoint/'competence.json')
        if self.config['models'] != MODELS or self.config['order'] != list(ORDER):
            raise ValueError('Guard versions differ from fitted competence contract')
        if self.config['feature_contract'] != dict(prompt_tokens=PROMPT_TOKENS, policy_tokens=POLICY_TOKENS, semantic_fields=list(SEMANTIC_FIELDS), structure_dimensions=10):
            raise ValueError('Feature contract mismatch')
        for relative, expected in self.config['artifact_hashes'].items():
            if digest(checkpoint/relative)!=expected: raise ValueError('Checkpoint integrity failure')
        self.head = self.config['head']; self.features = Features(checkpoint, threads)

    def predict(self, content, policy, labels):
        started = time.perf_counter(); ph = policy_hash(policy)
        if tuple(labels) not in (('ALLOW','BLOCK'), ('ALLOW','BLOCK','REVIEW')):
            raise ValueError('Unknown decision contract')
        # The hash also binds the allowed decisions; metadata cannot grant support.
        key = policy_contract_hash(policy, labels)
        if key not in self.config['supported_policy_hashes']:
            return dict(selected_model=self.config['default_model'], route_reason='unsupported_policy_default',
                fallback_required=True, guard_correctness_probabilities=None, moderation_decision=None,
                policy_sha256=ph, router_ms=1000*(time.perf_counter()-started))
        x, trace = self.features.one(content, policy, labels)
        p = probabilities(x, self.head); model, reason = route(p, self.config, key)
        return dict(selected_model=model, route_reason=reason, fallback_required=model==self.config['default_model'],
            guard_correctness_probabilities={m:float(v) for m,v in zip(ORDER,p)},
            moderation_decision=None, policy_sha256=ph, router_ms=1000*(time.perf_counter()-started), **trace)


def policy_contract_hash(policy, labels):
    # Hash only meaningful policy text and the declared label set; IDs are not features.
    from evals.routed_guard.common import sha
    return sha(policy_text(policy, labels))
