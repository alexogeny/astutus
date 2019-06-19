import discord
import arrow
from typing import List, Optional
from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from utils import checks, Truthy
from string import ascii_letters, digits

AVAILABLE_SETTINGS = [
    "censor",
    "logging",
    "modlog",
    "autokick",
    "autoban",
    "autorole",
    "greet",
    "prefix",
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
    """Set all the things that you need to set with this module. This includes toggling functions on and off, as well as setting a custom bot prefix."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.group(name="settings", aliases=["set", "setting"], invoke_without_command=True)
    async def settings(self, ctx, setting: SettingsKey, value: Optional):
        return

    @settings.command(name="prefix")
    @checks.is_mod()
    async def prefix(self, ctx, *, prefix=None):
        pfx_set = await self.bot.db.hget(f"{ctx.guild.id}:set", "pfx")
        if not prefix or prefix is None:
            await ctx.send("Current server prefix: **{}**".format(pfx_set or ";"))
            return
        if len(prefix) > 2:
            raise cmd.BadArgument(
                "Custom prefix must be **1** to **2** characters in length."
            )
        if any([p for p in prefix if p in ascii_letters + digits]):
            raise cmd.BadArgument(
                "Custom prefix must be a non-letter, non-number character."
            )
        await self.bot.db.hset(f"{ctx.guild.id}:set", "pfx", prefix)
        await ctx.send(f"Set the custom server prefix to **{prefix}**")

    @settings.command(name="autorole")
    @checks.is_mod()
    async def autorole(self, ctx, role: Optional[cmd.RoleConverter] = None):
        if not role:
            raise cmd.BadArgument("You need to supply a role.")
        await self.bot.db.hset(f"{ctx.guild.id}:set", "autorole", role.id)
        await ctx.send(f"Set the autorole to @**{role}**!")

    @settings.command(name="greet", aliases=["welcome"])
    @checks.is_mod()
    async def greet(self, ctx, *message):
        msg = " ".join(message)
        if len(msg) > 140:
            raise cmd.BadArgument(
                "Greets are limited to 140 characters. Please choose a smaller message."
            )
        await self.bot.db.hset(f"{ctx.guild.id}:set", "grt", msg)
        await self.bot.db.hset(f"{ctx.guild.id}:set", "grtc", ctx.channel.id)
        await ctx.send(
            msg.format(
                user=str(ctx.author), server=str(ctx.guild), mention=ctx.author.mention
            )
        )

    @settings.command(name="goodbye", aliases=["depart", "fairwell"])
    @checks.is_mod()
    async def goodbye(self, ctx, *message):
        msg = " ".join(message)
        if len(msg) > 140:
            raise cmd.BadArgument(
                "Goodbyes are limited to 140 characters. Please choose a smaller message."
            )
        await self.bot.db.hset(f"{ctx.guild.id}:set", "dpt", msg)
        await self.bot.db.hset(f"{ctx.guild.id}:set", "dptc", ctx.channel.id)
        await ctx.send(
            msg.format(
                user=str(ctx.author), server=str(ctx.guild), mention=ctx.author.mention
            )
        )

    @cmd.command(name="toggle")
    @checks.is_mod()
    async def toggle(self, ctx, setting: SettingsKey, value: Optional[Truthy]):
        "Toggle a function of the bot on or off. Everything defaults to off."
        if value == None:
            value = await self.bot.db.hget(f"{ctx.guild.id}:toggle", setting)
            value = value is None and "off" or value == "0" and "off" or "on"
            await ctx.send("**{}** is currently **{}**.".format(setting, value))
            return
        await self.bot.db.hset(f"{ctx.guild.id}:toggle", setting, value)
        await ctx.send(
            "**{}** is now **{}**".format(setting, int(value) and "on" or "off")
        )


def setup(bot):
    cog = SettingsModule(bot)
    bot.add_cog(cog)
