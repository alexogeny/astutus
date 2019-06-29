import discord
import arrow
from typing import List, Optional
from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from .utils import checks
from .utils.converters import Truthy
from string import ascii_letters, digits

AVAILABLE_SETTINGS = [
    "censor",
    "logging",
    "modlog",
    "autokick",
    "autoban",
    "autorole",
    "greet",
    "goodbye",
    "prefix",
    "restrictions",
]


class SettingsKey(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        if arg.lower() not in AVAILABLE_SETTINGS:
            raise cmd.BadArgument(f"**{arg}** is not a valid server setting.")
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

    @settings.command(name="role")
    @checks.is_mod()
    async def role(self, ctx, roletype, role: Optional[cmd.RoleConverter] = None):
        if not ctx.guild.me.guild_permissions.manage_roles:
            raise cmd.BotMissingPermissions(("Manage Roles",))
        roletypes = "auto muted jailed curator".split()
        if roletype.lower() not in roletypes:
            raise cmd.BadArgument(
                "**Role type** must be one of: {}".format(
                    ", ".join([f"**{l}**" for l in roletypes])
                )
            )
        if role is None:
            raise cmd.BadArgument("Could not find a role with that name.")
        await self.bot.db.hset(f"{ctx.guild.id}:set", f"role{roletype}", role.id)
        await ctx.send(f":white_check_mark: Set **{roletype} role** to @**{role}**")

    @settings.command(name="logging", aliases=["log"])
    @checks.is_mod()
    async def logging(
        self, ctx, logtype, channel: Optional[cmd.TextChannelConverter] = None
    ):
        logtypes = "joins leaves edits deletes avatars channels roles pins".split()
        if logtype.lower() not in logtypes:
            raise cmd.BadArgument(
                "**Log type** must be one of: {}".format(
                    ", ".join([f"**{l}**" for l in logtypes])
                )
            )
        if channel is None:
            raise cmd.BadArgument("Could not find channel with that name.")
        await self.bot.db.hset(f"{ctx.guild.id}:set", f"log{logtype}", channel.id)
        await ctx.send(
            f":white_check_mark: Set **log{logtype}** channel to #**{channel}**!"
        )
        print(ctx.bot.permissions)

    @settings.command(name="greet", aliases=["welcome"])
    @checks.is_mod()
    async def greet(self, ctx, key: str = "message", *message):
        if key.lower().startswith("m"):
            msg = " ".join(message)
            if len(msg) > 140:
                raise cmd.BadArgument(
                    "Greets are limited to 140 characters. Please choose a smaller message."
                )
            await self.bot.db.hset(f"{ctx.guild.id}:set", "grt", msg)
            await ctx.send(
                msg.format(
                    user=str(ctx.author),
                    server=str(ctx.guild),
                    mention=ctx.author.mention,
                )
            )
        elif key.lower().startswith("c"):
            await self.bot.db.hset(f"{ctx.guild.id}:set", "grtc", ctx.channel.id)
            await ctx.send(f"Set greet channel to #**{ctx.channel}**")

    @settings.command(name="goodbye", aliases=["depart", "fairwell"])
    @checks.is_mod()
    async def goodbye(self, ctx, key: str = "message", *message):
        if key.lower().startswith("m"):
            msg = " ".join(message)
            if len(msg) > 140:
                raise cmd.BadArgument(
                    "Goodbyes are limited to 140 characters. Please choose a smaller message."
                )
            await self.bot.db.hset(f"{ctx.guild.id}:set", "dpt", msg)
            await ctx.send(
                msg.format(
                    user=str(ctx.author),
                    server=str(ctx.guild),
                    mention=ctx.author.mention,
                )
            )
        elif key.lower().startswith("c"):
            channel = await cmd.TextChannelConverter().convert(ctx, " ".join(message))
            if not channel:
                raise cmd.BadArgument(
                    f"Could not find channel: #**{' '.join(message)}**"
                )
            await self.bot.db.hset(f"{ctx.guild.id}:set", "dptc", channel.id)
            await ctx.send(f"Set goodbye channel to #**{channel}**")

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
