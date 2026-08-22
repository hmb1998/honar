import discord
from discord.ext import commands
from collections import defaultdict, deque
from datetime import timedelta
import time
import re


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Message timestamps
        self.messages = defaultdict(lambda: deque(maxlen=15))

        # Duplicate messages
        self.last_messages = defaultdict(lambda: deque(maxlen=5))

        # Strikes
        self.strikes = defaultdict(int)

        # Member joins per guild
        self.joins = defaultdict(lambda: deque(maxlen=50))

        # Settings
        self.max_messages = 5
        self.time_window = 5

        self.max_duplicates = 3

        self.max_mentions = 5

        self.max_everyone = 1

        self.timeout_seconds = 60

        # Anti-Raid
        self.raid_join_limit = 8
        self.raid_time_window = 10

        # Link protection
        self.block_links = True

        self.link_pattern = re.compile(
            r"(https?://|www\.)[^\s]+",
            re.IGNORECASE
        )

    # =========================================================
    # Permission / Exempt
    # =========================================================

    def is_exempt(self, member: discord.Member):
        """Admins and moderators are ignored."""

        if member.guild_permissions.administrator:
            return True

        if member.guild_permissions.manage_messages:
            return True

        if member.guild_permissions.moderate_members:
            return True

        return False

    # =========================================================
    # Punishment
    # =========================================================

    async def punish(self, message, reason):

        member = message.author

        self.strikes[member.id] += 1
        strikes = self.strikes[member.id]

        # Delete spam message
        try:
            await message.delete()
        except (discord.NotFound, discord.Forbidden):
            pass

        # 3 strikes = timeout
        if strikes >= 3:

            try:
                await member.timeout(
                    timedelta(seconds=self.timeout_seconds),
                    reason=f"Anti-Spam: {reason}"
                )

                self.strikes[member.id] = 0

                warning = await message.channel.send(
                    f"🔇 {member.mention} بۆ "
                    f"**{self.timeout_seconds} چرکە** timeout کرا.\n"
                    f"📛 هۆکار: **{reason}**"
                )

                await warning.delete(delay=5)

            except discord.Forbidden:

                warning = await message.channel.send(
                    f"⚠️ نەتوانرا {member.mention} timeout بکرێت.\n"
                    f"Bot دەبێت `Moderate Members` ـی هەبێت."
                )

                await warning.delete(delay=7)

            except Exception as e:
                print(f"❌ Timeout error: {e}")

        else:

            warning = await message.channel.send(
                f"⚠️ {member.mention} **Spam قەدەغەیە!**\n"
                f"📛 Strike: **{strikes}/3**\n"
                f"هۆکار: **{reason}**"
            )

            await warning.delete(delay=4)

    # =========================================================
    # Message Anti-Spam
    # =========================================================

    @commands.Cog.listener()
    async def on_message(self, message):

        if not message.guild:
            return

        if message.author.bot:
            return

        member = message.author

        if self.is_exempt(member):
            return

        now = time.monotonic()

        # =====================================================
        # 1. Flood Spam
        # =====================================================

        user_messages = self.messages[member.id]

        user_messages.append(now)

        while (
            user_messages
            and now - user_messages[0] > self.time_window
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
        # 2. Duplicate Spam
        # =====================================================

        content = message.content.strip().lower()

        if content:

            last_messages = self.last_messages[member.id]

            last_messages.append(content)

            duplicate_count = sum(
                1
                for msg in last_messages
                if msg == content
            )

            if duplicate_count >= self.max_duplicates:

                await self.punish(
                    message,
                    "دووبارەکردنەوەی هەمان نامە"
                )

                last_messages.clear()
                return

        # =====================================================
        # 3. Mention Spam
        # =====================================================

        mention_count = (
            len(message.mentions)
            + len(message.role_mentions)
        )

        if mention_count >= self.max_mentions:

            await self.punish(
                message,
                "Mention Spam"
            )

            return

        # =====================================================
        # 4. @everyone / @here Spam
        # =====================================================

        if message.mention_everyone:

            await self.punish(
                message,
                "@everyone / @here Spam"
            )

            return

        # =====================================================
        # 5. Link Spam
        # =====================================================

        if self.block_links and content:

            links = self.link_pattern.findall(content)

            if links:

                await self.punish(
                    message,
                    "ناردنی لینک"
                )

                return

    # =========================================================
    # Anti-Raid / Join Spam
    # =========================================================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.bot:
            # Bot joins are still recorded for raid detection
            pass

        guild = member.guild
        now = time.monotonic()

        joins = self.joins[guild.id]

        joins.append(now)

        while (
            joins
            and now - joins[0] > self.raid_time_window
        ):
            joins.popleft()

        # =====================================================
        # Raid detected
        # =====================================================

        if len(joins) >= self.raid_join_limit:

            print(
                f"🚨 Anti-Raid: {guild.name} "
                f"{len(joins)} joins detected"
            )

            # Try to notify system channel
            channel = guild.system_channel

            if channel:

                try:
                    warning = await channel.send(
                        f"🚨 **ANTI-RAID ACTIVATED**\n"
                        f"لە ماوەی {self.raid_time_window} چرکەدا "
                        f"**{len(joins)}** ئەندام هاتنە ناو سێرڤەر.\n"
                        f"🛡️ سیستەمی دژەRaid چالاک بوو."
                    )

                    await warning.delete(delay=10)

                except discord.Forbidden:
                    pass

            # If the newly joined member is a bot,
            # remove it during an active raid.
            if member.bot:

                try:
                    await member.kick(
                        reason="Anti-Raid: Bot joined during raid"
                    )

                except discord.Forbidden:
                    pass

                except Exception as e:
                    print(
                        f"❌ Anti-Raid kick error: {e}"
                    )

    # =========================================================
    # Anti-Raid Status Command
    # =========================================================

    @commands.command(
        name="raidstatus",
        aliases=["raid", "antiraid"]
    )
    @commands.has_permissions(administrator=True)
    async def raidstatus(self, ctx):

        joins = self.joins[ctx.guild.id]

        now = time.monotonic()

        recent = [
            x for x in joins
            if now - x <= self.raid_time_window
        ]

        embed = discord.Embed(
            title="🛡️ Anti-Raid Status",
            color=0x2ecc71
        )

        embed.add_field(
            name="👥 Joins",
            value=str(len(recent)),
            inline=True
        )

        embed.add_field(
            name="🚨 Raid Limit",
            value=str(self.raid_join_limit),
            inline=True
        )

        embed.add_field(
            name="⏱️ Time Window",
            value=f"{self.raid_time_window} چرکە",
            inline=True
        )

        if len(recent) >= self.raid_join_limit:
            embed.description = "🚨 **RAID DETECTED**"
        else:
            embed.description = "✅ هیچ Raid ـێکی چالاک نییە."

        await ctx.send(embed=embed)

    # =========================================================
    # Anti-Spam Status
    # =========================================================

    @commands.command(
        name="antispam",
        aliases=["spamsettings"]
    )
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx):

        embed = discord.Embed(
            title="🛡️ Anti-Spam System",
            description="سیستەمی دژەسپام چالاکە.",
            color=0x2ecc71
        )

        embed.add_field(
            name="💬 Flood",
            value=f"{self.max_messages} نامە / "
                  f"{self.time_window} چرکە",
            inline=False
        )

        embed.add_field(
            name="🔁 Duplicate",
            value=f"{self.max_duplicates} جار",
            inline=False
        )

        embed.add_field(
            name="📢 Mention",
            value=f"{self.max_mentions} mention",
            inline=False
        )

        embed.add_field(
            name="📣 Everyone/Here",
            value="چالاکە",
            inline=False
        )

        embed.add_field(
            name="🔗 Link Spam",
            value="چالاکە",
            inline=False
        )

        embed.add_field(
            name="🚨 Anti-Raid",
            value=f"{self.raid_join_limit} join / "
                  f"{self.raid_time_window} چرکە",
            inline=False
        )

        embed.add_field(
            name="🔇 Punishment",
            value=f"3 strikes → "
                  f"{self.timeout_seconds} چرکە timeout",
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
