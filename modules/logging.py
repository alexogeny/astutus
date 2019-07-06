# from imgurpython import ImgurClient
import mimetypes
from difflib import unified_diff
from urllib3.util import parse_url
import arrow
import discord
from discord.ext import commands as cmd
from discord.utils import get


class LoggingModule(cmd.Cog):
    """Automagically log message edits, deletes, user avatar changes, moderator actions, and so much more. You can access the settings of this module through the settings menu. Use **;help set log** for more info."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    async def parse_avatar(self, user):
        url = user.avatar_url_as(static_format="png", size=1024)
        parsed = parse_url(str(url))
        ext = parsed.path.split(".")[-1]
        ctype = f"image/{ext}"
        return url, ctype, ext

    async def log_avatar(self, user):
        cached = await self.bot.db.hget("avatar_cache", user.id)
        if not cached or cached is None:
            url, ctype, ext = await self.parse_avatar(user)
            i = await self.bot.cdn.upload_file("u", user.id, url, ext, ctype)
            await self.bot.db.hset("avatar_cache", user.id, i)
        return cached

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

        embed = await self.bot.embed()
        embed.title = f"**{member}** joined **{member.guild}**"
        embed.description = f"{member.mention} (ID: {member.id})"
        embed.color = 0x36CE31
        cached = await self.log_avatar(member)
        embed.set_thumbnail(url=cached)

        created = (member.joined_at - member.created_at).days
        plural = "s" if created != 1 else ""
        embed.add_field(name="Born", value=f"**{created}** day{plural} ago")

        await chan.send(embed=embed)

    @cmd.Cog.listener()
    async def on_member_remove(self, member):
        log_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "logging") or 0
        if not int(log_is_on):
            return
        log_chan = await self.bot.db.hget(f"{member.guild.id}:set", "logleaves") or 0
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        embed = discord.Embed(
            title=f"**{member}** left **{member.guild}**",
            description=f"{member.mention} (ID: {member.id})",
            color=0xFF0000,
        )
        i = await self.log_avatar(member)
        embed.set_thumbnail(url=i)
        await chan.send(embed=embed)

    @cmd.Cog.listener()
    async def on_message_edit(self, before, after):
        if not hasattr(after, "guild") or after.author.bot:
            return
        log = await self.bot.db.hget(f"{before.guild.id}:toggle", "logging") or 0
        if not int(log):
            return
        log_chan = await self.bot.db.hget(f"{before.guild.id}:set", "logedits") or 0
        chan = self.bot.get_channel(int(log_chan))
        if chan is None:
            await self.bot.db.hdel(f"{before.guild.id}:set", "logedits")
            return
        embed = discord.Embed(
            title=f"Message by @**{before.author}** in #**{before.channel}** was edited",
            description=f"{before.author.mention} (ID: {before.author.id})",
        )
        diff = unified_diff(
            before.content.split("\n"),
            after.content.split("\n"),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
        embed.add_field(
            name="Changes", value="```diff\n{}\n```".format("\n".join(list(diff)))
        )
        await chan.send(embed=embed)

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
        if hash(before.avatar) != hash(after.avatar):
            await self.log_user_avatar(after)

    async def log_user_avatar(self, after):
        url, ctype, ext = await self.parse_avatar(after)
        i = await self.bot.cdn.upload_file("u", after.id, url, ext, ctype)
        await self.bot.db.hset("avatar_cache", after.id, i)
        chans_to_log_avatars = []
        for guild in self.bot.guilds:
            log_is_on = await self.bot.db.hget(f"{guild.id}:toggle", "logging") or 0
            if int(log_is_on):
                log_chan = await self.bot.db.hget(f"{guild.id}:set", "logavatars") or 0
                chan = self.bot.get_channel(int(log_chan))
                if chan is None:
                    await self.bot.db.hdel(f"{guild.guild.id}:set", "logavatars")
                else:
                    if get(guild.members, id=after.id) is not None:
                        chans_to_log_avatars.append(chan)
        if chans_to_log_avatars:
            embed = await self.bot.embed()
            embed.title = f"**{after}**'s new avatar"
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

    async def mod_log(
        self, action, guild, author, user, reason, duration=None, roles=None
    ):
        log_mod = await self.bot.db.hget(f"{guild.id}:set", "logmod")
        if log_mod is not None:
            log_mod = guild.get_channel(int(log_mod))
        if log_mod is None:
            await self.bot.db.hdel(f"{guild.id}:set", "logmod")
            raise cmd.BadArgument("Modlog channel is missing.")
        await self.bot.db.zincrement("cases", guild.id)
        case_number = await self.bot.db.zscore("cases", guild.id)
        pfx = await self.bot.db.hget(f"{guild.id}:set", "pfx")
        embed = await self.bot.embed()
        embed.description = f"{user.mention} {action} by {author.mention}"
        embed.add_field(name="Case", value=case_number)
        embed.add_field(name="User ID", value=user.id)
        if reason is None:
            reason = "Responsible moderator, do **{}reason {}** to set a moderation reason.".format(
                self.bot.config["DEFAULT"]["prefix"] if pfx is None else pfx,
                case_number,
            )
        else:
            reason = reason.split("]")[-1]
        embed.add_field(name="Reason", value=reason)
        if duration is not None:
            embed.add_field(name="Duration", value=duration)
        if roles is not None:
            embed.add_field(
                name=action.title(), value=", ".join([r.mention for r in roles])
            )
        i = await self.log_avatar(user)
        embed.set_thumbnail(url=i)
        i = await self.log_avatar(author)
        embed.set_author(name=f"{author} ({author.id})", icon_url=i)
        case = await log_mod.send(embed=embed)
        await self.bot.db.hset(f"{guild.id}:case", case_number, case.id)

    async def on_member_ban(self, guild, author, user, reason, duration):
        await self.mod_log("banned", guild, author, user, reason, duration=duration)

    async def on_member_unban(self, guild, author, user, reason):
        await self.mod_log("unbanned", guild, author, user, reason)

    async def on_member_warn(self, guild, author, user, reason, duration):
        await self.mod_log("warned", guild, author, user, reason, duration=duration)
        automod = await self.bot.db.hget(f"{guild.id}:toggle", "automod")
        if automod is None or not int(automod):
            return
        offenses = int(await self.bot.db.zscore(f"{guild.id}:wrncnt", user.id) or 0)
        if not offenses:
            return
        for action in "mute kick ban".split():
            value = int(await self.bot.db.hget(f"{guild.id}:set", "automodmute") or 100)
            mod = self.bot.get_cog("ModerationModule")
            if offenses >= value:
                if action == "mute":
                    duration = arrow.utcnow().shift(hours=24)
                    await mod.mute_action(
                        guild,
                        user,
                        arrow.utcnow().shift(hours=24),
                        f"Auto mute at {offenses} offenses.",
                    )
                    await self.on_member_mute(
                        guild,
                        guild.me,
                        user,
                        "Exceeded auto mute warning limit.",
                        duration=duration.humanize().replace("in ", ""),
                    )

    async def on_member_pardon(self, guild, author, user, reason):
        await self.mod_log("pardoned", guild, author, user, reason)

    async def on_member_mute(self, guild, author, user, reason, duration):
        await self.mod_log("muted", guild, author, user, reason, duration=duration)

    async def on_member_unmute(self, guild, author, user, reason):
        await self.mod_log("unmuted", guild, author, user, reason)

    async def on_member_kick(self, guild, author, user, reason):
        await self.mod_log("kicked", guild, author, user, reason)

    async def on_member_nickname_update(self, guild, author, user, reason):
        await self.mod_log("renamed", guild, author, user, reason)

    async def on_member_role_add(self, guild, author, user, reason, roles, mod=True):
        if mod:
            await self.mod_log("roles added", guild, author, user, reason, roles=roles)
        else:
            await self.log_role("roles added", guild, user, reason, roles)

    async def on_member_role_remove(self, guild, author, user, reason, roles, mod=True):
        if mod:
            await self.mod_log(
                "roles removed", guild, author, user, reason, roles=roles
            )
        else:
            await self.log_role("roles removed", guild, user, reason, roles)

    async def log_role(self, action, guild, user, reason, roles=None):
        log_is_on = await self.bot.db.hget(f"{guild.id}:toggle", "logging")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{guild.id}:set", "logroles")
        if not log_chan:
            return
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        embed = await self.bot.embed()
        embed.description = f"{user.mention} {action} by self-assignment."
        embed.add_field(name="User ID", value=user.id)
        embed.add_field(name="Reason", value=reason)
        if roles is not None:
            embed.add_field(
                name=action.title(), value=", ".join([r.mention for r in roles])
            )
        i = await self.log_avatar(user)
        embed.set_thumbnail(url=i)
        await chan.send(embed=embed)


def setup(bot):
    bot.add_cog(LoggingModule(bot))
