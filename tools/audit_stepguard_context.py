"""Count source inputs without displaying examples, labels, or loading model weights."""
import argparse
import hashlib
import json
import math
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from importlib.metadata import version
from pathlib import Path

DATASET_REVISION = "aadeae009800d8fbcd145575f1d1a6b37abb0950"
TOKENIZER_REVISION = "1001bb4d826a52d1f399e183466143f4da7b741b"
DATASET_FILE = "sft3k/agentguard_sft3k_sharegpt.jsonl"


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main():
    from tokenizers import Tokenizer

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    urls = [
        f"https://huggingface.co/datasets/ninty-seven/stepguard_data/resolve/{DATASET_REVISION}/{DATASET_FILE}",
        f"https://huggingface.co/Qwen/Qwen3.5-4B-Base/resolve/{TOKENIZER_REVISION}/tokenizer.json",
    ]
    with ThreadPoolExecutor(max_workers=2) as executor:
        source, tokenizer_bytes = executor.map(fetch, urls)
    tokenizer = Tokenizer.from_str(tokenizer_bytes.decode())
    tokenizer.no_truncation()
    tokenizer.no_padding()
    inputs = []
    for line in source.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        human = [turn["value"] for turn in row["conversations"] if turn["from"] == "human"]
        if len(human) != 1 or not isinstance(human[0], str):
            raise ValueError("Expected exactly one source human input")
        inputs.append(human[0])
    counts = sorted(len(item.ids) for item in tokenizer.encode_batch(inputs, add_special_tokens=False))
    if not counts:
        raise ValueError("Empty input population")
    result = {
        "kind": "input_length_audit_only",
        "dataset": "ninty-seven/stepguard_data",
        "dataset_revision": DATASET_REVISION,
        "path": DATASET_FILE,
        "dataset_file_sha256": hashlib.sha256(source).hexdigest(),
        "tokenizer": "Qwen/Qwen3.5-4B-Base",
        "tokenizer_revision": TOKENIZER_REVISION,
        "tokenizer_file_sha256": hashlib.sha256(tokenizer_bytes).hexdigest(),
        "tokenizers_version": version("tokenizers"),
        "counted": "Full source human input, including source task instructions; excludes the assistant reviewer target. No added model wrapper or new policy.",
        "not_a_measure_of": "Per-model eligibility, model quality, or inference performance. Other tokenizers and wrappers differ.",
        "labels_or_target_text_printed": False,
        "inference_runs": 0,
        "paid_compute_usd": 0,
        "all": {
            "n": len(counts), "min": counts[0],
            **{f"p{q}": counts[math.ceil(q / 100 * len(counts)) - 1] for q in (50, 95, 99)},
            "max": counts[-1],
            "at_or_below": {str(n): sum(v <= n for v in counts)
                            for n in (1024, 1536, 2048, 6144, 7168, 8192, 14336, 16384, 30720, 32768)},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
