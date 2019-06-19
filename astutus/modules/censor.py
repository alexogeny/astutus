import discord

from discord.ext import commands as cmd
import arrow
from utils import checks


class CensorModule(cmd.Cog):
    """A module for your Christian MineCraft server. Allows you to autodelete bad words with the bot, and optionally issue warnings for it. You can also set channels to be ignored."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.group(name="censor", hidden=True)
    @checks.is_mod()
    async def censor(self, ctx):
        return

    @censor.command(name="ignore")
    @checks.is_mod()
    async def censor_ignore(self, ctx, channels: cmd.Greedy[cmd.TextChannelConverter]):
        ign = await self.bot.db.hget(f"{ctx.guild.id}:set", "cen_ign")
        ign = ign and ign.split() or []
        if not channels:
            await ctx.send("Censor ignores the channels:")
        for c in channels:
            if not str(c.id) in ign:
                ign.append(str(c.id))
        ign = " ".join(ign)
        await self.bot.db.hset(f"{ctx.guild.id}:set", "cen_ign", ign)
        await ctx.send(
            "Added {} to the censor ignore list.".format(
                ", ".join([f"#**{c}**" for c in channels])
            )
        )

    @censor.command(name="unignore")
    @checks.is_mod()
    async def censor_unignore(
        self, ctx, channels: cmd.Greedy[cmd.TextChannelConverter]
    ):
        ign = await self.bot.db.hget(f"{ctx.guild.id}:set", "cen_ign")
        ign = ign and ign.split() or []
        removed = []
        if not channels:
            await ctx.send("Censor ignores the channels:")
        for c in channels:
            if str(c.id) in ign:
                removed.append(c)
                ign = [i for i in ign if i != str(c.id)]
        ign = " ".join(ign)
        await self.bot.db.hset(f"{ctx.guild.id}:set", "cen_ign", ign)
        await ctx.send(
            "Removed {} from the censor ignore list.".format(
                ", ".join([f"#**{c}**" for c in channels])
            )
        )

    @censor.command(name="add")
    @checks.is_mod()
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
            if len(word) < 3:
                not_added.append(word)
            elif word.lower() not in censored and len(censored) < 50:
                censored.append(word.lower())
                added.append(word.lower())
            elif word.lower() in censored and len(censored) <= 50:
                not_added.append(word)
            else:
                over_limit.append(word)
        if not added and not_added:
            await ctx.send("Did not add any words to censor.")
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
    @checks.is_mod()
    async def censor_remove(self, ctx, *, words: str):
        censored = await self.bot.db.hget(f"{ctx.guild.id}:set", "cen_wrd")
        censored = censored and censored.split() or []
        removed = []
        not_removed = []
        if not words:
            return
        words = words.split()
        for word in words:
            if word.lower() in censored and len(censored) > 0:
                removed.append(word.lower())
            else:
                not_removed.append(word)
        if not removed:
            await ctx.send("None of those words are in the censor.")
            return
        censored = [c for c in censored if c not in removed]
        await self.bot.db.hset(f"{ctx.guild.id}:set", "cen_wrd", " ".join(censored))
        await ctx.send(
            "Removed the following words from the censor: {}.".format(
                ", ".join([f"**{w}**" for w in words if w in removed])
            )
        )

    @cmd.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.guild_permissions.ban_members:
            return
        censor_on = await self.bot.db.hget(f"{message.guild.id}:toggle", "censor")
        if not censor_on or not int(censor_on):
            return
        ignored_channels = await self.bot.db.hget(f"{message.guild.id}:set", "cen_ign")
        if ignored_channels and str(message.channel.id) in ignored_channels:
            return
        censored_words = await self.bot.db.hget(f"{message.guild.id}:set", "cen_wrd")
        if not censored_words:
            return
        censored_words = censored_words.split()
        if any([w for w in censored_words if w in message.clean_content.lower()]):
            mod = self.bot.get_cog("ModerationModule")
            wid = arrow.utcnow().timestamp
            exp = arrow.get(9999999999)
            zs = await mod.warn_func(
                message.channel.guild.id, message.author.id, wid, exp.timestamp
            )
            await message.channel.send(
                "**{}** used a censored word. They now have **{}** warning{}.".format(
                    message.author, zs, zs != 1 and "s" or ""
                )
            )
            await message.delete()


def setup(bot):
    cog = CensorModule(bot)
    bot.add_cog(cog)
