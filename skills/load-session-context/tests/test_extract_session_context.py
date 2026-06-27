import importlib.util
import json
import tempfile
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts/extract_session_context.py"


def load_extractor():
    spec = importlib.util.spec_from_file_location("extract_session_context", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExtractSessionContextTests(unittest.TestCase):
    def setUp(self):
        self.extractor = load_extractor()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.rollout = Path(self.tmpdir.name) / "rollout.jsonl"

    def tearDown(self):
        self.tmpdir.cleanup()

    def write_jsonl(self, rows):
        with self.rollout.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")

    def test_extracts_latest_replacement_history_and_tail(self):
        self.write_jsonl(
            [
                {
                    "timestamp": "2026-06-01T00:00:00Z",
                    "type": "session_meta",
                    "payload": {
                        "id": "session-1",
                        "cwd": "/repo",
                    },
                },
                {
                    "timestamp": "2026-06-01T00:00:01Z",
                    "type": "compacted",
                    "payload": {
                        "window_number": 1,
                        "window_id": "window-old",
                        "replacement_history": [
                            {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": "old prompt"}],
                            }
                        ],
                    },
                },
                {
                    "timestamp": "2026-06-01T00:00:02Z",
                    "type": "compacted",
                    "payload": {
                        "window_number": 2,
                        "window_id": "window-new",
                        "replacement_history": [
                            {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": "load this"}],
                            },
                            {
                                "type": "message",
                                "role": "assistant",
                                "content": [{"type": "output_text", "text": "loaded"}],
                            },
                            {
                                "type": "compaction",
                                "id": "cmp_123",
                                "encrypted_content": "opaque",
                            },
                        ],
                    },
                },
                {
                    "timestamp": "2026-06-01T00:00:03Z",
                    "type": "event_msg",
                    "payload": {
                        "type": "agent_message",
                        "message": "tail status",
                    },
                },
                {
                    "timestamp": "2026-06-01T00:00:04Z",
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "name": "exec_command",
                        "arguments": json.dumps({"cmd": "git status --short"}),
                    },
                },
            ]
        )

        report = self.extractor.extract_context(self.rollout, max_tail_events=10)

        self.assertEqual(report["session"]["id"], "session-1")
        self.assertEqual(report["latest_compaction"]["window_id"], "window-new")
        self.assertEqual(report["latest_compaction"]["messages"][0]["text"], "load this")
        self.assertEqual(report["latest_compaction"]["messages"][1]["text"], "loaded")
        self.assertEqual(report["latest_compaction"]["encrypted_compaction_count"], 1)
        self.assertEqual(report["tail"][0]["message"], "tail status")
        self.assertEqual(report["tail"][1]["command"], "git status --short")

    def test_resolves_rollout_by_session_id(self):
        session_dir = Path(self.tmpdir.name) / "sessions"
        nested = session_dir / "2026" / "06" / "01"
        nested.mkdir(parents=True)
        rollout = nested / "rollout-2026-06-01T00-00-00-session-2.jsonl"
        rollout.write_text(
            json.dumps({"type": "session_meta", "payload": {"id": "session-2"}}) + "\n",
            encoding="utf-8",
        )

        resolved = self.extractor.resolve_rollout_path("session-2", sessions_root=session_dir)

        self.assertEqual(resolved, rollout.resolve())

    def test_limits_latest_replacement_history_messages(self):
        self.write_jsonl(
            [
                {
                    "timestamp": "2026-06-01T00:00:00Z",
                    "type": "compacted",
                    "payload": {
                        "replacement_history": [
                            {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text": f"message {idx}"}],
                            }
                            for idx in range(5)
                        ],
                    },
                },
            ]
        )

        report = self.extractor.extract_context(self.rollout, max_history_messages=2)

        messages = report["latest_compaction"]["messages"]
        self.assertEqual([message["text"] for message in messages], ["message 3", "message 4"])
        self.assertEqual(report["latest_compaction"]["omitted_message_count"], 3)


if __name__ == "__main__":
    unittest.main()
