# HONAR Discord Bot

A Python Discord bot with moderation, utility, economy, games, GitHub and YouTube music support.

## Railway deployment

1. Connect this repository to Railway.
2. Add the environment variable:
   - `DISCORD_TOKEN` = your Discord bot token
   - `BOT_PREFIX` = optional, default `!`
   - `GITHUB_TOKEN` or `HONAR_GITHUB_TOKEN` = optional
3. Railway detects the included `Dockerfile`.
4. Redeploy.

The Docker image uses Python 3.12 and installs FFmpeg, avoiding the Python 3.13 `audioop` compatibility problem and providing the executable required by the music cog.

## Discord intents

Enable these privileged intents in the Discord Developer Portal:

- Presence Intent
- Server Members Intent
- Message Content Intent

## Music

The music cog uses `yt-dlp` and FFmpeg. Supported commands include:

- `!play <YouTube URL or search>`
- `!skip`
- `!pause`
- `!resume`
- `!stop`
- `!queue`
- `!nowplaying`
- `!volume 0-100`
- `!remove <number>`
- `!clearqueue`

Never commit bot tokens or other secrets.
