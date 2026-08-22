import discord
from discord.ext import commands
import random
import aiohttp


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="say", aliases=["echo", "repeat", "بڵێ"])
    async def say(self, ctx, *, message: str):
        """ناردنی نامەیەک لەجیاتی تۆ"""
        await ctx.send(message)

    @commands.hybrid_command(name="8ball", aliases=["eightball", "fortune", "تۆپی_هەشت"])
    async def eightball(self, ctx, *, question: str):
        """پیشبینی بە تۆپی ٨"""
        answers = [
            "بەڵێ ✅", "نەخێر ❌", "دڵنیا بە", "دەکرێت 🎯",
            "بەداخەوە نەخێر", "بە دڵنیاییەوە بەڵێ ✅",
            "پرسیارەکە دووبارە بکەوە", "ناتوانم پێشبینی بکەم 🔮",
            "باشترین شت وا نییە", "بەتەواوەتی ✨",
            "خەیاڵی باشە 💭", "ڕوون نییە 🌫",
            "پێویستە چاوەڕوان بکەیت", "ئەوە دڵنیایە 🎲",
            "بەڵێ بە مەرجێک", "ناتوانم ڕاستی بڵێم 🤫"
        ]
        embed = discord.Embed(
            title="🎱 تۆپی ٨",
            description=f"**پرسیار:** {question}\n**وەڵام:** {random.choice(answers)}",
            color=random.choice([0x3498db, 0xe74c3c, 0x2ecc71, 0xf1c40f])
        )
        embed.set_footer(text=f"لەلایەن {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", aliases=["coin", "flip", "هەڵدانی_دراو"])
    async def coinflip(self, ctx):
        """هەڵدانی دراو - هێڵ یان نەخش"""
        result = random.choice(["هێڵ (Heads) 🪙", "نەخش (Tails) 🪙"])
        embed = discord.Embed(
            title="🪙 هەڵدانی دراو",
            description=f"**ئەنجام:** {result}",
            color=0xf1c40f
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dice", aliases=["roll", "تەختەی_ژمارە"])
    async def dice(self, ctx, sides: int = 6):
        """هەڵدانی تەختەی ژمارە (زیاتر لە ١٠٠٠ نا)"""
        if sides < 1 or sides > 1000:
            return await ctx.send("❌ ژمارە ١-١٠٠٠")
        result = random.randint(1, sides)
        embed = discord.Embed(
            title=f"🎲 تەختەی {sides} لایەنی",
            description=f"**ئەنجام:** {result}",
            color=0xe67e22
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="meme", aliases=["میم"])
    async def meme(self, ctx, subreddit: str = "memes"):
        """پیشاندانی میم لە ڕێددیت"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://meme-api.com/gimme/{subreddit}") as r:
                if r.status != 200:
                    return await ctx.send("❌ نەتوانرا میم وەربگیرێت")
                data = await r.json()
        embed = discord.Embed(
            title=data.get("title", "میم"),
            color=random.choice([0x3498db, 0xe74c3c, 0x2ecc71])
        )
        embed.set_image(url=data.get("url", ""))
        embed.set_footer(text=f"👍 {data.get('ups', 0)} | r/{data.get('subreddit', subreddit)}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="joke", aliases=["jokes", "گاڵتە"])
    async def joke(self, ctx):
        """گاڵتەیەکی هەرەمەکی"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://v2.jokeapi.dev/joke/Any?lang=de&blacklistFlags=nsfw") as r:
                data = await r.json()
            if data.get("type") == "single":
                await ctx.send(f"😂 {data['joke']}")
            else:
                await ctx.send(f"😂 {data['setup']}\n\n||{data['delivery']}||")

    @commands.hybrid_command(name="fact", aliases=["facts", "ڕاستی"])
    async def fact(self, ctx):
        """ڕاستییەکی هەرەمەکی"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/random.json?language=en") as r:
                data = await r.json()
        await ctx.send(f"💡 **ڕاستی:** {data.get('text', 'نەدۆزرایەوە')}")

    @commands.hybrid_command(name="reverse", aliases=["rev", "پێچەوانە"])
    async def reverse(self, ctx, *, text: str):
        """پێچەوانەکردنەوەی دەق"""
        await ctx.send(text[::-1][:2000])

    @commands.hybrid_command(name="choose", aliases=["pick", "ch", "هەڵبژاردن"])
    async def choose(self, ctx, options: str):
        """هەڵبژاردن لە نێوان چەند شتێک؛ هەڵبژاردەکان بە کۆما جیا بکەرەوە."""
        choices = [item.strip() for item in options.split(",") if item.strip()]
        if len(choices) < 2:
            return await ctx.send("❌ بەلایەنی کەم ٢ هەڵبژاردە بنووسە و بە کۆما جیاکیان بکەرەوە.")
        result = random.choice(choices)
        await ctx.send(f"🤔 **من هەڵدەبژێڕم:** {result}")

    @commands.hybrid_command(name="rps", aliases=["rockpaperscissors", "کەقەز_تێر_هەڵمەت"])
    async def rps(self, ctx, choice: str):
        """کەقەز، تێر، هەڵمەت (rock/paper/scissors)"""
        choices = {"کەقەز": "rock", "تێر": "scissors", "هەڵمەت": "paper",
                   "rock": "rock", "paper": "paper", "scissors": "scissors"}
        bot_choice = random.choice(list(choices.values())[:3])
        user = choices.get(choice.lower(), None)
        if not user:
            return await ctx.send("❌ هەڵبژاردن: کەقەز، تێر، هەڵمەت (rock, paper, scissors)")
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        results = {
            ("rock", "scissors"): "تۆ بردی 🎉", ("paper", "rock"): "تۆ بردی 🎉",
            ("scissors", "paper"): "تۆ بردی 🎉",
            ("scissors", "rock"): "بۆت بردی 🤖", ("rock", "paper"): "بۆت بردی 🤖",
            ("paper", "scissors"): "بۆت بردی 🤖"
        }
        if user == bot_choice:
            result = "یەکسان بوون ⚖️"
        else:
            result = results.get((user, bot_choice), results.get((bot_choice, user), "نەزانراو"))
        await ctx.send(
            f"{emojis[user]} **تۆ:** {user}\n"
            f"{emojis[bot_choice]} **بۆت:** {bot_choice}\n"
            f"**ئەنجام:** {result}"
        )


async def setup(bot):
    await bot.add_cog(Fun(bot))
