# HMB NEXUS Music 403 Fix

## What changed

- `cogs/music.py`: YouTube audio is downloaded by **yt-dlp** first and then FFmpeg reads the local audio file.
- This avoids the old path where a signed `googlevideo` URL was handed directly to FFmpeg and returned `HTTP 403`.
- `mweb` is tried first with the BgUtils PO-token provider, followed by `web_embedded`, `tv`, and `android_vr`.
- Deno + `yt-dlp-ejs` are enabled for current YouTube JS challenges.
- Optional `YOUTUBE_COOKIE_FILE` remains available, but the bot does not require a cookie file by default.
- The Dockerfile no longer imports `bgutil_ytdlp_pot_provider` as a normal Python module. The plugin is auto-discovered by yt-dlp.

## Railway

Redeploy after replacing the files. The container starts the BgUtils provider on `127.0.0.1:4416` before starting the bot.

Optional Railway variable:

`YOUTUBE_COOKIE_FILE=/app/cookies.txt`

Only set this if you intentionally mount/provide a valid cookies file. Do not commit cookies to GitHub.

## Important

YouTube can still reject traffic by IP, account, or video. PO tokens improve compatibility but are not a guarantee against every 403.
