"""
Simple web app for testing policies with oss-safeguard
"""

import os
import numpy as np
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import libsql_client
from sentence_transformers import SentenceTransformer
import fal_client

load_dotenv()

app = Flask(__name__)
app.config['POLICIES_DIR'] = Path('policies')
app.config['DB_URL'] = "file:prompts.db"
# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "openai/gpt-oss-safeguard-20b"

# Initialize search components
search_client = None
embedding_model = None

def init_search():
    """Initialize search components lazily"""
    global search_client, embedding_model
    if search_client is None:
        try:
            search_client = libsql_client.create_client_sync(
                url=app.config['DB_URL'],
                auth_token=os.getenv("TURSO_AUTH_TOKEN")
            )
            embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("Search engine initialized")
        except Exception as e:
            print(f"Warning: Could not initialize search engine: {e}")
            return False
    return True



def get_policies():
    """Get list of all policy files in the policies directory"""
    policies_dir = app.config['POLICIES_DIR']
    if not policies_dir.exists():
        return []

    policy_files = []
    for file_path in sorted(policies_dir.glob('*.txt')):
        policy_files.append({
            'name': file_path.stem,
            'filename': file_path.name
        })

    return policy_files


def read_policy(filename):
    """Read policy content from file"""
    policy_path = app.config['POLICIES_DIR'] / filename
    if not policy_path.exists():
        return None

    with open(policy_path, 'r') as f:
        return f.read()


def evaluate_content(policy_text, content):
    """Evaluate content against policy using oss-safeguard"""
    try:
        response = groq_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": policy_text},
                {"role": "user", "content": content}
            ],
            temperature=0.1,
            max_tokens=500,
        )

        result = {
            "success": True,
            "response": response.choices[0].message.content,
            "model": MODEL,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        }

        # Extract verdict
        response_lower = result["response"].lower()
        if "unsafe" in response_lower[:50]:
            result["verdict"] = "UNSAFE"
        elif "safe" in response_lower[:50]:
            result["verdict"] = "SAFE"
        else:
            result["verdict"] = "UNKNOWN"

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/policies')
def api_policies():
    """API endpoint to get list of policies"""
    policies = get_policies()
    return jsonify(policies)


@app.route('/api/policy/<filename>')
def api_policy(filename):
    """API endpoint to get policy content"""
    policy_text = read_policy(filename)
    if policy_text is None:
        return jsonify({"error": "Policy not found"}), 404

    return jsonify({"filename": filename, "content": policy_text})


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """API endpoint to evaluate content against a policy"""
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    policy_filename = data.get('policy')
    content = data.get('content')
    if not policy_filename or not content:
        return jsonify({"error": "Policy and content are required"}), 400

    # Read policy
    policy_text = read_policy(policy_filename)
    if policy_text is None:
        return jsonify({"error": "Policy not found"}), 404

    # Evaluate
    result = evaluate_content(policy_text, content)

    return jsonify(result)


@app.route('/api/generate-image', methods=['POST'])
def api_generate_image():
    """API endpoint to generate an image from a prompt"""
    data = request.json

    if not data:
        return jsonify({"error": "No data provided"}), 400

    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    model = data.get('model', 'imagineart/imagineart-1.5-preview/text-to-image')
    result = generate_image_fal(prompt, model)
    return jsonify(result)


def generate_image_fal(prompt, model_id):
    """Generate an image using Fal.ai hosted models"""
    if not os.getenv("FAL_KEY"):
        return {
            "success": False,
            "error": "FAL_KEY not configured. Please set it in your .env file."
        }

    try:
        print(f"Generating image with Fal.ai model: {model_id}")
        result = fal_client.subscribe(
            model_id,
            arguments={"prompt": prompt},
        )

        images = result.get("images", [])
        if not images:
            return {
                "success": False,
                "error": "No images returned from Fal.ai"
            }

        image = images[0]
        print(f"Image generated successfully: {image['url']}")
        return {
            "success": True,
            "provider": "fal",
            "model": model_id,
            "image_url": image["url"],
            "width": image.get("width"),
            "height": image.get("height"),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fal.ai generation failed: {str(e)}"
        }



@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search the diffusion db dataset"""
    if not init_search():
        return jsonify({"error": "Search engine not available. Database may not be initialized."}), 503

    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    limit = min(int(data.get('limit', 10)), 50)  # Cap at 50 results
    nsfw_filter = data.get('nsfw_filter')  # 'safe', 'nsfw', or None
    min_words = int(data.get('min_words', 10))  # Minimum word count (default: 10)

    try:
        # Perform hybrid search
        results = hybrid_search(
            query=query,
            top_k=limit,
            keyword_weight=0.3,
            vector_weight=0.7,
            nsfw_filter=nsfw_filter,
            min_words=min_words
        )

        return jsonify({
            "success": True,
            "query": query,
            "count": len(results),
            "min_words": min_words,
            "results": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def hybrid_search(query, top_k=10, keyword_weight=0.3, vector_weight=0.7, nsfw_filter=None, min_words=10):
    """
    Perform hybrid search combining keyword and vector search

    Args:
        min_words: Minimum number of words in the prompt (default: 10)
    """
    # Normalize weights
    total_weight = keyword_weight + vector_weight
    keyword_weight = keyword_weight / total_weight
    vector_weight = vector_weight / total_weight

    # Get query embedding
    query_embedding = embedding_model.encode([query])[0]

    # Keyword search - get more results to account for filtering
    keyword_results = keyword_search(query, top_k * 5, nsfw_filter)
    keyword_ids = {r['id']: r['score'] for r in keyword_results}

    # Vector search - get more results to account for filtering
    vector_results = vector_search(query_embedding, top_k * 5, nsfw_filter)
    vector_ids = {r['id']: r['score'] for r in vector_results}

    # Combine results
    all_ids = set(keyword_ids.keys()) | set(vector_ids.keys())

    combined_results = []
    for prompt_id in all_ids:
        keyword_score = keyword_ids.get(prompt_id, 0)
        vector_score = vector_ids.get(prompt_id, 0)
        hybrid_score = (keyword_weight * keyword_score) + (vector_weight * vector_score)

        # Get prompt details
        result = search_client.execute(
            "SELECT id, prompt, nsfw, width, height FROM prompts WHERE id = ?",
            [prompt_id]
        )

        if result.rows:
            row = result.rows[0]
            prompt_text = str(row[1])

            # Filter by word count
            word_count = len(prompt_text.split())
            if word_count >= min_words:
                combined_results.append({
                    'id': int(row[0]),
                    'prompt': prompt_text,
                    'nsfw': bool(row[2]),
                    'width': int(row[3]),
                    'height': int(row[4]),
                    'score': float(round(hybrid_score, 3)),
                    'word_count': word_count
                })

    # Sort by hybrid score and return top_k
    combined_results.sort(key=lambda x: x['score'], reverse=True)
    return combined_results[:top_k]


def keyword_search(query, limit, nsfw_filter=None):
    """Perform FTS5 keyword search"""
    nsfw_clause = ""
    if nsfw_filter == 'safe':
        nsfw_clause = "AND p.nsfw = 0"
    elif nsfw_filter == 'nsfw':
        nsfw_clause = "AND p.nsfw = 1"

    sql = f"""
        SELECT p.id, rank as score
        FROM prompts_fts fts
        JOIN prompts p ON p.id = fts.rowid
        WHERE prompts_fts MATCH ?
        {nsfw_clause}
        ORDER BY rank
        LIMIT ?
    """

    result = search_client.execute(sql, [query, limit])

    if not result.rows:
        return []

    # Normalize scores
    scores = [abs(row[1]) for row in result.rows]
    max_score = max(scores) if scores else 1

    return [
        {'id': int(row[0]), 'score': float(1 - (abs(row[1]) / max_score))}
        for row in result.rows
    ]


def vector_search(query_embedding, limit, nsfw_filter=None):
    """Perform vector similarity search"""
    nsfw_clause = ""
    if nsfw_filter == 'safe':
        nsfw_clause = "WHERE nsfw = 0"
    elif nsfw_filter == 'nsfw':
        nsfw_clause = "WHERE nsfw = 1"

    sql = f"SELECT id, embedding FROM prompts {nsfw_clause}"
    result = search_client.execute(sql)

    if not result.rows:
        return []

    # Compute cosine similarities
    similarities = []
    for row in result.rows:
        prompt_id = row[0]
        embedding_blob = row[1]
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)

        # Cosine similarity
        similarity = np.dot(query_embedding, embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
        )
        similarities.append((prompt_id, similarity))

    # Sort and get top results
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_results = similarities[:limit]

    # Normalize scores
    if top_results:
        max_sim = float(top_results[0][1])
        min_sim = float(top_results[-1][1])
        score_range = max_sim - min_sim if max_sim != min_sim else 1

        return [
            {'id': int(pid), 'score': float((sim - min_sim) / score_range)}
            for pid, sim in top_results
        ]

    return []


if __name__ == '__main__':
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in environment variables")
        print("Please set GROQ_API_KEY in your .env file")
        exit(1)

    # Create policies directory if it doesn't exist
    app.config['POLICIES_DIR'].mkdir(exist_ok=True)

    print(f"\nStarting OSS-Safeguard Policy Tester")
    print(f"Policies directory: {app.config['POLICIES_DIR'].absolute()}")
    print(f"Available policies: {len(get_policies())}")
    print(f"\nOpen http://localhost:5001 in your browser\n")

    app.run(debug=True, host='0.0.0.0', port=5001)
