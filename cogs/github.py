import asyncio
from urllib.parse import quote

import aiohttp
import discord
from discord.ext import commands

from config import GITHUB_TOKEN


class Github(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.headers = (
            {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if GITHUB_TOKEN
            else {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        self.base = "https://api.github.com"

    async def _req(self, endpoint, params=None):
        url = f"{self.base}/{endpoint.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout,
            ) as session:
                async with session.get(url, params=params) as response:

                    if response.status == 200:
                        return await response.json()

                    if response.status == 404:
                        return None

                    if response.status == 403:
                        return {"_error": "rate_limit"}

                    if response.status == 401:
                        return {"_error": "unauthorized"}

                    return {"_error": f"http_{response.status}"}

        except (aiohttp.ClientError, asyncio.TimeoutError):
            return {"_error": "network"}

    async def _send_error(self, ctx, data):
        if not isinstance(data, dict):
            return False

        error = data.get("_error")

        if not error:
            return False

        messages = {
            "rate_limit": (
                "⏳ سنووری GitHub API ـەکە گەیشتە کۆتایی. "
                "دواتر هەوڵبدە."
            ),
            "unauthorized": (
                "❌ GitHub Token ـەکە نادروستە یان "
                "دەستگەیشتنی پێویستی نییە."
            ),
            "network": (
                "❌ پەیوەندی بە GitHub ـەوە سەرکەوتوو نەبوو."
            ),
        }

        await ctx.send(
            messages.get(
                error,
                "❌ GitHub هەڵەیەکی وەڵامدایە.",
            )
        )

        return True

    # =========================================================
    # GitHub User
    # =========================================================

    @commands.hybrid_command(
        name="github",
        aliases=["gh", "گیتهاب"],
    )
    async def _github(self, ctx, username: str):
        """زانیاری پڕۆفایلی گیتهاب"""

        username = username.strip()

        data = await self._req(
            f"users/{quote(username, safe='')}"
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send("❌ بەکارهێنەر نەدۆزرایەوە")
            return

        embed = discord.Embed(
            title=f"🔷 {data.get('login', username)}",
            url=data.get("html_url"),
            color=0x2B3137,
        )

        if data.get("avatar_url"):
            embed.set_thumbnail(
                url=data["avatar_url"]
            )

        embed.description = (
            data.get("bio")
            or "بێ وەسف"
        )

        embed.add_field(
            name="📁 ڕێپۆی گشتی",
            value=str(data.get("public_repos", 0)),
            inline=True,
        )

        embed.add_field(
            name="👥 شوێنکەوتووان",
            value=str(data.get("followers", 0)),
            inline=True,
        )

        embed.add_field(
            name="👤 شوێنکەوتوو",
            value=str(data.get("following", 0)),
            inline=True,
        )

        embed.add_field(
            name="📍 شوێن",
            value=data.get("location") or "نەزانراو",
            inline=True,
        )

        embed.add_field(
            name="🏢 کار",
            value=data.get("company") or "نەزانراو",
            inline=True,
        )

        created_at = data.get("created_at")

        if created_at:
            embed.set_footer(
                text=f"بەکارهێنەر بووە لە {created_at[:10]}"
            )

        await ctx.send(embed=embed)

    # =========================================================
    # Repository
    # =========================================================

    @commands.hybrid_command(
        name="repo",
        aliases=["repository", "ڕێپۆ"],
    )
    async def _repo(self, ctx, owner: str, repo: str):
        """زانیاری ڕێپۆزیتۆری"""

        owner = owner.strip()
        repo = repo.strip()

        data = await self._req(
            f"repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send("❌ ڕێپۆ نەدۆزرایەوە")
            return

        embed = discord.Embed(
            title=f"📦 {data.get('full_name', f'{owner}/{repo}')}",
            url=data.get("html_url"),
            color=0x2B3137,
        )

        embed.description = (
            data.get("description")
            or "بێ وەسف"
        )

        embed.add_field(
            name="⭐ ئەستێرە",
            value=str(data.get("stargazers_count", 0)),
            inline=True,
        )

        embed.add_field(
            name="🍴 فۆرک",
            value=str(data.get("forks_count", 0)),
            inline=True,
        )

        embed.add_field(
            name="🐛 ئیشی کراوە",
            value=str(data.get("open_issues_count", 0)),
            inline=True,
        )

        embed.add_field(
            name="👁 بینین",
            value=str(data.get("watchers_count", 0)),
            inline=True,
        )

        size_mb = data.get("size", 0) / 1024

        embed.add_field(
            name="📏 قەبارە",
            value=f"{size_mb:.1f} MB",
            inline=True,
        )

        embed.set_footer(
            text=f"زمان: {data.get('language') or 'نەزانراو'}"
        )

        await ctx.send(embed=embed)

    # =========================================================
    # User Repositories
    # =========================================================

    @commands.hybrid_command(
        name="repos",
        aliases=["userrepos", "ڕێپۆکانی"],
    )
    async def _repos(
        self,
        ctx,
        username: str,
        limit: int = 5,
    ):
        """پێڕستی ڕێپۆکانی بەکارهێنەر"""

        limit = min(max(limit, 1), 30)

        encoded_username = quote(
            username.strip(),
            safe="",
        )

        data = await self._req(
            f"users/{encoded_username}/repos",
            {
                "per_page": limit,
                "sort": "updated",
            },
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send(
                f"❌ هیچ ڕێپۆیەک بۆ {username} نەدۆزرایەوە"
            )
            return

        msg = f"**📁 ڕێپۆکانی {username}:**\n"

        for i, repo_data in enumerate(data[:limit], 1):
            msg += (
                f"{i}. [{repo_data['name']}]"
                f"({repo_data['html_url']}) - "
                f"{repo_data.get('stargazers_count', 0)} ⭐\n"
            )

        await ctx.send(msg[:2000])

    # =========================================================
    # Stars
    # =========================================================

    @commands.hybrid_command(
        name="stars",
        aliases=["topstars", "ئەستێرەکان"],
    )
    async def _stars(
        self,
        ctx,
        username: str,
        limit: int = 5,
    ):
        """پڕ ئەستێرەترین ڕێپۆکانی بەکارهێنەر"""

        limit = min(max(limit, 1), 30)

        encoded_username = quote(
            username.strip(),
            safe="",
        )

        data = await self._req(
            f"users/{encoded_username}/repos",
            {
                "per_page": limit,
                "sort": "stars",
            },
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send(
                "❌ هیچ ڕێپۆیەک نەدۆزرایەوە"
            )
            return

        sorted_repos = sorted(
            data,
            key=lambda item: item.get(
                "stargazers_count",
                0,
            ),
            reverse=True,
        )[:limit]

        msg = (
            f"**⭐ پڕ ئەستێرەترین ڕێپۆکانی "
            f"{username}:**\n"
        )

        for i, repo_data in enumerate(
            sorted_repos,
            1,
        ):
            msg += (
                f"{i}. [{repo_data['name']}]"
                f"({repo_data['html_url']}) - "
                f"{repo_data.get('stargazers_count', 0)} ⭐\n"
            )

        await ctx.send(msg[:2000])

    # =========================================================
    # Issues
    # =========================================================

    @commands.hybrid_command(
        name="issues",
        aliases=["iss", "ئیشەکان"],
    )
    async def _issues(
        self,
        ctx,
        owner: str,
        repo: str,
        state: str = "open",
    ):
        """پیشاندانی ئیشەکانی ڕێپۆ"""

        state = (
            state
            if state in {"open", "closed", "all"}
            else "open"
        )

        data = await self._req(
            f"repos/{quote(owner.strip(), safe='')}/"
            f"{quote(repo.strip(), safe='')}/issues",
            {
                "state": state,
                "per_page": 5,
            },
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send(
                f"✅ هیچ ئیشێک نییە لە **{owner}/{repo}**"
            )
            return

        msg = (
            f"**🐛 ئیشەکانی {owner}/{repo} "
            f"({state}):**\n"
        )

        for issue in data[:5]:

            if "pull_request" in issue:
                continue

            msg += (
                f"- [{issue['title']}]"
                f"({issue['html_url']}) - "
                f"{issue['user']['login']}\n"
            )

        if msg.endswith(f"({state}):**\n"):
            msg += "هیچ Issue ـێکی ڕاستەقینە نییە."

        await ctx.send(msg[:2000])

    # =========================================================
    # Pull Requests
    # =========================================================

    @commands.hybrid_command(
        name="pr",
        aliases=[
            "pullrequest",
            "pull",
            "داواکاری",
        ],
    )
    async def _pr(
        self,
        ctx,
        owner: str,
        repo: str,
        state: str = "open",
    ):
        """داواکاری ڕاکێشان"""

        state = (
            state
            if state in {"open", "closed", "all"}
            else "open"
        )

        data = await self._req(
            f"repos/{quote(owner.strip(), safe='')}/"
            f"{quote(repo.strip(), safe='')}/pulls",
            {
                "state": state,
                "per_page": 5,
            },
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send(
                f"✅ هیچ PRێک نییە لە **{owner}/{repo}**"
            )
            return

        msg = (
            f"**🔀 PRەکانی {owner}/{repo} "
            f"({state}):**\n"
        )

        for pr in data[:5]:
            msg += (
                f"- [{pr['title']}]"
                f"({pr['html_url']}) - "
                f"{pr['user']['login']}\n"
            )

        await ctx.send(msg[:2000])

    # =========================================================
    # Gists
    # =========================================================

    @commands.hybrid_command(
        name="gist",
        aliases=["gists", "گێست"],
    )
    async def _gist(
        self,
        ctx,
        username: str,
    ):
        """پێڕستی گێستەکانی بەکارهێنەر"""

        encoded_username = quote(
            username.strip(),
            safe="",
        )

        data = await self._req(
            f"users/{encoded_username}/gists",
            {
                "per_page": 5,
            },
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send(
                f"📭 هیچ گێستێک نییە بۆ {username}"
            )
            return

        msg = f"**📝 گێستەکانی {username}:**\n"

        for gist in data[:5]:
            files = "، ".join(
                gist.get("files", {}).keys()
            )

            desc = (
                gist.get("description")
                or "بێ وەسف"
            )[:40]

            msg += (
                f"- {desc} - {files}\n"
            )

        await ctx.send(msg[:2000])

    # =========================================================
    # Contributors
    # =========================================================

    @commands.hybrid_command(
        name="contributors",
        aliases=[
            "contribs",
            "بەشداربووان",
        ],
    )
    async def _contributors(
        self,
        ctx,
        owner: str,
        repo: str,
    ):
        """بەشداربووانی ڕێپۆ"""

        data = await self._req(
            f"repos/{quote(owner.strip(), safe='')}/"
            f"{quote(repo.strip(), safe='')}/contributors",
            {
                "per_page": 10,
            },
        )

        if await self._send_error(ctx, data):
            return

        if not data:
            await ctx.send(
                f"❌ هیچ بەشداربووێک نییە بۆ {owner}/{repo}"
            )
            return

        msg = (
            f"**👥 بەشداربووانی "
            f"{owner}/{repo}:**\n"
        )

        for contributor in data[:10]:

            login = contributor.get(
                "login",
                "unknown",
            )

            contributions = contributor.get(
                "contributions",
                0,
            )

            msg += (
                f"- [{login}]"
                f"(https://github.com/{login}) - "
                f"{contributions} بەشداری\n"
            )

        await ctx.send(msg[:2000])

    # =========================================================
    # GitHub Search
    # =========================================================

    @commands.hybrid_command(
        name="gitsearch",
        aliases=[
            "ghsearch",
            "گەڕان",
        ],
    )
    async def _gitsearch(
        self,
        ctx,
        *,
        query: str,
    ):
        """گەڕان لە گیتهاب بۆ ڕێپۆ"""

        data = await self._req(
            "search/repositories",
            {
                "q": query,
                "per_page": 5,
            },
        )

        if await self._send_error(ctx, data):
            return

        if (
            not data
            or data.get("total_count", 0) == 0
        ):
            await ctx.send(
                f"❌ هیچ نەدۆزرایەوە بۆ '{query}'"
            )
            return

        msg = (
            f"**🔍 ئەنجامی گەڕان بۆ "
            f"'{query}':**\n"
        )

        for repo_data in data["items"][:5]:

            msg += (
                f"- [{repo_data['full_name']}]"
                f"({repo_data['html_url']}) - "
                f"{repo_data.get('stargazers_count', 0)} ⭐ - "
                f"{repo_data.get('language') or '?'}\n"
            )

        await ctx.send(msg[:2000])


async def setup(bot):
    await bot.add_cog(Github(bot))
