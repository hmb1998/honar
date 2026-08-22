"""Minimal Discord Rich Presence RPC client.

Uses Discord's documented local RPC protocol. This updates the Rich Presence
of the Discord desktop user running this process; it does NOT update a bot
user on Discord's Gateway.
"""

from __future__ import annotations

import json
import os
import socket
import struct
import sys
import uuid
from pathlib import Path
from typing import Any


class DiscordRPCError(RuntimeError):
    pass


def _ipc_candidates() -> list[str]:
    if sys.platform.startswith("win"):
        return [rf"\\\\?\\pipe\\discord-ipc-{i}" for i in range(10)]

    candidates: list[str] = []
    if sys.platform == "darwin":
        candidates.extend(
            [
                str(Path.home() / "Library/Application Support/discord/discord-ipc-0"),
                "/tmp/discord-ipc-0",
            ]
        )
    else:
        runtime = os.getenv("XDG_RUNTIME_DIR")
        if runtime:
            candidates.append(os.path.join(runtime, "discord-ipc-0"))
        candidates.extend(
            [
                "/tmp/discord-ipc-0",
                str(Path.home() / ".config/discord/discord-ipc-0"),
            ]
        )

    return [path.replace("discord-ipc-0", f"discord-ipc-{i}") for path in candidates for i in range(10)]


class DiscordRPC:
    def __init__(self, client_id: str):
        self.client_id = str(client_id).strip()
        if not self.client_id.isdigit():
            raise ValueError("Discord application ID must be numeric.")
        self.sock: socket.socket | None = None

    def connect(self) -> None:
        last_error: Exception | None = None
        for path in _ipc_candidates():
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(path)
                self.sock = sock
                self._send(0, {"v": 1, "client_id": self.client_id})
                self._recv()
                return
            except (OSError, DiscordRPCError) as exc:
                last_error = exc
                try:
                    sock.close()
                except Exception:
                    pass

        raise DiscordRPCError(
            "Discord Desktop IPC was not found. Start the Discord desktop app "
            "and run this companion on the same computer."
        ) from last_error

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def _send(self, opcode: int, payload: dict[str, Any]) -> None:
        if self.sock is None:
            raise DiscordRPCError("RPC is not connected.")
        data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self.sock.sendall(struct.pack("<II", opcode, len(data)) + data)

    def _recv(self) -> tuple[int, dict[str, Any]]:
        if self.sock is None:
            raise DiscordRPCError("RPC is not connected.")

        header = self._read_exact(8)
        opcode, length = struct.unpack("<II", header)
        raw = self._read_exact(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise DiscordRPCError("Discord RPC returned invalid JSON.") from exc
        if isinstance(payload, dict) and payload.get("evt") == "ERROR":
            raise DiscordRPCError(str(payload.get("data") or payload))
        return opcode, payload

    def _read_exact(self, size: int) -> bytes:
        if self.sock is None:
            raise DiscordRPCError("RPC is not connected.")
        chunks: list[bytes] = []
        remaining = size
        while remaining:
            chunk = self.sock.recv(remaining)
            if not chunk:
                raise DiscordRPCError("Discord RPC connection closed.")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def set_activity(self, activity: dict[str, Any]) -> None:
        nonce = str(uuid.uuid4())
        self._send(
            1,
            {
                "cmd": "SET_ACTIVITY",
                "args": {"pid": os.getpid(), "activity": activity},
                "nonce": nonce,
            },
        )
        self._recv()
