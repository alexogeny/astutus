import aiohttp
import io
import discord
from discord.ext import commands as cmd


async def download_image(path):
    async with aiohttp.ClientSession() as session:
        async with session.get(path) as response:
            buffer = io.BytesIO(await response.read())

    return buffer
