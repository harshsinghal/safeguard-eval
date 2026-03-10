"""
Build a local libsql (SQLite) database from the DiffusionDB metadata parquet file.

The database stores prompts, NSFW labels, and vector embeddings to support
hybrid keyword + vector search in the web app.

Usage:
    # Load all 2M prompts
    python search_and_evaluate.py --init

    # Load a subset (faster for testing)
    python search_and_evaluate.py --init --num-samples 50000

    # Force reload even if database already has data
    python search_and_evaluate.py --init --force
"""

import os
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import libsql_client
from tqdm import tqdm

load_dotenv()

METADATA_FILE = "metadata.parquet"
DB_URL = "file:prompts.db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def initialize_database(client):
    """Create tables and indexes if they don't exist"""
    client.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY,
            prompt TEXT NOT NULL,
            nsfw INTEGER,
            width INTEGER,
            height INTEGER,
            embedding BLOB
        )
    """)

    client.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts
        USING fts5(prompt, content=prompts, content_rowid=id)
    """)

    client.execute("""
        CREATE TRIGGER IF NOT EXISTS prompts_ai AFTER INSERT ON prompts BEGIN
            INSERT INTO prompts_fts(rowid, prompt) VALUES (new.id, new.prompt);
        END
    """)

    client.execute("""
        CREATE TRIGGER IF NOT EXISTS prompts_ad AFTER DELETE ON prompts BEGIN
            INSERT INTO prompts_fts(prompts_fts, rowid, prompt) VALUES('delete', old.id, old.prompt);
        END
    """)

    client.execute("""
        CREATE TRIGGER IF NOT EXISTS prompts_au AFTER UPDATE ON prompts BEGIN
            INSERT INTO prompts_fts(prompts_fts, rowid, prompt) VALUES('delete', old.id, old.prompt);
            INSERT INTO prompts_fts(rowid, prompt) VALUES (new.id, new.prompt);
        END
    """)


def create_embeddings(prompts, model):
    """Create embeddings for a list of prompts in batches"""
    batch_size = 256
    embeddings = []

    for i in tqdm(range(0, len(prompts), batch_size), desc="Creating embeddings"):
        batch = prompts[i:i + batch_size]
        batch_embeddings = model.encode(batch, show_progress_bar=False)
        embeddings.append(batch_embeddings)

    return np.vstack(embeddings)


def load_data(client, model, num_samples=None, force=False):
    """Load prompts and embeddings from the parquet file into the database"""
    result = client.execute("SELECT COUNT(*) FROM prompts")
    count = result.rows[0][0] if result.rows else 0

    if count > 0 and not force:
        print(f"Database already contains {count:,} prompts. Use --force to reload.")
        return

    if count > 0:
        client.execute("DELETE FROM prompts")
        print("Cleared existing data.")

    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(
            f"{METADATA_FILE} not found. Run: python fetch_diffusiondb.py"
        )

    print(f"Loading {METADATA_FILE}...")
    df = pd.read_parquet(METADATA_FILE)
    print(f"Total prompts in dataset: {len(df):,}")

    if num_samples and num_samples < len(df):
        print(f"Sampling {num_samples:,} prompts...")
        df = df.sample(n=num_samples, random_state=42).reset_index(drop=True)

    print("Creating embeddings (this takes a while for large datasets)...")
    embeddings = create_embeddings(df['prompt'].tolist(), model)

    print("Inserting into database...")
    batch_size = 1000

    for i in tqdm(range(0, len(df), batch_size), desc="Inserting batches"):
        batch_df = df.iloc[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        for j, (idx, row) in enumerate(batch_df.iterrows()):
            embedding_blob = batch_embeddings[j].tobytes()
            client.execute(
                "INSERT INTO prompts (id, prompt, nsfw, width, height, embedding) VALUES (?, ?, ?, ?, ?, ?)",
                [int(idx), row['prompt'], int(row.get('nsfw', 0)),
                 int(row.get('width', 0)), int(row.get('height', 0)), embedding_blob]
            )

    result = client.execute("SELECT COUNT(*) FROM prompts")
    final_count = result.rows[0][0]
    print(f"\nDone. Database contains {final_count:,} prompts.")


def main():
    parser = argparse.ArgumentParser(
        description="Build the local libsql database from DiffusionDB metadata"
    )
    parser.add_argument("--init", action="store_true", required=True,
                        help="Initialize the database")
    parser.add_argument("--num-samples", type=int, default=None,
                        help="Number of prompts to load (default: all ~2M)")
    parser.add_argument("--force", action="store_true",
                        help="Force reload even if database already has data")
    parser.add_argument("--db-url", type=str, default=DB_URL,
                        help=f"Database URL (default: {DB_URL})")
    args = parser.parse_args()

    client = libsql_client.create_client_sync(
        url=args.db_url,
        auth_token=os.getenv("TURSO_AUTH_TOKEN")
    )
    initialize_database(client)

    print(f"Loading sentence transformer model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    load_data(client, model, num_samples=args.num_samples, force=args.force)


if __name__ == "__main__":
    main()
