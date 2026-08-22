import discord
from discord.ext import commands
import random
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime as dt, timezone


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = Path(__file__).resolve().parent.parent / "data" / "economy_data.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with self.data_file.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError, TypeError):
                return {}
        return {}

    def save_data(self):
        temp_path = self.data_file.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path, self.data_file)

    def get_user(self, user_id):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {
                "balance": 100,
                "bank": 0,
                "xp": 0,
                "level": 1,
                "inventory": [],
                "last_daily": None
            }
        return self.data[user_id]

    @commands.command(name="balance", aliases=["bal", "money", "پارە"])
    async def balance(self, ctx, member: discord.Member = None):
        """پیشاندانی هاوسەنگی ئەندام"""
        if not member:
            member = ctx.author
        user = self.get_user(member.id)
        embed = discord.Embed(
            title=f"💰 هاوسەنگی {member.name}",
            color=0xf1c40f
        )
        embed.add_field(name="🔵 لەبەردەست", value=f"{user['balance']} 💰", inline=True)
        embed.add_field(name="🏦 بانک", value=f"{user['bank']} 💰", inline=True)
        embed.add_field(name="📊 کۆی گشتی", value=f"{user['balance'] + user['bank']} 💰", inline=True)
        embed.add_field(name="📈 ئاست", value=f"Level {user['level']}", inline=True)
        embed.add_field(name="✨ XP", value=f"{user['xp']}/{(user['level'] * 100)}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="daily", aliases=["دیاری_ڕۆژانە"])
    async def daily(self, ctx):
        """وەرگرتنی دیاری ڕۆژانە"""
        user = self.get_user(ctx.author.id)
        today = dt.now(timezone.utc).strftime("%Y-%m-%d")
        if user.get("last_daily") == today:
            return await ctx.send("⏰ **پێشتر دیاری ڕۆژانەت وەرگرتووە!** سبەی بێرەوە")
        amount = random.randint(50, 200)
        user["balance"] += amount
        user["last_daily"] = today
        self.save_data()
        embed = discord.Embed(
            title="🎁 دیاری ڕۆژانە",
            description=f"+{amount} 💰 زیادکرا بۆ هەژمارەکەت!",
            color=0x2ecc71
        )
        await ctx.send(embed=embed)

    @commands.command(name="work", aliases=["کار"])
    async def work(self, ctx):
        """کارکردن و بەدەستهێنانی پارە"""
        jobs = [
            ("پڕۆگرامەر", 150), ("بازرگان", 200), ("پزیشک", 250),
            ("مامۆستا", 100), ("ئەندازیار", 180), ("نووسەر", 120),
            ("شۆفێر", 90), ("فڕۆکەوان", 300), ("ئاهەنەگ", 80)
        ]
        user = self.get_user(ctx.author.id)
        job, salary = random.choice(jobs)
        bonus = random.randint(-20, 50)
        total = max(salary + bonus, 10)
        xp_gain = random.randint(5, 15)
        user["balance"] += total
        user["xp"] += xp_gain
        if user["xp"] >= user["level"] * 100:
            user["level"] += 1
            user["xp"] = 0
            await ctx.send(f"🎉 **{ctx.author.mention} بەرزکرایەوە بۆ ئاست {user['level']}!**")
        self.save_data()
        embed = discord.Embed(
            title="💼 کارکردن",
            description=f"**کار:** {job}\n**داهات:** +{total} 💰\n**XP:** +{random.randint(5, 15)} ✨",
            color=0x3498db
        )
        await ctx.send(embed=embed)

    @commands.command(name="rob", aliases=["steal", "دزیکردن"])
    async def rob(self, ctx, member: discord.Member):
        """دزیکردن لە ئەندامێکی تر"""
        if member == ctx.author:
            return await ctx.send("❌ ناتوانیت لە خۆت بدزیت!")
        user = self.get_user(ctx.author.id)
        target = self.get_user(member.id)
        if target["balance"] < 50:
            return await ctx.send(f"❌ **{member.name}** پارەی بەس نییە بۆ دزی")
        chance = random.randint(1, 100)
        if chance <= 40:
            amount = random.randint(10, target["balance"] // 2)
            target["balance"] -= amount
            user["balance"] += amount
            self.save_data()
            await ctx.send(f"🕵️ **دزی سەرکەوتوو بوو!** +{amount} 💰 لە **{member.name}**")
        else:
            fine = random.randint(20, 100)
            user["balance"] = max(user["balance"] - fine, 0)
            self.save_data()
            await ctx.send(f"🚔 **گیرایت!** -{fine} 💰 جریمە کرایت")

    @commands.command(name="transfer", aliases=["give", "pay", "ناردن"])
    async def transfer(self, ctx, member: discord.Member, amount: int):
        """ناردنی پارە بۆ ئەندامێکی تر"""
        if member == ctx.author:
            return await ctx.send("❌ ناتوانیت پارە بۆ خۆت بنێریت.")
        if member.bot:
            return await ctx.send("❌ ناتوانیت پارە بۆ Bot بنێریت.")
        if amount < 1:
            return await ctx.send("❌ بڕی پارە نادروستە")
        user = self.get_user(ctx.author.id)
        target = self.get_user(member.id)
        if user["balance"] < amount:
            return await ctx.send("❌ پارەی پێویستت نییە!")
        user["balance"] -= amount
        target["balance"] += amount
        self.save_data()
        await ctx.send(f"💸 **{ctx.author.name}** {amount} 💰 نارد بۆ **{member.name}**")

    @commands.command(name="shop", aliases=["store", "فرۆشگا"])
    async def shop(self, ctx):
        """فرۆشگا - کەرینی شتەکان"""
        items = {
            "🎫 تیکیتی لۆتۆ": 100, "🎣 کەپچکی کەپ": 150,
            "🏠 خانوو": 5000, "🚗 ئۆتۆمبێل": 2000,
            "💎 ئەڵماس": 1000, "🎁 سندوقی دیاری": 300,
            "🛡 قەڵغان": 750
        }
        embed = discord.Embed(title="🏪 فرۆشگا", color=0xe67e22)
        for item, price in items.items():
            embed.add_field(name=item, value=f"{price} 💰", inline=True)
        embed.set_footer(text="!buy [ناوی شتەکە] بۆ کڕین")
        await ctx.send(embed=embed)

    @commands.command(name="buy", aliases=["کڕین"])
    async def buy(self, ctx, *, item_name: str):
        """کڕینی شت لە فرۆشگا"""
        items = {
            "تیکیتی لۆتۆ": 100, "کەپچکی کەپ": 150,
            "خانوو": 5000, "ئۆتۆمبێل": 2000,
            "ئەڵماس": 1000, "سندوقی دیاری": 300, "قەڵغان": 750
        }
        found = None
        for name, price in items.items():
            if item_name in name:
                found = (name, price)
                break
        if not found:
            return await ctx.send("❌ ئەو شتە لە فرۆشگا نییە")
        user = self.get_user(ctx.author.id)
        if user["balance"] < found[1]:
            return await ctx.send(f"❌ پارەی پێویستت نییە! {found[1]} 💰 پێویستە")
        user["balance"] -= found[1]
        user["inventory"].append(found[0])
        self.save_data()
        await ctx.send(f"✅ **{found[0]}** کریا! +1 بۆ کۆگات")

    @commands.command(name="inventory", aliases=["inv", "کۆگا"])
    async def inventory(self, ctx):
        """پیشاندانی کۆگا"""
        user = self.get_user(ctx.author.id)
        if not user["inventory"]:
            return await ctx.send("📭 **کۆگات بەتاڵە** - بڕۆ !shop")
        from collections import Counter
        count = Counter(user["inventory"])
        msg = f"**🎒 کۆگای {ctx.author.name}:**\n"
        for item, c in count.most_common():
            msg += f"- {item} x{c}\n"
        await ctx.send(msg[:2000])

    @commands.command(name="leaderboard", aliases=["lb", "top", "ڕیزبەندی"])
    async def leaderboard(self, ctx):
        """ڕیزبەندی دەوڵەمەندترین ئەندامان"""
        sorted_users = sorted(
            self.data.items(),
            key=lambda x: x[1]["balance"] + x[1]["bank"],
            reverse=True
        )[:10]
        if not sorted_users:
            return await ctx.send("📭 هیچ بەکارهێنەرێک نییە")
        msg = "**🏆 ڕیزبەندی دەوڵەمەندترین ئەندامان:**\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, u) in enumerate(sorted_users, 1):
            member = ctx.guild.get_member(int(uid))
            name = member.name if member else "نەناسراو"
            medal = medals[i-1] if i <= 3 else f"{i}."
            total = u["balance"] + u["bank"]
            msg += f"{medal} **{name}** - {total} 💰\n"
        await ctx.send(msg[:2000])


async def setup(bot):
    await bot.add_cog(Economy(bot))
