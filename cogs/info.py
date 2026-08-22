import discord
from discord.ext import commands
import datetime


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", aliases=["h", "commands", "یارمەتی"])
    async def help(self, ctx, *, command_name: str = None):
        """پیشاندانی هەموو کۆماندەکان یان یارمەتی کۆماندێکی دیاریکراو"""
        if command_name:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                return await ctx.send(f"❌ کۆماندی `{command_name}` نەدۆزرایەوە")
            aliases = ", ".join(cmd.aliases) if cmd.aliases else "هیچ"
            embed = discord.Embed(
                title=f"📖 یارمەتی: {cmd.name}",
                description=cmd.help or "بێ وەسف",
                color=0x3498db
            )
            embed.add_field(name="🔤 ناوەکانی تر", value=f"`{aliases}`", inline=False)
            embed.add_field(name="📝 بەکارهێنان", value=f"`{self.bot.command_prefix}{cmd.name}`", inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title=f"📖 لیستی کۆماندەکانی {self.bot.user.name}",
                description=f"پێشگر: `!` | کۆی گشتی: **{len(self.bot.commands)}** کۆماند",
                color=0x3498db
            )
            cogs_data = {}
            for cmd in self.bot.commands:
                cog_name = cmd.cog_name or "بێ پۆل"
                if cog_name not in cogs_data:
                    cogs_data[cog_name] = []
                cogs_data[cog_name].append(cmd.name)
            for cog, cmds in sorted(cogs_data.items()):
                embed.add_field(
                    name=f"📂 {cog} ({len(cmds)})",
                    value=", ".join(f"`{c}`" for c in cmds[:10]),
                    inline=False
                )
            embed.set_footer(text="!help [کۆماند] بۆ زانیاری وردتر")
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="botinfo", aliases=["bi", "about", "زانیاری_بۆت"])
    async def botinfo(self, ctx):
        """زانیاری دەربارەی بۆت"""
        start_time = getattr(self.bot, "start_time", None)
        if start_time is None:
            start_time = datetime.datetime.now(datetime.timezone.utc)
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        delta = datetime.datetime.now(datetime.timezone.utc) - start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        embed = discord.Embed(
            title=f"🤖 زانیاری {self.bot.user.name}",
            color=0x2b3137
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        embed.add_field(name="📦 وەشان", value="v2.0.0", inline=True)
        embed.add_field(name="🐍 پایتۆن", value="3.11+", inline=True)
        embed.add_field(name="📚 discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="⏱ کارکردن", value=f"{days}ڕ {hours}ک {minutes}خ {seconds}چ", inline=True)
        embed.add_field(name="👥 سێرڤەرەکان", value=f"{len(self.bot.guilds)} 🏠", inline=True)
        embed.add_field(name="📊 کۆماندەکان", value=f"{len(self.bot.commands)} ⚡", inline=True)
        embed.set_footer(text=f"ID: {self.bot.user.id}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverlist", aliases=["guilds", "سێرڤەرەکان"])
    @commands.is_owner()
    async def serverlist(self, ctx):
        """پێڕستی سێرڤەرەکانی بۆت (تەنها خاوەن)"""
        msg = "**🏠 سێرڤەرەکانی بۆت:**\n"
        for guild in self.bot.guilds:
            msg += f"- **{guild.name}** - {guild.member_count} ئەندام\n"
        await ctx.send(msg[:2000])

    @commands.hybrid_command(name="invite", aliases=["invitebot", "بانگهێشت"])
    async def invite(self, ctx):
        """لینکی بانگهێشتکردنی بۆت"""
        perms = discord.Permissions(
            send_messages=True, read_messages=True, connect=True, speak=True,
            use_voice_activation=True, kick_members=True, ban_members=True,
            moderate_members=True, manage_messages=True, manage_channels=True,
            manage_roles=True
        )
        link = discord.utils.oauth_url(self.bot.user.id, permissions=perms)
        embed = discord.Embed(
            title="🔗 بانگهێشتی بۆت بکە",
            description=f"[کرتە بکە بۆ بانگهێشتکردن]({link})",
            color=0x3498db
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="support", aliases=["پشتیوانی"])
    async def support(self, ctx):
        """زانیاری پشتیوانی"""
        embed = discord.Embed(
            title="🛠 پشتیوانی",
            description="بۆ پشتیوانی و ڕاپۆرتی هەڵەکان:\n- ناردنی نامە بە خاوەنی بۆت\n- دروستکردنی ئیش لە گیتهاب",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stats", aliases=["statistics", "ئامارەکان"])
    async def stats(self, ctx):
        """ئامارەکانی بۆت"""
        total_members = sum(g.member_count for g in self.bot.guilds)
        total_channels = sum(len(g.channels) for g in self.bot.guilds)
        total_roles = sum(len(g.roles) for g in self.bot.guilds)
        embed = discord.Embed(
            title="📊 ئامارە گشتییەکان",
            color=0x9b59b6
        )
        embed.add_field(name="🏠 سێرڤەر", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 ئەندام", value=total_members, inline=True)
        embed.add_field(name="💬 چانێل", value=total_channels, inline=True)
        embed.add_field(name="🏷 ڕۆڵ", value=total_roles, inline=True)
        embed.add_field(name="⚡ کۆماند", value=len(self.bot.commands), inline=True)
        embed.add_field(name="🤖 بۆت", value=sum(1 for g in self.bot.guilds for m in g.members if m.bot), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roleinfo", aliases=["ri", "زانیاری_ڕۆڵ"])
    async def roleinfo(self, ctx, *, role: discord.Role):
        """زانیاری ڕۆڵێک"""
        embed = discord.Embed(
            title=f"🏷 زانیاری {role.name}",
            color=role.color
        )
        embed.add_field(name="ID", value=role.id, inline=True)
        embed.add_field(name="ڕەنگ", value=str(role.color), inline=True)
        embed.add_field(name="جیا", value="بەڵێ" if role.hoist else "نەخێر", inline=True)
        embed.add_field(name="باسی", value="بەڵێ" if role.mentionable else "نەخێر", inline=True)
        embed.add_field(name="شوێن", value=role.position, inline=True)
        embed.add_field(name="ئەندام", value=len(role.members), inline=True)
        embed.add_field(name="دروستکراوە", value=role.created_at.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="channelinfo", aliases=["ci", "زانیاری_چانێل"])
    async def channelinfo(self, ctx, *, channel: discord.TextChannel = None):
        """زانیاری چانێلێک"""
        if not channel:
            channel = ctx.channel
        embed = discord.Embed(
            title=f"💬 زانیاری {channel.name}",
            color=0x3498db
        )
        embed.add_field(name="ID", value=channel.id, inline=True)
        embed.add_field(name="جۆر", value=str(channel.type), inline=True)
        embed.add_field(name="بابەت", value=channel.topic or "بێ بابەت", inline=False)
        embed.add_field(name="NSFW", value="بەڵێ 🔞" if channel.nsfw else "نەخێر", inline=True)
        embed.add_field(name="دروستکراوە", value=channel.created_at.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="emoji", aliases=["emojis", "ئیمۆجی"])
    async def emoji(self, ctx, *, emoji_name: str = None):
        """پیشاندانی ئیمۆجی یان لیستی هەموو ئیمۆجیەکان"""
        if emoji_name:
            emoji = discord.utils.get(ctx.guild.emojis, name=emoji_name)
            if emoji:
                embed = discord.Embed(title=f":{emoji.name}:", color=0xf1c40f)
                embed.set_image(url=emoji.url)
                embed.add_field(name="ID", value=emoji.id, inline=True)
                embed.add_field(name="ئەنیمەیشن", value="بەڵێ" if emoji.animated else "نەخێر", inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ ئیمۆجی `:{emoji_name}:` نەدۆزرایەوە")
        else:
            if not ctx.guild.emojis:
                return await ctx.send("📭 هیچ ئیمۆجیەکی سەرڤەر نییە")
            msg = f"**😃 ئیمۆجیەکانی {ctx.guild.name}:**\n"
            for e in ctx.guild.emojis[:50]:
                msg += f"{e} `:{e.name}:` "
            await ctx.send(msg[:2000])


async def setup(bot):
    await bot.add_cog(Info(bot))
