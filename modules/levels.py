from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta


class LevelsModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        # self.xp_tracker = {}
        # self.lvl_tracker = {}
        self.level_map = {
            i + 1: x
            for i, x in enumerate(
                floor(lvl * 10 + pow(lvl, 2.43)) for lvl in range(150)
            )
        }

    async def get_xp(self, key, id):
        uxp = await self.bot.db.zscore(key, id)
        if not uxp or uxp == "0":
            uxp = 0
        return int(uxp)

    async def get_user_xp(self, ctx, user):
        if user is None:
            user = ctx.author.id
        uxp = await self.get_xp("xp:gl", user)
        user = await self.bot.fetch_user(user)
        return uxp, user

    async def get_user_level(self, user_xp):
        lvl = max(next((k for k, v in self.level_map.items() if v > user_xp), 1), 1)
        nxt = self.level_map[lvl] - user_xp
        return lvl - 1, nxt

    @checks.is_bot_owner()
    @cmd.command(name="setxp", hidden=True)
    async def setxp(self, ctx, user: MemberID, amount: int):
        user = await self.bot.fetch_user(user)
        await self.bot.db.zadd("xp:gl", user.id, amount)
        await ctx.send(f":white_check_mark: Updated **{user}** xp to **{amount}**")

    @cmd.command()
    async def xp(self, ctx, user: MemberID = None):
        user_xp, user = await self.get_user_xp(ctx, user)
        await ctx.send(f"@**{user}** has **{user_xp}** xp!")

    @cmd.command()
    async def rank(self, ctx, user: MemberID = None):
        user_xp, user = await self.get_user_xp(ctx, user)
        rank = await self.bot.db.zrank("xp:gl", user.id)
        if not user_xp:
            user_xp = 0
            rank = "unknown"
        else:
            rank = rank + 1
        await ctx.send(f"@**{user}** has **{user_xp}**xp. Rank **{rank}**!")

    @cmd.command(aliases=["lvl"])
    async def level(self, ctx, user: MemberID = None):
        user_xp, user = await self.get_user_xp(ctx, user)
        lvl, nxt = await self.get_user_level(user_xp)
        await ctx.send(f"@**{user}** is level **{lvl}**. **{nxt}** to next level!")

    @cmd.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if author.bot:
            return
        now = arrow.utcnow()
        last_xp = await self.bot.db.hget("lvl:cd", author.id)
        if last_xp is None:
            last_xp = now.shift(seconds=-40)
        else:
            last_xp = arrow.get(last_xp)
        if last_xp <= now.shift(seconds=-20):
            uxp = await self.get_xp("xp:gl", author.id)
            lvl, _ = await self.get_user_level(uxp)
            last_level = await self.bot.db.hget("lvl:ls", author.id)
            if last_level is None:
                await self.bot.db.hset("lvl:ls", author.id, lvl)
                last_level = lvl
            last_level = int(last_level)
            await self.bot.db.zincrement("xp:gl", author.id)
            await self.bot.db.hset("lvl:cd", author.id, now.timestamp)
            nxt, _ = await self.get_user_level(uxp + 1)
            if last_level != nxt:
                await message.channel.send(
                    f"GG @**{author}**, you just leveled up to **{nxt}**!"
                )
                await self.bot.db.hset("lvl:ls", author.id, nxt)


def setup(bot):
    bot.add_cog(LevelsModule(bot))
