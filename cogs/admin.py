import discord
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick", aliases=["k", "دەرکردن"])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="هۆکاری دیاری نەکراو"):
        """دەرکردنی ئەندام لە سێرڤەر"""
        await member.kick(reason=reason)
        await ctx.send(f"👢 **{member}** دەرکرا - {reason}")

    @commands.command(name="ban", aliases=["b", "قەدەغە"])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="هۆکاری دیاری نەکراو"):
        """قەدەغەکردنی ئەندام لە سێرڤەر"""
        await member.ban(reason=reason)
        await ctx.send(f"🔨 **{member}** قەدەغەکرا - {reason}")

    @commands.command(name="unban", aliases=["ub", "لابردنی_قەدەغە"])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """لابردنی قەدەغەی ئەندام"""
        banned_users = [entry async for entry in ctx.guild.bans()]
        for ban_entry in banned_users:
            if member.lower() in ban_entry.user.name.lower() or member == str(ban_entry.user.id):
                await ctx.guild.unban(ban_entry.user)
                return await ctx.send(f"✅ **{ban_entry.user}** قەدەغەی لابرا")
        await ctx.send("❌ ئەندام نەدۆزرایەوە لە لیستی قەدەغەکراوان")

    @commands.command(name="mute", aliases=["timeout", "بێدەنگ"])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int = 10, *, reason="هۆکاری دیاری نەکراو"):
        """بێدەنگکردنی ئەندام بۆ ماوەیەک"""
        duration = discord.utils.utcnow() + __import__('datetime').timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 **{member}** بۆ {minutes} خولەک بێدەنگکرا - {reason}")

    @commands.command(name="unmute", aliases=["untimeout", "لابردنی_بێدەنگی"])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """لابردنی بێدەنگی ئەندام"""
        await member.timeout(None)
        await ctx.send(f"🔊 **{member}** بێدەنگی لابرا")

    @commands.command(name="clear", aliases=["purge", "delete", "سڕینەوە"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """سڕینەوەی نامەکانی چانێل"""
        if amount < 1 or amount > 100:
            return await ctx.send("❌ ژمارە ١-١٠٠")
        deleted = await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 **{len(deleted) - 1}** نامە سڕانەوە", delete_after=3)

    @commands.command(name="slowmode", aliases=["slow", "هێواش"])
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 5):
        """دانانی مۆدی هێواش بۆ چانێل"""
        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ ٠-٢١٦٠٠ چرکە")
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐢 **مۆدی هێواش:** {seconds} چرکە")

    @commands.command(name="lock", aliases=["lockdown", "داخستن"])
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """داخستنی چانێل بۆ ئەندامان"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 **چانێل داخرا**")

    @commands.command(name="unlock", aliases=["کردنەوە"])
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """کردنەوەی چانێل"""
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 **چانێل کرایەوە**")

    @commands.command(name="nickname", aliases=["nick", "ناو"])
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nick: str = None):
        """گۆڕینی ناوی ئەندام"""
        old = member.display_name
        await member.edit(nick=nick)
        await ctx.send(f"✏️ **ناوی {old}** گۆڕدرا بۆ **{nick or member.name}**")


async def setup(bot):
    await bot.add_cog(Admin(bot))
