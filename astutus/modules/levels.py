from discord.ext import commands as cmd
from utils import checks, MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta


class XPModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.xp_tracker = {}
        self.level_map = {
            i + 1: x
            for i, x in enumerate(
                floor(lvl * 10 + pow(lvl, 2.43)) for lvl in range(150)
            )
        }

    @cmd.command()
    async def rank(self, ctx, user: MemberID = None):
        if user is None:
            user = ctx.author.id

        xp = await self.bot.db.zscore("xp:gl", user)
        rank = await self.bot.db.zrank("xp:gl", user)

        if not xp:
            xp = 0
            rank = "unknown"
        else:
            rank = rank + 1

        user = await self.bot.fetch_user(user)
        await ctx.send(f"**{user}** has **{xp}**xp. Rank **{rank}**!")

    @cmd.command(aliases=["lvl"])
    async def level(self, ctx, user: MemberID = None):
        if user is None:
            user = ctx.author.id
        xp = await self.bot.db.zscore("xp:gl", user)
        if not xp:
            xp = 0
        else:
            xp = int(xp)
        lvl = max(next((k for k, v in self.level_map.items() if v > xp), 1), 1)
        nxt = self.level_map[lvl + 1] - xp
        user = await self.bot.fetch_user(user)
        await ctx.send(
            f"@\u200b**{user}** is level **{lvl-1}**. **{nxt}** to next level!"
        )

    @cmd.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if author.bot:
            return
        now = arrow.utcnow()
        if self.xp_tracker.get(author.id, now.shift(seconds=-40)) <= now.shift(
            seconds=-20
        ):
            await self.bot.db.zincrement("xp:gl", author.id)
            self.xp_tracker[author.id] = now


def setup(bot):
    bot.add_cog(XPModule(bot))
