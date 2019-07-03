from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember
from .utils.discord_search import choose_item
import arrow
from math import floor
from datetime import timedelta
from random import random
import arrow
from typing import Optional


class FunModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="cookie", aliases=["kookie", "cookies"])
    async def cookie(self, ctx, *user: str):
        """Give people cookies."""
        if user:
            user = await choose_item(ctx, "member", ctx.guild, " ".join(user).lower())
        else:
            user = ctx.author
        if ctx.invoked_with.endswith("s"):
            have = "have" if user == ctx.author else "has"
            addr = "You" if user == ctx.author else f"@**{user}**"
            user = ctx.author if user == ctx.author else user

            count = int(await self.bot.db.zscore("cookies", user.id) or 0)
            plural = "s" if count != 1 else ""
            await ctx.send(f":cookie: {addr} {have} **{count}** cookie{plural}.")
            return
        if user.id == ctx.author.id:
            raise cmd.BadArgument(
                f"You cannot give yourself a cookie, **{ctx.author}**"
            )
        now = arrow.utcnow()
        next_cookie = await self.bot.db.hget("cookie", ctx.author.id)
        if next_cookie is None:
            next_cookie = now
        else:
            next_cookie = arrow.Arrow.strptime(next_cookie, "%Y%m%d")
        if next_cookie > now:
            raise cmd.BadArgument(
                f"You can only give away 1 cookie a day, **{ctx.author}**"
            )
        await self.bot.db.zincrement("cookies", user.id, score=1)
        await self.bot.db.hset(
            "cookie", ctx.author.id, now.shift(days=1).strftime("%Y%m%d")
        )
        await ctx.send(
            f":cookie: @**{ctx.author}** has given @**{user}** a cookie! Om nom nom!"
        )

    @cmd.command(name="ayy", aliases=["ayylmao"])
    async def ayy(self, ctx):
        await ctx.send("lmao")

    @cmd.command(name="f", aliases=["payrespects"])
    async def _f(self, ctx):
        now = arrow.utcnow()
        count = int(await self.bot.db.zscore("f", now.strftime("%Y%m%d")) or 0)
        next_respect = await self.bot.db.hget("respects", ctx.author.id)

        if next_respect is None:
            next_respect = now
        else:
            next_respect = arrow.Arrow.strptime(next_respect, "%Y%m%d")
        if next_respect > now:
            await ctx.send("You have already paid your respects today.")
        else:
            await self.bot.db.zincrement("f", now.strftime("%Y%m%d"))
            await self.bot.db.hset(
                "respects", ctx.author.id, now.shift(days=1).strftime("%Y%m%d")
            )
            await ctx.send(f"Respects paid: {count+1}")

    @cmd.command(name="mock")
    async def _mock(self, ctx, *, message):

        try:
            await ctx.message.delete()
        except Exception as e:
            await ctx.send("Oops, I cannot manage messages in this channel.")
            return
        msgbuff = ""
        uppercount = 0
        lowercount = 0
        for c in message:
            if c.isalpha():
                if uppercount == 2:
                    uppercount = 0
                    upper = False
                    lowercount += 1
                elif lowercount == 2:
                    lowercount = 0
                    upper = True
                    uppercount += 1
                else:
                    upper = random() > 0.5
                    uppercount = uppercount + 1 if upper else 0
                    lowercount = lowercount + 1 if not upper else 0

                msgbuff += c.upper() if upper else c.lower()
            else:
                msgbuff += c

        await ctx.send(
            f"<:sponge_left:475979172372807680> {msgbuff} <:sponge_right:475979143964524544>"
        )


def setup(bot):
    bot.add_cog(FunModule(bot))
