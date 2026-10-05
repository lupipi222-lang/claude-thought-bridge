from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from contextlib import asynccontextmanager, closing
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .protocol import Event, notification_body
from .push import push_to_all


SETTINGS = Settings.from_env()
WEB_DIR = Path(__file__).with_name("web")


def connect_db() -> sqlite3.Connection:
    SETTINGS.relay_db.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(SETTINGS.relay_db)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with closing(connect_db()) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                ts TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                text TEXT NOT NULL,
                meta TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_events_conversation_id
                ON events(conversation_id, id);
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                endpoint TEXT PRIMARY KEY,
                subscription TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def authorize(request: Request, expected: str) -> None:
    if not expected:
        raise HTTPException(status_code=503, detail="server token is not configured")
    header = request.headers.get("authorization", "")
    supplied = header[7:] if header.lower().startswith("bearer ") else request.cookies.get("thought_bridge_session", "")
    if supplied != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


def row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "event_id": row["event_id"],
        "ts": row["ts"],
        "conversation_id": row["conversation_id"],
        "kind": row["kind"],
        "text": row["text"],
        "meta": json.loads(row["meta"] or "{}"),
    }


class EventHub:
    def __init__(self) -> None:
        self.queues: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self.queues.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        self.queues.discard(queue)

    def publish(self, event: dict) -> None:
        for queue in tuple(self.queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:
                    pass


HUB = EventHub()
# No visible client is known at process start, so replies may notify immediately.
last_visible_at = 0.0


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Claude Thought Bridge", lifespan=lifespan)


@app.post("/api/events")
async def receive_event(request: Request):
    authorize(request, SETTINGS.relay_agent_token)
    try:
        event = Event.from_dict(await request.json())
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not event.text:
        raise HTTPException(status_code=400, detail="text is required")
    with closing(connect_db()) as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO events(event_id, ts, conversation_id, kind, text, meta) VALUES(?,?,?,?,?,?)",
                (
                    event.event_id,
                    event.ts,
                    event.conversation_id,
                    event.kind,
                    event.text,
                    json.dumps(event.meta, ensure_ascii=False),
                ),
            )
            connection.commit()
            row_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            row = connection.execute("SELECT id FROM events WHERE event_id = ?", (event.event_id,)).fetchone()
            return {"ok": True, "duplicate": True, "id": row["id"] if row else None}
    wire = {"id": row_id, **event.to_dict()}
    HUB.publish(wire)

    body = notification_body(event.text) if event.kind == "reply" else None
    if body and time.time() - last_visible_at > SETTINGS.presence_ttl_seconds:
        payload = {
            "title": "New reply",
            "body": body,
            "url": "/",
            "event_id": event.event_id,
            # Unique per reply bubble: never replace another bubble's notification.
            "tag": f"reply-{event.event_id}",
        }
        asyncio.create_task(asyncio.to_thread(push_to_all, connect_db, SETTINGS, payload))
    return {"ok": True, "id": row_id, "event_id": event.event_id}


@app.get("/api/history")
async def history(request: Request, conversation_id: str = "main", limit: int = 200):
    authorize(request, SETTINGS.relay_user_token)
    safe_limit = max(1, min(500, int(limit)))
    with closing(connect_db()) as connection:
        rows = connection.execute(
            "SELECT * FROM events WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
            (conversation_id, safe_limit),
        ).fetchall()
    return {"events": [row_to_dict(row) for row in reversed(rows)]}


@app.post("/api/session")
async def create_session(request: Request):
    """Exchange the header token for an HttpOnly session cookie used by SSE."""
    authorize(request, SETTINGS.relay_user_token)
    response = JSONResponse({"ok": True})
    response.set_cookie(
        "thought_bridge_session",
        SETTINGS.relay_user_token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return response


@app.get("/api/stream")
async def stream(request: Request):
    authorize(request, SETTINGS.relay_user_token)
    queue = HUB.subscribe()

    async def generate():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            HUB.unsubscribe(queue)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/presence")
async def presence(request: Request):
    authorize(request, SETTINGS.relay_user_token)
    data = await request.json()
    global last_visible_at
    if data.get("visible"):
        last_visible_at = time.time()
    else:
        # The page reports the transition to background. Do not keep suppressing
        # notifications for the remainder of the visibility TTL.
        last_visible_at = 0.0
    return {"ok": True}


@app.get("/api/push/public-key")
async def push_public_key(request: Request):
    authorize(request, SETTINGS.relay_user_token)
    return {"public_key": SETTINGS.vapid_public_key}


@app.post("/api/push/subscribe")
async def push_subscribe(request: Request):
    authorize(request, SETTINGS.relay_user_token)
    subscription = await request.json()
    endpoint = str(subscription.get("endpoint") or "")
    if not endpoint:
        raise HTTPException(status_code=400, detail="endpoint is required")
    with closing(connect_db()) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO push_subscriptions(endpoint, subscription) VALUES(?,?)",
            (endpoint, json.dumps(subscription, ensure_ascii=False)),
        )
        connection.commit()
    return {"ok": True}


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")


def main() -> None:
    import uvicorn

    uvicorn.run(
        "thought_bridge.server:app",
        host=SETTINGS.relay_bind_host,
        port=SETTINGS.relay_bind_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
