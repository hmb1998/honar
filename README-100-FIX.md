# HMB NEXUS — 100% Fix Pack

This build keeps the no-cookie Music design and hardens the project for Railway.

## Main fixes
- Updated yt-dlp to 2026.08.19.
- Keeps BgUtils PO-token provider on localhost:4416.
- Docker now waits for the PO-token provider health endpoint instead of blindly sleeping 2 seconds.
- Fixed moderation role hierarchy comparisons in `cogs/moderation.py`.
- Fixed Economy `/work` showing a different XP amount than the amount actually awarded.
- Added `startup_check.py` for deployment diagnostics.

## Music
Cookies are NOT required by default. The bot uses yt-dlp + Deno/EJS + BgUtils PO-token provider.
YouTube can still reject particular videos/IPs; no implementation can guarantee playback for every YouTube request.

## Railway
Set:
- `DISCORD_TOKEN`

Do not put YouTube cookies in the public repository.

After deployment, check Railway logs for:
`BgUtils PO-token provider is ready`


## Music Panel patch
- Music Panel Search now uses the same yt-dlp download path as playback.
- This avoids failing on metadata-only YouTube extraction when YouTube returns
  "Sign in to confirm you're not a bot" but the actual media download succeeds.
- Already-downloaded panel tracks are reused by the player, so the same track
  is not downloaded twice.
