import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, PREFIX

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("honar")


# ============================================================
# INTENTS
# ============================================================

INTENTS = discord.Intents.all()


# ============================================================
# COGS
# ============================================================

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


# ============================================================
# BOT
# ============================================================

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=INTENTS,
    help_command=None,
)


# ============================================================
# HMB NEXUS APPLICATION EMOJIS
# ============================================================
#
# These are Application Emojis from the Discord Developer Portal.
# They are fetched from Discord when the bot starts.
#
# Use from any cog:
#
#     self.bot.hmb_emoji(1)
#     self.bot.hmb_emoji(2)
#     ...
#     self.bot.hmb_emoji(10)
#
# Or:
#
#     emoji = self.bot.get_hmb_emoji(1)
#
# ============================================================

HMB_APPLICATION_EMOJI_IDS = {
    1: 1540666353969532978,
    2: 1540665589931057192,
    3: 1540665426676023296,
    4: 1540664002923864157,
    5: 1540663259907231764,
    6: 1540662537077653504,
    7: 1540661704818696262,
    8: 1540660973906698251,
    9: 1540660698873471057,
    10: 1540665960465948496,
}

HMB_EMOJIS: dict[int, discord.Emoji] = {}


async def load_application_emojis():
    """Fetch the 10 HMB NEXUS Application Emojis from Discord."""

    HMB_EMOJIS.clear()

    logger.info("Loading HMB NEXUS Application Emojis...")

    for number, emoji_id in HMB_APPLICATION_EMOJI_IDS.items():
        try:
            emoji = await bot.fetch_application_emoji(emoji_id)

            if emoji:
                HMB_EMOJIS[number] = emoji
                logger.info(
                    "Loaded HMB Emoji %s: %s (%s)",
                    number,
                    emoji.name,
                    emoji.id,
                )

        except discord.NotFound:
            logger.error(
                "HMB Emoji %s was not found. ID=%s",
                number,
                emoji_id,
            )

        except discord.Forbidden:
            logger.error(
                "Discord denied access to HMB Emoji %s. ID=%s",
                number,
                emoji_id,
            )

        except discord.HTTPException as error:
            logger.error(
                "Discord API error loading HMB Emoji %s: %s",
                number,
                error,
            )

        except Exception:
            logger.exception(
                "Unexpected error loading HMB Emoji %s",
                number,
            )

    logger.info(
        "HMB NEXUS Emojis loaded: %s/%s",
        len(HMB_EMOJIS),
        len(HMB_APPLICATION_EMOJI_IDS),
    )


def hmb_emoji(number: int, fallback: str = "❔") -> str:
    """
    Return an HMB Application Emoji as a string.

    Example:
        hmb_emoji(1)
        hmb_emoji(10)

    If an emoji cannot be loaded, the fallback is returned.
    """

    emoji = HMB_EMOJIS.get(number)

    if emoji is None:
        return fallback

    return str(emoji)


def get_hmb_emoji(number: int) -> discord.Emoji | None:
    """Return the actual discord.Emoji object."""

    return HMB_EMOJIS.get(number)


# Make the helpers available to every cog through the bot instance.
bot.hmb_emojis = HMB_EMOJIS
bot.hmb_emoji = hmb_emoji
bot.get_hmb_emoji = get_hmb_emoji


# ============================================================
# LOAD COGS
# ============================================================

async def load_cogs():
    """Load every cog before syncing slash commands."""

    loaded = 0

    for cog in COGS:
        extension = f"cogs.{cog}"

        try:
            await bot.load_extension(extension)
            loaded += 1
            logger.info("Loaded: %s", extension)

        except commands.NoEntryPointError:
            logger.warning(
                "Skipped %s: no setup() entry point.",
                extension,
            )

        except Exception:
            logger.exception(
                "Failed to load %s",
                extension,
            )

    logger.info(
        "Cogs loaded: %s/%s",
        loaded,
        len(COGS),
    )


# ============================================================
# SYNC SLASH COMMANDS
# ============================================================

async def sync_slash_commands():
    """Sync all hybrid/slash commands globally."""

    try:
        synced = await bot.tree.sync()

        logger.info(
            "Global Slash Commands synced: %s",
            len(synced),
        )

    except Exception:
        logger.exception(
            "Failed to sync slash commands.",
        )


# ============================================================
# SETUP HOOK
# ============================================================

async def setup_hook():
    # Application Emojis must be loaded before the cogs
    # so every cog can use bot.hmb_emoji().
    await load_application_emojis()

    await load_cogs()

    await sync_slash_commands()


bot.setup_hook = setup_hook


# ============================================================
# READY
# ============================================================

@bot.event
async def on_ready():
    logger.info(
        "Logged in as %s (%s)",
        bot.user,
        bot.user.id,
    )

    logger.info(
        "Servers: %s | Cogs: %s | HMB Emojis: %s/10",
        len(bot.guilds),
        len(bot.cogs),
        len(HMB_EMOJIS),
    )

    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{PREFIX}help | /help | HMB NEXUS",
        ),
    )


# ============================================================
# RESUMED
# ============================================================

@bot.event
async def on_resumed():
    logger.info("Discord connection resumed.")


# ============================================================
# PREFIX COMMAND ERROR
# ============================================================

@bot.event
async def on_command_error(
    ctx: commands.Context,
    error: commands.CommandError,
):
    if isinstance(error, commands.CommandNotFound):
        return

    messages = {
        commands.MissingPermissions:
            "❌ تۆ ڕێگەپێدانی ئەم کارەت نییە.",
        commands.BotMissingPermissions:
            "❌ بۆت ڕێگەپێدانی ئەم کارەی نییە.",
        commands.MemberNotFound:
            "❌ ئەندام نەدۆزرایەوە.",
        commands.ChannelNotFound:
            "❌ چانێل نەدۆزرایەوە.",
        commands.RoleNotFound:
            "❌ ڕۆڵ نەدۆزرایەوە.",
        commands.BadArgument:
            "❌ زانیارییەکە هەڵەیە.",
    }

    for error_type, message in messages.items():
        if isinstance(error, error_type):
            try:
                await ctx.send(message)
            except discord.HTTPException:
                pass
            return

    if isinstance(error, commands.MissingRequiredArgument):
        try:
            await ctx.send(
                f"❌ ئەرگومێنتێک کەمە. "
                f"`{PREFIX}help` یان `/help` بەکاربهێنە."
            )
        except discord.HTTPException:
            pass
        return

    if isinstance(error, commands.CommandOnCooldown):
        try:
            await ctx.send(
                f"⏳ تکایە **{error.retry_after:.1f}** "
                f"چرکە چاوەڕێ بکە."
            )
        except discord.HTTPException:
            pass
        return

    logger.exception(
        "Unhandled prefix command error",
        exc_info=error,
    )

    try:
        await ctx.send("❌ هەڵەیەکی نەخوازراو ڕوویدا.")
    except discord.HTTPException:
        pass


# ============================================================
# SLASH COMMAND ERROR
# ============================================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: discord.app_commands.AppCommandError,
):
    """Friendly error handler for slash commands."""

    if isinstance(
        error,
        discord.app_commands.MissingPermissions,
    ):
        message = "❌ تۆ ڕێگەپێدانی ئەم کارەت نییە."

    elif isinstance(
        error,
        discord.app_commands.BotMissingPermissions,
    ):
        message = "❌ بۆت ڕێگەپێدانی ئەم کارەی نییە."

    elif isinstance(
        error,
        discord.app_commands.TransformerError,
    ):
        message = "❌ زانیارییەکە هەڵەیە."

    else:
        logger.exception(
            "Unhandled slash command error",
            exc_info=error,
        )
        message = "❌ هەڵەیەکی نەخوازراو ڕوویدا."

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                message,
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                message,
                ephemeral=True,
            )

    except discord.HTTPException:
        pass


# ============================================================
# MAIN
# ============================================================

async def main():
    bot.start_time = datetime.now(timezone.utc)

    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
