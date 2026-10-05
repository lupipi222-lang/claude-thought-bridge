import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from thought_bridge import server


class ServerIntegrationTests(unittest.TestCase):
    def test_separate_bubbles_are_stored_and_returned_in_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_settings = server.SETTINGS
            original_visible_at = server.last_visible_at
            server.SETTINGS = replace(
                original_settings,
                relay_db=Path(temp_dir) / "relay.sqlite3",
                relay_agent_token="agent-test-token",
                relay_user_token="user-test-token",
                presence_ttl_seconds=999999.0,
            )
            server.last_visible_at = 10**20
            try:
                with TestClient(server.app) as client:
                    for event_id, text in (
                        ("bubble-1", "第一条"),
                        ("bubble-2", "[[自我状态]]只在网页里[[/自我状态]]第二条"),
                        ("bubble-3", "第三条"),
                    ):
                        response = client.post(
                            "/api/events",
                            headers={"Authorization": "Bearer agent-test-token"},
                            json={
                                "event_id": event_id,
                                "ts": "2026-01-01T00:00:00+00:00",
                                "conversation_id": "main",
                                "kind": "reply",
                                "text": text,
                                "meta": {},
                            },
                        )
                        self.assertEqual(response.status_code, 200)

                    history = client.get(
                        "/api/history",
                        headers={"Authorization": "Bearer user-test-token"},
                    )
                    self.assertEqual(history.status_code, 200)
                    events = history.json()["events"]
                    self.assertEqual([event["event_id"] for event in events], ["bubble-1", "bubble-2", "bubble-3"])
                    self.assertEqual(len({event["id"] for event in events}), 3)

                    session = client.post(
                        "/api/session",
                        headers={"Authorization": "Bearer user-test-token"},
                    )
                    self.assertEqual(session.status_code, 200)
                    self.assertIn("HttpOnly", session.headers["set-cookie"])

                    client.post(
                        "/api/presence",
                        headers={"Authorization": "Bearer user-test-token"},
                        json={"visible": True},
                    )
                    self.assertGreater(server.last_visible_at, 0)
                    client.post(
                        "/api/presence",
                        headers={"Authorization": "Bearer user-test-token"},
                        json={"visible": False},
                    )
                    self.assertEqual(server.last_visible_at, 0)
            finally:
                server.SETTINGS = original_settings
                server.last_visible_at = original_visible_at


if __name__ == "__main__":
    unittest.main()
