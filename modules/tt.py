from discord.ext import commands as cmd
from discord.ext import tasks as tsk
import discord
from enum import Enum, unique
from .utils import checks
from .utils.time import Duration, get_hms
from .utils.converters import Truthy, MemberID
from .utils.etc import (
    ttconvert_discover,
    ttconvert_from_scientific,
    ttconvert_to_scientific,
)
from typing import Optional
import asyncio
import arrow
from datetime import datetime
from itertools import zip_longest
import difflib
from string import ascii_lowercase, digits
from math import floor


def rotate(table, mod):
    return table[mod:] + table[:mod]


def lget(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


TIER_LIST = "SABCD"

RAID_DECKS = {
    "head": [
        ("Skull Bash", "Crushing Instinct"),
        (
            "Grim Shadow",
            "Razor Wind",
            "Inspiring Force",
            "Prismatic Rift",
            "Fragmentize",
        ),
        "Only target the Head. You need Skull Bash and Crushing Instinct for this deck, the third card can be almost anything of your choice.",
    ],
    "torso": [
        ("Soul Fire", "Moonbeam"),
        (
            "Grim Shadow",
            "Razor Wind",
            "Inspiring Force",
            "Prismatic Rift",
            "Fragmentize",
        ),
        "Only target the Torso. You only need Moonbeam and Soul Fire for this deck, the third card can be almost anything of your choice.",
    ],
    "all": [
        ("Whip of Lightning", "Blazing Inferno"),
        ("Inspiring Force", "Prismatic Rift"),
        "Target as many parts of the Titan Lord as possible. If the Titan has all its armor, use Prismatic Rift. If only Body remains, use Inspiring Force. Only use this deck if all parts are either armored or exposed.",
    ],
    "decay": [
        ("Decaying Strike", "Fusion Bomb", "Rancid Gas"),
        (),
        "Target as many parts of the Titan Lord as possible. Use this deck only when a new Titan with full HP spawns. Rotate between all parts, switching to the next each time Fusion activates. You cannot attack a part that already has Fusion applied, otherwise Fusion will never detonate.",
    ],
    "focus": [
        ("Clan Ship Barrage", "Ancestral Favor"),
        ("Razor Wind", "Fragmentize"),
        "Target any part of the Titan. Pick Razor Wind for the Body, and Fragmentize for the Armor.",
    ],
    "duo": [
        ("Purifying Blast", "Acid Drench"),
        ("Prismatic Rift", "Inspiring Force"),
        "Focus on two close-proximity parts for maximal damage e.g. Head and Torso, or Shoulder and Hand. Pick Inspiring Force for Body and Prismatic Rift for Armor.",
    ],
}

RAID_CARDS = {
    "Crushing Instinct": {
        "t": 1,
        "d": "activate Crushing Instinct, increasing damage dealt to the Titan Lord's head. Best used in conjunction with Skull Bash and another card of your choice.",
    },
    "Soul Fire": {
        "t": 1,
        "d": "activate a stack of Soul Fire, increasing damage dealt to the Titan Lord’s Torso. Use in conjunction with Moon Beam and another card of your choice for best damage on the torso.",
    },
    "Purifying Blast": {
        "t": 0,
        "d": "activate Purifying Blast, consuming all Affliction stacks on the damaged part, increasing this card's damage. Best used in conjunction with Acid Drench and Inspiring Force or Prismatic Rift.",
    },
    "Whip of Lightning": {
        "t": 1,
        "d": "activate Whip of Lightning. Whip of Lightning's chance to activate increases for each afflicted Titan Lord part. Used in decks targeting as many parts of the Titan Lord as possible.",
    },
    "Clan Ship Barrage": {
        "t": 1,
        "d": "activate Clanship Barrage. Clanship Barrage's damage increases for the remainder of the attack whenever any burst card is activated. Use with another Burst card and Ancestral Favor for best results.",
    },
    "Razor Wind": {
        "t": 1,
        "d": "activate Razor Wind, dealing extra damage against the Titan Lord's Body (any part that doesn't have armor that isn't a skeleton).",
    },
    "Moonbeam": {
        "t": 1,
        "d": "activate Moon Beam, dealing extra damage against the Titan Lord's Torso, armored or not.",
    },
    "Fragmentize": {
        "t": 1,
        "d": "activate Fragmentize, dealing extra damage against the Titan Lord's Armor.",
    },
    "Skull Bash": {
        "t": 1,
        "d": "activate Skull Bash, dealing extra damage against the Titan Lord's Head, armored or not.",
    },
    "Grim Shadow": {
        "t": 1,
        "d": "apply a stack of Shadow to the targeted part. When a part is afflicted with the maximum number of Shadow stacks (7), all Shadow stacks on that part deal bonus damage. Use this card on any part, armored or not, but focus on one part only. It synergizes best with single target decks.",
    },
    "Fusion Bomb": {
        "t": 2,
        "d": "apply a stack of Fusion to the targeted part. When the Fusion affliction expires, it detonates and deals damage to the afflicted Titan Lord part. Attacking a part with a stack of Fusion causes the stack to reset its detonation timer, so go for multiple or all parts of the Titan when using Fusion Bomb to minimize damage waste.",
    },
    "Decaying Strike": {
        "t": 2,
        "d": "apply a stack of Decay to the targeted part. Decaying Strike's damage multiplies by the remaining health percentage of the damaged part. Use this when there is a new Titan Lord with full HP for best results.",
    },
    "Blazing Inferno": {
        "t": 2,
        "d": "apply a stack of Inferno to the targeted part. For each part afflicted by Inferno, this card's activation chance increases. Pair this card with Whip of Lightning in your all parts deck, they synergize well. This card is otherwise useless.",
    },
    "Thriving Plague": {
        "t": 3,
        "d": "apply a stack of Plague to the targeted part. All Plague stacks deal additional damage per second for each part afflicted by Plague. This card is good on Whip of Lightning decks, though Inferno is preferred. No use for this card in the current meta.",
    },
    "Radioactivity": {
        "t": 4,
        "d": "apply a stack of Radioactivity to the targeted part. For each second a part is afflicted by Radioactivity, all Radioactivity stacks on that part deal additional damage per second. A much worse version of Grim Shadow. Don't use it.",
    },
    "Acid Drench": {
        "t": 4,
        "d": "apply a stack of Acid to the targeted part. When a stack of Acid is applied to a Titan Lord part, the duration of all other Acid stacks on that part are reset. Use in Purifying Blast decks for best results. Do not buy this card, as it only increases its minuscule damage and not the chance, stacks or duration.",
    },
    "Ancestral Favor": {
        "t": 0,
        "d": "activate a stack of Favor, increasing all Burst Damage and Burst Chance. Pair this card with burst cards of your choice and deal massive damage to the Titan Lord.",
    },
    "Inspiring Force": {
        "t": 0,
        "d": "activate a stack of Inspiration, increasing Raid Damage dealt to the Titan Lord's Body. One of the most versatile cards in the game, useful in any Body deck.",
    },
    "Prismatic Rift": {
        "t": 0,
        "d": "activate a stack of Prismatic, increasing Damage dealt to the Titan Lord's Armor. One of the most versatile cards in the game, useful in any Armor deck.",
    },
    "Rancid Gas": {
        "t": 2,
        "d": "activate a stack of Rancid, increasing all Affliction Damage and Affliction Chance. All Affliction decks currently lack viability, so this card ranks lower.",
    },
    "Victory March": {
        "t": 3,
        "d": "activate a stack of Victory March, increasing Raid Damage dealt for each exposed Titan Lord Skeleton part. Overpowers other support cards once 6/8 Titan Lord parts have been destroyed. Do not use this card otherwise.",
    },
}


class TTRaidCard(cmd.Converter):
    async def convert(self, ctx: cmd.Context, arg):
        arg = arg.title()
        closest_match = difflib.get_close_matches(
            arg, list(RAID_CARDS.keys()), n=1, cutoff=0.85
        )
        if closest_match:
            return closest_match[0], RAID_CARDS.get(closest_match[0])
        if not closest_match and arg.strip():
            closest_match = next(
                (k for k in list(RAID_CARDS.keys()) if k.startswith(arg)), None
            )
            if closest_match:
                return closest_match, RAID_CARDS.get(closest_match)
        if not closest_match and arg.strip():
            closest_match = next(
                (
                    k
                    for k in list(RAID_CARDS.keys())
                    if "".join([x[0] for x in k.lower().split()]) == arg.lower()
                ),
                None,
            )
            if closest_match:
                return closest_match, RAID_CARDS.get(closest_match)
        return None, None


class TTDeck(cmd.Converter):
    async def convert(self, ctx, arg):
        arg = arg.lower()
        closest_match = difflib.get_close_matches(
            arg, list(RAID_DECKS.keys()), n=1, cutoff=0.85
        )
        if closest_match:
            return closest_match[0], RAID_DECKS.get(closest_match[0])
        if not closest_match and arg.strip():
            closest_match = next(
                (k for k in list(RAID_DECKS.keys()) if k.startswith(arg)), None
            )
            if closest_match:
                return closest_match, RAID_DECKS.get(closest_match)
        return None, None


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
            "code",
            "name",
        ]:
            await ctx.send(f"**{arg}** is not a valid settings key for TT2 module.")
            raise cmd.BadArgument("Bad key for TT2 settings")
        if arg == "average":
            arg == "avg"
        elif arg == "grandmaster":
            arg == "gm"
        if (
            arg in "gmmastercaptainknightrecruitapplicantguesttimer"
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



TTRoles = dict(
    G="gm",
    M="master",
    C="captain",
    K="knight",
    R="recruit",
    T="timer",
)

class TapTitansModule(cmd.Cog):
    """Tap Titans 2 is an idle RPG game on iOS and Android that lets you take the battle to the titans! Level up heroes, participate in Clan Raids, and stomp on other players in Tournaments!\nI am working hard to make improvements to this module. It's nearly a thousand lines long and that's just with decks and raids!"""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.aliases = ["tt"]
        self.raid_timer.start()
        self.em = 440785686438871040

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
        if not any(roles):
            await ctx.send(
                "Looks like no clan roles are set up. Anyone with manage guild *and* manage roles permission can do this."
            )
            raise cmd.BadArgument
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

    @tsk.loop(seconds=10)
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
        current = g.get("current", "").split()
        qmode = int(g.get("mode", 1))
        upnext = q[0:qmode]
        depl = int(g.get("depl", 0))
        reset = int(g.get("reset", 0))
        if not current and not q and (spawn or depl):
            arr = arrow.get(spawn).shift(hours=12 * (reset + 1)) - now
            _h, _m, _s = await get_hms(arr)
            if _h < 0 or _m < 0 or _s < 0:
                reset = reset + 1
                await self.bot.db.hset(f"{guild.id}:tt:{group}", "reset", reset)
                _h, _m, _s = await get_hms(arr)
                arr = arrow.get(spawn).shift(hours=12 * (reset + 1)) - now
            content = "Raid reset #**{}** starts in **{:02}**h **{:02}**m **{:02}**s.".format(
                reset + 1, _h, _m, _s
            )
            message = int(g.get("edit", 0))
            await self.update_timer_message(chan, message, content)
        elif not current and not q and (cd or depl):
            arr = now - arrow.get(cd)
            _h, _m, _s = await get_hms(arr)
            content = "Raid cooldown ended **{:02}**h **{:02}**m **{:02}**s ago.".format(
                _h, _m, _s
            )
            message = int(g.get("edit", 0))
            await self.update_timer_message(chan, message, content)

        if len(current) > 0:
            return

        if not len(upnext) and not len(current) and not depl:
            await chan.send(
                "Queue has ended! You may now queue up for reset #**{}**.".format(
                    reset + 1
                )
            )
            await self.bot.db.hset(f"{guild.id}:tt:{group}", "depl", 1)
            await self.bot.db.delete(f"{guild.id}:tt:{group}:q")
            return
        elif not len(upnext) and not len(current) and depl:
            return

        members = [guild.get_member(int(m)) for m in upnext]
        cnt = 0
        while cnt < len(upnext):
            await self.bot.db.lrem(f"{guild.id}:tt:{group}:q", upnext[cnt])
            cnt += 1
        await self.bot.db.hset(
            f"{guild.id}:tt:{group}", "current", " ".join([str(m.id) for m in members])
        )
        await chan.send(
            "It's {}'s turn to attack the raid!".format(
                ", ".join([f"{m.mention}" for m in members])
            )
        )

    async def update_timer_message(self, channel, message, content):
        m = await channel.fetch_message(message)
        await m.edit(content=content)

    @raid_timer.before_loop
    async def before_raid_timer(self):
        await self.bot.wait_until_ready()

    @cmd.group(name="taptitans", aliases=["tt"], case_insensitive=True, hidden=True)
    async def taptitans(self, ctx):
        pass

    @taptitans.command(name="groupadd", aliases=["gadd"], usage="slot")
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_groupadd(self, ctx):
        """Adds a new raid group to the server. You will only ever need more than one of these if you have more than one Tap Titans 2 clan in your discord server *looking at you AC & GT*."""
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

    @taptitans.command(name="groupdel", aliases=["gdel"], usage="slot")
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_groupdel(self, ctx, slot: Optional[int]):
        """Deletes an existing raid group in the slot. Warning - irreversible. Do this only if you mean it."""
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

    @taptitans.command(
        name="groupget", aliases=["gshow", "groupshow", "gget"], usage="slot"
    )
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_groupget(self, ctx, slot: Optional[int] = 1):
        """Displays a tap titans raid group and the most important values that go into setting up a raid, including roles and broadcast channel."""
        if slot not in [1, 2, 3]:
            await ctx.send("You must specify a slot between **1** and **3** to show.")
            return
        r = await self.bot.db.hgetall(f"{ctx.guild.id}:tt:{slot}")
        ns = "**not-set**"
        roles = "\n".join(
            ["`{}` @**{}**".format(
                n,
                discord.utils.get(ctx.guild.roles, id=int(r.get(m, 0)))
            ) for n, m in TTRoles.items()]
        )
        await ctx.send(
            f"**{r.get('name', '<clanname>')}** [{r.get('code', '00000')}] "
            f"T{r.get('tier', 1)}Z{r.get('zone', 1)}\n"
            f"{roles}\n"
            f"Messages are broadcast in #**{discord.utils.get(ctx.guild.channels, id=int(r.get('announce', 0)))}** and queue size is **{r.get('mode', 1)}**."
        )

    @taptitans.group(name="set", usage="key val")
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_set(self, ctx, group: Optional[TTRaidGroup], key: TTKey, val):
        "Set a settings key for tap titans clan."
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_admin_or_mod_or_master(ctx, groupdict)
        if key in "gmmastercaptainknightrecruitapplicantguesttimer":
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
        elif key == "name":
            await self.bot.db.hset(group, key, val)
        elif key == "code":
            val = val.lower()
            if len(val) > 7 or len(val) < 5:
                return
            _, db = await self.bot.db.hscan("cc", match=val)
            cc = groupdict.get(key, None)
            if val == cc:
                await ctx.send("You are already using this clan code.")
                return
            in_use = lget(db, 1, 0)
            if in_use and in_use != str(ctx.guild.id):
                await ctx.send(
                    "A guild is already using that code. Appeal to bot owner if someone stole your clan code."
                )
                return
            if not cc:
                await self.bot.db.hdel("cc", cc)
            await self.bot.db.hset("cc", val, ctx.guild.id)
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

    @taptitans.group(
        name="raid",
        aliases=["boss", "rd"],
        case_insensitive=True,
        invoke_without_command=True,
        usage="0h0m0s",
    )
    async def tt_raid(
        self,
        ctx,
        group: Optional[TTRaidGroup],
        level: cmd.Greedy[int],
        time: Optional[Duration],
    ):
        "Sets a raid to spawn after the given time."
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_timer_permissions(ctx, groupdict)
        is_live = groupdict.get("spawn", 0)
        cd = groupdict.get("cd", 0)
        reset = int(groupdict.get("reset", 0))
        if not reset and not cd:
            rs_txt = "starts"
        elif cd:
            rs_txt = "cooldown ends"
        else:
            rs_txt = f"reset #**{reset}** is"
        if is_live or cd:
            arr_x = arrow.get(is_live or cd)
            arr_n = arrow.utcnow()
            if arr_n > arr_x and is_live and not cd:
                arr_x = arr_x.shift(hours=12 * (reset + 1))
                dt = arr_x - arr_n
                rs_txt = f"reset #**{reset+1}** is"
            elif arr_x >= arr_n:
                dt = arr_x - arr_n
            _h, _m, _s = await get_hms(dt)
            await ctx.send(f"Raid {rs_txt} in **{_h}**h **{_m}**m **{_s}**s.")
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

    @tt_raid.command(name="clear", aliases=["end", "ended", "cleared", "cd"])
    async def tt_raid_clear(
        self, ctx, group: Optional[TTRaidGroup], cd: Optional[Duration]
    ):
        "Clears a raid. Use this only when you complete a raid. Use cancel if you want to wipe the timer."
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        spawn = groupdict.get("spawn", 0)
        if not spawn and not groupdict.get("cd", 0):
            await ctx.send("No raid to clear.")
            return
        elif groupdict.get("cd", 0):
            await ctx.send(
                "Raid is on cooldown. Use **cancel** if you wish to cancel it."
            )
            return
        await self.has_timer_permissions(ctx, groupdict)

        now = arrow.utcnow()
        spwn_arrow = arrow.get(spawn)
        if now < spwn_arrow:
            await ctx.send("You can't clear an unspawned raid. Use **cancel** instead.")
            return
        if cd == None:
            cd = now.shift(minutes=59, seconds=59)
        delta = cd - now
        _h, _m, _s = await get_hms(delta)
        shifter = {}
        if _m not in [0, 59]:
            shifter["minutes"] = 60 - _m
        if _s not in [0, 59]:
            shifter["seconds"] = 60 - _s
        if cd < spwn_arrow.shift(minutes=60):
            await ctx.send(
                "You cannot timetravel. The cooldown end must be at least 60 minutes after the start of the raid."
            )
            raise cmd.BadArgument

        total_time = now.shift(**shifter) - spwn_arrow
        g = groupdict
        _h2, _m2, _s2 = await get_hms(total_time)
        cleared = f"**{_h2}**h **{_m2}**m **{_s2}**s"
        await ctx.send(
            "Tier **{}**, Zone **{}** raid **cleared** in {}.".format(
                g.get("tier", 1), g.get("zone", 1), cleared
            )
        )
        shft_arrow = now.shift(minutes=_m > 0 and _m or 0, seconds=_s > 0 and _s or 0)
        await self.bot.db.hset(group, "cd", shft_arrow.timestamp)
        await self.bot.db.hdel(group, "spawn")
        await self.bot.db.hdel(group, "edit")
        cleared = f"**{_h}**h **{_m}**m **{_s}**s"
        msg = await ctx.send(f"Raid cooldown ends in {cleared}.")
        await self.bot.db.hset(group, "edit", msg.id)

    @tt_raid.command(name="cancel", aliases=["abort", "stop"])
    async def tt_raid_cancel(self, ctx, group: Optional[TTRaidGroup]):
        "Cancels a currently scheduled raid."
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
            await self.bot.db.hdel(group, "current")
            await self.bot.db.hdel(group, "depl")
            await self.bot.db.hdel(group, "reset")
        await self.bot.db.delete(f"{group}:q")
        await ctx.send("Cancelled the current raid.")

    @taptitans.command(
        name="queue", aliases=["q"], case_insensitive=True, usage="show|clear|skip"
    )
    async def tt_queue(self, ctx, group: Optional[TTRaidGroup], list=None):
        (
            "Enter into the tap titans raid queue.\n"
            "**show** displays the queue.\n"
            "**clear** clears the entire queue and any currently attacking groups.\n"
            "**skip** skips the currently attack group e.g. if someone goes afk"
        )
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        await self.has_clan_permissions(ctx, groupdict)
        result = groupdict.get("spawn", 0)
        if not result:
            await ctx.send("No raid/reset to queue for.")
            return
        resets = int(groupdict.get("reset", 0))
        depl = int(groupdict.get("depl", 0))
        if not resets and not depl:
            resets = "first spawn"
        elif resets and not depl:
            resets = f"reset #{resets}"
        elif depl:
            resets = f"reset #{resets+1}"
        q = f"{group}:q"
        users = await self.bot.db.lrange(q)
        current = groupdict.get("current", "").split()
        if not list:
            if not str(ctx.author.id) in users:
                await self.bot.db.rpush(q, ctx.author.id)
                users.append(ctx.author.id)
            else:
                await ctx.send(
                    f"You're already #**{users.index(str(ctx.author.id))+1}** in the queue, **{ctx.author}**."
                )
                return
        elif list in ["clear", "wipe", "erase"]:
            await self.has_timer_permissions(ctx, groupdict)
            await self.bot.db.delete(q)
            await self.bot.hdel(group, "current")
            await ctx.send("Queue has been cleared!")
            return
        elif list in ["skip"]:
            await self.has_timer_permissions(ctx, groupdict)
            await self.bot.hdel(group, "current")
        if str(ctx.author.id) in current:
            await ctx.send(
                f"You are attacking, **{ctx.author}**. Use **;tt d** to finish your turn."
            )
            return
        u = []

        mode = int(groupdict.get("mode", 1))
        clusters = zip_longest(*[iter(users)] * mode, fillvalue=None)
        result = []
        for c in clusters:
            temp = str(len(result) + 1)
            r = []
            for u in c:
                if u != None:
                    ux = await self.bot.fetch_user(int(u))
                    r.append(f"{ux}")
            result.append(temp + ". " + ", ".join(r))

        if result:
            await ctx.send(
                "**Queue** for **{}**:\n```{}```\nUse **;tt unqueue** to cancel.".format(
                    resets, result and "\n".join(result) or " "
                )
            )
            return
        await ctx.send(f"**Queue** for **{resets}** is currently **empty**.")

    @taptitans.command(name="unqueue", aliases=["unq", "uq"], case_insensitive=True)
    async def tt_unqueue(
        self, ctx, group: Optional[TTRaidGroup], members: cmd.Greedy[MemberID]
    ):
        "Remove yourself from the tap titans raid queue."
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
        current = g.get("current", "").split()
        if str(ctx.author.id) in current:
            await ctx.send(
                "You can't cancel your place when it's your turn. Try **;tt d** / **;tt done** to finish your turn."
            )
            return
        elif not str(ctx.author.id) in q:
            await ctx.send(f"You're not in the queue, **{ctx.author}**.")
            return
        else:
            res = await self.bot.db.lrem(f"{group}:q", ctx.author.id)
            if res:
                await ctx.send(f"Ok **{ctx.author}**, I removed you from the queue.")

    @taptitans.command(name="done", aliases=["d"])
    async def tt_done(self, ctx, group: Optional[TTRaidGroup]):
        "Mark yourself as done in the raid queue. Will only work if you're currently attacking."
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        g = await self.bot.db.hgetall(group)
        await self.has_clan_permissions(ctx, g)
        if not g.get("spawn", 0):
            await ctx.send("No raid/reset rn.")
            return
        current = g.get("current", "").split()
        if not str(ctx.author.id) in current:
            q = await self.bot.db.lrange(f"{group}:q")
            if not str(ctx.author.id) in q:
                await ctx.send(
                    "Looks like it is not your turn and you are not in the queue."
                )
            else:
                await ctx.send(
                    "It is not your turn but you are in the queue. To cancel your place, do **;tt uq**"
                )
        else:
            current = " ".join(current)
            current = current.replace(str(ctx.author.id), "")
            await self.bot.db.hset(group, "current", current.strip())
            await ctx.send(f"**{ctx.author}** has finished their turn.")

    @taptitans.command(name="card", aliases=["cards"], case_insensitive=True)
    async def tt_card(self, ctx, *card):
        "Shows you information about tap titans cards."
        card, data = await TTRaidCard().convert(ctx, " ".join(card))
        if not card:
            await ctx.send(
                "Available cards: {}".format(
                    ", ".join([f"**{k}**" for k in RAID_CARDS.keys()])
                )
            )
            return
        await ctx.send(
            "{} **{}** - **{}** Tier\nTaps have a chance to {}".format(
                discord.utils.get(self.bot.emojis, name=card.lower().replace(" ", "_")),
                card,
                TIER_LIST[data["t"]],
                data["d"],
            )
        )

    @taptitans.command(
        name="deck", aliases=["decks"], case_insensitive=True, usage="deckname"
    )
    async def tt_deck(self, ctx, *deck):
        "Shows you some of the best tap titans deck combinations available."
        crimtain = await self.bot.fetch_user(190222871254007808)
        deck, data = await TTDeck().convert(ctx, " ".join(deck))
        if not deck or deck is None:
            await ctx.send(
                "Available decks: {}".format(
                    ", ".join([f"**{x}**" for x in RAID_DECKS.keys()])
                )
            )
            return
        await ctx.send(
            "**{} Deck**\n\n**Core cards**\n{}\n\n**Optional cards**\n{}\n\n{}\n\ncommand inspired by **{}**".format(
                deck.title(),
                ", ".join(
                    [
                        f"{discord.utils.get(self.bot.emojis, name=d.lower().replace(' ', '_'), guild_id=440785686438871040)} {d}"
                        for d in data[0]
                    ]
                ),
                data[1]
                and ", ".join(
                    [
                        f"{discord.utils.get(self.bot.emojis, name=d.lower().replace(' ', '_'), guild_id = 440785686438871040)} {d}"
                        for d in data[1]
                    ]
                )
                or "n/a",
                data[2],
                crimtain,
            )
        )

    @taptitans.command(name="optimizers", aliases=["opti", "optimisers", "optis"])
    async def tt_opti(self, ctx):
        "Displays a link to TT2 optimisers."
        t_url = "<https://tinyurl.com/{}>"
        await ctx.send(
            "**List of TapTitans2 Optimizers**\nThese links should be useful in helping you best level your skill tree and artifacts.\n**Mmlh Skill Point Optimizer:** {}\n**Mmlh Artifact Optimizer:** {}\n**Parrot SP/Arti Optimizer:** {}".format(
                t_url.format("spoptimiser"),
                t_url.format("artoptimiser"),
                t_url.format("TT2Optimizer"),
            )
        )

    @taptitans.command(name="compendium", aliases=["comp"])
    async def tt_compendium(self, ctx):
        "Displays a link to the TT2 Compendium site."
        await ctx.send(
            "**TapTitans2 Compendium**\nThis site made by the Compendium Team provides great sample builds, guides, & tools, whether you're new or a veteran player.\n<https://tt2-compendium.herokuapp.com>"
        )

    @taptitans.group(name="hero", case_insensitive=True)
    async def tt_hero(self):
        return

    @taptitans.group(name="equip", case_insensitive=True)
    async def tt_equip(self):
        return

    @taptitans.group(
        name="artifact",
        aliases=["arti", "arts", "artifacts"],
        invoke_without_command=True,
    )
    async def tt_artifacts(self, ctx, artifact: Optional[str], lvl_from: Optional[int], lvl_to: Optional[int]):
        if not artifact:
            await ctx.send('Here is a list of the artifacts sorted by tier')
        elif artifact and not any([lvl_from, lvl_to]):
            await ctx.send("here would be artifact basic info")
        else:
            await ctx.send("heree would be artifact leveling info")
    
    @tt_artifacts.command(name='build')
    async def tt_artifacts_build(self, ctx, build: Optional[str]):
        if not build:
            await ctx.send('List of builds for searching: ')
        

    @taptitans.group(name="enhancement", case_insensitive=True)
    async def tt_enhance(self):
        return

    @taptitans.group(name="enchant", case_insensitive=True)
    async def tt_enchant(self):
        return

    async def titancount(self, stage, ip, ab, snap):
        return round(max((stage // 500 * 2 + 8 - (ip + ab)) / max(2 * snap, 1), 1))

    @taptitans.command(
        name="titancount",
        aliases=["titans", "count"],
        case_insensitive=True,
        usage="stage ip ab snaps",
    )
    async def tt_titancount(
        self, ctx, stage: int = 10000, ip: int = 30, ab: int = 5, snap: int = 0
    ):
        "Shows you how many titans there would be at any given stage."
        if any([x for x in [stage, ip, ab] if x < 0]):
            raise cmd.BadArgument
        count = await self.titancount(stage, ip, ab, snap)
        await ctx.send(
            "Titan count at stage {} (IP {}, AB {}, {} Snap{} active) would be: {}".format(
                stage, ip, ab, snap, snap != 1 and "s", count
            )
        )

    @taptitans.command(
        name="edskip",
        aliases=["ed"],
        usage="stage ip mystic_impact arcain_bargain anni_plat",
    )
    async def tt_ed(
        self,
        ctx,
        stage: int = 1,
        ip: Optional[int] = 0,
        mystic_impact: Optional[int] = 0,
        arcane_bargain: Optional[int] = 0,
        anniversary_platinum: Optional[float] = 1.0,
    ):
        (
            "Helps you calculate the optimal ED skip level you need to put into your build.\n"
            "Optimal here means the total skip required to clear maximum splash with 1 Snap active.\n"
        )
        count = await self.titancount(stage, ip, arcane_bargain, 0)
        count2 = floor(count / 2)
        current_skip = mystic_impact + arcane_bargain
        ed_boosts = [
            0,
            1,
            2,
            3,
            4,
            6,
            8,
            10,
            12,
            14,
            16,
            18,
            20,
            23,
            26,
            29,
            33,
            38,
            44,
            51,
            59,
            68,
            78,
            89,
            101,
        ]
        result = 0
        while current_skip * anniversary_platinum < count2 and result < 25:
            current_skip = mystic_impact + arcane_bargain + ed_boosts[result]
            result += 1
        await ctx.send(
            f"{discord.utils.get(self.bot.emojis, name='edskip', guild_id=self.em)} Optimal ED level at stage **{stage}** ({count} titans) is: **{result}**."
        )

    @taptitans.group(name="titanlord", case_insensitive=True)
    async def tt_titanlord(self):
        return

    @taptitans.group(name="skill", case_insensitive=True)
    async def tt_skill(self):
        return

    @taptitans.command(
        name="tournament", aliases=["tournaments", "tourneys", "tourney"], usage="next"
    )
    async def tt_tournaments(self, ctx, last: Optional[int] = 3):
        (
            "Displays a forecast of upcoming Tap Titans 2 tournaments.\n"
            "Icon colour will indicate tournament status. Live = blue. Not live = red.\n"
            "You can extend the forecast up to 10 future tournaments with the <next> parameter."
        )
        if last not in range(1, 11):
            await ctx.send(
                "Do you really need to see {} weeks into the future?".format(
                    round(last / 2)
                )
            )
            return
        prizes = "hero_weapon skill_point crafting_shard"
        bonuses = [
            ("x3 warlord boost", "warlord_boost"),
            ("+5 mana regen", "mystic_staff"),
            ("x1.2 all probability bonus", "all_probability"),
            ("x3 sorcerer boost", "titanias_sceptre"),
            ("x10 chesterson gold", "chesterson_gold"),
            ("+100% multiple fairies", "fairy_chance"),
            ("x3 knight boost", "knight_boost"),
            ("+20% mana refund", "mystical_beans_of_senzu"),
            ("x1.5 prestige relics", "relic"),
            ("x10 boss gold", "boss_gold"),
        ]
        result, i, now = [], 0, arrow.utcnow()
        origin = arrow.get(1532242116)
        weeks, _ = divmod((now - origin).days, 7)
        current = int(now.format("d"))
        tourneys = weeks * 2
        icon = "tourney_red"
        if current in [1, 5]:
            shifter = 2
        if current in [2, 6]:
            shifter = 1
        if current in [3, 7]:
            shifter = 0
            icon = "tourney"
        if current in [4]:
            shifter = 3
        prizes = rotate(prizes.split(), tourneys % 3)
        bonuses = rotate(bonuses, tourneys % 10)
        flipper = lambda i: current <= 3 and i % 2 or 0
        result = [
            (
                now.shift(days=i * 3.5 + shifter + flipper(i)).format("ddd DD MMM"),
                bonuses[i],
                prizes[i % 3],
            )
            for i in range(last)
        ]
        result = "\n===================\n".join(
            [
                ":calendar_spiral: `{}`\n{} {}\n{} {}".format(
                    r[0],
                    discord.utils.get(self.bot.emojis, name=r[1][1], guild_id=self.em),
                    r[1][0],
                    discord.utils.get(self.bot.emojis, name=r[2], guild_id=self.em),
                    r[2].replace("_", " ").title() + "s",
                )
                for r in result
            ]
        )
        await ctx.send(
            f"{discord.utils.get(self.bot.emojis, name=icon, guild_id=self.em)} TT2 Tournament Forecast\n===================\n{result}\n===================\n{last==3 and 'Tip: show more tourneys with ;tt tourney 8' or ''}"
        )

    @taptitans.command(name="convert", aliases=["cvt"], usage="value")
    async def tt_convert(self, ctx, val: Optional[str] = "1e+5000"):
        (
            "Allows you to convert a scientific/letter notation into the opposite version.\n"
            "The bot will automagically figure out which way you want to convert.\n"
        )
        result, f, t = None, "scientific", "letter"
        mode = await ttconvert_discover(val)
        if mode == 0:
            result = await ttconvert_from_scientific(val)
        elif mode == 1:
            result = await ttconvert_to_scientific(val)
            f, t = "letter", "scientific"
        await ctx.send(
            "{} Conversion of **{}** from **{}** to **{}** is: **{}**".format(
                discord.utils.get(self.bot.emojis, name="_orange", guild_id=self.em),
                val,
                f,
                t,
                result,
            )
        )

    @taptitans.command(
        name="gold", aliases=["goldsource", "goldsources"], usage="<kind>"
    )
    async def tt_gold(self, ctx, kind: Optional[str]):
        "Displays optimal artifacts required for a specific gold source."
        taco = await self.bot.fetch_user(381376462189625344)
        sources = dict(
            phom=(
                "Pet Heart of Midas is a great, reliable, balanced gold source. It's frequent, gives you good gold, and can be used in both pushing and farming.",
                "neko_sculpture bronzed_compass heroic_shield",
            ),
            fairy=(
                "Fair is supposedly the best gold source out there, but it can be frustrating waiting for a gold ad fairy and getting an all skills fairy instead.",
                "chest_of_contentment great_fay_medallion bronzed_compass",
            ),
            chesterson=(
                "A tougher nut to crack, this one of the best gold sources for farming, but might leave you up sh*t creek when trying to push. Relies heavily on multispawn chesterson gold.",
                "chest_of_contentment essence_of_the_kitsune coins_of_ebizu",
            ),
            boss=(
                "Boss gold uses Hands of Midas in order to get large amounts of gold upon killing bosses. It benefits directly from the Heart of Midas skill too, but it is faster than waiting for a pHoM proc. Typically is weaker than pHoM.",
                "heroic_shield laborers_pendant titanias_sceptre",
            ),
            inactive=(
                "Inactive gold will be the weakest compared to any other source, but it can be reliable/relevant if you don't have Stones of the Valrunes artifact yet. Playing an active gold source will always be better nonetheless.",
                "zakynthos_coin khrysos_bowl",
            ),
        )
        if not kind or kind.lower() not in sources.keys():
            await ctx.send(
                "Available gold sources:\n{}".format(", ".join(sources.keys()))
            )
            return
        await ctx.send(
            "**{} Gold**\n{}\n{}\n\ncommand inspired by **{}**".format(
                kind,
                sources[kind.lower()][0],
                " ".join(
                    str(discord.utils.get(self.bot.emojis, name=x, guild_id=self.em))
                    for x in sources[kind.lower()][1].split()
                ),
                taco,
            )
        )


def setup(bot):
    bot.add_cog(TapTitansModule(bot))
