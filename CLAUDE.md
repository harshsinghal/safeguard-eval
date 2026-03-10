# OSS-Safeguard Policy Tester — Claude Code Guide

A content moderation web app that lets users search DiffusionDB prompts, write custom prompts, evaluate them against policies using `gpt-oss-safeguard-20b` (via Groq), and generate images via Fal.ai.

## Quick Start

```bash
cp .env.example .env       # add your GROQ_API_KEY and FAL_KEY
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py              # opens at http://localhost:5001
```

## Architecture

```
app.py                     — Flask web server
templates/index.html       — Single-page frontend
policies/                  — Content moderation policies (.txt files)
fetch_diffusiondb.py       — Downloads metadata.parquet from HuggingFace
search_and_evaluate.py     — Builds the local libsql database from the parquet file
prompts.db                 — SQLite database (local, not committed)
```

## Data Pipeline (one-time setup)

```bash
# Step 1: Download DiffusionDB metadata (~185MB parquet)
python fetch_diffusiondb.py

# Step 2: Build the local database (computes embeddings — slow for 2M rows)
python search_and_evaluate.py --init --num-samples 100000   # subset for testing
python search_and_evaluate.py --init                        # full 2M
```

The database stores each prompt's text, NSFW label, dimensions, and a vector embedding (`all-MiniLM-L6-v2`) for semantic search.

## Database Schema

```sql
CREATE TABLE prompts (
    id        INTEGER PRIMARY KEY,
    prompt    TEXT NOT NULL,
    nsfw      INTEGER,
    width     INTEGER,
    height    INTEGER,
    embedding BLOB          -- float32 vector, 384 dimensions
);
CREATE VIRTUAL TABLE prompts_fts USING fts5(prompt, ...);  -- for keyword search
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/policies` | GET | List policy files |
| `/api/policy/<filename>` | GET | Get policy text |
| `/api/evaluate` | POST | Evaluate a prompt against a policy |
| `/api/generate-image` | POST | Generate image via Fal.ai |
| `/api/search` | POST | Hybrid keyword + vector search |

### POST /api/evaluate
```json
{ "policy": "nsfw_strict.txt", "content": "a prompt to test" }
```

### POST /api/search
```json
{ "query": "fantasy warrior", "limit": 10, "min_words": 10, "nsfw_filter": "safe" }
```

### POST /api/generate-image
```json
{ "prompt": "a mountain at sunrise", "provider": "fal", "model": "fal-ai/flux/schnell" }
```

## Policies

Plain `.txt` files in `policies/`. Each is a system prompt for the safeguard model. The model returns `SAFE` or `UNSAFE` with an explanation. Add a `.txt` file and it appears automatically in the UI.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | For policy evaluation |
| `FAL_KEY` | No | For image generation |
| `TURSO_AUTH_TOKEN` | No | Only if using a remote Turso DB instead of local `prompts.db` |

## Common Tasks

**Add a new policy:** Create `policies/<name>.txt` with a system prompt that instructs the model to respond SAFE or UNSAFE.

**Change Fal.ai model:** Update the default in `api_generate_image()` in `app.py`, or users can edit it in the UI.

**Use a remote database:** Set `TURSO_AUTH_TOKEN` and update `DB_URL` in `app.py` to a `libsql+wss://` URL.
