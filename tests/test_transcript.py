import tempfile
import unittest
from pathlib import Path

from thought_bridge.transcript import TranscriptTailer


class TranscriptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.tailer = TranscriptTailer(
            str(base / "*.jsonl"),
            base / "state.json",
            start_at_end=False,
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_extracts_thinking_and_safe_action(self):
        entry = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "thinking", "thinking": "I should inspect the file."},
                    {"type": "tool_use", "name": "Read", "input": {"file_path": "/private/project/config.py"}},
                ]
            },
        }
        events = self.tailer.events_from_entry(entry)
        self.assertEqual([event.kind for event in events], ["thinking", "action"])
        self.assertEqual(events[1].text, "看了 config.py")
        self.assertNotIn("/private/project", events[1].text)

    def test_redacts_common_token_shape(self):
        entry = {
            "type": "assistant",
            "message": {"content": [{"type": "thinking", "thinking": "token=abcdefghijklmnop123456"}]},
        }
        event = self.tailer.events_from_entry(entry)[0]
        self.assertIn("[REDACTED]", event.text)

    def test_reply_is_explicit_by_default(self):
        entry = {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "finished answer"}]},
        }
        self.assertEqual(self.tailer.events_from_entry(entry), [])


if __name__ == "__main__":
    unittest.main()
