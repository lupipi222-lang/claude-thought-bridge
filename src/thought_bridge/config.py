from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env_file(path: Path | None = None) -> Path | None:
    """Load a tiny KEY=VALUE file without overwriting real environment vars."""
    chosen = path or Path(os.environ.get("BRIDGE_ENV_FILE", PROJECT_ROOT / ".env"))
    if not chosen.exists():
        return None
    for raw in chosen.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if value[:1] == value[-1:] and value[:1] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)
    return chosen


def as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def as_float(value: str | None, default: float) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def as_int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    sinks: tuple[str, ...]
    transcript_glob: str
    state_dir: Path
    poll_seconds: float
    redact_mode: str
    auto_reply_from_transcript: bool
    relay_bind_host: str
    relay_bind_port: int
    relay_url: str
    relay_event_path: str
    relay_agent_token: str
    relay_user_token: str
    relay_db: Path
    presence_ttl_seconds: float
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_api_base: str
    vapid_public_key: str
    vapid_private_key: str
    vapid_subject: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        sink_names = tuple(
            part.strip().lower()
            for part in os.environ.get("BRIDGE_SINKS", "relay").split(",")
            if part.strip()
        )
        state_dir = Path(os.environ.get("BRIDGE_STATE_DIR", PROJECT_ROOT / "state")).expanduser()
        return cls(
            sinks=sink_names,
            transcript_glob=os.environ.get("CLAUDE_TRANSCRIPT_GLOB", ""),
            state_dir=state_dir,
            poll_seconds=as_float(os.environ.get("BRIDGE_POLL_SECONDS"), 1.0),
            redact_mode=os.environ.get("BRIDGE_REDACT", "common").strip().lower(),
            auto_reply_from_transcript=as_bool(os.environ.get("AUTO_REPLY_FROM_TRANSCRIPT")),
            relay_bind_host=os.environ.get("RELAY_BIND_HOST", "127.0.0.1"),
            relay_bind_port=as_int(os.environ.get("RELAY_BIND_PORT"), 8787),
            relay_url=os.environ.get("RELAY_URL", "http://127.0.0.1:8787").rstrip("/"),
            relay_event_path=os.environ.get("RELAY_EVENT_PATH", "/api/events"),
            relay_agent_token=os.environ.get("RELAY_AGENT_TOKEN", ""),
            relay_user_token=os.environ.get("RELAY_USER_TOKEN", ""),
            relay_db=Path(os.environ.get("RELAY_DB", state_dir / "relay.sqlite3")).expanduser(),
            presence_ttl_seconds=as_float(os.environ.get("PRESENCE_TTL_SECONDS"), 20.0),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
            telegram_api_base=os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/"),
            vapid_public_key=os.environ.get("VAPID_PUBLIC_KEY", ""),
            vapid_private_key=os.environ.get("VAPID_PRIVATE_KEY", ""),
            vapid_subject=os.environ.get("VAPID_SUBJECT", "mailto:admin@example.com"),
        )

    def ensure_state_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
