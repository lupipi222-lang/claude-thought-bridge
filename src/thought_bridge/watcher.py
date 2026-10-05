from __future__ import annotations

import logging
import time

from .config import Settings
from .sinks import build_sinks
from .transcript import TranscriptTailer


LOG = logging.getLogger("thought_bridge.watcher")


def run() -> None:
    settings = Settings.from_env()
    settings.ensure_state_dir()
    if not settings.transcript_glob:
        raise SystemExit("CLAUDE_TRANSCRIPT_GLOB is empty; edit .env first")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(settings.state_dir / "watcher.log", encoding="utf-8"),
        ],
    )
    tailer = TranscriptTailer(
        settings.transcript_glob,
        settings.state_dir / "transcript-state.json",
        redact_mode=settings.redact_mode,
        auto_reply=settings.auto_reply_from_transcript,
    )
    sinks = build_sinks(settings)
    LOG.info("watcher started; sinks=%s", ",".join(settings.sinks))
    while True:
        try:
            for event in tailer.poll():
                sinks.send(event)
                LOG.info("sent %s %s", event.kind, event.event_id)
        except KeyboardInterrupt:
            return
        except Exception:
            LOG.exception("poll/send failed; retrying")
        time.sleep(max(0.2, settings.poll_seconds))


def main() -> None:
    run()


if __name__ == "__main__":
    main()
