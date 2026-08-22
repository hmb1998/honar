# Honar Discord Bot

## Environment Variables
- `DISCORD_TOKEN` — required
- `HONAR_GITHUB_TOKEN` — optional; recommended GitHub token name
- `GITHUB_TOKEN` — optional legacy fallback
- `BOT_PREFIX` — optional; defaults to `!`

## Discord Intents
The bot uses `Intents.all()`. Enable the required privileged intents in the Discord Developer Portal:
- Presence Intent
- Server Members Intent
- Message Content Intent

## Music
The music cog requires the **FFmpeg executable** to be installed on the hosting machine and available on `PATH`.

## Run
```bash
pip install -r requirements.txt
python main.py
```

Do not commit tokens or generated economy data.
