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
        # MEMORY / TRACKING
        # =====================================================

        # Messages per guild/user
        self.messages = defaultdict(
            lambda: deque(maxlen=20)
        )

        # Duplicate messages
        self.last_messages = defaultdict(
            lambda: deque(maxlen=6)
        )

        # Strikes
        self.strikes = defaultdict(int)

        # Recent joins
        self.joins = defaultdict(
            lambda: deque(maxlen=100)
        )

        # Active raid mode
        # guild_id -> expiry timestamp
        self.raid_mode = {}

        # Channels locked by Anti-Raid
        # guild_id -> {
        #     channel_id: original_send_messages_value
        # }
        self.locked_channels = defaultdict(dict)

        # Prevent repeated raid messages
        self.raid_notifications = {}

        # =====================================================
        # ANTI-SPAM SETTINGS
        # =====================================================

        self.max_messages = 5
        self.time_window = 5

        self.max_duplicates = 3

        self.max_mentions = 5

        self.max_everyone = 1

        self.timeout_seconds = 60

        self.max_strikes = 3

        # =====================================================
        # ANTI-RAID SETTINGS
        # =====================================================

        self.raid_join_limit = 8

        self.raid_time_window = 10

        # How long lockdown remains active
        self.raid_duration = 60

        # Kick bots that join during active raid
        self.kick_bots_during_raid = True

        # =====================================================
        # LINK PROTECTION
        # =====================================================

        self.block_links = True

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

        # =====================================================
        # START CLEANUP TASK
        # =====================================================

        self.raid_cleanup.start()

    # =========================================================
    # UNLOAD
    # =========================================================

    def cog_unload(self):

        self.raid_cleanup.cancel()

    # =========================================================
    # USER KEY
    # =========================================================

    def user_key(
        self,
        guild_id: int,
        user_id: int
    ):
        return guild_id, user_id

    # =========================================================
    # EXEMPT MEMBERS
    # =========================================================

    def is_exempt(
        self,
        member: discord.Member
    ):

        perms = member.guild_permissions

        if perms.administrator:
            return True

        if perms.manage_messages:
            return True

        if perms.moderate_members:
            return True

        return False

    # =========================================================
    # ALLOWED DOMAIN
    # =========================================================

    def is_allowed_domain(
        self,
        url: str
    ):

        try:

            domain = url.lower().strip()

            if "://" in domain:
                domain = domain.split(
                    "://",
                    1
                )[1]

            domain = domain.split(
                "/",
                1
            )[0]

            domain = domain.split(
                ":",
                1
            )[0]

            if domain.startswith("www."):
                domain = domain[4:]

            for allowed in self.allowed_domains:

                if (
                    domain == allowed
                    or domain.endswith(
                        "." + allowed
                    )
                ):
                    return True

            return False

        except Exception:

            return False

    # =========================================================
    # LOG CHANNEL
    # =========================================================

    def get_log_channel(
        self,
        guild: discord.Guild
    ):

        if guild.system_channel:

            permissions = (
                guild.system_channel.permissions_for(
                    guild.me
                )
            )

            if permissions.send_messages:
                return guild.system_channel

        for channel in guild.text_channels:

            permissions = channel.permissions_for(
                guild.me
            )

            if permissions.send_messages:

                return channel

        return None

    # =========================================================
    # PUNISH
    # =========================================================

    async def punish(
        self,
        message: discord.Message,
        reason: str
    ):

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
        # DELETE MESSAGE
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
        # TIMEOUT AFTER STRIKES
        # -----------------------------------------------------

        if strikes >= self.max_strikes:

            try:

                await member.timeout(
                    timedelta(
                        seconds=self.timeout_seconds
                    ),
                    reason=(
                        f"Anti-Spam: {reason}"
                    )
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
                    f"⚠️ نەتوانرا "
                    f"{member.mention} timeout بکرێت.\n"
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
                f"📛 هۆکار: **{reason}**"
            )

        # -----------------------------------------------------
        # WARNING
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
    # MESSAGE EVENT
    # =========================================================

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):

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
        # RAID LOCKDOWN
        # =====================================================

        raid_expiry = self.raid_mode.get(
            guild_id,
            0
        )

        if raid_expiry > now:

            # During lockdown, normal members
            # cannot send messages.

            try:

                await message.delete()

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):

                pass

            return

        # =====================================================
        # FLOOD SPAM
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
        # MESSAGE CONTENT
        # =====================================================

        content = (
            message.content
            .strip()
            .lower()
        )

        # =====================================================
        # DUPLICATE SPAM
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
        # MENTION SPAM
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
        # EVERYONE / HERE
        # =====================================================

        if message.mention_everyone:

            await self.punish(
                message,
                "@everyone / @here Spam"
            )

            return

        # =====================================================
        # LINK FILTER
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
    # MEMBER JOIN
    # =========================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):

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
        # ALREADY RAID MODE
        # =====================================================

        if (
            self.raid_mode.get(
                guild_id,
                0
            ) > now
        ):

            if (
                member.bot
                and self.kick_bots_during_raid
            ):

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

            return

        # =====================================================
        # RAID DETECTION
        # =====================================================

        if (
            len(joins)
            >= self.raid_join_limit
        ):

            await self.activate_raid(
                guild,
                len(joins)
            )

            # Kick the bot that triggered raid
            if (
                member.bot
                and self.kick_bots_during_raid
            ):

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
    # RAID LOCKDOWN
    # =========================================================

    async def lock_channels(
        self,
        guild: discord.Guild
    ):

        me = guild.me

        if not me:
            return

        for channel in guild.text_channels:

            try:

                permissions = channel.permissions_for(
                    me
                )

                if not permissions.manage_roles:
                    # Bot still needs permission
                    # to edit channel overwrites.
                    continue

                overwrite = channel.overwrites_for(
                    guild.default_role
                )

                # Save original permission only once
                if (
                    channel.id
                    not in self.locked_channels[
                        guild.id
                    ]
                ):

                    self.locked_channels[
                        guild.id
                    ][channel.id] = (
                        overwrite.send_messages
                    )

                # Lock @everyone
                overwrite.send_messages = False

                await channel.set_permissions(
                    guild.default_role,
                    overwrite=overwrite,
                    reason=(
                        "Anti-Raid Lockdown"
                    )
                )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):

                continue

    # =========================================================
    # RESTORE CHANNELS
    # =========================================================

    async def unlock_channels(
        self,
        guild: discord.Guild
    ):

        saved = self.locked_channels.get(
            guild.id,
            {}
        )

        for channel_id, old_value in list(
            saved.items()
        ):

            channel = guild.get_channel(
                channel_id
            )

            if not channel:
                continue

            try:

                overwrite = channel.overwrites_for(
                    guild.default_role
                )

                # Restore original value
                overwrite.send_messages = (
                    old_value
                )

                await channel.set_permissions(
                    guild.default_role,
                    overwrite=overwrite,
                    reason=(
                        "Anti-Raid Lockdown Ended"
                    )
                )

            except (
                discord.Forbidden,
                discord.HTTPException
            ):

                continue

        self.locked_channels.pop(
            guild.id,
            None
        )

    # =========================================================
    # ACTIVATE RAID
    # =========================================================

    async def activate_raid(
        self,
        guild: discord.Guild,
        join_count: int
    ):

        guild_id = guild.id

        now = time.monotonic()

        already_active = (
            self.raid_mode.get(
                guild_id,
                0
            ) > now
        )

        # Extend raid protection
        self.raid_mode[guild_id] = (
            now + self.raid_duration
        )

        # Lock channels
        await self.lock_channels(
            guild
        )

        # Don't send notification repeatedly
        if already_active:
            return

        self.raid_notifications[
            guild_id
        ] = now

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

            embed = discord.Embed(
                title="🚨 ANTI-RAID ACTIVATED",
                description=(
                    "🔒 **Raid Lockdown چالاک کرا.**\n\n"
                    "نامەکانی ئەندامانی ئاسایی "
                    "کاتییەوە داخراون."
                ),
                color=0xe74c3c
            )

            embed.add_field(
                name="👥 Joins",
                value=str(
                    join_count
                ),
                inline=True
            )

            embed.add_field(
                name="⏱️ Detection",
                value=(
                    f"{self.raid_time_window} "
                    f"چرکە"
                ),
                inline=True
            )

            embed.add_field(
                name="🔒 Lockdown",
                value=(
                    f"{self.raid_duration} "
                    f"چرکە"
                ),
                inline=True
            )

            warning = await channel.send(
                embed=embed
            )

            await warning.delete(
                delay=10
            )

        except discord.HTTPException:

            pass

    # =========================================================
    # RAID CLEANUP / AUTO UNLOCK
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

            guild = self.bot.get_guild(
                guild_id
            )

            self.raid_mode.pop(
                guild_id,
                None
            )

            if guild:

                await self.unlock_channels(
                    guild
                )

                channel = self.get_log_channel(
                    guild
                )

                if channel:

                    try:

                        message = await channel.send(
                            "🔓 **Raid Lockdown کۆتایی هات.**\n"
                            "✅ Channel ـەکان گەڕانەوە بۆ دۆخی پێشوو."
                        )

                        await message.delete(
                            delay=8
                        )

                    except discord.HTTPException:

                        pass

                print(
                    f"🔓 Raid Mode ended: "
                    f"{guild.name}"
                )

    @raid_cleanup.before_loop
    async def before_raid_cleanup(self):

        await self.bot.wait_until_ready()

    # =========================================================
    # MANUAL RAID LOCK
    # =========================================================

    @commands.command(
        name="raidlock"
    )
    @commands.has_permissions(
        administrator=True
    )
    async def raidlock(
        self,
        ctx
    ):

        guild = ctx.guild

        now = time.monotonic()

        self.raid_mode[
            guild.id
        ] = now + self.raid_duration

        await self.lock_channels(
            guild
        )

        await ctx.send(
            "🔒 **Raid Lockdown چالاک کرا.**\n"
            f"⏱️ ماوە: "
            f"**{self.raid_duration} چرکە**"
        )

    # =========================================================
    # MANUAL RAID UNLOCK
    # =========================================================

    @commands.command(
        name="raidunlock"
    )
    @commands.has_permissions(
        administrator=True
    )
    async def raidunlock(
        self,
        ctx
    ):

        guild = ctx.guild

        self.raid_mode.pop(
            guild.id,
            None
        )

        await self.unlock_channels(
            guild
        )

        await ctx.send(
            "🔓 **Raid Lockdown داخرا.**\n"
            "✅ Channel ـەکان restore کران."
        )

    # =========================================================
    # RAID STATUS
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
    async def raidstatus(
        self,
        ctx
    ):

        guild = ctx.guild

        guild_id = guild.id

        now = time.monotonic()

        joins = [
            timestamp
            for timestamp
            in self.joins[guild_id]
            if now - timestamp
            <= self.raid_time_window
        ]

        expiry = self.raid_mode.get(
            guild_id,
            0
        )

        active = expiry > now

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
                expiry - now
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
                "✅ Raid Mode چالاک نییە."
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

        embed.add_field(
            name="🔒 Lockdown",
            value=(
                "چالاکە"
                if active
                else "ناچالاکە"
            ),
            inline=True
        )

        await ctx.send(
            embed=embed
        )

    # =========================================================
    # ANTI-SPAM STATUS
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
    async def antispam(
        self,
        ctx
    ):

        embed = discord.Embed(
            title="🛡️ Anti-Spam System",
            description=(
                "سیستەمی دژەسپام چالاکە."
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
            name="🔒 Raid Lockdown",
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
# SETUP
# =========================================================

async def setup(bot):

    await bot.add_cog(
        AntiSpam(bot)
    )
