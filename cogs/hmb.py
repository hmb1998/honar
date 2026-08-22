import discord
from discord import app_commands
from discord.ext import commands


class HMB(commands.Cog):
    """HMB NEXUS verification/status commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hmb_emojis", description="Test the 10 HMB NEXUS application emojis")
    async def hmb_emojis(self, interaction: discord.Interaction):
        emojis = [self.bot.hmb_emoji(i) for i in range(1, 11)]
        loaded = sum(1 for i in range(1, 11) if self.bot.get_hmb_emoji(i) is not None)

        embed = discord.Embed(
            title="👑 HMB NEXUS • Application Emojis",
            description="\n".join(f"**{i}.** {emojis[i - 1]}" for i in range(1, 11)),
            color=0x7C3AED,
        )
        embed.set_footer(text=f"Loaded: {loaded}/10 • HMB NEXUS")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="hmb_status", description="Show HMB NEXUS bot systems status")
    async def hmb_status(self, interaction: discord.Interaction):
        loaded_emojis = sum(1 for i in range(1, 11) if self.bot.get_hmb_emoji(i) is not None)
        embed = discord.Embed(title="👑 HMB NEXUS • System Status", color=0x7C3AED)
        embed.add_field(name="🤖 Bot", value="🟢 Online", inline=True)
        embed.add_field(name="😀 Application Emojis", value=f"🟢 {loaded_emojis}/10", inline=True)
        embed.add_field(name="⚡ Slash Commands", value=f"🟢 {len(self.bot.tree.get_commands())}", inline=True)
        embed.add_field(name="🌐 Servers", value=f"🟢 {len(self.bot.guilds)}", inline=True)
        embed.add_field(name="🎮 Gateway Presence", value="🟢 Active", inline=True)
        embed.add_field(name="🖼️ Rich Presence Assets", value="ℹ️ Activity/SDK only", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(HMB(bot))
