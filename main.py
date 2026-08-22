import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, PREFIX

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("honar")

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
)


@bot.event
async def on_ready():
    print("\n========================================")
    print(f"✅ {bot.user} ئامادەیە!")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🏠 Servers: {len(bot.guilds)}")
    print(f"🧩 Cogs: {len(bot.cogs)}")
    print("========================================\n")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{PREFIX}help | {len(bot.cogs)} کۆگ",
        )
    )


@bot.event
async def on_resumed():
    logger.info("🔄 Discord connection resumed.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send("❌ تۆ ڕێگەپێدانی ئەم کارەت نییە.")
    if isinstance(error, commands.BotMissingPermissions):
        return await ctx.send("❌ بۆت ڕێگەپێدانی ئەم کارەی نییە.")
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f"❌ ئەرگومێنتێک کەمە. `{PREFIX}help` بەکاربهێنە.")
    if isinstance(error, commands.MemberNotFound):
        return await ctx.send("❌ ئەندام نەدۆزرایەوە.")
    if isinstance(error, commands.ChannelNotFound):
        return await ctx.send("❌ چانێل نەدۆزرایەوە.")
    if isinstance(error, commands.RoleNotFound):
        return await ctx.send("❌ ڕۆڵ نەدۆزرایەوە.")
    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(f"⏳ تکایە **{error.retry_after:.1f}** چرکە چاوەڕێ بکە.")
    if isinstance(error, commands.BadArgument):
        return await ctx.send("❌ زانیارییەکە هەڵەیە.")

    logger.error("Command error", exc_info=error)
    try:
        await ctx.send("❌ هەڵەیەکی نەخوازراو ڕوویدا.")
    except discord.HTTPException:
        pass


async def load_cogs():
    cogs = [
        "admin", "moderation", "antispam", "fun", "utility",
        "info", "economy", "games", "images", "music", "github",
    ]
    loaded = 0
    for cog in cogs:
        try:
            await bot.load_extension(f"cogs.{cog}")
            loaded += 1
            logger.info("✅ %s بارکرا", cog)
        except Exception:
            logger.exception("❌ %s بارنەکرا", cog)

    logger.info("🧩 کۆی Cogs ـی بارکراو: %s/%s", loaded, len(cogs))


async def main():
    bot.start_time = datetime.now(timezone.utc)
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot وەستا.")
