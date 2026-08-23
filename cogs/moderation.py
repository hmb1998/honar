import discord
from discord.ext import commands
from datetime import datetime, timezone


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # (guild_id, member_id) -> warnings
        self.warning_data = {}

    def key(self, guild_id, member_id):
        return guild_id, member_id

    def can_moderate(self, ctx, member):
        if member == ctx.author:
            return False, "❌ ناتوانیت خۆت moderate بکەیت."
        if member == ctx.guild.owner:
            return False, "❌ ناتوانیت خاوەنی سێرڤەر moderate بکەیت."
        if ctx.author != ctx.guild.owner and member.top_role >= ctx.author.top_role:
            return False, "❌ ڕۆڵی ئەندامەکە لە تۆ یان بەرزترە."
        if ctx.guild.me and member.top_role >= ctx.guild.me.top_role:
            return False, "❌ ڕۆڵی ئەندامەکە لە Bot یان بەرزترە."
        return True, None

    @commands.hybrid_command(name="warn", aliases=["w", "ئاگاداری"])
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str ="هۆکار نەدراوە"):
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)

        key = self.key(ctx.guild.id, member.id)
        warns = self.warning_data.setdefault(key, [])
        warns.append({
            "reason": reason[:1000],
            "mod": ctx.author.id,
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        })

        embed = discord.Embed(title="⚠️ ئاگادارکردنەوە", color=0xffcc00)
        embed.add_field(name="ئەندام", value=member.mention, inline=False)
        embed.add_field(name="هۆکار", value=reason[:1024], inline=False)
        embed.add_field(name="ژمارە", value=f"#{len(warns)}", inline=True)
        embed.add_field(name="لەلایەن", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

        try:
            await member.send(f"⚠️ لە **{ctx.guild.name}** ئاگادارکرایتەوە.\n📛 {reason}")
        except (discord.Forbidden, discord.HTTPException):
            pass

    @commands.hybrid_command(name="warnings", aliases=["warns", "ئاگادارییەکان"])
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        warns = self.warning_data.get(self.key(ctx.guild.id, member.id), [])
        if not warns:
            return await ctx.send(f"✅ **{member}** هیچ ئاگادارییەکی نییە.")

        embed = discord.Embed(title=f"⚠️ ئاگادارییەکانی {member}", color=0xffcc00)
        for i, warning in enumerate(warns[:25], 1):
            mod = ctx.guild.get_member(warning["mod"])
            value = f"**هۆکار:** {warning['reason']}\n**لەلایەن:** {mod.mention if mod else 'نەناسراو'}"
            embed.add_field(name=f"#{i} — {warning['time']}", value=value[:1024], inline=False)
        if len(warns) > 25:
            embed.set_footer(text=f"{len(warns) - 25} ئاگاداریی تر هەیە.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="delwarn", aliases=["dw", "removewarn", "سڕینەوەی_ئاگاداری"])
    @commands.has_permissions(kick_members=True)
    async def delwarn(self, ctx, member: discord.Member, index: int = None):
        key = self.key(ctx.guild.id, member.id)
        warns = self.warning_data.get(key, [])
        if not warns:
            return await ctx.send(f"❌ **{member}** هیچ ئاگادارییەکی نییە.")

        if index is not None:
            if not 1 <= index <= len(warns):
                return await ctx.send(f"❌ ژمارەکە نادروستە. {len(warns)} ئاگاداری هەیە.")
            warns.pop(index - 1)
            if not warns:
                self.warning_data.pop(key, None)
            return await ctx.send(f"✅ ئاگاداری #{index} لابرا.")

        self.warning_data.pop(key, None)
        await ctx.send(f"✅ هەموو ئاگادارییەکانی **{member}** سڕانەوە.")

    @commands.hybrid_command(name="voicekick", aliases=["vkick", "disconnect", "دەرکردن_لە_ڤۆیس"])
    @commands.has_permissions(move_members=True)
    @commands.bot_has_permissions(move_members=True)
    async def voicekick(self, ctx, member: discord.Member):
        if not member.voice:
            return await ctx.send("❌ ئەندام لە ڤۆیس نییە.")
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        try:
            await member.move_to(None, reason=f"By {ctx.author}")
            await ctx.send(f"👢 **{member}** لە ڤۆیس دەرکرا.")
        except discord.HTTPException:
            await ctx.send("❌ نەتوانرا ئەندام لە ڤۆیس دەرکرێت.")

    @commands.hybrid_command(name="voicemove", aliases=["vmove", "گواستنەوە"])
    @commands.has_permissions(move_members=True)
    @commands.bot_has_permissions(move_members=True)
    async def voicemove(self, ctx, member: discord.Member, *, channel: discord.VoiceChannel):
        if not member.voice:
            return await ctx.send("❌ ئەندام لە ڤۆیس نییە.")
        ok, error = self.can_moderate(ctx, member)
        if not ok:
            return await ctx.send(error)
        try:
            await member.move_to(channel, reason=f"By {ctx.author}")
            await ctx.send(f"🚚 **{member}** گوازرایەوە بۆ **{channel}**")
        except discord.HTTPException:
            await ctx.send("❌ نەتوانرا ئەندام بگوازرێتەوە.")

    @commands.hybrid_command(name="massrole", aliases=["mass", "ڕۆڵی_گشتی"])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def massrole(self, ctx, role: discord.Role):
        if role.is_default():
            return await ctx.send("❌ ناتوانیت @everyone زیاد بکەیت.")
        if role.managed:
            return await ctx.send("❌ ئەم role ـە managed ـە.")
        if role >= ctx.guild.me.top_role:
            return await ctx.send("❌ ئەم role ـە لە role ـی Bot بەرزترە یان یەکسانە.")

        count = 0
        failed = 0
        for member in ctx.guild.members:
            if member.bot or role in member.roles:
                continue
            try:
                await member.add_roles(role, reason=f"Mass role by {ctx.author}")
                count += 1
            except (discord.Forbidden, discord.HTTPException):
                failed += 1

        await ctx.send(f"✅ Role **{role}** زیادکرا بۆ **{count}** ئەندام.\n⚠️ سەرکەوتوو نەبوو: **{failed}**")

    @commands.hybrid_command(name="banlist", aliases=["bans", "لیستی_قەدەغە"])
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx):
        try:
            banned = [entry async for entry in ctx.guild.bans(limit=None)]
        except discord.HTTPException:
            return await ctx.send("❌ نەتوانرا لیستی Ban بخوێندرێتەوە.")

        if not banned:
            return await ctx.send("📭 هیچ کەسێک قەدەغە نەکراوە.")

        lines = [f"**🔨 لیستی قەدەغەکراوان ({len(banned)}):**"]
        for entry in banned[:50]:
            line = f"- **{entry.user}** (`{entry.user.id}`) — {entry.reason or 'بێ هۆکار'}"
            lines.append(line[:180])
        await ctx.send("\n".join(lines)[:2000])

    @commands.hybrid_command(name="slowmodeoff", aliases=["slowoff", "لابردنی_هێواشی"])
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmodeoff(self, ctx):
        await ctx.channel.edit(slowmode_delay=0, reason=f"By {ctx.author}")
        await ctx.send("⚡ **مۆدی هێواش لابرا.**")

    @commands.hybrid_command(name="nuke", aliases=["نۆک"])
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def nuke(self, ctx):
        channel = ctx.channel
        position = channel.position
        category = channel.category
        name = channel.name
        topic = getattr(channel, "topic", None)
        nsfw = getattr(channel, "nsfw", False)
        slowmode = getattr(channel, "slowmode_delay", 0)

        try:
            new = await channel.clone(
                name=name,
                reason=f"Nuke by {ctx.author}"
            )
            if category:
                await new.edit(category=category, position=position, reason=f"Nuke by {ctx.author}")
            else:
                await new.edit(position=position, reason=f"Nuke by {ctx.author}")
            await new.edit(
                topic=topic,
                nsfw=nsfw,
                slowmode_delay=slowmode,
                reason=f"Nuke by {ctx.author}"
            )
            await channel.delete(reason=f"Nuke by {ctx.author}")
            await new.send("💣 **چانێل نۆک کرایەوە!**")
        except discord.HTTPException:
            await ctx.send("❌ Nuke سەرکەوتوو نەبوو.")

    @nuke.error
    async def nuke_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ تکایە {error.retry_after:.1f} چرکە چاوەڕێ بکە.")
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Moderation(bot))
