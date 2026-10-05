from __future__ import annotations

import re


PATTERNS = [
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:Bearer\s+)[A-Za-z0-9._~+/-]{16,}", re.I),
    re.compile(r"(?i)(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
]


def redact(text: str, mode: str = "common") -> str:
    if mode in {"none", "off", "0"}:
        return text
    out = text
    for pattern in PATTERNS:
        out = pattern.sub("[REDACTED]", out)
    return out
