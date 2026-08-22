# HMB NEXUS — Railway Bot

## Music fix — NO COOKIE

This version is prepared for Railway and does **not** require a `YOUTUBE_COOKIE` variable.

### What was fixed

- `/play` now defers Discord interactions immediately, preventing `404 Unknown interaction (10062)` while YouTube is resolving.
- yt-dlp uses the current EJS JavaScript challenge support with Deno.
- BgUtils PO-token provider runs locally inside the same Railway container and can help with YouTube's `Sign in to confirm you're not a bot` check.
- Multiple YouTube player clients are tried automatically.
- If yt-dlp cannot resolve a track, the bot tries a current public Invidious API fallback.
- The Music Control Panel Search button uses the same resolver.
- Queue / Skip / Stop / Pause / Resume / Volume / Shuffle continue to use the existing music system.

### Railway

Use the included `Dockerfile` and redeploy the service.

Required Railway variable:

```text
DISCORD_TOKEN=your_bot_token
```

Optional variables already supported by the bot remain unchanged.

**Do not add `YOUTUBE_COOKIE`. It is not required by this version.**

### After deploy

1. Open Railway → Deployments.
2. Wait for the new Docker build to finish.
3. Open Deploy Logs and confirm the bot is online.
4. Run `/play` with a song name.
5. You can also open the HMB NEXUS music panel and press **Search**.

### Important

YouTube changes its anti-bot and playback requirements frequently. The code has multiple fallbacks, but no third-party YouTube extractor can guarantee permanent playback for every video and every Railway IP.
