from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Callable

from .config import Settings


def push_to_all(
    connection_factory: Callable[[], sqlite3.Connection],
    settings: Settings,
    notification: dict,
) -> None:
    """Send Web Push without allowing push failures to affect message storage."""
    if not (settings.vapid_public_key and settings.vapid_private_key):
        return
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        return
    with closing(connection_factory()) as connection:
        rows = connection.execute("SELECT endpoint, subscription FROM push_subscriptions").fetchall()
    dead: list[str] = []
    payload = json.dumps(notification, ensure_ascii=False)
    for endpoint, raw in rows:
        try:
            subscription = json.loads(raw)
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
                ttl=120,
            )
        except WebPushException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in {404, 410}:
                dead.append(endpoint)
        except Exception:
            continue
    if dead:
        with closing(connection_factory()) as connection:
            connection.executemany("DELETE FROM push_subscriptions WHERE endpoint = ?", [(item,) for item in dead])
            connection.commit()
