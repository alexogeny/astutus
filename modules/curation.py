from typing import Optional
from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import ChannelID
from .utils.time import Duration


class CurationModule(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(CurationModule(bot))
