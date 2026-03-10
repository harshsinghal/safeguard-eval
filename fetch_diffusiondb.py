"""
Fetch sample prompts from DiffusionDB dataset from Hugging Face
Dataset: https://huggingface.co/datasets/poloclub/diffusiondb

Uses metadata.parquet file for fast access to prompts without downloading images.
"""

import pandas as pd
import argparse
import json
from pathlib import Path
from urllib.request import urlretrieve
import os


METADATA_URL = "https://huggingface.co/datasets/poloclub/diffusiondb/resolve/main/metadata.parquet"
METADATA_LARGE_URL = "https://huggingface.co/datasets/poloclub/diffusiondb/resolve/main/metadata-large.parquet"
METADATA_FILE = "metadata.parquet"
METADATA_LARGE_FILE = "metadata-large.parquet"


def download_metadata(use_large=False, force=False):
    """
    Download metadata file if not already present

    Args:
        use_large: Use large dataset (14M images) instead of 2M
        force: Force re-download even if file exists
    """
    url = METADATA_LARGE_URL if use_large else METADATA_URL
    filename = METADATA_LARGE_FILE if use_large else METADATA_FILE

    if os.path.exists(filename) and not force:
        print(f"Using existing {filename}")
        return filename

    print(f"Downloading {filename} from Hugging Face...")
    print(f"URL: {url}")
    print("This is a one-time download (file will be cached locally)")

    urlretrieve(url, filename)
    file_size = os.path.getsize(filename) / (1024 * 1024)  # Size in MB
    print(f"Downloaded {filename} ({file_size:.1f} MB)")

    return filename


def fetch_diffusiondb_samples(num_samples=1000, output_file="diffusiondb_samples.json",
                               use_large=False, random_sample=True, filter_nsfw=None):
    """
    Fetch samples from DiffusionDB metadata

    Args:
        num_samples: Number of samples to fetch
        output_file: Output JSON file path
        use_large: Use large dataset (14M) instead of 2M
        random_sample: Randomly sample (True) or take first N (False)
        filter_nsfw: Filter by NSFW status - None (all), True (only NSFW), False (only safe)
    """
    print(f"Loading DiffusionDB dataset from Hugging Face...")
    print(f"Dataset: {'Large (14M)' if use_large else '2M'}")
    print(f"Sampling: {'Random' if random_sample else 'Sequential'}")
    if filter_nsfw is not None:
        print(f"NSFW filter: {'Only NSFW' if filter_nsfw else 'Only Safe'}")
    print()

    # Download metadata if needed
    metadata_file = download_metadata(use_large)

    # Load metadata
    print(f"\nLoading metadata from {metadata_file}...")
    df = pd.read_parquet(metadata_file)
    total_prompts = len(df)
    print(f"Total prompts in dataset: {total_prompts:,}")

    # Filter by NSFW if requested
    if filter_nsfw is not None:
        # Use prompt_nsfw column for filtering
        df = df[df['prompt_nsfw'] == (1.0 if filter_nsfw else 0.0)]
        print(f"After NSFW filter: {len(df):,} prompts")

    # Sample
    if num_samples > len(df):
        print(f"Warning: Requested {num_samples} samples but only {len(df)} available. Using all.")
        num_samples = len(df)

    if random_sample:
        sampled_df = df.sample(n=num_samples, random_state=42)
    else:
        sampled_df = df.head(num_samples)

    print(f"Sampled {num_samples} prompts")

    # Convert to list of dicts
    prompts = []
    for idx, row in sampled_df.iterrows():
        prompt_data = {
            "id": len(prompts),
            "prompt": row.get("prompt", ""),
            "seed": int(row.get("seed", 0)) if pd.notna(row.get("seed")) else None,
            "step": int(row.get("step", 0)) if pd.notna(row.get("step")) else None,
            "cfg": float(row.get("cfg", 0.0)) if pd.notna(row.get("cfg")) else None,
            "sampler": row.get("sampler", ""),
            "image_nsfw": float(row.get("image_nsfw", 0.0)) if pd.notna(row.get("image_nsfw")) else 0.0,
            "prompt_nsfw": float(row.get("prompt_nsfw", 0.0)) if pd.notna(row.get("prompt_nsfw")) else 0.0,
        }
        prompts.append(prompt_data)

    # Save results
    print(f"\nSaving {len(prompts)} prompts to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(prompts, f, indent=2)

    # Also save a CSV version for easy viewing
    csv_file = output_file.replace('.json', '.csv')
    result_df = pd.DataFrame(prompts)
    result_df.to_csv(csv_file, index=False)
    print(f"Also saved CSV version to {csv_file}")

    # Print some statistics
    print("\n=== Dataset Statistics ===")
    print(f"Total prompts: {len(prompts)}")
    print(f"Average prompt length: {result_df['prompt'].str.len().mean():.1f} characters")
    nsfw_count = (result_df['prompt_nsfw'] > 0.5).sum()
    print(f"NSFW prompts: {nsfw_count} ({nsfw_count/len(prompts)*100:.1f}%)")

    print(f"\nSample prompts:")
    for i in range(min(5, len(prompts))):
        nsfw_tag = "[NSFW]" if prompts[i]['prompt_nsfw'] > 0.5 else "[SAFE]"
        print(f"{i+1}. {nsfw_tag} {prompts[i]['prompt'][:80]}...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch DiffusionDB samples from Hugging Face metadata",
        epilog="Dataset: https://huggingface.co/datasets/poloclub/diffusiondb"
    )
    parser.add_argument("--num-samples", type=int, default=1000,
                        help="Number of samples to fetch (default: 1000)")
    parser.add_argument("--output", type=str, default="diffusiondb_samples.json",
                        help="Output file path (default: diffusiondb_samples.json)")
    parser.add_argument("--large", action="store_true",
                        help="Use large dataset (14M) instead of 2M")
    parser.add_argument("--sequential", action="store_true",
                        help="Take first N samples instead of random sampling")
    parser.add_argument("--nsfw-only", action="store_true",
                        help="Only fetch NSFW prompts")
    parser.add_argument("--safe-only", action="store_true",
                        help="Only fetch safe (non-NSFW) prompts")
    parser.add_argument("--force-download", action="store_true",
                        help="Force re-download of metadata file")

    args = parser.parse_args()

    # Determine NSFW filter
    filter_nsfw = None
    if args.nsfw_only:
        filter_nsfw = True
    elif args.safe_only:
        filter_nsfw = False

    fetch_diffusiondb_samples(
        args.num_samples,
        args.output,
        use_large=args.large,
        random_sample=not args.sequential,
        filter_nsfw=filter_nsfw
    )
