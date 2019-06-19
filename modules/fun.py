from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta


class FunModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="cookie", aliases=["kookie"])
    async def cookie(self, ctx, user: MemberID):
        """Give people cookies."""
        if not user:
            return
        if user == ctx.author.id:
            await ctx.send("You cannot give yourself a cookie, **{ctx.author}**")
            return


def setup(bot):
    bot.add_cog(FunModule(bot))
