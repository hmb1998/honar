import asyncio
import ast
import datetime
import operator
from contextlib import suppress

import aiohttp
import discord
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["latency", "پینگ"])
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        color = 0x2ecc71 if latency < 100 else (0xf1c40f if latency < 200 else 0xe74c3c)
        embed = discord.Embed(title="🏓 پۆنگ!", description=f"**پینگ:** {latency}ms", color=color)
        await ctx.send(embed=embed)

    @commands.command(name="uptime", aliases=["ut", "کات_کارکردن"])
    async def uptime(self, ctx):
        start = getattr(self.bot, "start_time", None)
        if start is None:
            return await ctx.send("❌ کاتی دەستپێکردنی Bot دیاری نییە.")
        delta = datetime.datetime.now(datetime.timezone.utc) - start
        total = max(0, int(delta.total_seconds()))
        days, rem = divmod(total, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        await ctx.send(f"⏱ **ماوەی کارکردن:** {days} ڕۆژ، {hours} کاتژمێر، {minutes} خولەک، {seconds} چرکە")

    @commands.command(name="avatar", aliases=["av", "pfp", "وێنەی_ئەندام"])
    async def avatar(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"🖼 وێنەی {member.name}", color=member.color)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["ui", "memberinfo", "زانیاری_ئەندام"])
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        roles = [r.mention for r in member.roles if r != ctx.guild.default_role]
        embed = discord.Embed(title=f"👤 زانیاری {member.name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ناو", value=member.name, inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="بۆتە؟", value="بەڵێ 🤖" if member.bot else "نەخێر 👤", inline=True)
        embed.add_field(name="بەرزترین ڕۆڵ", value=member.top_role.mention, inline=True)
        embed.add_field(name="ڕۆڵەکان", value=", ".join(roles[:10]) if roles else "هیچ", inline=False)
        if member.joined_at:
            embed.add_field(name="چووەتە سێرڤەر", value=discord.utils.format_dt(member.joined_at, "D"), inline=True)
        embed.add_field(name="دروستکردنی ئەکاونت", value=discord.utils.format_dt(member.created_at, "D"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["si", "guildinfo", "زانیاری_سێرڤەر"])
    async def serverinfo(self, ctx):
        guild = ctx.guild
        owner = guild.owner.mention if guild.owner else "نەزانراو"
        embed = discord.Embed(title=f"🏠 زانیاری {guild.name}", color=0x3498db)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="ناو", value=guild.name, inline=True)
        embed.add_field(name="ID", value=str(guild.id), inline=True)
        embed.add_field(name="خاوەن", value=owner, inline=True)
        embed.add_field(name="ئەندامان", value=f"{guild.member_count} 👥", inline=True)
        embed.add_field(name="چانێلەکان", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="ڕۆڵەکان", value=str(len(guild.roles)), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="poll", aliases=["vote", "survey", "ڕاپرسی"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(add_reactions=True, embed_links=True)
    async def poll(self, ctx, question: str, *options):
        if not 2 <= len(options) <= 10:
            return await ctx.send("❌ بەلایەنی کەم ٢ و زۆرترین ١٠ هەڵبژاردە.")
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        embed = discord.Embed(title=f"📊 {question}", color=0x3498db)
        for i, option in enumerate(options):
            embed.add_field(name=f"{emojis[i]} {option}", value="دەنگبدە! 🗳", inline=True)
        embed.set_footer(text=f"لەلایەن {ctx.author.name}")
        msg = await ctx.send(embed=embed)
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @commands.command(name="remind", aliases=["reminder", "بیرخستنەوە"])
    async def remind(self, ctx, time_text: str, *, text: str):
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        if not time_text or time_text[-1].lower() not in units:
            return await ctx.send("❌ بەکاربێنە: `10s`, `10m`, `1h`, `1d`")
        try:
            amount = int(time_text[:-1])
        except ValueError:
            return await ctx.send("❌ ژمارەکە نادروستە.")
        if amount <= 0:
            return await ctx.send("❌ کات دەبێت زیاتر لە 0 بێت.")
        seconds = amount * units[time_text[-1].lower()]
        if seconds > 604800:
            return await ctx.send("❌ زۆرترین کات ٧ ڕۆژە.")
        await ctx.send(f"⏰ **بیرخستنەوە:** {text}\n⏱ دوای {time_text}")
        await asyncio.sleep(seconds)
        with suppress(discord.Forbidden, discord.HTTPException):
            await ctx.author.send(f"⏰ **بیرخستنەوە:** {text}")

    @commands.command(name="translate", aliases=["tr", "وەرگێڕان"])
    async def translate(self, ctx, target: str, *, text: str):
        if not re_safe_lang(target):
            return await ctx.send("❌ کۆدی زمان نادروستە.")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://translate.googleapis.com/translate_a/single",
                    params={"client": "gtx", "sl": "auto", "tl": target, "dt": "t", "q": text},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    if r.status != 200:
                        return await ctx.send("❌ وەرگێڕان سەرکەوتوو نەبوو.")
                    data = await r.json()
            result = "".join(part[0] for part in data[0] if part and part[0])
            await ctx.send(f"🌍 **وەرگێڕان ({target}):** {result[:1900]}")
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            await ctx.send("❌ کێشەیەک لە وەرگێڕان ڕوویدا.")

    @commands.command(name="calculator", aliases=["calc", "math", "ژمێر"])
    async def calculator(self, ctx, *, expression: str):
        try:
            result = safe_calculate(expression)
            await ctx.send(f"🔢 **{expression} = {result}**")
        except (ValueError, TypeError, ZeroDivisionError):
            await ctx.send("❌ هەژمارکردنەکە نادروستە.")


def re_safe_lang(value):
    return len(value) <= 10 and value.isalpha() and value.isascii()


_ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    if len(expression) > 100:
        raise ValueError("expression too long")
    tree = ast.parse(expression, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if abs(node.value) > 10**12:
                raise ValueError("number too large")
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(node.op)](evaluate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
            left, right = evaluate(node.left), evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 12:
                raise ValueError("power too large")
            result = _ALLOWED_OPS[type(node.op)](left, right)
            if abs(result) > 10**15:
                raise ValueError("result too large")
            return result
        raise ValueError("unsupported expression")

    return evaluate(tree)


async def setup(bot):
    await bot.add_cog(Utility(bot))
