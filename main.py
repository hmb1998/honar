import discord
from discord.ext import commands
import asyncio
import logging
from config import DISCORD_TOKEN, PREFIX

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


@bot.event
async def on_ready():
    print(f"✅ {bot.user} ئامادەیە!")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{PREFIX}help | {len(bot.cogs)} کۆگ"
        )
    )


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ تۆ ڕێگەپێدانی ئەم کارەت نییە")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ ئەرگومێنتێک کەمە. بەکاربێنە: `{PREFIX}help`")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ بۆت ڕێگەپێدانی ئەم کارەی نییە")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ ئەندام نەدۆزرایەوە")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ هەڵە: {error}")


async def load_cogs():
    cogs_list = [
        "admin", "moderation", "fun", "utility",
        "info", "economy", "games", "images", "music", "github"
    ]
    for cog in cogs_list:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ {cog} بارکرا")
        except Exception as e:
            print(f"❌ {cog} بارنەکرا: {e}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
