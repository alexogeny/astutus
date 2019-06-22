import re
import asyncio
import io
from math import log10
from string import ascii_lowercase
import aiohttp
import discord
from discord.ext import commands as cmd
import arrow


def snake(text):
    return text.lower().replace(" ", "_").replace("'", "").replace("-", "")


def snake_get(func, term, arr):
    return next((a for a in arr if snake(func(a)) == term), None)


def rotate(table, mod):
    """Rotate a list."""
    return table[mod:] + table[:mod]


def lget(_list, idx, default):
    """Safely get a list index."""
    try:
        return _list[idx]
    except IndexError:
        return default


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


__scifi = re.compile(r"^([^a-z]+)([A-Za-z]+)$")
__lifi = re.compile(r"^([0-9\.]+)[^0-9]+([0-9,]+)$")


async def ttconvert_discover(number):
    if __lifi.match(number):
        return 0
    elif __scifi.match(number):
        return 1
    return 2


async def ttconvert_from_scientific(number):
    number, notation = __lifi.findall(number)[0]
    notation = int(notation.replace(",", "")) - 15
    modulo = notation % 3
    exponent = notation / 3
    output = []
    while exponent > 26:
        result, remainder = divmod(exponent, 26)
        output.append(remainder)
        exponent = result
    output.append(exponent)
    multiple = pow(10, modulo)
    l = len(output)
    if l > 2:
        output = [x for x in output[: -(l - 2)]] + [
            max(x - 1, 0) for x in output[-(l - 2) :]
        ]
    last_result = "".join([ascii_lowercase[int(last)] for last in output[::-1]])
    if len(last_result) == 1:
        last_result = "a" + last_result
    return "{}{}".format(int(float(number) * multiple), last_result)


async def ttconvert_to_scientific(number):
    number, letter = __scifi.findall(number)[0]
    map_to_alpha = [ascii_lowercase.index(x) for x in letter.lower()]
    a_to_one = [x + 1 for x in map_to_alpha[:-2]] + map_to_alpha[-2:]
    dict_map = dict(enumerate(a_to_one))
    map_to_alpha = [pow(26, x) for x in list(dict_map.keys())[::-1]]
    result = sum([x * a_to_one[i] for i, x in enumerate(map_to_alpha)])
    magnitude = int(log10(float(number)))
    number = float(number) / max((pow(10, magnitude)), 1)
    return "{}e{:,}".format(number, result * 3 + 15 + magnitude)
