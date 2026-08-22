import discord
from discord.ext import commands
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cat", aliases=["پشیلە"])
    async def cat(self, ctx):
        """پیشاندانی وێنەی پشیلە"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search") as r:
                if r.status != 200:
                    return await ctx.send("❌ نەتوانرا وێنە وەربگیرێت")
                data = await r.json()
        embed = discord.Embed(title="🐱 پشیلە", color=0xe67e22)
        embed.set_image(url=data[0]["url"])
        await ctx.send(embed=embed)

    @commands.command(name="dog", aliases=["سەگ"])
    async def dog(self, ctx):
        """پیشاندانی وێنەی سەگ"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as r:
                if r.status != 200:
                    return await ctx.send("❌ نەتوانرا وێنە وەربگیرێت")
                data = await r.json()
        embed = discord.Embed(title="🐶 سەگ", color=0x3498db)
        embed.set_image(url=data["message"])
        await ctx.send(embed=embed)

    @commands.command(name="fox", aliases=["ڕێوی"])
    async def fox(self, ctx):
        """پیشاندانی وێنەی ڕێوی"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://randomfox.ca/floof/") as r:
                if r.status != 200:
                    return await ctx.send("❌ نەتوانرا وێنە وەربگیرێت")
                data = await r.json()
        embed = discord.Embed(title="🦊 ڕێوی", color=0xe74c3c)
        embed.set_image(url=data["image"])
        await ctx.send(embed=embed)

    @commands.command(name="wanted", aliases=["داواکراو"])
    async def wanted(self, ctx, member: discord.Member = None):
        """پۆستەری داواکراو بۆ ئەندامێک"""
        if not member:
            member = ctx.author
        async with aiohttp.ClientSession() as session:
            async with session.get(member.display_avatar.url) as r:
                avatar_bytes = await r.read()
        avatar = Image.open(BytesIO(avatar_bytes)).resize((200, 200))
        wanted = Image.new("RGB", (300, 400), (230, 210, 160))
        draw = ImageDraw.Draw(wanted)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
            small_font = ImageFont.truetype("DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
            small_font = font
        wanted.paste(avatar, (50, 50))
        draw.text((150, 20), "داواکراو!", fill=(200, 0, 0), font=font, anchor="mt")
        draw.text((150, 270), member.name, fill=(0, 0, 0), font=small_font, anchor="mt")
        draw.text((150, 300), "ژیاوی دزی", fill=(100, 100, 100), font=small_font, anchor="mt")
        with BytesIO() as buf:
            wanted.save(buf, "PNG")
            buf.seek(0)
            await ctx.send(file=discord.File(buf, "wanted.png"))

    @commands.command(name="memecreate", aliases=["creatememe", "میم_دروستبکە"])
    async def memecreate(self, ctx, *, text: str):
        """دروستکردنی میم بە دەق - !memecreate دەقی سەرەوە | دەقی خوارەوە"""
        if "|" in text:
            top, bottom = text.split("|", 1)
        else:
            top = text
            bottom = ""
        img = Image.new("RGB", (500, 400), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        except:
            font = ImageFont.load_default()
        draw.rectangle([0, 0, 500, 60], fill=(0, 0, 0))
        draw.rectangle([0, 340, 500, 400], fill=(0, 0, 0))
        draw.text((250, 30), top.strip() if top else "", fill=(255, 255, 255), font=font, anchor="mt")
        draw.text((250, 370), bottom.strip() if bottom else "", fill=(255, 255, 255), font=font, anchor="mt")
        with BytesIO() as buf:
            img.save(buf, "PNG")
            buf.seek(0)
            await ctx.send(file=discord.File(buf, "meme.png"))


async def setup(bot):
    await bot.add_cog(Images(bot))
