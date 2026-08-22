import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("HONAR_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!").strip() or "!"

if not DISCORD_TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing. Add it in Railway Variables / Environment Variables."
    )
