import discord
from discord.ext import commands
import aiohttp
import asyncio
from urllib.parse import quote
from config import GITHUB_TOKEN


class Github(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        self.base = "https://api.github.com"

    async def _req(self, endpoint, params=None):
        url = f"{self.base}/{endpoint.lstrip('/')}"
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.get(url, params=params) as r:
                    if r.status == 200:
                        return await r.json()
                    if r.status == 404:
                        return None
                    if r.status == 403:
                        return {"_error": "rate_limit"}
                    return {"_error": f"http_{r.status}"}
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return {"_error": "network"}

    async def _send_error(self, ctx, data):
        if isinstance(data, dict) and data.get("_error"):
            msg = {
                "rate_limit": "⏳ GitHub سنووری API ـی گەیشتۆتە کۆتایی. دواتر هەوڵبدە.",
                "network": "❌ پەیوەندی بە GitHub ـەوە سەرکەوتوو نەبوو.",
            }.get(data["_error"], "❌ GitHub هەڵەیەکی وەڵامدایە.")
            await ctx.send(msg)
            return True
        return False

    @commands.command(name="github", aliases=["gh", "گیتهاب"])
    async def _github(self, ctx, username: str):
        """زانیاری پڕۆفایلی گیتهاب"""
        data = await self._req(f"users/{username}")
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send("❌ بەکارهێنەر نەدۆزرایەوە")
        embed = discord.Embed(
            title=f"🔷 {data['login']}",
            url=data["html_url"],
            color=0x2b3137
        )
        if data.get("avatar_url"):
            embed.set_thumbnail(url=data["avatar_url"])
        embed.description = data.get("bio", "بێ وەسف")
        embed.add_field(name="📁 ڕێپۆی گشتی", value=data.get("public_repos", 0), inline=True)
        embed.add_field(name="👥 شوێنکەوتووان", value=data.get("followers", 0), inline=True)
        embed.add_field(name="👤 شوێنکەوتوو", value=data.get("following", 0), inline=True)
        embed.add_field(name="📍 شوێن", value=data.get("location", "نەزانراو"), inline=True)
        embed.add_field(name="🏢 کار", value=data.get("company", "نەزانراو"), inline=True)
        if data.get("created_at"):
            embed.set_footer(text=f"بەکارهێنەر بووە لە {data['created_at'][:10]}")
        await ctx.send(embed=embed)

    @commands.command(name="repo", aliases=["repository", "ڕێپۆ"])
    async def _repo(self, ctx, owner: str, repo: str):
        """زانیاری ڕێپۆزیتۆری"""
        data = await self._req(f"repos/{owner}/{repo}")
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send("❌ ڕێپۆ نەدۆزرایەوە")
        embed = discord.Embed(
            title=f"📦 {data['full_name']}",
            url=data["html_url"],
            color=0x2b3137
        )
        embed.description = data.get("description", "بێ وەسف")
        embed.add_field(name="⭐ ئەستێرە", value=data.get("stargazers_count", 0), inline=True)
        embed.add_field(name="🍴 فۆرک", value=data.get("forks_count", 0), inline=True)
        embed.add_field(name="🐛 ئیشی کراوە", value=data.get("open_issues_count", 0), inline=True)
        embed.add_field(name="👁 بینین", value=data.get("watchers_count", 0), inline=True)
        embed.add_field(name="📏 قەبارە", value=f"{data.get('size', 0) / 1024:.1f} MB", inline=True)
        embed.set_footer(text=f"زمان: {data.get('language', 'نەزانراو')}")
        await ctx.send(embed=embed)

    @commands.command(name="repos", aliases=["userrepos", "ڕێپۆکانی"])
    async def _repos(self, ctx, username: str, limit: int = 5):
        """پێڕستی ڕێپۆکانی بەکارهێنەر"""
        data = await self._req(f"users/{quote(username, safe="")}/repos", {"per_page": min(max(limit, 1), 30), "sort": "updated"})
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send(f"❌ هیچ ڕێپۆیەک بۆ {username} نەدۆزرایەوە")
        msg = f"**📁 ڕێپۆکانی {username}:**\n"
        for i, r in enumerate(data[:limit], 1):
            msg += f"{i}. [{r['name']}]({r['html_url']}) - {r['stargazers_count']} ⭐\n"
        await ctx.send(msg[:2000])

    @commands.command(name="stars", aliases=["topstars", "ئەستێرەکان"])
    async def _stars(self, ctx, username: str, limit: int = 5):
        """پڕ ئەستێرەترین ڕێپۆکانی بەکارهێنەر"""
        data = await self._req(f"users/{quote(username, safe="")}/repos", {"per_page": min(max(limit, 1), 30), "sort": "stars"})
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send(f"❌ هیچ ڕێپۆیەک نەدۆزرایەوە")
        sorted_repos = sorted(data, key=lambda x: x["stargazers_count"], reverse=True)[:limit]
        msg = f"**⭐ پڕ ئەستێرەترین ڕێپۆکانی {username}:**\n"
        for i, r in enumerate(sorted_repos, 1):
            msg += f"{i}. [{r['name']}]({r['html_url']}) - {r['stargazers_count']} ⭐\n"
        await ctx.send(msg[:2000])

    @commands.command(name="issues", aliases=["iss", "ئیشەکان"])
    async def _issues(self, ctx, owner: str, repo: str, state: str = "open"):
        """پیشاندانی ئیشەکانی ڕێپۆ"""
        data = await self._req(f"repos/{quote(owner, safe="")}/{quote(repo, safe="")}/issues", {"state": state if state in {"open","closed","all"} else "open", "per_page": 5})
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send(f"✅ هیچ ئیشێک نییە لە **{owner}/{repo}**")
        msg = f"**🐛 ئیشەکانی {owner}/{repo} ({state}):**\n"
        for issue in data[:5]:
            if "pull_request" not in issue:
                msg += f"- [{issue['title']}]({issue['html_url']}) - {issue['user']['login']}\n"
        await ctx.send(msg[:2000])

    @commands.command(name="pr", aliases=["pullrequest", "pull", "داواکاری"])
    async def _pr(self, ctx, owner: str, repo: str, state: str = "open"):
        """داواکاری ڕاکێشان (Pull Requests)"""
        data = await self._req(f"repos/{quote(owner, safe="")}/{quote(repo, safe="")}/pulls", {"state": state if state in {"open","closed","all"} else "open", "per_page": 5})
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send(f"✅ هیچ PRێک نییە لە **{owner}/{repo}**")
        msg = f"**🔀 PRەکانی {owner}/{repo} ({state}):**\n"
        for pr in data[:5]:
            msg += f"- [{pr['title']}]({pr['html_url']}) - {pr['user']['login']}\n"
        await ctx.send(msg[:2000])

    @commands.command(name="gist", aliases=["gists", "گێست"])
    async def _gist(self, ctx, username: str):
        """پێڕستی گێستەکانی بەکارهێنەر"""
        data = await self._req(f"users/{quote(username, safe="")}/gists", {"per_page": 5})
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send(f"📭 هیچ گێستێک نییە بۆ {username}")
        msg = f"**📝 گێستەکانی {username}:**\n"
        for g in data[:5]:
            files = "، ".join(g["files"].keys())
            desc = g.get("description", "بێ وەسف")[:40]
            msg += f"- {desc} - {files}\n"
        await ctx.send(msg[:2000])

    @commands.command(name="contributors", aliases=["contribs", "بەشداربووان"])
    async def _contributors(self, ctx, owner: str, repo: str):
        """بەشداربووانی ڕێپۆ"""
        data = await self._req(f"repos/{quote(owner, safe="")}/{quote(repo, safe="")}/contributors", {"per_page": 10})
        if await self._send_error(ctx, data):
            return
        if not data:
            return await ctx.send(f"❌ هیچ بەشداربووێک نییە بۆ {owner}/{repo}")
        msg = f"**👥 بەشداربووانی {owner}/{repo}:**\n"
        for c in data[:10]:
            msg += f"- [{c['login']}](https://github.com/{c['login']}) - {c['contributions']} بەشداری\n"
        await ctx.send(msg[:2000])

    @commands.command(name="gitsearch", aliases=["ghsearch", "گەڕان"])
    async def _gitsearch(self, ctx, *, query: str):
        """گەڕان لە گیتهاب بۆ ڕێپۆ"""
        data = await self._req("search/repositories", {"q": query, "per_page": 5})
        if await self._send_error(ctx, data):
            return
        if not data or data.get("total_count", 0) == 0:
            return await ctx.send(f"❌ هیچ نەدۆزرایەوە بۆ '{query}'")
        msg = f"**🔍 ئەنجامی گەڕان بۆ '{query}':**\n"
        for r in data["items"][:5]:
            msg += f"- [{r['full_name']}]({r['html_url']}) - {r['stargazers_count']} ⭐ - {r.get('language', '?')}\n"
        await ctx.send(msg[:2000])


async def setup(bot):
    await bot.add_cog(Github(bot))
