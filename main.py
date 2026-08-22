import discord
from discord.ext import commands
import asyncio
import logging

from config import DISCORD_TOKEN, PREFIX


# =========================================================
# Logging
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("honar")


# =========================================================
# Bot Settings
# =========================================================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None
)


# =========================================================
# Bot Ready
# =========================================================

@bot.event
async def on_ready():

    print("")
    print("========================================")
    print(f"✅ {bot.user} ئامادەیە!")
    print(f"🆔 ID: {bot.user.id}")
    print(f"🏠 Servers: {len(bot.guilds)}")
    print(f"🧩 Cogs: {len(bot.cogs)}")
    print("========================================")
    print("")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{PREFIX}help | {len(bot.cogs)} کۆگ"
        )
    )


# =========================================================
# Disconnect / Resume
# =========================================================

@bot.event
async def on_resumed():

    logger.info("🔄 Discord connection resumed.")


# =========================================================
# Command Error Handler
# =========================================================

@bot.event
async def on_command_error(ctx, error):

    # Ignore errors already handled by commands
    if hasattr(ctx.command, "on_error"):
        return

    # Missing permissions
    if isinstance(
        error,
        commands.MissingPermissions
    ):

        await ctx.send(
            "❌ تۆ ڕێگەپێدانی ئەم کارەت نییە."
        )

    # Bot permissions
    elif isinstance(
        error,
        commands.BotMissingPermissions
    ):

        await ctx.send(
            "❌ بۆت ڕێگەپێدانی ئەم کارەی نییە."
        )

    # Missing argument
    elif isinstance(
        error,
        commands.MissingRequiredArgument
    ):

        await ctx.send(
            f"❌ ئەرگومێنتێک کەمە.\n"
            f"بەکاربێنە: `{PREFIX}help`"
        )

    # Member not found
    elif isinstance(
        error,
        commands.MemberNotFound
    ):

        await ctx.send(
            "❌ ئەندام نەدۆزرایەوە."
        )

    # Command not found
    elif isinstance(
        error,
        commands.CommandNotFound
    ):

        return

    # Cooldown
    elif isinstance(
        error,
        commands.CommandOnCooldown
    ):

        await ctx.send(
            f"⏳ تکایە **{error.retry_after:.1f}** "
            f"چرکە چاوەڕێ بکە."
        )

    # Bad argument
    elif isinstance(
        error,
        commands.BadArgument
    ):

        await ctx.send(
            "❌ زانیارییەکە هەڵەیە."
        )

    # Check failure
    elif isinstance(
        error,
        commands.CheckFailure
    ):

        await ctx.send(
            "❌ تۆ ڕێگەپێدانی ئەم فرمانەت نییە."
        )

    # Other errors
    else:

        logger.error(
            "Command error",
            exc_info=error
        )

        try:

            await ctx.send(
                f"❌ هەڵەیەک ڕوویدا:\n"
                f"`{error}`"
            )

        except discord.HTTPException:

            pass


# =========================================================
# Load Cogs
# =========================================================

async def load_cogs():

    cogs_list = [

        # Moderation
        "admin",
        "moderation",

        # Protection
        "antispam",

        # Fun
        "fun",

        # Utility
        "utility",

        # Information
        "info",

        # Economy
        "economy",

        # Games
        "games",

        # Images
        "images",

        # Music
        "music",

        # GitHub
        "github"
    ]

    print("")
    print("🔄 دەست بە Load کردنی Cogs دەکات...")
    print("")

    loaded = 0
    failed = 0

    for cog in cogs_list:

        try:

            await bot.load_extension(
                f"cogs.{cog}"
            )

            loaded += 1

            print(
                f"✅ {cog} بارکرا"
            )

        except Exception as e:

            failed += 1

            print(
                f"❌ {cog} بارنەکرا: {e}"
            )

            logger.exception(
                f"Failed to load cog: {cog}"
            )

    print("")
    print("========================================")
    print(
        f"✅ Loaded: {loaded}"
    )
    print(
        f"❌ Failed: {failed}"
    )
    print(
        f"🧩 Total active Cogs: {len(bot.cogs)}"
    )
    print("========================================")
    print("")


# =========================================================
# Main
# =========================================================

async def main():

    async with bot:

        # Load all Cogs
        await load_cogs()

        # Start Discord Bot
        await bot.start(
            DISCORD_TOKEN
        )


# =========================================================
# Start Bot
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print("")
        print("🛑 Bot بە دەستی بەکارهێنەر وەستا.")

    except Exception as e:

        print("")
        print(
            f"❌ Bot بە هەڵە وەستا: {e}"
        )

        logger.exception(
            "Fatal bot error"
        )
