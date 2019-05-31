import asyncio
import discord


def setup_bot(bot):
    @bot.check
    async def globally_block_bots(ctx):
        return not ctx.author.bot

    @bot.check
    async def global_blacklist(ctx):
        blacklists = ctx.bot.blacklists
        return not any(
            (
                ctx.author.id in blacklists["users"],
                ctx.guild.id in blacklists["servers"],
                ctx.channel.id in blacklists["channels"],
            )
        )
