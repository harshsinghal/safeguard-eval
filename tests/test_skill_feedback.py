"""Protect review fidelity and avoid exposing non-visible session content."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

LAB = runpy.run_path(str(Path(__file__).resolve().parents[1] / "tools" / "pi_skill_lab.py"))


def message(entry_id, parent, role, content, **extra):
    return {"type": "message", "id": entry_id, "parentId": parent,
            "message": {"role": role, "content": content, **extra}}


class FeedbackTests(unittest.TestCase):
    def test_switched_sessions_are_included_and_copied_ancestors_counted_once(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name)
            first, second = p / "session.jsonl", p / "fork.jsonl"
            a = message("a", None, "user", "An original question")
            b = message("b", "a", "assistant", [{"type": "text", "text": "One answer"}],
                        usage={"totalTokens": 10, "cost": {"total": .01}})
            first.write_text(json.dumps(a) + "\n" + json.dumps(b))
            second.write_text(json.dumps(a) + "\n" + json.dumps(b) + "\n" +
                              json.dumps(message("c", "b", "user", "A new branch question")))
            (p / "session-index.json").write_text(json.dumps([str(first), str(second)]))
            entries, warnings = LAB["run_entries"](p)
            self.assertFalse(warnings)
            report = LAB["summarize"](entries)
            self.assertEqual(len(report["turns"]), 3)
            self.assertEqual(report["usage"]["tokens"]["totalTokens"], 10)
            self.assertEqual(report["turns"][-1]["session_file"], "fork.jsonl")

    def test_visible_turns_preserve_branches_without_reasoning_or_tool_output(self):
        entries = [
            message("u", None, "user", "Explain policy models."),
            message("a", "u", "assistant", [{"type": "thinking", "thinking": "PRIVATE_REASONING"},
                                           {"type": "text", "text": "First answer."},
                                           {"type": "toolCall", "name": "read", "arguments": {"path": "SKILL.md"}}]),
            message("t", "a", "toolResult", [{"type": "text", "text": "PRIVATE_TOOL_OUTPUT"}]),
            message("b", "u", "assistant", [{"type": "text", "text": "Alternative answer."}]),
            {"type": "custom", "customType": "safeguard-feedback", "data": {"targetId": "b", "note": "Clearer"}},
        ]
        r = LAB["summarize"](entries)
        self.assertEqual([(t["id"], t["parent_id"]) for t in r["turns"]], [("u", None), ("a", "u"), ("b", "u")])
        self.assertNotIn("PRIVATE_", json.dumps(r))
        self.assertEqual(r["feedback"][0]["target_id"], "b")
        self.assertEqual(r["tool_calls"][0]["name"], "read")

    def test_usage_includes_all_branches_and_ancillary_work_without_double_reasoning(self):
        u = {"input": 10, "output": 5, "reasoning": 3, "cacheRead": 2, "cacheWrite": 1,
             "totalTokens": 18, "cost": {"total": 0.01}}
        entries = [message("a", "u", "assistant", [], usage=u),
                   message("b", "u", "assistant", [], usage=u),
                   {"type": "compaction", "usage": u},
                   {"type": "usage", "kind": "cache_warm", "usage": u},
                   message("t", "a", "toolResult", [], usage=u)]
        r = LAB["summarize"](entries)["usage"]
        self.assertEqual(r["tokens"]["totalTokens"], 90)
        self.assertEqual(r["tokens"]["output"], 25)
        self.assertAlmostEqual(r["pi_estimated_cost_usd"], 0.05)
        self.assertEqual(r["model_responses"], 2)

    def test_partial_log_and_empty_failed_answer_remain_visible(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name) / "session.jsonl"
            p.write_text(json.dumps(message("err", "u", "assistant", [], stopReason="error", errorMessage="Timeout")) + '\n{"type":')
            entries, warnings = LAB["read_entries"](p)
            self.assertEqual(len(warnings), 1)
            r = LAB["summarize"](entries)
            self.assertEqual(r["turns"][0]["error"], "Timeout")
            self.assertEqual(r["usage"]["assistant_messages_missing_usage"], 1)

    def test_export_masks_common_keys_and_omits_tool_arguments_from_readable_review(self):
        with tempfile.TemporaryDirectory() as name:
            p = Path(name)
            secret = "sk-or-v1-" + "a" * 60
            rows = [message("u", None, "user", "A pasted key: " + secret),
                    message("a", "u", "assistant", [{"type": "toolCall", "name": "bash", "arguments": {"command": "PRIVATE_COMMAND", "apiKey": "another-private-value"}}])]
            (p / "session.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
            LAB["export_review"](p)
            text = (p / "review.md").read_text()
            structured = (p / "review.json").read_text()
            self.assertNotIn(secret, text + structured)
            self.assertNotIn("another-private-value", structured)
            self.assertNotIn("PRIVATE_COMMAND", text)
            self.assertIn("PRIVATE_COMMAND", structured)
            self.assertIn(secret, (p / "session.jsonl").read_text())  # Native evidence untouched.


if __name__ == "__main__":
    unittest.main()
