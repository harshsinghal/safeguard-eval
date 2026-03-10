# OSS-Safeguard Policy Tester

A web app for testing content moderation policies against image generation prompts. Search the [DiffusionDB](https://huggingface.co/datasets/poloclub/diffusiondb) dataset of 2 million Stable Diffusion prompts, evaluate them against custom policies using `gpt-oss-safeguard-20b`, and generate images via Fal.ai — all in one UI.

## How It Works

1. **Search** the DiffusionDB dataset with natural language (hybrid keyword + vector search)
2. **Select a policy** — or write your own as a plain text file
3. **Evaluate** the prompt: the safeguard model returns SAFE or UNSAFE with a reason
4. **Generate an image** from the prompt via Fal.ai to see what it would actually produce

## Prerequisites

- Python 3.9+
- [Groq API key](https://console.groq.com) (free tier available) — for policy evaluation
- [Fal.ai API key](https://fal.ai/dashboard/keys) (optional) — for image generation

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/safeguard-eval.git
cd safeguard-eval
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
FAL_KEY=your_fal_api_key_here        # optional
```

**Groq API key:** [console.groq.com](https://console.groq.com) → API Keys → Create Key

**Fal.ai key:** [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys) → Add Key

### 3. Run the web app

```bash
python app.py
```

Open [http://localhost:5001](http://localhost:5001). The app works immediately — search requires additional setup below.

## Setting Up Search (Optional)

The search panel requires a local database built from DiffusionDB.

### Step 1: Download the metadata

```bash
python fetch_diffusiondb.py
```

Downloads `metadata.parquet` (~185MB) from HuggingFace — a one-time download containing 2 million prompts with NSFW labels.

### Step 2: Build the database

```bash
# Load a subset for testing (faster)
python search_and_evaluate.py --init --num-samples 50000

# Load the full 2M dataset (takes a while — embeddings are computed locally)
python search_and_evaluate.py --init
```

This creates `prompts.db` with each prompt's text, NSFW label, and a vector embedding. Search then uses hybrid keyword + semantic matching.

## Policies

Policies are `.txt` files in the `policies/` directory. Five are included:

| Policy | Description |
|--------|-------------|
| `nsfw_strict.txt` | Blocks sexual content, nudity, violence, drugs |
| `nsfw_moderate.txt` | Allows suggestive content, blocks explicit material |
| `deity_nuanced.txt` | Allows artistic religious depictions, blocks photorealistic ones |
| `violence_filter.txt` | Blocks graphic violence, allows historical/fantasy context |
| `copyright_characters.txt` | Blocks named copyrighted characters and celebrities |

### Writing a Custom Policy

Add a `.txt` file to `policies/` — it appears in the UI automatically:

```
You are a content moderation assistant. [Describe your use case]

Block:
- [What to disallow]

Allow:
- [What to permit]

Respond with:
- "SAFE" if the prompt is acceptable
- "UNSAFE" if it violates the policy

Provide a brief explanation.
```

## Project Structure

```
safeguard-eval/
├── app.py                   # Flask web server
├── templates/
│   └── index.html           # Web UI
├── policies/                # Policy definition files
├── fetch_diffusiondb.py     # Download DiffusionDB metadata.parquet
├── search_and_evaluate.py   # Build local libsql database from parquet
├── .env.example             # Environment variable template
└── requirements.txt
```

## Using with Claude Code

This repo includes `CLAUDE.md` and `.claude/settings.json`. Open the project in Claude Code and it will understand the architecture and can help you extend the app, write new policies, or modify the UI.

```bash
claude
```

## License

MIT
