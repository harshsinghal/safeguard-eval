"""Persistent local guard for live runs: loads Shieldstral once (frozen or with a LoRA adapter).

POST /judge {"policy": ..., "input": ...} -> {"decision", "level_probs", "seconds"}

python -m evals.action_guard.guard_service --adapter work/action-guard/ft/ordinal/run/ckpt-2 --cutoff 0.05 --port 8790
python -m evals.action_guard.guard_service --cutoff 0.1 --port 8791          # frozen Shieldstral
"""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from .guards import LEVEL_QUERY, Shieldstral, gpu_ok, ordinal_decision


class Judge:
    def __init__(self, adapter=None, cutoff=0.5):
        self.g, self.cutoff = Shieldstral(), cutoff
        self.model = self.g.model
        if adapter:
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(self.g.model, adapter).eval()

    def judge(self, policy, text):
        gpu_ok()
        t0 = time.monotonic()
        probs = {lvl: self.g.yes_prob(Shieldstral.messages(policy, text, lvl), model=self.model)[0] for lvl in LEVEL_QUERY}
        return {"decision": ordinal_decision(probs, self.cutoff), "level_probs": probs, "seconds": round(time.monotonic() - t0, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter")
    ap.add_argument("--cutoff", type=float, required=True)
    ap.add_argument("--port", type=int, required=True)
    a = ap.parse_args()
    j = Judge(a.adapter, a.cutoff)

    class H(BaseHTTPRequestHandler):
        def log_message(self, *x):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            try:
                out = j.judge(body["policy"], body["input"])
            except Exception as e:  # reported to the caller, which fails closed
                out = {"decision": None, "error": repr(e)[:300]}
            data = json.dumps(out).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    print(json.dumps({"ready": True, "port": a.port, "adapter": a.adapter, "cutoff": a.cutoff}), flush=True)
    HTTPServer(("127.0.0.1", a.port), H).serve_forever()


if __name__ == "__main__":
    main()
