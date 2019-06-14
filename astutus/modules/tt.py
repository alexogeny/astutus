from discord.ext import commands as cmd
from discord.ext import tasks as tsk
import discord
from enum import Enum, unique
from astutus.utils import Duration, checks, Truthy, get_hms, MemberID
from typing import Optional
import asyncio
import arrow
from datetime import datetime
from itertools import zip_longest
import difflib
from string import ascii_lowercase, digits

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

@unique
class TTRoles(Enum):
    G = 'gm'
    M = 'master'
    C = 'captain'
    K = 'knight'
    R = 'recruit'
    T = 'timer'

class TapTitansModule(cmd.Cog):
    """Tap Titans 2 is an idle RPG game on iOS and Android that lets you take the battle to the titans! Level up heroes, participate in Clan Raids, and stomp on other players in Tournaments!\nI am working hard to make improvements to this module. It's nearly a thousand lines long and that's just with decks and raids!"""

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

        if depl:
            return

        if len(current) > 0:
            return

        if len(upnext) == 0 and " ".join(current).strip() == "":
            await chan.send(
                "Queue has ended! You may now queue up for reset #**{}**.".format(
                    reset + 1
                )
            )
            await self.bot.db.hset(f"{guild.id}:tt:{group}", "depl", 1)
            await self.bot.db.delete(f"{guild.id}:tt:{group}:q")
            return
        elif len(upnext) == 0 and " ".join(current).strip() != "":
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

    @cmd.group(case_insensitive=True, hidden=True)
    async def tt(self, ctx):
        pass

    @tt.command(name="groupadd")
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

    @tt.command(name="groupdel")
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

    @tt.command(name="groupget", aliases=["gshow", "groupshow", "gget"])
    @cmd.guild_only()
    @checks.is_mod()
    async def tt_groupget(self, ctx, slot: Optional[int] = 1):
        if slot not in [1, 2, 3]:
            await ctx.send("You must specify a slot between **1** and **3** to show.")
            return
        r = await self.bot.db.hgetall(f"{ctx.guild.id}:tt:{slot}")
        ns = "**not-set**"
        roles = '\n'.join([f"`{n}` @{r.get(m, ns)}" for n, m in TTRoles.__members__.items()])
        print(roles)
        await ctx.send(
            f"**{r.get('name', '<clanname>')}** [{r.get('code', '00000')}] "
            f"T{r.get('tier', 1)}Z{r.get('zone', 1)}\n"
            f"{roles}\n"
            f"Messages are broadcast in #{r.get('announce', ns)} and queue size is **{r.get('mode', 1)}**."
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
                await ctx.send('You are already using this clan code.')
                return
            in_use = lget(db, 1, 0)
            print(in_use)
            if in_use and in_use != str(ctx.guild.id):
                await ctx.send(
                    "A guild is already using that code. Appeal to bot owner if someone stole your clan code."
                )
                return
            print(db)
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

    @tt_raid.command(name="clear", aliases=["end", "ended", "cleared", "cd"])
    async def tt_raid_clear(
        self, ctx, group: Optional[TTRaidGroup], cd: Optional[Duration]
    ):
        if group == None:
            group = f"{ctx.guild.id}:tt:1"
        group = await self.get_raid_group_or_break(group, ctx)
        groupdict = await self.bot.db.hgetall(group)
        spawn, reset = groupdict.get("spawn", None), int(groupdict.get("reset", 0))
        if not spawn or spawn is None:
            await ctx.send("No raid to clear.")
            return
        await self.has_timer_permissions(ctx, groupdict)

        now = arrow.utcnow()
        spwn_arrow = arrow.get(spawn)
        if now < spwn_arrow:
            await ctx.send(
                "You can't clear a raid before it spawns. Use **cancel** instead."
            )
            return
        if cd != None or cd:
            delta = cd - now
            _h, _m, _s = await get_hms(delta)

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
            await self.bot.db.hdel(group, "current")
            await self.bot.db.hdel(group, "depl")
            await self.bot.db.hdel(group, "reset")
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
            await ctx.send("Queue has been cleared!")
            return
        elif list in ["skip"]:
            await self.has_timer_permissions(ctx, groupdict)
            await self.bot.hset(group, "current", "")
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

    @tt.command(name="unqueue", aliases=["unq", "uq"], case_insensitive=True)
    async def tt_unqueue(
        self, ctx, group: Optional[TTRaidGroup], members: cmd.Greedy[MemberID]
    ):
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

    @tt.command(name="done", aliases=["d"])
    async def tt_done(self, ctx, group: Optional[TTRaidGroup]):
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

    @tt.command(name="card", aliases=["cards"], case_insensitive=True)
    async def tt_card(self, ctx, *card):
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

    @tt.command(name="deck", aliases=["decks"], case_insensitive=True)
    async def tt_deck(self, ctx, *deck):
        deck, data = await TTDeck().convert(ctx, " ".join(deck))
        if not deck or deck is None:
            await ctx.send(
                "Available decks: {}".format(
                    ", ".join([f"**{x}**" for x in RAID_DECKS.keys()])
                )
            )
            return
        await ctx.send(
            "**{} Deck**\n\n**Core cards**\n{}\n\n**Optional cards**\n{}\n\n{}".format(
                deck.title(),
                ", ".join(
                    [
                        f"{discord.utils.get(self.bot.emojis, name=d.lower().replace(' ', '_'))} {d}"
                        for d in data[0]
                    ]
                ),
                data[1]
                and ", ".join(
                    [
                        f"{discord.utils.get(self.bot.emojis, name=d.lower().replace(' ', '_'))} {d}"
                        for d in data[1]
                    ]
                )
                or "n/a",
                data[2],
            )
        )

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
