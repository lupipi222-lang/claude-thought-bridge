import unittest
from unittest.mock import patch

from thought_bridge.protocol import Event
from thought_bridge.sinks import TelegramSink


class TelegramSinkTests(unittest.TestCase):
    def test_state_is_silent_and_reply_notifies(self):
        sent = []
        sink = TelegramSink("https://api.telegram.org", "test-token", "test-chat")
        with patch("thought_bridge.sinks._post_json", side_effect=lambda url, payload: sent.append(payload) or {}):
            sink.send(Event("reply", "[[自我状态]]心里话[[/自我状态]]正式回复"))
        self.assertEqual(len(sent), 2)
        self.assertTrue(sent[0]["disable_notification"])
        self.assertIn("blockquote expandable", sent[0]["text"])
        self.assertFalse(sent[1]["disable_notification"])
        self.assertEqual(sent[1]["text"], "正式回复")

    def test_long_thinking_keeps_each_html_chunk_closed(self):
        sent = []
        sink = TelegramSink("https://api.telegram.org", "test-token", "test-chat")
        with patch("thought_bridge.sinks._post_json", side_effect=lambda url, payload: sent.append(payload) or {}):
            sink.send(Event("thinking", "<&>" * 2000))
        self.assertGreater(len(sent), 1)
        for payload in sent:
            self.assertTrue(payload["text"].startswith("<blockquote expandable>"))
            self.assertTrue(payload["text"].endswith("</blockquote>"))
            self.assertTrue(payload["disable_notification"])


if __name__ == "__main__":
    unittest.main()
