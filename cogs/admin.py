import discord
from discord.ext import commands
from datetime import timedelta


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def bot_member(self, guild):
        return guild.me

    def can_moderate(self, ctx, member):
        me = self.bot_member(ctx.guild)
        if member == ctx.author:
            return False, "❌ ناتوانیت خۆت moderate بکەیت."
        if member == ctx.guild.owner:
            return False, "❌ ناتوانیت خاوەنی سێرڤەر moderate بکەیت."
        if me and member >= me:
            return False, "❌ ڕۆڵی ئەندامەکە لە Bot یان بەرزترە."
        if ctx.author != ctx.guild.owner and member >= ctx.author:
            return False, "❌ ڕۆڵی ئەندامەکە لە تۆ یان بەرزترە."
        return True, None

    @commands.hybrid_command(name="kick", aliases=["k", "دەرکردن"])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str ="هۆکاری دیاری نەکراو"):
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        try:
            await member.kick(reason=f"{reason} | By {ctx.author} ({ctx.author.id})")
            await ctx.send(f"👢 **{member}** دەرکرا.\n📛 {reason}")
        except discord.HTTPException:
            await ctx.send("❌ Kick سەرکەوتوو نەبوو.")

    @commands.hybrid_command(name="ban", aliases=["b", "قەدەغە"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str ="هۆکاری دیاری نەکراو"):
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        try:
            await member.ban(reason=f"{reason} | By {ctx.author} ({ctx.author.id})")
            await ctx.send(f"🔨 **{member}** قەدەغەکرا.\n📛 {reason}")
        except discord.HTTPException:
            await ctx.send("❌ Ban سەرکەوتوو نەبوو.")

    @commands.hybrid_command(name="unban", aliases=["ub", "لابردنی_قەدەغە"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx, *, member: str):
        member = member.strip()
        try:
            async for entry in ctx.guild.bans(limit=None):
                user = entry.user
                if member == str(user.id) or member.lower() in str(user).lower():
                    await ctx.guild.unban(user, reason=f"By {ctx.author} ({ctx.author.id})")
                    return await ctx.send(f"✅ **{user}** قەدەغەی لابرا.")
        except discord.HTTPException:
            return await ctx.send("❌ نەتوانرا لیستی Ban بخوێندرێتەوە.")
        await ctx.send("❌ ئەندام نەدۆزرایەوە لە لیستی قەدەغەکراوان.")

    @commands.hybrid_command(name="mute", aliases=["timeout", "بێدەنگ"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int = 10, *, reason: str ="هۆکاری دیاری نەکراو"):
        if minutes < 1 or minutes > 40320:
            return await ctx.send("❌ ماوە دەبێت لە 1 تا 40320 خولەک بێت.")
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        try:
            await member.timeout(timedelta(minutes=minutes), reason=f"{reason} | By {ctx.author}")
            await ctx.send(f"🔇 **{member}** بۆ **{minutes}** خولەک timeout کرا.\n📛 {reason}")
        except discord.HTTPException:
            await ctx.send("❌ Timeout سەرکەوتوو نەبوو.")

    @commands.hybrid_command(name="unmute", aliases=["untimeout", "لابردنی_بێدەنگی"])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        try:
            await member.timeout(None, reason=f"By {ctx.author} ({ctx.author.id})")
            await ctx.send(f"🔊 **{member}** بێدەنگی لابرا.")
        except discord.HTTPException:
            await ctx.send("❌ نەتوانرا timeout لاببرێت.")

    @commands.hybrid_command(name="clear", aliases=["purge", "delete", "سڕینەوە"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def clear(self, ctx, amount: int):
        if not 1 <= amount <= 100:
            return await ctx.send("❌ ژمارەکە دەبێت لە 1 تا 100 بێت.")
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            await ctx.send(f"🧹 **{max(len(deleted) - 1, 0)}** نامە سڕانەوە.", delete_after=3)
        except discord.HTTPException:
            await ctx.send("❌ نەتوانرا نامەکان بسڕدرێنەوە.")

    @commands.hybrid_command(name="slowmode", aliases=["slow", "هێواش"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 5):
        if not 0 <= seconds <= 21600:
            return await ctx.send("❌ 0 تا 21600 چرکە.")
        await ctx.channel.edit(slowmode_delay=seconds, reason=f"By {ctx.author}")
        await ctx.send(f"🐢 **Slowmode:** {seconds} چرکە")

    @commands.hybrid_command(name="lock", aliases=["lockdown", "داخستن"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def lock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Lock by {ctx.author}")
        await ctx.send("🔒 **چانێل داخرا بۆ @everyone.**")

    @commands.hybrid_command(name="unlock", aliases=["کردنەوە"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unlock(self, ctx):
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unlock by {ctx.author}")
        await ctx.send("🔓 **چانێل کرایەوە.**")

    @commands.hybrid_command(name="nickname", aliases=["nick", "ناو"])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nick: str = None):
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        if nick and len(nick) > 32:
            return await ctx.send("❌ ناوی نوێ زۆر درێژە.")
        try:
            old = member.display_name
            await member.edit(nick=nick, reason=f"By {ctx.author}")
            await ctx.send(f"✏️ **{old}** گۆڕدرا بۆ **{nick or member.name}**")
        except discord.HTTPException:
            await ctx.send("❌ نەتوانرا nickname بگۆڕدرێت.")


async def setup(bot):
    await bot.add_cog(Admin(bot))
