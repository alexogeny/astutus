from imgurpython import ImgurClient
import discord
from discord.ext import commands as cmd
from .utils.etc import download_image


class LoggingModule(cmd.Cog):
    """Automagically log message edits, deletes, user avatar changes, moderator actions, and so much more. You can access the settings of this module through the settings menu. Use **;help set log** for more info."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        self.imgur = ImgurClient(
            self.bot.config["IMGUR"]["client"], self.bot.config["IMGUR"]["secret"]
        )
        self.image_cache = {}
        self.avatar_cache = {}

    async def upload_to_imgur(self, url, anon=False):
        return self.imgur.upload_from_url(url, anon=anon)

    @cmd.Cog.listener()
    async def on_member_join(self, member):
        log_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "log")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{member.guild.id}:set", "l_usr")
        if not log_chan:
            return
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        await chan.send(":inbox_tray: **{member}** joined the server")

    @cmd.Cog.listener()
    async def on_member_remove(self, member):
        log_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "log")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{member.guild.id}:set", "l_usr")
        if not log_chan:
            return
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        await chan.send(":outbox_tray: **{member}** left the server")

    @cmd.Cog.listener()
    async def on_message_edit(self, before, after):
        if not hasattr(after, "guild") or after.author.bot:
            return
        # print(payload.data)
        log_is_on = await self.bot.db.hget(f"{before.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{before.guild.id}:set", "logmessages")
        if not log_chan or log_chan is None:
            return
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{before.guild.id}:set", "logmessages")
            return
        embed = discord.Embed(
            title=f"Message by @**{before.author}** in #**{before.channel}** was edited",
            description=f"{before.author.mention} (ID: {before.author.id})",
        )
        embed.add_field(
            name="Content Before", value=before.content[0:400], inline=False
        )
        embed.add_field(name="Content After", value=after.content[0:400], inline=False)
        try:
            await chan.send(embed=embed)
        except discord.errors.HTTPException:
            pass

    @cmd.Cog.listener()
    async def on_message(self, message):
        if not hasattr(message, "guild"):
            return
        attch = []
        if message.attachments:
            for attachment in message.attachments:
                if any([x in attachment.url for x in [".gif", ".jpg", ".png"]]):
                    print(attachment.url)
                    i = await self.upload_to_imgur(attachment.url, anon=True)
                    attch.append(i["link"])
        if attch:
            self.image_cache[message.id] = attch

    @cmd.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        attch = self.image_cache.get(message.id, [])
        print(attch)
        log_is_on = await self.bot.db.hget(f"{message.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{message.guild.id}:set", "logmessages")
        if not log_chan or log_chan is None:
            return
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{message.guild.id}:set", "logmessages")
            return
        embed = discord.Embed(
            title=f"Message by @**{message.author}** in #**{message.channel}** was deleted",
            description=f"{message.author.mention} (ID: {message.author.id})",
        )
        embed.add_field(
            name="Content",
            value=message.content[0:900] or "No message content detected.",
        )
        if attch:
            embed.add_field(name="Images", value="\n".join([a for a in attch]))
            embed.set_image(url=attch[0])
        await chan.send("", embed=embed)

    @cmd.Cog.listener()
    async def on_user_update(self, before, after):
        if before.bot:
            return
        i = None
        if before.avatar != after.avatar:
            i = await self.upload_to_imgur(
                str(after.avatar_url_as(static_format="png", size=1024)), anon=True
            )
            self.avatar_cache[str(after.id)] = i["link"]
        chans_to_log_avatars = []
        for guild in self.bot.guilds:
            log_is_on = await self.bot.db.hget(f"{guild.id}:toggle", "logging")
            if log_is_on in (None, "0"):
                return
            log_chan = await self.bot.db.hget(f"{guild.id}:set", "logavatars")
            if not log_chan or log_chan is None:
                return
            chan = self.bot.get_channel(int(log_chan))
            if chan is None:
                await self.bot.db.hdel(f"{guild.guild.id}:set", "logavatars")
            else:
                chans_to_log_avatars.append(chan)
        if chans_to_log_avatars:
            embed = discord.Embed(title=f"**{after}**'s new avatar")
            embed.set_image(url=self.avatar_cache[str(after.id)])
            for chan in chans_to_log_avatars:
                async with chan.typing():
                    await chan.send(embed=embed)

    @cmd.Cog.listener()
    async def on_bulk_message_delete(self, payload):
        return

    @cmd.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_is_on = await self.bot.db.hget(f"{channel.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{channel.guild.id}:set", "logchannels")
        if not log_chan or log_chan is None:
            return
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{channel.guild.id}:set", "logchannels")
            return
        embed = discord.Embed(title=f"Channel #**{channel}** was **deleted**")
        embed.add_field(name="Category", value=channel.category)
        await chan.send("", embed=embed)

    @cmd.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_is_on = await self.bot.db.hget(f"{channel.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{channel.guild.id}:set", "logchannels")
        if not log_chan or log_chan is None:
            return
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{channel.guild.id}:set", "logchannels")
            return
        embed = discord.Embed(title=f"Channel #**{channel}** was **created**")
        embed.add_field(name="Category", value=channel.category)
        await chan.send("", embed=embed)

    @cmd.Cog.listener()
    async def on_guild_role_create(self, role):
        return

    @cmd.Cog.listener()
    async def on_guild_role_delete(self, role):
        return

    async def on_member_ban(self, g, u):
        return

    async def on_member_unban(self, g, u):
        return

    async def on_member_mute(self, g, u):
        return

    async def on_member_unmute(self, g, u):
        return

    async def on_member_kick(self, g, u):
        return


def setup(bot):
    bot.add_cog(LoggingModule(bot))
