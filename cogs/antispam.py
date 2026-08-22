import discord
from discord.ext import commands
from collections import defaultdict, deque
from datetime import timedelta
import time


class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # message timestamps per user
        self.messages = defaultdict(lambda: deque(maxlen=10))

        # duplicate messages per user
        self.last_messages = defaultdict(lambda: deque(maxlen=5))

        # strikes per user
        self.strikes = defaultdict(int)

        # Settings
        self.max_messages = 5
        self.time_window = 5

        self.max_duplicates = 3

        self.max_mentions = 5

        self.timeout_seconds = 60

    def is_exempt(self, member: discord.Member):
        """Admins and moderators are ignored by Anti-Spam."""
        if member.guild_permissions.administrator:
            return True

        if member.guild_permissions.manage_messages:
            return True

        if member.guild_permissions.moderate_members:
            return True

        return False

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
                    f"🔇 {member.mention} بۆ **{self.timeout_seconds} چرکە** "
                    f"timeout کرا.\n"
                    f"📛 هۆکار: **{reason}**"
                )

                await warning.delete(delay=5)

            except discord.Forbidden:
                warning = await message.channel.send(
                    f"⚠️ نەتوانرا {member.mention} timeout بکرێت. "
                    f"پێویستە Bot ڕۆڵی `Moderate Members` ـی هەبێت."
                )

                await warning.delete(delay=7)

            except Exception as e:
                print(f"❌ Anti-Spam timeout error: {e}")

        else:
            warning = await message.channel.send(
                f"⚠️ {member.mention} **Spam قەدەغەیە!**\n"
                f"📛 Strike: **{strikes}/3**\n"
                f"هۆکار: **{reason}**"
            )

            await warning.delete(delay=4)

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignore bots
        if message.author.bot:
            return

        # Ignore DMs
        if not message.guild:
            return

        member = message.author

        # Ignore admins/moderators
        if self.is_exempt(member):
            return

        now = time.monotonic()

        # --------------------------------
        # 1. Flood protection
        # --------------------------------

        user_messages = self.messages[member.id]

        user_messages.append(now)

        while user_messages and now - user_messages[0] > self.time_window:
            user_messages.popleft()

        if len(user_messages) >= self.max_messages:
            await self.punish(
                message,
                "ناردنی نامەی زۆر لە کاتی کەمدا"
            )

            user_messages.clear()
            return

        # --------------------------------
        # 2. Duplicate message protection
        # --------------------------------

        content = message.content.strip().lower()

        if content:
            last_messages = self.last_messages[member.id]

            last_messages.append(content)

            duplicate_count = sum(
                1 for msg in last_messages
                if msg == content
            )

            if duplicate_count >= self.max_duplicates:
                await self.punish(
                    message,
                    "دووبارەکردنەوەی هەمان نامە"
                )

                last_messages.clear()
                return

        # --------------------------------
        # 3. Mention spam protection
        # --------------------------------

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

    @commands.command(name="antispam", aliases=["spamsettings"])
    @commands.has_permissions(administrator=True)
    async def antispam(self, ctx):
        """پیشاندانی ڕێکخستنی Anti-Spam"""

        embed = discord.Embed(
            title="🛡️ Anti-Spam",
            description="سیستەمی دژەسپامی بۆتەکە چالاکە.",
            color=0x2ecc71
        )

        embed.add_field(
            name="💬 Flood",
            value=f"{self.max_messages} نامە لە {self.time_window} چرکە",
            inline=False
        )

        embed.add_field(
            name="🔁 Duplicate",
            value=f"{self.max_duplicates} جار هەمان نامە",
            inline=False
        )

        embed.add_field(
            name="📢 Mention",
            value=f"{self.max_mentions} mention",
            inline=False
        )

        embed.add_field(
            name="🔇 Punishment",
            value=f"3 strikes → {self.timeout_seconds} چرکە timeout",
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
