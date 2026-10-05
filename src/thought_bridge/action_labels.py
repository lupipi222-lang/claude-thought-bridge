from __future__ import annotations

from pathlib import PurePath


SKIP_TOOLS = {
    "TodoWrite",
    "ToolSearch",
    "mcp__thought-bridge__reply",
    "mcp__thought_bridge__reply",
}


def short_path(value: object) -> str:
    raw = str(value or "").replace("\\", "/").rstrip("/")
    return PurePath(raw).name if raw else "文件"


def describe_tool(name: str, args: dict | None) -> str | None:
    if not name or name in SKIP_TOOLS:
        return None
    data = args if isinstance(args, dict) else {}
    if name == "Read":
        path = str(data.get("file_path", ""))
        if path.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic")):
            return "看了一张图"
        if path.lower().endswith((".mp3", ".m4a", ".wav", ".ogg")):
            return "听了一段音频"
        return f"看了 {short_path(path)}"
    if name == "Write":
        return f"写了 {short_path(data.get('file_path'))}"
    if name == "Edit":
        return f"改了 {short_path(data.get('file_path'))}"
    if name in {"Glob", "Find"}:
        return "找了找文件"
    if name in {"Grep", "Search"}:
        return "在文件里查了查"
    if name in {"Bash", "PowerShell", "exec_command"}:
        return str(data.get("description") or data.get("title") or "执行了一条命令").strip()
    if name in {"WebSearch", "search_query"}:
        return "查了查网页"
    if name in {"WebFetch", "open"}:
        return "打开了一个网页"
    if name in {"Task", "Agent", "spawn_agent"}:
        return "请了一个帮手"
    if name == "Skill":
        return "使用了一个技能"
    if name.startswith("mcp__"):
        return "调用了一个外部工具"
    return None
