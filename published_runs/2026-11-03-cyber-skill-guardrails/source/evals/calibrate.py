"""Choose a score band on a complete development run, never on test labels."""
import argparse
import json
from pathlib import Path
from .run import digest, metrics, score_decision


def calibrate(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    rows = [json.loads(line) for line in (directory/'predictions.jsonl').read_text().splitlines()]
    if manifest['mode'] != 'inference' or manifest['split'] != 'dev' or not rows:
        raise ValueError('A live development run is required')
    if any(r['split'] != 'dev' or 'score' not in r for r in rows):
        raise ValueError('All development cases must have valid scores; fix errors before calibration')
    if len(rows) != len(manifest['selected_ids']) or len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Incomplete or duplicated predictions')
    grid = [i / 20 for i in range(1, 20)]
    candidates = []
    for low in grid:
        for high in grid:
            if low >= high:
                continue
            scored = [dict(r, prediction=score_decision(r['score'], low, high),
                           route=score_decision(r['score'], low, high)) for r in rows]
            summary = metrics(scored)
            candidates.append(dict(allow_below=low, block_at=high, metrics=summary))
    # Predeclared criterion: macro-F1; then coverage; then smaller band; then low/high.
    best = max(candidates, key=lambda r: (r['metrics']['macro_f1'], r['metrics']['automatic_coverage'],
                                         -(r['block_at']-r['allow_below']), -r['allow_below'], -r['block_at']))
    return dict(method='grid search on dev macro-F1; ties: coverage, narrower band, lower bounds',
                grid=grid, dev_manifest_sha256=digest(directory/'manifest.json'),
                dev_predictions_sha256=digest(directory/'predictions.jsonl'),
                selected=best, candidates=candidates)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dev_run', type=Path)
    args = parser.parse_args()
    result = calibrate(args.dev_run)
    with (args.dev_run/'calibration.json').open('x') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result['selected'], indent=2))


if __name__ == '__main__':
    main()
