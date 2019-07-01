import asyncio
import arrow
import discord
from discord.ext import commands as cmd
from .utils import checks


class WorldChatModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    async def wc_enabled(self, message):
        if not hasattr(message, "guild") or message.author.bot:
            return False
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return False
        wch = int(await self.bot.db.hget("worldchat", message.guild.id) or 0)
        if wch != message.channel.id:
            return False
        now = arrow.utcnow()
        last_send = await self.bot.db.hget("worldchats", message.author.id)
        if last_send is None:
            last_send = now.shift(hours=-1)
        else:
            last_send = arrow.get(last_send)
        if now > last_send.shift(seconds=5):
            await self.bot.db.hset("worldchats", message.author.id, now.timestamp)
            return True
        return False

    @cmd.Cog.listener()
    async def on_message(self, message):
        if not await self.wc_enabled(message):
            return
        await asyncio.sleep(2)
        attch = await self.bot.db.hget("image_cache", message.id)
        embed = await self.bot.embed()
        embed.title = str(message.author)
        if message.content:
            embed.description = message.content[0:300]
        if attch:
            attch = attch.split()
            embed.add_field(name="Images", value="\n".join([a for a in attch]))
            embed.set_image(url=attch[0])
        chats = await self.bot.db.hgetall("worldchat")
        censored = self.bot.profanity.censor(embed.description, "\\*")
        for guild, chat in chats.items():
            guild_obj = self.bot.get_guild(int(guild))
            if guild_obj is not None and int(guild) != message.guild.id:
                chan = guild_obj.get_channel(int(chat))
                if chan is not None:
                    censor = int(
                        await self.bot.db.hget("worldchatc", guild_obj.id) or 0
                    )
                    if not censor:
                        embed.description = censored
                    await chan.send(embed=embed)


def setup(bot):
    bot.add_cog(WorldChatModule(bot))
