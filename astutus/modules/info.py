from discord.ext import commands as cmd
import psutil
import arrow
import discord
from astutus.utils import MemberID, download_image


class InfoModule(cmd.Cog):
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

    @cmd.group()
    async def info(self, ctx):
        pass

    @info.command(name="bot")
    @cmd.guild_only()
    async def info_bot(self, ctx: cmd.Context):
        mem = self.process.memory_full_info().uss / 1024 ** 2
        cpu = self.process.cpu_percent() / psutil.cpu_count()
        result = "**Bot Information**:\nCPU - {:.2f}%\nRAM - {:.2f}M\n".format(cpu, mem)
        await ctx.send(result)

    @info.command(name="db")
    @cmd.guild_only()
    async def info_db(self, ctx: cmd.Context):
        size = await self.bot.db.size()
        await ctx.send(f"Current database size: **{size}**")


def setup(bot):
    bot.add_cog(InfoModule(bot))
