import re
import asyncio
import arrow
from discord.ext import commands as cmd

URL = re.compile(
    r"(?:(?:https?|ftp|file|mailto):?)(?://)?(?:[-\w.]|(?:%[\da-fA-F]{2}))+|(?:[\w:]+\@\w+\.\w+)"
)
VISA = re.compile(r"(4[0-9]{3})[\W\s-]?([0-9]{4}[\W\s-]?){3}")
MSTR = re.compile(
    r"(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}"
)
AMEX = re.compile(r"3[47][0-9]{13}")
DNRS = re.compile(r"3(?:0[0-5]|[68][0-9])[0-9]{11}")
DSCV = re.compile(r"6(?:011|5[0-9]{2})[0-9]{12}")
RET = re.compile(r"\n\n")


class WorldChatModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    async def wc_enabled(self, message):
        if not hasattr(message, "guild") or message.author.bot:
            return False
        log_is_on = await self.bot.db.hget(f"{message.guild.id}:toggle", "worldchat")
        if log_is_on in (None, "0"):
            return
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return False
        wch = int(
            await self.bot.db.hget(f"{message.guild.id}:set", "channelworldchat") or 0
        )
        if wch != message.channel.id:
            return False
        now = arrow.utcnow()
        last_send = await self.bot.db.hget("worldchats", message.author.id)
        if last_send is None:
            last_send = now.shift(hours=-1)
        else:
            last_send = arrow.get(last_send)
        if now > last_send.shift(seconds=60):
            await self.bot.db.hset("worldchats", message.author.id, now.timestamp)
            return True
        return False

    @cmd.Cog.listener()
    async def on_message(self, message):
        if not message.content or message.content is None:
            return
        any_match = [
            X.findall(message.content) for X in [URL, VISA, MSTR, AMEX, DNRS, DSCV]
        ]
        if any(any_match):
            return
        if not await self.wc_enabled(message):
            return

        embed = await self.bot.embed()
        embed.title = str(message.author)

        embed.description = RET.sub("", message.content[0:300]).replace("\n", " ")

        chats = await asyncio.gather(
            *[
                self.bot.db.hget(f"{g.id}:set", "channelworldchat")
                for g in self.bot.guilds
            ]
        )
        uncensored = embed.description
        censored = self.bot.profanity.censor(embed.description, "\\*")
        for chat in [c for c in chats if c not in ("0", None)]:
            chn = await self.bot.fetch_channel(int(chat))
            if chn is not None:
                # guild_obj = self.bot.get_guild(chn.guild)
                if chn.guild != message.guild:
                    censor = int(
                        await self.bot.db.hget("worldchatc", chn.guild.id) or 0
                    )
                    if not censor:
                        embed.description = censored
                    await chn.send(embed=embed)
                    embed.description = uncensored


def setup(bot):
    bot.add_cog(WorldChatModule(bot))
