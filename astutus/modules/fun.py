from discord.ext import commands as cmd
from astutus.utils import checks, MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta


class FunModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(FunModule(bot))
