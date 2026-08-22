import asyncio
import logging
import os
import json
import re
from typing import Optional
from urllib.parse import quote, urlparse, parse_qs
from urllib.request import Request, urlopen

import discord
import yt_dlp
from discord.ext import commands

logger = logging.getLogger("honar.music")

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    ),
    "options": "-vn",
}

# YouTube anonymous playback configuration.
# IMPORTANT: this bot intentionally does NOT require YOUTUBE_COOKIE.
# We try several public clients because YouTube changes which clients can
# stream without an authenticated browser session.
YOUTUBE_CLIENTS = [
    # web_safari can expose HLS audio that currently avoids some GVS PO-token
    # requirements. web_embedded/tv are useful anonymous fallbacks.
    "web_safari",
    "web_embedded",
    "tv",
    "android_vr",
    "web_music",
    "mweb",
    "web",
]

BASE_YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "retries": 2,
    "fragment_retries": 2,
    "socket_timeout": 20,
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    },
    # yt-dlp 2026 requires its EJS challenge solver for full YouTube support.
    # The matching yt-dlp-ejs package is installed in the Docker image.
    "js_runtimes": {"deno": {}},
}

INVIDIOUS_INSTANCES = [
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://yt.chocolatemoo53.com",
    "https://invidious.tiekoetter.com",
    "https://invidious.f5.si",
]

YOUTUBE_URL = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/",
    re.IGNORECASE,
)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, list[dict]] = {}
        self.now_playing: dict[int, Optional[dict]] = {}

    def get_queue(self, guild_id: int) -> list[dict]:
        return self.queues.setdefault(guild_id, [])

    @staticmethod
    def _extract(query: str) -> Optional[dict]:
        last_error = None

        # Try anonymous/public clients one by one. No cookie is required.
        for client in YOUTUBE_CLIENTS:
            options = {
                **BASE_YDL_OPTIONS,
                "extractor_args": {
                    "youtube": {
                        "player_client": [client],
                        # Allow formats that are sometimes hidden when YouTube
                        # marks a client as missing a PO token.
                        "formats": ["missing_pot"],
                    },
                    # BgUtils provider is installed in the Docker image. If it
                    # is unavailable, yt-dlp simply continues with its normal
                    # anonymous clients.
                    "youtubepot-bgutilhttp": {
                        "base_url": os.getenv(
                            "YOUTUBE_POT_PROVIDER_URL",
                            "http://127.0.0.1:4416",
                        ),
                    },
                },
            }
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(query, download=False)

                if not info:
                    continue

                if "entries" in info:
                    entries = [entry for entry in info["entries"] if entry]
                    if not entries:
                        continue
                    info = entries[0]

                stream_url = info.get("url")
                if not stream_url:
                    continue

                return {
                    "url": info.get("webpage_url") or info.get("original_url") or query,
                    "stream_url": stream_url,
                    "title": info.get("title", "نەناسراو"),
                    "duration": int(info.get("duration") or 0),
                    "thumbnail": info.get("thumbnail"),
                }
            except Exception as exc:
                last_error = exc
                logger.warning("Anonymous YouTube client %s failed: %s", client, str(exc)[:250])

        if last_error:
            raise last_error
        return None

    @staticmethod
    def _youtube_video_id(value: str) -> Optional[str]:
        try:
            parsed = urlparse(value)
            host = parsed.netloc.lower().split(":")[0]
            if host == "youtu.be":
                return parsed.path.strip("/").split("/")[0] or None
            if "youtube.com" in host:
                return parse_qs(parsed.query).get("v", [None])[0]
        except Exception:
            return None
        return None

    @staticmethod
    def _invidious_request(url: str) -> object:
        req = Request(
            url,
            headers={
                "User-Agent": "HMB-NEXUS/2.0",
                "Accept": "application/json",
            },
        )
        with urlopen(req, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))

    @classmethod
    def _extract_invidious(cls, query: str) -> Optional[dict]:
        video_id = cls._youtube_video_id(query)

        for instance in INVIDIOUS_INSTANCES:
            try:
                if video_id:
                    data = cls._invidious_request(
                        f"{instance}/api/v1/videos/{video_id}?hl=en"
                    )
                else:
                    search_query = query[8:] if query.lower().startswith("ytsearch:") else query
                    results = cls._invidious_request(
                        f"{instance}/api/v1/search?q={quote(search_query)}&type=video&hl=en"
                    )
                    if not isinstance(results, list) or not results:
                        continue
                    first = next(
                        (item for item in results if item.get("type") == "video"),
                        None,
                    )
                    if not first:
                        continue
                    video_id = first.get("videoId")
                    if not video_id:
                        continue
                    data = cls._invidious_request(
                        f"{instance}/api/v1/videos/{video_id}?hl=en"
                    )

                if not isinstance(data, dict):
                    continue

                formats = data.get("adaptiveFormats") or []
                audio = [
                    fmt for fmt in formats
                    if fmt.get("url")
                    and str(fmt.get("type", "")).startswith("audio/")
                ]
                audio.sort(
                    key=lambda fmt: (
                        int(fmt.get("bitrate") or 0),
                        int(fmt.get("clen") or 0),
                    ),
                    reverse=True,
                )
                if not audio:
                    continue

                fmt = audio[0]
                thumb = None
                thumbs = data.get("videoThumbnails") or []
                if thumbs:
                    thumb = thumbs[-1].get("url")

                return {
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "stream_url": fmt["url"],
                    "title": data.get("title", "نەناسراو"),
                    "duration": int(data.get("lengthSeconds") or 0),
                    "thumbnail": thumb,
                }
            except Exception as exc:
                logger.warning("Invidious fallback %s failed: %s", instance, str(exc)[:180])

        return None

    @classmethod
    def _extract_any(cls, query: str) -> Optional[dict]:
        try:
            return cls._extract(query)
        except Exception as primary_error:
            logger.warning(
                "yt-dlp failed; trying Invidious fallback: %s",
                str(primary_error)[:300],
            )
            fallback = cls._extract_invidious(query)
            if fallback:
                return fallback
            raise primary_error

    async def _resolve(self, query: str) -> Optional[dict]:
        return await asyncio.to_thread(self._extract_any, query)

    async def _send_play_error(self, ctx: commands.Context, exc: Exception):
        text = str(exc)
        lowered = text.lower()

        if any(x in lowered for x in (
            "sign in to confirm", "confirm you're not a bot",
            "login required", "po token", "http error 403",
        )):
            await ctx.send(
                "❌ YouTube لەم کاتەدا دەستپێگەیشتنی anonymous ـی ئەم لینکە ڕەتکردەوە.\n"
                "🔄 لینکێکی تری YouTube یان ناوی گۆرانییەکی تر تاقی بکەرەوە. "
                "ئەم سیستەمە بەبێ Cookie چەند client ـێک خۆکارانە تاقی دەکاتەوە."
            )
            return

        await ctx.send(f"❌ هەڵە لە ژەنین: `{text[:500]}`")

    async def _play_song(self, ctx: commands.Context, song: dict):
        voice = ctx.voice_client
        if not voice or not voice.is_connected():
            return

        try:
            info = await self._resolve(song["url"])
            if not info or not info.get("stream_url"):
                await ctx.send("❌ نەتوانرا گۆرانییەکە بخوێندرێتەوە.")
                return

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    info["stream_url"],
                    **FFMPEG_OPTIONS,
                ),
                volume=1.0,
            )

            guild_id = ctx.guild.id
            self.now_playing[guild_id] = {
                **info,
                "requester": song.get("requester"),
                "volume": 100,
            }

            def after(error):
                if error:
                    logger.error("Player error: %s", error)
                future = asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx),
                    self.bot.loop,
                )
                try:
                    future.result()
                except Exception:
                    logger.exception("Failed to continue queue.")

            voice.play(source, after=after)

            duration = info["duration"]
            mins, secs = divmod(duration, 60)
            await ctx.send(
                f"🎵 **ئێستا دەژەنێت:** {info['title']}\n"
                f"⏱ `{mins}:{secs:02d}`\n"
                f"🔗 {info['url']}"
            )

        except Exception as exc:
            logger.exception("Music playback failed")
            await self._send_play_error(ctx, exc)

    async def play_next(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        voice = ctx.voice_client

        if not voice or not voice.is_connected():
            return

        if queue:
            song = queue.pop(0)
            await self._play_song(ctx, song)
        else:
            self.now_playing[guild_id] = None
            try:
                await voice.disconnect()
            except discord.HTTPException:
                pass

    @commands.hybrid_command(name="play", aliases=("p", "ژەنین"))
    async def play(self, ctx: commands.Context, *, query: str):
        """ژەنینی گۆرانی لە YouTube بە لینک یان ناو."""
        if not ctx.guild:
            return await ctx.send("❌ ئەم فەرمانە تەنها لە سێرڤەر کار دەکات.")

        if not ctx.author.voice:
            return await ctx.send("🔇 سەرەتا بچۆ ناو Voice Channel!")

        # Slash commands expire while yt-dlp is contacting YouTube.
        # Defer immediately so a slow extraction cannot cause:
        # 404 Not Found (error code: 10062): Unknown interaction
        if ctx.interaction is not None and not ctx.interaction.response.is_done():
            await ctx.defer()

        voice = ctx.voice_client
        target_channel = ctx.author.voice.channel

        if voice and voice.channel != target_channel:
            if voice.is_playing():
                return await ctx.send("❌ بۆت لە Voice Channel ـێکی ترە.")
            await voice.move_to(target_channel)
        elif not voice:
            voice = await target_channel.connect()

        try:
            target = query.strip()
            source_query = target if YOUTUBE_URL.match(target) else f"ytsearch:{target}"
            song = await self._resolve(source_query)
        except Exception as exc:
            logger.exception("YouTube resolve failed for %r", query)
            await self._send_play_error(ctx, exc)
            return

        if not song:
            return await ctx.send("❌ هیچ گۆرانییەک نەدۆزرایەوە.")

        song["requester"] = ctx.author
        queue = self.get_queue(ctx.guild.id)

        if voice.is_playing() or voice.is_paused():
            queue.append(song)
            await ctx.send(
                f"📥 **زیادکرا بۆ ڕیز:** {song['title']}\n"
                f"📋 شوێن: `{len(queue)}`"
            )
        else:
            await self._play_song(ctx, song)

    @commands.hybrid_command(name="skip", aliases=("s", "next", "پەڕاندن"))
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ **گۆرانی پەڕێندرایەوە.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

    @commands.hybrid_command(name="stop", aliases=("leave", "dc", "وەستان"))
    async def stop(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        self.queues[guild_id] = []
        self.now_playing[guild_id] = None

        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 **بۆت لە Voice دەرچوو.**")
        else:
            await ctx.send("❌ بۆت لە Voice نییە.")

    @commands.hybrid_command(name="queue", aliases=("q", "list", "ڕیز"))
    async def queue(self, ctx: commands.Context):
        queue = self.get_queue(ctx.guild.id)
        current = self.now_playing.get(ctx.guild.id)

        if not queue and not current:
            return await ctx.send("📭 **ڕیز بەتاڵە.**")

        lines = ["📋 **ڕیزی گۆرانیەکان:**"]

        if current:
            lines.append(f"🎵 **ئێستا:** {current['title']}")

        for index, song in enumerate(queue[:10], start=1):
            lines.append(f"{index}. {song.get('title', song['url'])}")

        if len(queue) > 10:
            lines.append(f"... و {len(queue) - 10} گۆرانیی تر")

        lines.append(f"\n**کۆی ڕیز:** {len(queue)}")
        await ctx.send("\n".join(lines)[:2000])

    @commands.hybrid_command(name="pause", aliases=("pa", "ڕاگرتن"))
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ **ڕاگیرا.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

    @commands.hybrid_command(name="resume", aliases=("res", "unpause", "بەردەوام"))
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ **بەردەوام بووەوە.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ڕانەگیراوە.")

    @commands.hybrid_command(name="volume", aliases=("vol", "v", "دەنگ"))
    async def volume(self, ctx: commands.Context, vol: int):
        if not 0 <= vol <= 100:
            return await ctx.send("❌ دەنگ دەبێت لە نێوان `0-100` بێت.")

        if (
            ctx.voice_client
            and ctx.voice_client.source
            and isinstance(ctx.voice_client.source, discord.PCMVolumeTransformer)
        ):
            ctx.voice_client.source.volume = vol / 100
            if ctx.guild.id in self.now_playing:
                self.now_playing[ctx.guild.id]["volume"] = vol
            await ctx.send(f"🔊 **دەنگ:** `{vol}%`")
        else:
            await ctx.send("❌ سەرچاوەی دەنگ بەردەست نییە.")

    @commands.hybrid_command(name="nowplaying", aliases=("np", "current", "ئێستا"))
    async def nowplaying(self, ctx: commands.Context):
        current = self.now_playing.get(ctx.guild.id)

        if not current:
            return await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

        mins, secs = divmod(current["duration"], 60)
        embed = discord.Embed(
            title="🎵 ئێستا دەژەنێت",
            description=(
                f"**{current['title']}**\n"
                f"⏱ `{mins}:{secs:02d}`\n"
                f"🔊 `{current.get('volume', 100)}%`"
            ),
            color=0x5865F2,
            url=current["url"],
        )
        if current.get("thumbnail"):
            embed.set_thumbnail(url=current["thumbnail"])

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="remove", aliases=("rm", "del", "لابردن"))
    async def remove(self, ctx: commands.Context, index: int):
        queue = self.get_queue(ctx.guild.id)

        if 1 <= index <= len(queue):
            removed = queue.pop(index - 1)
            await ctx.send(f"🗑 **لابردرا:** {removed.get('title', 'گۆرانی')}")
        else:
            await ctx.send(
                f"❌ ژمارە نادروستە. ڕیز `{len(queue)}` گۆرانی هەیە."
            )

    @commands.hybrid_command(name="clearqueue", aliases=("cq", "clearq", "بەتاڵ"))
    async def clearqueue(self, ctx: commands.Context):
        self.queues[ctx.guild.id] = []
        await ctx.send("🗑 **ڕیز بەتاڵکرایەوە.**")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
