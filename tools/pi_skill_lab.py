#!/usr/bin/env python3
"""Opt-in Pi user test: isolated profile, native logs, local review. No secret printing."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "safeguard-eval"
MODEL = "openai/gpt-6-luna"
DEFAULT_LAB = Path.home() / "workspace" / "safeguard-eval-feedback"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    path.chmod(0o600)


def api(path, key=None):
    headers = {"Authorization": "Bearer " + key} if key else {}
    req = urllib.request.Request("https://openrouter.ai/api/v1/" + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def read_key(config):
    value = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not value and config.get("key_file"):
        value = Path(config["key_file"]).read_text(encoding="utf-8").strip()
    matches = re.findall(r"sk-or-v1-[A-Za-z0-9_-]+", value)
    if len(matches) != 1:
        raise ValueError("Set OPENROUTER_API_KEY or supply a file containing one OpenRouter key.")
    return matches[0]


def redact(text):
    # Best effort only. Raw text and private context still need human review.
    text = re.sub(r"\b(?:sk-or-v1-|sk-|hf_|ghp_)[A-Za-z0-9_-]{12,}", "[REDACTED_KEY]", text)
    text = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)\S+", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)((?:api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*)[^\s\"']+",
                  r"\1[REDACTED]", text)
    return text.replace(str(Path.home()), "~")


def visible_text(content):
    if isinstance(content, str):
        return content
    return "\n".join(b.get("text", "") for b in (content or []) if b.get("type") == "text")


def redact_tree(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_tree(v) for v in value]
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if re.search(r"(?i)^(api.?key|authorization|secret|access.?token)$", k)
                    else redact_tree(v)) for k, v in value.items()}
    return value


def read_entries(path):
    if not path.exists():
        return [], []
    entries, warnings = [], []
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            warnings.append(f"Invalid/incomplete JSONL at line {number}; review the native log.")
    return entries, warnings


def run_entries(run):
    index = run / "session-index.json"
    paths = json.loads(index.read_text()) if index.exists() else [str(run / "session.jsonl")]
    entries, warnings, seen = [], [], set()
    for name in dict.fromkeys(paths):
        path = Path(name)
        if not path.exists():
            warnings.append("A recorded session file is unavailable: " + redact(str(path)))
            continue
        rows, notes = read_entries(path)
        warnings.extend(notes)
        for row in rows:
            # Forked Pi files can copy ancestor entries. Do not bill/count them twice.
            fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=False)
            if fingerprint not in seen:
                seen.add(fingerprint)
                row["_session_file"] = path.name
                entries.append(row)
    return entries, warnings


def summarize(entries):
    turns, feedback, events, tool_calls = [], [], [], []
    tokens = {k: 0 for k in ("input", "output", "cacheRead", "cacheWrite", "totalTokens")}
    estimated_cost, calls, response_ids = 0.0, 0, []
    missing_usage = 0
    for e in entries:
        m = e.get("message", {}) if e.get("type") == "message" else {}
        usage = m.get("usage") or e.get("usage")
        if usage:
            for k in tokens:
                tokens[k] += usage.get(k, 0) or 0
            estimated_cost += (usage.get("cost") or {}).get("total", 0) or 0
        if m.get("role") == "assistant":
            calls += 1
            if not usage:
                missing_usage += 1
            if m.get("responseId"):
                response_ids.append(m["responseId"])
            for b in m.get("content", []):
                if b.get("type") == "toolCall":
                    tool_calls.append({"entry_id": e.get("id"), "name": b.get("name"),
                                       "arguments": b.get("arguments", {})})
        if m.get("role") in ("user", "assistant"):
            text = visible_text(m.get("content"))
            # Preserve failed/empty responses as visible failures, not missing turns.
            if text or m.get("stopReason") in ("error", "aborted", "length"):
                turns.append({"id": e.get("id"), "parent_id": e.get("parentId"), "session_file": e.get("_session_file"),
                              "timestamp": e.get("timestamp"), "role": m["role"],
                              "text": redact(text), "model": m.get("model"),
                              "provider": m.get("provider"), "response_model": m.get("responseModel"),
                              "stop_reason": m.get("stopReason"),
                              "error": redact(m.get("errorMessage", ""))})
        if e.get("type") == "custom" and e.get("customType") == "safeguard-feedback":
            feedback.append({"target_id": e.get("data", {}).get("targetId"),
                             "note": redact(e.get("data", {}).get("note", ""))})
        if e.get("type") in ("model_change", "thinking_level_change", "compaction", "branch_summary", "context_edit"):
            events.append({k: e[k] for k in ("type", "id", "parentId", "timestamp", "modelId",
                                           "provider", "thinkingLevel", "targetId") if k in e})
    return {"turns": turns, "feedback": feedback, "events": events,
            # Tool arguments remain in a private structured report for provenance;
            # they are NOT included in the readable/shareable conversation export.
            "tool_calls": tool_calls,
            "usage": {"tokens": tokens, "model_responses": calls, "pi_estimated_cost_usd": estimated_cost,
                      "assistant_messages_missing_usage": missing_usage},
            "response_ids": list(dict.fromkeys(response_ids))}


def reconcile(run, key):
    entries, _ = run_entries(run)
    report = summarize(entries)
    costs = []
    for response_id in report["response_ids"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", response_id):
            continue
        try:
            d = api("generation?id=" + response_id, key)["data"]
            costs.append({k: d.get(k) for k in ("id", "model", "provider_name", "total_cost",
                                              "native_tokens_prompt", "native_tokens_completion")})
        except (urllib.error.URLError, ValueError, KeyError):
            costs.append({"id": response_id, "total_cost": None, "status": "unavailable"})
    write_json(run / "billing.json", {"checked_at": now(), "generations": costs,
                                     "note": "OpenRouter generation metadata; unavailable records are not zero cost."})


def export_review(run):
    entries, warnings = run_entries(run)
    report = summarize(entries)
    report.pop("response_ids")
    # Redact all strings including tool args before writing the structured review.
    report = redact_tree(report)
    report["warnings"] = warnings
    report["export_scope"] = "Original visible turns by first-seen session file, in each file's append order. Copied fork ancestors counted once. No reasoning/tool outputs. Not an exact model-context reconstruction."
    if (run / "billing.json").exists():
        b = json.loads((run / "billing.json").read_text())
        amounts = [g["total_cost"] for g in b["generations"] if isinstance(g.get("total_cost"), (int, float))]
        report["usage"]["openrouter_cost_usd_for_available_records"] = sum(amounts)
        report["usage"]["billing_records_available"] = len(amounts)
        report["usage"]["billing_records_requested"] = len(b["generations"])
    write_json(run / "review.json", report)
    meta = json.loads((run / "run.json").read_text()) if (run / "run.json").exists() else {}
    out = ["# Safeguard Eval — Pi conversation review", "",
           f"Run: {run.name}. Model: {meta.get('model', 'see native log')}. Skill: {meta.get('skill_version', 'unknown')}.",
           "", "Local review only. Check for private information before sharing. No automatic upload.",
           "Visible turns are grouped by session file in append order; IDs preserve branches. Copied ancestors count once. Reasoning and tool payloads are excluded.",
           "", "## Usage", "", "```json", json.dumps(report["usage"], indent=2), "```", "",
           "Pi costs are estimates, not a billing guarantee. Missing provider records are not zero cost.", ""]
    for t in report["turns"]:
        out.extend([f"## {t['role'].capitalize()} · {t['id']} (parent {t['parent_id']}; {t['session_file']})", "", t["text"], ""])
        if t["error"]:
            out.extend(["Error: " + t["error"], ""])
        if t["stop_reason"] in ("error", "aborted", "length"):
            out.extend(["Completion state: " + t["stop_reason"], ""])
    if report["feedback"]:
        out.extend(["## Review notes", ""])
        out.extend(f"- {n['target_id']}: {n['note']}" for n in report["feedback"])
    if warnings:
        out.extend(["", "## Log warnings", "", *warnings])
    (run / "review.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    (run / "review.md").chmod(0o600)
    return report


def setup(args):
    lab = args.lab.expanduser().resolve()
    lab.mkdir(parents=True, exist_ok=True, mode=0o700)
    lab.chmod(0o700)
    config_path = lab / "lab.json"
    old = json.loads(config_path.read_text()) if config_path.exists() else {}
    config = {**old, "model": MODEL, "provider": "openrouter", "budget_usd": 0.50, "max_calls": 100}
    if args.key_file:
        config["key_file"] = str(args.key_file.expanduser().resolve())
    read_key(config)  # Validate privately; never copy the value into configuration.
    model = next(m for m in api("models")["data"] if m["id"] == MODEL)
    write_json(lab / "model-catalog-snapshot.json", {"checked_at": now(), "model": model})
    profile = lab / "agent"
    profile.mkdir(exist_ok=True, mode=0o700)
    install = runpy.run_path(str(SKILL / "scripts" / "install.py"))["install"]
    result = install(SKILL, profile / "skills" / "safeguard-eval", update=True)
    price = model["pricing"]
    write_json(profile / "models.json", {"providers": {"openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1", "api": "openai-completions", "apiKey": "${OPENROUTER_API_KEY}",
        "models": [{"id": MODEL, "name": "GPT-6 Luna (Safeguard Eval user test)", "reasoning": True,
                    "input": ["text"], "contextWindow": model["context_length"], "maxTokens": 4096,
                    "cost": {"input": float(price["prompt"])*1e6, "output": float(price["completion"])*1e6,
                             "cacheRead": float(price.get("input_cache_read", 0))*1e6,
                             "cacheWrite": float(price.get("input_cache_write", 0))*1e6}}]}}})
    write_json(profile / "settings.json", {"defaultProvider": "openrouter", "defaultModel": MODEL,
                                          "defaultThinkingLevel": "low", "cacheWarming": "off",
                                          "retry": {"enabled": False}})
    config["installed_skill"] = result["destination"]
    write_json(config_path, config)
    (lab / "workspace").mkdir(exist_ok=True)
    if sys.platform == "darwin":
        import shlex
        launcher = lab / "Start Pi.command"
        launcher.write_text("#!/bin/zsh\n" + shlex.quote(sys.executable) + " " +
                            shlex.quote(str(Path(__file__).resolve())) + " --lab " + shlex.quote(str(lab)) +
                            " start\nprintf '\\nSession ended. Press Return to close.\\n'\nread -r reply\n")
        launcher.chmod(0o700)
    print(f"Pi lab ready at {lab}; model {MODEL}. Existing Pi defaults are unchanged.")


def start(args):
    lab = args.lab.expanduser().resolve()
    config = json.loads((lab / "lab.json").read_text())
    skill = Path(config["installed_skill"])
    installer = runpy.run_path(str(SKILL / "scripts" / "install.py"))
    release = installer["verify_package"](skill)
    key = read_key(config)
    questions = json.loads(args.questions.read_text()) if args.questions else None
    if questions is not None and (not isinstance(questions, list) or not questions or
                                  not all(isinstance(q, str) and q.strip() for q in questions)):
        raise ValueError("Questions must be a nonempty JSON array of nonempty strings.")
    run = lab / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6])
    run.mkdir(parents=True, mode=0o700)
    shutil.copytree(skill, run / "skill-snapshot")
    meta = {"started_at": now(), "label": args.label, "model": config["model"], "provider": config["provider"],
            "thinking": "low", "skill_version": release["version"],
            "skill_manifest_sha256": hashlib.sha256((skill / "manifest.json").read_bytes()).hexdigest(),
            "pi_version": subprocess.check_output(["pi", "--version"], text=True).strip(),
            "mode": "scripted multi-turn" if questions else "interactive user session",
            "extra_answer_instructions": False, "tools": "Pi defaults: read, bash, edit, write",
            "cost_stop_usd_estimate": config["budget_usd"], "max_model_responses": config["max_calls"]}
    write_json(run / "run.json", meta)
    if questions:
        write_json(run / "questions.json", questions)
    env = os.environ.copy()
    env.update(PI_CODING_AGENT_DIR=str(lab / "agent"), OPENROUTER_API_KEY=key,
               PI_TELEMETRY="0", SAFEGUARD_LAB_BUDGET_USD=str(config["budget_usd"]),
               SAFEGUARD_LAB_MAX_CALLS=str(config["max_calls"]), SAFEGUARD_LAB_RUN_DIR=str(run))
    cmd = ["pi", "--offline", "--provider", config["provider"], "--model", config["model"], "--thinking", "low",
           "--session", str(run / "session.jsonl"), "--session-dir", str(run), "--no-context-files", "--no-prompt-templates",
           "--no-skills", "--skill", str(skill), "--no-extensions", "-e", str(ROOT / "tools" / "pi_skill_feedback.ts"),
           "--no-approve"]
    # --offline disables Pi startup network checks, not model API requests.
    print(f"Run: {run}\nModel: {config['model']}. Logs local; inference goes through OpenRouter.\n"
          "Ask ordinary questions. /feedback saves a private note; /lab-usage shows usage.\n", flush=True)
    code = 0
    try:
        if questions:
            for i, question in enumerate(questions, 1):
                print(f"Question {i}/{len(questions)}", flush=True)
                with (run / f"turn-{i:02d}.stdout").open("w") as out, (run / f"turn-{i:02d}.stderr").open("w") as err:
                    completed = subprocess.run(cmd + ["--print", question], cwd=lab / "workspace", env=env,
                                               stdout=out, stderr=err, timeout=180)
                code = completed.returncode
                report = export_review(run)
                last = report["turns"][-1] if report["turns"] else {}
                if code or last.get("stop_reason") in ("error", "aborted"):
                    break
                if report["usage"]["pi_estimated_cost_usd"] >= config["budget_usd"] or report["usage"]["model_responses"] >= config["max_calls"]:
                    break
        else:
            code = subprocess.call(cmd, cwd=lab / "workspace", env=env)
    except (KeyboardInterrupt, subprocess.TimeoutExpired):
        code = 130
    finally:
        meta.update(finished_at=now(), exit_code=code)
        write_json(run / "run.json", meta)
        try:
            reconcile(run, key)
        except (OSError, ValueError, KeyError):
            print("Provider billing lookup unavailable; the conversation and Pi estimates remain saved.", file=sys.stderr)
        report = export_review(run)
        print(f"Review: {run / 'review.md'}\n" + json.dumps(report["usage"], indent=2))
    return code


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--lab", type=Path, default=DEFAULT_LAB)
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("setup")
    s.add_argument("--key-file", type=Path)
    s = sub.add_parser("start")
    s.add_argument("--questions", type=Path)
    s.add_argument("--label", default="user")
    s = sub.add_parser("report")
    s.add_argument("--run", type=Path)
    args = p.parse_args()
    try:
        if args.command == "setup":
            setup(args)
        elif args.command == "start":
            return start(args)
        else:
            run = args.run or max((args.lab.expanduser() / "runs").iterdir(), key=lambda d: d.name)
            report = export_review(run)
            print(str(run / "review.md"))
            print(json.dumps(report["usage"], indent=2))
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print("Lab error: " + redact(str(exc)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
