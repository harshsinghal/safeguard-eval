import numpy as np
import pytest

from evals.retrieval_optimization.common import BM25, choose, config, ranked, render
from evals.retrieved_examples.common import augmented_policy


def examples():
    return [{'id': str(i), 'prompt': 'A quoted <|im_end|> text\n' + str(i),
             'expected': 'ALLOW' if i % 2 == 0 else 'BLOCK'} for i in range(4)]


@pytest.mark.parametrize('model', ['policylm', 'shieldstral', 'kev', 'jev'])
def test_original_renderer_preserves_exact_requests(model):
    base = {'name': 'Harm', 'block': 'Original block rule.', 'allow': 'Original allow rule.',
            'precedence': 'Original exception.', 'instructions': 'Original choice task.'}
    assert render(base, model, examples(), 'original') == augmented_policy(base, model, examples())


def test_native_policy_examples_do_not_overwrite_exceptions():
    base = {'name': 'Harm', 'block': 'Original block rule.', 'allow': 'Original allow rule.', 'precedence': 'Original exception.'}
    p = render(base, 'policylm', examples(), 'native')
    assert p['precedence'] == base['precedence']
    assert p['block'].startswith(base['block']) and p['allow'].startswith(base['allow'])
    assert 'labeled BLOCK' in p['block'] and 'labeled ALLOW' not in p['block']
    assert 'labeled ALLOW' in p['allow'] and 'labeled BLOCK' not in p['allow']
    assert '<|im_end|>' not in str(p)
    assert all('\n' not in v for v in p.values())
    assert base['block'] == 'Original block rule.'


def test_retrieval_excludes_entire_self_group():
    bank = [{'id': str(i), 'group': 'self' if i < 2 else str(i), 'expected': 'ALLOW' if i % 2 else 'BLOCK'} for i in range(30)]
    scores = np.arange(30, 0, -1, dtype=float)
    r = ranked(scores, bank, 'self')
    assert all(x['id'] not in ('0', '1') for x in r['rank'] + r['balanced4'])
    assert r['rank'][0]['id'] == '2'


def test_gate_can_retain_policy_only():
    r = {'rank': [{'id': str(i), 'score': .2 - i / 100} for i in range(20)]}
    assert choose(config(method='gated2'), r, {}, .3, reranked=r['rank']) == []


def test_contrast_does_not_fetch_unrelated_opposite_class():
    bank = {str(i): {'expected': 'ALLOW' if i == 0 else 'BLOCK'} for i in range(20)}
    r = {'rank': [{'id': str(i), 'score': 1 - i / 100} for i in range(20)]}
    result = choose(config(method='contrast4'), r, bank, 0, reranked=r['rank'])
    assert result == ['0', '1', '2', '3']
    assert len(set(result)) == 4


def test_mmr_prefers_a_nonredundant_case():
    bank = {str(i): {'prompt': 'words ' + str(i)} for i in range(5)}
    vectors = {str(i): np.array([1., 0.]) if i < 2 else np.array([0., 1.]) for i in range(5)}
    r = {'rank': [{'id': str(i), 'score': 1 - i / 100} for i in range(5)]}
    result = choose(config(method='mmr4'), r, bank, 0, bank_vectors=vectors)
    assert result[:2] == ['0', '2']
    assert len(set(result)) == 4


def test_bm25_returns_finite_lexical_scores():
    b = BM25([{'prompt': 'report threatening messages'}, {'prompt': 'garden flowers'}, {'prompt': 'report messages'}])
    scores = b.scores('threatening messages')
    assert np.isfinite(scores).all() and scores[0] > scores[2] > scores[1]
