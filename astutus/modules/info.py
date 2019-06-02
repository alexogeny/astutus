from discord.ext import commands as cmd

import time
import arrow
import discord
from astutus.utils import MemberID, download_image


class InfoModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command()
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


def setup(bot):
    bot.add_cog(InfoModule(bot))
