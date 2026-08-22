import logging
import random
from typing import Optional

import discord
from discord.ext import commands

logger = logging.getLogger("honar.music_panel")


class MusicSearchModal(discord.ui.Modal, title="🎵 HMB NEXUS Music Search"):
    query = discord.ui.TextInput(
        label="YouTube link or song name",
        placeholder="Paste YouTube URL or type a song name...",
        required=True,
        max_length=200,
    )

    def __init__(self, panel: "MusicPanel"):
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        query = str(self.query).strip()
        await interaction.response.defer(ephemeral=True, thinking=True)

        music = self.panel.music
        if music is None:
            return await interaction.followup.send(
                "❌ Music cog بەردەست نییە.", ephemeral=True
            )

        try:
            from .music import YOUTUBE_URL
            source_query = query if YOUTUBE_URL.match(query) else f"ytsearch:{query}"
            song = await music._resolve(source_query)
        except Exception as exc:
            logger.exception("Music panel search failed: %r", query)
            message = str(exc).lower()
            if any(x in message for x in (
                "sign in to confirm", "confirm you're not a bot",
                "login required", "po token", "http error 403",
            )):
                return await interaction.followup.send(
                    "❌ YouTube لەم کاتەدا ئەم گۆرانییە بە anonymous access ڕەتکردەوە. "
                    "🔄 لینک یان ناوی گۆرانییەکی تر تاقی بکەرەوە؛ Cookie پێویست نییە.",
                    ephemeral=True,
                )
            return await interaction.followup.send(
                f"❌ هەڵە لە گەڕان: `{str(exc)[:500]}`", ephemeral=True
            )

        if not song:
            return await interaction.followup.send(
                "❌ هیچ گۆرانییەک نەدۆزرایەوە.", ephemeral=True
            )

        guild = interaction.guild
        if guild is None:
            return await interaction.followup.send(
                "❌ ئەم کارە تەنها لە سێرڤەر کار دەکات.", ephemeral=True
            )

        member = guild.get_member(interaction.user.id)
        if member is None or member.voice is None or member.voice.channel is None:
            return await interaction.followup.send(
                "🔇 سەرەتا بچۆ ناو Voice Channel.", ephemeral=True
            )

        song["requester"] = interaction.user
        voice = guild.voice_client
        target = member.voice.channel

        try:
            if voice and voice.channel != target:
                if voice.is_playing() or voice.is_paused():
                    return await interaction.followup.send(
                        "❌ بۆت لە Voice Channel ـێکی ترە.", ephemeral=True
                    )
                await voice.move_to(target)
            elif voice is None:
                voice = await target.connect()

            queue = music.get_queue(guild.id)
            if voice.is_playing() or voice.is_paused():
                queue.append(song)
                return await interaction.followup.send(
                    f"📥 **زیادکرا بۆ ڕیز:** {song['title']}\n📋 شوێن: `{len(queue)}`",
                    ephemeral=True,
                )

            # This is a component/modal interaction, not a slash-command
            # interaction. commands.Context.from_interaction() therefore
            # raises: "interaction does not have command data".
            # _play_song only needs a tiny context-like adapter.
            class PanelContext:
                guild = guild
                author = interaction.user

                @property
                def voice_client(self):
                    return guild.voice_client

                async def send(self, content=None, **kwargs):
                    kwargs.setdefault("ephemeral", True)
                    return await interaction.followup.send(
                        content=content, **kwargs
                    )

            await music._play_song(PanelContext(), song)
            # _play_song already reports the playback result.

        except Exception as exc:
            logger.exception("Music panel playback failed")
            await interaction.followup.send(
                f"❌ هەڵە: `{str(exc)[:500]}`", ephemeral=True
            )


class VolumeModal(discord.ui.Modal, title="🔊 HMB NEXUS Volume"):
    volume = discord.ui.TextInput(
        label="Volume (0-100)",
        placeholder="75",
        required=True,
        min_length=1,
        max_length=3,
    )

    def __init__(self, panel: "MusicPanel"):
        super().__init__()
        self.panel = panel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            value = int(str(self.volume).strip())
        except ValueError:
            return await interaction.response.send_message(
                "❌ تەنها ژمارە بنووسە: `0-100`", ephemeral=True
            )

        if not 0 <= value <= 100:
            return await interaction.response.send_message(
                "❌ Volume دەبێت `0-100` بێت.", ephemeral=True
            )

        guild = interaction.guild
        voice = guild.voice_client if guild else None
        if not voice or not isinstance(voice.source, discord.PCMVolumeTransformer):
            return await interaction.response.send_message(
                "❌ سەرچاوەی دەنگ بەردەست نییە.", ephemeral=True
            )

        voice.source.volume = value / 100
        current = self.panel.music.now_playing.get(guild.id)
        if current:
            current["volume"] = value

        await interaction.response.send_message(
            f"🔊 Volume: `{value}%`", ephemeral=True
        )


class MusicControlView(discord.ui.View):
    def __init__(self, panel: "MusicPanel", guild_id: int):
        super().__init__(timeout=1800)
        self.panel = panel
        self.guild_id = guild_id

    @property
    def music(self):
        return self.panel.music

    async def send(self, interaction: discord.Interaction, text: str):
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    @discord.ui.button(label="Search", emoji="🔎", style=discord.ButtonStyle.primary, row=0)
    async def search(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MusicSearchModal(self.panel))

    @discord.ui.button(label="Previous", emoji="⏮️", style=discord.ButtonStyle.secondary, row=1)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        music = self.music
        current = music.now_playing.get(self.guild_id)
        voice = interaction.guild.voice_client if interaction.guild else None
        if not current or not voice:
            return await self.send(interaction, "❌ گۆرانییەکی پێشوو بەردەست نییە.")

        # Put the current track at the front, then let the existing music cog advance.
        music.get_queue(self.guild_id).insert(
            0,
            {"url": current["url"], "requester": current.get("requester")},
        )
        voice.stop()
        await self.send(interaction, "⏮️ **Previous** کرا.")

    @discord.ui.button(label="Play / Pause", emoji="⏯️", style=discord.ButtonStyle.success, row=1)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client if interaction.guild else None
        if not voice:
            return await self.send(interaction, "❌ بۆت لە Voice نییە.")
        if voice.is_playing():
            voice.pause()
            return await self.send(interaction, "⏸️ **Pause** کرا.")
        if voice.is_paused():
            voice.resume()
            return await self.send(interaction, "▶️ **Resume** کرا.")
        await self.send(interaction, "❌ هیچ گۆرانییەک ناژەنرێت.")

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.secondary, row=1)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = interaction.guild.voice_client if interaction.guild else None
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()
            await self.send(interaction, "⏭️ **Skip** کرا.")
        else:
            await self.send(interaction, "❌ هیچ گۆرانییەک ناژەنرێت.")

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, row=1)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        music = self.music
        music.queues[self.guild_id] = []
        music.now_playing[self.guild_id] = None
        voice = interaction.guild.voice_client if interaction.guild else None
        if voice:
            await voice.disconnect()
        await self.send(interaction, "⏹️ **Stop:** پەخش و Queue وەستاندران.")

    @discord.ui.button(label="Queue", emoji="📋", style=discord.ButtonStyle.secondary, row=2)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        music = self.music
        items = music.get_queue(self.guild_id)
        current = music.now_playing.get(self.guild_id)
        lines = ["📋 **HMB NEXUS Queue**"]
        if current:
            lines.append(f"🎵 ئێستا: **{current['title']}**")
        for i, song in enumerate(items[:15], 1):
            lines.append(f"`{i}` • {song.get('title', song.get('url', 'Unknown'))[:90]}")
        if not current and not items:
            lines.append("📭 Queue بەتاڵە.")
        await self.send(interaction, "\n".join(lines)[:1900])

    @discord.ui.button(label="Volume", emoji="🔊", style=discord.ButtonStyle.secondary, row=2)
    async def volume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VolumeModal(self.panel))

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=2)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        items = self.music.get_queue(self.guild_id)
        if len(items) < 2:
            return await self.send(interaction, "ℹ️ بۆ Shuffle کەمتر لە ٢ گۆرانی هەیە.")
        random.shuffle(items)
        await self.send(interaction, "🔀 **Queue Shuffle** کرا.")

    @discord.ui.button(label="Lyrics", emoji="📜", style=discord.ButtonStyle.secondary, row=2)
    async def lyrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = self.music.now_playing.get(self.guild_id)
        if not current:
            return await self.send(interaction, "❌ هیچ گۆرانییەک ناژەنرێت.")
        await self.send(
            interaction,
            f"📜 Lyrics API لەم وەشانەدا نییە.\n🔗 {current.get('url', '')}",
        )


class MusicPanel(commands.Cog):
    """Interactive HMB NEXUS music control panel."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def music(self):
        return self.bot.get_cog("Music")

    @commands.hybrid_command(name="musicpanel", aliases=("musiccontrol", "player"))
    async def musicpanel(self, ctx: commands.Context):
        """Open the HMB NEXUS interactive music control panel."""
        if not ctx.guild:
            return await ctx.send("❌ ئەم فەرمانە تەنها لە سێرڤەر کار دەکات.")

        music = self.music
        if music is None:
            return await ctx.send("❌ Music system لۆد نەکراوە.")

        current = music.now_playing.get(ctx.guild.id)
        items = music.get_queue(ctx.guild.id)
        embed = discord.Embed(
            title="🎵 HMB NEXUS • MUSIC CONTROL",
            description=(
                "🔎 **Search:** لینکێکی YouTube یان ناوی گۆرانی بنووسە.\n"
                "▶️ Play/Pause • ⏭ Skip • ⏹ Stop • 📋 Queue\n"
                "🔊 Volume • 🔀 Shuffle • 📜 Lyrics"
            ),
            color=0x7C3AED,
        )

        if current:
            duration = int(current.get("duration") or 0)
            mins, secs = divmod(duration, 60)
            embed.add_field(
                name="🎵 NOW PLAYING",
                value=(
                    f"**{current.get('title', 'Unknown')}**\n"
                    f"⏱ `{mins}:{secs:02d}` • 🔊 `{current.get('volume', 100)}%`"
                ),
                inline=False,
            )
            if current.get("thumbnail"):
                embed.set_thumbnail(url=current["thumbnail"])
        else:
            embed.add_field(name="🎵 NOW PLAYING", value="Nothing is playing.", inline=False)

        queue_text = "\n".join(
            f"`{i}` • {song.get('title', 'Unknown')[:70]}"
            for i, song in enumerate(items[:5], 1)
        ) or "Queue is empty."
        embed.add_field(name=f"📋 QUEUE ({len(items)})", value=queue_text, inline=False)
        embed.set_footer(text="HMB • NEXUS | Powered by HONAR")

        await ctx.send(embed=embed, view=MusicControlView(self, ctx.guild.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicPanel(bot))
