from __future__ import annotations

import html
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .config import Settings
from .protocol import Event, split_self_state


def _post_json(url: str, payload: dict, headers: dict | None = None, timeout: int = 15) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw) if raw else {}


class Sink:
    def send(self, event: Event) -> None:
        raise NotImplementedError


@dataclass
class RelaySink(Sink):
    base_url: str
    event_path: str
    token: str

    def send(self, event: Event) -> None:
        if not self.token:
            raise RuntimeError("RELAY_AGENT_TOKEN is empty")
        _post_json(
            f"{self.base_url}{self.event_path}",
            event.to_dict(),
            {"Authorization": f"Bearer {self.token}"},
        )


@dataclass
class TelegramSink(Sink):
    api_base: str
    bot_token: str
    chat_id: str

    @property
    def endpoint(self) -> str:
        return f"{self.api_base}/bot{self.bot_token}/sendMessage"

    def _send(self, text: str, *, silent: bool, wrapper: str = "{}") -> None:
        if not self.bot_token or not self.chat_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty")
        for part in _split_telegram(text, limit=3500):
            _post_json(
                self.endpoint,
                {
                    "chat_id": self.chat_id,
                    # Escape each chunk before adding markup so a split can never
                    # cut an HTML entity or leave a Telegram tag unclosed.
                    "text": wrapper.format(html.escape(part)),
                    "parse_mode": "HTML",
                    "disable_notification": silent,
                },
            )

    def send(self, event: Event) -> None:
        if event.kind == "thinking":
            self._send(event.text, silent=True, wrapper="<blockquote expandable>{}</blockquote>")
            return
        if event.kind == "action":
            self._send(event.text, silent=True, wrapper="<code>⚙ {}</code>")
            return
        state, body = split_self_state(event.text)
        if state:
            self._send(state, silent=True, wrapper="<blockquote expandable>🫧 {}</blockquote>")
        if body:
            self._send(body, silent=False)


class MultiSink(Sink):
    def __init__(self, sinks: list[Sink]) -> None:
        self.sinks = sinks

    def send(self, event: Event) -> None:
        errors: list[str] = []
        for sink in self.sinks:
            try:
                sink.send(event)
            except Exception as exc:
                errors.append(f"{type(sink).__name__}: {type(exc).__name__}: {exc}")
        if errors:
            raise RuntimeError("; ".join(errors))


def _split_telegram(text: str, limit: int = 3800) -> list[str]:
    if len(text) <= limit:
        return [text]
    parts: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        parts.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    if remaining:
        parts.append(remaining)
    return parts


def build_sinks(settings: Settings) -> MultiSink:
    sinks: list[Sink] = []
    if "relay" in settings.sinks:
        sinks.append(RelaySink(settings.relay_url, settings.relay_event_path, settings.relay_agent_token))
    if "telegram" in settings.sinks:
        sinks.append(TelegramSink(settings.telegram_api_base, settings.telegram_bot_token, settings.telegram_chat_id))
    if not sinks:
        raise RuntimeError("BRIDGE_SINKS did not select relay or telegram")
    return MultiSink(sinks)
