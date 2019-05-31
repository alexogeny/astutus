import discord
import typing
import asyncio
from discord.ext import commands as cmd
import arrow


class TrackingModule(object):
    """docstring for TrackingModule"""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.command()
    async def seen(self, ctx: cmd.Context, user: MemberID = None):
        if user is None:
            user = ctx.author.id
        ls_unknown = False
