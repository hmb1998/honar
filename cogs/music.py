import asyncio
import logging
import re
from typing import Optional

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

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
}

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
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)

        if not info:
            return None

        if "entries" in info:
            entries = [entry for entry in info["entries"] if entry]
            if not entries:
                return None
            info = entries[0]

        return {
            "url": info.get("webpage_url") or info.get("original_url") or query,
            "stream_url": info.get("url"),
            "title": info.get("title", "نەناسراو"),
            "duration": int(info.get("duration") or 0),
            "thumbnail": info.get("thumbnail"),
        }

    async def _resolve(self, query: str) -> Optional[dict]:
        return await asyncio.to_thread(self._extract, query)

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
            await ctx.send(f"❌ هەڵە لە ژەنین: `{exc}`")

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

    @commands.command(name="play", aliases=("p", "ژەنین"))
    async def play(self, ctx: commands.Context, *, query: str):
        """ژەنینی گۆرانی لە YouTube بە لینک یان ناو."""
        if not ctx.guild:
            return await ctx.send("❌ ئەم فەرمانە تەنها لە سێرڤەر کار دەکات.")

        if not ctx.author.voice:
            return await ctx.send("🔇 سەرەتا بچۆ ناو Voice Channel!")

        voice = ctx.voice_client
        target_channel = ctx.author.voice.channel

        if voice and voice.channel != target_channel:
            if voice.is_playing():
                return await ctx.send("❌ بۆت لە Voice Channel ـێکی ترە.")
            await voice.move_to(target_channel)
        elif not voice:
            voice = await target_channel.connect()

        song = await self._resolve(query if YOUTUBE_URL.match(query) else f"ytsearch:{query}")

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

    @commands.command(name="skip", aliases=("s", "next", "پەڕاندن"))
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ **گۆرانی پەڕێندرایەوە.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

    @commands.command(name="stop", aliases=("leave", "dc", "وەستان"))
    async def stop(self, ctx: commands.Context):
        guild_id = ctx.guild.id
        self.queues[guild_id] = []
        self.now_playing[guild_id] = None

        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 **بۆت لە Voice دەرچوو.**")
        else:
            await ctx.send("❌ بۆت لە Voice نییە.")

    @commands.command(name="queue", aliases=("q", "list", "ڕیز"))
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

    @commands.command(name="pause", aliases=("pa", "ڕاگرتن"))
    async def pause(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ **ڕاگیرا.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ناژەنرێت.")

    @commands.command(name="resume", aliases=("res", "unpause", "بەردەوام"))
    async def resume(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ **بەردەوام بووەوە.**")
        else:
            await ctx.send("❌ هیچ گۆرانییەک ڕانەگیراوە.")

    @commands.command(name="volume", aliases=("vol", "v", "دەنگ"))
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

    @commands.command(name="nowplaying", aliases=("np", "current", "ئێستا"))
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

    @commands.command(name="remove", aliases=("rm", "del", "لابردن"))
    async def remove(self, ctx: commands.Context, index: int):
        queue = self.get_queue(ctx.guild.id)

        if 1 <= index <= len(queue):
            removed = queue.pop(index - 1)
            await ctx.send(f"🗑 **لابردرا:** {removed.get('title', 'گۆرانی')}")
        else:
            await ctx.send(
                f"❌ ژمارە نادروستە. ڕیز `{len(queue)}` گۆرانی هەیە."
            )

    @commands.command(name="clearqueue", aliases=("cq", "clearq", "بەتاڵ"))
    async def clearqueue(self, ctx: commands.Context):
        self.queues[ctx.guild.id] = []
        await ctx.send("🗑 **ڕیز بەتاڵکرایەوە.**")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
