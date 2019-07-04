import mimetypes
import discord
from discord.ext import commands as cmd


class StarboardModule(cmd.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def can_star(self, user):
        curator = int(
            await self.bot.db.hget(f"{user.guild.id}:set", "rolecurator") or 0
        )
        curator = user.guild.get_role(curator)
        return user.guild_permissions.ban_members or curator in user.roles

    @cmd.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != "⭐":
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not hasattr(channel, "guild"):
            return
        enabled = await self.bot.db.hget(f"{channel.guild.id}:toggle", "starboard")
        if enabled is None or enabled == "0":
            return
        member = channel.guild.get_member(payload.user_id)
        if member.bot or not await self.can_star(member):
            return
        quote_chan = int(
            await self.bot.db.hget(f"{channel.guild.id}:set", "channelstarboard") or 0
        )
        quote_chan = channel.guild.get_channel(quote_chan)
        if quote_chan is None:
            return
        quote_list = await self.bot.db.lrange(f"{channel.guild.id}:starboard")
        if str(payload.message_id) in quote_list:
            return
        message = await channel.fetch_message(payload.message_id)
        await self.bot.db.rpush(f"{channel.guild.id}:starboard", message.id)
        await self.bot.db.zincrement("starboard", channel.guild.id)
        quote_number = await self.bot.db.zscore("starboard", channel.guild.id)
        embed = await self.bot.embed()
        i = await self.bot.db.hget("avatar_cache", message.author.id)
        if not i or i is None:
            url = message.author.avatar_url_as(static_format="png", size=1024)
            urls = str(url).split("/")[-1].split("?")[0]
            ctype, _ = mimetypes.guess_type(urls)
            ext = ctype.split("/")[-1]
            i = await self.bot.cdn.upload_file("u", message.author.id, url, ext, ctype)
            await self.bot.db.hset("avatar_cache", message.author.id, i)
        embed.set_thumbnail(url=i)
        i = await self.bot.db.hget("avatar_cache", member.id)
        if not i or i is None:
            url = member.avatar_url_as(static_format="png", size=1024)
            urls = str(url).split("/")[-1].split("?")[0]
            ctype, _ = mimetypes.guess_type(urls)
            ext = ctype.split("/")[-1]
            i = await self.bot.cdn.upload_file("u", member.id, url, ext, ctype)
            await self.bot.db.hset("avatar_cache", member.id, i)
        embed.set_author(name=f"⭐ added by @{member}", icon_url=i)
        embed.description = "Quote #**{}** in {} by {}\n[Message Link]({})".format(
            quote_number, channel.mention, message.author.mention, message.jump_url
        )
        embed.colour = 0xE2B031

        if message.content:
            embed.description = "{}\n\n{}".format(
                embed.description, message.content[0:1500]
            )

        attch = await self.bot.db.hget("image_cache", message.id)
        if attch:
            attch = next(iter(attch.split()), None)
            if attch is not None:
                embed.set_image(url=attch)

        await quote_chan.send(embed=embed)


def setup(bot):
    bot.add_cog(StarboardModule(bot))
