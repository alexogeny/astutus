from discord.ext import commands as cmd
from .utils import checks


class PremiumModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command()
    @checks.is_premium_user()
    async def premium(self, ctx):
        await ctx.send("You have premium! Yay!!!")


def setup(bot):
    bot.add_cog(PremiumModule(bot))
