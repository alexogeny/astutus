import discord
import typing
import asyncio
from discord.ext import commands as cmd
from astutus.utils import MemberID, checks, ActionReason, BannedMember
import arrow
from itertools import starmap


class TrackingModule(cmd.Cog):
    """docstring for TrackingModule"""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.cap = self.bot.config["TRACKING"]["history"]

    @cmd.command()
    async def seen(self, ctx: cmd.Context, user: MemberID = None):
        if user is None:
            user = ctx.author.id
        obj = await self.bot.db.hget("tr:ls", user)
        user = await self.bot.fetch_user(user)
        if not obj:
            await ctx.send(f"I have not seen **{user}** before.")
            return
        now = arrow.get(obj)
        await ctx.send(f"The last time I saw **{user}** was **{now.humanize()}**")

    async def track_last_seen(self, member):
        await self.bot.db.hset("tr:ls", member, arrow.utcnow().timestamp)

    async def track_username(self, member, username):
        obj = f"tr:un:{member.id}"
        names = await self.bot.db.lrange(obj, 0, -1)
        if username not in names:
            await self.bot.db.rpush(obj, username)
        if await self.bot.db.llen(obj) > self.cap:
            await self.bot.db.lpop(obj)

    async def track_nickname(self, member, nickname):
        obj = f"tr:nn:{member.guild.id}:{member.id}"
        nicks = await self.bot.db.lrange(obj, 0, -1)
        if nickname not in nicks:
            await self.bot.db.rpush(obj, nickname)
        if await self.bot.db.llen(obj) > self.cap:
            await self.bot.db.lpop(obj)

    @cmd.Cog.listener()
    async def on_guild_join(self, guild):
        updates = (
            m.id for m in guild.members if m.status is not discord.Status.offline
        )
        to_update = starmap(self.track_last_seen, updates)
        await asyncio.gather(*to_update)

    @cmd.Cog.listener()
    async def on_member_update(self, before, member):
        if before.status != member.status:
            await self.track_last_seen(member.id)
        if before.name != member.name:
            await self.track_last_seen(member.id)
            await self.track_username(member, before.name)
        nick_before = before.display_name
        nick_after = member.display_name
        if nick_before != nick_after and hasattr(member, "guild"):
            await self.track_last_seen(member.id)
            await self.track_nickname(member, nick_before)

    @cmd.Cog.listener()
    async def on_typing(self, channel, member, when):
        await self.track_last_seen(member.id)

    @cmd.Cog.listener()
    async def on_member_join(self, member):
        await asyncio.gather(self.track_last_seen(member.id))


def setup(bot):
    cog = TrackingModule(bot)
    bot.add_cog(cog)
