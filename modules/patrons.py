from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember
from .utils.discord_search import choose_item
import arrow
from math import floor
from datetime import timedelta
import asyncio
import random


class PatronModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.immo = 259451392630980610
        self.pleb = 254710997225308181
        self.bae = 514905469094068253
        self.bunnybot = 575101399747133443
        self.dream = 426087355250638859
        self.teto = 435221942807691266

    @cmd.command(name="dreamzxe", aliases=["dream", "xze", "bunnybot", "dreamxze"])
    async def _dream(self, ctx):
        s_bunnybot = ctx.guild.get_member(self.bunnybot)
        s_dream = ctx.guild.get_member(self.dream)
        if s_dream is not None and s_bunnybot is not None:
            await ctx.send(":rabbit: The whole rabbit squad is here!")
        elif s_dream is not None and s_bunnybot is None:
            await ctx.send(":rabbit: The master rabbit has lost the robot rabbit.")
        elif s_dream is None and s_bunnybot is not None:
            await ctx.send(":rabbit: The robbot rabbit is trying to find the master.")

    @cmd.command(name="bae")
    async def _bae(self, ctx):
        if ctx.message.author.id != self.bae:
            await ctx.send("Oh, you are not bae ...")
            return
        await ctx.send("OMG, HI BAE!!")

    @cmd.command(name="pleb")
    async def _pleb(self, ctx):
        if ctx.author.id != self.pleb:
            await ctx.send("You are not enough of a pleb to use this command :<")
            return
        u = await self.bot.fetch_user(self.pleb)
        await ctx.send(
            f"**{u}** is the most pleb pleb I ever met, out of all the plebs >:D"
        )

    @cmd.command()
    async def triforce(self, ctx):
        u = await self.bot.fetch_user(283441304749342720)
        if ctx.message.author.id == 283441304749342720:
            await ctx.send(
                f"The legendary **{u}** represents wisdom, courage, and power. Behold, the might!"
            )
            return

        choice = random.Random(int(ctx.author.id)).choice([1, 2, 3])
        choice = ["courage", "power", "wisdom"][choice - 1]
        await ctx.send(f"**{u}** has spoken. Your affinity is: **{choice}**!")

    @cmd.command(name="blame")
    async def blame(self, ctx, *user):
        if user:
            user = await choose_item(ctx, "member", ctx.guild, " ".join(user).lower())
        else:
            user = ctx.author
        if not user:
            raise cmd.BadArgument("You must specify a user to blame!")

        if user.id == ctx.author.id and user.id != self.immo:
            raise cmd.BadArgument(
                "You cannot blame yourself. Whatever it was, it was not your fault. :pensive:"
            )

        now = arrow.utcnow()
        next_blame = await self.bot.db.hget("blame:last", ctx.author.id)
        if next_blame is None:
            next_blame = now
        else:
            next_blame = arrow.get(next_blame)
        if now < next_blame and ctx.author.id != self.immo:
            raise cmd.BadArgument("Please wait an hour between casting blames.")
        if ctx.author.id != self.immo:
            await self.bot.db.hset(
                "blame:last", ctx.author.id, now.shift(hours=1).timestamp
            )
        await self.bot.db.zincrement("blames", user.id)
        await self.bot.db.zincrement("blames", self.immo)
        if self.immo == user.id:
            await self.bot.db.zincrement("immo", now.format("YYYYMMDD"))
        await self.bot.db.zincrement("immo", now.format("YYYYMMDD"))

        blames = await self.bot.db.zscore("blames", user.id)
        plural = "s" if int(blames) != 1 else ""
        await ctx.send(f"{user} has been blamed {blames} time{plural}!")

    @cmd.command(name="blames")
    async def blames(self, ctx, *user):
        if user:
            user = await choose_item(ctx, "member", ctx.guild, " ".join(user).lower())
        else:
            user = ctx.author

        blames = await self.bot.db.zscore("blames", user.id)

        if not blames:
            blames = "0"
        plural = "s" if int(blames) != 1 else ""
        await ctx.send(f"{user} has been blamed {blames} time{plural}!")

    @cmd.command(name="immo", aliases=["immovality"])
    async def _immo(self, ctx, period: str = "day"):
        if period.lower() not in "day week month year".split():
            raise cmd.BadArgument(
                "Immo means blamed, not immortal! Timespan must be one of: {}".format(
                    ", ".join("day week month year".split())
                )
            )
        mapper = dict(day=0, week=7, month=30, year=365)
        back_to = arrow.utcnow().shift(days=mapper[period.lower()])
        count = 0
        _, scores = await self.bot.db.zscan("immo")
        scores = dict(zip(scores[0::2], scores[1::2]))
        for score, val in scores.items():
            if arrow.get(score) <= back_to:
                count += int(val)
        immo = self.bot.get_user(self.immo)
        plural = "s" if count != 1 else ""
        await ctx.send(
            f"{immo} has been blamed {count} time{plural} in the last {period.lower()}!"
        )


def setup(bot):
    bot.add_cog(PatronModule(bot))
