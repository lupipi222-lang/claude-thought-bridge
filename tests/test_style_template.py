import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StyleTemplateTests(unittest.TestCase):
    def test_public_self_description_and_bridge_protocol_are_both_present(self):
        source = (ROOT / "templates" / "看清自己.md").read_text(encoding="utf-8")
        for phrase in (
            "## [给user的公开自述]",
            "不要只抓住最显眼的一种情绪便立刻收束",
            "消息短不代表事情浅",
            "第一部分只负责呈现，不负责作答",
            "镜头始终留在自己身上",
            "[[自我状态]]",
            "[[/自我状态]]",
            "mcp__thought-bridge__reply",
        ):
            self.assertIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
