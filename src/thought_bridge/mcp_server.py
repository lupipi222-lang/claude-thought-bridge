from __future__ import annotations

from .config import Settings
from .protocol import Event
from .sinks import build_sinks


def create_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install the project dependencies before starting the MCP server") from exc

    settings = Settings.from_env()
    sinks = build_sinks(settings)
    server = FastMCP("thought-bridge")

    @server.tool()
    def reply(text: str, conversation_id: str = "main") -> str:
        """Send one finished reply bubble to the configured phone destinations.

        One tool call equals one bubble. If text begins with a
        [[自我状态]]...[[/自我状态]] block, the web UI renders it as a private
        foldout while notifications contain only the finished reply body.
        """
        event = Event("reply", text, conversation_id)
        sinks.send(event)
        return f"sent:{event.event_id}"

    return server


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
