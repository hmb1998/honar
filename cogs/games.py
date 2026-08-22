import discord
from discord.ext import commands
import random
import asyncio


class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tictactoe", aliases=["ttt", "tic", "دۆزینەوە"])
    async def tictactoe(self, ctx, member: discord.Member):
        """یاری تیک تەک تۆ بە یاریزانێکی تر"""
        if member == ctx.author:
            return await ctx.send("❌ ناتوانیت لەگەڵ خۆت یاری بکەیت")
        if member.bot:
            return await ctx.send("❌ ناتوانیت لەگەڵ بۆت یاری بکەیت")

        board = ["⬜"] * 9
        current_player = ctx.author
        msg = await ctx.send("**🎮 تیک تەک تۆ**\n" + self.ttt_display(board))

        def check(reaction, user):
            return user in [ctx.author, member] and str(reaction.emoji) in "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣" and reaction.message.id == msg.id

        for turn in range(9):
            await msg.clear_reactions()
            for i in range(9):
                if board[i] == "⬜":
                    await msg.add_reaction(["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"][i])
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("⏰ کاتی یاری تەواو بوو")
            if user != current_player:
                await ctx.send(f"⏳ **{current_player.name}**، نۆبەی تۆیە!")
                continue
            pos = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"].index(str(reaction.emoji))
            if board[pos] != "⬜":
                await ctx.send("❌ ئەم شوێنە پڕە!")
                continue
            board[pos] = "❌" if current_player == ctx.author else "⭕"
            await msg.edit(content="**🎮 تیک تەک تۆ**\n" + self.ttt_display(board))

            winner = self.ttt_check(board)
            if winner or turn == 8:
                await msg.clear_reactions()
                if winner:
                    winner_user = ctx.author if winner == "❌" else member
                    await ctx.send(f"🎉 **{winner_user.name} بردی!**")
                else:
                    await ctx.send("⚖️ **یەکسان بوون!**")
                return
            current_player = member if current_player == ctx.author else ctx.author

    def ttt_display(self, board):
        return f"{board[0]}{board[1]}{board[2]}\n{board[3]}{board[4]}{board[5]}\n{board[6]}{board[7]}{board[8]}"

    def ttt_check(self, board):
        wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        for a, b, c in wins:
            if board[a] == board[b] == board[c] != "⬜":
                return board[a]
        return None

    @commands.command(name="guessnumber", aliases=["guess", "مەزەندە"])
    async def guessnumber(self, ctx):
        """مەزەندەکردنی ژمارەیەک لە ١-١٠٠"""
        number = random.randint(1, 100)
        attempts = 0
        await ctx.send("🔢 **مەزەندە بکە!** ژمارەیەک لە نێوان ١-١٠٠ (بە 5 هەڵوەشان بڵێ: exit)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        while True:
            try:
                msg = await self.bot.wait_for("message", timeout=60, check=check)
                if msg.content.lower() == "exit":
                    return await ctx.send(f"👋 واز هێنرا! ژمارەکە **{number}** بوو")
                guess = int(msg.content)
                attempts += 1
                if guess < number:
                    await ctx.send("📈 **بەرزتر!**")
                elif guess > number:
                    await ctx.send("📉 **نزمتر!**")
                else:
                    await ctx.send(f"🎉 **دۆزیویەتی!** ژمارەکە {number} بوو لە {attempts} هەوڵدا!")
                    return
            except ValueError:
                await ctx.send("❌ تەنها ژمارە بنووسە")
            except asyncio.TimeoutError:
                return await ctx.send(f"⏰ کاتی تەواو بوو! ژمارەکە **{number}** بوو")

    @commands.command(name="typingrace", aliases=["typing", "خێرایی_نووسین"])
    async def typingrace(self, ctx):
        """پێشبڕکێی خێرایی نووسین"""
        texts = [
            "پایتۆن زمانێکی بەرنامەسازی ئاسانە",
            "بۆتی دیسکۆرد بە پایتۆن دروست دەکرێت",
            "خێرایی نووسین زۆر گرنگە بۆ پڕۆگرامەران",
            "هەر ڕۆژێک شتێکی نوێ فێربە لە پڕۆگرامسازی",
            "AI و بۆتەکان داهاتووی تەکنۆلۆژیان"
        ]
        text = random.choice(texts)
        await ctx.send(f"⌨️ **پێشبڕکێی نووسین!** ئەم دەقە بنووسە:\n```{text}```")
        await ctx.send("3...", delete_after=1)
        await asyncio.sleep(1)
        await ctx.send("2...", delete_after=1)
        await asyncio.sleep(1)
        await ctx.send("1...", delete_after=1)
        await asyncio.sleep(1)
        await ctx.send("🚀 **دەست پێبکە!**", delete_after=0.5)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30, check=check)
            if msg.content.strip() == text:
                await ctx.send(f"🎉 **ڕاستە!** {ctx.author.mention} بردی!")
            else:
                await ctx.send("❌ **هەڵەیە!** دەقەکە ڕاست نەبوو")
        except asyncio.TimeoutError:
            await ctx.send("⏰ کاتی تەواو بوو!")

    @commands.command(name="quiz", aliases=["trivia", "کویز"])
    async def quiz(self, ctx):
        """پرسیاری زانستی"""
        questions = [
            ("پایتەختی کوردستان چییە؟", ["هەولێر", "سلێمانی", "دهۆک", "کەرکووک"], 0),
            ("پایتۆن لە کام ساڵدا دروستکرا؟", ["1989", "1991", "1995", "2000"], 1),
            ("Discord لە کام ساڵدا بڵاوکرایەوە؟", ["2012", "2015", "2018", "2020"], 1),
            ("ڕووباری زێی گەورە لە کوێ دەڕژێت؟", ["دجله", "فورات", "دەریاچەی ورمێ", "ئاوگانیستان"], 0),
        ]
        q, options, correct = random.choice(questions)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        msg = f"**❓ {q}**\n"
        for i, opt in enumerate(options):
            msg += f"{emojis[i]} {opt}\n"
        embed = discord.Embed(title="🧠 کویز", description=msg, color=0x9b59b6)
        question_msg = await ctx.send(embed=embed)
        for e in emojis[:len(options)]:
            await question_msg.add_reaction(e)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in emojis[:len(options)]

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30, check=check)
            choice = emojis.index(str(reaction.emoji))
            if choice == correct:
                await ctx.send(f"✅ **ڕاستە!** {options[correct]} 🎉")
            else:
                await ctx.send(f"❌ **هەڵەیە!** وەڵامی ڕاست: {options[correct]}")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ کاتی تەواو بوو! وەڵام: {options[correct]}")

    @commands.command(name="hangman", aliases=["هەڵواسین"])
    async def hangman(self, ctx):
        """یاری هەڵواسین"""
        words = ["پایتۆن", "دیسکۆرد", "کۆماند", "بۆت", "سێرڤەر", "چانێل", "ڕۆڵ"]
        word = random.choice(words)
        guessed = []
        tries = 6
        display = " ".join("_" if c not in guessed else c for c in word)
        msg = await ctx.send(f"**🎮 هەڵواسین**\n{display}\n🔤 هەوڵەکان: {tries}")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1

        while tries > 0 and "_" in display:
            try:
                letter_msg = await self.bot.wait_for("message", timeout=30, check=check)
                letter = letter_msg.content
                if letter in guessed:
                    await ctx.send(f"🔁 **{letter}** پێشتر هاتووە!")
                    continue
                guessed.append(letter)
                if letter in word:
                    display = " ".join(c if c in guessed else "_" for c in word)
                    await msg.edit(content=f"**🎮 هەڵواسین**\n{display}\n✅ ڕاست!")
                else:
                    tries -= 1
                    await msg.edit(content=f"**🎮 هەڵواسین**\n{display}\n❌ هەڵە! هەوڵەکان: {tries}")
            except asyncio.TimeoutError:
                return await ctx.send(f"⏰ کاتی تەواو بوو! وشەکە: **{word}**")

        if "_" not in display:
            await ctx.send(f"🎉 **بردی!** وشەکە: {word}")
        else:
            await ctx.send(f"💀 **دۆڕایت!** وشەکە: {word}")


async def setup(bot):
    await bot.add_cog(Games(bot))
