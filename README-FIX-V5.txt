HMB NEXUS V5 - Railway build fix

This version fixes the Railway build failure:
ModuleNotFoundError: No module named 'bgutil_ytdlp_pot_provider'

The bgutil package is a yt-dlp plugin, not a top-level Python module. The old
Dockerfile incorrectly tried to import it directly. V5 verifies the package
with `pip show` instead and runs the bgutil POT HTTP provider on localhost:4416.

Railway:
1. Replace the project files with this ZIP.
2. Redeploy.
3. Do NOT add YOUTUBE_COOKIE.
4. Keep DISCORD_TOKEN in Railway Variables.
5. Test /play or the Music Panel Search.

The bot config uses:
youtubepot-bgutilhttp:base_url=http://127.0.0.1:4416

The POT provider is started automatically by Docker CMD before the bot.
