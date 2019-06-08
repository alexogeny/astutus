import discord

from discord.ext import commands as cmd

from astutus.utils import checks


class CensorModule(cmd.Cog):
    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.group(name="censor")
    @checks.is_mod()
    async def censor(self, ctx):
        return

    @censor.command(name="add")
    async def censor_add(self, ctx, *, words: str):
        censored = await self.bot.db.hget(f"{ctx.guild.id}:set", "cen_wrd")
        censored = censored and censored.split() or []
        not_added = []
        added = []
        over_limit = []
        if not words:
            return
        words = words.split()
        for word in words:
            if word.lower() not in censored and len(censored) < 50:
                censored.append(word.lower())
                added.append(word.lower())
            elif word.lower() in censored and len(censored) <= 50:
                not_added.append(word)
            else:
                over_limit.append(word)
        if not added and not_added:
            await ctx.send("All words currently exist in censor.")
            return
        await self.bot.db.hset(f"{ctx.guild.id}:set", "cen_wrd", " ".join(censored))

        if not_added:
            not_added = "\nDid not add words that exist in censor: {}.".format(
                ", ".join([f"**{w}**" for w in not_added])
            )
        if over_limit:
            over_limit = "\nDid not add words that exceed the limit of 50 censored words: {}.".format(
                ", ".join([f"**{w}**" for w in over_limit])
            )
        await ctx.send(
            "Added the following words to the censor: {}.{}{}".format(
                ", ".join([f"**{w}**" for w in words if w not in not_added]),
                not_added or "",
                over_limit or "",
            )
        )

    @censor.command(name="remove")
    async def censor_remove(self, ctx, *words: str):
        return

    @cmd.Cog.listener()
    async def on_message(self, message):
        censor_on, not_ignored_chan, censored_words = None, None, None


def setup(bot):
    cog = CensorModule(bot)
    bot.add_cog(cog)
