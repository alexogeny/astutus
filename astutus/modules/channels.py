from typing import Optional
from discord.ext import commands as cmd
from astutus.utils import checks, ChannelID, Duration


class ChannelObject(cmd.TextChannelConverter):
    async def convert(self, ctx: cmd.Context, channel):
        channel = await super().convert(ctx, channel)
        return channel


class ChannelsModule(object):
    def __init__(self, bot):
        self.bot = bot

    @cmd.command()
    @checks.can_manage_channels()
    async def slowmode(
        self,
        ctx: cmd.Context,
        channel: ChannelID,
        expires: Optional[Duration],
        *,
        mode=None,
    ):
        if not channel:
            channel = ctx.channel.id
        channel = ctx.guid.get_channel(channel)
        if mode is None:
            await ctx.send(
                f"Slowmode for #**{channel}** is set to: **{channel.slowmode_delay}** seconds."
            )
            return
        mode = mode is not None and mode.isdigit() and int(mode)
        if mode not in range(0, 121):
            await ctx.send(
                "You must specify a slowmode between **0** and **120** seconds."
            )
            return
        await channel.edit(slowmode_delay=mode)
        await ctx.send(f"Set the slowmode for #**{channel}** to **{mode}** seconds.")
