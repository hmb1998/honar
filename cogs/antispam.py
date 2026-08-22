import discord
from discord.ext import commands, tasks
from collections import defaultdict, deque
from datetime import timedelta
import time
import re


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # =====================================================
        # Memory / Tracking
        # =====================================================

        # Messages per user per guild
        self.messages = defaultdict(lambda: deque(maxlen=20))

        # Duplicate messages
        self.last_messages = defaultdict(lambda: deque(maxlen=6))

        # Strikes
        self.strikes = defaultdict(int)

        # Recent joins per guild
        self.joins = defaultdict(lambda: deque(maxlen=100))

        # Active raid mode
        self.raid_mode = {}

        # =====================================================
        # Anti-Spam Settings
        # =====================================================

        self.max_messages = 5
        self.time_window = 5

        self.max_duplicates = 3

        self.max_mentions = 5

        self.max_everyone = 1

        self.timeout_seconds = 60

        self.max_strikes = 3

        # =====================================================
        # Anti-Raid Settings
        # =====================================================

        self.raid_join_limit = 8
        self.raid_time_window = 10

        # How long raid protection stays active
        self.raid_duration = 60

        # =====================================================
        # Link Protection
        # =====================================================

        self.block_links = True

        # Allowed domains
        self.allowed_domains = {
            "discord.com",
            "discord.gg",
            "discordapp.com",
            "github.com",
            "youtu.be",
            "youtube.com",
        }

        self.link_pattern = re.compile(
            r"https?://[^\s]+|www\.[^\s]+",
            re.IGNORECASE
        )

        # Start raid cleanup task
        self.raid_cleanup.start()

    # =========================================================
    # Unload
    # =========================================================

    def cog_unload(self):
        self.raid_cleanup.cancel()

    # =========================================================
    # Permission Check
    # =========================================================

    def is_exempt(self, member: discord.Member):

        perms = member.guild_permissions

        if perms.administrator:
            return True

        if perms.manage_messages:
            return True

        if perms.moderate_members:
            return True

        return False

    # =========================================================
    # User Key
    # =========================================================

    def user_key(self, guild_id, user_id):

        return (guild_id, user_id)

    # =========================================================
    # Domain Whitelist
    # =========================================================

    def is_allowed_domain(self, url):

        try:

            domain = url.lower()

            if "://" in domain:
                domain = domain.split("://", 1)[1]

            domain = domain.split("/", 1)[0]
            domain = domain.split(":", 1)[0]

            if domain.startswith("www."):
                domain = domain[4:]

            for allowed in self.allowed_domains:

                if (
                    domain == allowed
                    or domain.endswith("." + allowed)
                ):
                    return True

            return False

        except Exception:
            return False

    # =========================================================
    # Get Channel For Logs
    # =========================================================

    def get_log_channel(self, guild):

        # Try system channel first
        if guild.system_channel:
            return guild.system_channel

        # Otherwise find a channel where bot can send
        for channel in guild.text_channels:

            permissions = channel.permissions_for(
                guild.me
            )

            if (
                permissions.send_messages
                and permissions.embed_links
            ):
                return channel

        return None

    # =========================================================
    # Punishment
    # =========================================================

    async def punish(self, message, reason):

        if not message.guild:
            return

        member = message.author

        key = self.user_key(
            message.guild.id,
            member.id
        )

        self.strikes[key] += 1

        strikes = self.strikes[key]

        # -----------------------------------------------------
        # Delete message
        # -----------------------------------------------------

        try:

            await message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

        # -----------------------------------------------------
        # Timeout
        # -----------------------------------------------------

        if strikes >= self.max_strikes:

            try:

                await member.timeout(
                    timedelta(
                        seconds=self.timeout_seconds
                    ),
                    reason=f"Anti-Spam: {reason}"
                )

                self.strikes[key] = 0

                text = (
                    f"🔇 {member.mention} "
                    f"بۆ **{self.timeout_seconds} چرکە** "
                    f"timeout کرا.\n"
                    f"📛 هۆکار: **{reason}**"
                )

            except discord.Forbidden:

                text = (
                    f"⚠️ نەتوانرا {member.mention} "
                    f"timeout بکرێت.\n"
                    f"Bot پێویستی بە "
                    f"`Moderate Members` هەیە."
                )

            except discord.HTTPException:

                text = (
                    f"⚠️ timeout ـی "
                    f"{member.mention} سەرکەوتوو نەبوو."
                )

        else:

            text = (
                f"⚠️ {member.mention} "
                f"**Spam قەدەغەیە!**\n"
                f"📛 Strike: "
                f"**{strikes}/{self.max_strikes}**\n"
                f"هۆکار: **{reason}**"
            )

        # -----------------------------------------------------
        # Warning
        # -----------------------------------------------------

        try:

            warning = await message.channel.send(
                text
            )

            await warning.delete(
                delay=5
            )

        except discord.HTTPException:
            pass

    # =========================================================
    # Message Anti-Spam
    # =========================================================

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignore DMs
        if not message.guild:
            return

        # Ignore bots
        if message.author.bot:
            return

        member = message.author

        # Ignore admins/moderators
        if self.is_exempt(member):
            return

        guild_id = message.guild.id
        user_id = member.id

        key = self.user_key(
            guild_id,
            user_id
        )

        now = time.monotonic()

        # =====================================================
        # RAID MODE
        # =====================================================

        raid_expiry = self.raid_mode.get(
            guild_id,
            0
        )

        if raid_expiry > now:

            # During raid mode, normal members cannot spam.
            # Delete suspicious messages immediately.

            content = message.content.strip()

            if content:

                # Allow commands from moderators only.
                if content.startswith(
                    str(self.bot.command_prefix)
                ):
                    return

        # =====================================================
        # 1. Flood
        # =====================================================

        user_messages = self.messages[key]

        user_messages.append(now)

        while (
            user_messages
            and now - user_messages[0]
            > self.time_window
        ):

            user_messages.popleft()

        if len(user_messages) >= self.max_messages:

            await self.punish(
                message,
                "ناردنی نامەی زۆر لە کاتی کەمدا"
            )

            user_messages.clear()

            return

        # =====================================================
        # Content
        # =====================================================

        content = (
            message.content
            .strip()
            .lower()
        )

        # =====================================================
        # 2. Duplicate Spam
        # =====================================================

        if content:

            recent = self.last_messages[key]

            recent.append(content)

            duplicate_count = sum(
                1
                for item in recent
                if item == content
            )

            if (
                duplicate_count
                >= self.max_duplicates
            ):

                await self.punish(
                    message,
                    "دووبارەکردنەوەی هەمان نامە"
                )

                recent.clear()

                return

        # =====================================================
        # 3. Mention Spam
        # =====================================================

        mention_count = (
            len(message.mentions)
            + len(message.role_mentions)
        )

        if (
            mention_count
            >= self.max_mentions
        ):

            await self.punish(
                message,
                "Mention Spam"
            )

            return

        # =====================================================
        # 4. Everyone / Here
        # =====================================================

        if message.mention_everyone:

            await self.punish(
                message,
                "@everyone / @here Spam"
            )

            return

        # =====================================================
        # 5. Link Protection
        # =====================================================

        if (
            self.block_links
            and content
        ):

            links = self.link_pattern.findall(
                content
            )

            blocked_links = [
                link
                for link in links
                if not self.is_allowed_domain(
                    link
                )
            ]

            if blocked_links:

                await self.punish(
                    message,
                    "ناردنی لینکی ڕێگەپێنەدراو"
                )

                return

    # =========================================================
    # Member Join / Anti-Raid
    # =========================================================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        guild = member.guild

        guild_id = guild.id

        now = time.monotonic()

        joins = self.joins[guild_id]

        joins.append(now)

        # Remove old joins
        while (
            joins
            and now - joins[0]
            > self.raid_time_window
        ):

            joins.popleft()

        # =====================================================
        # Raid Detection
        # =====================================================

        if (
            len(joins)
            >= self.raid_join_limit
        ):

            await self.activate_raid(
                guild,
                len(joins)
            )

            # Kick bots that join during raid
            if member.bot:

                try:

                    await member.kick(
                        reason=(
                            "Anti-Raid: "
                            "Bot joined during raid"
                        )
                    )

                except (
                    discord.Forbidden,
                    discord.HTTPException
                ):

                    pass

    # =========================================================
    # Activate Raid Mode
    # =========================================================

    async def activate_raid(
        self,
        guild,
        join_count
    ):

        guild_id = guild.id

        now = time.monotonic()

        already_active = (
            self.raid_mode.get(
                guild_id,
                0
            ) > now
        )

        # Extend raid mode
        self.raid_mode[guild_id] = (
            now + self.raid_duration
        )

        # Don't spam notifications
        if already_active:
            return

        print(
            f"🚨 Anti-Raid activated: "
            f"{guild.name} "
            f"({join_count} joins)"
        )

        channel = self.get_log_channel(
            guild
        )

        if not channel:
            return

        try:

            warning = await channel.send(
                f"🚨 **ANTI-RAID ACTIVATED**\n\n"
                f"👥 Join ـەکان: "
                f"**{join_count}**\n"
                f"⏱️ ماوە: "
                f"**{self.raid_time_window} چرکە**\n"
                f"🔒 Raid Mode: "
                f"**{self.raid_duration} چرکە**\n\n"
                f"🛡️ سیستەمی پاراستن چالاک کرا."
            )

            await warning.delete(
                delay=10
            )

        except discord.HTTPException:
            pass

    # =========================================================
    # Raid Cleanup
    # =========================================================

    @tasks.loop(seconds=5)
    async def raid_cleanup(self):

        now = time.monotonic()

        expired = [
            guild_id
            for guild_id, expiry
            in self.raid_mode.items()
            if expiry <= now
        ]

        for guild_id in expired:

            self.raid_mode.pop(
                guild_id,
                None
            )

            print(
                f"✅ Raid Mode بەسەرچوو "
                f"بۆ guild: {guild_id}"
            )

    @raid_cleanup.before_loop
    async def before_raid_cleanup(self):

        await self.bot.wait_until_ready()

    # =========================================================
    # Raid Status
    # =========================================================

    @commands.command(
        name="raidstatus",
        aliases=[
            "raid",
            "antiraid"
        ]
    )
    @commands.has_permissions(
        administrator=True
    )
    async def raidstatus(self, ctx):

        guild_id = ctx.guild.id

        now = time.monotonic()

        joins = [
            timestamp
            for timestamp
            in self.joins[guild_id]
            if now - timestamp
            <= self.raid_time_window
        ]

        active = (
            self.raid_mode.get(
                guild_id,
                0
            ) > now
        )

        embed = discord.Embed(
            title="🛡️ Anti-Raid Status",
            color=(
                0xe74c3c
                if active
                else 0x2ecc71
            )
        )

        if active:

            remaining = (
                self.raid_mode[guild_id]
                - now
            )

            embed.description = (
                "🚨 **RAID MODE چالاکە**"
            )

            embed.add_field(
                name="⏳ ماوەی ماوە",
                value=(
                    f"{remaining:.0f} چرکە"
                ),
                inline=False
            )

        else:

            embed.description = (
                "✅ هیچ Raid ـێکی "
                "چالاک نییە."
            )

        embed.add_field(
            name="👥 Joins",
            value=str(
                len(joins)
            ),
            inline=True
        )

        embed.add_field(
            name="🚨 Raid Limit",
            value=str(
                self.raid_join_limit
            ),
            inline=True
        )

        embed.add_field(
            name="⏱️ Window",
            value=(
                f"{self.raid_time_window} "
                f"چرکە"
            ),
            inline=True
        )

        await ctx.send(
            embed=embed
        )

    # =========================================================
    # Anti-Spam Status
    # =========================================================

    @commands.command(
        name="antispam",
        aliases=[
            "spamsettings"
        ]
    )
    @commands.has_permissions(
        administrator=True
    )
    async def antispam(self, ctx):

        embed = discord.Embed(
            title="🛡️ Anti-Spam System",
            description=(
                "سیستەمی دژەسپام "
                "چالاکە."
            ),
            color=0x2ecc71
        )

        embed.add_field(
            name="💬 Flood",
            value=(
                f"{self.max_messages} "
                f"نامە / "
                f"{self.time_window} چرکە"
            ),
            inline=False
        )

        embed.add_field(
            name="🔁 Duplicate",
            value=(
                f"{self.max_duplicates} جار"
            ),
            inline=False
        )

        embed.add_field(
            name="📢 Mention",
            value=(
                f"{self.max_mentions} mention"
            ),
            inline=False
        )

        embed.add_field(
            name="📣 Everyone / Here",
            value="چالاکە",
            inline=False
        )

        embed.add_field(
            name="🔗 Link Filter",
            value=(
                "چالاکە + Whitelist"
            ),
            inline=False
        )

        embed.add_field(
            name="🚨 Anti-Raid",
            value=(
                f"{self.raid_join_limit} "
                f"join / "
                f"{self.raid_time_window} "
                f"چرکە"
            ),
            inline=False
        )

        embed.add_field(
            name="🔒 Raid Mode",
            value=(
                f"{self.raid_duration} "
                f"چرکە"
            ),
            inline=False
        )

        embed.add_field(
            name="🔇 Punishment",
            value=(
                f"{self.max_strikes} "
                f"strikes → "
                f"{self.timeout_seconds} "
                f"چرکە timeout"
            ),
            inline=False
        )

        embed.add_field(
            name="✅ Allowed Links",
            value=(
                "Discord • GitHub • YouTube"
            ),
            inline=False
        )

        await ctx.send(
            embed=embed
        )


# =========================================================
# Setup
# =========================================================

async def setup(bot):

    await bot.add_cog(
        AntiSpam(bot)
    )
