from __future__ import annotations

import glob
import json
import os
import re
from pathlib import Path

from .action_labels import describe_tool
from .protocol import Event
from .redact import redact


CHANNEL_RE = re.compile(r"<channel\b[^>]*\bchat_id=[\"']([^\"']+)[\"']", re.I)


class TranscriptTailer:
    def __init__(
        self,
        pattern: str,
        state_path: Path,
        *,
        redact_mode: str = "common",
        auto_reply: bool = False,
        start_at_end: bool = True,
    ) -> None:
        self.pattern = pattern
        self.state_path = state_path
        self.redact_mode = redact_mode
        self.auto_reply = auto_reply
        self.start_at_end = start_at_end
        self.path: str | None = None
        self.offset = 0
        self.conversation_id = "main"
        self._load_state()

    def _load_state(self) -> None:
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self.path = data.get("path")
            self.offset = int(data.get("offset", 0))
            self.conversation_id = str(data.get("conversation_id") or "main")
        except Exception:
            return

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temp.write_text(
            json.dumps(
                {"path": self.path, "offset": self.offset, "conversation_id": self.conversation_id},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        os.replace(temp, self.state_path)

    def latest_path(self) -> str | None:
        files = [path for path in glob.glob(self.pattern, recursive=True) if os.path.isfile(path)]
        return max(files, key=os.path.getmtime) if files else None

    def poll(self) -> list[Event]:
        newest = self.latest_path()
        if not newest:
            return []
        if newest != self.path:
            self.path = newest
            self.offset = os.path.getsize(newest) if self.start_at_end else 0
            self.conversation_id = "main"
            self._save_state()
            return []
        size = os.path.getsize(newest)
        if size < self.offset:
            self.offset = 0
        if size == self.offset:
            return []

        start = self.offset
        with open(newest, "rb") as handle:
            handle.seek(start)
            raw = handle.read()
        # Only consume newline-terminated records. A writer may still be appending
        # the final JSON object when we poll.
        boundary = raw.rfind(b"\n")
        if boundary < 0:
            return []
        complete = raw[: boundary + 1]
        self.offset = start + len(complete)
        events: list[Event] = []
        for line in complete.decode("utf-8", errors="ignore").splitlines():
            try:
                entry = json.loads(line)
            except (TypeError, ValueError):
                continue
            events.extend(self.events_from_entry(entry))
        self._save_state()
        return events

    def events_from_entry(self, entry: dict) -> list[Event]:
        entry_type = entry.get("type")
        message = entry.get("message") if isinstance(entry.get("message"), dict) else {}
        content = message.get("content")
        if entry_type == "user":
            text = content if isinstance(content, str) else ""
            if isinstance(content, list):
                text = next(
                    (str(block.get("text", "")) for block in content if isinstance(block, dict) and block.get("type") == "text"),
                    "",
                )
            match = CHANNEL_RE.search(text)
            if match:
                self.conversation_id = match.group(1)
            return []
        if entry_type != "assistant" or not isinstance(content, list):
            return []

        output: list[Event] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "thinking":
                text = redact(str(block.get("thinking") or "").strip(), self.redact_mode)
                if text:
                    output.append(Event("thinking", text, self.conversation_id))
            elif block_type == "tool_use":
                label = describe_tool(str(block.get("name") or ""), block.get("input"))
                if label:
                    output.append(Event("action", label, self.conversation_id))
            elif block_type == "text" and self.auto_reply:
                text = redact(str(block.get("text") or "").strip(), self.redact_mode)
                if text:
                    output.append(Event("reply", text, self.conversation_id))
        return output
