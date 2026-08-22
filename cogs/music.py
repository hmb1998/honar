import discord
from discord.ext import commands
import yt_dlp
import asyncio
import re

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': True, 'quiet': True}


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.now_playing = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not ctx.voice_client or not ctx.voice_client.is_connected():
            return
        if queue:
            song = queue.pop(0)
            await self._play_song(ctx, song)
        else:
            self.now_playing[ctx.guild.id] = None
            await ctx.voice_client.disconnect()

    async def _play_song(self, ctx, song):
        try:
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(song["url"], download=False)
                url = info.get("url")
                title = info.get("title", "نەناسراو")
                duration = info.get("duration", 0)
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            self.now_playing[ctx.guild.id] = {
                "title": title,
                "url": song["url"],
                "duration": duration
            }
            ctx.voice_client.play(
                source,
                after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx), self.bot.loop
                )
            )
            mins = duration // 60
            secs = duration % 60
            await ctx.send(
                f"🎵 **ئێستا دەژەنێت:** {title}\n"
                f"⏱ {mins}:{secs:02d}\n"
                f"🔗 {song['url']}"
            )
        except Exception as e:
            await ctx.send(f"❌ هەڵە لە ژەنین: {e}")

    @commands.command(name="play", aliases=["p", "ژەنین"])
    async def play(self, ctx, *, query: str):
        """ژەنینی گۆرانی لە یوتیوب - بە لینک یان ناو"""
        if not ctx.author.voice:
            return await ctx.send("🔇 سەرەتا بچە ناو ڤۆیس چانێل!")
        voice = ctx.voice_client
        if not voice:
            voice = await ctx.author.voice.channel.connect()
        url_pattern = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/')
        if not url_pattern.match(query):
            with yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': True, 'quiet': True}) as ydl:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)
                if info and info.get("entries"):
                    query = f"https://youtube.com/watch?v={info['entries'][0]['id']}"
                else:
                    return await ctx.send("❌ هیچ گۆرانیەک نەدۆزرایەوە")
        song = {"url": query, "requester": ctx.author}
        queue = self.get_queue(ctx.guild.id)
        if voice.is_playing():
            queue.append(song)
            await ctx.send(f"📥 **زیادکرا بۆ ڕیز:** {query}")
        else:
            await self._play_song(ctx, song)

    @commands.command(name="skip", aliases=["s", "next", "پەڕاندن"])
    async def skip(self, ctx):
        """پەڕاندنی گۆرانی بۆ گۆرانی داهاتوو"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭ **پەڕێندرا**")
        else:
            await ctx.send("❌ هیچ گۆرانیەک ناژەنرێت")

    @commands.command(name="stop", aliases=["leave", "dc", "وەستان"])
    async def stop(self, ctx):
        """ڕاگرتنی گۆرانی و جێهێشتنی ڤۆیس چانێل"""
        self.queues[ctx.guild.id] = []
        self.now_playing[ctx.guild.id] = None
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 **جێهێشترا**")

    @commands.command(name="queue", aliases=["q", "list", "ڕیز"])
    async def queue(self, ctx):
        """پیشاندانی ڕیزی گۆرانیەکان"""
        queue = self.get_queue(ctx.guild.id)
        np = self.now_playing.get(ctx.guild.id)
        if not queue and not np:
            return await ctx.send("📭 **ڕیز بەتاڵە**")
        msg = "**📋 ڕیزی گۆرانیەکان:**\n"
        if np:
            msg += f"🎵 **ئێستا:** {np['title']}\n"
        for i, s in enumerate(queue[:10], 1):
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                try:
                    info = ydl.extract_info(s['url'], download=False)
                    title = info.get('title', s['url'])
                except:
                    title = s['url']
            msg += f"{i}. {title}\n"
        msg += f"\n**کۆی گشتی:** {len(queue)} گۆرانی"
        await ctx.send(msg[:2000])

    @commands.command(name="pause", aliases=["pa", "ڕاگرتن"])
    async def pause(self, ctx):
        """ڕاگرتنی کاتی گۆرانی"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸ **ڕاگیرا**")
        else:
            await ctx.send("❌ هیچ گۆرانیەک ناژەنرێت")

    @commands.command(name="resume", aliases=["res", "unpause", "بەردەوام"])
    async def resume(self, ctx):
        """بەردەوامبوون لە گۆرانی"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ **بەردەوامبووەوە**")
        else:
            await ctx.send("❌ هیچ گۆرانیەک ڕانەگیراوە")

    @commands.command(name="volume", aliases=["vol", "v", "دەنگ"])
    async def volume(self, ctx, vol: int):
        """دانانی ئاستی دەنگ (0-100)"""
        if vol < 0 or vol > 100:
            return await ctx.send("❌ دەنگ دەبێت لە نێوان 0-100 بێت")
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = vol / 100
            await ctx.send(f"🔊 **دەنگ کرایە:** {vol}%")
        else:
            await ctx.send("❌ ناتوانرێت دەنگ بگۆڕدرێت")

    @commands.command(name="nowplaying", aliases=["np", "current", "ئێستا"])
    async def nowplaying(self, ctx):
        """پیشاندانی گۆرانی کە ئێستا دەژەنرێت"""
        np = self.now_playing.get(ctx.guild.id)
        if np:
            mins = np['duration'] // 60 if np['duration'] else 0
            secs = np['duration'] % 60 if np['duration'] else 0
            embed = discord.Embed(
                title="🎵 ئێستا دەژەنێت",
                description=f"**{np['title']}**\n⏱ {mins}:{secs:02d}",
                color=0x1DB954,
                url=np['url']
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ هیچ گۆرانیەک ناژەنرێت")

    @commands.command(name="remove", aliases=["rm", "del", "لابردن"])
    async def remove(self, ctx, index: int):
        """لابردنی گۆرانی لە ڕیز بە ژمارە"""
        queue = self.get_queue(ctx.guild.id)
        if 1 <= index <= len(queue):
            queue.pop(index - 1)
            await ctx.send(f"🗑 **لابردرا:** گۆرانی ژمارە {index}")
        else:
            await ctx.send(f"❌ ژمارە نادروستە. ڕیز تەنها {len(queue)} گۆرانی هەیە")

    @commands.command(name="clearqueue", aliases=["cq", "clearq", "بەتاڵ"])
    async def clearqueue(self, ctx):
        """بەتاڵکردنەوەی تەواوی ڕیز"""
        self.queues[ctx.guild.id] = []
        await ctx.send("🗑 **ڕیز بەتاڵکرایەوە**")


async def setup(bot):
    await bot.add_cog(Music(bot))
