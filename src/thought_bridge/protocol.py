from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


SELF_STATE_RE = re.compile(
    r"^\s*\[\[自我状态[：:]?\]\]([\s\S]*?)\[\[/自我状态\]\]",
    re.MULTILINE,
)
ALL_SELF_STATE_RE = re.compile(
    r"\[\[自我状态[：:]?\]\][\s\S]*?\[\[/自我状态\]\]",
    re.MULTILINE,
)
SPACE_RE = re.compile(r"\s+")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_self_state(text: str | None) -> tuple[str, str]:
    raw = text or ""
    match = SELF_STATE_RE.match(raw)
    if not match:
        return "", raw.strip()
    state = match.group(1).strip()
    body = raw[match.end() :].strip()
    body = re.sub(r"^[—-]{2,}\s*", "", body).strip()
    return state, body


def notification_body(text: str | None, limit: int = 160) -> str | None:
    """Return only user-visible reply text; never leak self-state metadata."""
    visible = ALL_SELF_STATE_RE.sub(" ", text or "")
    body = SPACE_RE.sub(" ", visible).strip()
    if not body:
        return None
    if len(body) > limit:
        body = body[:limit].rstrip() + "…"
    return body


@dataclass(slots=True)
class Event:
    kind: str
    text: str
    conversation_id: str = "main"
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = field(default_factory=utc_now)
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.kind not in {"thinking", "action", "reply"}:
            raise ValueError(f"unsupported event kind: {self.kind}")
        self.text = str(self.text or "").strip()
        self.conversation_id = str(self.conversation_id or "main")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        return cls(
            kind=data.get("kind", "reply"),
            text=data.get("text", ""),
            conversation_id=data.get("conversation_id", "main"),
            event_id=data.get("event_id") or str(uuid.uuid4()),
            ts=data.get("ts") or utc_now(),
            meta=data.get("meta") if isinstance(data.get("meta"), dict) else {},
        )
