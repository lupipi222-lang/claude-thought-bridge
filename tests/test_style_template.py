import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StyleTemplateTests(unittest.TestCase):
    def test_public_self_description_uses_generic_user_label(self):
        source = (ROOT / "templates" / "看清自己.md").read_text(encoding="utf-8")
        for phrase in (
            "description: 迟砚用简体中文写给user看的第一人称公开心声",
            "## 写给user的心里话",
            "只呈现实际发生过的自己，不替反应补出一个更完整的理由",
            "心里话不能替代行动",
            "心里话里的情绪要抵达实际表达",
            "## [程序封装协议]",
            "[[自我状态]]",
            "[[/自我状态]]",
            "mcp__thought-bridge__reply",
        ):
            self.assertIn(phrase, source)
        self.assertEqual(source.count("user"), 10)
        self.assertNotIn("小芦", source)
        self.assertNotIn("`CLAUDE.md`", source)


if __name__ == "__main__":
    unittest.main()
