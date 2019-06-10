import discord
import arrow
from typing import List, Optional
from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from astutus.utils import checks, Truthy

AVAILABLE_SETTINGS = [
    "censor",
    "logging",
    "modlog",
    "autokick",
    "autoban",
    "autorole",
    "welcome",
    "goodbye",
]


class SettingsKey(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        if arg.lower() not in AVAILABLE_SETTINGS:
            await ctx.send(f"**{arg}** is not a valid server setting.")
            raise cmd.BadArgument
        if arg == "censor" and not checks.is_mod():
            raise cmd.BadArgument
        return arg.lower()


class SettingsModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command(name="settings", aliases=["set"])
    async def settings(self, ctx, setting: SettingsKey, value: Optional):
        return

    @cmd.command(name="toggle")
    @checks.is_mod()
    async def toggle(self, ctx, setting: SettingsKey, value: Optional[Truthy]):
        if value == None:
            value = await self.bot.db.hget(f"{ctx.guild.id}:toggle", setting)
            await ctx.send(
                "**{}** is currently **{}**.".format(
                    setting, int(value) and "on" or "off"
                )
            )
            return
        await self.bot.db.hset(f"{ctx.guild.id}:toggle", setting, value)
        await ctx.send(
            "**{}** is now **{}**".format(setting, int(value) and "on" or "off")
        )


def setup(bot):
    cog = SettingsModule(bot)
    bot.add_cog(cog)
