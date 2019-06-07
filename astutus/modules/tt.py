from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from astutus.utils import Duration, checks, Truthy, get_hms
from typing import Optional
import asyncio
import arrow
from datetime import datetime
from itertools import zip_longest


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
            "mode",
            "depl",
            "lastq"
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


class TTRaidGroup(cmd.Converter):
    async def convert(self, ctx, arg):
        if arg[0] != "g" or arg[1] not in ("1", "2", "3"):
            raise cmd.BadArgument()
        elif arg == "gm":
            raise cmd.BadArgument()
        else:
            return f"{ctx.guild.id}:tt:{arg[1]}"


class TapTitansModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.raid_timer.start()

    def cog_unload(self):
        self.raid_timer.cancel()

    async def get_roles(self, groupdict, *roles):
        return [int(groupdict.get(r, 0)) for r in roles]

    async def get_raid_group_or_break(self, group, ctx):
        test = await self.bot.db.exists(group)
        if not test:
            await ctx.send(
                "Looks like there are not any raid groups. Set one up by ;tt group add"
            )
            raise cmd.BadArgument()
        return group

    async def has_timer_permissions(self, ctx, groupdict):
        roles = await self.get_roles(groupdict, *["gm", "master", "timer"])
        if not any(roles):
            await ctx.send(
                "Looks like no clan roles are set up. Anyone with manage guild *and* manage roles permission can do this."
            )
            raise cmd.BadArgument
        if not await checks.user_has_role([r.id for r in ctx.author.roles], *roles):
            raise cmd.BadArgument

    async def has_clan_permissions(self, ctx, groupdict):
        roles = await self.get_roles(
            groupdict, *["gm", "master", "captain", "knight", "recruit"]
        )
        if not await checks.user_has_role([r.id for r in ctx.author.roles], *roles):
            raise cmd.BadArgument

    async def has_admin_or_mod_or_master(self, ctx, groupdict):
        is_admin = await checks.user_has_admin_perms(ctx.author, ctx.guild)
        if is_admin:
            return True
        is_mod = await checks.user_has_mod_perms(ctx.author, ctx.guild)
        if is_mod:
            return True
        roles = await self.get_roles(groupdict, *["gm", "master"])
        if not await checks.user_has_role((r.id for r in ctx.author.roles), *roles):
            raise cmd.BadArgument
        if not is_mod and not is_admin:
            raise cmd.BadArgument

    @tsk.loop(seconds=5)
    async def raid_timer(self):
        now = arrow.utcnow()
        future = now.shift(hours=50)
        await asyncio.gather(
            *(self.update_raid_timer(guild, now, future) for guild in self.bot.guilds)
        )

    async def update_raid_timer(self, guild, now, future):
        await asyncio.gather(
            *(self.update_timer_group(guild, now, future, g) for g in [1, 2, 3]),
            return_exceptions=True,
        )

    async def update_timer_group(self, guild, now, future, group):
        exists = await self.bot.db.exists(f"{guild.id}:tt:{group}")
        if not exists:
            raise asyncio.CancelledError
        g = await self.bot.db.hgetall(f"{guild.id}:tt:{group}")
        spawn = g.get("spawn", 0)
        cd = g.get("cd", 0)
        if not any([spawn, cd]):
            raise asyncio.CancelledError
        if (
            spawn
            and not now < arrow.get(spawn or future.timestamp)
            or cd
            and not now < arrow.get(cd or future.timestamp)
        ):
            # print('timer below zero')
            await self.update_timer_queue(guild, now, future, group, g)
            raise asyncio.CancelledError
        c = int(g.get("announce", 0))
        if not c:
            raise asyncio.CancelledError
        chan = guild.get_channel(c)
        if not chan:
            raise asyncio.CancelledError
        reset = g.get("reset", 0)
        if not reset and not cd:
            reset = "start"
        elif cd:
            reset = "cooldown end"
        else:
            reset = f"reset #**{reset}** start"
        if spawn:
            dt = arrow.get(spawn) - now
        elif cd:
            dt = arrow.get(cd) - now
        _h, _m, _s = await get_hms(dt)
        content = "Raid {}s in **{:02}**h **{:02}**m **{:02}**s.".format(
            reset, _h, _m, _s
        )
        message = int(g.get("edit", 0))
        if message:
            await self.update_timer_message(chan, message, content)
        else:
            await chan.send(content)

    async def update_timer_queue(self, guild, now, future, group, g):
        q = await self.bot.db.lrange(f"{guild.id}:tt:{group}:q")
        spawn = g.get("spawn", 0)
        cd = g.get("cd", 0)
        c = int(g.get("announce", 0))
        chan = guild.get_channel(c)
        current = g.get("lastq", "").split()
        qmode = int(g.get("mode", 1))
        upnext = q[0:qmode]
        depl = int(g.get("depl", 0))
        if not q and spawn or depl:
            reset = g.get("reset", 0)
            arr = arrow.get(spawn).shift(hours=12) - now
            _h, _m, _s = await get_hms(arr)
            content = "Raid reset #**{}** starts in **{:02}**h **{:02}**m **{:02}**s.".format(
                reset + 1, _h, _m, _s
            )
            message = int(g.get("edit", 0))
            await self.update_timer_message(chan, message, content)
        elif not q and cd or depl:
            arr = now - arrow.get(cd)
            _h, _m, _s = await get_hms(arr)
            content = "Raid cooldown ended **{:02}**h **{:02}**m **{:02}**s ago.".format(
                _h, _m, _s
            )
            message = int(g.get("edit", 0))
            await self.update_timer_message(chan, message, content)

        if depl:
            return

        if len([m for m in upnext if m in current]) > 0:
            return

        if upnext == current:
            return
        elif len(upnext) == 0:
            await chan.send(
                "Queue has ended! You may now queue up for reset {}.".format(
                    int(g.get("reset", 0) + 1)
                )
            )
            await self.bot.db.hset(f"{guild.id}:tt:{group}", "depl", 1)
            return

        members = [guild.get_member(int(m)) for m in upnext]
        cnt = 0
        while cnt < len(upnext):
            await self.bot.db.lpop(f"{guild.id}:tt:{group}:q")
            cnt += 1
        await self.bot.db.hset(group, "lastq", " ".join([str(m.id) for m in members]))
        await chan.send(
            "It's {}'s turn to attack the raid!".format(
                ", ".join([f"**{m}**" for m in members])
            )
        )

    async def update_timer_message(self, channel, message, content):
        m = await channel.fetch_message(message)
        await m.edit(content=content)

    @raid_timer.before_loop
    async def before_raid_timer(self):
        await self.bot.wait_until_ready()

    @cmd.group(case_insensitive=True)
    async def tt(self, ctx):
        pass

    @tt.command(name="groupadd")
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_groupadd(self, ctx):
        res = dict(
            zip(
                ["1", "2", "3"],
                await asyncio.gather(
                    *(self.bot.db.hgetall(f"{ctx.guild.id}:tt:{x}") for x in [1, 2, 3])
                ),
            )
        )
        count = len([k for k in res if res[k]])
        if count < 3:
            slot = next((x for x in res if not res[x]), "3")
            group = f"{ctx.guild.id}:tt:{slot}"
            r1 = await self.bot.db.hset(group, "tier", 1)
            r2 = await self.bot.db.hset(group, "zone", 1)
            if not r1 and not r2:
                await ctx.send("Could not add group right now. Try again later.")
                return
            res[slot] = {"tier": 1}
            await ctx.send(
                "Successfully added group **{}** to ~**{}**. Currently used slots: [{}] [{}] [{}]".format(
                    slot,
                    ctx.guild,
                    res["1"] and "x" or "",
                    res["2"] and "x" or "",
                    res["3"] and "x" or "",
                )
            )
        elif count == 3:
            await ctx.send(
                f"~**{ctx.guild}** has reached maximum group count of **3**. Use **groupdel <x>** to delete a group."
            )

    @tt.command(name="groupdel")
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_groupdel(self, ctx, slot: Optional[int]):
        if slot not in [1, 2, 3]:
            await ctx.send("You must specify a slot between **1** and **3** to delete.")
            return
        result = await self.bot.db.delete(f"{ctx.guild.id}:tt:{slot}")
        res = dict(
            zip(
                ["1", "2", "3"],
                await asyncio.gather(
                    *(self.bot.db.hgetall(f"{ctx.guild.id}:tt:{x}") for x in [1, 2, 3])
                ),
            )
        )
        if result:
            await ctx.send(
                "Deleted group in slot **{}** from **{}**. Currently used slots: [{}] [{}] [{}]".format(
                    slot,
                    ctx.guild,
                    res["1"] and "x" or "",
                    res["2"] and "x" or "",
                    res["3"] and "x" or "",
                )
            )
            return
        await ctx.send(
            "There's no group in that slot. Currently used slots: [{}] [{}] [{}]".format(
                res["1"] and "x" or "", res["2"] and "x" or "", res["3"] and "x" or ""
            )
        )

    @tt.group(name="set")
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_set(self, ctx, group: Optional[TTRaidGroup], key: TTKey, val):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_admin_or_mod_or_master(ctx, groupdict)
        if key in "gmmastercaptainknightrecruitapplicantguest":
            val = await cmd.RoleConverter().convert(ctx, val)
            await self.bot.db.hset(group, key, val.id)
        elif key == "announce":
            val = await cmd.TextChannelConverter().convert(ctx, val)
            await self.bot.db.hset(group, key, val.id)
        elif key in "zonetier":
            try:
                val = int(val)
            except:
                raise cmd.BadArgument(f"Bad value for raid {key}")
            else:
                if not 1 <= val <= 10:
                    raise cmd.BadArgument()
                await self.bot.db.hset(group, key, val)
        elif key == "farm":
            val = await Truthy().convert(ctx, val)
            await self.bot.db.hset(group, key, val)
        elif key == "depl":
            val = await Truthy().convert(ctx, val)
            await self.bot.db.hset(group, key, val)
        elif key == "mode":
            try:
                val = int(val)
            except:
                raise cmd.BadArgument
            if not 1 <= val <= 5:
                await ctx.send("Queue mode must be between 1 and 5.")
                return
            await self.bot.db.hset(group, key, val)
        else:
            await self.bot.db.hset(group, key, val)
        await ctx.send(f"Set the TT2 **{key}** key to **{val}**")

    @tt.group(
        name="raid",
        aliases=["boss", "rd"],
        case_insensitive=True,
        invoke_without_command=True,
    )
    async def tt_raid(
        self,
        ctx,
        group: Optional[TTRaidGroup],
        level: cmd.Greedy[int],
        time: Optional[Duration],
    ):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_timer_permissions(ctx, groupdict)
        is_live = groupdict.get("spawn", 0)
        reset = groupdict.get("reset", 0)
        if not reset:
            reset = "starts"
        else:
            reset = f"reset #**{reset}** is"
        if is_live:
            dt = arrow.get(is_live) - arrow.utcnow()
            _h, _m, _s = await get_hms(dt)
            await ctx.send(f"Raid {reset} in **{_h}**h **{_m}**m **{_s}**s.")
            return
        if not level or len(level) == 0 or level == None:
            tier = groupdict.get("tier", 1)
            zone = groupdict.get("zone", 1)
        elif not all(1 <= x <= 10 for x in level):
            await ctx.send("Tier/zone must be between **1** and **10**.")
            raise cmd.BadArgument()
        elif len(level) == 2:
            tier, zone = level
        elif len(level) == 1:
            tier, zone = level, 1
        await self.bot.db.hset(group, "depl", 0)
        if not time or time == None:
            time = await Duration().convert(ctx, "24h")
        await self.bot.db.hset(group, "spawn", time.timestamp)
        time = time.humanize()
        if time == "just now":
            time = "now"
        edit = await ctx.send(
            f"Tier **{tier}**, zone **{zone}** raid starts **{time}**."
        )
        announce = int(groupdict.get("announce", 0))
        if announce and announce != ctx.channel.id:
            chan = self.bot.get_channel(announce)
            if chan:
                edit = await chan.send(
                    f"Tier **{tier}**, zone **{zone}** raid starts **{time}**."
                )
                await self.bot.db.hset(group, "edit", edit.id)
        elif announce:
            await self.bot.db.hset(group, "edit", edit.id)
        elif not announce:
            announce = await self.bot.db.hset(group, "announce", ctx.channel.id)
            await self.bot.db.hset(group, "edit", edit.id)

    @tt_raid.command(name="clear", aliases=["end", "ended", "cleared"])
    async def tt_raid_clear(self, ctx, group: Optional[TTRaidGroup]):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        spawn, reset = groupdict.get("spawn", None), groupdict.get("reset", 0)
        if not spawn or spawn is None:
            await ctx.send("No raid to clear.")
            return
        print(groupdict.get("spawn"))
        await self.has_timer_permissions(ctx, groupdict)
        now = arrow.utcnow()
        spwn_arrow = arrow.get(spawn)
        if now < spwn_arrow:
            await ctx.send(
                "You can't clear a raid before it spawns. Use **cancel** instead."
            )
            return
        total_time = now - spwn_arrow
        g = groupdict
        _h, _m, _s = await get_hms(total_time)
        cleared = f"**{_h}**h **{_m}**m **{_s}**s"
        await ctx.send(
            "Tier **{}**, Zone **{}** raid **cleared** in {}.".format(
                g.get("tier", 1), g.get("zone", 1), cleared
            )
        )
        shft_arrow = now.shift(hours=1)
        await self.bot.db.hset(group, "cd", shft_arrow.timestamp)
        await self.bot.db.hdel(group, "spawn")
        await self.bot.db.hdel(group, "edit")
        _h, _m, _s = await get_hms(shft_arrow - now)
        cleared = f"**{_h}**h **{_m}**m **{_s}**s."
        msg = await ctx.send("Raid cooldown ends in {}.")
        await self.bot.db.hset(group, "edit", msg.id)

    @tt_raid.command(name="cancel", aliases=["abort", "stop"])
    async def tt_raid_cancel(self, ctx, group: Optional[TTRaidGroup]):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_timer_permissions(ctx, groupdict)
        spawn = groupdict.get("spawn", None)
        cd = groupdict.get("cd", None)
        if not any([spawn, cd]):
            await ctx.send("No raid to cancel.")
            return
        else:
            await self.bot.db.hdel(group, "edit")
            await self.bot.db.hdel(group, "spawn")
            await self.bot.db.hdel(group, "cd")
            await self.bot.db.hdel(group, "lastq")
            await self.bot.db.hdel(group, "depl")
        await self.bot.db.delete(f"{group}:q")
        await ctx.send("Cancelled the current raid.")

    @tt_raid.command(name="info", aliases=["information"])
    async def tt_raid_info(self):
        return

    @tt.command(name="queue", aliases=["q"], case_insensitive=True)
    async def tt_queue(self, ctx, group: Optional[TTRaidGroup], list=None):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_clan_permissions(ctx, groupdict)
        # result = await self.bot.db.hget(group, "spawn")
        result = groupdict.get('spawn', 0)
        if not result:
            await ctx.send("No raid/reset to queue for.")
            return
        resets = int(groupdict.get('resets', 0))
        depl = int(groupdict.get('depl', 0))
        if not resets and not depl:
            resets = "first spawn"
        elif resets and not depl:
            resets = f"reset #{resets}"
        elif depl:
            resets = f"reset #{resets+1}"
        q = f"{group}:q"
        users = await self.bot.db.lrange(q)

        if not list:
            if not str(ctx.author.id) in users:
                await self.bot.db.rpush(q, ctx.author.id)
                users.append(ctx.author.id)
            else:
                await ctx.send(
                    f"You're already #**{users.index(str(ctx.author.id))+1}** in the queue, **{ctx.author}**."
                )
                return
        u = []

        mode = groupdict.get("mode", 1)
        clusters = zip_longest(*[iter(users)] * 3, fillvalue=None)
        result = []
        for c in clusters:
            temp = str(len(result) + 1)
            r = []
            for u in c:
                if u != None:
                    ux = await self.bot.fetch_user(int(u))
                    r.append(f"{ux}")
            result.append(temp + ". " + ", ".join(r))

        await ctx.send(
            "**Queue** for **{}**:\n```{}```\nUse **;tt unqueue** to cancel.".format(
                resets, "\n".join(result)
            )
        )

    @tt.command(name="unqueue", aliases=["unq", "uq"], case_insensitive=True)
    async def tt_unqueue(self, ctx, group: Optional[TTRaidGroup]):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        g = await self.bot.db.hgetall(group)
        await self.has_clan_permissions(ctx, g)
        result = g.get("spawn", 0)
        depl = g.get("depl", 0)
        if not result:
            await ctx.send("No raid/reset to queue for.")
            return
        resets = g.get("resets", 0)
        if not resets and not depl:
            resets = "first spawn"
        elif resets and not depl:
            resets = f"reset #{resets}"
        elif depl:
            resets = f"reset #{resets}+1"
        q = await self.bot.db.lrange(f"{group}:q")
        current = g.get("lastq", "").split()

        if str(ctx.author.id) in current:
            await ctx.send(
                "You can't cancel your place when it's your turn. Try **;tt d** / **;tt done** to finish your turn."
            )
            return
        elif not str(ctx.author.id) in q:
            await ctx.send(f"You're not in the queue, **{ctx.author}**.")
            return
        res = await self.bot.db.lrem(f"{group}:q", ctx.author.id)
        if res:
            await ctx.send(f"Ok **{ctx.author}**, I removed you from the queue.")

    @tt.command(name="done", aliases=["d"])
    async def tt_done(self, ctx, group: Optional[TTRaidGroup]):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        g = await self.bot.db.hgetall(group)
        await self.has_clan_permissions(ctx, g)
        result = await self.bot.db.hget(group, "spawn")
        if not result:
            await ctx.send("No raid/reset rn.")
            return
        print(g.get("lastq"))

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
