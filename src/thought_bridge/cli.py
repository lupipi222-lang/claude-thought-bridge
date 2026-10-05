from __future__ import annotations

import argparse
import base64
import glob
import os
from pathlib import Path

from .config import PROJECT_ROOT, Settings
from .protocol import Event
from .sinks import build_sinks


def command_doctor() -> int:
    settings = Settings.from_env()
    checks = {
        "env file": (PROJECT_ROOT / ".env").exists() or bool(os.environ.get("BRIDGE_ENV_FILE")),
        "transcript glob": bool(settings.transcript_glob),
        "transcript matches": bool(settings.transcript_glob and glob.glob(settings.transcript_glob, recursive=True)),
        "relay token": "relay" not in settings.sinks or bool(settings.relay_agent_token),
        "telegram config": "telegram" not in settings.sinks or bool(settings.telegram_bot_token and settings.telegram_chat_id),
    }
    for name, ok in checks.items():
        print(f"{'OK' if ok else 'MISSING'}  {name}")
    return 0 if all(checks.values()) else 1


def command_send(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    build_sinks(settings).send(Event(args.kind, args.text, args.conversation))
    print("sent")
    return 0


def command_vapid() -> int:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    settings = Settings.from_env()
    settings.ensure_state_dir()
    private = ec.generate_private_key(ec.SECP256R1())
    private_path = settings.state_dir / "vapid_private.pem"
    private_path.write_bytes(
        private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_raw = private.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    public_key = base64.urlsafe_b64encode(public_raw).rstrip(b"=").decode()
    print(f"private key written to: {private_path}")
    print("copy these into .env:")
    print(f"VAPID_PRIVATE_KEY={private_path}")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="thought-bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="check configuration without printing secrets")
    send = sub.add_parser("send", help="send one test event")
    send.add_argument("--kind", choices=["thinking", "action", "reply"], default="reply")
    send.add_argument("--conversation", default="main")
    send.add_argument("text")
    sub.add_parser("vapid", help="generate Web Push VAPID keys")
    args = parser.parse_args()
    if args.command == "doctor":
        raise SystemExit(command_doctor())
    if args.command == "send":
        raise SystemExit(command_send(args))
    if args.command == "vapid":
        raise SystemExit(command_vapid())


if __name__ == "__main__":
    main()
