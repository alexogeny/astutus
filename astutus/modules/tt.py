from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from astutus.utils import Duration, checks, Truthy
from typing import Optional
import arrow
from datetime import datetime


class TTKey(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        if arg.lower() not in [
            "grandmaster",
            "gm",
            "master",
            "captain",
            "knight",
            "recruit",
            "guest",
            "applicant",
            "timer",
            "tier",
            "zone",
            "average",
            "avg",
            "announce",
            "farm",
        ]:
            await ctx.send(f"**{arg}** is not a valid settings key for TT2 module.")
            raise cmd.BadArgument("Bad key for TT2 settings")
        if arg == "average":
            arg == "avg"
        elif arg == "grandmaster":
            arg == "gm"
        if (
            arg in "gmmastercaptainknightrecruitapplicantguest"
            and not checks.can_manage_roles()
        ):
            raise cmd.BadArgument()
        elif arg == "announce" and not checks.can_manage_channels():
            raise cmd.BadArgument()
        return arg.lower()


class TapTitansModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.raid_timer.start()

    @tsk.loop(minutes=1.0)
    async def raid_timer(self):
        return

    @raid_timer.before_loop
    async def before_unban_timer(self):
        await self.bot.wait_until_ready()

    @cmd.group(case_insensitive=True)
    async def tt(self, ctx):
        pass

    @tt.group(name="set")
    @cmd.guild_only()
    async def tt_set(self, ctx, key: TTKey, val):
        if key in "gmmastercaptainknightrecruitapplicantguest":
            val = await cmd.RoleConverter().convert(ctx, val)
            await self.bot.db.hset(f"{ctx.guild.id}:tt", key, val.id)
        elif key == "announce":
            val = await cmd.TextChannelConverter().convert(ctx, val)
            await self.bot.db.hset(f"{ctx.guild.id}:tt", key, val.id)
        elif key in "zonetier":
            try:
                val = int(val)
            except:
                raise cmd.BadArgument(f"Bad value for raid {key}")
            else:
                if not 1 <= val <= 10:
                    raise cmd.BadArgument()
                await self.bot.db.hset(f"{ctx.guild.id}:tt", key, val)
        elif key == "farm":
            val = await Truthy().convert(ctx, val)
            await self.bot.db.hset(f"{ctx.guild.id}:tt", key, val)
        else:
            await self.bot.db.hset(f"{ctx.guild.id}:tt", key, val)
        await ctx.send(f"Set the TT2 **{key}** key to **{val}**")

    @tt.group(name="raid", aliases=["boss", "rd"], case_insensitive=True)
    async def tt_raid(self, ctx, level: cmd.Greedy[int], time: Optional[Duration]):
        roles = (
            await self.bot.db.hget(f"{ctx.guild.id}:tt", "gm"),
            await self.bot.db.hget(f"{ctx.guild.id}:tt", "master"),
            await self.bot.db.hget(f"{ctx.guild.id}:tt", "timer"),
        )
        print(roles)
        if not await checks.user_has_role(
            (str(r.id) for r in ctx.author.roles), *roles
        ):
            raise cmd.BadArgument
        if not level or len(level) == 0 or level == None:
            tier = await self.bot.db.hget(f"{ctx.guild.id}:tt", "tier") or 1
            zone = await self.bot.db.hget(f"{ctx.guild.id}:tt", "zone") or 1
        elif not all(1 <= x <= 10 for x in level):
            await ctx.send("Tier/zone must be between **1** and **10**.")
            raise cmd.BadArgument()
        elif len(level) == 2:
            tier, zone = level
        elif len(level) == 1:
            tier, zone = level, 1
        if not time or time == None:
            time = await Duration().convert(ctx, "24h")
        time = time.humanize()
        if time == "just now":
            time = "now"
        await ctx.send(f"Tier **{tier}**, zone **{zone}** raid starts **{time}**.")

    @tt_raid.command(name="start", aliases=["prep"])
    async def raid_start(self, ctx: cmd.Context, level: str, time: Optional[Duration]):
        if not time or time == None:
            time = arrow.utcnow()

        # get levels from user or clan in db
        # set spawn to 24h from now or the <time> argument
        # add the timer to the internal list and to the db
        # return a statement of confirmation
        return

    @tt_raid.command(name="clear", aliases=["end", "failed", "ended", "cleared"])
    async def raid_clear(self):
        return

    @tt_raid.command(name="info", aliases=["information"])
    async def raid_info(self):
        return

    @tt.group(name="queue", aliases=["q"], case_insensitive=True)
    async def tt_queue(self, cancel: bool = True):
        return

    @tt.group(name="card", case_insensitive=True)
    async def tt_card(self):
        return

    @tt.group(name="deck", case_insensitive=True)
    async def tt_deck(self):
        return

    @tt.group(name="hero", case_insensitive=True)
    async def tt_hero(self):
        return

    @tt.group(name="equip", case_insensitive=True)
    async def tt_equip(self):
        return

    @tt.group(name="artifact", case_insensitive=True)
    async def tt_artifact(self):
        return

    @tt.group(name="enhancement", case_insensitive=True)
    async def tt_enhance(self):
        return

    @tt.group(name="enchant", case_insensitive=True)
    async def tt_enchant(self):
        return

    @tt.group(name="titan", case_insensitive=True)
    async def tt_titan(self):
        return

    @tt.group(name="titanlord", case_insensitive=True)
    async def tt_titanlord(self):
        return

    @tt.group(name="skill", case_insensitive=True)
    async def tt_skill(self):
        return


def setup(bot):
    bot.add_cog(TapTitansModule(bot))
