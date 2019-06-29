import discord
import arrow
from typing import List, Optional
from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from .utils import checks
from .utils.converters import MemberID, ActionReason, BannedMember
from .utils.time import Duration, get_hms

from itertools import chain, zip_longest


class TimerModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.timer_timer.start()

    def cog_unload(self):
        self.timer_timer.cancel()

    @tsk.loop(seconds=6)
    async def timer_timer(self):
        now = arrow.utcnow()
        for guild in self.bot.guilds:
            to_action = await self.bot.db.zbyscore(
                f"{guild.id}:timer",
                now.shift(seconds=-6).timestamp,
                now.timestamp,
                withscores=True,
            )
            if to_action:
                clusters = dict(zip_longest(*[iter(to_action)] * 2, fillvalue=None))
                for action, time in clusters.items():
                    m, c, _ = action.split(".")
                    m, c = guild.get_member(int(m)), guild.get_channel(int(c))
                    if m != None and c != None:
                        t = arrow.get(time)
                        n = await self.bot.db.zscore(f"{guild.id}:timert", action)
                        narr = arrow.get(n)
                        delta = t - narr
                        _h, _m, _s = await get_hms(delta)
                        await c.send(
                            ":alarm_clock: Bzzt! Hey {}, the timer you set {}{}{}ago has gone off!".format(
                                m.mention,
                                _h and f"**{_h}** hour{_h > 1 and 's' or ''}, " or "",
                                _m and f"**{_m}** minute{_m > 1 and 's' or ''}, " or "",
                                _s and f"**{_s}** second{_s > 1 and 's' or ''} " or "",
                            )
                        )
                        await self.bot.db.zrem(f"{guild.id}:timert", action)
                await self.bot.db.zrembyscore(
                    f"{guild.id}:timer", now.shift(seconds=-6).timestamp, now.timestamp
                )

    @timer_timer.before_loop
    async def before_timer_timer(self):
        await self.bot.wait_until_ready()

    @cmd.command()
    @cmd.guild_only()
    async def timer(
        self, ctx: cmd.Context, duration: Optional[Duration], *, reason: str = None
    ):
        arr = arrow.utcnow()
        if duration is None or not duration:
            duration = arr.shift(minutes=1)
        if duration < arr:
            await ctx.send("Are you a time traveler? Set your timers for the future.")
            raise cmd.BadArgument
        _, slots = await self.bot.db.zscan(
            f"{ctx.guild.id}:timer", match=f"{ctx.author.id}."
        )
        slots = dict(zip(slots[0::2], slots[1::2]))
        print(slots)
        if len(slots) > 4:
            raise cmd.BadArgument(f"You can 5 timers per server, **{ctx.author}**.")
        await self.bot.db.zadd(
            f"{ctx.guild.id}:timer",
            f"{ctx.author.id}.{ctx.channel.id}.{ctx.message.id}",
            duration.timestamp,
        )
        await self.bot.db.zadd(
            f"{ctx.guild.id}:timert",
            f"{ctx.author.id}.{ctx.channel.id}.{ctx.message.id}",
            arr.timestamp,
        )
        duration = duration.humanize()
        if duration == "just now":
            duration = "shortly"
        await ctx.send(f"Ok **{ctx.author}**, timer will go off **{duration}**.")


def setup(bot):
    cog = TimerModule(bot)
    bot.add_cog(cog)
