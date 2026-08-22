import asyncio
import logging
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import discord
import yt_dlp
from discord.ext import commands

logger = logging.getLogger("honar.music")

YOUTUBE_URL = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/",
    re.IGNORECASE,
)

POT_PROVIDER_URL = (
    os.getenv("YOUTUBE_POT_PROVIDER_URL", "http://127.0.0.1:4416").strip()
    or "http://127.0.0.1:4416"
)

# YouTube has been changing which clients require PO tokens.  mweb is the
# recommended client for GVS + PO tokens; web_embedded/tv are useful fallbacks.
YOUTUBE_CLIENTS = ("mweb", "web_embedded", "tv", "android_vr")

MUSIC_TMP_ROOT = Path(
    os.getenv("MUSIC_TMP_DIR", "/tmp/hmb-nexus-music")
)
MUSIC_TMP_ROOT.mkdir(parents=True, exist_ok=True)

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def _base_ydl_options(client: str, *, download: bool = False, outtmpl: str = "") -> dict:
    options = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "retries": 3,
        "fragment_retries": 3,
        "extractor_retries": 3,
        "file_access_retries": 3,
        "socket_timeout": 30,
        "force_ipv4": True,
        "http_headers": {
            "User-Agent": UA,
            "Accept-Language": "en-US,en;q=0.9",
        },
        # Modern yt-dlp uses Deno + yt-dlp-ejs for YouTube JS challenges.
        "js_runtimes": {"deno": {}},
        "remote_components": {"ejs": ["github"]},
        "extractor_args": {
            "youtube": {
                "player_client": [client],
            },
            "youtubepot-bgutilhttp": {
                "base_url": POT_PROVIDER_URL,
            },
        },
    }

    # Optional browser cookies. The bot works without them when YouTube allows
    # anonymous playback, but an operator can provide a valid cookies file if
    # YouTube requires authentication for a particular video/IP.
    cookie_file = os.getenv("YOUTUBE_COOKIE_FILE", "").strip()
    if cookie_file and Path(cookie_file).is_file():
        options["cookiefile"] = cookie_file

    if download:
        options.update(
            {
                "outtmpl": outtmpl,
                "overwrites": True,
                "continuedl": False,
                "nopart": True,
                # Keep the file in the source container; ffmpeg only reads it.
                "postprocessors": [],
            }
        )

    return options


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, list[dict]] = {}
        self.now_playing: dict[int, Optional[dict]] = {}
        self._download_lock: dict[int, asyncio.Lock] = {}

    def get_queue(self, guild_id: int) -> list[dict]:
        return self.queues.setdefault(guild_id, [])

    def _guild_lock(self, guild_id: int) -> asyncio.Lock:
        return self._download_lock.setdefault(guild_id, asyncio.Lock())

    @staticmethod
    def _youtube_video_id(value: str) -> Optional[str]:
        try:
            parsed = urlparse(value)
            host = parsed.netloc.lower().split(":")[0]
            if host == "youtu.be":
                return parsed.path.strip("/").split("/")[0] or None
            if "youtube.com" in host:
                value_id = parse_qs(parsed.query).get("v", [None])[0]
                if value_id:
                    return value_id
                parts = [p for p in parsed.path.split("/") if p]
                if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
                    return parts[1]
        except Exception:
            pass
        return None

    @staticmethod
    def _pick_entry(info: dict) -> Optional[dict]:
        if not info:
            return None
        if info.get("entries") is not None:
            for entry in info.get("entries") or []:
                if entry:
                    return entry
            return None
        return info

    @classmethod
    def _extract_info(cls, query: str) -> Optional[dict]:
        last_error: Optional[Exception] = None

        for client in YOUTUBE_CLIENTS:
            try:
                opts = _base_ydl_options(client)
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(query, download=False)
                info = cls._pick_entry(info)
                if not info:
                    continue

                # A resolved stream URL is still returned for compatibility
                # with the existing panel/queue. Playback itself does NOT feed
                # this URL to ffmpeg; it downloads through yt-dlp first.
                return {
                    "url": info.get("webpage_url") or info.get("original_url") or query,
                    "title": info.get("title") or "نەناسراو",
                    "duration": int(info.get("duration") or 0),
                    "thumbnail": info.get("thumbnail"),
                    "video_id": info.get("id") or cls._youtube_video_id(query),
                }
            except Exception as exc:
                last_error = exc
                logger.warning("yt-dlp extract client=%s failed: %s", client, str(exc)[:300])

        if last_error:
            raise last_error
        return None

    @classmethod
    def _download_audio(cls, query: str) -> dict:
        """Download the audio with yt-dlp, then let FFmpeg read a local file.

        This is intentional: passing a signed googlevideo URL directly to
        FFmpeg can produce HTTP 403 even when yt-dlp itself can download it.
        yt-dlp keeps the YouTube headers/PO-token/session handling on the
        request that actually transfers the media.
        """
        last_error: Optional[Exception] = None
        workdir: Optional[Path] = None

        for client in YOUTUBE_CLIENTS:
            try:
                workdir = Path(tempfile.mkdtemp(prefix="track-", dir=MUSIC_TMP_ROOT))
                outtmpl = str(workdir / "audio.%(ext)s")
                opts = _base_ydl_options(client, download=True, outtmpl=outtmpl)
                opts["paths"] = {"home": str(workdir)}

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(query, download=True)
                    info = cls._pick_entry(info)

                if not info:
                    raise RuntimeError("yt-dlp هیچ گۆرانییەکی نەگەڕاندەوە")

                candidates = sorted(
                    p for p in workdir.iterdir()
                    if p.is_file() and p.name != ".ytdl"
                )
                if not candidates:
                    raise RuntimeError("فایلی دەنگ دروست نەکرا")

                audio_file = candidates[0]
                return {
                    "url": info.get("webpage_url") or info.get("original_url") or query,
                    "title": info.get("title") or "نەناسراو",
                    "duration": int(info.get("duration") or 0),
                    "thumbnail": info.get("thumbnail"),
                    "video_id": info.get("id") or cls._youtube_video_id(query),
                    "audio_file": str(audio_file),
                    "temp_dir": str(workdir),
                }

            except Exception as exc:
                last_error = exc
                logger.warning("yt-dlp download client=%s failed: %s", client, str(exc)[:350])
                if workdir:
                    shutil.rmtree(workdir, ignore_errors=True)
                workdir = None

        if last_error:
            raise last_error
        return None

    @classmethod
    def _extract_any(cls, query: str) -> Optional[dict]:
        return cls._extract_info(query)

    async def _resolve(self, query: str) -> Optional[dict]:
        return await asyncio.to_thread(self._extract_any, query)

    async def _send_play_error(self, ctx, exc: Exception):
        text = str(exc)
        lowered = text.lower()
        if any(
            marker in lowered
            for marker in (
                "sign in to confirm",
                "confirm you're not a bot",
                "login required",
                "po token",
                "http error 403",
                "forbidden",
            )
        ):
            message = (
                "❌ **YouTube playback ڕەتکرایەوە.**\n"
                "🔐 PO Token provider هەوڵی دا، بەڵام YouTube ئەم request ـەی ڕەتکردەوە.\n"
                "💡 زۆرجار هۆکارەکە IP/YouTube restriction ـە؛ Cookie تەنها کاتێک پێویستە "
                "کە ڤیدیۆکە login بخوازێت."
            )
        else:
            message = f"❌ هەڵە لە ژەنین: `{text[:700]}`"
        await ctx.send(message)

    async def _play_song(self, ctx, song: dict):
        voice = ctx.voice_client
        if not voice or not voice.is_connected():
            return

        guild_id = ctx.guild.id
        temp_dir: Optional[str] = None

        try:
            async with self._guild_lock(guild_id):
                # Re-resolve/download immediately before playback so temporary
                # YouTube URLs are never reused from an earlier request.
                info = await asyncio.to_thread(self._download_audio, song["url"])

            if not info or not info.get("audio_file"):
                raise RuntimeError("گۆرانییەکە download نەکرا")

            temp_dir = info.get("temp_dir")
            self.now_playing[guild_id] = {
                **info,
                "requester": song.get("requester"),
                "volume": 100,
            }

            source = discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    info["audio_file"],
                    before_options="-nostdin",
                    options="-vn",
                ),
                volume=1.0,
            )

            def after(error):
                if error:
                    logger.error("Player error: %s", error)
                future = asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                )
                try:
                    future.result()
                except Exception:
                    logger.exception("Failed to continue queue")
                finally:
                    if temp_dir:
                        shutil.rmtree(temp_dir, ignore_errors=True)

            voice.play(source, after=after)

            duration = int(info.get("duration") or 0)
            mins, secs = divmod(duration, 60)
            await ctx.send(
                f"🎵 **ئێستا دەژەنێت:** {info['title']}\n"
                f"⏱ `{mins}:{secs:02d}`\n"
                f"🔗 {info['url']}"
            )

        except Exception as exc:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            logger.exception("Music playback failed")
            await self._send_play_error(ctx, exc)

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        voice = ctx.voice_client
        if not voice or not voice.is_connected():
            return
        if queue:
            await self._play_song(ctx, queue.pop(0))
        else:
            self.now_playing[guild_id] = None
            try:
                await voice.disconnect()
            except discord.HTTPException:
                pass

    @commands.hybrid_command(name="play", aliases=("p", "ژەنین"))
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.guild:
            return await ctx.send("❌ ئەم فەرمانە تەنها لە سێرڤەر کار دەکات.")
        if not ctx.author.voice:
            return await ctx.send("🔇 سەرەتا بچۆ ناو Voice Channel!")

        if ctx.interaction is not None and not ctx.interaction.response.is_done():
            await ctx.defer()

        voice = ctx.voice_client
        target = ctx.author.voice.channel
        if voice and voice.channel != target:
            if voice.is_playing():
                return await ctx.send("❌ بۆت لە Voice Channel ـێکی ترە.")
            await voice.move_to(target)
        elif not voice:
            voice = await target.connect()

        try:
            target_query = query.strip()
            source_query = target_query if YOUTUBE_URL.match(target_query) else f"ytsearch:{target_query}"
            song = await self._resolve(source_query)
        except Exception as exc:
            logger.exception("YouTube/source resolve failed for %r", query)
            await self._send_play_error(ctx, exc)
            return

        if not song:
            return await ctx.send("❌ هیچ گۆرانییەک نەدۆزرایەوە.")

        song["requester"] = ctx.author
        queue = self.get_queue(ctx.guild.id)
        if voice.is_playing() or voice.is_paused():
            queue.append(song)
            return await ctx.send(
                f"📥 **زیادکرا بۆ ڕیز:** {song['title']}\n📋 شوێن: `{len(queue)}`"
            )
        await self._play_song(ctx, song)

    @commands.hybrid_command(name="skip", aliases=("s", "next", "پەڕاندن"))
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ **گۆرانی پەڕێندرایەوە.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

    @commands.hybrid_command(name="stop", aliases=("leave", "dc", "وەستان"))
    async def stop(self, ctx):
        self.queues[ctx.guild.id] = []
        self.now_playing[ctx.guild.id] = None
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 **بۆت لە Voice دەرچوو.**")
        else:
            await ctx.send("❌ بۆت لە Voice نییە.")

    @commands.hybrid_command(name="queue", aliases=("q", "list", "ڕیز"))
    async def queue(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        current = self.now_playing.get(ctx.guild.id)
        if not queue and not current:
            return await ctx.send("📭 **ڕیز بەتاڵە.**")
        lines = ["📋 **ڕیزی گۆرانیەکان:**"]
        if current:
            lines.append(f"🎵 **ئێستا:** {current['title']}")
        for index, song in enumerate(queue[:10], 1):
            lines.append(f"{index}. {song.get('title', song.get('url', 'گۆرانی'))}")
        if len(queue) > 10:
            lines.append(f"... و {len(queue)-10} گۆرانیی تر")
        lines.append(f"\n**کۆی ڕیز:** {len(queue)}")
        await ctx.send("\n".join(lines)[:2000])

    @commands.hybrid_command(name="pause", aliases=("pa", "ڕاگرتن"))
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ **ڕاگیرا.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

    @commands.hybrid_command(name="resume", aliases=("res", "unpause", "بەردەوام"))
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ **بەردەوام بووەوە.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ڕانەگیراوە.")

    @commands.hybrid_command(name="volume", aliases=("vol", "v", "دەنگ"))
    async def volume(self, ctx, vol: int):
        if not 0 <= vol <= 100:
            return await ctx.send("❌ دەنگ دەبێت لە نێوان `0-100` بێت.")
        source = ctx.voice_client.source if ctx.voice_client else None
        if isinstance(source, discord.PCMVolumeTransformer):
            source.volume = vol / 100
            current = self.now_playing.get(ctx.guild.id)
            if current:
                current["volume"] = vol
            await ctx.send(f"🔊 **دەنگ:** `{vol}%`")
        else:
            await ctx.send("❌ سەرچاوەی دەنگ بەردەست نییە.")

    @commands.hybrid_command(name="nowplaying", aliases=("np", "current", "ئێستا"))
    async def nowplaying(self, ctx):
        current = self.now_playing.get(ctx.guild.id)
        if not current:
            return await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")
        mins, secs = divmod(int(current.get("duration") or 0), 60)
        embed = discord.Embed(
            title="🎵 ئێستا دەژەنێت",
            description=(
                f"**{current['title']}**\n"
                f"⏱ `{mins}:{secs:02d}`\n"
                f"🔊 `{current.get('volume', 100)}%`"
            ),
            color=0x5865F2,
            url=current.get("url"),
        )
        if current.get("thumbnail"):
            embed.set_thumbnail(url=current["thumbnail"])
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="remove", aliases=("rm", "del", "لابردن"))
    async def remove(self, ctx, index: int):
        queue = self.get_queue(ctx.guild.id)
        if 1 <= index <= len(queue):
            removed = queue.pop(index - 1)
            await ctx.send(f"🗑 **لابردرا:** {removed.get('title', 'گۆرانی')}")
        else:
            await ctx.send(f"❌ ژمارە نادروستە. ڕیز `{len(queue)}` گۆرانی هەیە.")

    @commands.hybrid_command(name="clearqueue", aliases=("cq", "clearq", "بەتاڵ"))
    async def clearqueue(self, ctx):
        self.queues[ctx.guild.id] = []
        await ctx.send("🗑 **ڕیز بەتاڵکرایەوە.**")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
