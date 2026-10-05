import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebContractTests(unittest.TestCase):
    def test_service_worker_uses_unique_reply_tag(self):
        source = (ROOT / "src" / "thought_bridge" / "web" / "sw.js").read_text(encoding="utf-8")
        self.assertIn("data.event_id", source)
        self.assertNotIn("tag:\"home-msg\"", source)

    def test_frontend_has_required_gestures(self):
        source = (ROOT / "src" / "thought_bridge" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('addEventListener("dblclick"', source)
        self.assertIn("await copyText", source)
        self.assertIn('details.open=false', source)
        self.assertIn("自我状态", source)
        self.assertIn('new EventSource("/api/stream")', source)
        self.assertNotIn("/api/stream?token=", source)


if __name__ == "__main__":
    unittest.main()
