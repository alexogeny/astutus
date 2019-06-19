from pathlib import Path
from discord.ext import commands as cmds
import datetime
import asyncio
import discord
import os


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
        for module in Path("./astutus/modules").rglob("*.py"):
            module = str(module).replace(".py", "").replace("\\", ".")
            try:
                self.load_extension(module)
            except Exception as e:
                print(f"Failed to load ext: {module}")
                print(e)
            else:
                print(f"Loaded ext: {module}")

    async def on_ready(self):
        if not hasattr(self, "booted_at"):
            self.booted_at = datetime.datetime.utcnow()
        oauth = f"https://discordapp.com/api/oauth2/authorize?client_id={self.user.id}&permissions={{}}&scope=bot"
        self.link_admin = oauth.format("8")
        self.link_normal = oauth.format("2146954487")
        print(f"Ready: {self.user} (ID: {self.user.id})")
        print(f"Invite link: {self.link_admin}")
        # discord.opus.load_opus("opus")
        # if discord.opus.is_loaded():
        #     print("Loaded opus")

    async def on_command_error(self, ctx, error):
        if isinstance(error, cmds.CommandOnCooldown):
            cd = round(error.retry_after)
            await ctx.send(
                f"Woah **{ctx.author}**, please cool down a second. Try **{ctx.command.name}** again in **{cd}**s."
            )
        if isinstance(error, cmds.BadArgument):
            await ctx.send(f":negative_squared_cross_mark: {error}")

    async def process_commands(self, message: discord.Message):
        context = await self.get_context(message)
        if context.command is None or context.author.bot:
            return

        await self.invoke(context)

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
