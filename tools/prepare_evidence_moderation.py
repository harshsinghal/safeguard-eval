"""Prepare immutable local inputs and a source-grounded annotation review packet."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.evidence_moderation.controls import PAIRS
from evals.evidence_moderation.schema import SCHEMA, TYPES, ACTION_TYPES, VERSION, blank, validate

STATE = ROOT / "work/evidence-moderation-v1"
PUBLIC = ROOT / "local_runs/evidence-moderation-v1"
SOURCE = ROOT.parent / "safeguard-enterprise-benchmark/work/frozen-enterprise-inputs-v0.1/evaluation.jsonl"
META = ROOT / "benchmarks/enterprise-moderation/v0.1/evaluation.jsonl"
DOCS = ROOT / "docs/evidence-moderation"


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def jsonl(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(v, ensure_ascii=False, allow_nan=False) + "\n" for v in values))


def normalize(text):
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def components(meta, inputs):
    parent = {m["group"]: m["group"] for m in meta}

    def find(group):
        while parent[group] != group:
            parent[group] = parent[parent[group]]
            group = parent[group]
        return group

    def union(left, right):
        a, b = sorted((find(left), find(right)))
        parent[b] = a

    features = []
    for m in meta:
        text = normalize(inputs[m["id"]]["content"])
        words = text.split()
        shingles = {tuple(words[i:i + 5]) for i in range(len(words) - 4)}
        features.append((m["group"], text, shingles))
    exact_links = near_links = 0
    for i, (group, text, shingles) in enumerate(features):
        for other_group, other_text, other in features[:i]:
            if text == other_text:
                union(group, other_group)
                exact_links += 1
            elif shingles and other and min(len(shingles), len(other)) >= .8 * max(len(shingles), len(other)):
                intersection = len(shingles & other)
                if intersection / (len(shingles) + len(other) - intersection) >= .8:
                    union(group, other_group)
                    near_links += 1
    return {m["id"]: find(m["group"]) for m in meta}, dict(exact_links=exact_links, near_links=near_links)


def select():
    meta = rows(META)
    inputs = {r["id"]: r for r in rows(SOURCE)}
    groups, grouping = components(meta, inputs)
    excluded = {r["id"] for r in rows(ROOT / "work/qwen-extraction-v0/inputs.private.jsonl")}
    candidates = defaultdict(lambda: defaultdict(list))
    for m in meta:
        r = inputs[m["id"]]
        if sha(r["content"]) != m["input_sha256"] or r["input_sha256"] != m["input_sha256"]:
            raise ValueError("Source input hash mismatch")
        if m["id"] in excluded:
            continue
        group = groups[m["id"]]
        split = "development" if int(sha("evidence-v1:" + group), 16) % 2 == 0 else "evaluation"
        candidates[(m["track"], split)][(m["expected"], m["length_band"])].append(m)
    chosen = []
    for (track, split), strata in sorted(candidates.items()):
        for values in strata.values():
            values.sort(key=lambda m: sha("evidence-v1:" + m["id"]))
        used = set()
        selected = []
        while len(selected) < 6:
            progress = False
            for key in sorted(strata):
                values = strata[key]
                while values and groups[values[0]["id"]] in used:
                    values.pop(0)
                if values and len(selected) < 6:
                    m = values.pop(0)
                    selected.append(m)
                    used.add(groups[m["id"]])
                    progress = True
            if not progress:
                raise ValueError(f"Insufficient independent groups for {track}/{split}")
        for m in selected:
            chosen.append(dict(id=m["id"], content=inputs[m["id"]]["content"],
                               input_sha256=m["input_sha256"], group=groups[m["id"]],
                               original_group=m["group"], split=split, track=track,
                               source_kind="existing_benchmark", source_id=m["source_id"],
                               original_label=m["expected"], length_band=m["length_band"]))
    ordered_pairs = sorted(PAIRS, key=lambda p: sha("evidence-v1:" + p[0]))
    for i, (family, *texts) in enumerate(ordered_pairs):
        for j, text in enumerate(texts):
            chosen.append(dict(id=f"control-{family}-{j + 1}", content=text, input_sha256=sha(text),
                               group=f"control-{family}", original_group=f"control-{family}",
                               split="development" if i < 8 else "evaluation", track="authored_controls",
                               source_kind="assistant_authored", source_id=f"control-{family}-{j + 1}",
                               original_label=None, length_band="long" if len(text) > 2000 else "short"))
    chosen.sort(key=lambda c: (c["split"], c["track"], c["id"]))
    if len(chosen) != 200:
        raise ValueError("Expected exactly 200 inputs")
    return chosen, grouping


def render_review(path, cases):
    # Source labels and sampling metadata never enter the annotation view.
    payload = [dict(id=c["id"], content=c["content"], input_sha256=c["input_sha256"], annotation=blank(c)) for c in cases]
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    page = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'">
<title>Prompt evidence review</title>
<style>body{font:16px system-ui;margin:24px;background:#f5f5f5;color:#17202a}button,select,input{font:inherit;margin:5px;padding:6px}main{display:grid;grid-template-columns:1fr 1fr;gap:18px}pre,textarea{box-sizing:border-box;width:100%;height:65vh;overflow:auto;background:white;border:1px solid #aaa;padding:16px;white-space:pre-wrap;overflow-wrap:anywhere;font:14px monospace}details{margin:12px 0}#message{min-height:24px;color:#553300}@media(max-width:800px){main{grid-template-columns:1fr}}</style>
<h1>Prompt evidence review</h1><p>Pending annotations need semantic review. Save the case, then export before closing. Source text stays in this local file.</p>
<details><summary>Policy</summary><div>__POLICY__</div></details>
<details><summary>Annotation guide</summary><div>__GUIDE__</div></details>
<details><summary>Entity and action types</summary><div>__TYPES__</div></details>
<label>Prompt <select id="cases"></select></label><button id="save">Save case</button><button id="export">Export annotations</button>
<label>Resume from export <input id="import" type="file" accept=".json,application/json"></label>
<p id="message" role="status"></p><main><section><h2>Original prompt</h2><pre id="prompt"></pre></section><section><h2>Annotation JSON</h2><textarea id="editor" spellcheck="false" aria-label="Annotation JSON"></textarea></section></main>
<label>Find exact span <input id="span" type="text"></label><button id="offset">Find Unicode offsets</button><output id="matches"></output>
<script id="data" type="application/json">__DATA__</script>
<script>
const records=JSON.parse(document.getElementById('data').textContent);
const byId=new Map(records.map(r=>[r.id,r]));
const select=document.getElementById('cases'), editor=document.getElementById('editor'), message=document.getElementById('message');
for(const r of records){const option=document.createElement('option');option.value=r.id;option.textContent=r.id;select.append(option);}
let active=records[0].id, dirty=false;
function show(){const r=byId.get(active);document.getElementById('prompt').textContent=r.content;editor.value=JSON.stringify(r.annotation,null,2);message.textContent=r.annotation.status;}
function save(){try{const a=JSON.parse(editor.value),r=byId.get(active);if(a.id!==r.id||a.input_sha256!==r.input_sha256)throw Error('Case ID or hash mismatch');r.annotation=a;dirty=true;message.textContent='Saved in this tab. Export to retain changes. Python validation is required.';return true;}catch(e){message.textContent=e.message;return false;}}
select.onchange=()=>{const next=select.value;if(save()){active=next;show();}else select.value=active;};
document.getElementById('save').onclick=save;editor.oninput=()=>{dirty=true;};
document.getElementById('export').onclick=()=>{if(!save())return;const blob=new Blob([JSON.stringify(records.map(r=>r.annotation),null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='__SPLIT__-annotations.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);dirty=false;};
document.getElementById('import').onchange=async event=>{try{if(dirty&&!confirm('Replace current edits with the imported annotations?'))return;const input=JSON.parse(await event.target.files[0].text());if(!Array.isArray(input)||input.length!==records.length||new Set(input.map(a=>a.id)).size!==records.length)throw Error('Expected all unique cases for this split');for(const a of input){if(!byId.has(a.id)||byId.get(a.id).input_sha256!==a.input_sha256)throw Error('Input binding mismatch');}for(const a of input)byId.get(a.id).annotation=a;dirty=false;show();}catch(e){message.textContent=e.message;}};
document.getElementById('offset').onclick=()=>{const text=byId.get(active).content,term=document.getElementById('span').value,matches=[];if(term){let start=text.indexOf(term);while(start>=0){matches.push({start:Array.from(text.slice(0,start)).length,end:Array.from(text.slice(0,start+term.length)).length});start=text.indexOf(term,start+1);}}document.getElementById('matches').textContent=JSON.stringify(matches);};
window.onbeforeunload=e=>{if(dirty){e.preventDefault();e.returnValue='';}};show();
</script></html>"""
    def prose(name):
        return "<div style='white-space:pre-wrap'>" + html.escape((DOCS / name).read_text()) + "</div>"
    page = page.replace("__POLICY__", prose("POLICY.md")).replace("__GUIDE__", prose("ANNOTATION.md"))
    page = page.replace("__TYPES__", "<div style='white-space:pre-wrap'>" + html.escape(json.dumps({"mentions": TYPES, "actions": ACTION_TYPES}, indent=2)) + "</div>")
    page = page.replace("__SPLIT__", cases[0]["split"]).replace("__DATA__", data)
    path.write_text(page)


def prepare():
    if STATE.exists() or PUBLIC.exists():
        raise ValueError("Preserve existing pilot. Use a new version for changed preparation.")
    cases, grouping = select()
    STATE.mkdir(parents=True)
    PUBLIC.mkdir(parents=True)
    write(DOCS / "schema.json", SCHEMA)
    jsonl(STATE / "inputs.private.jsonl", cases)
    for split in ("development", "evaluation"):
        cohort = [c for c in cases if c["split"] == split]
        write(STATE / f"{split}-annotations.json", [blank(c) for c in cohort])
        render_review(STATE / f"{split}-review.html", cohort)
    safe = [{k: v for k, v in c.items() if k != "content"} | {"input_chars": len(c["content"])} for c in cases]
    jsonl(PUBLIC / "cases.jsonl", safe)
    files = [Path(__file__), *sorted((ROOT / "evals/evidence_moderation").glob("*.py")),
             DOCS / "PLAN.md", DOCS / "POLICY.md", DOCS / "ANNOTATION.md", DOCS / "schema.json"]
    registration = dict(schema_version=VERSION, created_utc=datetime.now(timezone.utc).isoformat(),
                        status="prepared_pending_annotation", cases=200, splits=dict(Counter(c["split"] for c in cases)),
                        track_counts=dict(Counter(c["track"] for c in cases)), grouping=grouping,
                        source_hashes={str(p.relative_to(ROOT.parent)): digest(p) for p in (SOURCE, META)},
                        code_hashes={str(p.relative_to(ROOT)): digest(p) for p in files},
                        input_sha256=digest(STATE / "inputs.private.jsonl"),
                        private_file_hashes={p.name: digest(p) for p in STATE.iterdir() if p.is_file()},
                        prior_exposure="Existing source suite was used in earlier studies; new split is experiment-local only.",
                        review_status="All 200 annotations pending; zero human-reviewed gold cases.",
                        paid_api_cost_usd=0, model_inference_performed=False, gpu_workers_started=0)
    write(PUBLIC / "registration.json", registration)
    verify()


def verify():
    reg = json.loads((PUBLIC / "registration.json").read_text())
    cases = rows(STATE / "inputs.private.jsonl")
    assert digest(STATE / "inputs.private.jsonl") == reg["input_sha256"]
    assert all(digest(ROOT / p) == value for p, value in reg["code_hashes"].items())
    assert all(digest(ROOT.parent / p) == value for p, value in reg["source_hashes"].items())
    assert all(digest(STATE / p) == value for p, value in reg["private_file_hashes"].items())
    assert len(cases) == len({c["id"] for c in cases}) == 200
    assert Counter(c["split"] for c in cases) == {"development": 100, "evaluation": 100}
    groups, texts = {}, {}
    for case in cases:
        assert sha(case["content"]) == case["input_sha256"]
        for mapping, key in ((groups, case["group"]), (texts, normalize(case["content"]))):
            assert mapping.setdefault(key, case["split"]) == case["split"]
        assert not validate(blank(case), case)
    for split in ("development", "evaluation"):
        counts = Counter(c["track"] for c in cases if c["split"] == split)
        assert counts.pop("authored_controls") == 16 and len(counts) == 14 and set(counts.values()) == {6}
    safe = rows(PUBLIC / "cases.jsonl")
    assert safe == [{k: v for k, v in c.items() if k != "content"} | {"input_chars": len(c["content"])} for c in cases]
    exported = "\n".join(p.read_text() for p in PUBLIC.glob("*.json*"))
    assert all(c["content"] not in exported for c in cases if len(c["content"]) >= 32)
    result = dict(passed=True, cases=200, split_sizes={"development": 100, "evaluation": 100},
                  source_binding=True, group_separation=True, normalized_duplicate_separation=True,
                  annotations_pending=200, restricted_full_text_exported=False)
    write(PUBLIC / "verification.json", result)
    print(json.dumps(result))


def validate_export(path):
    cases = {c["id"]: c for c in rows(STATE / "inputs.private.jsonl")}
    annotations = json.loads(path.read_text())
    if not isinstance(annotations, list) or any(not isinstance(a, dict) or a.get("id") not in cases for a in annotations):
        raise ValueError("Expected annotation array with known case IDs")
    ids = [a["id"] for a in annotations]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate case IDs")
    errors = {a["id"]: problems for a in annotations if (problems := validate(a, cases[a["id"]]))}
    print(json.dumps(dict(records=len(annotations), status_counts=dict(Counter(a.get("status") for a in annotations)), errors=errors), indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "verify", "validate"))
    parser.add_argument("--annotations", type=Path)
    args = parser.parse_args()
    if args.stage == "validate":
        if not args.annotations:
            parser.error("validate requires --annotations")
        validate_export(args.annotations)
    elif args.stage == "prepare":
        prepare()
    else:
        verify()
