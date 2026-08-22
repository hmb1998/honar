import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, PREFIX

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("honar")

INTENTS = discord.Intents.all()

COGS = (
    "admin",
    "moderation",
    "antispam",
    "fun",
    "utility",
    "info",
    "economy",
    "games",
    "images",
    "music",
    "github",
)

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=INTENTS,
    help_command=None,
)


@bot.event
async def on_ready():
    logger.info("Logged in as %s (%s)", bot.user, bot.user.id)
    logger.info("Servers: %s | Cogs: %s", len(bot.guilds), len(bot.cogs))

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{PREFIX}help | {len(bot.cogs)} cogs",
        ),
    )


@bot.event
async def on_resumed():
    logger.info("Discord connection resumed.")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return

    messages = {
        commands.MissingPermissions: "❌ تۆ ڕێگەپێدانی ئەم کارەت نییە.",
        commands.BotMissingPermissions: "❌ بۆت ڕێگەپێدانی ئەم کارەی نییە.",
        commands.MemberNotFound: "❌ ئەندام نەدۆزرایەوە.",
        commands.ChannelNotFound: "❌ چانێل نەدۆزرایەوە.",
        commands.RoleNotFound: "❌ ڕۆڵ نەدۆزرایەوە.",
        commands.BadArgument: "❌ زانیارییەکە هەڵەیە.",
    }

    for error_type, message in messages.items():
        if isinstance(error, error_type):
            await ctx.send(message)
            return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ ئەرگومێنتێک کەمە. `{PREFIX}help` بەکاربهێنە.")
        return

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"⏳ تکایە **{error.retry_after:.1f}** چرکە چاوەڕێ بکە."
        )
        return

    logger.exception("Unhandled command error", exc_info=error)
    try:
        await ctx.send("❌ هەڵەیەکی نەخوازراو ڕوویدا.")
    except discord.HTTPException:
        pass


async def load_cogs():
    loaded = 0

    for cog in COGS:
        extension = f"cogs.{cog}"
        try:
            await bot.load_extension(extension)
            loaded += 1
            logger.info("Loaded: %s", extension)
        except commands.NoEntryPointError:
            # Empty/placeholder cogs can exist without a setup() function.
            logger.warning("Skipped %s: no setup() entry point.", extension)
        except Exception:
            logger.exception("Failed to load %s", extension)

    logger.info("Cogs loaded: %s/%s", loaded, len(COGS))


async def main():
    bot.start_time = datetime.now(timezone.utc)

    async with bot:
        await load_cogs()

        if not bot.cogs:
            raise RuntimeError(
                "No cogs were loaded. Check the cogs directory and dependencies."
            )

        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
