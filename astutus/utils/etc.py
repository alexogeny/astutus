import aiohttp
import io
import discord
from discord.ext import commands as cmd
import arrow
import asyncio


async def download_image(path):
    async with aiohttp.ClientSession() as session:
        async with session.get(path) as response:
            buffer = io.BytesIO(await response.read())

    return buffer


async def choose_from(ctx, choices, text, timeout=10):
    chooser = await ctx.send(text)

    def check(m):
        if m.author == ctx.author:
            return m.content.isnumeric() or m.content.lower().strip() == "c"
        return False

    try:
        msg = await ctx.bot.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        await msg.channel.send(f"**{ctx.author}**'s query timed out.")
        await chooser.delete()
        raise cmd.BadArgument("Timed out")
    else:
        if msg.content.lower() == "c":
            await chooser.delete()
            await msg.channel.send(f"**{ctx.author}**'s query was cancelled.")
            raise cmd.BadArgument("Timed out")
        i = int(msg.content) - 1
        if i > -1 and i < len(choices):
            await chooser.delete()
            return choices[i]


async def search_for(items, term):
    return [items.index(x) for x in items if term in x]
