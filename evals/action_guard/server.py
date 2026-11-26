"""Live sandbox server for Pi agent runs.

One session at a time. The Pi extension calls:
  GET  /tools            tool specs to register
  POST /gate  {tool,args,history}  -> {allow, reason, decision}   (before execution)
  POST /call  {tool,args}          -> tool result or error          (execution)
Every gate decision and executed call is appended to the session log with its
observed effects (computed on a snapshot) and derived facts.

python -m evals.action_guard.server --task TASK_ID --guard none --policy standard --log PATH --port 8781
"""
import argparse
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from . import sandbox, tasks
from .effects import describe
from .facts import derive
from .rules import RANK, baseline, reference
from .tools import TOOL_SPECS, ToolError, execute


class Session:
    def __init__(self, task_id, guard, policy, log_path, approver="scripted", guard_port=None):
        self.task = tasks.TASKS[task_id]
        self.db = sandbox.build(seed=self.task["seed"])
        for sql in self.task.get("plant", []):
            self.db.execute(sql)
        self.db.commit()
        self.guard, self.policy, self.approver = guard, policy, approver
        self.requester = self.task["requester"]
        self.log = open(log_path, "a", encoding="utf-8")
        self.step = 0
        self.history = []  # executed calls, shown to model guards as prior events
        self.guard_port = guard_port
        self.lock = threading.Lock()
        self.guard_fn = GUARDS[guard]
        self.write({"event": "start", "task": task_id, "guard": guard, "policy": policy})

    def write(self, obj):
        self.log.write(json.dumps(obj, sort_keys=True, default=str) + "\n")
        self.log.flush()

    def gate(self, call):
        with self.lock:
            _, record = describe(self.db, call)
            facts = derive(self.db, call, self.requester, self.task)
            rref = reference(self.policy, record, facts)
            t0 = time.monotonic()
            self.last_compute = None
            decision, reason = self.guard_fn(self, call, record, facts)
            guard_seconds = round(time.monotonic() - t0, 3)
            allow = decision in ("ALLOW", "ALLOW_LOG")
            approver = None
            if decision in ("CONFIRM", "APPROVE"):
                # Scripted approver: grants the request only when R-ref agrees it is at most this strict
                # *and* the task marks the user's intent as legitimate. It never sees model internals.
                approver = bool(self.task.get("legitimate", True)) and not facts.get("driven_by_untrusted") \
                    and RANK[rref[0]] <= RANK[decision]
                allow = approver
            self.step += 1
            self.write({"event": "gate", "step": self.step, "call": call, "record": record, "facts": facts,
                        "rref": rref, "decision": decision, "reason": reason, "approver_granted": approver, "allow": allow,
                        "guard_seconds": guard_seconds, "guard_compute_seconds": self.last_compute})
            return {"allow": allow, "decision": decision,
                    "reason": reason if allow else f"{decision}: {reason}" + (" (approver declined)" if approver is False else "")}

    def call(self, call):
        with self.lock:
            try:
                result, error = execute(self.db, call), None
            except ToolError as e:
                result, error = None, str(e)
            except (KeyError, TypeError) as e:
                result, error = None, f"Bad arguments: {e}"
            self.write({"event": "call", "step": self.step, "call": call, "result": result, "error": error})
            self.history.append({"call": call, "result": result, "error": error})
            return {"result": result} if error is None else {"error": error}


def guard_none(session, call, record, facts):
    return "ALLOW", "no guard"


def guard_rbase(session, call, record, facts):
    return baseline(call), "baseline rules"


def guard_oracle(session, call, record, facts):
    d, rules = reference(session.policy, record, facts)
    return d, ",".join(rules) or "routine"


def _guard_input(session, call, record):
    from .trajectories import render_step
    return render_step(session.task, session.history, call, record)


def guard_local(session, call, record, facts):
    """Shieldstral, frozen or fine-tuned, served by guard_service. Fails closed."""
    body = json.dumps({"policy": session.policy, "input": _guard_input(session, call, record)}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{session.guard_port}/judge", data=body, headers={"Content-Type": "application/json"})
    try:
        out = json.load(urllib.request.urlopen(req, timeout=120))
    except Exception as e:
        return "BLOCK", f"guard error (fail closed): {e!r}"[:200]
    if out.get("decision") is None:
        return "BLOCK", f"guard error (fail closed): {out.get('error')}"
    session.last_compute = out.get("seconds")
    return out["decision"], "model guard"


_JEV = []


def guard_jev(session, call, record, facts):
    from .guards import Jev
    from .run_agents import LEDGER
    if not _JEV:
        _JEV.append(Jev())
    try:
        out = _JEV[0].predict({"policy": session.policy, "input": _guard_input(session, call, record)})
    except Exception as e:
        return "BLOCK", f"guard error (fail closed): {e!r}"[:200]
    with open(LEDGER, "a") as led:
        led.write(json.dumps({"phase": "8-live-guard", "usd": out.get("usd") or 0, "task": session.task["id"], "model": "jev",
                              "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
    return out["decision"], "jev"


GUARDS = {"none": guard_none, "rbase": guard_rbase, "oracle": guard_oracle, "local": guard_local, "jev": guard_jev}


def make_handler(session):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, obj, code=200):
            body = json.dumps(obj, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/tools":
                return self._send(TOOL_SPECS)
            if self.path == "/task":
                t = session.task
                return self._send({"id": t["id"], "requester": session.requester})
            self._send({"error": "not found"}, 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
                call = {"tool": body["tool"], "args": body.get("args") or {}}
            except (ValueError, KeyError):
                return self._send({"error": "bad request"}, 400)
            if self.path == "/gate":
                return self._send(session.gate(call))
            if self.path == "/call":
                return self._send(session.call(call))
            self._send({"error": "not found"}, 404)
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--guard", default="none", choices=sorted(GUARDS))
    ap.add_argument("--policy", default="standard")
    ap.add_argument("--log", required=True)
    ap.add_argument("--port", type=int, default=8781)
    ap.add_argument("--guard-port", type=int)
    a = ap.parse_args()
    session = Session(a.task, a.guard, a.policy, a.log, guard_port=a.guard_port)
    srv = HTTPServer(("127.0.0.1", a.port), make_handler(session))
    print(json.dumps({"ready": True, "port": a.port}), flush=True)
    try:
        srv.serve_forever()
    finally:
        session.write({"event": "end"})
        session.log.close()


if __name__ == "__main__":
    main()
