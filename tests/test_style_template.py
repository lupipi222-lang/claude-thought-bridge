import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StyleTemplateTests(unittest.TestCase):
    def test_style_uses_generic_user_label_and_contains_only_content_rules(self):
        source = (ROOT / "templates" / "看清自己.md").read_text(encoding="utf-8")
        for phrase in (
            "description: 用简体中文写给user看的第一人称心里话",
            "## 写给user的心里话",
            "从这一刻最先抓住我的东西开始写",
            "已知事实、记忆、猜测和幻想要在语气上分得出来",
            "心里话不替代真正的说话与行动",
        ):
            self.assertIn(phrase, source)
        self.assertNotIn("小芦", source)
        self.assertNotIn("迟砚", source)
        self.assertNotIn("程序封装协议", source)
        self.assertNotIn("[[自我状态]]", source)
        self.assertNotIn("mcp__thought-bridge__reply", source)

    def test_sending_protocol_lives_in_claude_rules_template(self):
        source = (ROOT / "templates" / "CLAUDE_心里话相关规则.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "公开心声的内容与质感只以当前启用的「看清自己」user style 为准",
            "[[自我状态]]",
            "[[/自我状态]]",
            "mcp__thought-bridge__reply",
            "不要把公开心声作为 `thinking` 或 `action` 事件发送",
        ):
            self.assertIn(phrase, source)
        self.assertNotIn("小芦", source)
        self.assertNotIn("mcp__home__reply", source)


if __name__ == "__main__":
    unittest.main()
