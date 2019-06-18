from discord.ext import commands as cmd


class AutoroleModule(cmd.Cog):
    """Allows you to automagically give a user a role when they join the server. You can access this setting in the ;settings menu - use ;help set autorole for more info"""

    def __init__(self, bot: cmd.Bot):
        self.bot = bot

    @cmd.Cog.listener()
    async def on_member_join(self, member):
        auto_is_on = await self.bot.db.hget(f"{member.guild.id}:toggle", "autorole")
        if auto_is_on in (None, "0"):
            return
        auto_role = await self.bot.db.hget(f"{member.guild.id}:set", "autorole")
        if not auto_role:
            return
        role = member.guild.get_role(int(auto_role))
        if not role:
            await self.bot.db.hset(f"{member.guild.id}:toggle", "autorole", "0")
            await self.bot.db.hdel(f"{member.guild.id}:set", "autorole")
            return
        await member.add_roles(role)


def setup(bot):
    bot.add_cog(AutoroleModule(bot))
