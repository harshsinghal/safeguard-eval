"""Summarize recorded extraction timing; this is not a serving benchmark."""
import argparse
import json
from pathlib import Path

import numpy as np


def summarize(state):
    state = Path(state)
    result = {
        'scope': 'One L40S, BF16, batch size one, full pinned checkpoints loaded. '
                 'Per-row time includes tokenization, validation, forward, pooling '
                 'and label-score extraction. Split time also includes feature writes; '
                 'fit split includes 16 native-forward parity checks. Model loading, '
                 'checkpoint hashing, transfers and setup are not all included. '
                 'Memory is peak Torch allocation, not minimum serving VRAM. '
                 'Qwen uses fallback Torch linear attention without optional fla kernels.',
        'models': {},
    }
    for model in ['shieldstral', 'qwen']:
        result['models'][model] = {}
        for split in ['fit', 'validation', 'test']:
            folder = state / 'features' / model / split
            manifest = json.loads((folder / 'manifest.json').read_text())
            rows = json.loads((folder / 'records.json').read_text())
            seconds = np.array([r['seconds'] for r in rows])
            valid = [r for r, ok in zip(rows, manifest['valid']) if ok]
            result['models'][model][split] = {
                'n': len(rows), 'valid': len(valid),
                'split_seconds': manifest['seconds'],
                'median_row_seconds': float(np.median(seconds)),
                'p95_row_seconds': float(np.quantile(seconds, .95)),
                'peak_gpu_bytes': manifest['peak_gpu_bytes'],
                'gpu': manifest['gpu'],
                'min_tokens': min(r['tokens'] for r in valid),
                'max_tokens': max(r['tokens'] for r in valid),
                'empty_content': sum(r['empty_content'] for r in valid),
                'outer_whitespace_trimmed': sum(r['outer_whitespace_trimmed'] for r in valid),
                'top_token_outside_label_pair': sum(not r['top_token_is_label'] for r in valid),
            }
    (state / 'runtime-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', required=True)
    summarize(parser.parse_args().state)
