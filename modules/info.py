from discord.ext import commands as cmd
import psutil
import arrow
import discord
from .utils.converters import MemberID
from .utils.etc import download_image


class InfoModule(cmd.Cog):
    """Find information on the bot, users, and other things, like if the bot has a custom prefix set."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.process = psutil.Process()

    @cmd.command()
    @cmd.cooldown(1, 30, cmd.BucketType.user)
    async def avatar(self, ctx, user: MemberID = None):
        if user == None:
            user = ctx.author.id
        async with ctx.typing():
            user_profile = await self.bot.fetch_user(user)
            base, _ = str(user_profile.avatar_url).split("?")
            name, ext = ".".join(base.split(".")[:-1]), base.split(".")[-1]
            if user_profile.is_avatar_animated():
                ext = "gif"
            discord_file = discord.File(
                await download_image(f"{name}.{ext}"),
                filename=f"{user_profile}_avatar.{ext}",
            )
        await ctx.send(content=f"**{user_profile}**'s avatar:", file=discord_file)

    @cmd.command()
    async def prefix(self, ctx):
        "Show's the bot's current prefix for this guild."
        cstm = await self.bot.db.hget(f"{ctx.guild.id}:set", "pfx")
        if not cstm or cstm is None:
            cstm = ""
        await ctx.send(
            "You can summon me with: **{}**{}".format(
                self.bot.config["DEFAULT"]["prefix"], cstm and f" or **{cstm}**" or ""
            )
        )

    @cmd.command(name="botinfo")
    @cmd.guild_only()
    async def info_bot(self, ctx: cmd.Context):
        mem = self.process.memory_full_info().uss / 1024 ** 2
        cpu = self.process.cpu_percent() / psutil.cpu_count()
        prem = await self.bot.db.hgetall("premium")
        result = "**Bot Information**:\nCPU - {:.2f}%\nRAM - {:.2f}M\nPremium servers - {}".format(
            cpu, mem, len(prem)
        )
        await ctx.send(result)

    @cmd.command(name="db")
    @cmd.guild_only()
    async def dbinfo(self, ctx: cmd.Context):
        size = await self.bot.db.size()
        await ctx.send(f"Current database size: **{size}**")


def setup(bot):
    bot.add_cog(InfoModule(bot))
