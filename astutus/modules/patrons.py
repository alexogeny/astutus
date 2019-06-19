from discord.ext import commands as cmd
from ..utils import checks, MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta
import asyncio
import random


class PatronModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command()
    async def bae(self, ctx):
        if ctx.message.author.id != 514905469094068253:
            await ctx.send("Oh, you are not bae ...")
            return
        await ctx.send("OMG, HI BAE!!")

    @cmd.command()
    async def pleb(self, ctx):
        if ctx.author.id != 254710997225308181:
            await ctx.send("You are not enough of a pleb to use this command :<")
            return
        u = await self.bot.fetch_user(254710997225308181)
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


def setup(bot):
    bot.add_cog(PatronModule(bot))
