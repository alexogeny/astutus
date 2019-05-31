import aiohttp
import io


async def download_image(path):
    async with aiohttp.ClientSession() as session:
        async with session.get(path) as response:
            buffer = io.BytesIO(await response.read())

    return buffer
