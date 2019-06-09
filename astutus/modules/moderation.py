import discord
import arrow
from typing import List, Optional
from discord.ext import commands as cmd
from discord.ext import tasks as tsk
from astutus.utils import (
    checks,
    MemberID,
    ActionReason,
    BannedMember,
    delta_convert,
    Duration,
)
from uuid import uuid4
from copy import deepcopy
from itertools import chain


async def bulk_mod(ctx, kind: str, members: List[int], reason: str):
    done = []
    for member in members:
        member_object = await ctx.bot.fetch_user(member)
        try:
            await getattr(ctx.guild, kind)(member_object, reason=reason)
        except:
            pass
        done.append(member_object)
    return done


class ModerationModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.unmute_timer.start()
        self.unban_timer.start()

    def cog_unload(self):
        self.unmute_timer.cancel()
        # self.unwarn_timer.cancel()
        self.unban_timer.cancel()
        # self.unjail_timer.cancel()

    @tsk.loop(seconds=10)
    async def unmute_timer(self):
        now = arrow.utcnow()
        for guild in self.bot.guilds:
            to_action = await self.bot.db.zbyscore(
                f"{guild.id}:mutes", now.shift(seconds=-11).timestamp, now.timestamp
            )
            if to_action:
                role = await self.get_or_create_muted_role(guild)
                for action in to_action:
                    yes = guild.get_member(int(action))
                    if yes:
                        await yes.remove_roles(role, reason="Mute expired")
                await self.bot.db.zrembyscore(
                    f"{guild.id}:mutes", now.shift(seconds=-11).timestamp, now.timestamp
                )

    @tsk.loop(seconds=10)
    async def unban_timer(self):
        now = arrow.utcnow()
        for guild in self.bot.guilds:
            to_action = await self.bot.db.zbyscore(
                f"{guild.id}:bans", now.shift(seconds=-11).timestamp, now.timestamp
            )
            if to_action:
                for action in to_action:
                    usr = await self.bot.fetch_user(action)
                    await guild.unban(usr, reason="ban expired")
                await self.bot.db.zrembyscore(
                    f"{guild.id}:bans", now.shift(seconds=-11).timestamp, now.timestamp
                )

    @unban_timer.before_loop
    async def before_unban_timer(self):
        await self.bot.wait_until_ready()

    @unmute_timer.before_loop
    async def before_unmute_timer(self):
        await self.bot.wait_until_ready()

    async def mute_muted_role(self, role: discord.Role, guild: discord.Guild):
        for channel in guild.channels:
            perms = channel.overwrites_for(role)
            if (
                type(channel) is discord.TextChannel
                and not perms.send_messages == False
            ):
                try:
                    await channel.set_permissions(
                        role, send_messages=False, add_reactions=False
                    )
                except:
                    pass
            elif type(channel) is discord.VoiceChannel and not perms.speak == False:
                try:
                    await channel.set_permissions(role, speak=False)
                except:
                    pass

    async def create_muted_role(self, guild):
        perms = discord.Permissions()
        perms.update(
            send_messages=False,
            read_messages=True,
            add_reactions=False,
            create_instant_invite=False,
            embed_links=False,
            attach_files=False,
            mention_everyone=False,
            speak=False,
            connect=True,
        )
        role = await guild.create_role(
            name="Muted",
            permissions=perms,
            colour=discord.Colour(0xE74C3C),
            reason="Creating Muted role since one does not exist already.",
        )
        await self.mute_muted_role(role, guild)
        await self.bot.db.hset(f"{guild.id}:role", "muted", role.id)
        return role

    async def get_muted_role(self, guild):
        r = await self.bot.db.hget(f"{guild.id}:role", "muted")
        if r:
            found = guild.get_role(int(r))
            if found:
                return found
        return

    async def get_or_create_muted_role(self, guild):
        r = await self.get_muted_role(guild)
        if not r:
            r = await self.create_muted_role(guild)
        return r

    @cmd.command()
    @cmd.guild_only()
    @checks.can_kick()
    async def kick(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        *,
        reason: ActionReason = None,
    ):
        kicked = await bulk_mod(ctx, "kick", members, reason)
        kicked = ", ".join([f"**{k}**" for k in kicked])
        await ctx.send(f"**{ctx.author}** kicked {kicked}.")

    @cmd.command()
    @cmd.guild_only()
    @checks.can_kick()
    async def warn(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        duration: Optional[Duration],
        *,
        reason: ActionReason = None,
    ):
        wid = arrow.utcnow().timestamp
        if duration == None or not duration:
            duration = arrow.get(9999999999)
        if len(members) > 1:
            result = []
            for m in members:
                mem = ctx.guild.get_member(m)
                if mem:
                    zs = await self.bot.db.zincrement(f"{ctx.guild.id}:wrncnt", m)
                    await self.bot.db.zadd(
                        f"{ctx.guild.id}:wrn", f"{m}.{wid}", duration.timestamp
                    )
                    result.append(mem)
            result = ", ".join([f"**{k}**" for k in result])
            duration = duration.humanize()
            if duration == "just now":
                duration = "shortly"
            await ctx.send(f"**{ctx.author}** warned {result}.")
            return
        elif len(members) == 0:
            return
        mem = ctx.guild.get_member(members[0])
        zs = await self.bot.db.zincrement(f"{ctx.guild.id}:wrncnt", members[0])
        await self.bot.db.zadd(
            f"{ctx.guild.id}:wrn", f"{members[0]}.{wid}", duration.timestamp
        )
        await ctx.send(
            "**{}** warned **{}**. They now have **{}** warning{}.".format(
                ctx.author, mem, zs, int(zs) > 1 and "s" or ""
            )
        )

    @cmd.command(name="warnings")
    async def warnings(self, ctx, member: Optional[cmd.MemberConverter]):
        if not member:
            member = ctx.author
        zs = await self.bot.db.zscore(f"{ctx.guild.id}:wrncnt", member.id)
        await ctx.send(
            "**{}** has **{}** warning{}".format(member, zs, int(zs) != 1 and "s" or "")
        )

    @cmd.command(name="mutewarn")
    async def mutewarn(self, ctx):
        await self.mute.invoke(await self.bot.get_context(ctx.message))
        await self.warn.invoke(await self.bot.get_context(ctx.message))

    @cmd.command()
    @cmd.guild_only()
    @checks.can_kick()
    async def pardon(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        *,
        reason: ActionReason = None,
    ):
        if len(members) > 1:
            pardoned = []
            for m in members:
                warnings = await self.bot.db.zscore(f"{ctx.guild.id}:wrncnt", m)
                warnings = int(warnings)
                if warnings > 0:
                    await self.bot.db.zincrement(f"{ctx.guild.id}:wrncnt", m, score=-1)
                    to_delete = await self.bot.db.zscan(
                        f"{ctx.guild.id}:wrn", m, count=1
                    )
                    if to_delete:
                        await self.bot.db.zrem(f"{ctx.guild.id}:wrn", to_delete[0])
                    pardoned.append(ctx.guild.get_member(m))
            result = ", ".join([f"**{k}**" for k in pardoned])
            await ctx.send(f"**{ctx.author}** pardoned {result}.")
        elif len(members) == 0:
            return
        m = members[0]
        mem = ctx.guild.get_member(m)
        warnings = await self.bot.db.zscore(f"{ctx.guild.id}:wrncnt", m)
        warnings = int(warnings)
        if warnings > 0:
            zs = await self.bot.db.zincrement(f"{ctx.guild.id}:wrncnt", m, score=-1)
            to_delete = await self.bot.db.zscan(
                f"{ctx.guild.id}:wrn", match=f"{m}.", count=1
            )
            if len(to_delete) / 2 > 1:
                to_delete = to_delete[1][0]
                await self.bot.db.zrem(f"{ctx.guild.id}:wrn", to_delete)
            await ctx.send(
                "**{}** pardoned **{}**. They now have **{}** warning{}.".format(
                    ctx.author, mem, zs, int(zs) != 1 and "s" or ""
                )
            )

    @cmd.command()
    @cmd.guild_only()
    @checks.can_kick()
    async def mute(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        duration: Optional[Duration],
        *,
        reason: ActionReason = None,
    ):
        if duration == None or not duration:
            duration = arrow.get(7559466982)
        role = await self.get_or_create_muted_role(ctx.guild)
        await self.mute_muted_role(role, ctx.guild)
        result = []
        for m in members:
            mem = ctx.guild.get_member(m)
            if mem:
                await mem.add_roles(role)
                await self.bot.db.zadd(f"{ctx.guild.id}:mutes", m, duration.timestamp)
                result.append(mem)
        result = ", ".join([f"**{k}**" for k in result])
        duration = duration.humanize()
        if duration == "just now":
            duration = "now"
        await ctx.send(
            f"**{ctx.author}** muted {result}. They will be unmuted **{duration}**."
        )

    @cmd.command()
    @cmd.guild_only()
    @checks.can_kick()
    async def unmute(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        *,
        reason: ActionReason = None,
    ):
        role = await self.get_or_create_muted_role(ctx.guild)
        await self.mute_muted_role(role, ctx.guild)
        result = []
        for m in members:
            mem = ctx.guild.get_member(m)
            if mem:
                await mem.remove_roles(role)
                await self.bot.db.zrem(f"{ctx.guild.id}:mutes", m)
                result.append(mem)
        result = ", ".join([f"**{k}**" for k in result])
        await ctx.send(f"**{ctx.author}** unmuted {result}.")

    @cmd.command()
    @cmd.guild_only()
    @checks.can_ban()
    async def ban(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        duration: Optional[Duration],
        *,
        reason: ActionReason = None,
    ):
        if duration == None or not duration:
            duration = arrow.get(7559466982)
        banned = await bulk_mod(ctx, "ban", members, reason)
        for b in banned:
            await self.bot.db.zadd(f"{ctx.guild.id}:bans", b.id, duration.timestamp)
        result = ", ".join([f"**{k}**" for k in banned])
        duration = duration.humanize()
        if duration == "just now":
            duration = "now"
        await ctx.send(
            f"**{ctx.author}** banned {result}. They will be unbanned **{duration}**."
        )

    @cmd.command()
    @cmd.guild_only()
    @checks.can_ban()
    async def unban(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        *,
        reason: ActionReason = None,
    ):
        unbanned = await bulk_mod(ctx, "unban", members, reason)
        for b in unbanned:
            await self.bot.db.zrem(f"{ctx.guild.id}:bans", b.id)
        unbanned = ", ".join([f"**{k}**" for k in unbanned])
        await ctx.send(f"**{ctx.author}** unbanned {unbanned}.")

    @cmd.command(aliases=["nick"])
    @cmd.guild_only()
    @checks.can_manage_nicknames()
    async def nickname(self, ctx, member: MemberID, *nickname):
        member = discord.utils.get(ctx.guild.members, id=member)
        if member.top_role > ctx.author.top_role:
            await ctx.send(
                f"Sorry **{ctx.author}** - you must be higher in the rolelist to do that."
            )
            return
        old_nick = str(member.display_name)
        nickname = " ".join(nickname)[0:32]
        if not nickname:
            nickname = member.name
        try:
            await member.edit(
                reason=f"{ctx.author} (ID: {ctx.author.id})", nick=nickname
            )
        except discord.errors.Forbidden:
            await ctx.send(
                "Oops, I do not have permission. A server admin should fix this."
            )
        else:
            await ctx.send(
                f"Changed **{member}**'s nick from **{old_nick}** to **{nickname}**."
            )

    @cmd.Cog.listener()
    async def on_member_join(self, member):
        result = await self.bot.db.zscore(f"{member.guild.id}:mutes", member.id)
        if result is None:
            return
        if int(result) == 0:
            return
        role = await self.get_or_create_muted_role(member.guild)
        await self.mute_muted_role(role, member.guild)
        await member.add_roles(role)

    @cmd.Cog.listener()
    async def on_guild_role_update(self, b, a):
        r = await self.get_or_create_muted_role(b.guild)
        if b.id == r.id:
            await self.mute_muted_role(r, b.guild)

    @cmd.Cog.listener()
    async def on_guild_role_delete(self, r):
        r2 = await self.get_or_create_muted_role(r.guild)
        await self.mute_muted_role(r2, r.guild)


def setup(bot):
    cog = ModerationModule(bot)
    bot.add_cog(cog)
