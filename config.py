import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("HONAR_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!").strip() or "!"

if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing. Add it in Railway Variables / Environment Variables."
    )


# ============================================================
# HMB NEXUS PRESENCE SETTINGS
# ============================================================
#
# These control the BOT presence. Rich Presence artwork cannot
# be sent by bot users through the Gateway; see main.py.
#

HMB_APPLICATION_ID = os.getenv(
    "DISCORD_APPLICATION_ID",
    "",
).strip()

HMB_PRESENCE_NAME = os.getenv(
    "HMB_PRESENCE_NAME",
    "HMB • NEXUS",
).strip() or "HMB • NEXUS"

HMB_PRESENCE_STATE = os.getenv(
    "HMB_PRESENCE_STATE",
    "Music • Moderation • Games • Economy",
).strip() or "Music • Moderation • Games • Economy"
