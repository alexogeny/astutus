# from imgurpython import ImgurClient
import mimetypes
import discord
import arrow
from discord.ext import commands as cmd


class LoggingModule(cmd.Cog):
    """Automagically log message edits, deletes, user avatar changes, moderator actions, and so much more. You can access the settings of this module through the settings menu. Use **;help set log** for more info."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot
        # self.imgur = ImgurClient(
        #     self.bot.config["IMGUR"]["client"], self.bot.config["IMGUR"]["secret"]
        # )

    # async def upload_to_imgur(self, url, anon=False):
    #     return self.imgur.upload_from_url(url, anon=anon)

    @cmd.Cog.listener()
    async def on_member_join(self, member):
        log_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{member.guild.id}:set", "logjoins")
        if not log_chan:
            return
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        embed = discord.Embed(
            title=f"**{member}** joined **{member.guild}**",
            description=f"{member.mention} (ID: {member.id})",
            color=0x36CE31,
        )
        i = await self.bot.db.hget("avatar_cache", member.id)
        if not i or i is None:
            url = member.avatar_url_as(static_format="png", size=1024)
            urls = str(url).split("/")[-1].split("?")[0]
            ctype, _ = mimetypes.guess_type(urls)
            ext = ctype.split("/")[-1]
            i = await self.bot.cdn.upload_file("u", member.id, url, ext, ctype)
            await self.bot.db.hset("avatar_cache", member.id, i)
        embed.set_thumbnail(url=i)
        await chan.send(embed=embed)

    @cmd.Cog.listener()
    async def on_member_remove(self, member):
        log_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{member.guild.id}:set", "logleaves")
        if not log_chan:
            return
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        embed = discord.Embed(
            title=f"**{member}** left **{member.guild}**",
            description=f"{member.mention} (ID: {member.id})",
            color=0xFF0000,
        )
        i = await self.bot.db.hget("avatar_cache", member.id)
        if not i or i is None:
            url = member.avatar_url_as(static_format="png", size=1024)
            urls = str(url).split("/")[-1].split("?")[0]
            ctype, _ = mimetypes.guess_type(urls)
            ext = ctype.split("/")[-1]
            i = await self.bot.cdn.upload_file("u", member.id, url, ext, ctype)
            await self.bot.db.hset("avatar_cache", member.id, i)
        embed.set_thumbnail(url=i)
        await chan.send(embed=embed)

    @cmd.Cog.listener()
    async def on_message_edit(self, before, after):
        if not hasattr(after, "guild") or after.author.bot:
            return
        log_is_on = await self.bot.db.hget(f"{before.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{before.guild.id}:set", "logedits")
        if not log_chan or log_chan is None:
            return
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{before.guild.id}:set", "logedits")
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
        if message.attachments and not message.channel.nsfw:
            for attachment in message.attachments:
                if any([x in attachment.url for x in [".gif", ".jpg", ".png"]]):
                    url = attachment.url
                    ctype, _ = mimetypes.guess_type(str(url))
                    ext = attachment.filename.split(".")[-1]
                    i = await self.bot.cdn.upload_file(
                        "message", message.id, attachment, ext, ctype
                    )
                    attch.append(i)
        if attch:
            await self.bot.db.hset("image_cache", message.id, " ".join(attch))

    @cmd.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        attch = await self.bot.db.hget("image_cache", message.id)
        log_is_on = await self.bot.db.hget(f"{message.guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{message.guild.id}:set", "logdeletes")
        if not log_chan or log_chan is None:
            return
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{message.guild.id}:set", "logdeletes")
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
            attch = attch.split()
            embed.add_field(name="Images", value="\n".join([a for a in attch]))
            embed.set_image(url=attch[0])
        await chan.send("", embed=embed)

    @cmd.Cog.listener()
    async def on_user_update(self, before, after):
        if before.bot:
            return
        i = None
        if before.avatar != after.avatar:
            url = after.avatar_url_as(static_format="png", size=1024)
            urls = str(url).split("/")[-1].split("?")[0]
            ctype, _ = mimetypes.guess_type(urls)
            ext = ctype.split("/")[-1]
            i = await self.bot.cdn.upload_file("u", after.id, url, ext, ctype)
            await self.bot.db.hset("avatar_cache", after.id, i)
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
        if chans_to_log_avatars and i is not None:
            embed = discord.Embed(title=f"**{after}**'s new avatar")
            embed.set_image(url=i)
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

    async def mod_log(self, action, guild, author, user, reason, duration=None):
        log_mod = await self.bot.db.hget(f"{guild.id}:set", "logmod")
        if log_mod is not None:
            log_mod = guild.get_channel(int(log_mod))
        if log_mod is None:
            await self.bot.db.hdel(f"{guild.id}:set", "logmod")
            raise cmd.BadArgument("Modlog channel is missing.")
        await self.bot.db.zincrement("cases", guild.id)
        case_number = await self.bot.db.zscore("cases", guild.id)
        pfx = await self.bot.db.hget(f"{guild.id}:set", "pfx")
        embed = discord.Embed(
            title=f"@**{user}** {action} by @**{author}**",
            type="rich",
            description=f"{user.mention} (ID: {user.id})",
            timestamp=arrow.utcnow().datetime,
        )
        embed.set_footer(text=str(guild.me), icon_url=guild.me.avatar_url)
        if reason is None:
            reason = "Responsible moderator, do **{}reason {}** to set a moderation reason.".format(
                self.bot.config["DEFAULT"]["prefix"] if pfx is None else pfx,
                case_number,
            )
        embed.add_field(name="Reason", value=reason)
        if duration is not None:
            embed.add_field(name="Duration", value=duration)
        print(embed.to_dict())
        case = await log_mod.send(embed=embed)
        await self.bot.db.hset(f"{guild.id}:case", case_number, case.id)

    async def on_member_ban(self, guild, author, user, reason, duration):
        await self.mod_log("banned", guild, author, user, reason, duration=duration)

    async def on_member_unban(self, guild, author, user, reason):
        await self.mod_log("unbanned", guild, author, user, reason)

    async def on_member_warn(self, guild, author, user, reason, duration):
        await self.mod_log("warned", guild, author, user, reason, duration=duration)

    async def on_member_pardon(self, guild, author, user, reason):
        await self.mod_log("pardoned", guild, author, user, reason)

    async def on_member_mute(self, guild, author, user, reason, duration):
        await self.mod_log("muted", guild, author, user, reason, duration=duration)

    async def on_member_unmute(self, guild, author, user, reason):
        await self.mod_log("unmuted", guild, author, user, reason)

    async def on_member_kick(self, guild, author, user, reason):
        await self.mod_log("kicked", guild, author, user, reason)


def setup(bot):
    bot.add_cog(LoggingModule(bot))
