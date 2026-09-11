import asyncio
import logging
from datetime import datetime, timezone

import discord
import aiohttp
from discord.ext import commands

from config import (
    DISCORD_TOKEN,
    PREFIX,
    HMB_APPLICATION_ID,
    HMB_PRESENCE_NAME,
    HMB_PRESENCE_STATE,
)


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
    "music_panel",
    "github",
    "hmb",
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
# Application Emojis from:
# Discord Developer Portal
#
# Total: 10
#
# Usage from any cog:
#
#     self.bot.hmb_emoji(1)
#     self.bot.hmb_emoji(2)
#     ...
#     self.bot.hmb_emoji(10)
#
# Or:
#
#     self.bot.get_hmb_emoji(1)
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

    # FIXED EMOJI #10
    10: 1540659590645948496,
}


# ============================================================
# EMOJI STORAGE
# ============================================================

HMB_EMOJIS: dict[int, discord.Emoji] = {}


# ============================================================
# LOAD APPLICATION EMOJIS
# ============================================================

async def load_application_emojis():
    """
    Fetch all HMB NEXUS Application Emojis from Discord.
    """

    HMB_EMOJIS.clear()

    logger.info(
        "Loading HMB NEXUS Application Emojis..."
    )

    total = len(HMB_APPLICATION_EMOJI_IDS)

    for number, emoji_id in HMB_APPLICATION_EMOJI_IDS.items():

        try:
            emoji = await bot.fetch_application_emoji(
                emoji_id
            )

            if emoji is not None:

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
        total,
    )


# ============================================================
# HMB EMOJI HELPER
# ============================================================

def hmb_emoji(
    number: int,
    fallback: str = "❔",
) -> str:
    """
    Return an HMB Application Emoji as a string.

    Examples:

        hmb_emoji(1)
        hmb_emoji(5)
        hmb_emoji(10)

    If the emoji is unavailable,
    the fallback emoji will be returned.
    """

    emoji = HMB_EMOJIS.get(number)

    if emoji is None:
        return fallback

    return str(emoji)


# ============================================================
# GET HMB EMOJI OBJECT
# ============================================================

def get_hmb_emoji(
    number: int,
) -> discord.Emoji | None:
    """
    Return the actual Discord Emoji object.
    """

    return HMB_EMOJIS.get(number)



# ============================================================
# HMB SERVER CUSTOM EMOJI SYNC
# ============================================================
#
# Application Emojis are NOT shown in Discord's normal server
# emoji picker. This sync copies the 10 Application Emojis into
# a target Discord server as normal Custom Emojis.
#
# Railway variable (recommended):
#
#   HMB_EMOJI_GUILD_ID=YOUR_SERVER_ID
#
# If it is empty and the bot is in exactly one server, that
# server is used automatically.
# ============================================================

HMB_SERVER_EMOJI_NAMES = {
    1: "hmb_01",
    2: "hmb_02",
    3: "hmb_03",
    4: "hmb_04",
    5: "hmb_05",
    6: "hmb_06",
    7: "hmb_07",
    8: "hmb_08",
    9: "hmb_09",
    10: "hmb_10",
}


def get_hmb_emoji_guilds() -> list[discord.Guild]:
    """Return every server where the bot is currently installed.

    HMB NEXUS server emojis are synchronized to ALL guilds the bot
    can see. This means no HMB_EMOJI_GUILD_ID is required.
    """
    return list(bot.guilds)


async def sync_hmb_server_emojis(
    guild: discord.Guild | None = None,
) -> tuple[int, int, int]:
    """
    Copy the 10 HMB Application Emojis into a server as Custom Emojis.

    Returns:
        (created, already_exists, failed)
    """
    if guild is None:
        guilds = get_hmb_emoji_guilds()
        if not guilds:
            logger.warning(
                "HMB server emoji sync skipped: set HMB_EMOJI_GUILD_ID "
                "when the bot is in multiple servers."
            )
            return (0, 0, 0)
        guild = guilds[0]

    me = guild.me
    if me is None:
        try:
            me = await guild.fetch_member(bot.user.id)
        except discord.HTTPException:
            me = None

    if me is None or not me.guild_permissions.manage_emojis_and_stickers:
        logger.error(
            "Cannot sync HMB server emojis in %s: "
            "bot needs Manage Expressions permission.",
            guild.name,
        )
        return (0, 0, 10)

    created = 0
    already_exists = 0
    failed = 0

    logger.info(
        "Syncing HMB server emojis to: %s (%s)",
        guild.name,
        guild.id,
    )

    for number in range(1, 11):
        app_emoji = HMB_EMOJIS.get(number)
        if app_emoji is None:
            failed += 1
            logger.error(
                "HMB server emoji %s skipped: application emoji not loaded.",
                number,
            )
            continue

        name = HMB_SERVER_EMOJI_NAMES[number]

        existing = discord.utils.get(guild.emojis, name=name)
        if existing is not None:
            already_exists += 1
            logger.info(
                "HMB Server Emoji %s already exists: %s (%s)",
                number,
                existing.name,
                existing.id,
            )
            continue

        try:
            # In discord.py 2.7.x, ApplicationEmoji.url is a plain URL string,
            # not an Asset object. Download the image explicitly before creating
            # the server custom emoji.
            image_url = str(app_emoji.url)

            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    image_url,
                    headers={"User-Agent": "HMB-NEXUS/1.0"},
                ) as response:
                    if response.status != 200:
                        body = await response.text()
                        raise RuntimeError(
                            f"Emoji image download failed: HTTP {response.status} {body[:200]}"
                        )
                    image_bytes = await response.read()

            if not image_bytes:
                raise RuntimeError("Emoji image download returned empty data")

            await guild.create_custom_emoji(
                name=name,
                image=image_bytes,
                reason="HMB NEXUS Application Emoji sync",
            )

            created += 1
            logger.info(
                "Created HMB Server Emoji %s: %s",
                number,
                name,
            )

        except discord.Forbidden:
            failed += 1
            logger.error(
                "Discord denied creation of HMB Server Emoji %s in %s. "
                "Check Manage Expressions permission.",
                number,
                guild.name,
            )

        except discord.HTTPException as error:
            failed += 1
            logger.error(
                "Discord API error creating HMB Server Emoji %s: %s",
                number,
                error,
            )

        except Exception:
            failed += 1
            logger.exception(
                "Unexpected error creating HMB Server Emoji %s",
                number,
            )

    logger.info(
        "HMB Server Emoji sync finished: created=%s | existing=%s | failed=%s",
        created,
        already_exists,
        failed,
    )

    return created, already_exists, failed


async def auto_sync_hmb_server_emojis():
    """Synchronize all 10 HMB emojis to EVERY server containing the bot."""
    guilds = get_hmb_emoji_guilds()

    if not guilds:
        logger.info("HMB Server Emoji auto-sync: bot is not in any server yet.")
        return

    logger.info(
        "Starting HMB Server Emoji auto-sync for %s server(s)...",
        len(guilds),
    )

    total_created = 0
    total_existing = 0
    total_failed = 0

    for index, guild in enumerate(guilds, start=1):
        try:
            created, existing, failed = await sync_hmb_server_emojis(guild)
            total_created += created
            total_existing += existing
            total_failed += failed

            logger.info(
                "HMB Emoji sync [%s/%s] %s (%s): created=%s | existing=%s | failed=%s",
                index,
                len(guilds),
                guild.name,
                guild.id,
                created,
                existing,
                failed,
            )

        except Exception:
            logger.exception(
                "HMB Server Emoji auto-sync failed for %s (%s).",
                guild.name,
                guild.id,
            )
            total_failed += 10

        # Small pause between guilds to be friendly to Discord rate limits.
        if index < len(guilds):
            await asyncio.sleep(1)

    logger.info(
        "HMB Server Emoji ALL-SERVER sync finished: servers=%s | created=%s | existing=%s | failed=%s",
        len(guilds),
        total_created,
        total_existing,
        total_failed,
    )


# ============================================================
# MAKE EMOJIS AVAILABLE TO ALL COGS
# ============================================================

bot.hmb_emojis = HMB_EMOJIS
bot.hmb_emoji = hmb_emoji
bot.get_hmb_emoji = get_hmb_emoji
bot.sync_hmb_server_emojis = sync_hmb_server_emojis


# ============================================================
# LOAD COGS
# ============================================================

async def load_cogs():
    """
    Load every cog before syncing slash commands.
    """

    loaded = 0

    for cog in COGS:

        extension = f"cogs.{cog}"

        try:

            await bot.load_extension(
                extension
            )

            loaded += 1

            logger.info(
                "Loaded: %s",
                extension,
            )

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

_slash_sync_lock = asyncio.Lock()
_slash_commands_synced = False


async def sync_slash_commands():
    """
    Sync all slash commands globally without blocking bot startup.
    Global command sync can take a little while, so it is NOT run
    inside setup_hook().
    """

    global _slash_commands_synced

    if _slash_commands_synced:
        return

    async with _slash_sync_lock:
        if _slash_commands_synced:
            return

        logger.info("Starting global Slash Command sync...")

        try:
            # Prevent a slow Discord API request from making the
            # Railway container appear frozen forever.
            synced = await asyncio.wait_for(
                bot.tree.sync(),
                timeout=90,
            )

            _slash_commands_synced = True

            logger.info(
                "Global Slash Commands synced: %s",
                len(synced),
            )

        except asyncio.TimeoutError:
            logger.error(
                "Global Slash Command sync timed out after 90 seconds. "
                "Bot remains online; sync will retry after reconnect."
            )

        except Exception:
            logger.exception(
                "Failed to sync slash commands."
            )


# ============================================================
# SETUP HOOK
# ============================================================

async def setup_hook():
    """
    Load emojis and cogs before Gateway login.
    Slash-command sync is intentionally started after on_ready().
    """

    await load_application_emojis()
    await load_cogs()


bot.setup_hook = setup_hook


# ============================================================
# HMB NEXUS BOT PRESENCE
# ============================================================
#
# IMPORTANT:
# Discord currently restricts BOT users to sending only:
#   - name
#   - state
#   - type
#   - url
#
# Therefore the Rich Presence Art Assets uploaded in:
#   Developer Portal -> Activities -> Art Assets
# cannot be attached to a BOT presence through the normal
# Discord Gateway. The uploaded Cover Image / Assets remain
# configured in the Developer Portal and can be used by
# supported Activity/SDK integrations.
#
# This function uses the fields that Discord allows for bots.
# ============================================================

async def update_hmb_presence():
    """Set the HMB NEXUS presence using fields allowed for bot users."""

    try:
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name=HMB_PRESENCE_NAME,
            state=HMB_PRESENCE_STATE,
        )

        await bot.change_presence(
            status=discord.Status.online,
            activity=activity,
        )

        logger.info(
            "HMB NEXUS presence enabled: Playing %s | %s",
            HMB_PRESENCE_NAME,
            HMB_PRESENCE_STATE,
        )

    except discord.HTTPException:
        logger.exception("Failed to update HMB NEXUS presence.")
    except Exception:
        logger.exception("Unexpected error updating HMB NEXUS presence.")


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

    # Set the bot presence immediately after Gateway login.
    await update_hmb_presence()

    # Copy Application Emojis into normal Server Custom Emojis so
    # they appear in Discord's emoji picker.
    await auto_sync_hmb_server_emojis()

    # Sync Slash Commands in the background so a slow global
    # Discord API request can never block the bot from becoming ready.
    if not _slash_commands_synced:
        asyncio.create_task(sync_slash_commands())


# ============================================================
# RESUMED
# ============================================================

@bot.event
async def on_resumed():

    logger.info(
        "Discord connection resumed."
    )


# ============================================================
# PREFIX COMMAND ERROR
# ============================================================

@bot.event
async def on_command_error(
    ctx: commands.Context,
    error: commands.CommandError,
):

    if isinstance(
        error,
        commands.CommandNotFound,
    ):
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

        if isinstance(
            error,
            error_type,
        ):

            try:

                await ctx.send(
                    message
                )

            except discord.HTTPException:
                pass

            return

    # --------------------------------------------------------
    # Missing Required Argument
    # --------------------------------------------------------

    if isinstance(
        error,
        commands.MissingRequiredArgument,
    ):

        try:

            await ctx.send(
                f"❌ ئەرگومێنتێک کەمە. "
                f"`{PREFIX}help` یان `/help` بەکاربهێنە."
            )

        except discord.HTTPException:
            pass

        return

    # --------------------------------------------------------
    # Cooldown
    # --------------------------------------------------------

    if isinstance(
        error,
        commands.CommandOnCooldown,
    ):

        try:

            await ctx.send(
                f"⏳ تکایە **{error.retry_after:.1f}** "
                f"چرکە چاوەڕێ بکە."
            )

        except discord.HTTPException:
            pass

        return

    # --------------------------------------------------------
    # Unknown Error
    # --------------------------------------------------------

    logger.exception(
        "Unhandled prefix command error",
        exc_info=error,
    )

    try:

        await ctx.send(
            "❌ هەڵەیەکی نەخوازراو ڕوویدا."
        )

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
    """
    Friendly error handler for slash commands.
    """

    if isinstance(
        error,
        discord.app_commands.MissingPermissions,
    ):

        message = (
            "❌ تۆ ڕێگەپێدانی ئەم کارەت نییە."
        )

    elif isinstance(
        error,
        discord.app_commands.BotMissingPermissions,
    ):

        message = (
            "❌ بۆت ڕێگەپێدانی ئەم کارەی نییە."
        )

    elif isinstance(
        error,
        discord.app_commands.TransformerError,
    ):

        message = (
            "❌ زانیارییەکە هەڵەیە."
        )

    else:

        logger.exception(
            "Unhandled slash command error",
            exc_info=error,
        )

        message = (
            "❌ هەڵەیەکی نەخوازراو ڕوویدا."
        )

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

    bot.start_time = datetime.now(
        timezone.utc
    )

    async with bot:

        await bot.start(
            DISCORD_TOKEN
        )


# ============================================================
# START BOT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot stopped."
        )
