from discord.ext import commands as cmd
from astutus.utils import checks, MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta


class XPModule(object):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.xp_tracker = {}
        self.level_map = {
            i + 1: x
            for i, x in enumerate(
                floor(lvl * 10 + pow(lvl, 2.43)) for lvl in range(120)
            )
        }

    async def on_message(self, message):
        author = message.author
        if author.bot:
            return
        now = arrow.utcnow()
        if (self.xp_tracker.get(author.id, now - timedelta(seconds=40))) <= (
            now - timedelta(seconds=30)
        ):
            await self.bot.db.zincrement("xp:global", author.id)
