import asyncio
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

    @cmd.group(name="premium", invoke_without_command=True)
    async def premium(self, ctx):
        "Shows you if the server is premium."
        prem = await self.bot.db.hget("premium", ctx.guild.id)
        if prem is None or not prem:
            raise cmd.BadArgument("Not a premium server.")
        user = "your" if prem == str(ctx.author.id) else "somebody else's"
        await ctx.send(f":tada: This is {user} premium server!")

    @premium.command(name="add")
    @checks.is_premium_user()
    async def premium_add(self, ctx):
        "Sets the current server to premium, if not already."
        prem = await self.bot.db.hget("premium", ctx.guild.id)
        if prem is not None and ctx.author.id != 305879281580638228:
            if int(prem) == ctx.author.id:
                raise cmd.BadArgument(
                    "This is your premium server.\nIf you would like to register"
                    " a different server, do **{}premium del**".format(ctx.prefix)
                )
            all_prem = await self.bot.db.hgetall("premium")
            if [val for val in all_prem.values() if val == str(ctx.author.id)]:
                raise cmd.BadArgument("You already have a premium server set!")
            raise cmd.BadArgument("This is somebody else's premium server.")
        await ctx.send(
            f"Would you like to set **{ctx.guild}** as your premium server?"
            "\nType **yes** to confirm or **no** to cancel."
        )

        def check(msg):
            return msg.author == ctx.author and msg.content.lower() in ["yes", "no"]

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            raise cmd.BadArgument("Query timed out.")

        if msg.content.lower() == "no":
            raise cmd.BadArgument(
                "Did not set premium server for **{}**.".format(ctx.author)
            )

        await self.bot.db.hset("premium", ctx.guild.id, str(ctx.author.id))
        await ctx.send(
            f":tada: Set **{ctx.author}**'s premium server to **{ctx.guild}**!"
        )


def setup(bot):
    bot.add_cog(PremiumModule(bot))
