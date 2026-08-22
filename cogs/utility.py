import discord
from discord.ext import commands
import aiohttp
import datetime
import asyncio


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["latency", "پینگ"])
    async def ping(self, ctx):
        """پشکنینی پینگی بۆت"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 پۆنگ!",
            description=f"**پینگ:** {latency}ms",
            color=0x2ecc71 if latency < 100 else (0xf1c40f if latency < 200 else 0xe74c3c)
        )
        await ctx.send(embed=embed)

    @commands.command(name="uptime", aliases=["ut", "کات_کارکردن"])
    async def uptime(self, ctx):
        """ماوەی کارکردنی بۆت"""
        delta = datetime.datetime.now() - self.bot.start_time
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        await ctx.send(
            f"⏱ **ماوەی کارکردن:** {days} ڕۆژ، {hours} کاتژمێر، "
            f"{minutes} خولەک، {seconds} چرکە"
        )

    @commands.command(name="avatar", aliases=["av", "pfp", "وێنەی_ئەندام"])
    async def avatar(self, ctx, member: discord.Member = None):
        """پیشاندانی وێنەی ئەندام"""
        if not member:
            member = ctx.author
        embed = discord.Embed(
            title=f"🖼 وێنەی {member.name}",
            color=member.color
        )
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["ui", "memberinfo", "زانیاری_ئەندام"])
    async def userinfo(self, ctx, member: discord.Member = None):
        """زانیاری وردی ئەندام"""
        if not member:
            member = ctx.author
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        embed = discord.Embed(
            title=f"👤 زانیاری {member.name}",
            color=member.color,
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="**ناو**", value=member.name, inline=True)
        embed.add_field(name="**ناسنامە**", value=member.mention, inline=True)
        embed.add_field(name="**ID**", value=member.id, inline=False)
        embed.add_field(name="**بۆتە؟**", value="بەڵێ 🤖" if member.bot else "نەخێر 👤", inline=True)
        embed.add_field(name="**بەرزترین ڕۆڵ**", value=member.top_role.mention, inline=True)
        embed.add_field(name="**ڕۆڵەکان**", value=", ".join(roles[:5]) if roles else "هیچ", inline=False)
        embed.add_field(name="**چووەتە سێرڤەر**", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="**بەکارهێنەر بووە**", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["si", "guildinfo", "زانیاری_سێرڤەر"])
    async def serverinfo(self, ctx):
        """زانیاری سێرڤەر"""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"🏠 زانیاری {guild.name}",
            color=0x3498db,
            timestamp=datetime.datetime.now()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="**ناو**", value=guild.name, inline=True)
        embed.add_field(name="**ID**", value=guild.id, inline=True)
        embed.add_field(name="**خاوەن**", value=guild.owner.mention, inline=True)
        embed.add_field(name="**ئەندامان**", value=f"{guild.member_count} 👥", inline=True)
        embed.add_field(name="**چانێلەکان**", value=f"{len(guild.channels)} 💬", inline=True)
        embed.add_field(name="**ڕۆڵەکان**", value=f"{len(guild.roles)} 🏷", inline=True)
        embed.add_field(name="**بۆتەکان**", value=sum(1 for m in guild.members if m.bot), inline=True)
        embed.add_field(name="**ئەندامانی مرۆڤ**", value=sum(1 for m in guild.members if not m.bot), inline=True)
        embed.add_field(name="**بوونەتە سێرڤەر**", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.set_footer(text=f"{len(guild.emojis)} ئیمۆجی")
        await ctx.send(embed=embed)

    @commands.command(name="poll", aliases=["vote", "survey", "ڕاپرسی"])
    @commands.has_permissions(manage_messages=True)
    async def poll(self, ctx, question, *options):
        """دروستکردنی ڕاپرسی - !poll "پرسیار" بەڵێ نەخێر"""
        if len(options) < 2:
            return await ctx.send("❌ بەلایەنی کەم ٢ هەڵبژاردە")
        if len(options) > 10:
            return await ctx.send("❌ زۆرترین ١٠ هەڵبژاردە")
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        embed = discord.Embed(title=f"📊 {question}", color=0x3498db)
        for i, opt in enumerate(options):
            embed.add_field(name=f"{emojis[i]} {opt}", value="دەنگبدە! 🗳", inline=True)
        embed.set_footer(text=f"لەلایەن {ctx.author.name}")
        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @commands.command(name="remind", aliases=["reminder", "بیرخستنەوە"])
    async def remind(self, ctx, time: str, *, text: str):
        """بیرخستنەوە - نمونە: !remind 10m نامە بنووسە"""
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        unit = time[-1]
        if unit not in units:
            return await ctx.send("❌ بەکاربێنە: s=چرکە, m=خولەک, h=کاتژمێر, d=ڕۆژ")
        try:
            amount = int(time[:-1])
        except:
            return await ctx.send("❌ ژمارە نادروستە")
        seconds = amount * units[unit]
        if seconds > 604800:
            return await ctx.send("❌ زۆرترین کات ٧ ڕۆژ")
        await ctx.send(f"⏰ **بیرخستنەوە:** {text}\n⏱ دوای {amount}{unit}")
        await asyncio.sleep(seconds)
        await ctx.author.send(f"⏰ **بیرخستنەوە:** {text}")

    @commands.command(name="translate", aliases=["tr", "وەرگێڕان"])
    async def translate(self, ctx, target: str, *, text: str):
        """وەرگێڕانی دەق - !translate en سڵاو (کۆدی زمان)"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://translate.googleapis.com/translate_a/single"
                f"?client=gtx&sl=auto&tl={target}&dt=t&q={text}"
            ) as r:
                if r.status != 200:
                    return await ctx.send("❌ وەرگێڕان سەرکەوتوو نەبوو")
                data = await r.json()
        result = data[0][0][0] if data and data[0] and data[0][0] else text
        await ctx.send(f"🌍 **وەرگێڕان ({target}):** {result}")

    @commands.command(name="calculator", aliases=["calc", "math", "ژمێر"])
    async def calculator(self, ctx, *, expression: str):
        """ژمێرەر - !calc 2+2*3"""
        allowed = "0123456789+-*/(). "
        if not all(c in allowed for c in expression):
            return await ctx.send("❌ تەنها ژمارە و +-*/()")
        try:
            result = eval(expression)
            await ctx.send(f"🔢 **{expression} = {result}**")
        except:
            await ctx.send("❌ هەڵە لە ژمێرەر")


async def setup(bot):
    bot.start_time = datetime.datetime.now()
    await bot.add_cog(Utility(bot))
