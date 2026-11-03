"""Label-free query features, training-bank retrieval and native Qwen reranking."""
import argparse
import gc
import time
from .common import *


class QwenEncoder:
    def __init__(self, spec):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        self.tok = AutoTokenizer.from_pretrained(spec['model'], revision=spec['revision'], padding_side='left')
        self.model = AutoModel.from_pretrained(spec['model'], revision=spec['revision'], torch_dtype=torch.bfloat16,
                                              attn_implementation='sdpa').cuda().eval().requires_grad_(False)

    def encode(self, texts, query=False):
        torch = self.torch
        inputs = [f'Instruct: {INSTRUCTION}\nQuery:{t}' if query else t for t in texts]
        encoded = self.tok(inputs, truncation=False, padding=False)['input_ids']
        if max(map(len, encoded)) > 32768:
            raise ValueError('Embedding context exceeded; no clipping')
        result = [None] * len(encoded)
        order = sorted(range(len(encoded)), key=lambda i: len(encoded[i]))
        start = time.monotonic()
        with torch.inference_mode():
            for at in range(0, len(order), 8):
                ids = order[at:at + 8]
                b = self.tok.pad([{'input_ids': encoded[i]} for i in ids], padding=True, return_tensors='pt').to('cuda')
                h = self.model(**b, use_cache=False).last_hidden_state[:, -1, :].float()
                v = torch.nn.functional.normalize(h, p=2, dim=1).cpu().numpy()
                for i, vector in zip(ids, v):
                    result[i] = vector
        print(canonical({'embedding_rows': len(encoded), 'max_tokens': max(map(len, encoded)),
                         'seconds': time.monotonic() - start, 'query_instruction': query}), flush=True)
        return np.array(result, dtype=np.float32)


def checked_array(path):
    m = read(path.with_suffix('.json'))
    if digest(path) != m['sha256']:
        raise ValueError('Changed cached embeddings')
    return np.load(path, allow_pickle=False)


def array_write(path, value, **metadata):
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, value, allow_pickle=False)
    write(path.with_suffix('.json'), {'sha256': digest(path), 'shape': list(value.shape), **metadata})


def features(state, split, encoders=None):
    state = Path(state)
    verify(state, test=split == 'test')
    bank = rows(state / 'private-bank-expanded.jsonl')
    short = rows(state / 'private-bank-short.jsonl')
    short_ids = {r['id'] for r in short}
    ix = {r['id']: i for i, r in enumerate(bank)}
    short_ix = [ix[r['id']] for r in short]
    queries = rows(state / f'inputs/{split}.jsonl')
    groups = {r['id']: r['group'] for r in rows(state / 'metadata/smoke.jsonl.gz')} if split == 'smoke' else {}
    for name in (encoders or RETRIEVERS):
        outputs = [state / f'retrieval/{name}/{split}-{kind}.jsonl.gz' for kind in ('short', 'expanded')]
        if all(p.exists() for p in outputs):
            continue
        engine = None
        if name != 'bm25':
            folder = state / f'private-embeddings/{name}'
            bp, qp = folder / 'bank.npy', folder / f'{split}.npy'
            if name == 'e5':
                if not bp.exists():
                    from evals.retrieved_examples.retrieve import Encoder
                    engine = Encoder()
                    missing = [r for r in bank if r['id'] not in short_ids]
                    extra, _ = engine.encode([r['prompt'] for r in missing])
                    old = np.load(state / 'private-e5-cache/bank.npy', allow_pickle=False)
                    values = {r['id']: v for r, v in zip(short, old)}
                    values.update({r['id']: v for r, v in zip(missing, extra)})
                    array_write(bp, np.array([values[r['id']] for r in bank]), encoder=ENCODERS[name])
                if not qp.exists():
                    old = np.load(state / f'private-e5-cache/{split}.npy', allow_pickle=False)
                    array_write(qp, old, encoder=ENCODERS[name], prior_cache=True)
            else:
                if not bp.exists() or not qp.exists() or not (folder / 'fitting-queries.npy').exists():
                    engine = QwenEncoder(ENCODERS[name])
                if not bp.exists():
                    array_write(bp, engine.encode([r['prompt'] for r in bank]), encoder=ENCODERS[name])
                if not qp.exists():
                    array_write(qp, engine.encode([r['prompt'] for r in queries], query=True), encoder=ENCODERS[name])
                if not (folder / 'fitting-queries.npy').exists():
                    array_write(folder / 'fitting-queries.npy', engine.encode([r['prompt'] for r in short], query=True), encoder=ENCODERS[name])
            bx, qx = checked_array(bp), checked_array(qp)
            if len(bx) != len(bank) or len(qx) != len(queries):
                raise ValueError('Embedding alignment mismatch')
            if not np.allclose(np.linalg.norm(bx, axis=1), 1, atol=1e-5):
                raise ValueError('Unnormalized embeddings')
            fit_x = bx[short_ix] if name == 'e5' else checked_array(folder / 'fitting-queries.npy')
        threshold_path = state / f'retrieval/{name}/gate.json'
        for kind, bb, indexes in (('short', short, short_ix), ('expanded', bank, list(range(len(bank))))):
            dest = state / f'retrieval/{name}/{split}-{kind}.jsonl.gz'
            if dest.exists():
                continue
            lexical = BM25(bb) if name == 'bm25' else None
            vectors = None if name == 'bm25' else bx[indexes]
            records = []
            for j, q in enumerate(queries):
                scores = lexical.scores(q['prompt']) if lexical else vectors @ qx[j]
                rr = ranked(scores, bb, groups.get(q['id']))
                records.append({'id': q['id'], 'prompt_sha256': q['prompt_sha256'], **rr})
            write_rows(dest, records)
            if kind == 'short' and not threshold_path.exists():
                top = []
                for j, r in enumerate(short):
                    scores = lexical.scores(r['prompt']) if lexical else vectors @ fit_x[j]
                    scores[j] = -np.inf
                    top.append(float(np.max(scores)))
                write(threshold_path, {'threshold': float(np.quantile(top, .1)), 'quantile': .1,
                                       'n': len(top), 'source': 'short fitting bank, own group excluded',
                                       'top_scores_sha256': hash_value(top)})
            write(dest.with_suffix('.manifest.json'), {'sha256': digest(dest), 'n': len(records), 'bank': kind,
                  'retriever': name, 'created_utc': now(), 'query_sha256': digest(state / f'inputs/{split}.jsonl')})
            print(canonical({'retriever': name, 'split': split, 'bank': kind, 'rows': len(records)}), flush=True)
        del engine
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except ImportError:
            pass


def rerank(state, split):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    state = Path(state)
    verify(state, test=split == 'test')
    selected = read(state / 'selection-retriever.json')['selected']
    names = sorted({x['retriever'] for x in selected.values()})
    if split == 'test':
        configs = read(state / 'freeze.json')['configurations']
        names = sorted({c['retriever'] for mm in configs.values() for c in mm.values()
                        if c['method'] in ('rerank2', 'rerank4', 'contrast4', 'gated2')})
    if not names:
        return
    bank = {r['id']: r for r in rows(state / 'private-bank-short.jsonl')}
    query = {r['id']: r for r in rows(state / f'inputs/{split}.jsonl')}
    tok = AutoTokenizer.from_pretrained(RERANKER['model'], revision=RERANKER['revision'], padding_side='left')
    model = AutoModelForCausalLM.from_pretrained(RERANKER['model'], revision=RERANKER['revision'],
            torch_dtype=torch.bfloat16, attn_implementation='sdpa').cuda().eval().requires_grad_(False)
    yes, no = [tok.convert_tokens_to_ids(t) for t in ('yes', 'no')]
    prefix = ('<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. '
              'Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n')
    suffix = '<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n'
    before = tok.encode(prefix, add_special_tokens=False)
    after = tok.encode(suffix, add_special_tokens=False)
    for name in names:
        dest = state / f'rerank/{name}/{split}.jsonl.gz'
        if dest.exists():
            continue
        ranks = rows(state / f'retrieval/{name}/{split}-short.jsonl.gz')
        by_query = {}
        batch, keys = [], []
        def flush():
            if not batch:
                return
            b = tok.pad([{'input_ids': ids} for ids in batch], padding=True, return_tensors='pt').to('cuda')
            with torch.inference_mode():
                h = model.model(**b, use_cache=False).last_hidden_state[:, -1, :]
                logits = model.lm_head(h).float()[:, [yes, no]]
                values = logits.softmax(-1)[:, 0].cpu().tolist()
            for (qid, bid), score in zip(keys, values):
                by_query.setdefault(qid, []).append({'id': bid, 'score': score})
            batch.clear()
            keys.clear()
        for n, r in enumerate(ranks):
            for item in r['rank']:
                # JSON escaping protects special-token boundaries without following source instructions.
                body = f'<Instruct>: {RERANK_INSTRUCTION}\n<Query>: {escaped(query[r["id"]]["prompt"])}\n<Document>: {escaped(bank[item["id"]]["prompt"])}'
                ids = before + tok.encode(body, add_special_tokens=False) + after
                if len(ids) > 32768:
                    raise ValueError('Reranker context exceeded; no clipping')
                # Small token-budgeted batches keep long cases from exhausting memory.
                if batch and (len(batch) >= 16 or max(len(ids), max(map(len, batch))) * (len(batch) + 1) > 16000):
                    flush()
                batch.append(ids)
                keys.append((r['id'], item['id']))
            if n % 128 == 0:
                print(canonical({'reranker': name, 'split': split, 'targets_done': n, 'targets': len(ranks)}), flush=True)
        flush()
        result = [{'id': r['id'], 'prompt_sha256': r['prompt_sha256'], 'candidates': by_query[r['id']]} for r in ranks]
        write_rows(dest, result)
        write(dest.with_suffix('.manifest.json'), {'sha256': digest(dest), 'model': RERANKER,
              'n': len(result), 'candidate_pairs': sum(len(r['candidates']) for r in result), 'created_utc': now()})
        print(canonical({'rerank_complete': name, 'split': split, 'n': len(result)}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['encode', 'rerank'])
    p.add_argument('--state', required=True)
    p.add_argument('--split', choices=['smoke', 'validation', 'test'], required=True)
    p.add_argument('--encoders', nargs='+', choices=RETRIEVERS)
    a = p.parse_args()
    if a.action == 'encode':
        features(a.state, a.split, a.encoders)
    else:
        rerank(a.state, a.split)
