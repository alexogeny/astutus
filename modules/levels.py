from discord.ext import commands as cmd
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember
import arrow
from math import floor
from datetime import timedelta
from typing import Optional, Union
from random import choice
import discord


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

    async def get_user_xp(self, ctx, user, where="gl"):
        if user is None:
            user = ctx.author.id
        uxp = await self.get_xp(f"xp:{where}", user)
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

    @checks.is_mod()
    @cmd.command(name="xpignore", aliases=["xpig"])
    async def xp_ignore(
        self, ctx, *to_ignore: Union[cmd.TextChannelConverter, cmd.MemberConverter]
    ):
        if not to_ignore:
            raise cmd.BadArgument("You need to specify a channel or user to ignore!")
        ignored = await self.bot.db.lrange(f"{ctx.guild.id}:xp:ign")
        i = 0
        for ign in to_ignore:
            if not str(ign.id) in ignored:
                await self.bot.db.rpush(f"{ctx.guild.id}:xp:ign", str(ign.id))
                i += 1
        plural = "s" if i != 1 else ""
        await ctx.send(f"Added **{i}** item{plural} to XP ignore!")

    @checks.is_mod()
    @cmd.command(name="xpunignore", aliases=["xpun"])
    async def xp_unignore(
        self, ctx, *to_unignore: Union[cmd.TextChannelConverter, cmd.MemberConverter]
    ):
        if not to_unignore:
            raise cmd.BadArgument("You need to specify a channel or user to unignore!")
        ignored = await self.bot.db.lrange(f"{ctx.guild.id}:xp:ign")
        if ignored is None or not ignored:
            raise cmd.BadArgument("Nothing in XP ignore list!")
        i = 0
        for ign in to_unignore:
            if str(ign.id) in ignored:
                await self.bot.db.lrem(f"{ctx.guild.id}:xp:ign", str(ign.id))
                i += 1
        plural = "s" if i != 1 else ""
        await ctx.send(f"Remove **{i}** item{plural} from XP ignore!")

    @cmd.command()
    async def xp(self, ctx, user: Optional[MemberID] = None, where: str = "here"):
        to_get = "gl" if where == "global" else ctx.guild.id
        user_xp, user = await self.get_user_xp(ctx, user, where=to_get)
        where = f" in **{ctx.guild}**" if where == "here" else ""
        await ctx.send(f"@**{user}** has **{user_xp}** xp{where}!")

    @cmd.command(name="leaderboard", aliases=["ldb", "lb"])
    async def ldb(self, ctx, where: str = "here"):
        to_get = "gl" if where == "global" else ctx.guild.id
        top = await self.bot.db.ztop(f"xp:{to_get}", stop=9)
        top = dict(zip(top[0::2], top[1::2]))
        top_res = []
        for i, top_user in enumerate(list(top.keys())):
            user = self.bot.get_user(int(top_user))
            if user is None:
                user = await self.bot.fetch_user(int(top_user))
            top_res.append(f"{i+1}. {user} - {top[top_user]}xp")
        where = ctx.guild if where == "here" else "Global"
        user_xp, user = await self.get_user_xp(ctx, ctx.author.id, where=to_get)
        rank = await self.bot.db.zrank(f"xp:{to_get}", user.id)
        if not user_xp:
            user_xp = 0
            rank = "unknown"
        else:
            rank = rank + 1
        emoji = ":earth_{}:".format(choice("americas asia africa".split()))
        embed = discord.Embed(title=f"{emoji} {where} leaderboard")
        top_css = "```css\n{}\n```".format("\n".join(top_res))
        embed.add_field(name="Top 10", value=top_css, inline=False)
        embed.add_field(
            name="My Rank",
            value="```css\n{}. {} - {}xp\n```".format(rank, ctx.author, user_xp),
        )
        if where != "Global":
            log = self.bot.get_cog("InfoModule")
            img = await log.get_or_upload_guildicon(ctx.guild)
            embed.set_thumbnail(url=img)
        else:
            embed.set_thumbnail(url="https://i.imgur.com/q2I08K7.png")
        await ctx.send(embed=embed)

    @cmd.command()
    async def rank(self, ctx, user: Optional[MemberID] = None, where: str = "here"):
        to_get = "gl" if where == "global" else ctx.guild.id
        user_xp, user = await self.get_user_xp(ctx, user, where=to_get)
        rank = await self.bot.db.zrank(f"xp:{to_get}", user.id)
        if not user_xp:
            user_xp = 0
            rank = "unknown"
        else:
            rank = rank + 1
        where = ctx.guild if where == "here" else "Global"
        await ctx.send(f"@**{user}** has **{user_xp}**xp. **{where}** rank **{rank}**!")

    @cmd.command(aliases=["lvl"])
    async def level(self, ctx, user: MemberID = None):
        user_xp, user = await self.get_user_xp(ctx, user)
        lvl, nxt = await self.get_user_level(user_xp)
        await ctx.send(f"@**{user}** is level **{lvl}**. **{nxt}** to next level!")

    @cmd.Cog.listener()
    async def on_message(self, message):
        author = message.author
        if author.bot or not hasattr(message, "guild"):
            return
        ignored = await self.bot.db.lrange(f"{message.guild.id}:xp:ign")
        if ignored is None:
            ignored = []

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
            if (
                str(message.author.id) not in ignored
                and str(message.channel.id) not in ignored
            ):
                await self.bot.db.zincrement(f"xp:{message.guild.id}", author.id)
            await self.bot.db.hset("lvl:cd", author.id, now.timestamp)
            nxt, _ = await self.get_user_level(uxp + 1)
            if last_level != nxt:
                await message.channel.send(
                    f"GG @**{author}**, you just leveled up to **{nxt}**!"
                )
                await self.bot.db.hset("lvl:ls", author.id, nxt)


def setup(bot):
    bot.add_cog(LevelsModule(bot))
