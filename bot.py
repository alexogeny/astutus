import datetime
import sys
import os
from os import listdir
from os.path import isfile, join
from itertools import chain
import discord
from discord.ext import commands as cmds
from discord.utils import get
from modules.utils.checks import user_has_role


async def prefix_callable(bot, message) -> list:
    user_id = bot.user.id
    prefix_base = [f"<@!{user_id}> ", f"<@{user_id}> "]
    if message.guild is not None:
        prefix_base.append(bot.config["DEFAULT"]["prefix"])
        custom = await bot.db.hget(f"{message.guild.id}:set", "pfx")
        if custom or custom != None:
            prefix_base.append(custom)
    return prefix_base


class AstutusBot(cmds.AutoShardedBot):
    def __init__(self, config):
        super().__init__(
            command_prefix=prefix_callable,
            description="",
            pm_help=None,
            help_attrs={"hidden": True},
            fetch_offline_members=False,
        )
        self.config = config
        self.exit_code = None
        self.prefixes = {}
        self.db = None
        self.blacklists = dict(users=[], channels=[], servers=[])
        self.remove_command("help")
        self.load_extensions()

    def load_extensions(self):
        extensions = [
            f.replace(".py", "")
            for f in listdir(self.config["DEFAULT"]["cogs"])
            if isfile(join(self.config["DEFAULT"]["cogs"], f))
        ]
        for extension in extensions:
            try:
                self.load_extension(
                    "{}.{}".format(self.config["DEFAULT"]["cogs"], extension)
                )
            except (discord.ClientException, ModuleNotFoundError) as e:
                print(f"Failed to load extension {extension}.", file=sys.stderr)
                # traceback.print_exc()

    async def on_ready(self):
        if not hasattr(self, "booted_at"):
            self.booted_at = datetime.datetime.utcnow()
        oauth = f"https://discordapp.com/api/oauth2/authorize?client_id={self.user.id}&permissions={{}}&scope=bot"
        self.link_admin = oauth.format("8")
        self.link_normal = oauth.format("2146954487")
        print(f"Ready: {self.user} (ID: {self.user.id})")
        print(f"Invite link: {self.link_admin}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, cmds.CommandOnCooldown):
            cd = round(error.retry_after)
            await ctx.send(
                f"Woah **{ctx.author}**, please cool down a second. Try **{ctx.command.name}** again in **{cd}**s."
            )
        if isinstance(error, cmds.BadArgument):
            await ctx.send(f":negative_squared_cross_mark: {error}")

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message)
        if ctx.command is None or ctx.author.bot:
            return

        restrictions = await ctx.bot.db.hget(f"{ctx.guild.id}:toggle", "restrictions")
        if restrictions == "1":
            mode = await ctx.bot.db.hget(f"{ctx.guild.id}:set", "rmode")
            cog = ctx.bot.get_cog("RestrictionsModule")
            _, chan, role, mem = await cog.get_restrictions(
                ctx.guild, ctx.command.qualified_name
            )
            chans = [get(ctx.guild.channels, id=int(c)) for c in chan]
            roles = [get(ctx.guild.roles, id=int(c)) for c in role]
            membs = [get(ctx.guild.members, id=int(c)) for c in mem]
            if not any([chans, roles, membs]):
                await self.invoke(ctx)
                return
            chan_perm = ctx.channel in chans or False
            role_perm = (
                await user_has_role(
                    [r.id for r in ctx.author.roles], *[r.id for r in roles]
                )
                or False
            )
            memb_perm = ctx.author in membs or False
            if mode == "and":
                if all([chan_perm, role_perm, memb_perm]):
                    await self.invoke(ctx)
                    return
                # else:
                rolmem = list(chain.from_iterable((roles, membs)))
                text = "**{}** can only be used".format(ctx.command.qualified_name)
                if chans:
                    text = text + " in " + ", ".join([f"**#{x}**" for x in chans])
                if rolmem:
                    text = text + " by " + ", ".join([f"**@{x}**" for x in rolmem])
                await ctx.send(text)
                return
            if not any([chan_perm, role_perm, memb_perm]):
                text = "**{}** can be used if:\n".format(ctx.command.qualified_name)
                res = []
                if chans:
                    res.append("are in " + ", ".join([f"**#{x}**" for x in chans]))
                if roles:
                    res.append(
                        "have the role " + ", ".join([f"**@{x}**" for x in roles])
                    )
                if membs:
                    res.append("are " + ", ".join([f"**@{x}**" for x in membs]))
                res = [f"- you {r}" for r in res]
                await ctx.send(
                    ":negative_squared_cross_mark: {}{}".format(
                        text, "; or\n".join(res)
                    )
                )
                return
        await self.invoke(ctx)

    async def on_message(self, message: discord.Message):
        await self.process_commands(message)

    async def stop(self, exit_code: int = 0, force: bool = False):
        if force:
            import sys

            sys.exit(exit_code)
        self.db.disconnect()
        self.loop.stop()
        self.exit_code = exit_code

    def run(self):
        token = self.config["DEFAULT"].get("token", os.environ.get("DISCORD_TOKEN", ""))
        super().run(token, reconnect=True)
