import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PREFIX = "!"

if not DISCORD_TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN دانەنراوە لە Environment Variables. لە Hosting ـەکەت Secret/Environment Variable ـێک بە ناوی DISCORD_TOKEN زیاد بکە.")
