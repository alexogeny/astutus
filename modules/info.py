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
        if user is None:
            user = ctx.author.id
        log = self.bot.get_cog("LoggingModule")
        if user:
            user = self.bot.get_user(user)
        cache = log.avatar_cache
        if not cache.get(str(user.id), None):
            i = await log.upload_to_imgur(
                str(user.avatar_url_as(static_format="png", size=1024)), anon=True
            )
            cache[str(user.id)] = i["link"]
        async with ctx.typing():
            embed = discord.Embed(title=f"**{user}**'s avatar")
            embed.set_image(url=cache[str(user.id)])
            await ctx.send(embed=embed)

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

    @cmd.group(name="info", invoke_without_command=True, aliases=["i"])
    async def info(self, ctx):
        return

    @info.command(name="bot")
    @cmd.guild_only()
    async def botinfo(self, ctx: cmd.Context):
        "Get information about the bot!"
        mem = self.process.memory_full_info().uss / 1024 ** 2
        cpu = self.process.cpu_percent() / psutil.cpu_count()
        prem = await self.bot.db.hgetall("premium")
        result = "**Bot Information**:\nCPU - {:.2f}%\nRAM - {:.2f}M\nPremium servers - {}".format(
            cpu, mem, len(prem)
        )
        await ctx.send(result)

    @info.command(name="db")
    @cmd.guild_only()
    async def dbinfo(self, ctx: cmd.Context):
        size = await self.bot.db.size()
        await ctx.send(f"Current database size: **{size}**")


def setup(bot):
    bot.add_cog(InfoModule(bot))
