import unittest

from thought_bridge.protocol import notification_body, split_self_state


class ProtocolTests(unittest.TestCase):
    def test_split_self_state(self):
        state, body = split_self_state(
            "[[自我状态]]\n只在折叠区\n[[/自我状态]]\n——\n正式回复"
        )
        self.assertEqual(state, "只在折叠区")
        self.assertEqual(body, "正式回复")

    def test_notification_excludes_self_state(self):
        text = "[[自我状态]]不进通知[[/自我状态]]\n正文第一泡"
        self.assertEqual(notification_body(text), "正文第一泡")

    def test_self_state_only_has_no_notification(self):
        self.assertIsNone(notification_body("[[自我状态]]只有自述[[/自我状态]]"))

    def test_notification_limit(self):
        body = notification_body("a" * 200, limit=20)
        self.assertEqual(body, "a" * 20 + "…")


if __name__ == "__main__":
    unittest.main()
