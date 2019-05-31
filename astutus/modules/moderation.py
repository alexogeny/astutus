import discord
import arrow
from typing import List, Optional
from discord.ext import commands as cmd
from astutus.utils import checks, MemberID, ActionReason, BannedMember, Delta
from uuid import uuid4
from copy import deepcopy


async def bulk_mod(ctx, kind: str, members: List[int], reason: str):
    done = []
    for member in members:
        member_object = discord.utils.get(ctx.guild.members, id=member)
        await getattr(member_object, kind)(reason=reason)
        done.append(member_object)
    return done


class ModerationModule(object):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.mutes = []
        self.warnings = []
        self.autokicks = []

    async def warn_count(self, member: int, guild: int):
        return len(
            [
                warning
                for warning in self.warnings
                if warning[0] == member
                and warning[1] == guild
                and warning[2] < arrow.utcnow().timestamp()
            ]
        )

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

    @cmd.command()
    @cmd.guild_only()
    @checks.can_kick()
    async def kick(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        duration: Optional[Delta],
        *,
        reason: ActionReason,
    ):
        kicked = await bulk_mod(ctx, "kick", members, reason)
        kicked = ", ".join([f"**{k}**" for k in kicked])
        await ctx.send(f"**{ctx.author}** kicked {kicked}.")

    @cmd.command()
    @cmd.guild_only()
    @checks.can_ban()
    async def ban(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        duration: Optional[Delta],
        *,
        reason: ActionReason,
    ):
        banned = await bulk_mod(ctx, "ban", members, reason)
        banned = ", ".join([f"**{k}**" for k in banned])
        await ctx.send(f"**{ctx.author}** banned {banned}.")

    @cmd.command()
    @cmd.guild_only()
    @checks.can_ban()
    async def unban(
        self,
        ctx: cmd.Context,
        members: cmd.Greedy[MemberID],
        duration: Optional[Delta],
        *,
        reason: ActionReason,
    ):
        unbanned = await bulk_mod(ctx, "unban", members, reason)
        unbanned = ", ".join([f"**{k}**" for k in unbanned])
        await ctx.send(f"**{ctx.author}** unbanned {unbanned}.")
