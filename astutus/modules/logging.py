from discord.ext import commands as cmd


class LoggingModule(cmd.Cog):
    """Automagically log message edits, deletes, user avatar changes, moderator actions, and so much more. You can access the settings of this module through the settings menu. Use **;help set log** for more info."""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

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
        await chan.send(':inbox_tray: **{member}** joined the server')
    
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
        await chan.send(':outbox_tray: **{member}** left the server')
    
    @cmd.Cog.listener()
    async def on_raw_message_edit(self, before, after):
        log_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "log")
        if log_is_on in (None, "0"):
            return
        log_chan = await self.bot.db.hget(f"{member.guild.id}:set", "l_msg")
        if not log_chan:
            return
        chan = self.bot.get_channel(int(log_chan))
        if not chan:
            return
        
    
    @cmd.Cog.listener()
    async def on_raw_message_delete(self, message):
        return
    
    @cmd.Cog.listener()
    async def on_raw_bulk_message_delete(self, messages):
        return
    
    @cmd.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        return
    
    @cmd.Cog.listener()
    async def on_guild_channel_create(self, channel):
        return
    
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
