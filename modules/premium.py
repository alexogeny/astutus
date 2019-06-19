from discord.ext import commands as cmd
from .utils import checks


class PremiumModule(cmd.Cog):
    (
        "Elixum premium is available for Patreon supporters and server boosters.\n"
        "Premium users can nominate a server of their choice for premium features.\n"
        "You can become a premium user at <https://patreon.com/lxmcneill>"
    )

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="amipremium")
    @checks.is_premium_user()
    async def premium_user(self, ctx):
        "Shows you if you have preium."
        await ctx.send("You have premium! Yay!!!")

    @cmd.command(name="premium")
    async def premium_server(self, ctx):
        "Shows you if the server is premium."
        await ctx.send("Not a premium server.")


def setup(bot):
    bot.add_cog(PremiumModule(bot))
