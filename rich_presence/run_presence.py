"""HMB NEXUS desktop Rich Presence companion.

Run this on the same computer as Discord Desktop. It uses Discord's official
local RPC protocol, so custom Rich Presence assets can be shown to other users.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from rpc_client import DiscordRPC, DiscordRPCError

APP_ID = os.getenv("DISCORD_APPLICATION_ID", "1540575563607969832").strip()
LARGE_IMAGE = os.getenv("HMB_LARGE_IMAGE_KEY", "").strip()
SMALL_IMAGE = os.getenv("HMB_SMALL_IMAGE_KEY", "").strip()
INVITE_URL = os.getenv("HMB_RP_BUTTON_URL", "").strip()

START = int(os.getenv("HMB_RP_START_TIMESTAMP", str(int(datetime.now(timezone.utc).timestamp()))))


def build_activity() -> dict:
    activity: dict = {
        "type": 0,
        "details": os.getenv("HMB_RP_DETAILS", "HMB NEXUS • Discord Bot"),
        "state": os.getenv("HMB_RP_STATE", "Music • Moderation • Games • Economy"),
        "timestamps": {"start": START},
        "party": {
            "id": os.getenv("HMB_RP_PARTY_ID", "HMB-NEXUS"),
            "size": [
                int(os.getenv("HMB_RP_PARTY_SIZE", "1")),
                int(os.getenv("HMB_RP_PARTY_MAX", "5")),
            ],
        },
    }

    assets: dict = {}
    if LARGE_IMAGE:
        assets["large_image"] = LARGE_IMAGE
        assets["large_text"] = os.getenv("HMB_RP_LARGE_TEXT", "HMB • NEXUS")
    if SMALL_IMAGE:
        assets["small_image"] = SMALL_IMAGE
        assets["small_text"] = os.getenv("HMB_RP_SMALL_TEXT", "Online")
    if assets:
        activity["assets"] = assets

    if INVITE_URL:
        activity["buttons"] = [{"label": "HMB NEXUS", "url": INVITE_URL}]

    return activity


def main() -> None:
    rpc = DiscordRPC(APP_ID)
    try:
        rpc.connect()
        rpc.set_activity(build_activity())
        print("HMB NEXUS Rich Presence is active on Discord Desktop.")
        print("Close this program to clear the local RPC connection.")
        while True:
            time.sleep(15)
            rpc.set_activity(build_activity())
    except KeyboardInterrupt:
        print("Stopping HMB NEXUS Rich Presence...")
    except DiscordRPCError as exc:
        print(f"Rich Presence error: {exc}")
        raise SystemExit(1)
    finally:
        rpc.close()


if __name__ == "__main__":
    main()
