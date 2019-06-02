from pathlib import Path
from discord.ext import commands as cmds
import datetime
import asyncio
import discord


async def prefix_callable(bot, message) -> list:
    user_id = bot.user.id
    prefix_base = [f"<@!{user_id}", f"<@{user_id}"]
    if message.guild is not None:
        prefix_base.extend(
            bot.prefixes.get(message.guild.id, [bot.config["DEFAULT"]["prefix"]])
        )
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
        for module in Path("./astutus/modules").rglob("*.py"):
            module = str(module).replace(".py", "").replace("\\", ".")
            try:
                self.load_extension(module)
            except:
                print(f"Failed to load ext: {module}")
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
        super().run(self.config["DEFAULT"]["token"], reconnect=True)
