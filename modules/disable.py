from typing import Union, Optional
from itertools import chain
import discord
from discord.ext import commands as cmd
from discord.utils import find, get
from .utils import checks


class DisableModule(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_mod()
    @cmd.group(name="disable", aliases=["dis"], invoke_without_command=True)
    async def disable(self, ctx, *, module=None):
        disabled = await self.bot.db.lrange(f"{ctx.guild.id}:disable")
        if not disabled:
            raise cmd.BadArgument(f"No modules disabled. **{ctx.prefix}help disable**")
        await ctx.send(
            "Disabled modules: {}".format(", ".join([f"**{d}**" for d in disabled]))
        )

    @checks.is_mod()
    @disable.command(name="add", aliases=["a"])
    async def disable_add(self, ctx, module):
        if module.lower() in ["disable", "utility"]:
            raise cmd.BadArgument(f"Cannot disable the {module.lower()} module!")
        modules = [str(s).replace("Module", "").lower() for s in self.bot.cogs]
        if module.lower() not in modules:
            raise cmd.BadArgument(
                "Available modules: {}".format(", ".join([f"**{m}**" for m in modules]))
            )
        disabled = await self.bot.db.lrange(f"{ctx.guild.id}:disable")
        if module.lower() in disabled:
            raise cmd.BadArgument("Module already disabled!")
        await self.bot.db.rpush(f"{ctx.guild.id}:disable", module.lower())
        await ctx.send(
            f":white_check_mark: Added **{module.lower()}** to disabled modules!"
        )

    @checks.is_mod()
    @disable.command(name="remove", aliases=["r", "d", "delete", "rem"])
    async def disable_rem(self, ctx, module):
        modules = [str(s).replace("Module", "").lower() for s in self.bot.cogs]
        if module.lower() not in modules:
            raise cmd.BadArgument(
                "Available modules: {}".format(", ".join([f"**{m}**" for m in modules]))
            )
        disabled = await self.bot.db.lrange(f"{ctx.guild.id}:disable")
        if module.lower() not in disabled:
            raise cmd.BadArgument("Module not disabled!")
        await self.bot.db.lrem(f"{ctx.guild.id}:disable", module.lower())
        await ctx.send(
            f":white_check_mark: Removed **{module.lower()}** from disabled modules!"
        )


def setup(bot):
    bot.add_cog(DisableModule(bot))
