import discord
from discord.ext import commands
import datetime


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}

    @commands.command(name="warn", aliases=["w", "ئاگاداری"])
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason="هۆکار نەدراوە"):
        """ئاگادارکردنەوەی ئەندام"""
        if member.id not in self.warnings:
            self.warnings[member.id] = []
        self.warnings[member.id].append({
            "reason": reason,
            "mod": ctx.author.id,
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        count = len(self.warnings[member.id])
        embed = discord.Embed(title="⚠️ ئاگادارکردنەوە", color=0xffcc00)
        embed.add_field(name="ئەندام", value=member.mention, inline=False)
        embed.add_field(name="هۆکار", value=reason, inline=False)
        embed.add_field(name="ژمارە", value=f"#{count}", inline=True)
        embed.add_field(name="لەلایەن", value=ctx.author.mention, inline=True)
        embed.set_footer(text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        await ctx.send(embed=embed)
        try:
            await member.send(f"⚠️ لە **{ctx.guild.name}** ئاگادارکرایتەوە: {reason}")
        except:
            pass

    @commands.command(name="warnings", aliases=["warns", "ئاگادارییەکان"])
    @commands.has_permissions(kick_members=True)
    async def warnings(self, ctx, member: discord.Member):
        """پیشاندانی هەموو ئاگادارییەکانی ئەندام"""
        warns = self.warnings.get(member.id, [])
        if not warns:
            return await ctx.send(f"✅ **{member.name}** هیچ ئاگادارییەکی نییە ✅")
        embed = discord.Embed(
            title=f"⚠️ ئاگادارییەکانی {member.name}",
            color=0xffcc00
        )
        for i, w in enumerate(warns, 1):
            mod = ctx.guild.get_member(w["mod"])
            embed.add_field(
                name=f"#{i} - {w['time']}",
                value=f"**هۆکار:** {w['reason']}\n**لەلایەن:** {mod.mention if mod else 'نەزانراو'}",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="delwarn", aliases=["dw", "removewarn", "سڕینەوەی_ئاگاداری"])
    @commands.has_permissions(kick_members=True)
    async def delwarn(self, ctx, member: discord.Member, index: int = None):
        """لابردنی ئاگاداری (بەبێ ژمارە هەموویان دەسڕێتەوە)"""
        if member.id not in self.warnings or not self.warnings[member.id]:
            return await ctx.send(f"❌ **{member.name}** هیچ ئاگادارییەکی نییە")
        if index:
            if 1 <= index <= len(self.warnings[member.id]):
                self.warnings[member.id].pop(index - 1)
                await ctx.send(f"✅ ئاگاداری #{index} لابرا")
            else:
                await ctx.send(f"❌ ژمارە نادروستە. {len(self.warnings[member.id])} ئاگاداری هەیە")
        else:
            self.warnings[member.id] = []
            await ctx.send(f"✅ هەموو ئاگادارییەکانی **{member.name}** سڕانەوە")

    @commands.command(name="voicekick", aliases=["vkick", "disconnect", "دەرکردن_لە_ڤۆیس"])
    @commands.has_permissions(move_members=True)
    async def voicekick(self, ctx, member: discord.Member):
        """دەرکردنی ئەندام لە ڤۆیس چانێل"""
        if member.voice:
            await member.move_to(None)
            await ctx.send(f"👢 **{member}** لە ڤۆیس دەرکرا")
        else:
            await ctx.send("❌ ئەندام لە ڤۆیس نییە")

    @commands.command(name="voicemove", aliases=["vmove", "گواستنەوە"])
    @commands.has_permissions(move_members=True)
    async def voicemove(self, ctx, member: discord.Member, *, channel: discord.VoiceChannel):
        """گواستنەوەی ئەندام بۆ ڤۆیس چانێلێکی تر"""
        if member.voice:
            await member.move_to(channel)
            await ctx.send(f"🚚 **{member}** گوازرایەوە بۆ **{channel}**")
        else:
            await ctx.send("❌ ئەندام لە ڤۆیس نییە")

    @commands.command(name="massrole", aliases=["mass", "ڕۆڵی_گشتی"])
    @commands.has_permissions(manage_roles=True)
    async def massrole(self, ctx, role: discord.Role):
        """زیادکردنی ڕۆڵ بۆ هەموو ئەندامان"""
        count = 0
        for member in ctx.guild.members:
            if not member.bot and role not in member.roles:
                try:
                    await member.add_roles(role)
                    count += 1
                except:
                    pass
        await ctx.send(f"✅ ڕۆڵی **{role}** بۆ **{count}** ئەندام زیادکرا")

    @commands.command(name="banlist", aliases=["bans", "لیستی_قەدەغە"])
    @commands.has_permissions(ban_members=True)
    async def banlist(self, ctx):
        """پیشاندانی لیستی قەدەغەکراوان"""
        banned = [entry async for entry in ctx.guild.bans()]
        if not banned:
            return await ctx.send("📭 هیچ کەسێک قەدەغەنەکراوە")
        msg = "**🔨 لیستی قەدەغەکراوان:**\n"
        for entry in banned[:20]:
            msg += f"- **{entry.user}** - {entry.reason or 'بێ هۆکار'}\n"
        await ctx.send(msg[:2000])

    @commands.command(name="slowmodeoff", aliases=["slowoff", "لابردنی_هێواشی"])
    @commands.has_permissions(manage_channels=True)
    async def slowmodeoff(self, ctx):
        """لابردنی مۆدی هێواش"""
        await ctx.channel.edit(slowmode_delay=0)
        await ctx.send("⚡ **مۆدی هێواش لابرا**")

    @commands.command(name="nuke", aliases=["نۆک"])
    @commands.has_permissions(administrator=True)
    async def nuke(self, ctx):
        """سڕینەوە و دروستکردنەوەی چانێل (نۆک)"""
        pos = ctx.channel.position
        name = ctx.channel.name
        topic = ctx.channel.topic
        nsfw = ctx.channel.nsfw
        slowmode_delay = ctx.channel.slowmode_delay
        await ctx.channel.delete()
        new = await ctx.channel.clone(name=name, nsfw=nsfw, topic=topic)
        await new.edit(slowmode_delay=slowmode_delay, position=pos)
        await new.send("💣 **چانێل نۆک کرایەوە!**")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
